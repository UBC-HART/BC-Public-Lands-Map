'''
JoinUtil.py

The join functions were moved to this utility file for clarity.
This file requires that the utility python file FunctionUtils.py is present in the same folder.

Lots of print statements added during debugging.

Ian Parfitt  27 Aug 2026
'''

import arcpy
import os

from FunctionUtils import sum_gross_improve, merge_land_char

arcpy.env.overwriteOutput = True

#Set working directories and gdbs
Workdir = r'C:\working\ArcProjects\workspace'
ScratchWksp = r'C:\working\ArcProjects\scratch\scratchworkspace.gdb'

BCPubLayer = r'C:\working\ArcProjects\workspace\BCPubOct.gdb\BC_PubIndexJan_20260118' # Created with ParcelMap_SelectBCPub.py

def joinit(arg1, arg2):
    print("Running joinit")
    jc = arg1
    RDinit = arg2
    Workgdb = RDinit + "PubJune.gdb"
    outGDB = os.path.join(Workdir, Workgdb)
    arcpy.env.workspace = outGDB
    # RDgdb = r'C:\working\ArcProjects\workspace\VanPubNov.gdb'
    RDbndLayer = RDinit + "_Bndry"
    arcpy.env.extent = RDbndLayer
   
    # jcn = arg1
    # jc = str(jcn)
    print("Running " + jc)

    # Variables and fields for joining
    inLayer = r'C:\working\GISdata\BCA\BCASpatial\Data\bca_spatial_20260109.gdb\Legal_Description'
    
    ADMINGroup = "ADMIN_AREA_GROUP_NAME"
    ADMINName = "ADMIN_AREA_NAME"
    ADMINAbrev = "ADMIN_AREA_ABBREVIATION"
    JURISCode = "JURISDICTION_CODE"
    Layer_fields = [ADMINName, JURISCode]
   
    # Selected fields from the Legal Description, General, Description, General Character,and Address patial layers
    # and Residential and NonResidential Index text files
    ourLegalfields = ["ROLL_NUMBER","FOLIO_ID", "FOLIO_STATUS","FOLIO_STATUS_DESCRIPTION","JURISDICTION_CODE","JURISDICTION","PID_NUMBER","FIRST_NATION_RESERVE_DESC","AIR_SPACE_PARCEL_NUMBER"]
    method = "KEEP_FIELDS"
        
    ourGnrFieldJoin = ["GEN_VALUES_COUNT", "sum_Gen_Gross_Improvement_Value", "sum_Gen_Gross_Land_Value", \
                    "GEN_PROPERTY_CLASS_CODE" , "GEN_PROPERTY_CLASS_DESC"]  
    # redundant fields removed from  ourGnrFieldJoin: "GEN_NET_IMPROVEMENT_VALUE", "GEN_NET_LAND_VALUE", "GEN_TXXMT_IMPROVEMENT_VALUE", "GEN_TXXMT_LAND_VALUE", \
    ourDescFieldJoin = ["ACTUAL_USE_CODE", "ACTUAL_USE_DESCRIPTION", "ALR_CODE", "ALR_DESCRIPTION", \
                    "NEIGHBOURHOOD_CODE","NEIGHBOURHOOD","MANUAL_CLASS_CODE","MANUAL_CLASS_DESCRIPTION"]
    ourCharFieldJoin = ["LAND_CHARACTERISTICS_COUNT", "merge_Land_Character_Code", "merge_Land_Character_Desc"] 
    ourAddressFieldJoin = ["STREET_DIRECTION_PREFIX", "STREET_NUMBER","STREET_NAME","STREET_TYPE","STREET_DIRECTION_SUFFIX", "CITY","POSTAL_CODE"]
    ourResIndexFieldJoin = ["Jurisdiction","Roll_Number","Area","MB_Year_Built","MB_Effective_Year","MB_Total_Finished_Area","MB_Num_Storeys","Land_Characteristic_Code_1","Land_Characteristic_Code_2",\
                        "Land_Characteristic_Code_3","Land_Characteristic_Code_4","Land_Characteristic_Code_5","Land_Characteristic_Code_6", \
                        "Other_Building_Flag","Land_Metric_Flag","Land_Width_Width","Land_Depth_Depth","Land_Sq_Measure","Land_Area_Total", \
                        "Inc_Occupancy_Code","School_District","Zoning"]
    ourNonResIndexFieldJoin = ["Jurisdiction","Roll_Number","Year_Built","Effective_Year","Number_of_Storeys","Gross_Leasable_Area","Net_Leasable_Area", \
                            "Number_of_Units_in_an_Co-op","Predominant_Manual_Class","Gross_Building_Area","Strata_Industrial_Commercial_Lot_Area", \
                            "Apartment-Number_of_Units","Senior_Housing-Number_of_Units","Other_Buildings","School_District","Zoning"]

    # Start cursor loop. 
    # NOTE: JURISDICTION_CODE (jc) is a string, Jurisdiction is a number

    # Create a layer file from the legal description to use for joining
    legal_lyr = "legalLyr" + jc
    result = arcpy.management.GetCount(inLayer)
    feature_count = int(result.getOutput(0))
    # print(f"The feature class '{inLayer}' contains {feature_count} features.")
    tempLegalLayer = arcpy.management.SelectLayerByAttribute(inLayer, "CLEAR_SELECTION")
    result = arcpy.management.GetCount(inLayer)
    feature_count = int(result.getOutput(0))
    # print(f"The feature class '{inLayer}' contains {feature_count} features after clearing selection.")
    result = arcpy.management.GetCount(tempLegalLayer)
    feature_count = int(result.getOutput(0))
    # print(f"The layer '{tempLegalLayer}' contains {feature_count} features after clearing selection.")


    if arcpy.Exists(legal_lyr):
        arcpy.Delete_management(legal_lyr)
    arcpy.management.MakeFeatureLayer(inLayer, legal_lyr)
    result = arcpy.management.GetCount(legal_lyr)
    feature_count = int(result.getOutput(0))
    # print(f"The feature class '{legal_lyr}' contains {feature_count} features.")

    # Create legal layer for the jc and join to the public land data
    outLayer = "Legal_" + jc
    # print(outLayer)
    where_clause = f'"{JURISCode}" = \'{jc}\''
    if arcpy.Exists(outLayer):
        arcpy.Delete_management(outLayer)
    if not arcpy.Exists(outLayer):
        where_clause = f'"{JURISCode}" = \'{jc}\''     
        tempoutLayer = arcpy.management.SelectLayerByAttribute(legal_lyr,"CLEAR_SELECTION")
        tempoutLayer = arcpy.management.SelectLayerByAttribute(legal_lyr,"NEW_SELECTION", where_clause )
        result = arcpy.management.GetCount(tempoutLayer)
        selected_feature_count = int(result.getOutput(0))
        # print(f"Number of selected features in '{tempoutLayer}': {selected_feature_count}")  
        arcpy.management.CopyFeatures(tempoutLayer,outLayer)
        arcpy.management.SelectLayerByAttribute(tempoutLayer, "CLEAR_SELECTION")

        feature_count = arcpy.management.GetCount(outLayer).getOutput(0)
        # print(f"The feature class '{outLayer}' contains {feature_count} features.")

        arcpy.Delete_management(legal_lyr)
        
        
        # arcpy.analysis.Select(inLayer, outLayer, where_clause)
        arcpy.management.DeleteField(outLayer,ourLegalfields, method)
        arcpy.management.AddIndex(outLayer, ["PID_NUMBER","ROLL_NUMBER","FOLIO_ID"], "PIDRollFolioIndex","UNIQUE", "NON_ASCENDING")
        print(outLayer + " created")

        # Join to BC Public Land data
        print("Joining to BC Public Land")
        lstFields = arcpy.ListFields(outLayer)
        OwnerField = "OwnerType"
        InJoinField = "PID_NUMBER"
        JoinField = "PID"
        Owner = False
        for field in lstFields:
            # print(field.name)
            if field.name == OwnerField:
                print("Field " + OwnerField + " exists")
                Owner = True
        if Owner != True:
                arcpy.management.JoinField(outLayer, InJoinField, BCPubLayer, JoinField, [OwnerField])
                print("Joined " + outLayer + " to " + BCPubLayer + " on " + JoinField)
            # pubLayerOld = "Pub_" + JURISCode
            # if arcpy.Exists(pubLayerOld):
            #    arcpy.management.Delete(pubLayerOld)

    # Create Public Land layer for the jurisdiction by deleting records with no Ownertype after joining legal layer to BC Public Land layer
    pubLayer = "Pub_" + jc
    OwnerField = "OwnerType"
    where_clause = f'"{OwnerField}" IS NOT NULL'
    pubLyr = pubLayer + "Lyr"
    
    # print(where_clause)
    if arcpy.Exists(pubLayer):
        arcpy.Delete_management(pubLayer)
    if not arcpy.Exists(pubLayer):
        arcpy.management.SelectLayerByAttribute(outLayer, "CLEAR_SELECTION")
        arcpy.analysis.Select(outLayer, pubLayer, where_clause)
        print(pubLayer + " created")
        feature_count = arcpy.management.GetCount(pubLayer).getOutput(0)
        # print(f"The feature class '{pubLayer}' contains {feature_count} features.")


    InJoinField = "FOLIO_ID"
    JoinField = "FOLIO_ID"
    disLayer = pubLayer + "_dis"
    disLyr = disLayer + "Lyr"
    pidnumFld = "PID_NUMBER"
    arcpy.Delete_management(tempoutLayer)
    if arcpy.Exists(tempoutLayer):
        print("Unable to delete tempoutLayer")
    if arcpy.Exists(disLyr):
        arcpy.Delete_management(disLyr)
    if arcpy.Exists(pubLyr):
        arcpy.Delete_management(pubLyr)  
    if arcpy.Exists(disLayer):
        print("Deleting " + disLayer)
        arcpy.Delete_management(disLayer)
    arcpy.management.MakeFeatureLayer(pubLayer, pubLyr)
    if not arcpy.Exists(disLayer):
        print("Running Pairwise Dissolve on " + pubLayer)
        arcpy.analysis.PairwiseDissolve(pubLayer, disLayer, ["FOLIO_ID"])
        print(disLayer + " created")
        
        testdisLayer = disLayer + "_test"
        # arcpy.management.CopyFeatures(disLayer,testdisLayer)
        feature_count = arcpy.management.GetCount(disLayer).getOutput(0)
        print(f"The feature class '{disLayer}' contains {feature_count} features.")
    arcpy.management.MakeFeatureLayer(disLayer, disLyr )    
    arcpy.management.JoinField(disLyr, InJoinField, pubLyr, JoinField)  
    
    if arcpy.Exists(pubLyr):
        arcpy.Delete_management(pubLyr)
    PIDIndex = "PIDindex"
    found_PIDIndex = False
    indexes = arcpy.ListIndexes(disLyr)
    for index in indexes:
        if index.name == PIDIndex:
            found_PIDIndex = True
            break
    if not found_PIDIndex:
        arcpy.management.AddIndex(disLyr, pidnumFld, PIDIndex,"UNIQUE", "NON_ASCENDING")
    
    # Run FunctionUtils functions
    sumGPVLayer = "sum_gen_prop_values_" + jc
    sumGPVLayer = sum_gross_improve(jc, disLyr)

    # pubLayer = "Pub_" + jc
    print("summing complete")
    print(sumGPVLayer)

    mergeLCLayer = "merge_land_char_" + jc
    mergeLCLayer = merge_land_char(jc, disLyr)

    print("merging complete")
    print(mergeLCLayer)

    # Set variables for joining
    inJoinField = 'FOLIO_ID'
    JoinField = "FOLIO_ID"
    inRollField = "ROLL_NUMBER"
    RollField = "Roll_Number"
    ourDescTab = r'C:\working\GISdata\BCA\BCASpatial\Data\bca_spatial_20260109.gdb\Descriptions'
    ourCharTab = "merge_land_char_" + jc
    ourGnrTab = "sum_gen_prop_values_" + jc
    ourAddressTab = r'C:\working\GISdata\BCA\BCASpatial\Data\bca_spatial_20260109.gdb\Addresses'
    ourNonResInv = r'C:\working\GISdata\BCA\NonResidentialInventory\Data\nonresidentialInventory.gdb\NonResidential_20260101'
    # Find Assessment Area for jurisdiction
    if jc in ("213","234","302","307","308","309","317","327","332","344","349","361","362","363","389","401","402","476","761","762","763","764"):
        aa = "01"
    elif jc in ("207","223","250","315","350","351","404","405","406","408","445","446","539","559","565","580","583","765","766","768","768","769","769","770"):
        aa = "04"
    elif jc in ("204","330","334","336","347","409","412","416","502","516","526","558","563","571","575","592","747","771","772","784","784","785"):
        aa = "06"
    elif jc in ("221","316","321","328","338","346","390","524","537","560","570","744","745","746","748","748"):
        aa = "08"
    elif jc in ("200","631","739"):
        aa = "09"
    elif jc in ("220","224","225","301","305","501","504","743"):
        aa = "10"
    elif jc in ("306","320","403"):
        aa = "11"
    elif jc in ("236","326","736"):
        aa = "14"
    elif jc in ("216","303","310","311","312","313","314","319","432","527","732","732","733","734","742","775","775","776"):
        aa = "15"
    elif jc in ("210","211","222","325","535","547","555","556","562","712","713","714","715","715","716","717","777"):
        aa = "17"
    elif jc in ("214","217","318","331","364","723"):
        aa = "19"
    elif jc in ("202","208","228","233","304","322","323","348","541","719","722","789","789"):
        aa = "20"
    elif jc in ("201","219","229","232","413","521","533","548","551","553","569","572","573","588","707","709","710","711","786","786"):
        aa = "21"  
    elif jc in ("205","209","215","337","426","517","532","567","568","701","702","703","704","718"):
        aa = "22"
    elif jc in ("212","345","352","451","503","508","512","515","536","538","540","542","544","724","726","729","730","730","731"):
        aa = "23"
    elif jc in ("391","470","492","557","727","727","728","749"):
        aa = "24"
    elif jc in ("227","329","339","340","341","342","407","410","411","414","415","478","528","529","549","564","566","578","750","752","754","780","787","787","788","792"):
        aa = "25"
    elif jc in ("226","335","506","519","520","525","545","584","585","755","755","756","756","756","757"):
        aa = "26"
    elif jc in ("206","255","333","343","420","514","561","577","759","760","781"):
        aa = "27"

    ourResInv = r'C:\working\GISdata\BCA\ResidentialInventory\Data_202601\residentialInventory.gdb\Residential_20260101_A' + aa
    print(ourResInv)
    
    # Join the dissolved layer to the spatial BCA tables
    arcpy.management.JoinField(disLyr, inJoinField, ourDescTab, JoinField, ourDescFieldJoin)
    print(ourDescTab + " Joined")
    arcpy.management.JoinField(disLyr, inJoinField, ourGnrTab, JoinField, ourGnrFieldJoin)
    print(ourGnrTab + " Joined")
    arcpy.management.JoinField(disLyr, inJoinField, ourCharTab, JoinField, ourCharFieldJoin)
    print(ourCharTab + " Joined")
    arcpy.management.JoinField(disLyr, inJoinField, ourAddressTab, JoinField, ourAddressFieldJoin)
    print(ourAddressTab + " Joined")
    arcpy.Delete_management(ourCharTab)
    arcpy.Delete_management(ourGnrTab)

    # Join the dissolved layer to the residential and non-residential inventory tables using the PID field
    pidFld = "PID"
    if not arcpy.ListIndexes(ourResInv, PIDIndex):
        arcpy.management.AddIndex(ourResInv, pidFld, PIDIndex,"UNIQUE", "NON_ASCENDING")
    arcpy.management.JoinField(disLyr, pidnumFld, ourResInv, pidFld, ourResIndexFieldJoin )
    print(ourResInv + " Joined")
    
    if not arcpy.ListIndexes(ourNonResInv, PIDIndex):
        arcpy.management.AddIndex(ourNonResInv, pidFld, PIDIndex,"UNIQUE", "NON_ASCENDING" )
    arcpy.management.JoinField(disLyr, pidnumFld, ourNonResInv, pidFld, ourNonResIndexFieldJoin )
    print(ourNonResInv + " Joined")
    # resinvtab = "resinvtab_" + jc + "20250401" 

    # Delete duplicate fields
    fieldList = arcpy.ListFields(disLyr,"*_1*" )
    for f in fieldList:
        print(f.name)
        substrings_to_check = ["Zoning", "Land_Characteristics_Code", "School_District"]
        if not any(sub in f.name for sub in substrings_to_check):
            print("Deleting " + f.name)
            arcpy.management.DeleteField(disLyr, f.name)

    return(disLayer)
