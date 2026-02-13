// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useState } from "react";
import {
  EuiPageTemplate,
  EuiPanel,
  EuiResizableContainer,
  EuiSpacer,
  EuiText,
  useGeneratedHtmlId,
  EuiButtonEmpty,
  useCurrentEuiBreakpoint,
  useEuiTheme,
} from "@elastic/eui";

import TssAutocomplete from "../features/terminology/components/TssAutocomplete";
import TssMetadata from "../features/terminology/components/TssMetadata";
import TssOeoInfo from "../features/terminology/components/TssOeoInfo";
import TssHierarchy from "../features/terminology/components/TssHierarchy";
import HowToUseViewer from "../features/terminology/components/HowToUseViewer";

function AccordionShim({ id, title, initialIsOpen = false, children }) {
  const [isOpen, setIsOpen] = useState(initialIsOpen);
  return (
    <EuiPanel color="transparent" hasShadow={false} paddingSize="s" style={{ paddingInline: 0 }}>
      <EuiButtonEmpty
        onClick={() => setIsOpen(!isOpen)}
        aria-controls={id}
        aria-expanded={isOpen}
        flush="left"
        iconType={isOpen ? "arrowDown" : "arrowRight"}
        iconSide="left"
      >
        {title}
      </EuiButtonEmpty>
      <div id={id} hidden={!isOpen} style={{ marginTop: 8 }}>
        {children}
      </div>
    </EuiPanel>
  );
}

export default function OeoViewerPage() {
  const { euiTheme } = useEuiTheme();

  // Detect Screen Size
  const bp = useCurrentEuiBreakpoint();
  const isMobile = bp === "xs" || bp === "s";

  // Use an object to track both IRI and Type for the Metadata widget
  const [selectedEntity, setSelectedEntity] = useState({ iri: "", type: "class" });

  const mobileInfoId = useGeneratedHtmlId({ prefix: "oeoInfoMobile" });
  const mobileHierarchyId = useGeneratedHtmlId({ prefix: "oeoHierarchyMobile" });
  const desktopInfoId = useGeneratedHtmlId({ prefix: "oeoInfoDesktop" });

  const handleAutocompleteChange = (sel) => {
    if (!sel) {
      setSelectedEntity({ iri: "", type: "class" });
      return;
    }
    const item = Array.isArray(sel) ? sel[0] : sel;
    setSelectedEntity({
      iri: item?.iri || "",
      type: item?.type || "class",
    });
  };

  const handleHierarchyClick = (...args) => {
    let iri = "";
    let type = "class";

    if (args.length >= 3) {
      iri = args[2]?.iri || args[2]?.entity?.iri || "";
      type = args[1] || "class"; // args[1] contains the entity type
    } else if (args.length === 1) {
      const a = args[0];
      iri = typeof a === "string" ? a : a?.entity?.iri || a?.iri || "";
      type = a?.type || "class";
    }

    if (iri) {
      setSelectedEntity({ iri, type });
    }
  };

  const handleNavigateToOntology = (...args) => {
    let url = "";
    if (args.length >= 3 && args[2]?.iri) {
      url = args[2].iri;
    } else if (args[0] && typeof args[0] === "object") {
      url = args[0].url || args[0].iri || args[0].ontologyIri || "";
    } else if (typeof args[0] === "string") {
      url = args[0];
    }

    if (url && (url.startsWith("http://") || url.startsWith("https://"))) {
      window.open(url, "_blank", "noopener,noreferrer");
    } else {
      console.warn("TSS: Could not extract valid IRI from navigation event", args);
    }
  };

  // Reusable Hierarchy Component
  const hierarchyComponent = (
    <TssHierarchy
      iri=""
      keepExpansionStates={true}
      onNavigateToEntity={handleHierarchyClick}
      onNavigateToOntology={handleNavigateToOntology}
    />
  );

  return (
    // Set restrictWidth to false so it uses the full available screen width
    <EuiPageTemplate paddingSize="m" grow={false} restrictWidth={false}>
      <EuiPageTemplate.Section grow={false}>
        <HowToUseViewer />
        <EuiSpacer size="m" />

        {isMobile ? (
          /* --- MOBILE LAYOUT --- */
          <EuiPanel hasShadow={false} color="transparent" paddingSize="s">

            <AccordionShim id={mobileHierarchyId} title="Full hierarchy" initialIsOpen={false}>
              <div style={{ padding: euiTheme.size.s }}>
                {hierarchyComponent}
              </div>
            </AccordionShim>

            <EuiSpacer size="m" />

            <AccordionShim id={mobileInfoId} title="About Open Energy Ontology" initialIsOpen={false}>
              <TssOeoInfo />
            </AccordionShim>

            <EuiSpacer size="m" />

            <TssAutocomplete onChange={handleAutocompleteChange} />

            <EuiSpacer size="m" />

            <EuiPanel paddingSize="m">
              <EuiText>
                <h3 style={{ marginTop: 0 }}>Entity Metadata</h3>
              </EuiText>

              {selectedEntity.iri ? (
                <TssMetadata
                  iri={selectedEntity.iri}
                  entityType={selectedEntity.type}
                  tabs={{ crossRef: false, termDepiction: false, terminologyInfo: false }}
                />
              ) : (
                <EuiText size="s" color="subdued">
                  <p>Use the autocomplete search or hierarchy to view details.</p>
                </EuiText>
              )}
            </EuiPanel>
          </EuiPanel>
        ) : (
          /* --- DESKTOP LAYOUT --- */
          <EuiResizableContainer style={{ minHeight: 600 }}>
            {(EuiResizablePanel) => (
              <>
                {/* Increased initialSize from 30 to 35 for more hierarchy width */}
                <EuiResizablePanel initialSize={35} minSize="25%" paddingSize="none">
                  <div style={{ position: "sticky", top: 16, maxHeight: "calc(100vh - 160px)", overflow: "auto" }}>
                    <EuiPanel hasShadow={false} color="subdued" paddingSize="s">
                      <EuiText size="s">
                        <h3 style={{ marginTop: 0 }}>Ontology Hierarchy</h3>
                      </EuiText>
                      {hierarchyComponent}
                    </EuiPanel>
                  </div>
                </EuiResizablePanel>

                {/* Decreased initialSize from 70 to 65 to balance the left side */}
                <EuiResizablePanel initialSize={65} minSize="40%" paddingSize="none">
                  <EuiPanel hasBorder={false} hasShadow={false} paddingSize="m">

                    <AccordionShim id={desktopInfoId} title="About Open Energy Ontology" initialIsOpen={false}>
                      <TssOeoInfo />
                    </AccordionShim>

                    <EuiSpacer size="l" />

                    <TssAutocomplete onChange={handleAutocompleteChange} />

                    <EuiSpacer size="l" />

                    <EuiPanel paddingSize="m">
                      <EuiText>
                        <h3 style={{ marginTop: 0 }}>Entity Metadata</h3>
                      </EuiText>

                      {selectedEntity.iri ? (
                        <TssMetadata
                          iri={selectedEntity.iri}
                          entityType={selectedEntity.type}
                          tabs={{ crossRef: false, termDepiction: false, terminologyInfo: false }}
                        />
                      ) : (
                        <EuiText size="s" color="subdued">
                          <p>Select a term from the hierarchy or use the search above to view details.</p>
                        </EuiText>
                      )}
                    </EuiPanel>
                  </EuiPanel>
                </EuiResizablePanel>
              </>
            )}
          </EuiResizableContainer>
        )}
      </EuiPageTemplate.Section>
    </EuiPageTemplate>
  );
}
