# stolen from 
# https://github.com/dcowden/cadquery/blob/master/cadquery/freecad_impl/exporters.py
# svg export modified to export hidden only 

from __future__ import unicode_literals

import cadquery

import FreeCAD
import Drawing

import tempfile, os, io

#weird syntax i know
from cadquery.freecad_impl import suppress_stdout_stderr

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class ExportTypes:
    STL = "STL"
    STEP = "STEP"
    AMF = "AMF"
    SVG = "SVG"
    TJS = "TJS"


class UNITS:
    MM = "mm"
    IN = "in"


def toString(shape, exportType, tolerance=0.1):
    s = io.StringIO()
    exportShape(shape, exportType, s, tolerance)
    return s.getvalue()

def guessUnitOfMeasure(shape):
    """
        Guess the unit of measure of a shape.
    """
    bb = shape.BoundBox

    dimList = [ bb.XLength, bb.YLength,bb.ZLength ]
    #no real part would likely be bigger than 10 inches on any side
    if max(dimList) > 10:
        return UNITS.MM

    #no real part would likely be smaller than 0.1 mm on all dimensions
    if min(dimList) < 0.1:
        return UNITS.IN

    #no real part would have the sum of its dimensions less than about 5mm
    if sum(dimList) < 10:
        return UNITS.IN

    return UNITS.MM

def getPaths(freeCadSVG):
    """
        freeCad svg is worthless-- except for paths, which are fairly useful
        this method accepts svg from fReeCAD and returns a list of strings suitable for inclusion in a path element
        returns two lists-- one list of visible lines, and one list of hidden lines

        HACK ALERT!!!!!
        FreeCAD does not give a way to determine which lines are hidden and which are not
        the only way to tell is that hidden lines are in a <g> with 0.15 stroke and visible are 0.35 stroke.
        so we actually look for that as a way to parse.

        to make it worse, elementTree xpath attribute selectors do not work in python 2.6, and we
        cannot use python 2.7 due to freecad. So its necessary to look for the pure strings! ick!
    """

    hiddenPaths = []
    visiblePaths = []
    if len(freeCadSVG) > 0:
        #yuk, freecad returns svg fragments. stupid stupid
        fullDoc = "<root>%s</root>" % freeCadSVG
        e = ET.ElementTree(ET.fromstring(fullDoc))
        segments = e.findall(".//g")
        for s in segments:
            paths = s.findall("path")

            if s.get("stroke-width") == "0.15": #hidden line HACK HACK HACK
                mylist = hiddenPaths
            else:
                mylist = visiblePaths

            for p in paths:
                mylist.append(p.get("d"))
        return (hiddenPaths,visiblePaths)
    else:
        return ([],[])


def getSVG(shape, opts=None, view_vector=(-0, 0, 20.0)):
    """
        Export a shape to SVG
    """
    
    d = {'width':800,'height':240,'marginLeft':200,'marginTop':20}

    if opts:
        d.update(opts)

    #need to guess the scale and the coordinate center
    uom = guessUnitOfMeasure(shape)

    width=float(d['width'])
    height=float(d['height'])
    marginLeft=float(d['marginLeft'])
    marginTop=float(d['marginTop'])

    #TODO:  provide option to give 3 views
    viewVector = FreeCAD.Base.Vector(view_vector)
    (visibleG0,visibleG1,hiddenG0,hiddenG1) = Drawing.project(shape,viewVector)

    (hiddenPaths,visiblePaths) = getPaths(Drawing.projectToSVG(shape,viewVector,"")) #this param is totally undocumented!

    #get bounding box -- these are all in 2-d space
    bb = visibleG0.BoundBox
    bb.add(visibleG1.BoundBox)
    bb.add(hiddenG0.BoundBox)
    bb.add(hiddenG1.BoundBox)

    #width pixels for x, height pixesl for y
    unitScale = min( width / bb.XLength * 0.75 , height / bb.YLength * 0.75 )

    #compute amount to translate-- move the top left into view
    (xTranslate,yTranslate) = ( (0 - bb.XMin) + marginLeft/unitScale ,(0- bb.YMax) - marginTop/unitScale)

    #compute paths ( again -- had to strip out freecad crap )
    hiddenContent = ""
    for p in hiddenPaths:
        hiddenContent += PATHTEMPLATE % p
    visibleContent = ""
    for p in visiblePaths:
        visibleContent += PATHTEMPLATE % p

    svg =  SVG_TEMPLATE % (
        {
            'unitScale': str(unitScale),
            'strokeWidth': 0.3, 
            'hiddenContent':  visibleContent,
            'xTranslate': str(xTranslate),
            'yTranslate': str(yTranslate),
            'width': str(width),
            'height': str(height),
            'textboxY': str(height - 30),
            'uom': str(uom)
        }
    )
    #svg = SVG_TEMPLATE % (
    #    {"content": projectedContent}
    #)
    return svg


def exportSVG(shape, fileName, view_vector=(0,0,20)):
    """
        accept a cadquery shape, and export it to the provided file
        TODO: should use file-like objects, not a fileName, and/or be able to return a string instead
        export a view of a part to svg
    """
    svg = getSVG(shape.val().wrapped, opts=None, view_vector=view_vector)
    f = open(fileName,'w')
    f.write(svg)
    f.close()



SVG_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   width="%(width)s"
   height="%(height)s"

>
    <g transform="scale(%(unitScale)s, -%(unitScale)s)   translate(%(xTranslate)s,%(yTranslate)s)" stroke-width="%(strokeWidth)s"  fill="none">
       <g  stroke="rgb(0, 0, 0)" fill="none" >
%(hiddenContent)s
       </g>
    </g>
</svg>
"""

PATHTEMPLATE="\t\t\t<path d=\"%s\" />\n"
