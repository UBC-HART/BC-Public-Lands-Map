'''
ParcelMap_SelectBCPub.py
Selects BC Public Lands from a ParcelMapBC snapshot spatial layer.
-Private, Mixed, Unclassified, First Nations, None Ownertypes not selected.
-Name and ParcelClass fields used to unselect Roads
-Legal Description field used to unselect Indian Reserves

BC Parks and Protected Areas polygons erased from selection output
Indian Reservations erased

Ian Parfitt 27 Aug 2026
'''

import arcpy
import requests
import csv
import sys
import pandas
import os

arcpy.env.overwriteOutput = True

#Set working directories and gdbs
Workdir = r'C:\working\ArcProjects\workspace'
ScratchWksp = r'C:\working\ArcProjects\scratch\scratchworkspace.gdb'
Workgdb = 'BCPubOct.gdb'
outGDB = os.path.join(Workdir, Workgdb)

arcpy.env.workspace = outGDB
arcpy.env.scratchWorkspace = ScratchWksp
print(arcpy.env.workspace)

inLayer = r'C:\working\GISdata\ICIS\ParcelMapBCSnapshot_2026-01-18.gdb\Parcel_Polygon'

if not arcpy.Exists(outGDB):
    arcpy.CreateFileGDB_management(Workdir, Workgdb)
    print(outGDB + " created")

outLayer = "BC_PubIndexJan"
if arcpy.Exists(outLayer):
    arcpy.Delete_management(outLayer)
    print(outLayer + " deleted")

where_clause = "Ownertype NOT IN ('PRIVATE','UNCLASS','MIXED OWNERSHIP','FIRST NATION','FIRST NATIONS','NONE','UNKNOWN') \
AND Name NOT IN ('Road', 'Lane', 'Statutory RoW') AND ParcelClass NOT IN ('ROAD', 'LANE') "

where_clauseIR = "LegalDescription LIKE '%INDIAN RESERVE%' OR LegalDescription LIKE '%I.R.%' OR LegalDescription LIKE 'I.R.%' \
OR PlanNumber LIKE '%INDIAN_RESERVE%' OR PlanNumber LIKE '%_IR_%' \
OR PID IN (15796841,15796876,15796931,24682250,7682361,7682387,7682409,7682425,5096294,5096286,28711033,28711009,13076795,13076825) \
OR PID IN (17038502,17038511,13106660,9980903,18361285,15212122,15212092,15212114,24379697,17038553,16984145,16984137,11397501,11812478) \
OR PID IN (28380151,3215326,8681911,28384024,28384032,15051056,9710230,34952391,9713778,9713743,9712658,9550151,9710264,9549234,2976323) \
OR PID IN (7973284,24650609,24671916,24651923,3496121,2111535,5183201,9392408,9390839,9008578,9392823,9392793,10157549,3441571,4403363) \
OR PIN IN (7409551,7267670,4788310,4788440,2489170,2489200,9537510,8749040,8954270,4728570,8107190,90006370,4121240,35033361,125770) \
OR PIN IN (518371,524811,457940,460200,460330,16685,166691,166431,167211,167051,457940,166851,522701,34952391,713380,171470,162590)"

# print(where_clauseIR)

tempLayer = "temppm"
arcpy.management.MakeFeatureLayer(inLayer, tempLayer)
arcpy.management.SelectLayerByAttribute(tempLayer, 'NEW_SELECTION', where_clause)
count = arcpy.management.GetCount(tempLayer)
print (f"Selected {count} features.")
arcpy.management.SelectLayerByAttribute(tempLayer, 'REMOVE_FROM_SELECTION', where_clauseIR)
count = arcpy.management.GetCount(tempLayer)
print (f"Selected {count} features.") 

arcpy.management.CopyFeatures(tempLayer, outLayer)
if arcpy.Exists(outLayer):
    print(outLayer + " created")
else:
    print(outLayer + " not created")
# arcpy.analysis.Select(inLayer, outLayer, where_clause)

arcpy.management.AddIndex(outLayer, ["PID"], "PIDIndex","UNIQUE", "NON_ASCENDING")
print("Index PIDIndex added to " + outLayer)

# Erase Indian Reserves, BC Parks and Ecoreserves, National Parks

irLayer = r'C:\working\GISdata\BCGW\ADM_INDIAN_RESERVES_BANDS_SP.gdb/WHSE_ADMIN_BOUNDARIES_ADM_INDIAN_RESERVES_BANDS_SP'
bcpaLayer = r'C:\working\GISdata\BCGW\TA_PARK_ECORES_PA_SVW.gdb\WHSE_TANTALIS_TA_PARK_ECORES_PA_SVW'
canpaLayer = r'C:\working\GISdata\BCGW\CLAB_NATIONAL_PARKS.gdb\WHSE_ADMIN_BOUNDARIES_CLAB_NATIONAL_PARKS'

noirLayer = outLayer + "_NoIR"
nobcpaLayer = noirLayer + "BCPA"
nocpaLayer = outLayer + "_20260118"
arcpy.analysis.PairwiseErase(outLayer,irLayer,noirLayer)
print(noirLayer + " Created")
arcpy.analysis.PairwiseErase(noirLayer,bcpaLayer,nobcpaLayer)
print(nobcpaLayer + " Created")
arcpy.analysis.PairwiseErase(nobcpaLayer,canpaLayer,nocpaLayer)
print(nocpaLayer + " Created")

arcpy.management.AddIndex(nocpaLayer, ["PID"], "PIDIndex","UNIQUE", "NON_ASCENDING")
print("Index PIDIndex added to " + nocpaLayer)
print("Done")