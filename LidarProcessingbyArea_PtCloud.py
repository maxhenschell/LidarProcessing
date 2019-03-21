'''*********************************************************************
Name: Get canopy heights from LIDAR
Description: This script demonstrates how to export
ground measurements from LAS files to a raster using a
LAS dataset.
*********************************************************************'''
# Import system modules
import arcpy 
import arcpy.sa 
from arcpy.sa import *
import os
import sys
import urllib.request, urllib.parse, urllib.error


arcpy.Delete_management("in_memory")
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension('3D')
arcpy.CheckOutExtension('Spatial')

#fp = 'Chazy.txt'
fp = sys.argv[1]#'LakeGeorgeNorth.txt'
nm = os.path.splitext(fp)[0]

#Get footprints, make directories
ldr = r'F:/lidar'
os.chdir(ldr)
basepth = os.path.join(ldr,nm)
outLAS = os.path.join(basepth,'lasD')

## Set local variables

gdbN = os.path.join(nm+'.gdb')
gdb = os.path.join(basepth,gdbN)

#Check if gdb exists, create if not
if not arcpy.Exists(gdb):
    arcpy.CreateFileGDB_management(basepth, gdbN)
    print(gdbN + " created")
else: print(gdbN + " exists")

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
DOWNLOADS_DIR = os.path.join(basepth,'footprints');wd = DOWNLOADS_DIR
if not os.path.exists(DOWNLOADS_DIR):
    os.mkdir(DOWNLOADS_DIR)
lines = open(fp).read().splitlines()
print("%d footprints to download"%len(lines))
for ur in lines:
    # Split on the rightmost / and take everything on the right side of that
    name = ur.rsplit('/', 1)[-1]
    # Combine the name and the downloads directory to get the local filename
    fil = os.path.join(DOWNLOADS_DIR, name)
    if not os.path.exists(fil):
        save(ur, fil)
    else: print("%s exists"%name)
    
## Execute CreateLasDataset
#lasD = os.path.join(outLAS, nm+'.lasd')#; print lasD
#recursion = "NO_RECURSION"
#surfCons = ''
#if not os.path.exists(lasD):
#    print("Creating %s..."%lasD)
#    arcpy.management.CreateLasDataset(DOWNLOADS_DIR, lasD, recursion, surfCons, sr)
#    print(" %s created!"%lasD)
#else: print("%s exists!"%lasD)
#statOut = os.path.join(outLAS,nm+"_stats.txt")
#arcpy.LasDatasetStatistics_management(lasD,"SKIP_EXISTING_STATS",statOut,"DATASET", "COMMA")

cellSize = 1
zFactor = ""

arcpy.env.workspace = outLAS
sr = r'H:/GIS_data/ForestModeling/ADK/NAD_1983_UTM_Zone_18N.prj'
cs = arcpy.SpatialReference(sr)

## Create multipoint feature
##Create all points multipoint feature
#AllPts = os.path.join(gdb, 'AllPts')
#if not arcpy.Exists(AllPts):
#    arcpy.LASToMultipoint_3d(wd, AllPts, 0.4, "","ANY_RETURNS", "", cs, "las", 1)
#    print(AllPts + " created")
#else: print(AllPts + " exists")
    
#Create veg multipoint feature
VegPts = os.path.join(gdb, 'VegPts')
if not arcpy.Exists(VegPts):
    classes = "0,1,2,3,4,5,9"
    rtns = "ANY_RETURNS"
    sfx = "las"
    attr = ""
    arcpy.LASToMultipoint_3d(wd,VegPts,cellSize, classes,rtns,attr,cs, sfx ,zFactor)
    print(VegPts + " created")
else: print(VegPts + " exists")
#Create ground multipoint feature
GrdPts = os.path.join(gdb, 'GrdPts')
if not arcpy.Exists(GrdPts):
    classes = "2,9"
    rtns = "ANY_RETURNS"
    sfx = "las"
    attr = ""
    arcpy.LASToMultipoint_3d(wd,GrdPts, cellSize,classes,rtns,attr,cs, sfx ,zFactor)
    print(GrdPts + " created")
else: print(GrdPts + " exists")

## Create DEM
Val = 'Shape.Z'
assignmentType = "MEAN"
priorityField = ""
cellSize = 2.5
preDEM = os.path.join(gdb, 'preDEM'); print(preDEM)
arcpy.PointToRaster_conversion(GrdPts, Val, preDEM, assignmentType, priorityField, cellSize)
outFocalStatistics = Con(IsNull(preDEM),FocalStatistics(preDEM, NbrRectangle(3, 3, "CELL"),"MEAN", "DATA"), preDEM)
DEM = os.path.join(gdb, 'DEM'); print (DEM)
outFocalStatistics.save(DEM)

## Create DSM-canopy
assignmentType = "MAXIMUM"
preDSM = os.path.join(gdb, 'preDSM'); print(preDSM)
arcpy.PointToRaster_conversion(VegPts, Val, preDSM, assignmentType, priorityField, cellSize)
outFocalStatistics = Con(IsNull(preDSM),FocalStatistics(preDSM, NbrRectangle(3, 3, "CELL"),"MEAN", "DATA"), preDSM)
DSM = os.path.join(gdb, 'DSM'); print(DSM)
outFocalStatistics.save(DSM)

## Get tree height raster
canopyHgt = os.path.join(gdb, 'CanopyHeight')
arcpy.Minus_3d(DSM, DEM, canopyHgt)

## END