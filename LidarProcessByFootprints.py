# -*- coding: utf-8 -*-
"""
Created on Wed Feb 13 12:36:38 2019

@author: mxhensch
"""

import sys
#import time
import urllib.request, urllib.parse, urllib.error
import os
#from urllib.parse import urljoin
#from pathlib import Path
import arcpy 
from arcpy.sa import *

arcpy.Delete_management("in_memory")
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension('3D')
arcpy.CheckOutExtension('Spatial')

#fp = "LakeGeorgeSouth.txt"#'Chazy.txt'
fp = sys.argv[1]#'LakeGeorgeNorth.txt'
nm = os.path.splitext(fp)[0]

#Get footprints, make directories
ldr = r'F:/lidar'
os.chdir(ldr)

basepth = os.path.join(ldr,nm)
if not os.path.exists(basepth):
    os.mkdir(basepth)

outLAS = os.path.join(basepth,'lasD')
if not os.path.exists(outLAS):
    os.mkdir(outLAS)
    
outDEM = os.path.join(basepth,'DEM')
if not os.path.exists(outDEM):
    os.mkdir(outDEM)

outDSM = os.path.join(basepth,'DSM')
if not os.path.exists(outDSM):
    os.mkdir(outDSM)

outCnpy = os.path.join(basepth,'Canopy')
if not os.path.exists(outCnpy):
    os.mkdir(outCnpy)



#Progress bar for download
def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 1e2 / totalsize
        s = "\r%5.1f%% %*d / %d" % (
            percent, len(str(totalsize)), readsofar, totalsize)
        sys.stderr.write(s)
        if readsofar >= totalsize: # near the end
            sys.stderr.write("\n")
    else: # total size is unknown
        sys.stderr.write("read %d\n" % (readsofar,))
#download saver
def save(url, filename):
    urllib.request.urlretrieve(url, filename, reporthook)
    
#Download footprints
DOWNLOADS_DIR = os.path.join(basepth,'footprints')
if not os.path.exists(DOWNLOADS_DIR):
    os.mkdir(DOWNLOADS_DIR)

lines = open(fp).read().splitlines()
print("%d number of footprints to download"%len(lines))
for ur in lines:
    # Split on the rightmost / and take everything on the right side of that
    name = ur.rsplit('/', 1)[-1]
    #print(name)
    # Combine the name and the downloads directory to get the local filename
    fil = os.path.join(DOWNLOADS_DIR, name)
    if not os.path.exists(fil):
        save(ur, fil)
    else: print("%s exists"%name)
    
#Process LIDAR
sr = r'H:/GIS_data/ForestModeling/ADK/NAD_1983_UTM_Zone_18N.prj'
NAD = arcpy.SpatialReference(sr)
recursion = "NO_RECURSION"
surfCons = ''
cellSize = 1
zFactor = ""

#DEM by tile
# get file names
    
