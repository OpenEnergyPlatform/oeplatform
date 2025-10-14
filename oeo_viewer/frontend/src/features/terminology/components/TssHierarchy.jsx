import { HierarchyWidget } from "@ts4nfdi/terminology-service-suite";


export default function TssMetadata() {

  return (
    <HierarchyWidget
      apiKey=""
      apiUrl="https://api.terminology.tib.eu/api/"
      backendType="ols"
      entityType="class"
      iri=""
      onNavigateToEntity={function cye() { }}
      onNavigateToOntology={function cye() { }}
      ontologyId="oeo"
      parameter=""
    />
  );
}
