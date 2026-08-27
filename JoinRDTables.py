'''
JoinRDTables.py
- Note that two utility files, JoinUtil.py and FunctionUtils.py are used by this code and must be present in the 
same folder when this file is run.  Note also that the GDB for each Regional District needs to be updated in the FunctionUtil before it is run.
Selects Regional District from provincial local gov poly layer
- Uses this to find all jurisdictions within RD, then sets a cursor to create separate layers by juridiction code
- Jurisdictions were removed if they comprise First Nation reserves. 
- The code allows for overwriting the list of jurisdictions created for a given RD so that individual or groups of jurisdictions can be run.
- Legal descriptions created first and joined (using PID) to the public land layer created from ParcelMap data.
- Records with null ownertype (i.e. legal polys with no matching PIDs in the public land layer) deleted.
- A dissolve of the legal200 layer (Vancouver City legal layer) showed that dissolving by roll number or folio_id results in the same number of features, which strongly indicates
that these two fields are interchangeable.  As a result, the public land legal layer join was dissolved by folio_id to join adjacent polys
- This layer becomes the core layer: other BCA poly layers for each jurisdiction are then joined on Folio_ID.
- Most of the join code was moved to a utility (JoinUtil.py).  This utility file must exist in the same folder as this file.
- The jurisdictions are divided into BCA assessment areas (AA). The JoinUtil file lists the correct AA file for each jurisdiction.
- Some fields were modified using functions in a second utility file (FunctionUtils.py):
       Overlapping polys indicate multiple units within a given property parcel. Land value and improvement value fields were summed to provide overal property values.
       Polys can have up to 6 Land Characteristics fields.  For simplicity, these were merged into a single field.

After joining, unsuitable polygons are removed based on size, shape, current land use, ALR, Land Characteristics
  Size: 
        Small = under 100m2 or circularity less than or equal to 0.25 (circularity is a measure of how long and thin a polygon is, see Methodology)
        Large = over 50000m2   
  Use: 
        ACTUAL_LAND_USE field is used to exclude uses including hospitals, schools, cemeteries, electrical utilities, ferry terminal and marina land uses are copied to their own layers and then deleted from the joined jurisdicion public land layer
        ACTUAL_LAND_USE does a poor job of identifying parks so a DATABC parks layer used as well.  An example using PIDs (for Vancouver) used as an example of further refining that could be done.
        ALR_CODE field used to remove Agricultural Land Reserve polys
  Land Characteristics:
       Values "91","C1","C2","C3","C4","F2","R4","R5" removed.

- A zonal statistics function in FunctionUtils.py calculates the mean slope of each parcel.
- A zonal geometry function in FunctionUtils.py calculates the thickness (largest internal circle)
- ratio of total improvement value divided by total land value calculated
- repeated field names from the BCA joins deleted.

Remember to update the GDB in FunctionUtils for each RD run!

Ian Parfitt  August 27 2026
'''

import arcpy
import os

from JoinUtil import joinit
from FunctionUtils import zonalStatMean, geoMeasures


arcpy.env.overwriteOutput = True

# Set RD initials
RDinit = "NRRM"
# Set working directories and gdbs
Workdir = r'C:\working\ArcProjects\workspace'
ScratchWksp = r'C:\working\ArcProjects\scratch\scratchworkspace.gdb'
# Update for RD (also remember to update FunctionUtil)
Workgdb = RDinit + 'PubJune.gdb'
outGDB = os.path.join(Workdir, Workgdb)
#update for RD 
DEMWksp = r'C:\working\GISdata\LidarBC'
DEMGDB = os.path.join(DEMWksp, RDinit)
#Specify SlopeGrid for the RD
SlopeGrid = RDinit + "_FinalSlp_alb.tif"  
if not arcpy.Exists(outGDB):
    arcpy.management.CreateFileGDB(Workdir, Workgdb)
    print (outGDB + " created")

arcpy.env.workspace = outGDB
arcpy.env.scratchWorkspace = ScratchWksp
print(arcpy.env.workspace)

# Dissolve BC Assessment Legal_Description layer to create a layer with jurisdictions.

legalFC = r'C:\working\GISdata\BCA\BCASpatial\Data\bca_spatial_20260109.gdb\Legal_Description' 
legalLyr = legalFC + "_lyr"
legaljurisFC = r'C:\working\GISdata\BCA\BCASpatial\Data\bca_spatial_20260109.gdb\Legal_Juris_Dissolve'  # Legal_Description dissolved on Jurisdiction Code and Jurisdiction

