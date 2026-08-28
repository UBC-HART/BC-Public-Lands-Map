'''
UpdateMean.py

Updates Public_<RD> feature class using the slope raster once it is complete

Ian Parfitt
27 Aug 2026
.


'''

import arcpy
import os

from arcpy.sa import *


arcpy.env.overwriteOutput = True

RDinit = "CCRD"
RDpubFC = "Public_" + RDinit

#Set working directories and gdbs
Workdir = r'C:\working\ArcProjects\workspace'
ScratchWksp = r'C:\working\ArcProjects\scratch\scratchworkspace.gdb'
Workgdb = RDinit + 'PubJune.gdb'
outGDB = os.path.join(Workdir, Workgdb)
DEMWksp = r'C:\working\GISdata\LidarBC'
DEMPath = os.path.join(DEMWksp,RDinit)
Slope0 = "CCRD_LBCHR_SLP_alb.tif"
if not arcpy.Exists(outGDB):
    arcpy.management.CreateFileGDB(Workdir, Workgdb)
    print (outGDB + " created")

arcpy.env.workspace = outGDB
arcpy.env.scratchWorkspace = ScratchWksp



def zonalStatMean(arg1, arg2, arg3):
    # this is a copy of the zonalStatMean function in FunctionUtils.py
    inPubLayer = arg1
    inSlopeGrd = arg2
    RDinit = arg3
    print ("running zm with " + inPubLayer + ' ' + inSlopeGrd + ' ' + RDinit)
    # arcpy.env.extent = extentLayer
    outGrid = "tmp" + RDinit + "grd"
    zoneField = "PID_int"
    # cellSize = 1
    # inputFC = "TempOut_" + jc
    arcpy.env.workspace = outGDB
    arcpy.env.extent = inPubLayer
    arcpy.env.snapRaster = inSlopeGrd
    arcpy.env.cellSize = inSlopeGrd
    # arcpy.env.mask = inPubLayer
    if not arcpy.Exists(outGrid):
        # arcpy.Delete_management(outGrid)
        # print(outGrid + " deleted")
        arcpy.conversion.FeatureToRaster(inPubLayer,zoneField,outGrid,inSlopeGrd)
        print(outGrid + " created")
    tmpGrid = outGrid + "0"
    if not arcpy.Exists(tmpGrid):
        # arcpy.Delete_management(tmpGrid)
        # print(tmpGrid + " deleted")
        outputGrid = Int(outGrid)
        outputGrid.save(tmpGrid)
        print(tmpGrid + " created")
    outGrid = tmpGrid
    arcpy.management.BuildRasterAttributeTable(outGrid)
    if arcpy.Exists(outGrid):
        print(outGrid + " set to tmpGrid")
     
    field_type = "BIGINTEGER"
    arcpy.management.AddField(outGrid,zoneField,field_type)
    print("Added field " + zoneField)
  
    print("Populating the PID field...")
    with arcpy.da.UpdateCursor(outGrid, ["Value", zoneField]) as cursor:
        for row in cursor:
            # Example logic: set the new field value to be equal to 'Value' field
            new_value = row[0] 
            cursor.updateRow((row[0], new_value))
    print("PID field population complete.")
    
    outZonalMeanTab = "zMeanTab_" + RDinit
    print(outZonalMeanTab)
    zoneField = "Value"
    if not arcpy.Exists(outZonalMeanTab):
        outZSaT = ZonalStatisticsAsTable(outGrid, zoneField, inSlopeGrd, outZonalMeanTab, "DATA", "MEAN")
        print(outZonalMeanTab + " table created")
    return(outZonalMeanTab)

def updateMean(arg1, arg2):
    print("Running updateMean with " + arg1)
    # 1. Define your paths (Update these to your actual data paths)
    outZonalMeanTab = arg1
    RDpubFC = arg2

    # Change these if your ID field names are different
    id_field = "Value"
    mean_field = "MEAN"

    # 2. Read values from Feature Class 1 into a Python dictionary
    # This maps {ID: Mean_Value}
    mean_dict = {}
    with arcpy.da.SearchCursor(outZonalMeanTab, [id_field, mean_field]) as search_cursor:
        for row in search_cursor:
            # Avoid adding null or empty IDs to the dictionary
            if row[0] is not None:
                mean_dict[row[0]] = row[1]

    # 3. Update Feature Class 2 using the dictionary matching
    pid_field = "PID_int"
    with arcpy.da.UpdateCursor(RDpubFC, [pid_field, mean_field]) as update_cursor:
        for row in update_cursor:
            current_id = row[0]
            
            # Check if the ID exists in our dictionary
            if current_id in mean_dict:
                # Update the Mean field in FC2 with the value from FC1
                row[1] = mean_dict[current_id]
                update_cursor.updateRow(row)

    print("Field update completed successfully.")

def main():
    print("Start update for "  + RDinit)
    # 1. Define paths
    RDpubFC = "Public_" + RDinit
    if arcpy.Exists(RDpubFC):
        print(RDpubFC + "_exists")
    
    output_fc = "Public_" + RDinit + "_PID"
    field_to_keep = "PID_int"  # Change to the exact field name you want to keep
    if arcpy.ListFields(RDpubFC, field_to_keep):
        print(field_to_keep + " exists")
     
    # 2. Initialize an empty FieldMappings object
    field_mappings = arcpy.FieldMappings()

    # 3. Create a FieldMap specifically for the field you want to keep
    field_map = arcpy.FieldMap()
    field_map.addInputField(RDpubFC, field_to_keep)

    # 4. Add the individual field map to the main mappings object
    field_mappings.addFieldMap(field_map)

    # 5. Export the feature class with the limited field mapping
    # Note: Mandatory system fields (OBJECTID, Shape) are retained automatically.
    # output_fc = os.path.join(output_gdb, output_name)
    arcpy.conversion.ExportFeatures(RDpubFC, output_fc, field_mapping=field_mappings)

    print(f"Successfully created: {output_fc} with only field '{field_to_keep}'")


    # Calculate Zonal Slope Mean as table and join table
    inSlopeGrid = os.path.join(DEMPath, Slope0)
    print(inSlopeGrid)
    zmeanTab = zonalStatMean(output_fc,inSlopeGrid, RDinit)  
    print(zmeanTab + " created") 
    ourZoneMeanFieldJoin = ["MEAN"] 
    pidField = "PID_NUMBER"
    valueField = "VALUE"
    pidIntField = "PID_int"
    zPIDIndex = "PIDx" + RDinit
    found_zPIDIndex = False
    indexes = arcpy.ListIndexes(zmeanTab)
    for index in indexes:
        if index.name == zPIDIndex:
            found_zPIDIndex = True
            break
    if not found_zPIDIndex:
        arcpy.management.AddIndex(zmeanTab, valueField, zPIDIndex,"UNIQUE", "NON_ASCENDING") 

    zmeanTab = "zMeanTab_" + RDinit
    updateMean(zmeanTab,RDpubFC)
    
    
print("Done")

if __name__ == "__main__":
    main()