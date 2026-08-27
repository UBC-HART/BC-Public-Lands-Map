'''
AppendRD.py
- Appends together the output of JoinRDTables to create single layer for a Regional District.
- Many other data layers are then joined to the RD Public Land layer to evaluate housing suitability.
- Requires that the utility file FunctionUtils.py is present in the same folder.
- Inputs:
        RD name and initials ("RDinit")
        <RDinit>_Bndry: input polygon layer with RD boundary and Jurisdictional Boundaries


- Outputs: 
        Public_<RD>,  Small_<RD>, Large_<RD>,Park_<RD>, School_<RD>, Hospital_<RD>, Cemetery_<RD>, Marina_<RD>, FerryTerminal_<RD>,
        Utilities_<RD>, ALR_<RD>, LandChar_<RD>, Vacant_<RD>, Underutilized_<RD>

Ian Parfitt  27 Aug 2026
'''

import arcpy
import os

from arcpy.sa import *

from FunctionUtils import create_centroid, runSAM, runER, runDA, remapAppend,runOCPZone,runSoil,runRiparian,merge_native_land, runDensity, fireThreat


arcpy.env.overwriteOutput = True

#Set working directories and gdbs
Workdir = r'C:\working\ArcProjects\workspace'
ScratchWksp = r'C:\working\ArcProjects\scratch\scratchworkspace.gdb'
# Update for RD
RDinit = 'CCRD'
Workgdb = RDinit + 'PubJune.gdb'
outGDB = os.path.join(Workdir, Workgdb)

if not arcpy.Exists(outGDB):
    arcpy.management.CreateFileGDB(Workdir, Workgdb)
    print (outGDB + " created")

arcpy.env.workspace = outGDB
arcpy.env.scratchWorkspace = ScratchWksp

#Update for RD
RD = 'Central Coast'

descFC = r'C:\working\GISdata\BCA\BCASpatial\Data\bca_spatial_20260109.gdb\Descriptions' 
descLyr = "desc_lyr"
descRDJCFC = r'C:\working\GISdata\BCA\BCASpatial\Data\bca_spatial_20260109.gdb\Desc_RD_Juris_Dissolve' 

outLayer = RDinit + "_Bndry"
RDbndLayer = outLayer

# print(where_clause)
arcpy.env.extent = descFC
descdisFlds = ["REGIONAL_DISTRICT", "JURISDICTION_CODE", "JURISDICTION"]

if not arcpy.Exists(descRDJCFC):
    arcpy.analysis.PairwiseDissolve(descFC, descRDJCFC, descdisFlds)
    print(descRDJCFC + " created")

RDJurisIndex = "RDJurisIndex"
found_RDJurisIndex = False
indexes = arcpy.ListIndexes(descRDJCFC)
for index in indexes:
    if index.name == RDJurisIndex:
        found_RDJurisIndex = True
        break
if not found_RDJurisIndex:
    arcpy.management.AddIndex(descRDJCFC, descdisFlds, RDJurisIndex,"UNIQUE", "NON_ASCENDING")
    print("Index " + RDJurisIndex + " added to " + descRDJCFC)          

descRDFld = "REGIONAL_DISTRICT"

where_clause = f"{descRDFld} = \'{RD}\'"
print(where_clause)

arcpy.env.extent = descFC #RDLayer
arcpy.management.MakeFeatureLayer(descRDJCFC, descLyr)
arcpy.management.SelectLayerByAttribute(descLyr, "CLEAR_SELECTION")
arcpy.management.SelectLayerByAttribute(descLyr, 'NEW_SELECTION', where_clause)

#Start cursor loop. Jurisdiction is selected, and loop runs unless jurisdiction is one of those removed during the joining phase.
# outLayer = can change here to run one jurisdiction etc

# Create an empty list to store the field values
field_values = []

spurjur = ''   # spurious jurisdictions 
# Use a SearchCursor to iterate through rows and get field values
# Optionally can exclude jurisdictions.
with arcpy.da.SearchCursor(descLyr, [descdisFlds]) as cursor:
    for row in cursor:
        # if not row[0] in ('403','727','746','769','736','739'):  # exclude spurious jurisdictions
        if RDinit == 'CVRD':
            spurjur = '446'
        if not row[1] in (spurjur):  # exclude spurious jurisdictions using spurjur variable
            field_values.append(row[1]) 
