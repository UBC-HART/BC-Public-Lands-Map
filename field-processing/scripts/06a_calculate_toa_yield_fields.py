"""
Step 6a: Calculate TOA yield fields

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# --- 1. CONFIGURATION ---
target_layer = "BC Public Lands"
lookup_table = "TOA_Categories_ExcelToTable"

# Conversion constant
SQM_PER_ACRE = 4046.86

# Official BC Transit-Oriented Area (TOA) FSR Lookup Map
# Adjust these decimal values if your jurisdiction uses alternative FSR schedules.
fsr_lookup = {
    "1": 5.0, "2": 4.0, "3": 3.0,
    "4A": 4.0, "4B": 3.0, "4C": 2.5,
    "5A": 3.0, "5B": 2.5, "5C": 2.0
}

# --- 2. ADD NEW FIELDS ---
print("Adding new fields if they do not already exist...")
existing_fields = [f.name for f in arcpy.ListFields(target_layer)]
if "TOA_Tier_v2" not in existing_fields:
    arcpy.management.AddField(target_layer, "TOA_Tier_v2", "TEXT", field_length=10)
if "TOA_Density" not in existing_fields:
    arcpy.management.AddField(target_layer, "TOA_Density", "DOUBLE")
if "TOA_Yield" not in existing_fields:
    arcpy.management.AddField(target_layer, "TOA_Yield", "DOUBLE")

# --- 3. LOAD STANDALONE EXCEL TABLE TO MEMORY ---
print(f"Reading lookup data from '{lookup_table}'...")
category_dict = {}  # Format: { 'JurisdictionName': 'Category_Letter' }
# Assumed fields in Excel Table: 'Jurisdiction' and 'TOA_Category'
with arcpy.da.SearchCursor(lookup_table, ["Jurisdiction", "TOA_Category"]) as s_cursor:
    for row in s_cursor:
        jurisdiction = row[0]
        category = row[1]
        if jurisdiction and category:
            # Clean text values (strip spaces, normalize case)
            category_dict[str(jurisdiction).strip().lower()] = str(category).strip()

# --- 4. UPDATE TARGET LAYER ---
print(f"Calculating fields in '{target_layer}'...")
fields_to_update = ["TOA_Tier", "Jurisdiction", "TOA_Tier_v2", "TOA_Density", "Area_m2", "TOA_Yield"]
updated_count = 0
with arcpy.da.UpdateCursor(target_layer, fields_to_update) as u_cursor:
    for row in u_cursor:
        toa_tier = str(row[0]).strip() if row[0] is not None else ""
        jurisdiction = str(row[1]).strip().lower() if row[1] is not None else ""
        area_m2 = row[4] if row[4] is not None else 0

        # Initialize variables
        tier_v2 = None
        density = None
        yield_val = None

        # --- TASK 1: TOA_Tier_v2 Logic ---
        if toa_tier in ["1", "2", "3"]:
            tier_v2 = toa_tier

        elif toa_tier in ["4", "5"]:
            if jurisdiction in category_dict:
                cat_letter = category_dict[jurisdiction]  # Expected: 'A', 'B', 'C', or 'n/a'
                if cat_letter.lower() != "n/a" and cat_letter.upper() in ["A", "B", "C"]:
                    tier_v2 = f"{toa_tier}{cat_letter.upper()}"
                else:
                    tier_v2 = None  # Category is 'n/a' maps to Null

        # --- TASK 2: TOA_Density Logic ---
        if tier_v2 in fsr_lookup:
            fsr = fsr_lookup[tier_v2]
            # Formula: (4046.86 * FSR * 0.825) / 65
            calculated_density = (SQM_PER_ACRE * fsr * 0.825) / 65
            # Cap at 250 max
            density = min(calculated_density, 250.0)

        # --- TASK 3: TOA_Yield Logic ---
        # density is units/acre, so area must be in acres
        if density is not None and area_m2 > 0:
            area_acres = area_m2 / SQM_PER_ACRE
            yield_val = area_acres * density

        # Save updates back into row
        row[2] = tier_v2
        row[3] = density
        row[5] = yield_val
        u_cursor.updateRow(row)
        updated_count += 1

print(f"Finished! Successfully added fields and processed {updated_count} records.")
