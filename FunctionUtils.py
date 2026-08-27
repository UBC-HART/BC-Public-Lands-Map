'''
FunctionUtils.py

functions to call


Ian Parfitt   Aug 27 2026

'''



import arcpy
import requests
import csv
import sys
import pandas
import os

from arcpy import env
from arcpy.sa import *

arcpy.env.overwriteOutput = True

#Set working directories and gdbs
RDinit = "NRRM"
Workdir = r'C:\working\ArcProjects\workspace'
arcpy.env.scratchWorkspace = r'C:\working\ArcProjects\scratch\scratchworkspace.gdb'
Workgdb = RDinit + 'PubApr.gdb'
outGDB = os.path.join(Workdir, Workgdb)

arcpy.env.workspace = outGDB

def sum_gross_improve(arg1, arg2):
    # Sum Gross Improvement for overlapping polys (same parcel, many units)
    jc = arg1
    targetFeatures = arg2
    joinFeatures = r'C:\working\GISdata\BCA\BCASpatial\Data\bca_spatial_20260109.gdb\Gen_Prop_Values'
        
    # Output will be the target features, pub polys, with all the attributes plus a sum of gross improvement
    outfc = "sum_gen_prop_values_" + jc
    
    # Create a new fieldmappings and add the two input feature classes.
    fieldmappings = arcpy.FieldMappings()
    fieldmappings.addTable(targetFeatures)
    fieldmappings.addTable(joinFeatures)
    
    # First get the GEN_GROSS_IMPROVEMENT_VALUE fieldmap. Setting the field's merge rule to sum will aggregate 
    #   the values for all overlapping gross improvement values. The field is also renamed to be more appropriate
    GIFieldIndex = fieldmappings.findFieldMapIndex("GEN_GROSS_IMPROVEMENT_VALUE")
    fieldmapA = fieldmappings.getFieldMap(GIFieldIndex)
    GLFieldIndex = fieldmappings.findFieldMapIndex("GEN_GROSS_LAND_VALUE")
    fieldmapB = fieldmappings.getFieldMap(GLFieldIndex)
    
    # Get the output field's properties as a field object
    fieldA = fieldmapA.outputField
    fieldB = fieldmapB.outputField
    
    # Rename the field and pass the updated field object back into the field map
    fieldA.name = "sum_Gen_Gross_Improvement_Value"
    fieldA.aliasName = "sum_Gen_Gross_Improvement_Value"
    fieldmapA.outputField = fieldA
    fieldB.name = "sum_Gen_Gross_Land_Value"
    fieldB.aliasName = "sum_Gen_Gross_Land_Value"
    fieldmapB.outputField = fieldB
    
    # Set the merge rule to sum and then replace the old fieldmap in the mappings object
    # with the updated one
    fieldmapA.mergeRule = "sum"
    fieldmappings.replaceFieldMap(GIFieldIndex, fieldmapA)
    fieldmapB.mergeRule = "sum"
    fieldmappings.replaceFieldMap(GLFieldIndex, fieldmapB)
    
    #Run the Spatial Join tool, using the defaults for the join operation and join type
    arcpy.analysis.SpatialJoin(targetFeatures, joinFeatures, outfc, "#", "#", fieldmappings, "CONTAINS")
    return(outfc)
    print(outfc + " created")

def merge_land_char(arg1, arg2):
    # Merge Land Characteristics (same poly, multiple fields)
    jc = arg1
    targetFeatures = arg2
    joinFeatures = r'C:\working\GISdata\BCA\BCASpatial\Data\bca_spatial_20260109.gdb\Land_Character'
    # joinFeatures = pubLayer
    
    # Output will be the target features, pub polys, with all the attributes plus merges of the land character code and description
    outfc = "merge_land_char_" + jc
    
    # Create a new fieldmappings object and add the two input feature classes.
    fieldmappings = arcpy.FieldMappings()
    fieldmappings.addTable(targetFeatures)
    fieldmappings.addTable(joinFeatures)
    
    # First get the LAND_CHARACTERISTIC_DESC fieldmap. This is a field in the input public land feature class.
    # The output will have the attributes of this layer. Setting the
    # field's merge rule to sum will aggregate the values for all overlapping land characteristic values. The field is also renamed to be more appropriate
    # for the output.
    LCCFieldIndex = fieldmappings.findFieldMapIndex("LAND_CHARACTERISTIC_CODE")
    fieldmapA = fieldmappings.getFieldMap(LCCFieldIndex)
    LCDFieldIndex = fieldmappings.findFieldMapIndex("LAND_CHARACTERISTIC_DESC")
    fieldmapB = fieldmappings.getFieldMap(LCDFieldIndex)
    
    # Get the output field's properties as a field object
    fieldA = fieldmapA.outputField
    fieldB = fieldmapB.outputField
    
    # Rename the field and pass the updated field object back into the field map
    fieldA.name = "merge_Land_Character_Code"
    fieldA.aliasName = "merge_Land_Character_Code"
    fieldA.length = 60
    fieldmapA.outputField = fieldA

    fieldB.name = "merge_Land_Character_Desc"
    fieldB.aliasName = "merge_Land_Character_Desc"
    fieldmapB.outputField = fieldB
    
    # Set the merge rule to sum and then replace the old fieldmap in the mappings object
    # with the updated one
    fieldmapA.joinDelimiter = " ; "
    fieldmapA.mergeRule = "Join"
    fieldmappings.replaceFieldMap(LCCFieldIndex, fieldmapA)

    fieldmapB.joinDelimiter = " ; "
    fieldmapB.mergeRule = "Join"
    fieldmappings.replaceFieldMap(LCDFieldIndex, fieldmapB)
    
    #Run the Spatial Join tool, using the defaults for the join operation and join type
    arcpy.analysis.SpatialJoin(targetFeatures, joinFeatures, outfc, "#", "#", fieldmappings, "CONTAINS")
    return(outfc)
    print(outfc + " created")

