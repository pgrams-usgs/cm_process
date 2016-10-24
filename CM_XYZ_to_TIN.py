# CM_XYZ_to_TIN
# Script to import channel mapping data and create TIN
# September 9, 2016
# Paul Grams
#
# modified from XYZ_v10.py which started as XYZ_FIST_FGDB_Folder_v10.py by Tim Andrews
#
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

# Local variables...

# GUI variables
# set as parameters in toolbox in this order #Display Name: Data Type
inYear = arcpy.GetParameterAsText(0) #Year data collected: string
inSegment = arcpy.GetParameterAsText(1) #Segment Name: string
inMbFolder = arcpy.GetParameterAsText(2) #Input MB Folder Folder
inSbFolder = arcpy.GetParameterAsText(3) #Input SB Folder: Folder
inTopoPts_shape = arcpy.GetParameterAsText(4) #Input topo points: Shapefile
inTopoBRK_shape = arcpy.GetParameterAsText(5) #Input topo breaklines: Shapefile
inTopoWE_shape = arcpy.GetParameterAsText(6) #Input topo WE: Shapefile
workspaceGDB = arcpy.GetParameterAsText(7) #Output Geodatabase: Workspace or Feature Dataset (must be geodatabase!)
aggregation_distance = arcpy.GetParameterAsText(8) #Aggragation Distance: string (default is 3)
outTinFolder = arcpy.GetParameterAsText(9) #Output folder for TIN: Workspace or Feature Dataset (must be folder!)
TinDelineationLength = arcpy.GetParameterAsText(10) #TIN Delineation Length: string (default is 6)
EliminationArea = arcpy.GetParameterAsText(11) #Multbeam data hole elimination threshold (default is 500)

## Note on Outputs
# The output TINs go in the output tin folder
# All other outputs go in the output geodatabase
# These include all the individual mb, sb, and topo point files and merged point files.
# AllPts_Seg_xxx_YYYY_merge has all mb, sb, and topo points in one file with the following fields:
# POINT_X, POINT_Y, POINT_Z, SOURCE_2014
# SOURCE_2014 has MB for multibeam data, SB for singlebeam data, and TOPO for topo data
#
# MB_Seg_xxx_YYYY_boundary is boundary of multibeam data coverage
#    created using aggradation with specified aggragation distance
# MB_Seg_xxx_YYYY_bdy_elim has holes removed using eliminate with
#     elimination size hardwired in at 500 m in line 217

# were inputs, changed to fixed
fileSuffix = "xyz"
#
inMbWS = inMbFolder
inSbWS = inSbFolder
# copy input shapefiles to feature classes in geodatabase

## convert shapefile to feature class
outTopoPtsFC = str(workspaceGDB + "\\" + "TopoPts_Seg_" + inSegment + "_" + inYear)
arcpy.CopyFeatures_management(inTopoPts_shape, outTopoPtsFC)
inTopoPts = os.path.basename(outTopoPtsFC)
#
outTopoBrkFC = str(workspaceGDB + "\\" + "TopoBrk_Seg_" + inSegment + "_" + inYear)
arcpy.CopyFeatures_management(inTopoBRK_shape, outTopoBrkFC)
inTopoBRK = os.path.basename(outTopoBrkFC)
#
outTopoWeFC = str(workspaceGDB + "\\" + "TopoWe_Seg_" + inSegment + "_" + inYear)
arcpy.CopyFeatures_management(inTopoWE_shape, outTopoWeFC)
inTopoWE = os.path.basename(outTopoWeFC)
#
arcpy.AddMessage(" ")
arcpy.AddMessage("Input Multibeam Folder Path is: " + inMbWS)
arcpy.AddMessage("Input Singlebeam Folder Path is: " + inSbWS)
arcpy.AddMessage("Input Topography points: " + inTopoPts)
arcpy.AddMessage("Input Topography breaklines: " + inTopoBRK)
arcpy.AddMessage("Input Topography water edge: " + inTopoWE)
arcpy.AddMessage(" ")

#
arcpy.AddMessage("Workspace Geodatabase is: " + workspaceGDB)
arcpy.AddMessage(" ")
arcpy.AddMessage("Input File Suffix is: " + fileSuffix)
arcpy.AddMessage(" ")


