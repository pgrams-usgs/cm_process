# CM_TIN_to_DEM
# Script to convert TIN to DEM outputs and produce data source and uncertainty outputs
#
# September 9, 2016
# Paul Grams 
#
##Input:
##1) Year data collected and segment.
##2) edited TIN.
##3) MB boundary. This is polygon defining area of multibeam data collection. It is created in
##     CM_XYZ_to_TIN.py. The file MB_Seg_*_*_bdy_elim should have interior "holes" removed.
##4) Topo boundary. Area of topographic surveys. Should be a shapefile in FinalTopo folder.
##5) All points. This is merged multibeam, singlebeam and topography points created in.
##     CM_XYZ_to_TIN.py. Should have just Point_X, Point_Y, Point_Z, and Source_year fields.
##Outputs: 
##1) DEM and hillshade at specified resolution;
##2) raster and polygon mask defining area of data coverage; 
##3) Data source polygon and rasters; 
##4) Point density raster; and
##5) Interpolation uncertainty raster.

import glob
import re
import sys
import string
import os
import arcpy
from arcpy import env

# Turn on history logging so that a history log file is written
arcpy.LogHistory = True

# Obtain a license for the 3D Analyst extension
arcpy.CheckOutExtension("3D")
from arcpy.sa import *

# spatial reference hardwired in
# Use the State Plane AZ Central projection file as input to the SpatialReference class
prjFile = r"C:\arcgis\Desktop10.0\Coordinate Systems\Projected Coordinate Systems\State Plane\NAD 1983 (Meters)\NAD 1983 StatePlane Arizona Central FIPS 0202 (Meters).prj"
spatialRef = arcpy.SpatialReference(prjFile)
arcpy.AddMessage(" ")
# Set the output Coordinate System
arcpy.env.outputCoordinateSystem = spatialRef
arcpy.AddMessage("Output Spatial Reference was set to " + str(prjFile))
arcpy.AddMessage(" ")

# Set environment settings
env.overwriteOutput = True

# Local variables...

# GUI variables
inYear = arcpy.GetParameterAsText(0) #Year data collected: String
inSegment = arcpy.GetParameterAsText(1) #Segment Name: String
inTIN = arcpy.GetParameterAsText(2) #Input TIN: TIN
inMBboundary = arcpy.GetParameterAsText(3) #Input mb boundary: Feature Layer (! use "elim" with holes removed)
inTopoBoundaryShape = arcpy.GetParameterAsText(4) #Input Topo Boundary: Feature Layer
inAllPts = arcpy.GetParameterAsText(5)  #Input merged points: Feature layer
outFolder = arcpy.GetParameterAsText(6) #Output folder: Workspace or Feature Dataset (USE FOLDER)
workspaceGDB = arcpy.GetParameterAsText(7) #Geodatabase: (empty output geodatabase not same as used for xyz to tin)
CellSize = arcpy.GetParameterAsText(8) #DEM Cell Size: String (default is 1)
DensitySearchRadius = arcpy.GetParameterAsText(9) #Point Density Search Radius: String (default is 5)

#
arcpy.AddMessage("Input TIN is: " + inTIN)
arcpy.AddMessage(" ")
arcpy.AddMessage("Output Folder is: " + outFolder)
arcpy.AddMessage(" ")


# Set environment settings
env.workspace = str(workspaceGDB)

###############################################
#
# need to find if cellsize is integer or decimal
# can't use decimal in filenames
#
CellSizeFloat = float(CellSize)
if CellSizeFloat == int(CellSizeFloat):
    # cellsize is an integer and use in filename
    CellSizeName = str(CellSize + "m")
else:
    temp = str(int(CellSizeFloat * 100))
    CellSizeName = str(temp + "cm")
arcpy.AddMessage("Cell Size is: " + CellSize + " m")
arcpy.AddMessage(" ")