arcpy.env.extent = legalFC
arcpy.management.MakeFeatureLayer(legalFC, legalLyr)
# arcpy.management.SelectLayerByAttribute(legalLyr, "CLEAR_SELECTION")

if not arcpy.Exists(legaljurisFC):
    arcpy.analysis.PairwiseDissolve(legalLyr, legaljurisFC, ["JURISDICTION_CODE","JURISDICTION"]) # Did not work correctly - only MVRD areas in output - so resorted to doing in ArcPro where it worked fine.
    print("Legal_Description dissolved on JURISDICTION_CODE and JURISDICTION")

#Select Regional District from GeoBC local government layer, adds an index
RD = 'Northern Rockies Regional Municipality'
RD2 = 'Northern Rockies RM'

ADMINGroup = "ADMIN_AREA_GROUP_NAME"
ADMINName = "ADMIN_AREA_NAME"
# NRRM uses ADMINName

inFC = r'C:\working\GISdata\BCGW\ABMS_LGL_ADMIN_AREAS_SVW.gdb\WHSE_LEGAL_ADMIN_BOUNDARIES_ABMS_LGL_ADMIN_AREAS_SVW'
inLayer = inFC + "_lyr"
arcpy.management.MakeFeatureLayer(inFC, inLayer)
RDbndFC = RDinit + "_Bndry"
RDbndLyr = RDbndFC + "_lyr"

# NRRM uses ADMINName
where_clause = f'"{ADMINName}" = \'{RD}\''
# All RDs use ADMINGroup
where_clause = f'"{ADMINGroup}" = \'{RD}\''


# print(where_clause)

# if arcpy.Exists(outLayer):
#    arcpy.Delete_management(outLayer)

if not arcpy.Exists(RDbndFC):
    arcpy.env.extent = inFC
    arcpy.management.SelectLayerByAttribute(inLayer, 'CLEAR_SELECTION')
    arcpy.management.SelectLayerByAttribute(inLayer, 'NEW_SELECTION', where_clause)
    arcpy.management.CopyFeatures(inLayer, RDbndFC)
    print(RDbndFC + " created")
    arcpy.management.MakeFeatureLayer(RDbndFC, RDbndLyr)

arcpy.env.extent = RDbndFC

outLayer = RDinit + "_Juris"
#if arcpy.Exists(outLayer):
#    arcpy.Delete_management(outLayer)
#    print(outLayer + " deleted")
if not arcpy.Exists(outLayer):
    arcpy.analysis.PairwiseClip(legaljurisFC, RDbndFC, outLayer)
    print(outLayer + " created")

JurisIndex = "JurisIndex"
found_JurisIndex = False
indexes = arcpy.ListIndexes(outLayer)
for index in indexes:
    if index.name == JurisIndex:
        found_JurisIndex = True
        break
JURISCode = "JURISDICTION_CODE"    
if not found_JurisIndex:
    arcpy.management.AddIndex(outLayer, JURISCode, "JurisIndex","UNIQUE", "NON_ASCENDING")
    print("Index JurisIndex added to " + outLayer)

outTab = RDinit + "_legaljurisLUT"
# if arcpy.Exists(outTab):
#    arcpy.Delete_management(outTab)
if not arcpy.Exists(outTab):
    arcpy.analysis.Statistics(outLayer, outTab, [["Shape_area", "SUM"]], JURISCode)

ADMINGroup = "ADMIN_AREA_GROUP_NAME"
ADMINName = "ADMIN_AREA_NAME"
ADMINAbrev = "ADMIN_AREA_ABBREVIATION"
JURISCode = "JURISDICTION_CODE"
JURIS = "JURISDICTION"
Layer_fields = [JURISCode]

arcpy.env.extent = RDbndFC

# Select Regional District from dissolved Description layer - this provides a list of 
# Jurisdictions by RD that doesn't have the boundary problems caused by clipping the legal layer.

RDjurisFC = r'C:\working\GISdata\BCA\BCASpatial\Data\bca_spatial_20260109.gdb\Desc_RD_Juris_Dissolve'
RDjurisLyr = "RDjurisLayer"
where_clause = f"REGIONAL_DISTRICT = '{RD2}'"

arcpy.management.MakeFeatureLayer(RDjurisFC, RDjurisLyr,where_clause)