def merge_native_land(arg1):
    # Join public land layer with overlapping native land territories.
    print("Running merge_native_land")
    inpubFC = arg1
    inpubLyr = "PublicLyr"
    arcpy.management.MakeFeatureLayer(inpubFC,inpubLyr)
    arcpy.management.SelectLayerByAttribute(inpubLyr, "CLEAR_SELECTION")
    joinFC = r'https://services6.arcgis.com/SC70xY1nSLm15pYn/arcgis/rest/services/Native_Land_Digital_territories/FeatureServer/0'
    # joinFC = r'C:\working\GISdata\FirstNations\FirstNations.gdb\nativeland_BCalb0'
    joinLyr = "nativelandLayer"
    arcpy.management.MakeFeatureLayer(joinFC,joinLyr)
    arcpy.management.SelectLayerByAttribute(joinLyr, "CLEAR_SELECTION") 
    joinFld = "Name"
    # joinFeatures = pubLayer
    arcpy.env.extent = joinFC
    outputFld = "FNTerritories"
    
    # Ensure the output field exists and is long enough
    # Unicode characters often take more bytes than standard ASCII
    if not arcpy.ListFields(inpubFC, outputFld):
        print(outputFld + " doesn't exist, adding")
        arcpy.management.AddField(inpubFC, outputFld, "TEXT", field_length=8000)

    # --- WORKFLOW ---
    # 1. Store join layer features in memory for faster access
    join_features = [row for row in arcpy.da.SearchCursor(joinFC, ["SHAPE@", joinFld])]

    # 2. Use an UpdateCursor to process target polygons
    print("Running cursors")
    with arcpy.da.UpdateCursor(inpubFC, ["SHAPE@", outputFld]) as cursor:
        for row in cursor:
            target_geom = row[0]
            intersecting_values = []

            # Check against every polygon in the join layer #testing target_geom.intersects in place of target_geom.overlaps(join_geom)  or target_geom.contains(join_geom).
            for join_geom, val in join_features:
                if val and (not target_geom.disjoint(join_geom)):  # (target_geom.overlaps(join_geom) or target_geom.contains(join_geom))
                    # Ensure the value is treated as a Unicode string
                    intersecting_values.append(str(val))
                    # print(intersecting_values)

            # 3. Concatenate unique values with your preferred delimiter
            if intersecting_values:
                unique_vals = sorted(list(set(intersecting_values))) # De-duplicate and sort
                row[1] = "; ".join(unique_vals)
                # print(row[1])
                cursor.updateRow(row)
    print("Concatenation complete.")
    
    return(inpubFC)

def merge_owner(arg1):
    # ParcelMap data has overlapping polys.  Add a field and merge all OwnerType values for overlapping polys. 
    RDinit = arg1
    print("merge_owner function starting for " + RDinit)
    joinFeatures = r'C:\working\ArcProjects\workspace\BCPubOct.gdb\BC_PubIndexJan_20260118'
    targetFeatures = r'C:\working\ArcProjects\workspace\BCPubOct.gdb\BC_PubIndex_cntOverlap' # replaced
    targetFeatures = r'C:\working\ArcProjects\workspace\BCPubOct.gdb\BC_PubJan26_cntOverlap'
    if not arcpy.Exists(targetFeatures):
        print("Counting overlaps in " + joinFeatures)
        arcpy.analysis.CountOverlappingFeatures(joinFeatures, targetFeatures)
    
    # targetFeatures = joinFeatures
    """ if not arcpy.Exists(targetFeatures):
        print("Counting overlapping features")
        arcpy.analysis.CountOverlappingFeatures(joinFeatures,targetFeatures)
        arcpy.management.AddField(targetFeatures,"OwnerType",'TEXT') """


    outfc = "BC_PubIndex_mergeOwner"
    
    # Create a new fieldmappings object and add the two input feature classes.
    fieldmappings = arcpy.FieldMappings()
    fieldmappings.addTable(targetFeatures)
    fieldmappings.addTable(joinFeatures)
    
    
    # First get the input fieldmap. Setting the
    # field's merge rule to sum will aggregate the values for all overlapping gross improvement values. The field is also renamed to be more appropriate
    # for the output.
    LCCFieldIndex = fieldmappings.findFieldMapIndex("OwnerType")
    fieldmapA = fieldmappings.getFieldMap(LCCFieldIndex)
       
    # Get the output field's properties as a field object
    fieldA = fieldmapA.outputField
    
    
    # Rename the field and pass the updated field object back into the field map
    fieldA.name = "merge_OwnerType"
    fieldA.aliasName = "merge_OwnerType"
    fieldA.length = 255
    fieldmapA.outputField = fieldA

   
    # Set the merge rule to join and then replace the old fieldmap in the mappings object
    # with the updated one
    fieldmapA.joinDelimiter = " ; "
    fieldmapA.mergeRule = "Join"
    fieldmappings.replaceFieldMap(LCCFieldIndex, fieldmapA)

    
    #Run the Spatial Join tool, using the defaults for the join operation and join type
    arcpy.analysis.SpatialJoin(targetFeatures, joinFeatures, outfc, "JOIN_ONE_TO_ONE", "#", fieldmappings, "CONTAINS")
    return(outfc)
    print(outfc + " created")

