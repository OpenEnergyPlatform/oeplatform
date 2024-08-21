from oeo_ext.oeo_extended_store.connection import oeo_owl

# Static parts, object properties:
has_linear_unit_numerator = oeo_owl.search_one(label="has unit numerator")
has_squared_unit_numerator = oeo_owl.search_one(label="has squared unit numerator")
has_cubed_unit_numerator = oeo_owl.search_one(label="has cubed unit numerator")
has_linear_unit_denominator = oeo_owl.search_one(label="has linear unit denominator")
has_squared_unit_denominator = oeo_owl.search_one(label="has squared unit denominator")
has_cubed_unit_denominator = oeo_owl.search_one(label="has cubed unit denominator")
UNIT = oeo_owl.search_one(label="unit")