del cursor

print(field_values)


# To get a list of unique values (optional)
unique_values = sorted(list(set(field_values)))
print (unique_values)
# unique_values = [''] - Use for running a single JC


for type in ['Public_', 'Vacant_', 'UnderUtilized_', 'Cemetery_','Park_','School_','Small_', 'Large_', 'Marina_','FerryTerminal_','Hospital_', 'ALR_', 'Utilities_', 'LandChar_']:
    incID = 1
    jcList = []
    outRDType = type + RDinit
    
    for value in unique_values:
        inLayer = type + str(value)
        if not arcpy.Exists(inLayer):
            print(inLayer + " does not exist")
        else:
            meanField = "MEAN"
            # print(arcpy.ListFields(inLayer, meanField))
            if arcpy.ListFields(inLayer, meanField) == 'None':
                arcpy.management.AddField(inLayer, meanField, "DOUBLE")
                print(meanField + " added to " + inLayer)
            # print(inLayer)
            if incID < 2:
                # print(str(incID))
                if arcpy.Exists(outRDType):
                    arcpy.Delete_management(outRDType)
                    print(outRDType + " deleted") 
                if not arcpy.Exists(outRDType):
                    arcpy.management.CopyFeatures(inLayer,outRDType)
                    print(outRDType + " created")
                incID += 1
            else:
                # meanField = "Mean"
                if not arcpy.Exists(inLayer):
                    print(inLayer + " does not exist")
                else:
                    jcList.append(inLayer)
                    # print(jcList)
                    incID += 1
                    # print(str(incID))
                    fieldMappings=remapAppend(outRDType,inLayer)
                    arcpy.management.Append(inLayer, outRDType, "NO_TEST", fieldMappings)
    print(outRDType + " created")


# Create centroids with PID_int field
RDpubFC = "Public_" + RDinit
# centroidFC = "MVRD_centroid"

centroidFC = create_centroid(RDinit,RDpubFC)

# Add SAM values for centroids, join to Public Land polygons
SAMFC = runSAM(RDinit,centroidFC)

ourSAMFieldJoin = ['walk_caf','walk_ccf','walk_ef','walk_emp','walk_hf', 'walk_psef','walk_srf','walk_gs_1','walk_gs_3','walk_gs_5', \
                        'transit_caf','transit_ccf','transit_ef','transit_emp','transit_hf', 'transit_psef','transit_srf','transit_gs_1','transit_gs_3','transit_gs_5'] 
pidField = "PID_NUMBER"
valueField = "VALUE"
pidIntField = "PID_int"
zPIDIndex = "PIDx" + RDinit
found_zPIDIndex = False
indexes = arcpy.ListIndexes(SAMFC)
for index in indexes:
    if index.name == zPIDIndex:
        found_zPIDIndex = True
        break
if not found_zPIDIndex:
    arcpy.management.AddIndex(SAMFC, pidIntField, zPIDIndex,"UNIQUE", "NON_ASCENDING")
arcpy.management.JoinField(RDpubFC, pidIntField, SAMFC, pidIntField, ourSAMFieldJoin)

# Calc NEAR values for Pharmacies
inputpharmaFC = r'C:\working\GISdata\BCGW\GSR_PHARMACIES_SV.gdb\WHSE_IMAGERY_AND_BASE_MAPS_GSR_PHARMACIES_SV'
arcpy.analysis.Near(RDpubFC,inputpharmaFC)
inFldname = "NEAR_DIST"
outFldname = "Pharmacy_Dist"
arcpy.management.AlterField(RDpubFC,
                             inFldname,
                             outFldname,
                             outFldname)
print("Near calculated to pharmacies")
arcpy.management.DeleteField(RDpubFC, "NEAR_FID")

# Calc NEAR values for Parks
inputparksFC = r'C:\working\GISdata\Parks\Parks.gdb\All_Parks'
arcpy.analysis.Near(RDpubFC,inputparksFC)
inFldname = "NEAR_DIST"
outFldname = "Parks_Dist"
arcpy.management.AlterField(RDpubFC,
                             inFldname,
                             outFldname,
                             outFldname)
print("Near calculated to parks")
arcpy.management.DeleteField(RDpubFC,"NEAR_FID")

