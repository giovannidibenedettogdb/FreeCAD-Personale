# SPDX-License-Identifier: LGPL-2.1-or-later
"""Core FeaturePython object for a single joint relation."""

import FreeCAD as App

from MechanicalJoint.App.JointTypes import JOINT_TYPE_LABELS


class JointFeaturePython:
    """Parametric data model for one mechanical joint."""

    def __init__(self, obj: App.DocumentObject):
        obj.Proxy = self
        self._init_properties(obj)

    def _init_properties(self, obj: App.DocumentObject) -> None:
        group = "MechanicalJoint"
        obj.addProperty("App::PropertyLinkSub", "ReferenceA", group, "Primary reference").ReferenceA = None
        obj.addProperty("App::PropertyLinkSub", "ReferenceB", group, "Secondary reference").ReferenceB = None

        enum_prop = obj.addProperty("App::PropertyEnumeration", "JointType", group, "Joint kinematic class")
        enum_prop.JointType = JOINT_TYPE_LABELS
        obj.JointType = JOINT_TYPE_LABELS[0]

        obj.addProperty("App::PropertyFloat", "LimitMin", group, "Lower travel limit").LimitMin = 0.0
        obj.addProperty("App::PropertyFloat", "LimitMax", group, "Upper travel limit").LimitMax = 360.0
        obj.addProperty("App::PropertyBool", "EnableCollisionGuard", group, "Enable anti-interpenetration checks").EnableCollisionGuard = True
        obj.addProperty("App::PropertyFloat", "Clearance", group, "Minimal allowed clearance (mm)").Clearance = 0.02

    def execute(self, obj: App.DocumentObject) -> None:
        # Placeholder hook where solver state and contact checks are evaluated.
        if obj.LimitMin > obj.LimitMax:
            raise ValueError("MechanicalJoint: LimitMin must be <= LimitMax")


class ViewProviderJoint:
    """Lightweight view provider with standard icon."""

    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self) -> str:
        return ":/icons/constraint.svg"


def create_joint(name: str = "MechanicalJoint"):
    doc = App.ActiveDocument
    if doc is None:
        raise RuntimeError("MechanicalJoint: No active document")

    obj = doc.addObject("App::FeaturePython", name)
    JointFeaturePython(obj)

    if App.GuiUp:
        ViewProviderJoint(obj.ViewObject)

    doc.recompute()
    return obj
