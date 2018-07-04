"""
Pan Tilt head mount
"""

import cadquery as cq
import cqparts
from cadquery import Solid
from cqparts.params import *
from cqparts.display import render_props, display
from cqparts.constraint import Fixed, Coincident
from cqparts.constraint import Mate
from cqparts.utils.geometry import CoordSystem

from cqparts_motors.shaft import Shaft

from servo import SubMicro

class MountTab(cqparts.Part):
    diameter  = PositiveFloat(6)
    height = PositiveFloat(4)
    length = PositiveFloat(4)
    hole = PositiveFloat(2)
    def make(self):
        mount = cq.Workplane("XY").circle(self.diameter/2).extrude(self.height)
        tab = cq.Workplane("XY")\
            .rect(self.length,self.diameter)\
            .extrude(self.height)\
            .translate((self.length,0,0))
        mount = mount.union(tab)
        return mount

class Base(cqparts.Part):
    diameter  = PositiveFloat(40)
    height = PositiveFloat(10)

    _render = render_props(color=(0,5,50))

    def make(self):
        base = cq.Workplane("XY").circle(self.diameter/2).extrude(self.height)
        return base


if __name__ == "__main__":
    from cqparts.display import display
    #B = Base()
    B = MountTab()
    display(B)
