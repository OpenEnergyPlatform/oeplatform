
/* eslint-disable max-len */
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useMemo, useEffect, useRef, useState } from "react";
import { MetadataWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssMetadata({
  iri,
  api,
  ontologyId,
  entityType = "class",
  parameter = "",
  useLegacy = false,
  tabs,
  onNavigateToDisambiguate,
  onNavigateToEntity,
  onNavigateToOntology,
}) {
  const { apiBase, ontology, lang } = useTssConfig();

  const resolvedApi = api ?? apiBase;
  const resolvedOntologyId = ontologyId ?? ontology ?? "OEO";

  // Referenz auf den Container des MetadataWidget
  const metadataRef = useRef(null);

  // Legende standardmäßig anzeigen, da Graph View der Starttab ist
  const [isGraphViewActive, setIsGraphViewActive] = useState(true);

  const mergedParameter = useMemo(() => {
    const parts = [];

    if (parameter) {
      parts.push(parameter.replace(/^&+/, ""));
    }

    if (lang) {
      parts.push(`lang=${encodeURIComponent(lang)}`);
    }

    return parts.join("&");
  }, [parameter, lang]);

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

  const callbackProps = {
    ...(onNavigateToDisambiguate
      ? { onNavigateToDisambiguate }
      : {}),
    ...(onNavigateToEntity
      ? { onNavigateToEntity }
      : {}),
    ...(onNavigateToOntology
      ? { onNavigateToOntology }
      : {}),
  };

  // Prüfen, welcher Tab aktuell ausgewählt ist
  useEffect(() => {
    const container = metadataRef.current;

    if (!container) return;

    const checkActiveTab = () => {
      const activeTab = container.querySelector(
        '[role="tab"][aria-selected="true"]'
      );

      if (!activeTab) return;

      const tabName = activeTab.textContent
        .trim()
        .toLowerCase();

      setIsGraphViewActive(tabName.includes("graph view"));
    };

    // Initial prüfen
    checkActiveTab();

    // Auf Änderungen an den Tabs reagieren
    const observer = new MutationObserver(checkActiveTab);

    observer.observe(container, {
      attributes: true,
      attributeFilter: ["aria-selected"],
      childList: true,
      subtree: true,
    });

    return () => {
      observer.disconnect();
    };
  }, [iri]);

  if (!iri) return null;

  return (
    <div
      ref={metadataRef}
      style={{
        position: "relative",
        width: "100%",
      }}
    >
      {/* Bestehendes MetadataWidget */}
      <MetadataWidget
        api={resolvedApi}
        ontologyId={resolvedOntologyId}
        entityType={entityType}
        iri={iri}
        parameter={mergedParameter}
        termLink=""
        initialSelectedTab="graphview"
        enableComparisonMode={true}
        rootWalk={true}
        {...finalTabs}
        {...callbackProps}
      />

      {/* Legende nur bei aktivem Graph View */}
      {isGraphViewActive && (
        <div
          style={{
            position: "absolute",
            right: "20px",
            bottom: "20px",
            zIndex: 2,
            width: "190px",
            padding: "14px",
            backgroundColor: "#ffffff",
            border: "1px solid #dce5ee",
            borderRadius: "6px",
            boxShadow: "0 2px 6px rgba(0,0,0,0.06)",
            fontSize: "13px",
          }}
        >
          <h4 style={{ margin: "0 0 14px 0" }}>
            Legend
          </h4>

          <div style={{ marginBottom: "12px" }}>
            <span
              style={{
                color: "#355d8b",
                marginRight: "8px",
              }}
            >
              ■
            </span>
            Selected entity
          </div>

          <div style={{ marginBottom: "12px" }}>
            <span
              style={{
                color: "#a5d5ec",
                marginRight: "8px",
              }}
            >
              ■
            </span>
            Related entity
          </div>

          <div>
            <span style={{ marginRight: "8px" }}>
              ➜
            </span>
            is a subclass of
          </div>
        </div>
      )}
    </div>
  );
}
