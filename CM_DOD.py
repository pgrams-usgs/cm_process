# ---------------------------------------------------------------------------
# CM_DOD.py
# Created: December 4, 2013
# Modified August 21, 2014 (renamed this version to CM_DOD_LMC)
# Modified January 9, 2017 to generalize for use in any segment
# Paul Grams
# ---------------------------------------------------------------------------
# Parameters
# arcpy.GetParameterAsText(0) Segment, String, Required, Input, Value List
# ---------------------------------------------------------------------------
# Import system modules
import sys, string, os, arcgisscripting
import arcpy
from arcpy import env
from arcpy.sa import *

# Check out any necessary licenses
arcpy.CheckOutExtension("Spatial")

# Turn on history logging so that a history log file is written
arcpy.LogHistory = True

# Allow for the overwriting of file geodatabases, if they previously exist
arcpy.env.overwriteOutput = True

# Use the projection file as input to the SpatialReference class
prjFile = r"C:\ArcGIS\Desktop10.2\Coordinate Systems\USGS_Favorites\NAD 1983 StatePlane Arizona Central FIPS 0202 (Meters).prj"
spatialRef = arcpy.SpatialReference(prjFile)

# Set the environment output Coordinate System
arcpy.env.outputCoordinateSystem = spatialRef

# input variables
inSegment = arcpy.GetParameterAsText(0) #Segment Name: String
inYear1 = arcpy.GetParameterAsText(1) #year or date for first DEM: String
inYear2 = arcpy.GetParameterAsText(2) #year or date for second DEM: String
Year1DEM = arcpy.GetParameterAsText(3) # raster dataset
Year2DEM = arcpy.GetParameterAsText(4) # raster dataset
Year1Source = arcpy.GetParameterAsText(5) # raster dataset
Year2Source = arcpy.GetParameterAsText(6) # raster dataset
geomorph = arcpy.GetParameterAsText(7) #feature class or shapefile
zoneField = arcpy.GetParameterAsText(8) #"GeomorphUnit"
zoneField2 = arcpy.GetParameterAsText(9) #"U_ID"
outFolder = arcpy.GetParameterAsText(10) #Output folder: Workspace or Feature Dataset (USE FOLDER)
workspaceGDB = arcpy.GetParameterAsText(11) #Geodatabase: (empty output geodatabase)
#fiducial = 
#
arcpy.AddMessage(outFolder)
print arcpy.GetMessages()
arcpy.AddMessage(inSegment)
print arcpy.GetMessages()
arcpy.AddMessage(inYear1)
print arcpy.GetMessages()
arcpy.AddMessage(inYear2)
print arcpy.GetMessages()
# ---------------------------------------------------------------------------
# compute uncertainty raster from input source rasters
#
# compare input source rasters
SourceCompare = str(outFolder + "\\" + inSegment + "_" + inYear1 + "_" +  inYear2 + "_SourceCompare.tif")
arcpy.gp.GreaterThanEqual_sa(Year2Source, Year1Source, SourceCompare)
# where input 1 was greater or equal, use input 1, otherwise, use input 2
SourceCombined = str(outFolder + "\\" + inSegment + "_" + inYear1 + "_" +  inYear2 + "_SourceCombined" + ".tif")
arcpy.gp.Con_sa(SourceCompare, Year2Source, SourceCombined, Year1Source, "")
# Reclassify to integer uncertainty (values in cm)
UncertaintyINTcm = str(outFolder + "\\" + inSegment + "_" + inYear1 + "_" +  inYear2 + "_UncertaintyINTcm" + ".tif")
arcpy.gp.Reclassify_sa(SourceCombined, "Value", "1 6;2 6;3 12", UncertaintyINTcm, "DATA")
# convert to float (values in cm)
UncertaintyFloat = str(outFolder + "\\" + inSegment + "_" + inYear1 + "_" +  inYear2 + "_UncertaintyFLOATcm" + ".tif")
arcpy.gp.Float_sa(UncertaintyINTcm, UncertaintyFloat)
# convert to meters
UncertaintyMETERS = str(outFolder + "\\" + inSegment + "_" + inYear1 + "_" +  inYear2 + "_Uncertainty" + ".tif")
arcpy.gp.Divide_sa(UncertaintyFloat, "100", UncertaintyMETERS)


##source = DataLocation + "\\Channel_Mapping\\Analysis\\GIS\\DEM_inputs_gdb\\CM_Source.gdb\\Seg_" + inSeg + "_source_union"
##zoneField3 = "SourceUnion"
##fiducial = DataLocation + "\\Channel_Mapping\\Analysis\\GIS\\Boundaries_gdb\\LMC_Fiducial_Areas.gdb\\Seg_" + inSeg + "_fid_Merge"
##zoneFieldFid = "Poly_ID"


