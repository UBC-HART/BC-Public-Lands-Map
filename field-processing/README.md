# BCPLM Field-Processing Scripts

This repository contains the sequential ArcGIS Pro scripts used to add and
populate derived fields on the **BC Public Lands** feature class, developed
as part of the BC Public Lands Map (BCPLM) project, a provincial public-lands
parcel mapping and scoring tool.

This stage follows on from `AppendRD.py` at the repository root, which
produces the merged "BC Public Lands" layer covering all regional districts.
The scripts here operate on that layer directly, adding the fields used for
parcel scoring and the map's public-facing attributes.

## What this is

These scripts were developed individually over several months, each adding
or recalculating a specific field, or a small set of related fields, on the
parcel layer. This includes address construction, density and yield
estimates, amenity proximity categories, infrastructure data-gap flags, and
the final parcel score. They do not constitute a single automated pipeline.
Rather, each script was run on its own in the ArcGIS Pro Python window, with
the output checked before proceeding to the next.

This repository preserves that structure rather than consolidating it into
one script, for the following reasons:

- Several steps depend on fields created by earlier steps.
- Two steps (**5** and **24**) are manual operations carried out in the
  ArcGIS Pro interface and have no associated code.
- Step **10** has two alternative versions (10a / 10b), depending on how the
  source layer was constructed. Only one of the two should be run.
- Re-running certain steps without checking for existing output is not
  guaranteed to be safe (e.g. re-adding a field that already exists), so a
  single "run everything" script would risk being misleading rather than
  useful.

## How to use these

1. Open the **BC Public Lands** layer in ArcGIS Pro and open the Python
   window, or a Notebook within the same project.
2. Work through the scripts in numeric order (see `scripts/`), pasting each
   one in and reviewing the printed output or row counts before proceeding
   to the next.
3. Adapt or skip anything specific to this project's schema, such as field
   names, the regional-district dictionary, or lookup tables, if these
   scripts are being reused for a different dataset.

These scripts require an ArcGIS Pro license (`arcpy`) and an active map with
the target layer loaded. They are not intended to be run as standalone
scripts from a plain Python interpreter.

## Step index