def SAMfieldmap(arg1, arg2, arg3):
    # changes field mappings from text to double
    samCSV = arg1
    print(samCSV + " rocks")
    samDir = arg2
    outGDB = arg3
    samTAB = samCSV.removesuffix(".csv")
    arcpy.env.workspace = samDir
  
    # Create a  fieldmapping from the CSV field
    fieldmappings = arcpy.FieldMappings()
    fieldmappings.addTable(samCSV)
   
   
    print("still rocks")
    cafFieldIndex = fieldmappings.findFieldMapIndex("acs_idx_caf")
    print(cafFieldIndex)
    if not cafFieldIndex == -1:
        cafFieldmap = fieldmappings.getFieldMap(cafFieldIndex)
        cafField = cafFieldmap.outputField
        cafField.type = "Double"
        cafField.precision = 9
        cafFieldmap.outputField = cafField
        fieldmappings.replaceFieldMap(cafFieldIndex, cafFieldmap)
    ccfFieldIndex = fieldmappings.findFieldMapIndex("acs_idx_ccf")
    print(ccfFieldIndex)
    if not ccfFieldIndex == -1:
        ccfFieldmap = fieldmappings.getFieldMap(ccfFieldIndex)
        ccfField = ccfFieldmap.outputField
        ccfField.type = "Double"
        ccfField.precision = 9
        ccfFieldmap.outputField = ccfField
        fieldmappings.replaceFieldMap(ccfFieldIndex, ccfFieldmap)
    efFieldIndex = fieldmappings.findFieldMapIndex("acs_idx_ef")
    if not efFieldIndex == -1:
        efFieldmap = fieldmappings.getFieldMap(efFieldIndex)
        efField = efFieldmap.outputField
        efField.type = "Double"
        efField.precision = 9
        efFieldmap.outputField = efField
        fieldmappings.replaceFieldMap(efFieldIndex, efFieldmap)
    empFieldIndex = fieldmappings.findFieldMapIndex("acs_idx_emp")
    if not empFieldIndex == -1:
        empFieldmap = fieldmappings.getFieldMap(empFieldIndex)
        empField = empFieldmap.outputField
        empField.type = "Double"
        empField.precision = 9
        empFieldmap.outputField = empField
        fieldmappings.replaceFieldMap(empFieldIndex, empFieldmap)
    hfFieldIndex = fieldmappings.findFieldMapIndex("acs_idx_hf")
    if not hfFieldIndex == -1: 
        hfFieldmap = fieldmappings.getFieldMap(hfFieldIndex) 
        hfField = hfFieldmap.outputField
        hfField.type = "Double"
        hfField.precision = 9
        hfFieldmap.outputField = hfField
        fieldmappings.replaceFieldMap(hfFieldIndex, hfFieldmap) 
    psefFieldIndex = fieldmappings.findFieldMapIndex("acs_idx_psef")
    if not psefFieldIndex == -1: 
        psefFieldmap = fieldmappings.getFieldMap(psefFieldIndex) 
        psefField = psefFieldmap.outputField
        psefField.type = "Double"
        psefField.precision = 9
        psefFieldmap.outputField = psefField
        fieldmappings.replaceFieldMap(psefFieldIndex, psefFieldmap)    
    srfFieldIndex = fieldmappings.findFieldMapIndex("acs_idx_srf")
    if not srfFieldIndex == -1: 
        srfFieldmap = fieldmappings.getFieldMap(srfFieldIndex) 
        srfField = srfFieldmap.outputField
        srfField.type = "Double"
        srfField.precision = 9
        srfFieldmap.outputField = srfField
        fieldmappings.replaceFieldMap(srfFieldIndex, srfFieldmap)
    lvl1FieldIndex = fieldmappings.findFieldMapIndex("acs_lvl_gs-1")
    if not lvl1FieldIndex == -1: 
        lvl1Fieldmap = fieldmappings.getFieldMap(lvl1FieldIndex) 
        lvl1Field = lvl1Fieldmap.outputField
        lvl1Field.type = "Double"
        lvl1Field.precision = 9
        lvl1Fieldmap.outputField = lvl1Field
        fieldmappings.replaceFieldMap(lvl1FieldIndex, lvl1Fieldmap)   
    lvl3FieldIndex = fieldmappings.findFieldMapIndex("acs_lvl_gs-3")
    if not lvl3FieldIndex == -1: 
        lvl3Fieldmap = fieldmappings.getFieldMap(lvl3FieldIndex) 
        lvl3Field = lvl3Fieldmap.outputField
        lvl3Field.type = "Double"
        lvl3Field.precision = 9
        lvl3Fieldmap.outputField = lvl3Field
        fieldmappings.replaceFieldMap(lvl3FieldIndex, lvl3Fieldmap)  
    lvl5FieldIndex = fieldmappings.findFieldMapIndex("acs_lvl_gs-5")
    if not lvl5FieldIndex == -1: 
        lvl5Fieldmap = fieldmappings.getFieldMap(lvl5FieldIndex) 
        lvl5Field = lvl5Fieldmap.outputField
        lvl5Field.type = "Double"
        lvl5Field.precision = 9
        lvl5Fieldmap.outputField = lvl5Field
        fieldmappings.replaceFieldMap(lvl5FieldIndex, lvl5Fieldmap)          

    # Get the output field's properties as a field object
   
    """    cafField = cafFieldmap.outputField
    ccfField = ccfFieldmap.outputField
    efField = efFieldmap.outputField
    empField = empFieldmap.outputField
    hfField = hfFieldmap.outputField
    srfField = srfFieldmap.outputField """

   
    
    # Rename the field and pass the updated field object back into the field map
    """     cafField.type = "Double"
    cafFieldmap.outputField = cafField
    ccfField.type = "Double"
    ccfFieldmap.outputField = ccfField
    efField.type = "Double"
    efFieldmap.outputField = efField
    empField.type = "Double"
    empFieldmap.outputField = empField
    hfField.type = "Double"
    hfFieldmap.outputField = hfField
    srfField.type = "Double"
    srfFieldmap.outputField = srfField """


    
    # Set the merge rule to sum and then replace the old fieldmap in the mappings object
    # with the updated one
    """ fieldmappings.replaceFieldMap(cafFieldIndex, cafFieldmap)
    fieldmappings.replaceFieldMap(ccfFieldIndex, ccfFieldmap)
    fieldmappings.replaceFieldMap(efFieldIndex, efFieldmap)
    fieldmappings.replaceFieldMap(empFieldIndex, empFieldmap)
    fieldmappings.replaceFieldMap(hfFieldIndex, hfFieldmap)
    fieldmappings.replaceFieldMap(srfFieldIndex, srfFieldmap) """

    
    #Run the tool, using the defaults for the join operation and join type
    arcpy.conversion.TableToTable(samCSV, outGDB, samTAB,field_mapping=fieldmappings)
    print(samTAB + " created")   
    return(samTAB)