outDOD = outFolder + "\\" + inSegment + "_DOD_" + inYear1 + "_" + inYear2 + ".tif"
outDeposition = outFolder + "\\" + inSegment + "_Deposition_" + inYear1 + "_" + inYear2 + ".tif"
outErosion = outFolder + "\\" + inSegment + "_Erosion_" + inYear1 + "_" + inYear2 + ".tif"

### Process: SUBTRACT DEM PAIRS
arcpy.AddMessage("subtracting DEMs")
print arcpy.GetMessages()
#outDOD = Minus(Year2DEM, Year1DEM)
arcpy.gp.Minus_sa(Year2DEM, Year1DEM, outDOD)
##DODmask = Int(outDOD/outDOD)
##DODmaskPoly = outGDB + Segment + "DODmaskPoly"
##arcpy.RasterToPolygon_conversion(DODmask, DODmaskPoly, "NO_SIMPLIFY", "Value")
##arcpy.AddField_management(DODmaskPoly, "Segment", "TEXT", "", "", 8)
###arcpy.CalculateField_management(DODmaskPoly, "Segment", 'A') CAN'T MAKE THIS WORK

##
##
### Process: separate out erosion and deposition
arcpy.AddMessage("separating erosion and deposition")
print arcpy.GetMessages()
wherePositive = "VALUE > 0"
whereNegative = "VALUE < 0"
outErosion = SetNull(outDOD, outDOD, wherePositive)
outDeposition = SetNull(outDOD, outDOD, whereNegative)

### Generate output tables
arcpy.AddMessage("generating output tables")
print arcpy.GetMessages()

##arcpy.AddMessage("...on fiducial areas")
##print arcpy.GetMessages()
##ZonalHistogram(fiducial, zoneFieldFid, DOD, outFile + "DOD_ZhistFiducial.dbf")
##ZonalStatisticsAsTable(fiducial, zoneFieldFid, DOD, outFile + "DOD_ZstatFiducial.dbf", "DATA")

arcpy.AddMessage("...on aggregated geomorphic units")
print arcpy.GetMessages()

outFileBase = outFolder + "\\" + inSegment
ZonalStatisticsAsTable(geomorph, zoneField, outDOD, outFileBase + "_DOD_Zstat.dbf", "DATA")
ZonalStatisticsAsTable(geomorph, zoneField, outErosion, outFileBase + "_Erosion_Zstat.dbf", "DATA")
ZonalStatisticsAsTable(geomorph, zoneField, outDeposition, outFileBase + "_Deposition_Zstat.dbf", "DATA")

##ZonalHistogram(geomorph, zoneField, DOD, outFile + "DOD_Zhist.dbf")
##ZonalHistogram(geomorph, zoneField, Erosion, outFile + "Erosion_Zhist.dbf")
##ZonalHistogram(geomorph, zoneField, Deposition, outFile + "Deposition_Zhist.dbf")

arcpy.AddMessage("...on every geomorphic unit")
print arcpy.GetMessages()

ZonalStatisticsAsTable(geomorph, zoneField2, outDOD, outFileBase + "_DOD_ZstatAllUnits.dbf", "DATA")
ZonalStatisticsAsTable(geomorph, zoneField2, outErosion, outFileBase + "_Erosion_ZstatAllUnits.dbf", "DATA")
ZonalStatisticsAsTable(geomorph, zoneField2, outDeposition, outFileBase + "_Deposition_ZstatAllUnits.dbf", "DATA")
ZonalStatisticsAsTable(geomorph, zoneField2, UncertaintyMETERS, outFileBase + "_Uncertainty_ZstatAllUnits.dbf", "DATA")

##arcpy.AddMessage("...on data source")
##print arcpy.GetMessages()
##ZonalStatisticsAsTable(source, zoneField3, DOD, outFile + "DOD_ZstatSource.dbf", "DATA")
##ZonalStatisticsAsTable(source, zoneField3, Erosion, outFile + "Erosion_ZstatSource.dbf", "DATA")
##ZonalStatisticsAsTable(source, zoneField3, Deposition, outFile + "Deposition_ZstatSource.dbf", "DATA")

### Save the outputs
arcpy.AddMessage("saving outputs")
print arcpy.GetMessages()
#DOD.save(outDOD)
#Deposition.save(outDeposition)
#Erosion.save(outErosion)

arcpy.AddMessage("Output datasets saved in...")
print arcpy.GetMessages()
arcpy.AddMessage(outFolder)
print arcpy.GetMessages()
arcpy.AddMessage("Output calculations saved in...")
print arcpy.GetMessages()
arcpy.AddMessage(outFolder)
print arcpy.GetMessages()
##



