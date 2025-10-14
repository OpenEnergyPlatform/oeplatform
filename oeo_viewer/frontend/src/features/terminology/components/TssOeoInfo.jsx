
import { OntologyInfoWidget } from "@ts4nfdi/terminology-service-suite";


export default function TssMetadata() {

  return (<OntologyInfoWidget
    api="https://api.terminology.tib.eu/api/"
    hasTitle
    onNavigateToDisambiguate={function cye() { }}
    onNavigateToEntity={function cye() { }}
    onNavigateToOntology={function cye() { }}
    ontologyId="oeo"
    parameter=""
    showBadges
    useLegacy
  />);
}