# spatial reference hardwired in
# Use the State Plane AZ Central projection file as input to the SpatialReference class
prjFile = r"C:\arcgis\Desktop10.0\Coordinate Systems\Projected Coordinate Systems\State Plane\NAD 1983 (Meters)\NAD 1983 StatePlane Arizona Central FIPS 0202 (Meters).prj"
spatialRef = arcpy.SpatialReference(prjFile)

# Set the output Coordinate System
arcpy.env.outputCoordinateSystem = spatialRef
arcpy.AddMessage("Output Spatial Reference was set to " + str(prjFile))
arcpy.AddMessage(" ")

# Set environment settings
env.workspace = str(workspaceGDB)
env.overwriteOutput = True

#############################################################
#############################################################
#
# process multibeam inputs 
# Get all the XYZ files in the input folder as a Glob
DataType = "MB"
FieldValue = '"MB"'
inputs = str(inMbWS+"\*" + str(fileSuffix))
arcpy.AddMessage("Inputs with wildcard are: " + inputs)
arcpy.AddMessage(" ")

theFiles = glob.glob(inputs)
FClist = []

# Loop through the input XYZ files
for i in theFiles:
  #inXYZfull = str(i).replace("\\","/")
  inXYZfull = str(i)
  inXYZ = os.path.split(inXYZfull)[1]
  inPath = os.path.split(inXYZfull)[0]
  #output = os.path.join(out_workspace, fc)
      
  arcpy.AddMessage("Input XYZ File is: " + inXYZfull)
  
  noextName = str(inXYZ[:-4])
  # arcpy.AddMessage("Input XYZ File without extension is: " + noextName)
  # arcpy.AddMessage("")

  shortFCName = str("pt_" + noextName)
  # arcpy.AddMessage("Short Output FC Name: " + shortFCName)
  # arcpy.AddMessage("Short Output GRID Name: " + outRasterName)

  outFCNameFull = str(workspaceGDB + "\\" + shortFCName)
  # arcpy.AddMessage("Full Output FC Name: " + outFCNameFull)
  # arcpy.AddMessage(" ")
  
  try:
    # Input file format
    inFormat = "XYZ"
    
    # Geometry of the output feature class
    outType = "POINT"

    # Multiplier applied to the input z values
    zFactor = 1

    # The character used to represent a decimal for floating point numbers
    decSep = "DECIMAL_POINT" # Specifies the decimal delimiter
    
    # Process: creating a feature class using an ASCII input file
    # ASCII3DToFeatureClass_3d (input, in_file_type, out_feature_class, out_geometry_type, {z_factor},
    #          {input_coordinate_system}, average_point_spacing, {file_suffix}, {decimal_separator})

    arcpy.ASCII3DToFeatureClass_3d(inXYZfull, inFormat, outFCNameFull, outType, zFactor, spatialRef, "#", fileSuffix, decSep)
    arcpy.AddMessage("Created XYZ Point Feature Class: " + outFCNameFull)  
    
    # Add X,Y, Z Fields
    arcpy.AddXY_management(outFCNameFull)
    arcpy.AddMessage("Added X,Y,Z fields to " + outFCNameFull)
    arcpy.AddMessage(" ")

    # Add field for data type
    #AddField_management (in_table, field_name, field_type, {field_precision}, {field_scale}, {field_length},
    #   {field_alias}, {field_is_nullable}, {field_is_required}, {field_domain})
    FieldName = str("Source_" + inYear)
    #FieldValue = '"MB"'
    arcpy.AddField_management(outFCNameFull, FieldName, "TEXT")
    arcpy.CalculateField_management(outFCNameFull, FieldName, FieldValue, "PYTHON_9.3")
    #
    #FClist.append(outFCNameFull)
    FClist = FClist + [outFCNameFull]
    arcpy.AddMessage("list of feature class files... ")
    arcpy.AddMessage(FClist)
    arcpy.AddMessage(" ")
    
  except:
    # If an error occurred while running the tool, print the error messages.
    print arcpy.GetMessages()

try:
  # merge
  #
  outPointMerge = str(workspaceGDB + "\\" + DataType +"_Seg_" + inSegment + "_" + inYear + "_merge")
  arcpy.Merge_management(FClist, outPointMerge)
  arcpy.AddMessage("created merged point file...")
  arcpy.AddMessage(outPointMerge)
  #MBpointMerge = outPointMerge
  MBpointMerge = os.path.basename(outPointMerge)
  arcpy.AddMessage("short name...")
  arcpy.AddMessage(MBpointMerge)
  
