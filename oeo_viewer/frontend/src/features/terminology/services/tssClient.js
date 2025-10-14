export function buildTssOptions({ apiBase, ontology = "oeo", lang = "en" } = {}) {
  // These option names mirror the Storybook props; adjust names once you confirm in the docs.
  return {
    apiBase,     // base URL for TS4NFDI gateway
    ontology,    // e.g., "SNOMED", "LOINC", "HPO" (depends on your use case)
    lang,        // UI / query language if supported
  };
}
