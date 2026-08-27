"""
Step 6b: Calculate density categories and yield estimates (incl. dead zone between 116-139 UPA).

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy
table = "BC Public Lands"
# 1. Define the 7 new fields and their data types
new_fields = [
    ("MedianExisting_Density", "DOUBLE"),
    ("Existing_density_Cat", "TEXT"),
    ("Max_density_Cat", "TEXT"),
    ("Median_density_Cat", "TEXT"),
    ("Yield_Max", "DOUBLE"),
    ("Yield_Median", "DOUBLE"),
    ("Yield_Existing", "DOUBLE")
]
# 2. Add fields safely if they do not exist
existing_fields = [f.name for f in arcpy.ListFields(table)]
for field_name, field_type in new_fields:
    if field_name not in existing_fields:
        length = 50 if field_type == "TEXT" else None
        arcpy.management.AddField(table, field_name, field_type, field_length=length)
# 3. Define cursor fields (Inputs + Outputs)
cursor_fields = [
    "Existing_Density", "Max_Density", "Median_Density", "Shape_Area", "TOA_Density",  # Indices 0, 1, 2, 3, 4
    "MedianExisting_Density", "Existing_density_Cat", "Max_density_Cat", "Median_density_Cat", # Indices 5, 6, 7, 8
    "Yield_Max", "Yield_Median", "Yield_Existing"                                       # Indices 9, 10, 11
]
# Helper function to categorize density
def categorize_density(density):
    if density is None:
        return "Unknown"
    if density <= 25:
        return "Low"
    elif density < 140:
        return "Moderate"
    elif density < 200:
        return "High"
    else:
        return "Very High"
# Helper function to calculate corrected yield (Density * Area in Acres)
# Converts area from m2 to acres (1 m2 = 0.0002471054 acres)
def calculate_yield_corrected(density, area_m2):
    if density is None or area_m2 is None:
        return None
 
    # Apply density override rule (if between 116 and 139, cap at 115)
    calc_density = 115.0 if 116 <= density <= 139 else float(density)
 
    area_acres = float(area_m2) * 0.0002471054
    return calc_density * area_acres
# 4. Process data rows safely using list index assignments
with arcpy.da.UpdateCursor(table, cursor_fields) as cursor:
    for row in cursor:
        ex_dens, max_dens, med_dens, area, toa_dens = row[0], row[1], row[2], row[3], row[4]
 
        # Ensure base numeric inputs are evaluated correctly
        ex_val  = float(ex_dens)  if ex_dens  is not None else 0.0
        max_val = float(max_dens) if max_dens is not None else 0.0
        med_val = float(med_dens) if med_dens is not None else 0.0
        toa_val = float(toa_dens) if toa_dens is not None else 0.0

        # Effective max density: higher of Max_Density or TOA_Density
        eff_max_val = max(max_val, toa_val)

        # Calculate MedianExisting_Density
        med_ex_dens = max(ex_val, med_val)
        row[5] = med_ex_dens
 
        # Categorizations
        row[6] = categorize_density(ex_val)       # Existing_density_Cat
        row[7] = categorize_density(eff_max_val)  # Max_density_Cat (larger of Max_Density / TOA_Density)
        row[8] = categorize_density(med_ex_dens)  # Median_density_Cat
 
        # Yield Calculations (Density * Area in Acres)
        row[9]  = calculate_yield_corrected(eff_max_val, area)  # Yield_Max
        row[10] = calculate_yield_corrected(med_ex_dens, area)  # Yield_Median
        row[11] = calculate_yield_corrected(ex_val, area)       # Yield_Existing
 
        # Pass the complete row sequence back to ArcPy
        cursor.updateRow(row)
print("Density analysis and corrected Yield calculations complete.")
