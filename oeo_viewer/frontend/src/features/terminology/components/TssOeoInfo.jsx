// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later


import React, { useMemo } from "react";
import { OntologyInfoWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

/**
 * Uses config:
 *  - apiBase (gateway) and olsApi (OLS) from TssConfigProvider
 *  - ontology, lang
 *
 * Props:
 *  - api: explicit URL override (beats everything)
 *  - apiSource: 'gateway' | 'ols'  (choose which config endpoint to use)
 *  - ontologyId: override ontology (defaults to config.ontology)
 *  - parameter: extra query params (lang is appended automatically)
 *  - hasTitle, showBadges, useLegacy: UI flags
 */

export default function TssOeoInfo({
  api,               // optional override; else config.apiBase
  ontologyId,        // optional override; else config.ontology
  parameter = "",
  hasTitle = true,
  showBadges = true,
  useLegacy = true,
}) {
  const { apiBase, ontology, lang } = useTssConfig();

  const resolvedApi = api ?? apiBase;
  const resolvedOntologyId = (ontologyId ?? ontology ?? "oeo").toLowerCase();

  const mergedParameter = useMemo(() => {
    const parts = [];
    if (parameter) parts.push(parameter.replace(/^&+/, ""));
    if (lang) parts.push(`lang=${encodeURIComponent(lang)}`);
    return parts.join("&");
  }, [parameter, lang]);

  return (
    <OntologyInfoWidget
      api={resolvedApi}
      ontologyId={resolvedOntologyId}
      parameter={mergedParameter}
      hasTitle={hasTitle}
      showBadges={showBadges}
      useLegacy={useLegacy}
    />
  );
}
