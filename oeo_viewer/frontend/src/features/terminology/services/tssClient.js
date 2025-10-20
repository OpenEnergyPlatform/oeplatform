import axios from "axios";

// Small helper to build a client bound to the current config
export function makeTssClient({ apiBase, requestHeaders = {} }) {
  const http = axios.create({
    baseURL: apiBase.replace(/\/+$/, "/"), // ensure trailing slash
    headers: { ...requestHeaders },
    timeout: 20_000,
  });

  return {
    // Example endpoints – adjust to the suite/gateway you use
    search: (params) => http.get("search", { params }),
    concept: (iri) => http.get("concept", { params: { iri } }),
    hierarchy: (iri) => http.get("hierarchy", { params: { iri } }),
  };
}
