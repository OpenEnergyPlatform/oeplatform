import types

from owlready2 import And, Ontology
from rdflib import URIRef

from oeo_ext.oeo_extended_store.connection import OEO_EXT_OWL_PATH, oeo_ext_owl, oeo_owl
from oeo_ext.oeo_extended_store.namespaces import OEOX
from oeo_ext.oeo_extended_store.oeox_types import OeoxTypes

# Static parts, object properties:
has_linear_unit_numerator = oeo_owl.search_one(label="has unit numerator")
has_squared_unit_numerator = oeo_owl.search_one(label="has squared unit numerator")
has_cubed_unit_numerator = oeo_owl.search_one(label="has cubed unit numerator")
has_linear_unit_denominator = oeo_owl.search_one(label="has linear unit denominator")
has_squared_unit_denominator = oeo_owl.search_one(label="has squared unit denominator")
has_cubed_unit_denominator = oeo_owl.search_one(label="has cubed unit denominator")
has_unit_prefix = oeo_owl.search_one(label="has prefix")
UNIT = oeo_owl.search_one(label="unit")

# UNITS = oeo.search(label="unit")


def automated_label_generator():
    return NotImplementedError


# def get_new_iri(ontox: Ontology, concept_type: OeoxTypes, base=OEOX) -> URIRef:
#     new_uri: URIRef
#     for annot_prop in ontox.metadata:
#         for i in range(len(annot_prop[ontox.metadata])):
#             if "0000Counter = " in annot_prop[ontox.metadata][i]:
#                 newNr = annot_prop[ontox.metadata][i][len("0000Counter = ") :]
#                 counter = int(newNr) + 1
#                 annot_prop[ontox.metadata][i] = "0000Counter = " + str(counter)
#                 new_uri = URIRef(base=OEOX, value=str(counter))

#     return new_uri


def get_new_iri(
    ontox: Ontology, concept_type: OeoxTypes, base=OEOX, id_prefix="OEOX_"
) -> URIRef:
    """
    Generates a new IRI for a composed unit based on the number of existing elements.

    Args:
        ontox (Ontology): The ontology in which to count existing elements.
        base (str): The base URI for the new IRI.

    Returns:
        URIRef: A new unique IRI for the composed unit.
    """

    existing_count = len(list(ontox.classes()))

    # Generate the new IRI using the count + 1
    new_counter = existing_count + 1
    # Build URI of pattern: oeox-base:ConceptLike<ComposedUnit>#ConceptID
    new_uri = URIRef(f"{base}{concept_type.value}/{id_prefix}{new_counter}")

    return new_uri


def build_composed_unit():
    raise NotImplementedError


def create_new_unit(
    numerator: list,
    denominator: list,
    oeo_ext_owl: Ontology = oeo_ext_owl,
    uriref=None,
    unit=UNIT,
):
    """
    return
        uriref is either URIRef type or None
        error is either dict with key:value or None
    """
    type = OeoxTypes.composedUnit
    if not uriref:
        uriref = get_new_iri(oeo_ext_owl, type)

    # Create the list to store the equivalent class restrictions
    equivalent_classes = []

    if not numerator:
        return None, {"error": "The numerator can't be empty!"}

    def build_combined_restriction(unitName, unitType, unitPrefix, numerator=True):
        """Helper function to build combined restrictions."""
        unit_class = oeo_owl.search_one(label=unitName)

        if not unit_class:
            raise ValueError(f"Unit '{unitName}' not found in the ontology.")

        # If a prefix is provided, combine it with the unit
        if unitPrefix:
            prefix_class = oeo_owl.search_one(label=unitPrefix)
            if not prefix_class:
                raise ValueError(f"Prefix '{unitPrefix}' not found in the ontology.")
            # Combine the unit with prefix
            combined_unit = And([unit_class, has_unit_prefix.some(prefix_class)])
        else:
            combined_unit = unit_class

        # Determine the appropriate restriction based on the unit type
        if numerator:
            if unitType == "linear":
                return has_linear_unit_numerator.some(combined_unit)
            elif unitType == "squared":
                return has_squared_unit_numerator.some(combined_unit)
            elif unitType == "cubed":
                return has_cubed_unit_numerator.some(combined_unit)
            else:
                raise ValueError(f"Unknown numerator type: {unitType}")
        else:
            if unitType == "linear":
                return has_linear_unit_denominator.some(combined_unit)
            elif unitType == "squared":
                return has_squared_unit_denominator.some(combined_unit)
            elif unitType == "cubed":
                return has_cubed_unit_denominator.some(combined_unit)
            else:
                raise ValueError(f"Unknown denominator type: {unitType}")

    # Process numerators
    for elem in numerator:
        restriction = build_combined_restriction(
            elem.get("unitName"),
            elem.get("unitType"),
            elem.get("unitPrefix"),
            numerator=True,
        )
        equivalent_classes.append(restriction)

    # Process denominators
    if denominator:
        for elem in denominator:
            restriction = build_combined_restriction(
                elem.get("unitName"),
                elem.get("unitType"),
                elem.get("unitPrefix"),
                numerator=False,
            )
            equivalent_classes.append(restriction)

    # Combine the restrictions into an intersection using the & operator
    if equivalent_classes:
        intersection = equivalent_classes[0]
        for restriction in equivalent_classes[1:]:
            intersection = intersection & restriction
    else:
        return None, {
            "error": "No equivalent_classes found while building the composedUnit."
        }

    # Create the new OWL class with the constructed equivalent class
    with oeo_ext_owl:
        NewClass = types.new_class(uriref, (unit,))
        NewClass.equivalent_to = [intersection]

    # Save the updated ontology
    oeo_ext_owl.save(file=str(OEO_EXT_OWL_PATH), format="rdfxml")

    return uriref, None  # Return the IRI of the newly created class
