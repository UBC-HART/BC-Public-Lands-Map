"""
Step 2: Update DrainageClass

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# Define layer and target field
table = "BC Public Lands"
field = ["DrainageClass"]

# Execute the update
with arcpy.da.UpdateCursor(table, field) as cursor:
    for row in cursor:
        val = row[0]
        # Checks if the value is Null, empty, or explicitly "NA"
        if val is None or str(val).strip() in ["", "NA"]:
            row[0] = "No data"
            cursor.updateRow(row)

print("DrainageClass nulls and 'NA' values successfully updated to 'n/a'.")
