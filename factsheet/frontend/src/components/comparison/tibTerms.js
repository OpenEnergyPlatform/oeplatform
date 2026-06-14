// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// Resolve an ontology IRI to { label, description } via the TIB Terminology
// Service. Extracted from quantitativeView.jsx so the registry-driven view can
// reuse the exact same resolution (terms → individuals → properties) and cache.
// OEO references all terms under its own base, so we normalise to the oeo IRI
// from the short form before querying.

import axios from "axios";

const cache = {};

export async function resolveTerm(iri) {
  if (!iri) return null;
  if (cache[iri]) return cache[iri];

  const shortForm = iri.split("/").pop().split(":").pop();
  const officialIri = `https://openenergyplatform.org/ontology/oeo/${shortForm}`;
  const encoded = encodeURIComponent(officialIri);
  const baseUrl =
    import.meta.env.VITE_TSS_API_BASE?.replace(/\/$/, "") ||
    "https://api.terminology.tib.eu/api";
  const ontology = import.meta.env.VITE_TSS_DEFAULT_ONTOLOGY || "oeo";

  const tryEndpoint = async (endpoint) => {
    try {
      const res = await axios.get(
        `${baseUrl}/ontologies/${ontology}/${endpoint}?iri=${encoded}`
      );
      const items = res.data?._embedded?.[endpoint];
      if (items && items.length > 0) {
        const item = items[0];
        return {
          iri,
          label: item.label || shortForm,
          description:
            item.description && item.description.length > 0
              ? item.description.join(" ")
              : "No official definition provided in the ontology.",
          type: endpoint,
        };
      }
    } catch (e) {
      /* fall through */
    }
    return null;
  };

  let info =
    (await tryEndpoint("terms")) ||
    (await tryEndpoint("individuals")) ||
    (await tryEndpoint("properties"));
  if (!info) {
    info = {
      iri,
      label: shortForm,
      description: "Term not found in Terminology Service.",
      type: "unknown",
    };
  }
  cache[iri] = info;
  return info;
}

// Resolve many IRIs; returns a map { iri: info }.
export async function resolveTerms(iris) {
  const out = {};
  await Promise.all(
    [...new Set(iris.filter(Boolean))].map(async (iri) => {
      out[iri] = await resolveTerm(iri);
    })
  );
  return out;
}