###############################################
#
# get extent of TIN and set extent environment
#desc = inTIN.extent
tinDomain = str(outFolder + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + "TIN_domain.shp")
arcpy.TinDomain_3d(inTIN, tinDomain, "POLYGON")
desc = arcpy.Describe(tinDomain)
xminFloat = desc.extent.XMin
xmaxFloat = desc.extent.XMax
yminFloat = desc.extent.YMin
ymaxFloat = desc.extent.YMax
xmin = int(xminFloat)
xmax = int(xmaxFloat)
ymin = int(yminFloat)
ymax = int(ymaxFloat)
arcpy.AddMessage("X Min, X Max, Y Min, and Y Max are...")
arcpy.AddMessage(xmin)
arcpy.AddMessage(xmax)
arcpy.AddMessage(ymin)
arcpy.AddMessage(ymax)
arcpy.AddMessage("")
#
arcpy.env.extent = arcpy.Extent(xmin, ymin, xmax, ymax)
#
###############################################
# create DEM
outRaster = str(outFolder + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + CellSizeName + ".tif")
arcpy.AddMessage("output raster is: " + outRaster)
CellSizeStatement = str("CELLSIZE " + CellSize)
arcpy.TinRaster_3d(inTIN, outRaster, "FLOAT", "LINEAR", CellSizeStatement, 1)
#
# create mask for area of DEM
RasterMask = str(outFolder + "\\" + "Seg_" + inSegment + "_" + inYear + "_mask.tif")
arcpy.gp.Divide_sa(outRaster, outRaster, RasterMask)
RasterMaskInt = str(outFolder + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + CellSizeName + "_maskInt.tif")
arcpy.gp.Int_sa(RasterMask, RasterMaskInt)
arcpy.AddMessage("output raster mask is: " + RasterMaskInt)
#
# convert raster mask to polygon
#PolyMask = str(workspaceGDB + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + CellSizeName + "_mask_poly")
PolyMask = str(workspaceGDB + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + CellSizeName + "_mask_poly")
arcpy.AddMessage("output polygon mask: " + PolyMask)
arcpy.AddMessage(PolyMask)

arcpy.RasterToPolygon_conversion(RasterMaskInt, PolyMask, "NO_SIMPLIFY", "Value")
#
###############################################
# Create hillshade
#
azimuth = 315
altitude = 45
modelShadows = "NO_SHADOWS"
zFactor = 1
outHillshade = str(outFolder + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + CellSizeName + "_hillshade.tif")
arcpy.HillShade_3d(outRaster, outHillshade, azimuth, altitude, modelShadows, zFactor)