# Calc NEAR values for water mains
inputwaterFC = r'C:\working\GISdata\ICIS\202602\Infrastructure_Mains.gdb\WATER_DISTRIBUTION'
arcpy.analysis.Near(RDpubFC,inputwaterFC)
inFldname = "NEAR_DIST"
outFldname = "WaterMain_Dist"
arcpy.management.AlterField(RDpubFC,
                             inFldname,
                             outFldname,
                             outFldname)
print("Near calculated to water mains")
arcpy.management.DeleteField(RDpubFC, "NEAR_FID")

# Calc NEAR values for BC Hydro Electrical
inputhydroFC = r'C:\working\GISdata\ICIS\202602\BCHydro.gdb\BCHydroPrimary'
arcpy.analysis.Near(RDpubFC,inputhydroFC)
inFldname = "NEAR_DIST"
outFldname = "BCHydroPrimary_Dist"
arcpy.management.AlterField(RDpubFC,
                             inFldname,
                             outFldname,
                             outFldname)
print("Near calculated to BC Hydro Primary")
arcpy.management.DeleteField(RDpubFC,"NEAR_FID")

# Calc NEAR values for roads
inputroadFC = r'C:\working\GISdata\DMTI\BC\Streets\BCrte.shp'
arcpy.analysis.Near(RDpubFC,inputroadFC)
inFldname = "NEAR_DIST"
outFldname = "Road_Dist"
arcpy.management.AlterField(RDpubFC,
                             inFldname,
                             outFldname,
                             outFldname)
print("Near calculated to roads")
arcpy.management.DeleteField(RDpubFC,"NEAR_FID")

# Calc Centroid NEAR values for roads
inputroadFC = r'C:\working\GISdata\DMTI\BC\Streets\BCrte.shp'
pubcentroidFC = RDinit + "_centroid"
if not arcpy.ListFields(pubcentroidFC, "Centroid_Road_Dist"):
    arcpy.analysis.Near(pubcentroidFC,inputroadFC)
    inFldname = "NEAR_DIST"
    outFldname = "Centroid_Road_Dist"
    arcpy.management.AlterField(pubcentroidFC,
                                inFldname,
                                outFldname,
                                outFldname)
    print("Near calculated to from parcel centroid to roads")
    arcpy.management.DeleteField(pubcentroidFC,"NEAR_FID")
JoinField = "PID_int"
arcpy.management.JoinField(RDpubFC, JoinField, pubcentroidFC, JoinField, [outFldname])



# Calc NEAR values for transit stops
inputtransitFC = r'C:\working\GISdata\GTFS\CanadaPubTransport.gdb\BC_mainStops_alb'
arcpy.analysis.Near(RDpubFC,inputtransitFC)
inFldname = "NEAR_DIST"
outFldname = "Transit_Dist"
arcpy.management.AlterField(RDpubFC,
                             inFldname,
                             outFldname,
                             outFldname)
print("Near calculated to transit stops")
arcpy.management.DeleteField(RDpubFC,"NEAR_FID")

#Identify OCP and Zoning info, join to polys
zoneOCPFC = runOCPZone(RDinit, centroidFC)
inFldname = "ICI_OCP_CLASS"
outFldname = "ICI_OCP_Class" 

arcpy.management.AlterField(zoneOCPFC,
                             inFldname,
                             outFldname,
                             outFldname)

ourzoneOCPFieldJoin = ['General_Zone', outFldname]
pidField = "PID_NUMBER"
valueField = "VALUE"
pidIntField = "PID_int"
zPIDIndex = "PIDx" + RDinit
found_zPIDIndex = False
indexes = arcpy.ListIndexes(zoneOCPFC)
for index in indexes:
    if index.name == zPIDIndex:
        found_zPIDIndex = True
        break
if not found_zPIDIndex:
    arcpy.management.AddIndex(zoneOCPFC, pidIntField, zPIDIndex,"UNIQUE", "NON_ASCENDING")
arcpy.management.JoinField(RDpubFC, pidIntField, zoneOCPFC, pidIntField, ourzoneOCPFieldJoin)

# Run Development Areas
print("Run Dev Areas")
RDpubFC = "Public_" + RDinit
DAFC = runDA(RDinit, RDpubFC)

