# Mechanical Joint Workbench (FreeCAD 1.1.1) — Proposta tecnica + scaffold implementativo

## 1) Architettura software generale

L'architettura è divisa in livelli, in modo da mantenere il **core cinematico** indipendente dalla GUI:

- **Layer A — Data Model (`App`)**
  - Oggetti documento FreeCAD (`App::FeaturePython` e in fase avanzata C++ `App::DocumentObject` custom).
  - Persistenza parametri giunti, limiti, stato collisioni, riferimenti a `App::Link`.
- **Layer B — Solver Core (`C++23`)**
  - Risolutore di vincoli non lineari + propagazione DoF su grafo multibody.
  - API stabile richiamabile da Python (pybind11 o binding FreeCAD nativi).
- **Layer C — Collision & Distance (`OpenCascade`)**
  - Broad-phase (AABB/OBB), narrow-phase OCC (`BRepExtrema`, `BRepAlgoAPI_Common`).
  - Classificazione contatti: proibito/funzionale/consentito.
- **Layer D — Kinematic Services**
  - FK/IK, finecorsa, anti-compenetrazione, gestione singolarità.
- **Layer E — GUI Workbench (`Gui`)**
  - Comandi, task panel, gizmo 3D, drag interattivo, animazione timeline.
- **Layer F — Reporting**
  - Distinta base, report interferenze, export CSV/JSON, snapshot stato meccanismo.

## 2) Struttura repository proposta

```text
src/Mod/MechanicalJoint/
  Init.py
  InitGui.py
  README.md
  App/
    JointTypes.py
    JointObject.py
    SolverBridge.py              # (fase successiva)
  Gui/
    Commands.py
    TaskJointEditor.py           # (fase successiva)
    TaskDiagnostics.py           # (fase successiva)
  Core/
    CMakeLists.txt               # (fase successiva)
    include/MechanicalJoint/
      JointGraph.hpp
      Constraint.hpp
      KinematicSolver.hpp
      CollisionEngine.hpp
    src/
      JointGraph.cpp
      KinematicSolver.cpp
      CollisionEngine.cpp
  Tests/
    test_joint_object.py
    test_constraint_graph.py
```

## 3) Moduli principali

1. **Constraint System**: normalizza vincoli geometrici in equazioni/scalari residui.
2. **Kinematic Solver**: Newton-Raphson + damping + gestione limiti e vincoli attivi.
3. **Collision Module**: distanza minima, overlap volume, contact pair classification.
4. **Joint Library**: rotoidale, prismatico, cilindrico, sferico, planare, fisso, cardanico, screw, gear pair, belt, cam.
5. **Diagnostics Engine**: DoF residui, ridondanze, sovravincoli, catene bloccate.
6. **Animation/Actuation**: motori, servo, profili temporali, sweep cinematica.
7. **Parametric Generators**: ingranaggi, molle, pulegge, cinghie, fasteners.
8. **Assembly Robustness**: gestione sottoassiemi annidati e riferimenti stabili su `App::Link`.

## 4) Classi C++ principali (design)

```cpp
// Core/include/MechanicalJoint/Constraint.hpp
#pragma once
#include <array>
#include <string>
#include <vector>

namespace MechanicalJoint {

enum class ContactClass { Forbidden, Functional, Allowed };
enum class JointKind {
    Revolute, Prismatic, Cylindrical, Spherical, Planar, Fixed,
    Universal, Screw, RackPinion, Gear, BeltPulley, CamFollower, CrankSlider
};

struct JointState {
    JointKind kind;
    std::array<double, 6> q{};      // generalized coordinates
    std::array<double, 6> qdot{};
    std::array<double, 6> limitMin{};
    std::array<double, 6> limitMax{};
};

class Constraint {
public:
    virtual ~Constraint() = default;
    virtual std::string name() const = 0;
    virtual int residualSize() const = 0;
    virtual void evaluate(const std::vector<double>& x, std::vector<double>& r) const = 0;
};

} // namespace MechanicalJoint
```

