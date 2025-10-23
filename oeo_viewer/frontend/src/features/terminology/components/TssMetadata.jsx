// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useMemo } from "react";
import { MetadataWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssMetadata({
  iri,
  api,                // optional explicit override; else comes from config.apiBase
  ontologyId,         // optional explicit override; else comes from config.ontology
  entityType = "class",
  parameter = "",
  useLegacy = true,

  // Optional compact tab overrides: { altNames?, crossRef?, graphView?, hierarchy?, termDepiction?, terminologyInfo? }
  tabs,

  // Optional handlers: only pass them if you actually provide them
  onNavigateToDisambiguate,
  onNavigateToEntity,
  onNavigateToOntology,
}) {
  const { apiBase, ontology, lang } = useTssConfig();

  // Resolve from config (no forced lowercasing to avoid OEO/oeo mismatch)
  const resolvedApi = api ?? apiBase;
  const resolvedOntologyId = ontologyId ?? ontology ?? "OEO";

  // Append lang to any extra parameters
  const mergedParameter = useMemo(() => {
    const parts = [];
    if (parameter) parts.push(parameter.replace(/^&+/, ""));
    if (lang) parts.push(`lang=${encodeURIComponent(lang)}`);
    return parts.join("&");
  }, [parameter, lang]);

  if (!iri) return null;

  // Default all tabs to true; apply overrides from `tabs` if provided
  const finalTabs = {
    altNamesTab: true,
    crossRefTab: true,
    graphViewTab: true,
    hierarchyTab: true,
    termDepictionTab: true,
    terminologyInfoTab: true,
    ...(tabs
      ? {
        altNamesTab: tabs.altNames ?? true,
        crossRefTab: tabs.crossRef ?? true,
        graphViewTab: tabs.graphView ?? true,
        hierarchyTab: tabs.hierarchy ?? true,
        termDepictionTab: tabs.termDepiction ?? true,
        terminologyInfoTab: tabs.terminologyInfo ?? true,
      }
      : null),
  };

  // Only include callbacks if they were provided (prevents unknown-prop warnings)
  const callbackProps = {
    ...(onNavigateToDisambiguate ? { onNavigateToDisambiguate } : {}),
    ...(onNavigateToEntity ? { onNavigateToEntity } : {}),
    ...(onNavigateToOntology ? { onNavigateToOntology } : {}),
  };

  return (
    <MetadataWidget
      api={resolvedApi}
      ontologyId={resolvedOntologyId}
      entityType={entityType}
      iri={iri}
      parameter={mergedParameter}
      useLegacy={useLegacy}
      termLink=""
      {...finalTabs}
      {...callbackProps}
    />
  );
}