def zonalStatMean(arg1, arg2, arg3):
    # zonal mean function for polygon slope calculation
    inPubLayer = arg1
    inSlopeGrd = arg2
    jc = arg3
    inPubLayer = "rePub_" + jc
    extentLayer = "rePub_" + jc
    print(arg1,arg2,arg3)
    # arcpy.env.extent = extentLayer
    outGrid = "tmp" + jc + "grd"
    zoneField = "PID_int"
    # cellSize = 1
    # inputFC = "TempOut_" + jc
    arcpy.env.workspace = outGDB
    arcpy.env.extent = inPubLayer
    arcpy.env.snapRaster = inSlopeGrd
    arcpy.env.cellSize = inSlopeGrd
    arcpy.env.mask = inPubLayer
    if not arcpy.Exists(outGrid):
        arcpy.Delete_management(outGrid)
        print(outGrid + " deleted")
        arcpy.conversion.FeatureToRaster(inPubLayer,zoneField,outGrid,inSlopeGrd)
        print(outGrid + " created")
    tmpGrid = outGrid + "0"
    if not arcpy.Exists(tmpGrid):
        arcpy.Delete_management(tmpGrid)
        print(tmpGrid + " deleted")
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
  
    """ field_type = "SHORT"
    lutField = "PID_link"
    arcpy.management.AddField(outGrid,lutField,field_type)
    print("Added field " + lutField) """
    
    print("Populating the PID field...")
    with arcpy.da.UpdateCursor(outGrid, ["Value", zoneField]) as cursor:
        for row in cursor:
            # Example logic: set the new field value to be equal to 'Value' field
            new_value = row[0] 
            cursor.updateRow((row[0], new_value))
    print("PID field population complete.")
    """ cellSize = 1
    sourceField = "PID_NUMBER"
    expression = "int(!{}!)".format(sourceField)
    arcpy.management.AddField(inPubLayer, zoneField, 'LONG')
    arcpy.management.CalculateField(inPubLayer, zoneField, expression, "PYTHON3")"""
    # testmeLayer = "AA_" + jc
    # arcpy.management.CopyFeatures(inPubLayer, testmeLayer) 
    outZonalMeanTab = "zMeanTab_" + jc
    print(outZonalMeanTab)
    zoneField = "Value"
    if not arcpy.Exists(outZonalMeanTab):
        outZSaT = ZonalStatisticsAsTable(outGrid, zoneField, inSlopeGrd, outZonalMeanTab, "DATA", "MEAN")
        print(outZonalMeanTab + " table created")
    return(outZonalMeanTab)

def remapAppend(arg1,arg2):
    targetLyr = arg1
    inputLyr = arg2

    fieldMappings = arcpy.FieldMappings()
    fieldMappings.addTable(targetLyr)
    field1 = "MB_Num_Storeys"
    field2 = "Land_Width_Width"
    target_field_map1 = fieldMappings.getFieldMap(fieldMappings.findFieldMapIndex(field1))
    target_field_map1.addInputField(inputLyr, field1)
    target_field1 = target_field_map1.outputField
    target_field1.type = "DOUBLE"
    target_field_map1.outputField = target_field1
    target_field_map2 = fieldMappings.getFieldMap(fieldMappings.findFieldMapIndex(field2))
    target_field_map2.addInputField(inputLyr, field2)
    target_field2 = target_field_map2.outputField
    target_field2.type = "DOUBLE"
    target_field_map2.outputField = target_field2
    return(fieldMappings)

def geoMeasures(arg1,arg2):
    # Calculates zonal thickness.  
    # The function creates several fields and often crashes after creating the Thickness field. 
    # This is OK as we only need the thickness field, error is handled so function completes.
    # Optionally, rasters created in this function can be deleted.
    inputPubLayer = arg1
    jc = arg2
    # inputPubLayer = "rePub_" + jc
    outGrid = "tmp" + jc + "grd"
    zoneField = "PID_int"
    cellSize = 1
    arcpy.env.workspace = outGDB
    arcpy.env.extent = inputPubLayer
    arcpy.env.mask = inputPubLayer
    print("Running GeoMeasures")
    # inputFC = "TempOut_" + jc
    # arcpy.env.workspace = outGDB
    r'''if arcpy.Exists(outGrid):
        arcpy.Delete_management(outGrid)
        print(outGrid + " deleted")'''
    if not arcpy.Exists(outGrid):
        arcpy.conversion.FeatureToRaster(inputPubLayer,zoneField,outGrid,cellSize)
        print(outGrid + " created")
    tmpGrid = outGrid + "0z"
    r'''if arcpy.Exists(tmpGrid):
        arcpy.Delete_management(tmpGrid)
        print(tmpGrid + " deleted")'''
    if not arcpy.Exists(tmpGrid):
        outputGrid = Int(outGrid)
        outputGrid.save(tmpGrid)
        print(tmpGrid + " created")
    # outGrid = tmpGrid
    arcpy.management.BuildRasterAttributeTable(tmpGrid)
    if arcpy.Exists(tmpGrid):
        print("VAT built for " + tmpGrid)
     
    field_type = "BIGINTEGER"
    arcpy.management.AddField(tmpGrid,zoneField,field_type)
    print("Added field " + zoneField)
  
    field_type = "SHORT"
    lutField = "PID_link"
    arcpy.management.AddField(tmpGrid,lutField,field_type)
    print("Added field " + lutField)
    
    print("Populating the PID field...")
    with arcpy.da.UpdateCursor(tmpGrid, ["Value", zoneField]) as cursor:
        for row in cursor:
            # Example logic: set the new field value to be equal to 'Value' field
            new_value = row[0] 
            cursor.updateRow((row[0], new_value))
    print("PID field population complete.")

    print("Populating the PID_link field...")
    with arcpy.da.UpdateCursor(tmpGrid, ["Value", lutField]) as cursor:
        itlink = 1
        for row in cursor:
            # Example logic: set the new field value to be equal to 'Value' field
            new_value = itlink 
            cursor.updateRow((row[0], new_value))
            itlink += 1
    print("PID_link field population complete.")

    outGrid = tmpGrid
    print(outGDB)
    print(outGrid)
    arcpy.env.extent = outGrid
    arcpy.env.mask = outGrid
    arcpy.env.snapRaster = outGrid
    zoneField = "PID_int"
    zgGrid = "zoneGeo" + jc
    if arcpy.Exists(zgGrid):
        arcpy.Delete_management(zgGrid)  
    lutField = "PID_link"
    valueField = "Value"
    processingCellSize = 1
    outgeoTab = "outgeoTab_" + jc
    if arcpy.Exists(outgeoTab):
        arcpy.Delete_management(outgeoTab)
    if not arcpy.Exists(outgeoTab):
        # print(outGrid, zoneField, 'THICKNESS', 0.2)
        # zgresult = arcpy.sa.ZonalGeometry("temp_236_grid", "PID_int", "THICKNESS", 0.2)
        try:
            print("Running Zonal Geometry as a Table")
            # arcpy.management.MakeRasterLayer(outGrid, "out_rasterlayer")
            outZonalGeometryAsTable = ZonalGeometryAsTable(outGrid, valueField, outgeoTab, processingCellSize)
            # print(outgeoTab + " created")
            # outZonalGeometry = ZonalGeometry(outGrid, lutField, 'THICKNESS', 0.2)
            # outZonalGeometry.save(zgGrid)
            print(outgeoTab + " created in try")
        except arcpy.ExecuteError:
        # Catches specific errors raised by ArcGIS tools
            print("\nAn ArcGIS execution error occurred:")
            # Print the tool's error messages
            print(arcpy.GetMessages(2)) 
            # sys.exit(1)


    # Delete temporary rasters
    r""" outGrid = "tmp" + jc + "grd"
    if arcpy.Exists(outGrid):
        arcpy.Delete_management(outGrid)
    tmpGrid = outGrid + "0"
    if arcpy.Exists(tmpGrid):
        arcpy.Delete_management(tmpGrid) """

    print("returning " + outgeoTab)
    return(outgeoTab)