#os.listdir(DOWNLOADS_DIR)
arcpy.env.workspace = DOWNLOADS_DIR
lasFiles = [f for f in os.listdir(DOWNLOADS_DIR) if f.endswith(('.LAS','.las'))]
#lasFiles = lasFiles[0:10]
#f = lasFiles[0]
for f in lasFiles:
    print("Processing %s..."%f)
    ff = os.path.splitext(f)[0]
    lasD = os.path.join(outLAS, 'tmp.lasd')#; print lasD
    print("   Creating %s..."%lasD)
    arcpy.CreateLasDataset_management (os.path.join(DOWNLOADS_DIR,f), lasD, recursion, surfCons, sr)
    print("   %s created!"%lasD)
    #Create DEM
    outDEMras = os.path.join(outDEM, ff+'_DEM.tif')
    if not os.path.exists(outDEMras):
        print("Begin %s processing..."%(ff+'_DEM.tif'))
    
        lasDEM = arcpy.CreateUniqueName(ff+'_DEM')
        returnValue = ''#[2,9]#'ANY'#['LAST', 'SINGLE']
        class_code = [2,9]
        print("   Creating LAS layer...")
        arcpy.MakeLasDatasetLayer_management(lasD, lasDEM, class_code)
        print("   Creating surface...")
        arcpy.conversion.LasDatasetToRaster(lasDEM, outDEMras, 'ELEVATION','BINNING MINIMUM NATURAL_NEIGHBOR', 'FLOAT','CELLSIZE', cellSize, zFactor)
        print("   %s processing completed!"%(f+'_DEM.tif'))
    
    #Create DSM
    outDSMras = os.path.join(outDSM, ff+'_DSM.tif')
    if not os.path.exists(outDSMras):
        print("Begin %s processing..."%(ff+'_DSM.tif'))
        lasDSM = arcpy.CreateUniqueName(ff+'_DSM')
        #returnValue = [3,4,5]#['FIRST', 'SINGLE']#[3,4,5]
        class_code = [0,1,2,9]
        print("   Creating LAS layer...")
        arcpy.MakeLasDatasetLayer_management(lasD, lasDSM, class_code)
        print("   Creating surface...")
        arcpy.conversion.LasDatasetToRaster(lasDSM, outDSMras, 'ELEVATION','BINNING MAXIMUM NATURAL_NEIGHBOR', 'FLOAT','CELLSIZE', cellSize, zFactor)
        print("%s processing completed!"%(ff+'_DSM.tif'))
    
    ## Get tree height raster
    canopyHgt = os.path.join(outCnpy, ff+'_CH.tif')
    if not os.path.exists(canopyHgt):
        print("Begin processing %s..."%(ff+'_CH.tif'))
        tmpHgt = "in_memory/hgt"
        arcpy.Minus_3d(outDSMras, outDEMras, tmpHgt)
        outFocalStatistics = Con(tmpHgt,tmpHgt,0,"VALUE > 0")
        outFocalStatistics.save(canopyHgt)
        print("%s processing completed!"%(ff+'_CH.tif'))
    
    os.remove(lasD)
    arcpy.Delete_management("in_memory")

    print("LiDaR proceesing complete for %s"%f)

arcpy.env.workspace = basepth
os.chdir(basepth)
#mosaic DEM
print("Mosaicing DEM")
outName = nm+"_DEM.tif"
if not os.path.exists(outName):
    arcpy.env.workspace = outDEM
    inRas = arcpy.ListRasters("*DEM*","TIF")
    Ras = ';'.join(inRas)
    bands = arcpy.GetRasterProperties_management(inRas[1], "BANDCOUNT")
    arcpy.MosaicToNewRaster_management(Ras,ldr, outName, NAD,"32_BIT_FLOAT", "", bands)


#mosaic DSM
print("Mosaicing DSM")
outName = nm+"_DSM.tif"
if not os.path.exists(outName):
    arcpy.env.workspace = outDSM
    inRas = arcpy.ListRasters("*DSM*","TIF")
    Ras = ';'.join(inRas)
    bands = arcpy.GetRasterProperties_management(inRas[1], "BANDCOUNT")
    arcpy.MosaicToNewRaster_management(Ras,ldr, outName, NAD,"32_BIT_FLOAT", "", bands)

#mosaic Canopy heights
print("Mosaicing Canopy")
outName = nm+"_Canopy.tif"
if not os.path.exists(outName):
    arcpy.env.workspace = outCnpy
    inRas = arcpy.ListRasters("*CH*","TIF")
    Ras = ';'.join(inRas)
    bands = arcpy.GetRasterProperties_management(inRas[1], "BANDCOUNT")
    outMos = 'in_memory/mos'
    arcpy.MosaicToNewRaster_management(Ras,'in_memory', 'mos', NAD,"32_BIT_FLOAT", "", bands)
    OutCon = Con(Raster(outMos) < 0.05,0, Raster(outMos))
    
    outNull = SetNull(OutCon>50,OutCon)
    lake = 'F:/lidar/ADK_lakes.tif'
    outNoWater = Con(lake == 1,0, outNull)
    outNoWater.save(outName)