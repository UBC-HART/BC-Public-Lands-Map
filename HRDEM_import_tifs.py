'''
HRDEM_import_tifs.py
This file gets DEM TIFs from the federal High Resolution DEM program (HRDEM) using an index created 
by a using a Regional District buffered public land layer (the output of RDPubExtent.py for that RD)
to clip the HRDEM index file.  
- Index source https://open.canada.ca/data/en/dataset/957782bf-847c-4644-a757-e383c0057995/resource/a74a0cb3-77ec-4049-9ab5-fad48680b62d
Note:  these are large files
Note: Set HRDWksp to the desired dowload directory.
Note: Temp folder created, could skip this step to save space
Downloaded TIF counter included.
Ian Parfitt 27 Aug 2026
'''
import arcpy
import requests
import os
from pathlib import PurePosixPath
from pathlib import Path
import shutil

arcpy.env.overwriteOutput = True

# https://nrs.objectstore.gov.bc.ca/gdwuts/092/092b/2023/dem/bc_092b023_xli1m_utm10_20231125_20231125.tif
baseURL = r'https://nrs.objectstore.gov.bc.ca/gdwuts/'
exampleTif = r'092/092b/2023/dem/bc_092b023_xli1m_utm10_20231125_20231125.tif'
outtest = exampleTif.replace('\\', '/')
#print(outtest)
tempfull = os.path.join(baseURL, outtest)
#print(tempfull)
tempoutTif = '092/092b/2023/dem/bc_092b023_xli1m_utm10_20231125_20231125.tif'
r'''demtempWorkspace = r'C:\working\GISdata\LidarBC\DEM2500\CRD\temp25hun'
os.makedirs(lidartempWorkspace, exist_ok=True)
demfinalWorkspace = r'C:\working\GISdata\LidarBC\DEM2500\CRD'
os.makedirs(lidarfinalWorkspace, exist_ok=True)'''

p = PurePosixPath(exampleTif)
print(str(p))
# print(str(exampleTif.as_posix))

# arcpy.env.workspace =lidarfinalWorkspace 


RD = 'Cowichan Valley Regional District'
RD = 'Strathcona Regional District'
RD = 'Regional District of Mount Waddington'
RD = 'Thompson-Nicola Regional District'
RD = 'qathet Regional District'
RD = 'Regional District of North Okanagan'
RD = 'Regional District of Central Okanagan'
RD = 'Central Coast Regional District'
RD = 'North Coast Regional District'
RD = 'Columbia Shuswap Regional District'
RD = 'Cariboo Regional District'
RD = 'Regional District of Fraser-Fort George'
RD = 'Northern Rockies Regional Municipality'
RD = 'Stikine Region (Unincorporated)'
RDinit = 'SUN'
verMonth = 'July'
RDWksp = r'C:\working\ArcProjects\workspace' 
RDgdb = RDinit + 'Pub' + verMonth + '.gdb'
RDhome = os.path.join(RDWksp, RDgdb)
HRDWksp = r'C:\working\GISdata\HRDEM'
HRDRDWksp = os.path.join(HRDWksp,RDinit)
os.makedirs(HRDWksp, exist_ok=True)
# ADMINGroup = "ADMIN_AREA_GROUP_NAME"
ADMINGroup = "ADMIN_AREA_NAME"
inFC = r'C:\working\GISdata\BCGW\ABMS_LGL_ADMIN_AREAS_SVW.gdb\WHSE_LEGAL_ADMIN_BOUNDARIES_ABMS_LGL_ADMIN_AREAS_SVW'
inLayer = inFC + "_lyr"
arcpy.management.MakeFeatureLayer(inFC, inLayer)
RDbndFC = RDinit + "_Bndry"
RDbndLyr = RDbndFC + "_lyr"
RDbndFP = os.path.join(RDhome, RDbndFC)
if not arcpy.Exists(RDbndFP):
            #Select Regional District from GeoBC local government layer, create RD boundary FC
            arcpy.management.MakeFeatureLayer(inFC, inLayer)
            where_clause = f'"{ADMINGroup}" = \'{RD}\''
            # print(where_clause)
            # if arcpy.Exists(outLayer):
            #    arcpy.Delete_management(outLayer)
            # if not arcpy.Exists(outLayer):
            arcpy.env.extent = inFC
            arcpy.management.SelectLayerByAttribute(inLayer, 'CLEAR_SELECTION')
            arcpy.management.SelectLayerByAttribute(inLayer, 'NEW_SELECTION', where_clause)
            arcpy.management.CopyFeatures(inLayer, RDbndFP)
            print(RDbndFP + " created")

print("Downloading HRDEM") 

tempWksp = "HRDEMtemp"
tempRDWksp = os.path.join(HRDRDWksp, tempWksp)
os.makedirs(tempRDWksp, exist_ok=True)
arcpy.env.workspace = HRDRDWksp
sourceIdx = RDinit + "_HRDEMsourceIndex"
# sourceIndex = r'C:\working\ArcProjects\workspace\LidarBC.gdb\Ldar_DSM_2500_MVRD'
RDbndFC = "Public_" + RDinit + "_buf1000"
RDbndFP = os.path.join(RDhome, RDbndFC)
HRD_DEMIdx = r'C:\working\GISdata\HRDEM\Datasets_Footprints.shp'
lend_idx = 16
dend_idx = 27

if not arcpy.Exists(sourceIdx):
    arcpy.analysis.PairwiseClip(HRD_DEMIdx, RDbndFP, sourceIdx)
    
tifcount = 1
with arcpy.da.SearchCursor(sourceIdx, ['tile_name', 'Ftp_dtm']) as search_cursor:
    for row in search_cursor:
        outFile = row[0]
        path = row[1]
        print(outFile)
        if not 'dsm' in outFile:
            outFilestrp = "hrd_" + outFile + ".tif"
            print(outFilestrp)
            """ filePathMS = row[1]
            print(filePathMS)
            filePathstrp = filePathMS[1:]
            print(filePathstrp)
            filePath = filePathstrp.replace('\\', '/').replace("..", ".")
            print(filePath) """
            fullinPath =path
            # print(baseURL)
            fulloutPath = os.path.join(tempRDWksp,outFilestrp)
            fullfinalPath = os.path.join(HRDRDWksp,outFilestrp)
                
            if not arcpy.Exists(fulloutPath):
                print(tempRDWksp)
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