def calc_circ(arg1, arg2):
    # Calculate circularitiy
    inputPubLayer = arg1
    jc = arg2
    
    GDBarea_field_name = "Shape_Area"
    GDBlength_field_name = "Shape_Length"
    GDBcircularity_field_name = "Shape_Circularity"
    
    """     arcpy.management.AddFields(inputPubLayer, [
            [area_field_name, "DOUBLE"],
            [perimeter_field_name, "DOUBLE"],
            [circularity_field_name, "DOUBLE"] 
        ])"""

    expression = f"(4 * math.pi * !{GDBarea_field_name}!) / (!{GDBlength_field_name}!**2)"
    arcpy.management.CalculateField(inputPubLayer, GDBcircularity_field_name, expression, "PYTHON3", '')

def runDensity(arg1, arg2):
    # Calculate dwelling density
    RDinit = arg1
    inputPubLayer = arg2
    
    print("runDensity function...")
    print(inputPubLayer)
    arcpy.env.extent = inputPubLayer
    
    densityFC = r'C:\working\GISdata\StatsCan\DBwDwellings\Density.gdb\DBwDwellings_capped_alb' 
        
    # Output will be the target features, pub polys, with all the attributes of the spatial join target
    outFC = RDinit + "_Density"
    
    # Create a new FieldMappings object and add the public land field map
    fms = arcpy.FieldMappings()
    fms.addTable(inputPubLayer)  # target
    fms.addTable(densityFC)      # join

    # rename/join DwellAcre -> Existing_Density
    idx = fms.findFieldMapIndex("DwellAcre")
    fm = fms.getFieldMap(idx)
    out_f = fm.outputField
    out_f.name = "Existing_Density"
    out_f.aliasName = "Existing Density"
    fm.outputField = out_f
    fm.mergeRule = "First"   # or Mean/Max/Median/etc as appropriate
    fms.replaceFieldMap(idx, fm)

    arcpy.analysis.SpatialJoin(
        target_features=inputPubLayer,
        join_features=densityFC,
        out_feature_class=outFC,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        field_mapping=fms,
        match_option="INTERSECT")
    
    print("Spatial Join for " + outFC + " complete")  

    return(outFC)

def runRiparian(arg1, arg2):
    # Create Riparian field, populate with Y if poly overlaps riparian buffer.
    RDinit = arg1
    inputPubLayer = arg2
    
    print("runRiparian function...")
    riparianFC = r'C:\working\GISdata\Riparian\Riparian.gdb\Riparian_buffer_All' 
    arcpy.env.extent = inputPubLayer # hoping to speed up this function by specifying extent   
    # Output will be the target features, pub polys, with all the attributes of the spatial join target
    outFC = RDinit + "_Riparian"
    
    # Create a new FieldMappings object and add the public land field map
    fms = arcpy.FieldMappings()
    fms.addTable(inputPubLayer)
    
    # Create FieldMap objects for fields to add from join layer
    fm_riparian= arcpy.FieldMap()
            
    #add desired join fields to corresponding FieldMap objects
    fm_riparian.addInputField(riparianFC, "Riparian")

    #set output field properties by creating new variables and set variable to FieldMap's outputfield.
    riparian_field = fm_riparian.outputField
    riparian_field.name = "Riparian"
    riparian_field.aliasName = "Riparian"
    fm_riparian.outputField = riparian_field

    
    #add fieldmaps to fieldmapping object
    fms.addFieldMap(fm_riparian)
    
    arcpy.Extent = inputPubLayer

    arcpy.analysis.SpatialJoin(
        target_features=inputPubLayer,
        join_features=riparianFC,
        out_feature_class=outFC,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        field_mapping=fms,
        match_option="INTERSECT")
    
    print("Spatial Join for " + outFC + " complete")  

    return(outFC)