```cpp
// Core/include/MechanicalJoint/KinematicSolver.hpp
#pragma once
#include <memory>
#include <vector>

namespace MechanicalJoint {

class Constraint;

struct SolveOptions {
    int maxIterations{50};
    double tolerance{1e-8};
    double lambda{1e-3};  // Levenberg damping
    bool enforceLimits{true};
    bool antiPenetration{true};
};

struct SolveReport {
    bool converged{false};
    int iterations{0};
    double residualNorm{0.0};
    int activeLimitCount{0};
    int collisionPairs{0};
};

class KinematicSolver {
public:
    void addConstraint(std::shared_ptr<Constraint> c);
    SolveReport solve(std::vector<double>& x, const SolveOptions& options);
private:
    std::vector<std::shared_ptr<Constraint>> constraints_;
};

} // namespace MechanicalJoint
```

## 5) Classi Python principali (implementate nello scaffold)

- `JointType` enum con tutti i tipi di giunto richiesti.
- `JointFeaturePython` con proprietà documento FreeCAD:
  - `ReferenceA`, `ReferenceB`, `JointType`, `LimitMin`, `LimitMax`, `EnableCollisionGuard`, `Clearance`.
- `CommandCreateRevolute` e `CommandRunDiagnostics`.
- `MechanicalJointWorkbench` registrato in GUI.

## 6) Design solver cinematico

Approccio realistico per FreeCAD 1.1.1:

- **Formulazione a vincoli**: `f(x)=0` con variabili generalizzate per ogni body/joint.
- **Risoluzione**:
  - fase 1: linearizzazione locale (`J * dx = -f`),
  - fase 2: aggiornamento con damping,
  - fase 3: proiezione su limiti/corse,
  - fase 4: attivazione vincoli anti-compenetrazione se distanza < clearance.
- **IK**: target pose come vincoli additivi con pesi; fallback su least-squares pesata.
- **Singolarità**: soglia su condizionamento Jacobiana + regolarizzazione.

## 7) Design sistema vincoli

I vincoli sono trattati come blocchi modulari:

- `GeometricConstraint`: coincidenza, parallelismo, offset, angolo.
- `JointConstraint`: equazioni dedicate per ogni joint type.
- `CouplingConstraint`: gear ratio, rack-pinion law, screw pitch law.
- `ContactConstraint`: non-penetrazione (`gap >= 0`) e contatti funzionali.

Le equazioni sono aggregate su grafo gerarchico (subassembly come super-nodo espandibile).

## 8) Strategia collision detection e distance query

- **Broad-phase**: BVH AABB per coppie candidate su assembly complessi.
- **Narrow-phase**:
  - distanza minima: `BRepExtrema_DistShapeShape`;
  - interferenza volumetrica: `BRepAlgoAPI_Common` (volume > epsilon).
- **In movimento**: campionamento temporale + conservative advancement per velocità elevate.
- **Classificazione contatti**:
  - `Forbidden`: violazione hard-stop,
  - `Functional`: contatto previsto (cam follower, battuta),
  - `Allowed`: touch nominale senza errore.

## 9) Propagazione gradi di libertà

- Grafo bipartito body/constraint.
- Calcolo DoF locale per joint e riduzione tramite rank Jacobiana globale.
- Propagazione top-down (subassembly) + bottom-up (feedback su vincoli attivi).
- Diagnostica real-time:
  - DoF residui,
  - sovravincolo,
  - ridondanze,
  - componenti isolate.

## 10) Strategia sottoassiemi annidati e App::Link

- Ogni sottoassieme mantiene `LCS` locale (Local Coordinate System).
- Le istanze `App::Link` ereditano trasformazioni via catena parent→child.
- I vincoli memorizzano:
  - path stabile (`DocumentObject` + `SubElement`),
  - fallback GUID locale,
  - contesto di assembly owner.
- Cache trasformazioni per ridurre recompute durante drag/animazione.

## 11) Strategia anti topological naming problem

- Prediligere riferimenti a feature semantiche (LCS, datum planes, axis systems) invece che facce nude.
- Per riferimenti geometrici diretti, salvare firma robusta:
  - tipo superficie,
  - bounding box locale,
  - centroide,
  - invarianti metrici.
