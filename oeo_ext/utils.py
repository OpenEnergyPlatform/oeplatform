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
