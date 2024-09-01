import types

from owlready2 import And, Ontology, Restriction, ThingClass
from rdflib import URIRef

from oeo_ext.oeo_extended_store.connection import OEO_EXT_OWL_PATH, oeo_ext_owl, oeo_owl
from oeo_ext.oeo_extended_store.namespaces import OEOX
from oeo_ext.oeo_extended_store.oeox_types import OeoxTypes
from oeo_ext.oeo_extended_store.properties import (
    UNIT,
    has_cubed_unit_denominator,
    has_cubed_unit_numerator,
    has_linear_unit_denominator,
    has_linear_unit_numerator,
    has_squared_unit_denominator,
    has_squared_unit_numerator,
    has_unit_prefix,
)


def automated_label_generator(new_unit_class: type):
    label_parts = []
    numerators = []
    denominators = []

    # Access the equivalent class definition
    if new_unit_class.equivalent_to:
        for eq_class in new_unit_class.equivalent_to:
            if isinstance(eq_class, And):
                for restriction in eq_class.Classes:
                    if isinstance(restriction, Restriction):
                        prop = restriction.property
                        target_class = restriction.value

                        # Handle cases where target_class is
                        # an And object (combination of unit and prefix)
                        if isinstance(target_class, And):
                            # Extract the unit label from the And object
                            unit_label = None
                            prefix_label = None
                            for sub_class in target_class.Classes:
                                if isinstance(sub_class, ThingClass):  # The unit part
                                    unit_label = sub_class.label[0]
                                elif (
                                    isinstance(sub_class, Restriction)
                                    and sub_class.property == has_unit_prefix
                                ):
                                    prefix_label = sub_class.value.label[0]
                            # Combine the prefix and unit if both are present
                            if prefix_label:
                                target_label = f"{prefix_label} {unit_label}"
                            else:
                                target_label = unit_label
                        else:
                            # If it's not an And object, just use the label directly
                            target_label = target_class.label[0]

                        # Check if the property corresponds to a numerator
                        if prop == has_linear_unit_numerator:
                            numerators.append(target_label)
                        elif prop == has_squared_unit_numerator:
                            if (
                                "square" in target_label.__str__()
                                or "squared" in target_label.__str__()
                            ):
                                numerators.append(f"{target_label}")
                            else:
                                numerators.append(f"squared {target_label}")
                        elif prop == has_cubed_unit_numerator:
                            if "cubic" in target_label.__str__():
                                numerators.append(f"{target_label}")
                            else:
                                numerators.append(f"cubic {target_label}")
                        # Check if the property corresponds to a denominator
                        elif prop == has_linear_unit_denominator:
                            denominators.append(target_label)
                        elif prop == has_squared_unit_denominator:
                            if (
                                "square" in target_label.__str__()
                                or "squared" in target_label.__str__()
                            ):
                                denominators.append(f"{target_label}")
                            else:
                                denominators.append(f"square {target_label}")
                        elif prop == has_cubed_unit_denominator:
                            if "cubic" in target_label.__str__():
                                denominators.append(f"{target_label}")
                            else:
                                denominators.append(f"cubic {target_label}")

    # Combine the numerators
    if numerators:
        label_parts.append(" and ".join(numerators))

    # Add 'per' and combine the denominators if they exist
    if denominators:
        label_parts.append("per")
        label_parts.append(" and ".join(denominators))

    # Combine the label parts into the final label
    generated_label = " ".join(label_parts)
    return generated_label


def generate_id(existing_count: int) -> str:
    """
    Generates an ID in the format 012345AA where the digits increment
    and the letters change.

    Args:
        existing_count (int): The current count of elements to determine the next ID.

    Returns:
        str: A new ID in the format 012345AA.
    """
    # Generate a 6-digit number, zero-padded
    num_part = f"{existing_count:06d}"

    # Generate a two-letter code
    # Example: 0 -> AA, 1 -> AB, 26 -> BA, ..., 675 -> ZZ
    letter_part = ""
    count = existing_count
    for _ in range(2):
        letter_part = chr(ord("A") + count % 26) + letter_part
        count //= 26

    return f"{num_part}{letter_part}"


def get_new_iri(
    ontox: Ontology, concept_type: OeoxTypes, base=OEOX, id_prefix="OEOX_"
) -> URIRef:
    """
    Generates a new IRI for a composed unit based on the number of
    existing elements.

    Args:
        ontox (Ontology): The ontology in which to count existing elements.
        base (str): The base URI for the new IRI.

    Returns:
        URIRef: A new unique IRI for the composed unit.
    """

    existing_count = len(list(ontox.classes()))

    # Generate the new IRI using the count + 1
    new_counter = generate_id(existing_count + 1)
    # Build URI of pattern: oeox-base/ConceptID
    new_uri = URIRef(f"{base}{id_prefix}{new_counter}")

    return new_uri


def create_new_unit(
    numerator: list,
    denominator: list,
    oeo_ext: Ontology = oeo_ext_owl,
    uriref=None,
    unit=UNIT,
    result_file=OEO_EXT_OWL_PATH,
):
    """
    return
        uriref is either URIRef type or None
        error is either dict with key:value or None
    """

    type = OeoxTypes.composedUnit
    if not uriref:
        uriref = get_new_iri(ontox=oeo_ext, concept_type=type)

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
    with oeo_ext:
        NewClass = types.new_class(uriref, (unit,))
        NewClass.equivalent_to = [intersection]

        new_label = automated_label_generator(NewClass)
        check_duplicate = oeo_ext.search_one(label=new_label)
        if check_duplicate is None:
            NewClass.label = new_label
        else:
            return None, {
                "error": f"This composedUnit: '{new_label}' already exists in the oeox"
            }

    # Save the updated ontology
    oeo_ext.save(file=str(result_file), format="rdfxml")

    return uriref, None  # Return the IRI of the newly created class