###############################################
#
## Create data source polygon file and source raster file
#
# copy mb boundary to workspace gdb and assign short name
inMBbasename = os.path.basename(inMBboundary)
MBboundaryCopy = str(workspaceGDB + "\\" + inMBbasename)
arcpy.CopyFeatures_management(inMBboundary, MBboundaryCopy)
inMBbdy = os.path.basename(MBboundaryCopy)
# assign short name to poly mask
inPolyMask = os.path.basename(PolyMask)
# copy topo boundary and assign short name
TopoBoundaryFC = str(workspaceGDB + "\\" + "TopoBND_Seg_" + inSegment + "_" + inYear)
arcpy.CopyFeatures_management(inTopoBoundaryShape, TopoBoundaryFC)
inTopoFC = os.path.basename(TopoBoundaryFC)
arcpy.AddMessage("short name...")
arcpy.AddMessage(inMBbdy)
arcpy.AddMessage(" ")
#
# Union boundary files
#inFeatures = str(inMBbdy + ";" + inPolyMask + ";" + inTopoFC)
inFeatures = [inMBbdy, inPolyMask, inTopoFC]
arcpy.AddMessage("features for union...")
arcpy.AddMessage(inFeatures)
outUnion = str(workspaceGDB + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + "union")
arcpy.Union_analysis(inFeatures, outUnion, "ALL", "", "GAPS")
#
# Run multipart to singlepart to make sure all polygons are individual
outSPunion = str(workspaceGDB + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + "unMP")
arcpy.MultipartToSinglepart_management(outUnion, outSPunion)
#
# Select and delete features outside DEM area
# SelectLayerByAttribute_management (in_layer_or_view, {selection_type}, {where_clause}, {invert_where_clause})
# FID_Seg_100_2014_mask_poly
outUnionLayer = str(workspaceGDB + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + "union_lyr")
arcpy.MakeFeatureLayer_management(outSPunion, outUnionLayer)
expression = str('"' + "FID_Seg_" + inSegment + "_" + inYear + "_" + CellSizeName + "_mask_poly" + '" ' + "= -1")
arcpy.AddMessage("expression is...")
arcpy.AddMessage(expression)
#arcpy.SelectLayerByAttribute_management(outUnionLayer, "NEW_SELECTION", ' "FID_Seg_240_2014_mask_poly" = -1 ')
arcpy.SelectLayerByAttribute_management(outUnionLayer, "NEW_SELECTION", expression)
arcpy.DeleteFeatures_management(outUnionLayer)
#
# Add Data Source Field and assign default value of 3 for sb/interpolated
FieldName = str("Source_" + inYear)
FieldValue = '"3"' #3 is for sb/interpolated
arcpy.AddField_management(outUnionLayer, FieldName, "TEXT")
arcpy.CalculateField_management(outUnionLayer, FieldName, FieldValue, "PYTHON_9.3")
# select areas of multibeam data and assign value
expression = str('"' + "FID_MB_Seg_" + inSegment + "_" + inYear + "_bdy_elim" + '" ' + "> -1")
arcpy.AddMessage("expression is...")
arcpy.AddMessage(expression)
arcpy.SelectLayerByAttribute_management(outUnionLayer, "NEW_SELECTION", expression)
FieldValue = '"1"' #1 is for mb
arcpy.CalculateField_management(outUnionLayer, FieldName, FieldValue, "PYTHON_9.3")
# select areas of topo data and assign value
expression = str('"' + "FID_TopoBND_Seg_" + inSegment + "_" + inYear + '" ' + "> -1")
arcpy.AddMessage("expression is...")
arcpy.AddMessage(expression)
arcpy.SelectLayerByAttribute_management(outUnionLayer, "NEW_SELECTION", expression)
FieldValue = '"2"' #1 is for topo
arcpy.CalculateField_management(outUnionLayer, FieldName, FieldValue, "PYTHON_9.3")
#
# select features smaller than threshold and eliminate
SizeThreshold = str("3")
expression = str('"' + "Shape_Area" + '" ' + "<" + SizeThreshold)
arcpy.AddMessage("expression is...")
arcpy.AddMessage(expression)
arcpy.SelectLayerByAttribute_management(outUnionLayer, "NEW_SELECTION", expression)
outUnionElim = str(workspaceGDB + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + "UnionElim")
arcpy.Eliminate_management(outUnionLayer, outUnionElim, "LENGTH")
# Dissolve
outUnionDissolve = str(workspaceGDB + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + CellSizeName + "_SourcePoly")
DissolveField = str('"Source_' + inYear + '"')
arcpy.Dissolve_management(outUnionElim, outUnionDissolve, DissolveField, "","SINGLE_PART", "DISSOLVE_LINES")
#
# convert to raster
outSourceRaster = str(outFolder + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + CellSizeName + "_Source.tif")
valueField = str('Source_' + inYear)
arcpy.PolygonToRaster_conversion(outUnionDissolve, valueField, outSourceRaster,"CELL_CENTER", "NONE", CellSize)
#
# Add text field to polygon
#
FieldName = str("Source_" + inYear + "_text")
arcpy.AddField_management(outUnionDissolve, FieldName, "TEXT")
#
outUnionDisLayer = str(workspaceGDB + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + CellSizeName + "_SourcePolyLyr")
arcpy.MakeFeatureLayer_management(outUnionDissolve, outUnionDisLayer)
#
FieldValue = '"MB"'
arcpy.AddMessage("field value is...")
arcpy.AddMessage(FieldValue)
#DataSourceString = str("1")
expression = str("Source_" + inYear + " = '1'")
#expression = str("!Source_" + inYear + "! = '1'")
arcpy.AddMessage("expression is...")
arcpy.AddMessage(expression)
arcpy.SelectLayerByAttribute_management(outUnionDisLayer, "NEW_SELECTION", expression)
arcpy.CalculateField_management(outUnionDisLayer, FieldName, FieldValue, "PYTHON_9.3")
#
FieldValue = '"TOPO"'
expression = str('"' + "Source_" + inYear + '" ' + "= '2'")
arcpy.SelectLayerByAttribute_management(outUnionDisLayer, "NEW_SELECTION", expression)
arcpy.CalculateField_management(outUnionDisLayer, FieldName, FieldValue, "PYTHON_9.3")
#
FieldValue = '"SB"'
expression = str('"' + "Source_" + inYear + '" ' + "= '3'")
arcpy.SelectLayerByAttribute_management(outUnionDisLayer, "NEW_SELECTION", expression)
arcpy.CalculateField_management(outUnionDisLayer, FieldName, FieldValue, "PYTHON_9.3")
#

