'''
lidarBC_import_tifs.py
This file gets DEM TIFs from Lidar BC using a Regional District buffered public land layer (output of RDPubExtent.py for that RD)
to clip the Lidar BC index file. TIFF files from both the 2500 and 20000 map grids are downloaded.
- Index listing https://governmentofbc.maps.arcgis.com/home/item.html?id=5f6a1f31212a4cb2826743d2e52ef02a
- Index feature server https://services6.arcgis.com/ubm4tcTYICKBpist/arcgis/rest/services/LiDAR_BC_S3_Public/FeatureServer
-  (this folder contains feature classes for various scales of dsm and dem tif files and point cloud files)
Set LBCworkspace to the location to store the TIFF files.  DEM2500 and DEM20000 subdirectories will be created.
Note: These are large files 
Note: RD must be updated
Note: Lots of print statements for debugging, TIF files downloaded are counted.
Note: Temp directory created: could be removed to save space. 
Ian Parfitt 27 August 2025
'''
import arcpy
import requests
import os
from pathlib import PurePosixPath
from pathlib import Path
import shutil

arcpy.env.overwriteOutput = True

# Example TIF URL: https://nrs.objectstore.gov.bc.ca/gdwuts/092/092b/2023/dem/bc_092b023_xli1m_utm10_20231125_20231125.tif
baseURL = r'https://nrs.objectstore.gov.bc.ca/gdwuts/'
exampleTif = r'092/092b/2023/dem/bc_092b023_xli1m_utm10_20231125_20231125.tif'
outtest = exampleTif.replace('\\', '/')
#print(outtest)
tempfull = os.path.join(baseURL, outtest)
#print(tempfull)
tempoutTif = '092/092b/2023/dem/bc_092b023_xli1m_utm10_20231125_20231125.tif'

RD = 'Regional District of Bulkley-Nechako'
RDinit = 'RDBN'
verMonth = 'June'
print("Running " + RD)
RDwksp = r'C:\working\ArcProjects\workspace' 
RDgdb = RDinit + 'Pub' + verMonth + '.gdb'
RDhome = os.path.join(RDwksp, RDgdb)
if not arcpy.Exists(RDhome):
    arcpy.management.CreateFileGDB(RDwksp, RDgdb)
    print(RDgdb + " created")

LBCworkspace = r'C:\working\GISdata\LidarBC'
LBCRDworkspace = os.path.join(LBCworkspace,RDinit)

RDbndFC = "Public_" + RDinit + "_buf1000"  # output of RDPubExtent.py
RDbndFP = os.path.join(RDhome, RDbndFC)
print("Using " + RDbndFC)

for scale in (20000, 2500):
    print("Downloading DEM" + str(scale))
    scaleWksp = "DEM" + str(scale)
    RDscaleWksp = os.path.join(LBCRDworkspace, scaleWksp)
    os.makedirs(RDscaleWksp, exist_ok=True)
    tempscaleWksp = "DEM" + str(scale) + "temp"
    tempRDscaleWksp = os.path.join(LBCRDworkspace, tempscaleWksp)
    os.makedirs(tempRDscaleWksp, exist_ok=True)
    arcpy.env.workspace = RDscaleWksp
    sourceIdx = RDinit + "_source" + str(scale) + "Index"
    # sourceIndex = r'C:\working\ArcProjects\workspace\LidarBC.gdb\Ldar_DSM_2500_MVRD'
    if scale == 20000:
        LBC_DEMIdx = r'https://services6.arcgis.com/ubm4tcTYICKBpist/arcgis/rest/services/LiDAR_BC_S3_Public/FeatureServer/6'
        lend_idx = 16
        dend_idx = 27
    elif scale == 2500:
        LBC_DEMIdx = r'https://services6.arcgis.com/ubm4tcTYICKBpist/arcgis/rest/services/LiDAR_BC_S3_Public/FeatureServer/5'
        lend_idx = 52
        dend_idx = 27
    if not arcpy.Exists(sourceIdx):
        arcpy.analysis.PairwiseClip(LBC_DEMIdx, RDbndFP, sourceIdx)
        print("Created " + sourceIdx)
        # if scale == 2500:
        #     LBC_DEMIdx = r'https://services6.arcgis.com/ubm4tcTYICKBpist/arcgis/rest/services/LiDAR_BC_S3_Public/FeatureServer/6'
        #     sourceeraseIdx = "source" + str(scale) + "20kEraseIndex"
        #     arcpy.analysis.PairwiseErase(sourceIdx,LBC_DEMIdx, sourceeraseIdx)
        #     sourceIdx = sourceeraseIdx
    # sourceIndex = r'C:\working\ArcProjects\workspace\CRDPubApr.gdb\CRD_25hun_eraselidardem'
    # sourceIndex = r'C:\working\ArcProjects\workspace\CRDPubApr.gdb\CRD_25hun_lidardemeast'  # to fill holes
    tifcount = 1
    with arcpy.da.SearchCursor(sourceIdx, ['filename', 'path']) as search_cursor:
        for row in search_cursor:
            outFile = row[0]
            path = row[1]
            print(outFile)
            if not 'dsm' in outFile:
                testsuffix = Path(outFile).suffix
                if testsuffix == ".laz":
                    start_idx = path.find("bc_")
                    lend_idx = path.find(".laz")
                    outFilestrp = path[start_idx:lend_idx] + ".laz"
                    outFile = path[start_idx:lend_idx] + ".tif"
                elif testsuffix == ".tif":
                    # outFilestrp = outFile[0:27] + ".tif"   For 20000 filenames
                    outFilestrp = outFile[0:dend_idx] + ".tif" 
                    outFilestrp = outFile
                print(outFilestrp)
                filePathMS = row[1]
                print(filePathMS)
                filePathstrp = filePathMS[1:]
                print(filePathstrp)
                filePath = filePathstrp.replace('\\', '/').replace("..", ".")
                print(filePath)
                fullinPath = os.path.join(baseURL,filePath)
                print(baseURL)
                fulloutPath = os.path.join(tempRDscaleWksp,outFilestrp)
                if testsuffix == ".laz":
                    fullfinalPath = os.path.join(RDscaleWksp,outFile)
                elif testsuffix == ".tif":    
                    fullfinalPath = os.path.join(RDscaleWksp,outFilestrp)
                    
                if not arcpy.Exists(fullfinalPath):
                    print(tempRDscaleWksp)
                    print(fullinPath)
                    req=requests.get(fullinPath, stream=True)
                    tifcount += 1
                    print(fulloutPath)
                    testsuffix = Path(outFilestrp).suffix
                    with open(fulloutPath, 'wb') as file:
                        file.write(req.content)
                        if testsuffix == ".laz":
                            try:
                                print('Should not be any las files')
                                shutil.copy2(fulloutPath,fullfinalPath)
                                # arcpy.conversion.ConvertLas(fulloutPath,lidarfinalWorkspace)
                            except arcpy.ExecuteError:
                                # Catches specific errors raised by ArcGIS tools
                                print("\nAn ArcGIS execution error occurred:")
                                # Print the tool's error messages
                                print(arcpy.GetMessages(2)) 
                                # sys.exit(1)
                        else:
                            print("Copy to final")
                            shutil.copy2(fulloutPath,fullfinalPath)         
                else:
                    print(fulloutPath + " already exists")
            #  time.sleep(2)
    print(tifcount)
print("Done")