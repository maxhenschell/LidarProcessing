# LidarProcessing
Process lidar data to create canopy models and DEMs  
LidarProcessingByArea_LAS creates an LAS file containing all of the selected footprints and processes products for the entire extent.  
LidarProcessingByArea_PtCloud creates point clouds from the entent of the lidar files and  processes products for the entire extent.  
While these create continuous surfaces (vs. LidarProcessingByFootprints, below) they DO NOT CURRENTLY WORK with py3.  
  
LidarProcessingByFootprints creates products (DEM,DSM, canopy model) for each footprint, then mosaics them. This leads to holes in the final products at the junction of the footprints. These can be imperfectly filled with the Elevation Void Fill function in ArcGIS.