ourDAFieldJoin = ['TOA_Tier','MTGA','UrbanCentre'] 
pidField = "PID_NUMBER"
valueField = "VALUE"
pidIntField = "PID_int"
zPIDIndex = "PIDx" + RDinit
found_zPIDIndex = False
indexes = arcpy.ListIndexes(DAFC)
for index in indexes:
    if index.name == zPIDIndex:
        found_zPIDIndex = True
        break
if not found_zPIDIndex:
    arcpy.management.AddIndex(DAFC, pidIntField, zPIDIndex,"UNIQUE", "NON_ASCENDING")
arcpy.management.JoinField(RDpubFC, pidIntField, DAFC, pidIntField, ourDAFieldJoin)

#Soil Drainage -run function, join to polys
soilFC = runSoil(RDinit, centroidFC)

soilfldname = "DrainageClass"
oursoilfldJoin = [soilfldname]
pidIntField = "PID_int"
zPIDIndex = "PIDx" + RDinit
found_zPIDIndex = False
indexes = arcpy.ListIndexes(soilFC)
for index in indexes:
    if index.name == zPIDIndex:
        found_zPIDIndex = True
        break
if not found_zPIDIndex:
    arcpy.management.AddIndex(soilFC, pidIntField, zPIDIndex,"UNIQUE", "NON_ASCENDING")
arcpy.management.JoinField(RDpubFC, pidIntField, soilFC, pidIntField, oursoilfldJoin)
print("Soil Drainage joined")

# Run Environmental Remediation for polygons
RDpubFC = "Public_" + RDinit
ERFC = runER(RDinit, RDpubFC)

ourERFieldJoin = ['ENV_RMDTN_SITES_ID','SITE_BY_RE'] 
pidField = "PID_NUMBER"
valueField = "VALUE"
pidIntField = "PID_int"
zPIDIndex = "PIDx" + RDinit
found_zPIDIndex = False
indexes = arcpy.ListIndexes(ERFC)
for index in indexes:
    if index.name == zPIDIndex:
        found_zPIDIndex = True
        break
if not found_zPIDIndex:
    arcpy.management.AddIndex(ERFC, pidIntField, zPIDIndex,"UNIQUE", "NON_ASCENDING")
arcpy.management.JoinField(RDpubFC, pidIntField, ERFC, pidIntField, ourERFieldJoin) 
print("Environmediation Joined")

# Riparian
RDpubriparian = "Riparian_" + RDinit
riparianFC =  runRiparian(RDinit, RDpubFC)

ourriparianFieldJoin = ['Riparian'] 
pidIntField = "PID_int"
zPIDIndex = "PIDx" + RDinit
found_zPIDIndex = False
indexes = arcpy.ListIndexes(riparianFC)
for index in indexes:
    if index.name == zPIDIndex:
        found_zPIDIndex = True
        break
if not found_zPIDIndex:
    arcpy.management.AddIndex(riparianFC, pidIntField, zPIDIndex,"UNIQUE", "NON_ASCENDING")
arcpy.management.JoinField(RDpubFC, pidIntField, riparianFC, pidIntField, ourriparianFieldJoin) 
print("Riparian Joined")

# Identify sites in Heritage Registry and join to polys
outFC = RDinit + "_heritage"
inHeritageFC = r'C:\working\GISdata\BCGW\HIST_HISTORIC_ENVIRONMNT_PA_SV.gdb/WHSE_HUMAN_CULTURAL_ECONOMIC_HIST_HISTORIC_ENVIRONMNT_PA_SV'
inFldname = "RECOGNITION_TYPE"
outFldname = "Heritage_Type" 

arcpy.analysis.SpatialJoin(
        target_features=centroidFC,
        join_features=inHeritageFC,
        out_feature_class=outFC,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        field_mapping="",
        match_option="INTERSECT")
print("Spatial Join for " + outFC + " complete") 

arcpy.management.AlterField(outFC,
                             inFldname,
                             outFldname,
                             outFldname)

ourheritageFieldJoin = outFldname
pidField = "PID_NUMBER"
valueField = "VALUE"
pidIntField = "PID_int"
zPIDIndex = "PIDx" + RDinit
found_zPIDIndex = False
indexes = arcpy.ListIndexes(outFC)
for index in indexes:
    if index.name == zPIDIndex:
        found_zPIDIndex = True
        break
if not found_zPIDIndex:
    arcpy.management.AddIndex(outFC, pidIntField, zPIDIndex,"UNIQUE", "NON_ASCENDING")
