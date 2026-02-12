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
  useCurrentEuiBreakpoint, // <--- Re-added for responsiveness
  useEuiTheme,             // <--- Re-added for spacing
} from "@elastic/eui";

import TssAutocomplete from "../features/terminology/components/TssAutocomplete";
import TssMetadata from "../features/terminology/components/TssMetadata";
import TssOeoInfo from "../features/terminology/components/TssOeoInfo";
import TssHierarchy from "../features/terminology/components/TssHierarchy";
import HowToUseViewer from "../features/terminology/components/HowToUseViewer";

function getIriFromSelection(sel) {
  if (!sel) return "";
  const item = Array.isArray(sel) ? sel[0] : sel;
  return item?.iri || "";
}

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

  // 1. Detect Screen Size
  const bp = useCurrentEuiBreakpoint();
  const isMobile = bp === "xs" || bp === "s";

  const [selectedIri, setSelectedIri] = useState("");

  const mobileInfoId = useGeneratedHtmlId({ prefix: "oeoInfoMobile" });
  const mobileHierarchyId = useGeneratedHtmlId({ prefix: "oeoHierarchyMobile" });
  const desktopInfoId = useGeneratedHtmlId({ prefix: "oeoInfoDesktop" });

  const handleAutocompleteChange = (sel) => {
    const iri = getIriFromSelection(sel);
    setSelectedIri(iri);
  };

  const handleHierarchyClick = (...args) => {
    let iri = "";
    if (args.length >= 3) iri = args[2]?.iri || args[2]?.entity?.iri || "";
    else if (args.length === 1) {
      const a = args[0];
      iri = typeof a === "string" ? a : a?.entity?.iri || a?.iri || "";
    }
    if (iri) setSelectedIri(iri);
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

  // Reusable Hierarchy Component to ensure consistent props between Desktop/Mobile
  const hierarchyComponent = (
    <TssHierarchy
      iri="" // Keep full tree visible
      keepExpansionStates={true}
      onNavigateToEntity={handleHierarchyClick}
      onNavigateToOntology={handleNavigateToOntology}
    />
  );

  return (
    <EuiPageTemplate paddingSize="m" grow={false} restrictWidth={1400}>
      <EuiPageTemplate.Section grow={false}>
        <HowToUseViewer />
        <EuiSpacer size="m" />

        {isMobile ? (
          /* --- MOBILE LAYOUT (Stacked Accordions) --- */
          <EuiPanel hasShadow={false} color="transparent" paddingSize="s">

            {/* 1. Hierarchy in Accordion */}
            <AccordionShim id={mobileHierarchyId} title="Full hierarchy" initialIsOpen={false}>
              <div style={{ padding: euiTheme.size.s }}>
                {hierarchyComponent}
              </div>
            </AccordionShim>

            <EuiSpacer size="m" />

            {/* 2. Info in Accordion */}
            <AccordionShim id={mobileInfoId} title="About Open Energy Ontology" initialIsOpen={false}>
              <TssOeoInfo />
            </AccordionShim>

            <EuiSpacer size="m" />

            {/* 3. Search */}
            <TssAutocomplete onChange={handleAutocompleteChange} />

            <EuiSpacer size="m" />

            {/* 4. Metadata Panel */}
            <EuiPanel paddingSize="m">
              <EuiText>
                <h3 style={{ marginTop: 0 }}>Entity Metadata</h3>
              </EuiText>

              {selectedIri ? (
                <TssMetadata
                  iri={selectedIri}
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
          /* --- DESKTOP LAYOUT (Split View) --- */
          <EuiResizableContainer style={{ minHeight: 600 }}>
            {(EuiResizablePanel) => (
              <>
                {/* LEFT COLUMN: Fixed Full Hierarchy */}
                <EuiResizablePanel initialSize={30} minSize="25%" paddingSize="none">
                  <div style={{ position: "sticky", top: 16, maxHeight: "calc(100vh - 160px)", overflow: "auto" }}>
                    <EuiPanel hasShadow={false} color="subdued" paddingSize="s">
                      <EuiText size="s">
                        <h3 style={{ marginTop: 0 }}>Ontology Hierarchy</h3>
                      </EuiText>
                      {hierarchyComponent}
                    </EuiPanel>
                  </div>
                </EuiResizablePanel>

                {/* RIGHT COLUMN: Search and Details */}
                <EuiResizablePanel initialSize={70} minSize="40%" paddingSize="none">
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

                      {selectedIri ? (
                        <TssMetadata
                          iri={selectedIri}
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
