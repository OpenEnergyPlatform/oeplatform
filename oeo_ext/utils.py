def get_class_data(oeo_label_name: str = ""):
    # units_used = []
    D = {
        "linear_unit_numerators": [],
        "squared_unit_numerators": [],
        "cubed_unit_numerators": [],
        "linear_unit_denominators": [],
        "squared_unit_denominators": [],
        "cubed_unit_denominators": [],
    }
    label = oeo_label_name
    n = int(input("Enter number of existing units needed : "))
    for i in range(0, n):
        this_unit = str(input("Enter " + str(i + 1) + ". unit: "))
        n_or_d = str(
            input("Is " + this_unit + " used as a numerator or denominator? [n/d]")
        )
        while not (n_or_d == "n" or n_or_d == "d"):
            print(
                "Faulty Input! Please input 'n' for numerator or 'd' for denominator!"
            )
            n_or_d = str(
                input("Is " + this_unit + " used as a numerator or denominator? [n/d]")
            )
        l_or_s = str(
            input("Is " + this_unit + " used linear, squared or cubed? [l/s/c]")
        )
        while not (l_or_s == "l" or l_or_s == "s" or l_or_s == "c"):
            print(
                "Faulty Input! Please input 'l' for linear, 's' for squared or 'c' for cubed!"  # noqa
            )
            # l_or_s = str(input("Is " + u + " used linear, squared or cubed? [l/s/c]"))
        if n_or_d == "n":
            if l_or_s == "l":
                D["linear_unit_numerators"].append(this_unit)
            elif l_or_s == "s":
                D["squared_unit_numerators"].append(this_unit)
            elif l_or_s == "c":
                D["cubed_unit_numerators"].append(this_unit)
        elif n_or_d == "d":
            if l_or_s == "l":
                D["linear_unit_denominators"].append(this_unit)
            elif l_or_s == "s":
                D["squared_unit_denominators"].append(this_unit)
            elif l_or_s == "c":
                D["cubed_unit_denominators"].append(this_unit)
    return label, D


def get_new_iri(ontox):
    new_class_iri = set()
    for annot_prop in ontox.metadata:
        for i in range(len(annot_prop[ontox.metadata])):
            if "0000Counter = " in annot_prop[ontox.metadata][i]:
                newNr = annot_prop[ontox.metadata][i][len("0000Counter = ") :]
                counter = int(newNr) + 1
                annot_prop[ontox.metadata][i] = "0000Counter = " + str(counter)
                new_class_iri.update(
                    (
                        "http://openenergy-platform.org/ontology/oeo-extended/"
                        + f"{str(counter):0>4}"
                    )
                )
        ontox.save()

    return new_class_iri
