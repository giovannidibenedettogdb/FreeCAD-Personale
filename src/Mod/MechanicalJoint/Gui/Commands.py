# SPDX-License-Identifier: LGPL-2.1-or-later
"""GUI commands for the Mechanical Joint workbench."""

import FreeCAD as App
import FreeCADGui as Gui

from MechanicalJoint.App.JointObject import create_joint


class CommandCreateRevolute:
    def GetResources(self):
        return {
            "Pixmap": ":/icons/constraint.svg",
            "MenuText": "Create Revolute Joint",
            "ToolTip": "Create a new parametric revolute joint object",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        obj = create_joint("RevoluteJoint")
        obj.JointType = "Revolute"
        App.Console.PrintMessage(f"MechanicalJoint: created {obj.Name}\n")


class CommandRunDiagnostics:
    def GetResources(self):
        return {
            "Pixmap": ":/icons/check.svg",
            "MenuText": "Run Joint Diagnostics",
            "ToolTip": "Run a lightweight diagnostic pass on mechanical joints",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        doc = App.ActiveDocument
        joint_objs = [obj for obj in doc.Objects if hasattr(obj, "JointType")]
        if not joint_objs:
            App.Console.PrintWarning("MechanicalJoint: no joint objects found\n")
            return

        underconstrained = [obj.Name for obj in joint_objs if obj.ReferenceA is None or obj.ReferenceB is None]
        App.Console.PrintMessage(
            "MechanicalJoint diagnostics: "
            f"joints={len(joint_objs)}, underconstrained={len(underconstrained)}\n"
        )


Gui.addCommand("MechanicalJoint_CreateRevolute", CommandCreateRevolute())
Gui.addCommand("MechanicalJoint_RunDiagnostics", CommandRunDiagnostics())
