"""
Step 1c: Change blanks to "N" in 3 fields:

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# Define layer and remaining text fields
table = "BC Public Lands"
fields = ["Vacant", "Riparian", "Heritage_Type"]

# Execute the update
with arcpy.da.UpdateCursor(table, fields) as cursor:
    for row in cursor:
        updated = False
        new_row = list(row)
        for i, val in enumerate(new_row):
            # Checks for database Null values, spaces, or empty text strings
            if val is None or str(val).strip() == "":
                new_row[i] = "N"
                updated = True
        if updated:
            cursor.updateRow(new_row)

print("Text fields successfully updated to 'N'.")
