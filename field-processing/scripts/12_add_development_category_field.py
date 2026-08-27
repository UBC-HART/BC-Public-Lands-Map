"""
Step 12: Add Development Category field

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# 1. Setup
layer_name = "BC Public Lands"
in_field   = "RecentDevIndex"
out_field  = "DevCategory"

# 2. Add DevCategory field if it doesn't exist
existing_fields = [f.name for f in arcpy.ListFields(layer_name)]
if out_field not in existing_fields:
    print(f"Adding field: {out_field}")
    arcpy.management.AddField(layer_name, out_field, "TEXT", field_length=10)

# 3. Get layer object
aprx = arcpy.mp.ArcGISProject("CURRENT")
m    = aprx.activeMap
lyr  = m.listLayers(layer_name)[0]
original_sym = lyr.symbology

# 4. Collect unique RD names
rd_names = sorted(set(
    row[0] for row in arcpy.da.SearchCursor(layer_name, ["RD_Name"])
    if row[0] is not None
))
print(f"Found {len(rd_names)} RD names: {rd_names}")

# 5. Calculate Jenks breaks and update categories per RD
for rd in rd_names:
    where = f"RD_Name = '{rd}'"

    # Apply definition query so renderer only sees this RD's data
    lyr.definitionQuery = where
    sym = lyr.symbology
    sym.updateRenderer('GraduatedColorsRenderer')
    sym.renderer.classificationField  = in_field
    sym.renderer.classificationMethod = 'NaturalBreaks'
    sym.renderer.breakCount           = 5
    lyr.symbology = sym

    breaks = [brk.upperBound for brk in lyr.symbology.renderer.classBreaks]
    print(f"  [{rd}] Breaks: {[round(b, 2) for b in breaks]}")

    # Update categories for this RD only
    with arcpy.da.UpdateCursor(layer_name, [in_field, out_field], where_clause=where) as cursor:
        for row in cursor:
            val = row[0]
            if val is None:
                row[1] = None
            elif val <= breaks[0]:
                row[1] = "Very Low"
            elif val <= breaks[1]:
                row[1] = "Low"
            elif val <= breaks[2]:
                row[1] = "Moderate"
            elif val <= breaks[3]:
                row[1] = "High"
            else:
                row[1] = "Very High"
            cursor.updateRow(row)

# 6. Clear definition query and restore original symbology
lyr.definitionQuery = ""
lyr.symbology = original_sym
print("Field 'DevCategory' has been updated (Very Low/Low/Moderate/High/Very High).")
