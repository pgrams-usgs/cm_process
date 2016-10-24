
#Channel Mapping work flow
September 12, 2016
##Use of scripts to go from points to DEM
1. Import the bathymetry points and topo points and create TIN using CM_XYZ_to_TIN.py in ArcGIS. This script creates a TIN for editing and creates a point file with all (mb, sb, and topo) points. Also creates the boundary file delineating the area of multibeam data collection. To avoid the problem with “holes” in the middle of the multibeam boundary file, they are removed with an “eliminate” command. The threshold for size of holes to eliminate is set to default at 500 square meters.
    * Setup
        1. Create empty folder for outputs within the segment_### directory. Suggest naming “Process_YYYYMMDD” (for date of processing)
        2. Create empty geodatabase within that folder. Naming convention: “seg_###_YYYY_xyz_YYYYMMDD” (first YYYY is for date of survey, second is for date of processing)
    * Script inputs:
        1. Bathymetry xyz (multibeam and singlebeam)
        2. topo points, 
        3. breaklines and water edge
    * Outputs
        1. seg_###_ YEAR_tin and seg_###_ YEAR_tin_edt: Tin (two identical copes, one for editing, one for backup)
        2. AllPts_Seg_###_YEAR_merge (all mb, sb, and topo points in one clean file with attribute for data source). Point feature class.
        3. MB_Seg_###_ YEAR_bdy_elim: multibeam data collection boundary with holes smaller than threshold removed. Polygon feature class.
        4. MB_Seg_###_ YEAR_boundary: multibeam data collection boundary (original). Polygon feature class.
        5. MB_Seg_###_ YEAR _merge: Merged multibeam points. Point feature class.
        6. SB_Seg_###_ YEAR_merge: Merged singlebeam points. Point feature class.
        7. SB_Seg_###_ YEAR_merge_erase: Merged singlebeam points with points in areas of multibeam data collection removed. Point feature class.
        8. And, copies of the inputs as point or line feature classes.
2. Edit TIN by manual inspection.
3. Run CM_TIN_to_DEM.py. This takes the edited TIN and produces DEM and associated data sets at specified resolution. Raster files are output in specified directory. Create a new empty geodatabase for output of non-raster files. If re-running, delete old rasters and files from gdb (or start with new gdb). If running same inputs at different output resolutions, the rasters can go to same output location, but specify new empty gdb for non-raster outputs.
    * Setup: 
        1. use same folder as step one for DEM outouts.
        2. Create empty geodatabase for non-raster outputs. Naming convention: “seg_###_YYYY_dem_YYYYMMDD” (first YYYY is for date of survey, second is for date of processing)
    * Inputs
        1. Edited TIN
        2. Multibeam boundary (should use the one with holes eliminated)
        3. Topo boundary (should be in the final topo folder)
        4. All points merged
* Outputs
        1. Seg_###_ YEAR_#m.tif: DEM at specified resolution. Extent of this and all other rasters should be set to extent of TIN area and forced to even 1 meter.
        2. Seg_###_ YEAR_#m_maskInt.tif: Integer raster mask of DEM area.
        3. Seg_###_ YEAR_#m_hillshade.tif: Hillshade at same resolution. Hillshade parameters are hardwired in and would need to be changed in script.
        4. 	AllPts_Seg_###_YEAR_1m_interp: All input points, with attributes added for DEM elevation and difference between Point elevation and DEM elevation for each point.  Point feature class.
        5. Seg_###_ YEAR_#m_mask_poly: Mask for area of final DEM. Polygon feature class.
        6. Seg_###_ YEAR_#m_SourcePoly: Data type (source) for DEM. Polygon feature class. 1 = multibeam data; 2 = topo data; 3 = singlebeam data and/or interpolated.
        7. Seg_###_ YEAR_#m_Source.tif: Source in raster format.
        8. Seg_###_ YEAR_#m_PtDensity.tif. Raster of  Point density for each grid cell. Uses a search radius specified in inputs.
        9. Seg_###_ YEAR_#m_InterpError.tif Interpolation uncertainty raster. Compares values of each point to corresponding grid cell and calculates difference. Generates surface using IDW gridding.