- Implementare remap post-recompute con scoring multi-criterio.

## 12) Progettazione UI

- **Task panel giunto**: scelta tipo giunto, selezione `ReferenceA/B`, limiti e clearance.
- **Snap intelligente**: suggerimento accoppiamenti coassiali/planari con ranking.
- **Gizmo 3D**: manipolazione DoF attivi con preview collisioni.
- **Pannello diagnostica live**: errori solver, conflitti, sovra/sottovincoli.
- **Animazione**: timeline, keyframe parametro, export video (MP4/GIF via ffmpeg opzionale).
- **BOM/report**: estrazione componenti, joint list, collision report.

## 13) Esempi di codice reali (inclusi)

### Registrazione Workbench
File: `InitGui.py`.

```python
class MechanicalJointWorkbench(Workbench):
    MenuText = "Mechanical Joint"
    def Initialize(self):
        from MechanicalJoint.Gui import Commands
        command_list = ["MechanicalJoint_CreateRevolute", "MechanicalJoint_RunDiagnostics"]
        self.appendToolbar("Mechanical Joint", command_list)
        self.appendMenu(["Mechanical Joint"], command_list)
```

### Creazione oggetto giunto
File: `App/JointObject.py`.

```python
obj = doc.addObject("App::FeaturePython", name)
JointFeaturePython(obj)
obj.JointType = "Revolute"
doc.recompute()
```

### Diagnostica minima
File: `Gui/Commands.py`.

```python
joint_objs = [obj for obj in doc.Objects if hasattr(obj, "JointType")]
underconstrained = [obj.Name for obj in joint_objs if obj.ReferenceA is None or obj.ReferenceB is None]
```

## 14) Roadmap di sviluppo

### MVP (6-8 settimane)

- Workbench installabile locale (`src/Mod/MechanicalJoint`).
- Giunti base: revolute, prismatic, fixed, cylindrical.
- FK base + limiti corsa.
- Collision check statico e diagnostica minima.
- UI essenziale + report testuale.

### Versione intermedia (3-5 mesi)

- IK multi-target stabile.
- Gear/rack-pinion/screw constraints.
- Sottoassiemi annidati con cache trasformazioni.
- Contatti funzionali in simulazione movimento.
- Generatori parametrici (gear/spring/pulley).

### Versione completa (6-12 mesi)

- Cam follower, belt drive avanzato, crank-slider dinamico.
- Solver ibrido con warm-start e gestione singolarità avanzata.
- Diagnostica live avanzata + export video + BOM estesa.
- Pipeline robusta anti-toponaming con remap semantico.

## 15) Test unitari e validazione

- **Unit test solver**: convergenza, rank Jacobiana, gestione limiti.
- **Unit test collision**: distance query, overlap detection, classification.
- **Regression test assembly**: robot 6 assi, biella-manovella, trasmissione ingranaggi.
- **Stress test**: assiemi 500+ componenti con `App::Link` annidati.
- **Golden scenarios**:
  - motore con camme,
  - sospensione doppio braccio,
  - esoscheletro con servoattuatori.

## 16) Limiti tecnici e compromessi realistici

- **Realistico subito**:
  - giunti base,
  - FK robusta,
  - collisioni statiche,
  - diagnostica DoF base,
  - integrazione GUI FreeCAD.
- **Richiede sviluppo avanzato**:
  - IK complessa su catene ridondanti,
  - camme-punterie robuste su geometrie reali sporche,
  - anti-toponaming generalizzato su tutti i casi,
  - realtime fluido su assiemi molto grandi senza C++ ottimizzato.

## Installazione locale senza Addon Manager

1. Copiare la cartella `src/Mod/MechanicalJoint` in `Mod/MechanicalJoint` della propria installazione FreeCAD 1.1.1 locale.
2. Riavviare FreeCAD.
3. Selezionare il workbench **Mechanical Joint** dal selettore workbench.

---

Questo scaffold è una base concreta e installabile localmente; il cuore solver/collision C++23 va completato progressivamente secondo la roadmap.
