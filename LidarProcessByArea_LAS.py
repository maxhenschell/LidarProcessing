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

fp = 'Chazy.txt'#"LakeGeorgeSouth.txt"#
#fp = sys.argv[1]#'LakeGeorgeNorth.txt'
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

outCnpy = os.path.join(basepth,'CHM')
if not os.path.exists(outCnpy):
    os.mkdir(outCnpy)

sr = r'H:/GIS_data/ForestModeling/ADK/NAD_1983_UTM_Zone_18N.prj'

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
print("%d footprints to download"%len(lines))
for ur in lines:
    # Split on the rightmost / and take everything on the right side of that
    name = ur.rsplit('/', 1)[-1]
    #print(name)
    # Combine the name and the downloads directory to get the local filename
    fil = os.path.join(DOWNLOADS_DIR, name)
    if not os.path.exists(fil):
        save(ur, fil)
    else: print("%s exists"%name)
    
# Execute CreateLasDataset
lasD = os.path.join(outLAS, nm+'.lasd')#; print lasD
recursion = "NO_RECURSION"
surfCons = ''
if not os.path.exists(lasD):
    print("Creating %s..."%lasD)
    arcpy.management.CreateLasDataset(DOWNLOADS_DIR, lasD, recursion, surfCons, sr)
    print(" %s created!"%lasD)
else: print("%s exists!"%lasD)

cellSize = 2
zFactor = ""

arcpy.env.workspace = outLAS

#Create DEM
outDEMras = os.path.join(outDEM, nm+'_DEM_full.tif')
print("Begin %s processing..."%(nm+'_DEM_full.tif'))
lasDEM = arcpy.CreateUniqueName(nm+'_DEM_full')
returnValue = ''#[2,9]#'ANY'#['LAST', 'SINGLE']
class_code = [2,9]
print("   Creating LAS layer...")
arcpy.MakeLasDatasetLayer_management(lasD, lasDEM, class_code)
print("   Creating surface...")
arcpy.conversion.LasDatasetToRaster(lasDEM, outDEMras, 'ELEVATION','BINNING MINIMUM NATURAL_NEIGHBOR', 'FLOAT','CELLSIZE', cellSize, zFactor)
print("%s processing completed!"%nm+'_DEM.tif')

#Create DSM
outDSMras = os.path.join(outDSM, nm+'_DSM_full.tif')
print("Begin %s processing..."%(nm+'_DSM_full.tif'))
lasDSM = arcpy.CreateUniqueName(nm+'_DSM_full')
#returnValue = [3,4,5]#['FIRST', 'SINGLE']#[3,4,5]
class_code = [0,1,2,3,4,5,9]
print("   Creating LAS layer...")
arcpy.MakeLasDatasetLayer_management(lasD, lasDSM, class_code)
print("   Creating surface...")
arcpy.conversion.LasDatasetToRaster(lasDSM, outDSMras, 'ELEVATION','BINNING MAXIMUM NATURAL_NEIGHBOR', 'FLOAT','CELLSIZE', cellSize, zFactor)
print("%s processing completed!"%nm+'_DSM_full.tif')

## Get tree height raster
canopyHgt = os.path.join(outCnpy, nm+'_CHM_full.tif')
print("Begin processing %s..."%(nm+'_CHM_full.tif'))
tmpHgt = "in_memory/hgt"
arcpy.Minus_3d(outDSMras, outDEMras, tmpHgt)
outFocalStatistics = Con(tmpHgt,tmpHgt,0,"VALUE > 0")
outFocalStatistics.save(canopyHgt)
print("%s processing completed!"%nm+'_CHM_full.tif')

print("LiDaR proceesing complete for %s"%nm)