"""
Step 15: Under or vacant field

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# 1. Define your parameters
target_layer = "BC Public Lands"
new_field = "Under_or_Vacant"

# 2. Create a robust Python multi-line code block function
code_block = """
def check_vacancy(vacant, percent_improve):
    # Safely convert to string and handle Nulls/None
    if vacant is None:
        vac_clean = ""
    else:
        vac_clean = str(vacant).strip().upper()
 
    # Check your conditions safely
    if vac_clean == "Y":
        return "Y"
    elif percent_improve is not None and percent_improve < 20:
        return "Y"
    else:
        return "N"
"""

# 3. Call the function inside the expression box
expression = "check_vacancy(!Vacant!, !PercentImproveLand!)"

# 4. Run the Calculate Field tool
print(f"Calculating values for '{new_field}'...")
try:
    arcpy.management.CalculateField(
        in_table=target_layer,
        field=new_field,
        expression=expression,
        expression_type="PYTHON3",
        code_block=code_block
    )
    print("Process complete! Field updated successfully.")
except arcpy.ExecuteError:
    print(arcpy.GetMessages(2))
