'''
RDPubExtentRedux.py

This code is used to create a polygon area of interest for DEM and Slope raster creation.  Initially it was 
set to the Regional District boundary, but this proved infeasible due to data size and time constraints.  N
Next it was shrunk to the bounding box of the public land data for an RD.  
This also proved too large so reduced further to a buffer around the RD's public land data.

Ian Parfitt  26 Aug 2026
'''

import arcpy
import os

from arcpy.sa import *

arcpy.env.overwriteOutput = True

#Update for RD
RD = 'Bulkley-Nechako'
RDinit = 'RDBN'

#Set working directories and gdbs
Workdir = r'C:\working\ArcProjects\workspace'
ScratchWksp = r'C:\working\ArcProjects\scratch\scratchworkspace.gdb'
# Update for RD
Workgdb = RDinit + 'PubJune.gdb'
outGDB = os.path.join(Workdir, Workgdb)

arcpy.env.workspace = outGDB
arcpy.env.scratchWorkspace = ScratchWksp

RDpubFC = "Public_" + RDinit
RDbndFC = RDinit + "_Bndry"


arcpy.env.extent = RDbndFC

RDpubBuf1000 = RDpubFC + "_buf1000"

if not arcpy.Exists(RDpubBuf1000):
    arcpy.analysis.PairwiseBuffer(RDpubFC,RDpubBuf1000,1000)

print("done")