###############################################
#
# Calculate Point Density
# copy
AllPtsMerge = str(workspaceGDB + "\\" + "AllPts_Seg_" + inSegment + "_" + inYear + "_" + CellSizeName + "_interp")
arcpy.CopyFeatures_management(inAllPts, AllPtsMerge)
#
outDensityRasterTemp = str(outFolder + "\\" + "Seg_" + inSegment + "_" + inYear + "_PtDensityTemp.tif")
outDensityRaster = str(outFolder + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + CellSizeName + "_PtDensity.tif")
#arcpy.gp.PointDensity_sa(AllPtsMerge, "NONE", outDensityRasterTemp, "1", "Circle 5 MAP", "SQUARE_MAP_UNITS")
#SearchExpression = str('"Circle ' + DensitySearchRadius + ' MAP"')
SearchExpression = str("Circle " + DensitySearchRadius + " MAP")
arcpy.AddMessage("expression is...")
arcpy.AddMessage(SearchExpression)
arcpy.gp.PointDensity_sa(AllPtsMerge, "NONE", outDensityRasterTemp, CellSize, SearchExpression, "SQUARE_MAP_UNITS")
arcpy.gp.Times_sa(outDensityRasterTemp, RasterMaskInt,outDensityRaster)
#
###############################################
#
## Calculate Interpolation Uncertainty
#
# Assign values from DEM to points
inputRasterStatement = str(outRaster + " DEM_Z")
arcpy.AddMessage("expression is...")
arcpy.AddMessage(inputRasterStatement)
ExtractMultiValuesToPoints(AllPtsMerge, inputRasterStatement, "NONE")
#
# Add field and calculate Point_Z minus DEM_Z
FieldName = str("PTZ_minus_DEMZ")
arcpy.AddField_management(AllPtsMerge, FieldName, "DOUBLE")
FieldValue = str("!POINT_Z! - !DEM_Z!")
arcpy.AddMessage("expression is...")
arcpy.AddMessage(FieldValue)
arcpy.CalculateField_management(AllPtsMerge, FieldName, FieldValue, "PYTHON_9.3")
#
# Calculate absolute value
FieldName = str("ABS_difference")
arcpy.AddField_management(AllPtsMerge, FieldName, "DOUBLE")
FieldValue = str("abs(!PTZ_minus_DEMZ!)")
arcpy.AddMessage("expression is...")
arcpy.AddMessage(FieldValue)
arcpy.CalculateField_management(AllPtsMerge, FieldName, FieldValue, "PYTHON_9.3")
#
# Interpolate to raster using IDW
# weighting power of 2 and using 12 points within max radius of 20 m is hardwired in
outPtInterpTemp = str(outFolder + "\\" + "Seg_" + inSegment + "_" + inYear + "_InterpTemp.tif")
outPtInterp = str(outFolder + "\\" + "Seg_" + inSegment + "_" + inYear + "_" + CellSizeName + "_InterpError.tif")
power = str("2")
SearchRadius = str("RadiusVariable(12, 20)")
#FieldName = str('"PTZ_minus_DEMZ"')
FieldName = str("ABS_difference")
arcpy.AddMessage("expression is...")
arcpy.AddMessage(FieldName)
outPtInterpTemp = Idw(AllPtsMerge, FieldName, CellSize, power, SearchRadius)
# multiply by mask
arcpy.gp.Times_sa(outPtInterpTemp, RasterMaskInt,outPtInterp)
#
###############################################
#
# delete temporary files
#
arcpy.Delete_management(outPtInterpTemp)
arcpy.Delete_management(outDensityRasterTemp)
arcpy.Delete_management(RasterMask)
arcpy.Delete_management(outUnion)
arcpy.Delete_management(outSPunion)
arcpy.Delete_management(outUnionElim)
arcpy.Delete_management(RasterMask)












