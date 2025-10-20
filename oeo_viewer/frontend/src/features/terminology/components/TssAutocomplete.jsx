// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later


import React from "react";
import { AutocompleteWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssAutocomplete({
  api,                 // optional override
  placeholder = "Type to search...",
  onChange = () => { },
  ontology,            // optional override
}) {
  const { apiBase, ontology: cfgOntology } = useTssConfig();

  const effectiveApi = api ?? apiBase;
  const effectiveOntology = (ontology ?? cfgOntology)?.trim();

  // Build the parameter string. The suite expects 'fieldList=...' and
  // (optionally) 'ontologies=' to restrict by ontology.
  const parameter = [
    "fieldList=description,label,iri,ontology_name,type,short_form&",
    effectiveOntology ? `ontology=${encodeURIComponent(effectiveOntology)}` : null,
  ].filter(Boolean).join("&");

  return (
    <AutocompleteWidget
      api={effectiveApi}
      placeholder={placeholder}
      parameter={parameter}
      hasShortSelectedLabel
      initialSearchQuery=""
      preselected={[]}
      selectionChangedEvent={onChange}
      showApiSource
      singleSelection
      useLegacy
    />
  );
}




// const navigate = useNavigate();

// <AutocompleteWidget
//   api={global_config.api_url}
//   placeholder={"Type to search"}
//   selectionChangedEvent={(selectedOption) => {
//     navigateToEntity(selectedOption, navigate);
//   }}
//   parameter="collection=nfdi4health&fieldList=description,label,iri,ontology_name,type,short_form"
//   allowCustomTerms={false}
//   singleSelection={true}
//   hasShortSelectedLabel={true}
// />


// /**
// * Global function which gets passed as selectionChangedEvent of AutocompleteWidget on several pages to navigate to the newly selected entity
// * @param selectedOption    the passed on selectedOptions of the entity
// * @param navigate          a function argument to pass the hook useNavigate() to use it outside a function component
// */
// export function navigateToEntity(
//   selectedOption: {
//     label: string;
//     iri?: string;
//     ontology_name?: string;
//     type?: string;
//   }[],
//   navigate: NavigateFunction
// ) {
//   if (selectedOption[0]) {
//     const targetIri = encodeURIComponent(
//       encodeURIComponent(selectedOption[0].iri)
//     );
//     // '#' and '&' have to be URI-escaped because the iri gets passed as query search parameter in the URL
//     if (selectedOption[0].type === "class") {
//       // Not checking if "term" should be right here because the api only uses class. However, this comment might be useful if related bugs should be detected later
//       navigate({
//         pathname: "/ontologies/" + selectedOption[0].ontology_name + "/terms",
//         search: "iri=" + targetIri,
//       });
//     } else if (selectedOption[0].type === "individual") {
//       navigate({
//         pathname:
//           "/ontologies/" + selectedOption[0].ontology_name + "/individuals",
//         search: "iri=" + targetIri,
//       });
//     } else if (selectedOption[0].type === "property") {
//       navigate({
//         pathname:
//           "/ontologies/" + selectedOption[0].ontology_name + "/properties",
//         search: "iri=" + targetIri,
//       });
//     } else if (selectedOption[0].type === "ontology") {
//       navigate({
//         pathname: "/ontologies/" + selectedOption[0].ontology_name + "/",
//       });
//     }
//   }
// }