arcpy.management.JoinField(RDpubFC, pidIntField, outFC, pidIntField, ourheritageFieldJoin)
print("Heritage Data Joined")


#Flood risk: extract to centroids, join to polys
outFC = RDinit + "_floodrisk"
infloodRas = r'C:\working\GISdata\NRCan\FS-national-2015-class.tif'
inFldname = "RASTERVALU"
outFldname = "Flood_Risk" 

ExtractValuesToPoints(centroidFC, infloodRas, outFC)
print("Extract flood risk values to " + outFC + " complete")
arcpy.management.AlterField(outFC,
                             inFldname,
                             outFldname,
                             outFldname)

ourfloodFieldJoin = outFldname
pidField = "PID_NUMBER"
valueField = "VALUE"
pidIntField = "PID_int"
zPIDIndex = "PIDx" + RDinit
found_zPIDIndex = False
indexes = arcpy.ListIndexes(outFC)
for index in indexes:
    if index.name == zPIDIndex:
        found_zPIDIndex = True
        break
if not found_zPIDIndex:
    arcpy.management.AddIndex(outFC, pidIntField, zPIDIndex,"UNIQUE", "NON_ASCENDING")
arcpy.management.JoinField(RDpubFC, pidIntField, outFC, pidIntField, ourfloodFieldJoin)

print("Flood risk joined")

#Fire Risk
firethreatFC = fireThreat(RDinit, centroidFC)
inFldname = "FIRE_THREAT_CLASS_DESC"
outFldname = "Fire_Risk"
arcpy.management.AlterField(firethreatFC,
                             inFldname,
                             outFldname,
                             outFldname)

ourfireFieldJoin = outFldname
pidIntField = "PID_int"
zPIDIndex = "PIDx" + RDinit
found_zPIDIndex = False
indexes = arcpy.ListIndexes(firethreatFC)
for index in indexes:
    if index.name == zPIDIndex:
        found_zPIDIndex = True
        break
if not found_zPIDIndex:
    arcpy.management.AddIndex(firethreatFC, pidIntField, zPIDIndex,"UNIQUE", "NON_ASCENDING")
arcpy.management.JoinField(RDpubFC, pidIntField, firethreatFC, pidIntField, ourfireFieldJoin)
print("Fire Threat Joined")

#Join First Nation Territories
fnterritoriesFC = merge_native_land(RDpubFC)
print("First Nations Joined") 

# Join Dwelling Density 
densityFC = runDensity(RDinit, RDpubFC)
ourdensityFieldJoin = ["Existing_Density","Max_Density", "Median_Density"] 
pidIntField = "PID_int"
zPIDIndex = "PIDx" + RDinit
found_zPIDIndex = False
indexes = arcpy.ListIndexes(densityFC)
for index in indexes:
    if index.name == zPIDIndex:
        found_zPIDIndex = True
        break
if not found_zPIDIndex:
    arcpy.management.AddIndex(densityFC, pidIntField, zPIDIndex,"UNIQUE", "NON_ASCENDING")
arcpy.management.JoinField(RDpubFC, pidIntField, densityFC, pidIntField, ourdensityFieldJoin) 
print("Dwelling Density Joined")

#Development Density: extract to centroids, join to polys
outFC = RDinit + "_devDensity"
indevRas = r'C:\working\GISdata\DevDensity\DevDensity.gdb\KernelD_Lega1'
inFldname = "RASTERVALU"
outFldname = "RecentDevIndex" 

ExtractValuesToPoints(centroidFC, indevRas, outFC)
print("Extract recent development index values to " + outFC + " complete")
arcpy.management.AlterField(outFC,
                             inFldname,
                             outFldname,
                             outFldname)

ourdevdenseFieldJoin = outFldname
pidIntField = "PID_int"
zPIDIndex = "PIDx" + RDinit
found_zPIDIndex = False
indexes = arcpy.ListIndexes(outFC)
for index in indexes:
    if index.name == zPIDIndex:
        found_zPIDIndex = True
        break
if not found_zPIDIndex:
    arcpy.management.AddIndex(outFC, pidIntField, zPIDIndex,"UNIQUE", "NON_ASCENDING")
arcpy.management.JoinField(RDpubFC, pidIntField, outFC, pidIntField, ourdevdenseFieldJoin)

print("Development density joined")
        
print("Done")