def create_centroid(arg1, arg2):
    RDinit = arg1
    inputPubLayer = arg2
    print("running create centroid")
    # jc = arg1
    centroidFC = RDinit + "_centroid"
    if arcpy.Exists(centroidFC):
        arcpy.Delete_management(centroidFC)
    if not arcpy.Exists(centroidFC):
        # Create output feature class (ensure schema matches input)
        desc = arcpy.Describe(inputPubLayer)
        # fields = [f.name for f in desc.fields if f.type not in ('Geometry', 'OID')]
        # fields.append("ORIG_ID") # Add a unique ID field

        arcpy.management.CreateFeatureclass(
            outGDB,
            centroidFC,
            "POINT",
            spatial_reference=desc.spatialReference
        )
        print(centroidFC + " created")
        arcpy.management.AddField(centroidFC, "PID_int", "BIGINTEGER") # Or appropriate type

        # Use cursors to process
        with arcpy.da.SearchCursor(inputPubLayer, ['SHAPE@TRUECENTROID', 'PID_int']) as search_cursor:
            with arcpy.da.InsertCursor(centroidFC, ['SHAPE@', 'PID_int']) as insert_cursor:
                for row in search_cursor:
                    centroid_point = row[0]
                    PID = row[1]
                    # Create list of attributes (excluding geometry and OID from search)
                    # attributes = list(row[2:])
                
                    # Insert centroid and original attributes
                    insert_cursor.insertRow([centroid_point, PID])

        print("Centroids created successfully with PID attribute")
    return(centroidFC)

def runSAM(arg1,arg2):
    # Creates all fields for two transportation types: offpeak transit, walking.
    RDinit = arg1
    centroidFC = arg2

    DBwksp = r'C:\working\GISdata\StatsCan\db2021\ldb_000b21f_e.gdb'
    SAMwksp = r'C:\working\GISdata\StatsCan\sam_msa2024\SAM2024.gdb'
    transitFC = 'transit_offpeak2024_DB2021'
    walkFC = 'walking2024_DB2021'

    # If necessary, modify field names so they are unique for walking and transit
    """ for type in ('walk','transit'):
        if type == 'walk':
            inSAMFC = walkFC
        if type == 'transit':
            inSAMFC = transitFC   
        print("running " + type)
        # inSAMFC = type + "FC"
        outSAMFC= inSAMFC + "_rev"
        inSAMFCFull = os.path.join(DBwksp, inSAMFC)
        outSAMFCFull = os.path.join(DBwksp, outSAMFC)

        if arcpy.Exists(outSAMFCFull):
            arcpy.Delete_management(outSAMFCFull)
            print(outSAMFCFull + " deleted")
            arcpy.management.CopyFeatures(inSAMFCFull, outSAMFCFull)

        print(inSAMFCFull + " copied to " + outSAMFCFull)


        for sam in ('caf', 'ccf', 'ef', 'emp', 'hf', 'psef', 'srf'):
            inFldname = 'acs_idx_' + sam
            outFldname = type + '_' + sam
            arcpy.management.AlterField(outSAMFCFull, 
                                        inFldname, 
                                        outFldname, 
                                        outFldname)
        iz = 1
        while iz <= 5:
            print('running ' + type + ' ' + str(iz))
            inFldname = 'acs_lvl_gs_' + str(iz)
            outFldname = type + '_gs_' + str(iz)
            arcpy.management.AlterField(outSAMFCFull, 
                                    inFldname, 
                                    outFldname, 
                                    outFldname)  
            iz += 2

        print(type + " complete") """    
    #Run spatial join for both travel types (walk, transit)

    idx = 0
    outFC = centroidFC
    for type in ('walk','transit'):
        print("Running spatial join for " + type)
        if type == 'walk':
            inSAMFC = walkFC
        if type == 'transit':
            inSAMFC = transitFC   

        outSAMFC= inSAMFC + "_rev"
        
        inSAMFCFull = os.path.join(DBwksp, inSAMFC)
        outSAMFCFull = os.path.join(DBwksp, outSAMFC)
        
        # 
        # 1. Create FieldMappings Object
        fms = arcpy.FieldMappings()

        # 2. Add all existing fields from the target points
        
        if type == 'walk':
            SAMFC = RDinit + "_SAMwalk"
            fms.addTable(centroidFC)
        else:
            outFC = SAMFC
            print(outFC)
            SAMFC = RDinit + "_SAM"
            fms.removeAll()
            fms.addTable(outFC)

        # 3. Create a FieldMap to bring over a specific polygon attribute
        # Example: Bringing "CityName" from polygon to points
                
        for sam in ('caf', 'ccf', 'ef', 'emp', 'hf', 'psef', 'srf'):
            outFldname = type + '_' + sam
            fldmapname = type + "_fldmap"
            print(outFldname, fldmapname, idx)
            fldmapname = arcpy.FieldMap()
            fldmapname.addInputField(outSAMFCFull, outFldname, idx)
              
            fms.addFieldMap(fldmapname)
            print("Added " + outFldname + " to field map")
            idx += 1
        iz = 1
        while iz <= 5:
            outFldname = type + '_gs_' + str(iz)    
            fldmapname = outFldname + "_map"
            fldmapname = arcpy.FieldMap()
            fldmapname.addInputField(outSAMFCFull, outFldname, idx)
            
            """ out_field = poly_field_map.outputField
            out_field.name = outFldname
            out_field.aliasName = outFldname
            poly_field_map.outputField = out_field """

            fms.addFieldMap(fldmapname)
            print("Added " + outFldname + " to field map")
            idx += 1
            iz += 2
        """ # Optional: Rename the output field in the point feature class
        field_name = poly_field_map.getFieldName(0)
        field_name = "AssignedCity" # New name
        poly_field_map.field = poly_field_map.field # Keep properties
        poly_field_map.outputField = field_name # Set new name """

        # 4. Add the configured field map to the mappings
        # fms.addFieldMap(poly_field_map)
        if arcpy.Exists(SAMFC):
            arcpy.Delete_management(SAMFC)
        # if not arcpy.Exists(SAMFC):
        arcpy.env.extent = outFC
        arcpy.analysis.SpatialJoin(
            target_features=outFC,
            join_features=outSAMFCFull,
            out_feature_class=SAMFC,
            join_operation="JOIN_ONE_TO_ONE",
            join_type="KEEP_ALL",
            field_mapping=fms,
            match_option="INTERSECT")
        print("Spatial Join for " + type + " complete")  
    return(SAMFC)

