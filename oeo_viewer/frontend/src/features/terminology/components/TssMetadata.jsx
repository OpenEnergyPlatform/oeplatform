import { MetadataWidget } from "@ts4nfdi/terminology-service-suite";


export default function TssMetadata(){

  return (<MetadataWidget
  altNamesTab
  api="https://api.terminology.tib.eu/api/"
  crossRefTab
  entityType="term"
  graphViewTab
  hierarchyTab
  hierarchyWrap
  iri="https://openenergyplatform.org/ontology/oeo/OEO_00000207"
  onNavigateToDisambiguate={function cye(){}}
  onNavigateToEntity={function cye(){}}
  onNavigateToOntology={function cye(){}}
  ontologyId="oeo"
  parameter=""
  termDepictionTab
  termLink=""
  terminologyInfoTab
  useLegacy
/>);
}
