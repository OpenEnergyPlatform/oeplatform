// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useMemo } from "react";
import { HierarchyWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssHierarchy({
  iri, // This is the currently selected entity we want to highlight
  ontologyId,
  apiUrl,
  backendType = "ols",
  entityType = "class",
  parameter = "",
  apiKey = "",
  keepExpansionStates,
  showSiblingsOnInit,
  useLegacy,
  includeObsoleteEntities,
  wrap,
  onNavigateToEntity,
  onNavigateToOntology,
}) {
  const { apiBase, ontology, lang } = useTssConfig();

  const resolvedApiUrl = apiUrl ?? apiBase;
  const resolvedOntologyId = ontologyId ?? ontology ?? "OEO";

  const mergedParameter = useMemo(() => {
    const parts = [];
    if (parameter) parts.push(parameter.replace(/^&+/, ""));
    if (lang) parts.push(`lang=${encodeURIComponent(lang)}`);
    return parts.join("&");
  }, [parameter, lang]);

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

      // 1. Force 'iri' to be empty so the widget ALWAYS loads the full ontology from the top
      iri=""

      // 2. Pass your selected term into 'targetIri' to expand and highlight it in the tree
      targetIri={iri || ""}

      ontologyId={resolvedOntologyId}
      parameter={mergedParameter}
      keepExpansionStates={keepExpansionStates}
      showSiblingsOnInit={showSiblingsOnInit}
      useLegacy={useLegacy}
      includeObsoleteEntities={includeObsoleteEntities}
      wrap={wrap}
      {...callbackProps}
    />
  );
}