# *****  Start JURISDICTION cursor loop. Jurisdiction is selected, and loop runs unless jurisdiction is an electoral area. ****
# As each Regional District is run, list of jurisdictions and anomalies will be noted below

print("Create Jurisdiction list")
# NOTE: JURISDICTION_CODE (jc) is a string
# outLayer = can change here to run one jurisdiction etc

# Create an empty list to store the field values
field_values = []

# Use a SearchCursor to iterate through rows and get field values
with arcpy.da.SearchCursor(RDjurisLyr, [Layer_fields]) as cursor:
    for row in cursor:
        field_values.append(row[0]) 
del cursor

print(field_values)   # Quoted list of all Jurisdictions

# Sorted unique valies 
unique_values = sorted(list(set(field_values)))
print (unique_values)

# MVRD unique_values = ['200','236','225','216', '220', '221', '224','301', '305', '306', '311', '312','313', '314','316','319','320','321','326', '328','501', '504', '537', '631','742', '743', '744', '745', '748']
#  note - one parcel with 727 jurisdiction code is an error - record refers to a poly in William's Lake (Roll Number 45402390)
#  note - one parcel with overlapping polys in several jurisdictions including Sechelt Rural '746'and Alberni Rural '769' for a submarine cable
#  note - '403' is Tsawassen First Nation, removed.
#  note - '736' and '739' Lower Mainland Rural have no polys left after removing IRs, regional parks, ALR, small polys.  Removed.
# CRD unique_values = ['213', '234', '302', '307', '308', '309', '315', '317', '327', '332', '344', '349', '361', '362', '389', '401','402','476', '761', '762', '763', '764']
#  note - '336' removed - has one spurious diamond poly in Legal_336 (Campbell River) has one feature that doesn't persist into Pub_336 although the empty feature class doesn't fail until feature to raster
#  note - '363' removed - only exists in Legal Description as 8 polygons.
#  note - '402' removed - only exists in Legal Description as 23 polygons.
#  note - '415' removed - 263 polygons 	Laxgalts'ap , most on Nass River except some near Victoria
#  note - '765' and '766' removed - Actually north of the CRD
# CVRD unique_values = ['207', '315', '445', '446', '539', '765', '766', '768']
# note - 446 no polys left after large and ALR polys removed
# RDOS unique_values = ['222', '325', '535', '555', '556', '562', '714', '715', '716','717', '777'] 
# SCRD unique_values = ['524', '570', '746']
# Note '346' removed - Sechelt Indian Lands
# RDN unique_values = ['250', '350', '351', '559', '565', '768', '769']
# RDAC unique_values = ['223', '580', '583', '770']
# Note '404' Toquiat first nation, removed.
# Note '405' Ucluelet first nation, removed.
# Note '406' Uchucklesaht Tribe, removed.
# Note '408' Huu-ay-aht  First Nation, removed.
# CZRD unique values = ['204', '412', '516', '771']
# SRD unique_values = ['336', '526', '571', '575', '592', '772', '784']
# Note '409', Ka:'yu:k't'h/Che:kt'les7et'h' First Nation, removed.
# MWRD unique values = ['334', '502', '558', '563', '784', '785']
# FVRD unique_values = ['303', '310', '313', '314', '432', '527', '732', '733', '734', '742', '775', '776']
# RDKB unique_values = ['210', '211', '229', '232', '521', '547', '548', '588', '711', '712', '713']
# RDCK unique_values = ['201', '219', '413', '533', '551', '553', '569', '572', '573', '707', '709', '710', '786']
# RDEK unique_values = ['205', '209', '215', '337', '517', '532', '567', '568', '701', '702', '703', '704']
# SLRD unique_values = ['338', '390', '540', '560', '729', '748']
# RDNO unique_values = ['202', '208', '233', '304', '323', '541', '722', '789']
# CCRD unique_values = ['749']
# PRRD unique_values = ['206', '333', '343', '420', '514', '561', '577', '759', '760']
# NRRM unique_values = ['255']

# list of unique values to run manually (overwrites list created above):
# unique_values = []