## Sand budgeting geomorphic change analysis
There are two versions of the script: CM_DOD.py will either run on an individual segment, or loop through and run on all segments, producing separate outputs for each segment. CM_DOD_all.py runs on the entire channel mapping reach (e.g. all of LMC).

Inputs to script:
1.	Segment to run
2.	Data location (it’s set to run for a couple locations with DEM inputs
3.	Output geodatabase
4.	Polygons features (geomorphic base map)
5.	Zone field 1
6.	Zone field 2

The two zone fields (both from the input polygon features) provide for two levels of aggregating outputs.  Usually pick “GeomorphUnit” as first and “U_ID” as second. The first groups results by geomorphic unit, the second runs the calculations for every feature individually. To run bed class calculations, run on GeoBed, which is union of geomorphic base map and bed classification change.

Hardwired inputs:
1. DEM 1 and DEM 2 (2009 and 2012 for LMC).  If looping through segments, it finds them in \\Channel_Mapping\\Analysis\\GIS\\DEM_gdb\\CM_2009_DEM.gdb\\ with predictable name. If Doing entire reach, it finds them in \\Channel_Mapping\\Analysis\\GIS\\DEM_tif\\ 
2. Uncertainty rasters: \\Channel_Mapping\\Analysis\\GIS\\DEM_inputs_gdb\\LMC_Uncertainty.gdb\\
## Uncertainty analysis using GCD:
1. Pt density from merged inputs. Used GCD tool with 5m window & developed FIS input and rules (merge of mb, sb, and topo)
2. Interpolation uncertainty (calculated by assigning grid elevation from final 1-m DEM to each data point in each input file). Any better way? Note: Due to problem of different fields for topo & sonar could not input merged points for built in GCD tool. Another issue with generating this surface is that a straight point to raster leaves holes in interp uncert. Surface, which leads to gaps in FIS uncertainty estimates. So, I did the following:
    * Used spatial analyst>extract multi values to points to add DEM elevation value to point table for each point coverage (again, had to do mb, sb, and topo separately).
    * Added field of pt to DEM difference and used field calculator to generate absolute value of difference
    * TIN of pt-DEM difference field
    * Raster to TIN for complete interp uncert raster.
3. Roughness. Ran topcat tool on 0.25m bathymetry using 1m spacing, minimum of 4 pts. This leaves holes where no data. So I did the following:  Potential enhancement: use PYSESA instead of Topcat. Create output with code for nodata rather than “no data” so that it doesn’t crash FIS. Need to modify FIS to use new no data code.
    * Generated points from topcat output surface
    * Tin model of roughness point values
    * TIN to raster for full coverage raster
4. Run FIS in GCD.  Potential improvement:  talk to north arrow about batch file GCD command line. Example: C:> gcd fiserror C:\myslope.tif c:\mypointdensity.tif c:\myinterperr.tif c:\myrough.tif c:\myoutput_uncertainty.tif c:\myfis_rules.fis
Confirm with Matt whether slope rater is needed.

## Needs:
1. Better route to “source” polygons. 
2.	Tool to merge input points into coverage with exact same fields would be handy
3.	Better way to generate associated surfaces without gaps or holes in data gaps. 
4.	Final reporting requires merging of segments to full 30ish miles to generating stats within each method area. Not a big deal, but part of the flow, so perhaps a merge tool that would input all segment DEMs, associated surfaces, FIS output into one giant project would be handy to have built in. Also, 2009 merged surfaces contain ~3million + points, which can get a bit cumbersome to process/make histograms, etc., so a stats tool that would spit out stats for each method area, including histograms (with user defined bins) would be handy. Not looking for graphs necessarily, just the data to plot in external software to make pretty and comply with USGS standards.
5.	Scripting/batch processing once all associated surfaces and FIS input/output and rules are generated.  
6.	Tracking of inputs/outputs. 
7.	Integration with Part II calculations.