def runER(arg1, arg2):
    # Environmental remediation: parcel poly overlaps point features
    RDinit = arg1
    RDpubFC = arg2
    outFC = RDinit + "_ER"
    envremedFC = r'C:\working\GISdata\BCGW\SITE_ENV_RMDTN_SITES_SVW.gdb\WHSE_WASTE_SITE_ENV_RMDTN_SITES_SVW'
    crownremedFC = r'C:\working\GISdata\BCGW\crowncontaminatedsites2024\ActiveProgramSites2024.shp'
    # 1. Create FieldMappings Object
    fms = arcpy.FieldMappings()
    fms.removeAll()

    # 2. Add all existing fields from the target points

    fms.addTable(RDpubFC)

    # 3. Create a FieldMap to bring over a specific polygon attribute
    # Example: Bringing "CityName" from polygon to points

    fldmapname = RDinit + "_remedfldmap"
    remfldname = "ENV_RMDTN_SITES_ID"
    fldmapname = arcpy.FieldMap()
    fldmapname.addInputField(envremedFC, remfldname)

    # 4. Add the configured field map to the mappings
    fms.addFieldMap(fldmapname)

    # 5. Run Spatial Join
    outFC = RDinit + "_remed"
    arcpy.analysis.SpatialJoin(
        target_features=RDpubFC,
        join_features=envremedFC,
        out_feature_class=outFC,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        field_mapping=fms,
        match_option="INTERSECT")
    print("Spatial Join for " + outFC + " complete")   

    # Spatial Join Crown Remediation

    inFC = outFC
    outFC = RDinit + "_EnviroRem"
    # 1. Create FieldMappings Object
    fms = arcpy.FieldMappings()
    fms.removeAll()

    # 2. Add all existing fields from the target points

    fms.addTable(inFC)

    # 3. Create a FieldMap to bring over a specific polygon attribute
    # Example: Bringing "CityName" from polygon to points

    fldmapname = RDinit + "_remedcrnfldmap"
    remfldname = "SITE_BY_RE"
    fldmapname = arcpy.FieldMap()
    fldmapname.addInputField(crownremedFC, remfldname)

    # 4. Add the configured field map to the mappings
    fms.addFieldMap(fldmapname)


    arcpy.analysis.SpatialJoin(
        target_features=inFC,
        join_features=crownremedFC,
        out_feature_class=outFC,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        field_mapping=fms,
        match_option="INTERSECT")
    print("Spatial Join for " + outFC + " complete")  
    return(outFC)

def runDA(arg1, arg2):
    # Development areas: centroid of parcel poly must be inside DA poly
    RDinit = arg1
    centroidFC = arg2
    # RDpubFC = arg2
    outFC = RDinit + "_DA"
    toaFC = r'C:\working\GISdata\BC_TODA\BC_TODA.gdb\BC_TOA_tiers_0'
    majortransitFC = r'C:\working\GISdata\MetroVanRD\Major_Transit_Growth_Corridor__MTGC.gdb\Major_Transit_Growth_Corridor__MTGC_'
    urbancentreFC = r'C:\working\GISdata\MetroVanRD\Urban_Centre__UC.gdb\Urban_Centre__UC_'
    
    # Spatial Join TOA
    # 1. Create FieldMappings Object
    fms = arcpy.FieldMappings()
    fms.removeAll()

    # 2. Add all existing fields from the target

    fms.addTable(centroidFC)

    # 3. Create a FieldMap to bring over a specific polygon attribute
    
    toafldname = "Tier"
    fm_toa = arcpy.FieldMap()
    fm_toa.addInputField(toaFC, toafldname)

    toa_fld = fm_toa.outputField
    toa_fld.name = "TOA_Tier"
    toa_fld.aliasName = "TOA Tier"
    fm_toa.outputField = toa_fld

    # 4. Add the configured field map to the mappings
    fms.addFieldMap(fm_toa)

    # 5. Run Spatial Join
    outFC = RDinit + "_toa"
    arcpy.analysis.SpatialJoin(
        target_features=centroidFC,
        join_features=toaFC,
        out_feature_class=outFC,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        field_mapping=fms,
        match_option="INTERSECT")
    print("Spatial Join for " + outFC + " complete")   

    # Spatial Join Major Transit Growth Areas

    inFC = outFC
    outFC = RDinit + "_MTGA"

    # 1. Create FieldMappings Object
    fms = arcpy.FieldMappings()
    fms.removeAll()

    # 2. Add all existing fields from the target 
    fms.addTable(inFC)

    # 3. Create a FieldMap to bring over a specific polygon attribute
    # fldmapname = RDinit + "_mtgafldmap"
    mtgafldname = "Name"
    fm_mtga = arcpy.FieldMap()
    fm_mtga.addInputField(majortransitFC, mtgafldname)
    mtga_fld = fm_mtga.outputField
    mtga_fld.name = "MTGA"
    mtga_fld.aliasName = "MTGA Name"
    fm_mtga.outputField = mtga_fld

    # 4. Add the configured field map to the mappings
    fms.addFieldMap(fm_mtga)


    arcpy.analysis.SpatialJoin(
        target_features=inFC,
        join_features=majortransitFC,
        out_feature_class=outFC,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        field_mapping=fms,
        match_option="INTERSECT")
    print("Spatial Join for " + outFC + " complete")  

    # Spatial Join Urban Centres
    inFC = outFC
    outFC = RDinit + "_UC"

    # 1. Create FieldMappings Object
    fms = arcpy.FieldMappings()
    fms.removeAll()

    # 2. Add all existing fields from the target 
    fms.addTable(inFC)

    # 3. Create a FieldMap to bring over a specific polygon attribute
    # fldmapname = RDinit + "_ucfldmap"
    ucfldname = "Name"
    fm_uc = arcpy.FieldMap()
    fm_uc.addInputField(urbancentreFC, ucfldname)
    uc_fld = fm_uc.outputField
    uc_fld.name = "UrbanCentre"
    uc_fld.aliasName = "Urban Centre"
    fm_uc.outputField = uc_fld

    # 4. Add the configured field map to the mappings
    fms.addFieldMap(fm_uc)


    arcpy.analysis.SpatialJoin(
        target_features=inFC,
        join_features=urbancentreFC,
        out_feature_class=outFC,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        field_mapping=fms,
        match_option="INTERSECT")
    print("Spatial Join for " + outFC + " complete")  

    return(outFC)