| # | Script | Description | Type |
|---|--------|-------------|------|
| 1a | [`01a_update_percentimproveland.py`](scripts/01a_update_percentimproveland.py) | Update PercentImproveLand | Script |
| 1b | [`01b_update_underutilized.py`](scripts/01b_update_underutilized.py) | Update Underutilized | Script |
| 1c | [`01c_change_blanks_to_n_in_3_fields.py`](scripts/01c_change_blanks_to_n_in_3_fields.py) | Change blanks to "N" in 3 fields: | Script |
| 1d | [`01d_update_vacant_values_to_y_if_percentimproveland_0_and_n.py`](scripts/01d_update_vacant_values_to_y_if_percentimproveland_0_and_n.py) | Update Vacant values to "Y" if PercentImproveLand = 0 and "N" otherwise | Script |
| 2 | [`02_update_drainageclass.py`](scripts/02_update_drainageclass.py) | Update DrainageClass | Script |
| 3a | [`03a_create_new_fields_and_calculate_x_y_coordinates.py`](scripts/03a_create_new_fields_and_calculate_x_y_coordinates.py) | Create new fields and calculate X & Y coordinates | Script |
| 3b | [`03b_create_full_address_and_address_url_updated_to_include.py`](scripts/03b_create_full_address_and_address_url_updated_to_include.py) | Create Full_Address and Address_url (updated to include X&Y coordinates if No Address Available) (*Updated June 29 with street direction: W, E, etc.) | Script |
| 4 | [`04_create_est_width_est_length_rectagle_chk_est_aspect_ra.py`](scripts/04_create_est_width_est_length_rectagle_chk_est_aspect_ra.py) | Create Est_Width, Est_Length, Rectagle_Chk, Est_Aspect_Ra, and Irregular fields | Script |
| 5 | [`05_calculate_area_m2_field_manually_use_calculate_geometry.md`](scripts/05_calculate_area_m2_field_manually_use_calculate_geometry.md) | Calculate "Area_m2" field manually; use Calculate Geometry geoprocessing tool | Manual |
| 6a | [`06a_calculate_toa_yield_fields.py`](scripts/06a_calculate_toa_yield_fields.py) | Calculate TOA yield fields | Script |
| 6b | [`06b_calculate_density_categories_and_yield_estimates_incl_d.py`](scripts/06b_calculate_density_categories_and_yield_estimates_incl_d.py) | Calculate density categories and yield estimates (incl. dead zone between 116-139 UPA). | Script |
| 7 | [`07_calculate_grocery_store_proximity.py`](scripts/07_calculate_grocery_store_proximity.py) | Calculate grocery store proximity | Script |
| 8 | [`08_calculate_pharmacy_and_transit_proximity.py`](scripts/08_calculate_pharmacy_and_transit_proximity.py) | Calculate pharmacy and transit proximity | Script |
| 9 | [`09_calculate_amenity_fields_as_the_greater_of_walking_or_transit.py`](scripts/09_calculate_amenity_fields_as_the_greater_of_walking_or_transit.py) | Calculate amenity fields as the greater of Walking or Transit | Script |
| 10a | [`10a_create_rd_name_field_local_merge.py`](scripts/10a_create_rd_name_field_local_merge.py) | Create RD_Name field (layer merged locally) | Script |
| 10b | [`10b_create_rd_name_field_from_premerged_layer.py`](scripts/10b_create_rd_name_field_from_premerged_layer.py) | Create RD_Name field (copy from an already-merged layer) | Script |
| 11 | [`11_calculate_amenity_terciles_by_regional_district_and_cat.py`](scripts/11_calculate_amenity_terciles_by_regional_district_and_cat.py) | Calculate amenity terciles by regional district and categories | Script |
| 12 | [`12_add_development_category_field.py`](scripts/12_add_development_category_field.py) | Add Development Category field | Script |
| 13 | [`13_adding_flood_risk_category.py`](scripts/13_adding_flood_risk_category.py) | Adding flood risk category | Script |
| 14 | [`14_create_zoning_summary_field.py`](scripts/14_create_zoning_summary_field.py) | Create Zoning summary field | Script |
| 15 | [`15_under_or_vacant_field.py`](scripts/15_under_or_vacant_field.py) | Under or vacant field | Script |
| 16 | [`16_actual_use_derived_field.py`](scripts/16_actual_use_derived_field.py) | Actual use derived field | Script |
| 17 | [`17_create_new_cleaned-up_fields.py`](scripts/17_create_new_cleaned-up_fields.py) | Create new cleaned-up fields | Script |
| 18 | [`18_new_field_under_or_vacant_chart.py`](scripts/18_new_field_under_or_vacant_chart.py) | New field: Under_or_Vacant_chart | Script |
| 19 | [`19_calculate_scoring.py`](scripts/19_calculate_scoring.py) | Calculate scoring | Script |
| 20 | [`20_create_cleaned_infrastructure_fields_depending_on_if_da.py`](scripts/20_create_cleaned_infrastructure_fields_depending_on_if_da.py) | Create cleaned Infrastructure fields depending on if "Data Gap" is flagged for the jurisdiction | Script |
| 21 | [`21_create_land_value_category_field.py`](scripts/21_create_land_value_category_field.py) | Create Land Value category field | Script |
| 22 | [`22_static_calculation_of_land_value_by_jurisdiction.py`](scripts/22_static_calculation_of_land_value_by_jurisdiction.py) | Static calculation of Land Value by Jurisdiction | Script |
| 23 | [`23_create_new_field_intersects_with_road_and_calculate.py`](scripts/23_create_new_field_intersects_with_road_and_calculate.py) | Create new field "Intersects_with_road" and calculate | Script |
| 24 | [`24_manual_-_spatial_join_with_lg_ocp_with_typology_layer_t.md`](scripts/24_manual_-_spatial_join_with_lg_ocp_with_typology_layer_t.md) | MANUAL - Spatial join with "LG_OCP_with_typology" layer to bring in "Inferred Building Typology simple" field for BCPLM layer. Then create new "BC Public Lands" layer (right-click layer -> Data -> Export Features) | Manual |
| 25 | [`25_change_nulls_to_no_data_available_for_inferred_building.py`](scripts/25_change_nulls_to_no_data_available_for_inferred_building.py) | Change nulls to "No data available" for "Inferred Building Typology simple" field | Script |

## Notes

- **Step 10 (RD_Name):** Run `10a` if the layer was merged locally from the
  original per-regional-district source layers. Run `10b` instead if the
  layer came from an already-merged layer, for instance one built by a
  collaborator, in which case `RD_Name` is copied over by matching on
  `PID_NUMBER`. Note that `CZRD` refers to Comox Valley and `SUN` refers to
  the Stikine Region.
