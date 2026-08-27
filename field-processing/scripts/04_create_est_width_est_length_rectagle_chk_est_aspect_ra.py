"""
Step 4: Create Est_Width, Est_Length, Rectagle_Chk, Est_Aspect_Ra, and Irregular fields

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

table = "BC Public Lands"

# 1. Define the 5 new fields and their data types
new_fields = [
    ("Est_Width", "DOUBLE"),
    ("Est_Length", "DOUBLE"),
    ("Rectangle_Chk", "DOUBLE"),
    ("Est_Aspect_Ra", "DOUBLE"),
    ("Irregular", "TEXT")
]

# 2. Add the fields safely if they do not exist
existing_fields = [f.name for f in arcpy.ListFields(table)]
for field_name, field_type in new_fields:
    if field_name not in existing_fields:
        # Giving text field a standard length of 50 characters
        length = 50 if field_type == "TEXT" else None
        arcpy.management.AddField(table, field_name, field_type, field_length=length)

# 3. Define all fields required for the calculations (source geometry + new fields)
cursor_fields = [
    "THICKNESS", "Shape_Area", "Shape_Length",
    "Est_Width", "Est_Length", "Rectangle_Chk", "Est_Aspect_Ra", "Irregular"
]

# 4. Process and calculate rows using an update cursor
with arcpy.da.UpdateCursor(table, cursor_fields) as cursor:
    for row in cursor:
        thickness, area, length, _, _, _, _, _ = row
 
        # Skip row calculations if critical input geometry data is missing or zero
        if thickness is None or area is None or length is None or area == 0:
            row[7] = "Unknown"
            cursor.updateRow(row)
            continue
 
        try:
            # Field 1: Est_Width
            width = float(thickness) * 2
            row[3] = width
 
            # Field 2: Est_Length
            if width == 0:
                raise ZeroDivisionError
            length_val = float(area) / width
            row[4] = length_val
 
            # Field 3: Rectangle_Chk
            rect_chk = abs((width * (float(length) - 2 * width) / 2) / float(area))
            row[5] = rect_chk
 
            # Field 4: Est_Aspect_Ra
            aspect_ra = length_val / width
            row[6] = aspect_ra
 
            # Field 5: Irregular (Your custom logic)
            if float(area) > 5000:
                class_result = "n/a (large parcel)"
            else:
                is_not_rect = (rect_chk < 0.9 or rect_chk > 1.1)
                is_too_long = (aspect_ra > 4)
 
                if is_not_rect or is_too_long:
                    class_result = "Irregular"
                else:
                    class_result = "Regular"
            row[7] = class_result

        except (ValueError, TypeError, ZeroDivisionError):
            row[7] = "Unknown"
 
        cursor.updateRow(row)

print("All 5 spatial calculation fields successfully created and populated.")
