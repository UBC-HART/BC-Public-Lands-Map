'''
Riparian_A_L.py

Selects riparian lines from BC Freshwater Atlas stream, linear boundary and coastline feature classes, 
buffers my 30m
Due to the size of the input data, the stream networks and linear boundaries were divided into two groups,
Watersheds with names beginning with the letters A-L and Watersheds with names beginning with the letters M-Z.
Specific line types were selected, merged and then buffered by 30m.  
The two output riparian buffer layers were then appended together manually in ArcPro to create the final BC riparian layer.

Ian Parfitt   27 Aug 2026
'''

import arcpy
import requests
import csv
import sys
import pandas
import os

arcpy.env.overwriteOutput = True

#Set working directories and gdbs
Workdir = r'C:\working\GISdata\Riparian'
ScratchWksp = r'C:\working\ArcProjects\scratch\scratchwkspce.gdb'
Workgdb = 'Riparian.gdb'
outGDB = os.path.join(Workdir, Workgdb)
arcpy.env.workspace = outGDB

if not arcpy.Exists(outGDB):
    arcpy.management.CreateFileGDB(Workdir, Workgdb)
    print (outGDB + " created")

StreamNetworkDir = r'C:\working\GISdata\BCGW\FWA\FWA_STREAM_NETWORKS_SP.gdb'
StreamNetworkFC = r'BCFWA_STREAM_NETWORKS_A_L'
StreamNetworkFP = os.path.join(StreamNetworkDir,StreamNetworkFC)

LinearNetworkDir = r'C:\working\GISdata\BCGW\FWA\FWA_LINEAR_BOUNDARIES_SP.gdb'
LinearNetworkFC = r'BCFWA_LINEAR_BOUNDARIES_A_L'
LinearNetworkFP = os.path.join(LinearNetworkDir,LinearNetworkFC)

CoastDir = r'C:\working\GISdata\BCGW\FWA_COASTLINES_SP.gdb'
CoastFC = r'WHSE_BASEMAPPING_FWA_COASTLINES_SP'
CoastFP = os.path.join(CoastDir,CoastFC)

arcpy.env.workspace = outGDB
# print(arcpy.env.workspace)

fcodeFld = "FEATURE_CODE"

arcpy.env.extent = r'C:\working\GISdata\BCGW\FWA\FWA_BC.gdb\FWA_ASSESSMENT_WATERSHEDS_POLY'
# arcpy.env.extent = LinearNetworkFP

print("Selecting Waterlines")
where_clause = (
    "FEATURE_CODE IN ('GB15300000','GB24300000', 'GC17100000', 'GE14850000', 'GC30050000','WA24200110','WA24200120',"
    "'WA24200130', 'WA24200140','WA24200150','WA24220110','WA24220120','WA24220130','WA24220140')" 
    )
print(where_clause)
# ["GA24850000", "GB15300000", "GC17100000", "GC3005000","GE14850000","GG05800000"]'
linearLyr = "LinearLYR"
linearOut = "Waterlines"
arcpy.management.MakeFeatureLayer(LinearNetworkFP, linearLyr)
arcpy.management.SelectLayerByAttribute(linearLyr,"NEW_SELECTION",where_clause)
arcpy.management.CopyFeatures(linearLyr,linearOut)
print(linearOut + " created")

# arcpy.env.extent = StreamNetworkFP

print("Selecting streams")
where_clause = f"{fcodeFld} IN ('GA24850000')"
print(where_clause)
# ["GA24850000", "GB15300000", "GC17100000", "GC3005000","GE14850000","GG05800000"]'
streamLyr = "streamLYR"
streamOut = "Streamlines"
arcpy.management.MakeFeatureLayer(StreamNetworkFP, streamLyr)
arcpy.management.SelectLayerByAttribute(streamLyr,"NEW_SELECTION",where_clause)
arcpy.management.CopyFeatures(streamLyr,streamOut)
print(streamOut + " created")

# arcpy.env.extent = CoastFP

print("Selecting coastlines")
where_clause = f"{fcodeFld} IN ('GE14850000','GG05800000')"
print(where_clause)
# ["GA24850000", "GB15300000", "GC17100000", "GC3005000","GE14850000","GG05800000"]'
coastLyr = "coastLYR"
coastOut = "Coastlines"
arcpy.management.MakeFeatureLayer(CoastFP, coastLyr)
arcpy.management.SelectLayerByAttribute(coastLyr,"NEW_SELECTION",where_clause)
arcpy.management.CopyFeatures(coastLyr,coastOut)
print(coastOut + " created")

linearOut = "Waterlines"
streamOut = "Streamlines"
coastOut = "Coastlines"

riplineFC = "Riparian_lines_A_L"
arcpy.management.Merge([linearOut,streamOut,coastOut], riplineFC)
print(riplineFC + " created")

riplineFC = "Riparian_lines_A_L"
rippolyFC = "Riparian_buffers_A_L"

print("Running Pairwise Buffer ...")
arcpy.analysis.PairwiseBuffer(riplineFC,rippolyFC, "30", "None", None, "PLANAR", "0.1 Meters")
print("Pairwise Buffer Complere")

# arcpy.analysis.Buffer(riplineFC,rippolyFC, "30", "ALL")

rippolyFC = "Riparian_buffers_A_L"
riparianFld = "Riparian"
expression = "'Y'"
if not arcpy.ListFields(rippolyFC,riparianFld):
    arcpy.management.AddField(rippolyFC,riparianFld,"TEXT",field_length = "3")
arcpy.management.CalculateField(rippolyFC,riparianFld,expression,'PYTHON3')
print(riparianFld + " added to " + rippolyFC)

print("Done")