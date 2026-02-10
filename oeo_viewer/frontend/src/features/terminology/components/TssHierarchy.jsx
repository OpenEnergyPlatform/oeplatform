// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later


import React, { useMemo } from "react";
import { HierarchyWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

/**
 * Props you can still override at call-site:
 * - iri
 * - ontologyId (defaults to config.ontology)
 * - apiUrl (defaults to config.apiBase)
 * - backendType ('ols' | ...)
 * - entityType ('class' | 'term'), defaults to 'class'
 * - parameter (extra query params)
 * - apiKey
 * - onNavigateToEntity / onNavigateToOntology
 */
export default function TssHierarchy({
  iri,
  ontologyId,
  apiUrl,
  backendType = "ols",
  entityType = "class",
  parameter = "",
  apiKey = "",
  onNavigateToEntity,
  onNavigateToOntology,
}) {
  const { apiBase, ontology, lang } = useTssConfig();

  // Resolve from config (no casing changes)
  const resolvedApiUrl = apiUrl ?? apiBase;
  const resolvedOntologyId = ontologyId ?? ontology ?? "OEO";

  // Merge extra params (+ lang)
  const mergedParameter = useMemo(() => {
    const parts = [];
    if (parameter) parts.push(parameter.replace(/^&+/, ""));
    if (lang) parts.push(`lang=${encodeURIComponent(lang)}`);
    return parts.join("&");
  }, [parameter, lang]);

  // Only include callbacks if actually provided
  const callbackProps = {
    ...(onNavigateToEntity ? { onNavigateToEntity } : {}),
    ...(onNavigateToOntology ? { onNavigateToOntology } : {}),
  };

  return (
    <HierarchyWidget
      apiKey={apiKey}
      apiUrl={resolvedApiUrl}
      backendType={backendType}
      entityType={entityType}
      iri={iri || ""}              // empty string = none selected
      ontologyId={resolvedOntologyId}
      parameter={mergedParameter}
      {...callbackProps}
    />
  );
}
