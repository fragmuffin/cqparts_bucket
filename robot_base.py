"""
Base for robot rovers
"""

import cadquery as cq
import cqparts
from cadquery import Solid
from cqparts.params import *
from cqparts.display import render_props, display
from cqparts.constraint import Fixed, Coincident
from cqparts.constraint import Mate
from cqparts.utils.geometry import CoordSystem

from motor_mount import MountedStepper 
from stepper import Stepper
from mercanum import MercanumWheel
from wheel import SimpleWheel

class PartRef(Parameter):

    def type(self, value):
        return value

class RobotBase(cqparts.Part):
    length = PositiveFloat(250)
    width = PositiveFloat(220)
    thickness = PositiveFloat(8)
    chamfer = PositiveFloat(30)
    _render = render_props(template="wood")

    def make(self):
        base = cq.Workplane("XY").rect(self.length,self.width).extrude(self.thickness)
        base = base.edges("|Z and >X").chamfer(self.chamfer)
        return base

    # TODO mountpoints for stuff

    def mate_back_third(self,offset=0):
        return Mate(self, CoordSystem(
            origin=(-self.length/2+offset, self.width/2,0),
            xDir=(1, 0, 0),
            normal=(0, 0,-1)
        ))

    def mate_RL(self,offset=0):
        return Mate(self, CoordSystem(
            origin=(-self.length/2+offset, self.width/2,0),
            xDir=(1, 0, 0),
            normal=(0, 0,-1)
        ))

    def mate_RR(self,offset=0):
        return Mate(self, CoordSystem(
            origin=(-self.length/2+offset, -self.width/2,0),
            xDir=(-1, 0, 0),
            normal=(0, 0,-1)
        ))

class ThisWheel(SimpleWheel):
    diameter = PositiveFloat(40)
    thickness = PositiveFloat(20)


class ThisStepper(Stepper):
    width = PositiveFloat(20)
    height = PositiveFloat(20)
    length = PositiveFloat(30)

class Rover(cqparts.Assembly):
    length = PositiveFloat(250)
    width = PositiveFloat(116)
    chamfer = PositiveFloat(40)
    wheel = PartRef(SimpleWheel)
    #wheel = PartRef(MercanumWheel)
    stepper = PartRef(Stepper)

    def make_components(self):
        base = RobotBase(
            length=self.length
            ,width=self.width
            ,chamfer=self.chamfer
        )
        # TODO target not working on mounted stepper yet
        comps = {
            'base': base,
            'Ldrive_b': MountedStepper(stepper=self.stepper,driven=self.wheel,target=base),
            'Rdrive_b': MountedStepper(stepper=self.stepper,driven=self.wheel,target=base),
            'Ldrive_f': MountedStepper(stepper=self.stepper,driven=self.wheel,target=base),
            'Rdrive_f': MountedStepper(stepper=self.stepper,driven=self.wheel,target=base)
        }
        return comps

    def make_constraints(self):
        constr = [
            Fixed(self.components['base'].mate_origin,
                  CoordSystem(origin=(0,0,100))),
            Coincident(
                self.components['Ldrive_b'].mate_corner(flip=-1),
                self.components['base'].mate_RL()
            ),
            Coincident(
                self.components['Rdrive_b'].mate_corner(flip=1),
                self.components['base'].mate_RR()
            ),
            Coincident(
                self.components['Ldrive_f'].mate_corner(flip=1),
                self.components['base'].mate_RL(offset=self.length-self.chamfer)
            ),
            Coincident(
                self.components['Rdrive_f'].mate_corner(flip=-1),
                self.components['base'].mate_RR(offset=self.length-self.chamfer)
            )
        ]
        return constr

if __name__ == "__main__":
    from cqparts.display import display
    #B = RobotBase()
    B = Rover()
    display(B)
