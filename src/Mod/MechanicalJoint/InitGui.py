# SPDX-License-Identifier: LGPL-2.1-or-later
"""Mechanical Joint Workbench GUI initialization for FreeCAD 1.1.1."""

import FreeCAD as App
import FreeCADGui as Gui


class MechanicalJointWorkbench(Workbench):
    """Workbench entry point registered in FreeCAD GUI."""

    MenuText = "Mechanical Joint"
    ToolTip = "Parametric mechanical joints, kinematics and diagnostics"
    Icon = """
    /* XPM */
    static const char *joint_xpm[] = {
    "16 16 3 1",
    "  c None",
    ". c #2f6db3",
    "+ c #ffffff",
    "                ",
    "      ....      ",
    "    ..++++..    ",
    "   .++....++.   ",
    "  .++.    .++.  ",
    "  .+.      .+.  ",
    " ..+.  ..  .+.. ",
    " .++. .++. .++. ",
    " .++. .++. .++. ",
    " ..+.  ..  .+.. ",
    "  .+.      .+.  ",
    "  .++.    .++.  ",
    "   .++....++.   ",
    "    ..++++..    ",
    "      ....      ",
    "                "};
    """

    def Initialize(self):
        from MechanicalJoint.Gui import Commands

        command_list = [
            "MechanicalJoint_CreateRevolute",
            "MechanicalJoint_RunDiagnostics",
        ]
        self.appendToolbar("Mechanical Joint", command_list)
        self.appendMenu(["Mechanical Joint"], command_list)

        App.Console.PrintLog("MechanicalJoint: GUI initialized\n")

    def Activated(self):
        App.Console.PrintMessage("Mechanical Joint workbench activated\n")

    def Deactivated(self):
        App.Console.PrintMessage("Mechanical Joint workbench deactivated\n")


Gui.addWorkbench(MechanicalJointWorkbench())
