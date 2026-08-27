"""
Step 22: Static calculation of Land Value by Jurisdiction

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy
from collections import defaultdict

# ---- Config ----
fc = "BC Public Lands"
juris_field = "JURISDICTION"
value_field = "sum_Gen_Gross_Land_Value"
sort_by_value = True   # True = sort output by total value (desc); False = alphabetical by jurisdiction
# ----------------

totals = defaultdict(float)   # jurisdiction -> running sum
counts = defaultdict(int)     # jurisdiction -> record count
null_value_rows = 0
null_juris_rows = 0

with arcpy.da.SearchCursor(fc, [juris_field, value_field]) as cursor:
    for juris, val in cursor:
        # Normalize the jurisdiction key
        if juris is None or (isinstance(juris, str) and juris.strip() == ""):
            juris = "n/a"
            null_juris_rows += 1

        # Skip/track null values but still count the row under its jurisdiction
        if val is None:
            null_value_rows += 1
            counts[juris] += 1
            continue

        totals[juris] += val
        counts[juris] += 1

# ---- Output ----
if sort_by_value:
    ordered = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
else:
    ordered = sorted(totals.items(), key=lambda kv: kv[0])

print("Sum of {0} by {1}".format(value_field, juris_field))
print("-" * 60)
grand_total = 0.0
for juris, total in ordered:
    grand_total += total
    print("{0:<35} {1:>18,.2f}  (n={2})".format(juris, total, counts[juris]))

print("-" * 60)
print("{0:<35} {1:>18,.2f}".format("GRAND TOTAL", grand_total))
print("")
print("Jurisdictions: {0}".format(len(totals)))
print("Rows with null {0}: {1}".format(value_field, null_value_rows))
print("Rows with null/blank {0}: {1}".format(juris_field, null_juris_rows))
