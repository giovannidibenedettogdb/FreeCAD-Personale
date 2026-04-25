# SPDX-License-Identifier: LGPL-2.1-or-later
"""Joint type declarations shared across App and Gui modules."""

from enum import Enum


class JointType(str, Enum):
    REVOLUTE = "Revolute"
    PRISMATIC = "Prismatic"
    CYLINDRICAL = "Cylindrical"
    SPHERICAL = "Spherical"
    PLANAR = "Planar"
    FIXED = "Fixed"
    UNIVERSAL = "Universal"
    SCREW = "Screw"
    RACK_PINION = "RackPinion"
    GEAR = "Gear"
    BELT_PULLEY = "BeltPulley"
    CAM_FOLLOWER = "CamFollower"
    CRANK_SLIDER = "CrankSlider"


JOINT_TYPE_LABELS = [jt.value for jt in JointType]
