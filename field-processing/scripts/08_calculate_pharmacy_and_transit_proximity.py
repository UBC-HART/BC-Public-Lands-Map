"""
Step 8: Calculate pharmacy and transit proximity

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.

Numbering note: two unrelated steps were both labeled "8." in the original working notes. This is the first of the two (pharmacy/transit proximity); the second (amenity max of walk/transit) is filed as 08b.
"""

import arcpy

# --- Configuration ---
fc = "BC Public Lands"

# --- Step 1: Add new category fields ---
arcpy.management.AddField(fc, "Pharmacy_cat", "TEXT", field_length=10)
arcpy.management.AddField(fc, "Transit_cat", "TEXT", field_length=10)
print("Fields added successfully.")

# --- Step 2: Define categorization function ---
def get_category(distance):
    if distance is None:
        return None
    elif distance < 720:
        return "Excellent"
    elif distance < 1440:
        return "Good"
    elif distance < 2160:
        return "Poor"
    else:
        return "None"

# --- Step 3: Populate fields using an Update Cursor ---
fields = ["Pharmacy_Dist", "Transit_Dist", "Pharmacy_cat", "Transit_cat"]

with arcpy.da.UpdateCursor(fc, fields) as cursor:
    for row in cursor:
        row[2] = get_category(row[0])  # Pharmacy_cat from Pharmacy_Dist
        row[3] = get_category(row[1])  # Transit_cat from Transit_Dist
        cursor.updateRow(row)

print("Categories populated successfully.")
