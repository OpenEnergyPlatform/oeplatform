import React from "react";
import { AutocompleteWidget } from "@ts4nfdi/terminology-service-suite";

export default function TssAutocomplete({
  api = "https://terminology.services.base4nfdi.de/api-gateway/",
  placeholder = "Type to search...",
  onChange = () => {},
  ontology,
}) {
  const parameter = [
    "fieldList=description,label,iri,ontology_name,type,short_form",
    ontology ? `ontologies=${encodeURIComponent(ontology)}` : null,
  ].filter(Boolean).join("&");

  return (
    <AutocompleteWidget
      api={api}
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