except:
  # If an error occurred while running a tool, then print the messages.
  arcpy.AddMessage("did not create merged point file: " + outPointMerge)
  print arcpy.GetMessages()
  
try:
    outMBboundary = str(workspaceGDB + "\\" + DataType + "_Seg_" + inSegment + "_" + inYear + "_boundary")
    fc = outPointMerge
    # Process: Aggregate Points
    arcpy.AggregatePoints_cartography(fc, outMBboundary, aggregation_distance)
    arcpy.AddMessage("Created Polygons from XYZ points...")
    arcpy.AddMessage(outMBboundary)
    
except:
  # If an error occurred while running a tool, then print the messages.
  arcpy.AddMessage("Did Not Create Polygons from XYZ points...")
  arcpy.AddMessage(outMBboundary)
  print arcpy.GetMessages()

try:
  outMBboundaryElim = str(workspaceGDB + "\\" + DataType + "_Seg_" + inSegment + "_" + inYear + "_bdy_elim")
  EliminationAreaExpression = str(EliminationArea + " SquareMeters")
  arcpy.EliminatePolygonPart_management(outMBboundary, outMBboundaryElim, "AREA", "500 SquareMeters", part_area_percent="0", part_option="ANY")
  arcpy.AddMessage("Eliminated holes in polygon...")
  arcpy.AddMessage(outMBboundaryElim)
  arcpy.AddMessage(" ")
except:
  # If an error occurred while running a tool, then print the messages.
  arcpy.AddMessage("Did Not eliminate holes in polygon...")
  arcpy.AddMessage(" ")
  print arcpy.GetMessages()

#
#############################################################
#############################################################
#
# process singlebeam inputs 
# Get all the XYZ files in the input folder as a Glob
DataType = "SB"
FieldValue = '"SB"'
inputs = str(inSbWS+"\*" + str(fileSuffix))
arcpy.AddMessage("Inputs with wildcard are: " + inputs)
arcpy.AddMessage(" ")

theFiles = glob.glob(inputs)
FClist = []

# Loop through the input XYZ files
for i in theFiles:
  #inXYZfull = str(i).replace("\\","/")
  inXYZfull = str(i)
  inXYZ = os.path.split(inXYZfull)[1]
  inPath = os.path.split(inXYZfull)[0]
  #output = os.path.join(out_workspace, fc)
      
  arcpy.AddMessage("Input XYZ File is: " + inXYZfull)
  
  noextName = str(inXYZ[:-4])
  # arcpy.AddMessage("Input XYZ File without extension is: " + noextName)
  # arcpy.AddMessage("")

  shortFCName = str("pt_" + noextName)
  # arcpy.AddMessage("Short Output FC Name: " + shortFCName)
  # arcpy.AddMessage("Short Output GRID Name: " + outRasterName)

  outFCNameFull = str(workspaceGDB + "\\" + shortFCName)
  # arcpy.AddMessage("Full Output FC Name: " + outFCNameFull)
  # arcpy.AddMessage(" ")
  
  try:
    # Input file format
    inFormat = "XYZ"
    
    # Geometry of the output feature class
    outType = "POINT"

    # Multiplier applied to the input z values
    zFactor = 1

    # The character used to represent a decimal for floating point numbers
    decSep = "DECIMAL_POINT" # Specifies the decimal delimiter
    
    # Process: creating a feature class using an ASCII input file
    # ASCII3DToFeatureClass_3d (input, in_file_type, out_feature_class, out_geometry_type, {z_factor},
    #          {input_coordinate_system}, average_point_spacing, {file_suffix}, {decimal_separator})

    arcpy.ASCII3DToFeatureClass_3d(inXYZfull, inFormat, outFCNameFull, outType, zFactor, spatialRef, "#", fileSuffix, decSep)
    arcpy.AddMessage("Created XYZ Point Feature Class: " + outFCNameFull)  
    
    # Add X,Y, Z Fields
    arcpy.AddXY_management(outFCNameFull)
    arcpy.AddMessage("Added X,Y,Z fields to " + outFCNameFull)
    arcpy.AddMessage(" ")

    # Add field for data type
    #AddField_management (in_table, field_name, field_type, {field_precision}, {field_scale}, {field_length},
    #   {field_alias}, {field_is_nullable}, {field_is_required}, {field_domain})
    FieldName = str("Source_" + inYear)
    arcpy.AddField_management(outFCNameFull, FieldName, "TEXT")
    arcpy.CalculateField_management(outFCNameFull, FieldName, FieldValue, "PYTHON_9.3")
    #
    #FClist.append(outFCNameFull)
    FClist = FClist + [outFCNameFull]
    arcpy.AddMessage("list of feature class files... ")
    arcpy.AddMessage(FClist)
    arcpy.AddMessage(" ")
    
  except:
    # If an error occurred while running the tool, print the error messages.
    print arcpy.GetMessages()