def runOCPZone(arg1, arg2):
    # Parcel centroid in OCP zone
    RDinit = arg1
    centroidFC = arg2
    outFC = RDinit + "_OCPZone"
    OCPFC = r'C:\working\GISdata\ICIS\OCPFeb2026\LG_OCP.gdb\LG_OCP'
    zoneFC = r'C:\working\GISdata\ICIS\ZoningFeb2026\LG_Zoning.gdb\LG_ZONING'
    
    # Spatial Join Zoning
    # 1. Create FieldMappings Object
    fms = arcpy.FieldMappings()
    fms.removeAll()

    # 2. Add all existing fields from the target points

    fms.addTable(centroidFC)

    # 3. Create a FieldMap to bring over a specific polygon attribute
    # Example: Bringing "CityName" from polygon to points

    fldmapname = RDinit + "_zonefldmap"
    zonefldname = "General_Zone"
    fldmapname = arcpy.FieldMap()
    fldmapname.addInputField(zoneFC, zonefldname)

    # 4. Add the configured field map to the mappings
    fms.addFieldMap(fldmapname)

    # 5. Run Spatial Join
    outFC = RDinit + "_Zone"
    arcpy.analysis.SpatialJoin(
        target_features=centroidFC,
        join_features=zoneFC,
        out_feature_class=outFC,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        field_mapping=fms,
        match_option="INTERSECT")
    print("Spatial Join for " + outFC + " complete")   

    # Spatial Join OCP

    inFC = outFC
    outFC = RDinit + "_ZoneOCP"
    # 1. Create FieldMappings Object
    fms = arcpy.FieldMappings()
    fms.removeAll()

    # 2. Add all existing fields from the target points

    fms.addTable(inFC)

    # 3. Create a FieldMap to bring over a specific polygon attribute
    # Example: Bringing "CityName" from polygon to points

    fldmapname = RDinit + "_OCPfldmap"
    OCPfldname = "ICI_OCP_CLASS"
    fldmapname = arcpy.FieldMap()
    fldmapname.addInputField(OCPFC, OCPfldname)

    # 4. Add the configured field map to the mappings
    fms.addFieldMap(fldmapname)


    arcpy.analysis.SpatialJoin(
        target_features=inFC,
        join_features=OCPFC,
        out_feature_class=outFC,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        field_mapping=fms,
        match_option="INTERSECT")
    print("Spatial Join for " + outFC + " complete")  
    return(outFC)

def runSoil(arg1, arg2):
    # Parcel centroid point in soil poly
    RDinit = arg1
    centroidFC = arg2
    outFC = RDinit + "_Soil"
    soilsFC = r'C:\working\GISdata\Soil\SOIL.gdb\STE_Soil_S_Polygon' 
        
    # Spatial Join Zoning
    # 1. Create FieldMappings Object
    fms = arcpy.FieldMappings()
    fms.removeAll()

    # 2. Add all existing fields from the target points

    fms.addTable(centroidFC)

    # 3. Create a FieldMap to bring over a specific polygon attribute
    # Example: Bringing "CityName" from polygon to points

    fldmapname = RDinit + "_soilfldmap"
    zonefldname = "DrainageClass"
    fldmapname = arcpy.FieldMap()
    fldmapname.addInputField(soilsFC, zonefldname)

    # 4. Add the configured field map to the mappings
    fms.addFieldMap(fldmapname)

    # 5. Run Spatial Join
    arcpy.analysis.SpatialJoin(
        target_features=centroidFC,
        join_features=soilsFC,
        out_feature_class=outFC,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        field_mapping=fms,
        match_option="INTERSECT")
    print("Spatial Join for " + outFC + " complete")   

    return(outFC)

def fireThreat(arg1, arg2):
    # Parcel centroid point in fire threat zone poly
    RDinit = arg1
    centroidFC = arg2
    outFC = RDinit + "_FireThreat"
    firethreatFC = r'C:\working\GISdata\BCGW\PROT_PSTA_FIRE_THREAT_RTG_SP.gdb\PROT_PSTA_FIRE_THREAT_RTG_SP' 
        
    # Spatial Join Zoning
    # 1. Create FieldMappings Object
    fms = arcpy.FieldMappings()
    fms.removeAll()

    # 2. Add all existing fields from the target points

    fms.addTable(centroidFC)

    # 3. Create a FieldMap to bring over a specific polygon attribute
    # Example: Bringing "CityName" from polygon to points

    fldmapname = RDinit + "_firefldmap"
    zonefldname = "FIRE_THREAT_CLASS_DESC"
    fldmapname = arcpy.FieldMap()
    fldmapname.addInputField(firethreatFC, zonefldname)

    # 4. Add the configured field map to the mappings
    fms.addFieldMap(fldmapname)

    # 5. Run Spatial Join
    arcpy.analysis.SpatialJoin(
        target_features=centroidFC,
        join_features=firethreatFC,
        out_feature_class=outFC,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        field_mapping=fms,
        match_option="INTERSECT")
    print("Spatial Join for " + outFC + " complete")   

    return(outFC)

def getFloodRisk(arg1, arg2):
    # Value of Flood risk raster at parcel centroid point
    RDinit = arg1
    centroidFC = arg2
    outFC = RDinit + "_FloodRisk"
    floodGrd = r'C:\working\GISdata\NRCan\FS-national-2015-class.tif' 
    ExtractValuesToPoints(centroidFC, floodGrd, outFC, "NONE", "VALUE_ONLY")

    print("Flood risk values extracted to "  + outFC)

    return(outFC)



def main():
    print("done")

if __name__ == "__main__":
    main()