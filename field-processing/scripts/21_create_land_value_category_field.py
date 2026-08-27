"""
Step 21: Create Land Value category field

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# --- Config ---
fc = "BC Public Lands"          # canonical feature class
value_field = "sum_Gen_Gross_Land_Value"
cat_field = "LandValue_Cat"

# --- Add the category field if it doesn't exist ---
existing = [f.name for f in arcpy.ListFields(fc)]
if cat_field not in existing:
    arcpy.management.AddField(fc, cat_field, "TEXT", field_length=12)

# --- Categorize ---
def categorize(v):
    if v is None:
        return "n/a"
    if v < 50000:
        return "< $50K"
    elif v < 250000:
        return "$50-250K"
    elif v < 1000000:
        return "$250K-1M"
    elif v < 5000000:
        return "$1-5M"
    else:
        return "> $5M"

with arcpy.da.UpdateCursor(fc, [value_field, cat_field]) as cur:
    for value, _ in cur:
        cur.updateRow([value, categorize(value)])

print(f"Done. '{cat_field}' populated on {fc}.")