# Merge SB points
outPointMerge = str(workspaceGDB + "\\" + DataType + "_Seg_" + inSegment + "_" + inYear + "_merge")
outPointMergeErase = str(workspaceGDB + "\\" + DataType + "_Seg_" + inSegment + "_" + inYear + "_merge_erase")
try:
  arcpy.Merge_management(FClist, outPointMerge)
  arcpy.AddMessage("created merged point file...")
  arcpy.AddMessage(outPointMerge)
  arcpy.Erase_analysis(outPointMerge, outMBboundary, outPointMergeErase)
  #SBpointMerge = outPointMergeErase
  SBpointMerge = os.path.basename(outPointMergeErase)
  arcpy.AddMessage("short name...")
  arcpy.AddMessage(SBpointMerge)
  arcpy.AddMessage(" ")
except:
  # If an error occurred while running a tool, then print the messages.
  arcpy.AddMessage("did not create merged point file: " + outPointMerge)
  print arcpy.GetMessages()
#
#############################################################
#############################################################
#
## Process topo data
# add fields
#
FieldName = str("POINT_X")
arcpy.AddField_management(inTopoPts, FieldName, "DOUBLE")
FieldValue = str("!EASTING!")
arcpy.CalculateField_management(inTopoPts, FieldName, FieldValue, "PYTHON_9.3")
#
FieldName = str("POINT_Y")
arcpy.AddField_management(inTopoPts, FieldName, "DOUBLE")
FieldValue = str("!NORTHING!")
arcpy.CalculateField_management(inTopoPts, FieldName, FieldValue, "PYTHON_9.3")
#
FieldName = str("POINT_Z")
arcpy.AddField_management(inTopoPts, FieldName, "DOUBLE")
FieldValue = str("!ELEVATION!")
arcpy.CalculateField_management(inTopoPts, FieldName, FieldValue, "PYTHON_9.3")
#
FieldName = str("Source_" + inYear)
arcpy.AddField_management(inTopoPts, FieldName, "TEXT")
FieldValue = '"TOPO"'
arcpy.CalculateField_management(inTopoPts, FieldName, FieldValue, "PYTHON_9.3")
# delete fields
dropFields = ["PT_ID", "GIS_KEY", "NORTHING", "EASTING", "ELEVATION", "DESCRIPTIO"]
arcpy.DeleteField_management(inTopoPts, dropFields)
#
## Merge mb points, sb points, and topo points
AllPtsMerge = str(workspaceGDB + "\\" + "AllPts_Seg_" + inSegment + "_" + inYear + "_merge")
MergeList = [MBpointMerge, SBpointMerge, inTopoPts]
arcpy.Merge_management(MergeList, AllPtsMerge)

#
#############################################################
#############################################################
#
## Create TIN
#
out_tin = str(outTinFolder + "\\" + "Seg_" + inSegment + "_" + inYear + "_tin")
in_features = str(MBpointMerge + " POINT_Z masspoints; " + SBpointMerge + " POINT_Z masspoints; " + inTopoPts + " POINT_Z masspoints;" + inTopoBRK + " <None> softline;" + inTopoWE + " <None> softline")
arcpy.AddMessage("input features for tin...")
arcpy.AddMessage(in_features)

try:
  arcpy.CreateTin_3d(out_tin, spatialRef, in_features, False)
except arcpy.ExecuteError:
  print arcpy.GetMessages()
#               
arcpy.DelineateTinDataArea_3d(out_tin, TinDelineationLength, "PERIMETER_ONLY")
# copy TIN for editing
copy_tin = str(outTinFolder + "\\" + "Seg_" + inSegment + "_" + inYear + "_tin_EDT")
arcpy.CopyTin_3d(out_tin, copy_tin)
