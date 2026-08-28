'''
MergeAllRDs.py

Merges all Regional District RD layers within a geodatabase into a single feature class in a new geodatabase.
Also removes polygons with null values in SAM fields (null values indicates water - all StatsCan DBs are terrestrial)

Ian Parfitt 27 Aug 2026
'''



import arcpy
import os

vDate = "Aug21"
# 1. Set the workspace to your source geodatabase
arcpy.env.workspace = r"C:\working\GISdata\Export\All_RDs_" + vDate + ".gdb"
workDir = r"C:\working\GISdata\Export"

# 2. Specify the output path for the new merged feature class
outgdbName = 'Merged_RDs_' + vDate + '.gdb'
outGDB = os.path.join(workDir, outgdbName)

outFC = "BCPL_" + vDate
outputFP = os.path.join(outGDB, outFC)

if not arcpy.Exists(outGDB):
    arcpy.management.CreateFileGDB(workDir, outgdbName)
    print (outGDB + " created")
if not arcpy.Exists(outputFP):
    # 3. List all feature classes in the workspace
    # Note: You can change the feature_type to "Polygon", "Polyline", or "Point" if needed
    feature_classes = arcpy.ListFeatureClasses(feature_type="All")

    # 4. Execute the Merge tool if any feature classes were found
    if feature_classes:
        print(f"Found {len(feature_classes)} feature classes to merge.")
        
        # Run the merge operation
        arcpy.management.Merge(inputs=feature_classes, output=outputFP)
        
        print("Merge operation completed successfully!")
    else:
        print("No feature classes found in the specified workspace.")
else:
    print(outputFP + " already exists")

# 5 Find SAM = <NULL> polys - these are primarily in the water.  Copy to a separate FC, delete, and save revised FC with no NULL SAMs

outFC_0 = outFC + "_0"
if not arcpy.Exists(outFC_0):

    arcpy.env.workspace = outGDB

    outLyr = outFC + "Lyr"
    arcpy.management.MakeFeatureLayer(outFC, outLyr)
    nullSAMFC = outFC + "_nullSAM"


    samField = "walk_caf"
    where_clause = f'"{samField}" IS NULL'
    arcpy.management.SelectLayerByAttribute(outLyr, "NEW_SELECTION", where_clause)
    if arcpy.Describe(outLyr).FIDSet:
            if int(arcpy.management.GetCount(outLyr)[0]) > 0:
                arcpy.management.CopyFeatures(outLyr, nullSAMFC)
                arcpy.management.DeleteFeatures(outLyr)
                print(nullSAMFC + " created")
    arcpy.management.SelectLayerByAttribute(outLyr, "CLEAR_SELECTION")
    arcpy.management.CopyFeatures(outLyr, outFC_0)
    print(outFC_0 + " created")

print("Done")