for value in unique_values:
    print(value)
    jc = value
    jcn = int(value)
    

    # Run the joinit function from the JoinUtil.py 
    disLayer = joinit(jc, RDinit)
    print(disLayer + " all joined up")

    # Create a copy of output joined polygon and then start removing parcels by size, shape, current use, land characteristics
    reducedLayer = "rePub_" + jc
    tempLayer = "tempLayer"
    arcpy.management.CopyFeatures(disLayer, reducedLayer)
    feature_count = arcpy.management.GetCount(reducedLayer).getOutput(0)
    print(f"The feature class '{reducedLayer}' contains {feature_count} features.")
    arcpy.management.MakeFeatureLayer(reducedLayer, tempLayer)
    print("feature layer " + reducedLayer + " created")    

    # If necessary, use to remove problematic values
    # JC 501: delete poly with PID 13196804 - its a water poly far from the rest of the JC (village of Anmore)
    if jc == '501':
        outlierLayer = "Outlier_" + jc
        pidField = "PID_NUMBER"
        PIDvalue = 13196804
        where_clause = f"{pidField} = {PIDvalue}"   
        arcpy.management.SelectLayerByAttribute(tempLayer,"NEW_SELECTION", where_clause)
        if arcpy.Describe(tempLayer).FIDSet:
            if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
                arcpy.management.CopyFeatures(tempLayer, outlierLayer)
                arcpy.management.DeleteFeatures(tempLayer)
                print(outlierLayer + " created")            

    # Remove parcels lt 100m2 or circularity lt eq .25

    # Calculate Circularity Ratio
    GDBarea_field_name = "Shape_Area"
    GDBlength_field_name = "Shape_Length"
    GDBcircularity_field_name = "Shape_Circularity"
    
    arcpy.management.AddFields(tempLayer, [
            [GDBcircularity_field_name, "DOUBLE"] 
        ])

    expression = f"(4 * math.pi * !{GDBarea_field_name}!) / (!{GDBlength_field_name}!**2)"
    arcpy.management.CalculateField(tempLayer, GDBcircularity_field_name, expression, "PYTHON3", '')
    print("Circularity Ratio calculated")

    # Remove small polygons
    smallLayer = "Small_" + jc
    areaField = "Shape_Area"
    area_threshold_value = 100
    circ_threshold_value = 0.25
    where_clause = f"{areaField} < {area_threshold_value} or {GDBcircularity_field_name} <= {circ_threshold_value} "   
    arcpy.management.SelectLayerByAttribute(tempLayer,"NEW_SELECTION", where_clause)
    if arcpy.Describe(tempLayer).FIDSet:
        if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
            arcpy.management.CopyFeatures(tempLayer, smallLayer)
            arcpy.management.DeleteFeatures(tempLayer)
            print(smallLayer + " created")

    # Remove large polygons
    largeLayer = "Large_" + jc
    areaField = "Shape_Area"
    area_threshold_value = 50000
    where_clause = f"{areaField} > {area_threshold_value} "   
    arcpy.management.SelectLayerByAttribute(tempLayer,"NEW_SELECTION", where_clause)
    if arcpy.Describe(tempLayer).FIDSet:
        if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
            arcpy.management.CopyFeatures(tempLayer, largeLayer)
            arcpy.management.DeleteFeatures(tempLayer)
            print(largeLayer + " created")


    # Remove specific land use types from public land layer & create separate layers for each
    UseField = "ACTUAL_USE_CODE"
    

    # Parks & Playing Fields
    parkLayer = "Park_" + jc

    # Use local and regional greenspace (parks and protected areas) to select parks & change ACTUAL USE fields
    inputLocalParkFC = r'C:\working\GISdata\BCGW\GBA_LOCAL_REG_GREENSPACES_SP.gdb\Local_Greenspace_Minus5'  # -5 buffer applied to layer above as many nonparks adjacent to parks were getting selected.
    arcpy.management.SelectLayerByLocation(tempLayer,'INTERSECT',inputLocalParkFC, '#','NEW_SELECTION')
    
    expression1 = "610"
    arcpy.management.CalculateField(tempLayer, UseField, expression1, "PYTHON3")

    expression2 = "'Parks & Playing Fields'"
    UseDescField = "ACTUAL_USE_DESCRIPTION"
    arcpy.management.CalculateField(tempLayer, UseDescField, expression2, "PYTHON3")

    
    # If necessary, use list of PIDs to select parks
    pidField = "PID_NUMBER"
    id_values = []
    csv_file = r'C:\working\ArcProjects\workspace\csvfiles\ParkPID_ 200_format_1Dec.csv'
    with open(csv_file, 'r') as f:
        numbers_str = f.readline().strip( )  # Read the single line and remove leading/trailing whitespace
        numbers_list = numbers_str.split(',')  # Split by comma

    # --- Format numbers for where_clause ---
    # Assuming 'ID_Field' is a numeric field. If it's a text field,
    # you would format it as: formatted_numbers = [f"'{num}'" for num in numbers_list]
    formatted_numbers = numbers_list    

    # --- Construct where_clause ---
    myseparator = ','
    where_clause = f'"{UseField}" = {610} OR "{pidField}" IN ({myseparator.join(formatted_numbers)[1:-1]})'
    where_clause = f"{UseField} = '{610}'"
    # print(f"Generated Where Clause: {where_clause}")
    
    # where_clause = f'"{UseField}" = {610} OR "{pidField}" IN {16622413,15849520,7971575,7971591,7971605,7971613,15393593,15393623,7971648,7971664,6588654,9537856,6984967,31792120,6931511,16209648,9669477,15043126,15490891,15490874,24371734,7025866,15978656,16010043,7068778,6577989,15093930,3948161,7755937,26054078,8348219,26251141,17796849,24656739}'
    print(where_clause)
    arcpy.management.SelectLayerByAttribute(tempLayer, "NEW_SELECTION", where_clause)
    if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
        arcpy.management.CopyFeatures(tempLayer, parkLayer)
        arcpy.management.DeleteFeatures(tempLayer)  
        print(parkLayer + " created")

    # Schools
    schoolLayer = "School_" + jc
    where_clause = f'"{UseField}" = {650}'
    where_clause = f"{UseField} = '{650}'"
    arcpy.management.SelectLayerByAttribute(tempLayer, "NEW_SELECTION", where_clause)
    if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
        arcpy.management.CopyFeatures(tempLayer, schoolLayer)
        arcpy.management.DeleteFeatures(tempLayer)
        print(schoolLayer + " created")

    # Hospitals
    hospitalLayer = "Hospital_" + jc
    where_clause = f'"{UseField}" = {640}'
    where_clause = f"{UseField} = '{640}'"
    arcpy.management.SelectLayerByAttribute(tempLayer, "NEW_SELECTION", where_clause)
    if arcpy.Describe(tempLayer).FIDSet:
        if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
            arcpy.management.CopyFeatures(tempLayer, hospitalLayer)
            arcpy.management.DeleteFeatures(tempLayer)
            print(hospitalLayer + " created")
                    
    # Cemeteries (Includes Public or Private).
    cemeLayer = "Cemetery_" + jc
    pidField = "PID_NUMBER"
    where_clause = f'"{UseField}" = {642} OR "{pidField}" IN {23231289, 23210117,14217309,14216868,14216965}'
    where_clause = f"{UseField} = '{642}'OR {pidField} IN {23231289, 23210117,14217309,14216868,14216965}"
    arcpy.management.SelectLayerByAttribute(tempLayer, "NEW_SELECTION", where_clause)
    if arcpy.Describe(tempLayer).FIDSet:
        if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
            arcpy.management.CopyFeatures(tempLayer, cemeLayer)
            arcpy.management.DeleteFeatures(tempLayer)
            print(cemeLayer + " created")

    # Marine Facilities (Marina)
    mariLayer = "Marina_" + jc
    pidField = "PID"
    where_clause = f'"{UseField}" = {280}'
    where_clause = f"{UseField} = '{280}'"
    arcpy.management.SelectLayerByAttribute(tempLayer, "NEW_SELECTION", where_clause)
    if arcpy.Describe(tempLayer).FIDSet:
        if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
            arcpy.management.CopyFeatures(tempLayer, mariLayer)
            arcpy.management.DeleteFeatures(tempLayer)
            print(mariLayer + " created")
    
    # Ferry Terminals   
    ferryLayer = "FerryTerminal_" + jc
    # where_clause = f'"{UseField}" = {505}'
    where_clause = f"{UseField} = '{505}'"
    arcpy.management.SelectLayerByAttribute(tempLayer, "NEW_SELECTION", where_clause)
    if arcpy.Describe(tempLayer).FIDSet:
        if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
            arcpy.management.CopyFeatures(tempLayer, ferryLayer)
            arcpy.management.DeleteFeatures(tempLayer)
            print(ferryLayer + " created")

    # Electrical Utilities (But not Gas?)
    utilLayer = "Utilities_" + jc
    pidField = "PID"
    where_clause = f'"{UseField}" = {580}'
    where_clause = f"{UseField} = '{580}'"
    arcpy.management.SelectLayerByAttribute(tempLayer, "NEW_SELECTION", where_clause)
    if arcpy.Describe(tempLayer).FIDSet:
        if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
            arcpy.management.CopyFeatures(tempLayer, utilLayer)
            arcpy.management.DeleteFeatures(tempLayer)
            print(utilLayer + " created")

    # Exclude parcels with unsuitable land characteristics
    landcharExclude = "LandChar_" + jc
    landcharField = "merge_Land_Character_Code"
    where_clause = f'{landcharField} IN {"91","C1","C2","C3","C4","F2","R4","R5"}'
    arcpy.management.SelectLayerByAttribute(tempLayer, "NEW_SELECTION", where_clause)
    if arcpy.Describe(tempLayer).FIDSet:
        if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
            arcpy.management.CopyFeatures(tempLayer, landcharExclude)
            arcpy.management.DeleteFeatures(tempLayer)
            print(landcharExclude + " created")
          
    # Exclude ALR parcels
    alrLayer = "ALR_" + jc
    alrField = "ALR_CODE"
    where_clause = f'{alrField} IN {"1","2","3","4"}'
    # print(where_clause)
    arcpy.management.SelectLayerByAttribute(tempLayer, "NEW_SELECTION", where_clause)
    if arcpy.Describe(tempLayer).FIDSet:
        if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
            arcpy.management.CopyFeatures(tempLayer, alrLayer)
            arcpy.management.DeleteFeatures(tempLayer)
            print(alrLayer + " created")

 
   
    # Calculate Zonal Slope Mean as table and join table
    inSlopeGrid = os.path.join(DEMGDB, SlopeGrid)
    if jc in  ("9999"):  # preventing Mean from running ("319","501","504","537")
        zoneField = "PID_int"
        sourceField = "PID_NUMBER"
        # expression = f"!{sourceField}!"
        arcpy.management.SelectLayerByAttribute(tempLayer, "CLEAR_SELECTION") 
        arcpy.management.AddField(tempLayer, zoneField, 'BIGINTEGER')
        print(zoneField + " added")
        expression = f"int(!{sourceField}!)"
        arcpy.management.CalculateField(tempLayer, zoneField, expression, "PYTHON3")
        # testmeLayer = "AA_" + jc
        # arcpy.management.CopyFeatures(tempLayer, testmeLayer)
        # print(testmeLayer + " created")
        zmeanTab = zonalStatMean(tempLayer,inSlopeGrid,jc)  
        print(zmeanTab + " created") 
        ourZoneMeanFieldJoin = ["MEAN"] 
        pidField = "PID_NUMBER"
        valueField = "VALUE"
        pidIntField = "PID_int"
        zPIDIndex = "PIDx" + jc
        found_zPIDIndex = False
        indexes = arcpy.ListIndexes(zmeanTab)
        for index in indexes:
            if index.name == zPIDIndex:
                found_zPIDIndex = True
                break
        if not found_zPIDIndex:
            arcpy.management.AddIndex(zmeanTab, valueField, zPIDIndex,"UNIQUE", "NON_ASCENDING")
        arcpy.management.JoinField(tempLayer, pidIntField, zmeanTab, valueField, ourZoneMeanFieldJoin)
    else:
        zoneField = "PID_int"
        sourceField = "PID_NUMBER"
        meanField = "MEAN"
        expression = f"!{sourceField}!"
        arcpy.management.SelectLayerByAttribute(tempLayer, "CLEAR_SELECTION") 
        arcpy.management.AddField(tempLayer, zoneField, 'BIGINTEGER')
        arcpy.management.CalculateField(tempLayer, zoneField, expression, "PYTHON3")
        arcpy.management.AddField(tempLayer, meanField, 'DOUBLE')


    # Calculate Geometry Measures as table and join table  
    geomeasureTab = "outgeoTab_" + jc
    if not arcpy.Exists(geomeasureTab):
        geomeasureTab = geoMeasures(tempLayer, jc)
        print(geomeasureTab + " returned now at main") 
    thicknessfieldJoin = ["THICKNESS"] 
    pidField = "PID_NUMBER"
    pidIntField = "VALUE"
    PIDIndex = "PIDx" + jc
    found_PIDIndex = False
    indexes = arcpy.ListIndexes(geomeasureTab)
    for index in indexes:
        if index.name == PIDIndex:
            found_PIDIndex = True
            break
    if not found_PIDIndex:
        arcpy.management.AddIndex(geomeasureTab, pidIntField, PIDIndex,"UNIQUE", "NON_ASCENDING")
        print("Index " + PIDIndex + " added")
    arcpy.management.JoinField(tempLayer, pidField, geomeasureTab, pidIntField, thicknessfieldJoin)
    print(geomeasureTab + " joined")

    # Identify Vacant Parcels: add Vacant field to use as flag
    vacField = "Vacant" 
    if not arcpy.ListFields(tempLayer, vacField):
        fieldLength = 2
        arcpy.management.AddField(tempLayer, vacField, 'TEXT', field_length=fieldLength)
        print("Field " + vacField + " added to " + tempLayer)

    vacLayer = "Vacant_" + jc
    useField = "ACTUAL_USE_DESCRIPTION"
    vacant = "Vacant"
    vacFlag = "Y"
    where_clause = f'{useField} LIKE \'%{vacant}%\''
    arcpy.management.SelectLayerByAttribute(tempLayer, "NEW_SELECTION", where_clause)
    if arcpy.Describe(tempLayer).FIDSet:
        if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
            expression = f"'{vacFlag}'"  
            arcpy.management.CalculateField(tempLayer, vacField, expression, "PYTHON3")
            arcpy.management.CopyFeatures(tempLayer, vacLayer)
            print(vacLayer + " created")


    # Identify Under-used Parcels: add Underused field to use as flag
    unduseField = "UnderUtilized" 
    if not arcpy.ListFields(tempLayer, unduseField):
        fieldLength = 2
        arcpy.management.AddField(tempLayer, unduseField, 'TEXT', field_length=fieldLength)
        print("Field " + unduseField + " added to " + tempLayer)

    unduseLayer = "UnderUtilized_" + jc
    improveField = "sum_Gen_Gross_Improvement_Value"
    unduseFlag = "Y"
    threshold_value = 500000
    where_clause = f"{improveField} < {threshold_value}"  
    arcpy.management.SelectLayerByAttribute(tempLayer, "NEW_SELECTION", where_clause)
    if arcpy.Describe(tempLayer).FIDSet:
        if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
            expression = f"'{unduseFlag}'"  
            arcpy.management.CalculateField(tempLayer, unduseField, expression, "PYTHON3")
            arcpy.management.CopyFeatures(tempLayer, unduseLayer)  
            print(unduseLayer + " created")
     

    # Calculate Improvement Value percent of Land Value: add field to store value
    imppercland = "PercentImproveLand" 
    if not arcpy.ListFields(tempLayer, imppercland):
        arcpy.management.AddField(tempLayer, imppercland, 'FLOAT')
        print("Field " + imppercland + " added to " + tempLayer)

    improveField = "sum_Gen_Gross_Improvement_Value"
    landvalField = "sum_Gen_Gross_Land_Value"
    where_clause = f'{improveField} > 0 AND {landvalField} > 0'
    arcpy.management.SelectLayerByAttribute(tempLayer, "NEW_SELECTION", where_clause)
    if arcpy.Describe(tempLayer).FIDSet:
        if int(arcpy.management.GetCount(tempLayer)[0]) > 0:
            expression = f"!{improveField}! / !{landvalField}! * 100"  
            arcpy.management.CalculateField(tempLayer, imppercland, expression, "PYTHON3")
            print("Field " + imppercland + " calculated")   

    # Create final layer
    finalLayer = "Public_" + jc
    arcpy.management.SelectLayerByAttribute(tempLayer, "CLEAR_SELECTION")
    arcpy.management.CopyFeatures(tempLayer, finalLayer)
    feature_count = arcpy.management.GetCount(finalLayer).getOutput(0)
    # print(f"The feature class '{finalLayer}' contains {feature_count} features.")
    print(finalLayer + " created")
    fieldList = arcpy.ListFields(finalLayer,"*_1*" )
    for f in fieldList:
        # print(f.name)
        substrings_to_check = ["Zoning", "Land", "School"]
        if not any(sub in f.name for sub in substrings_to_check):
            # print("Deleting " + f.name)
            arcpy.management.DeleteField(finalLayer, f.name)


print("Done")

