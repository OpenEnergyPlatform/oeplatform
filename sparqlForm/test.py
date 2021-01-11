inputSubject = "<https://openenergy-platform.org/thing/_Venkatesh_Murugadas>"
inputPredicate = "<http://xmlns.com/foaf/0.1/givenName>"
inputObject = '"Venkatesh"'
updateSubject = "<https://openenergy-platform.org/thing/_Venkatesh_Murugadas>"
updatePredicate = "<http://xmlns.com/foaf/0.1/givenName>"
updateObject = '"Venkatesh Murugadas"'
# triple = inputSubject + " " + inputPredicate + " " + inputObject

# print(triple)

oldTriple = inputSubject + " " + inputPredicate + " " + inputObject
newTriple = updateSubject + " " + updatePredicate + " " + updateObject
print(
    """
        DELETE { """
    + oldTriple
    + """
        } INSERT {"""
    + newTriple
    + """}WHERE { """
    + oldTriple
    + """}
        """
)
