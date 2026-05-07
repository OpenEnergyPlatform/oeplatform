// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useState, useEffect } from "react";
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
  EuiButtonIcon,
  EuiToolTip,
  copyToClipboard,
  EuiFlexGroup,
  EuiFlexItem,
  EuiGlobalToastList,
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
  const bp = useCurrentEuiBreakpoint();
  const isMobile = bp === "xs" || bp === "s";

  // Single source of truth for the selected entity
  const [selectedEntity, setSelectedEntity] = useState({ iri: "", type: "class" });

  // State for Toast Notifications
  const [toasts, setToasts] = useState([]);

  const mobileInfoId = useGeneratedHtmlId({ prefix: "oeoInfoMobile" });
  const mobileHierarchyId = useGeneratedHtmlId({ prefix: "oeoHierarchyMobile" });
  const desktopInfoId = useGeneratedHtmlId({ prefix: "oeoInfoDesktop" });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const iriFromUrl = params.get("iri");
    const typeFromUrl = params.get("type");

    if (iriFromUrl) {
      const decodedIri = decodeURIComponent(iriFromUrl);
      const decodedType = typeFromUrl ? decodeURIComponent(typeFromUrl) : "class";

      // 1. Update React state immediately
      setSelectedEntity({
        iri: decodedIri,
        type: decodedType,
      });

      // 2. Clear URL parameters after delay to ensure widgets initialize
      setTimeout(() => {
        const url = new URL(window.location);
        url.searchParams.delete("iri");
        url.searchParams.delete("type");
        window.history.replaceState({}, document.title, url.pathname);
      }, 500);
    }
  }, []);

  // --- Helper: Toast Logic ---
  const addToast = (title, contentNode) => {
    const toast = {
      title: title,
      text: contentNode,
      color: "success",
      iconType: "check",
      id: Math.random().toString(),
    };
    setToasts((toasts) => toasts.concat(toast));
  };

  const removeToast = (removedToast) => {
    setToasts((toasts) => toasts.filter((toast) => toast.id !== removedToast.id));
  };

  // --- Helper: Construct OEP Display IRI ---
  const getDisplayIri = (rawIri) => {
    if (!rawIri) return "";
    // Extract short_form (e.g., from http://.../OEO_000123 -> OEO_000123)
    const parts = rawIri.split("/");
    const shortForm = parts[parts.length - 1];
    // Return the stable OEP URL
    return `https://openenergyplatform.org/ontology/oeo/${shortForm}`;
  };

  // --- Handlers ---

  const shareCurrentView = () => {
    if (!selectedEntity.iri) return;

    const url = new URL(window.location.origin + window.location.pathname);
    url.searchParams.set("iri", selectedEntity.iri);
    url.searchParams.set("type", selectedEntity.type);

    if (copyToClipboard(url.toString())) {
      addToast(
        "View link copied",
        <p>A link to this specific view configuration has been copied to your clipboard.</p>
      );
    }
  };

  const copyTermIri = () => {
    if (!selectedEntity.iri) return;

    const displayIri = getDisplayIri(selectedEntity.iri);

    if (copyToClipboard(displayIri)) {
      addToast(
        "Term IRI copied",
        <>
          <p>The stable identifier for this term has been copied:</p>
          <div style={{ marginTop: 4, fontFamily: 'monospace', background: '#f5f7fa', padding: 4 }}>
            {displayIri}
          </div>
        </>
      );
    }
  };

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
      type = args[1] || "class";
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
    }
  };

  const hierarchyComponent = (
    <TssHierarchy
      iri={selectedEntity.iri}
      keepExpansionStates={true}
      onNavigateToEntity={handleHierarchyClick}
      onNavigateToOntology={handleNavigateToOntology}
      showSiblingsOnInit={true}
    />
  );

  return (
    <EuiPageTemplate paddingSize="m" grow={false} restrictWidth={false}>
      {/* Global Toast Container */}
      <EuiGlobalToastList
        toasts={toasts}
        dismissToast={removeToast}
        toastLifeTimeMs={6000}
      />

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

            {/* Search + Buttons (Mobile) */}
            <EuiFlexGroup alignItems="center" gutterSize="s">
              <EuiFlexItem>
                <TssAutocomplete onChange={handleAutocompleteChange} />
              </EuiFlexItem>
              <EuiFlexItem grow={false}>
                <EuiButtonIcon
                  display="base"
                  iconType="link"
                  aria-label="Copy Term IRI"
                  onClick={copyTermIri}
                  isDisabled={!selectedEntity.iri}
                />
              </EuiFlexItem>
              <EuiFlexItem grow={false}>
                <EuiButtonIcon
                  display="base"
                  iconType="share"
                  aria-label="Share current view"
                  onClick={shareCurrentView}
                  isDisabled={!selectedEntity.iri}
                />
              </EuiFlexItem>
            </EuiFlexGroup>

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
                <EuiResizablePanel initialSize={35} minSize="25%" paddingSize="none">
                  <div style={{ position: "sticky", top: 16, maxHeight: "calc(100vh - 160px)", overflow: "auto" }}>
                    <EuiPanel hasShadow={false} color="subdued" paddingSize="s">
                      <EuiText size="s">
                        <h3 style={{ marginTop: 0 }}>Ontology Hierarchy</h3>
                      </EuiText>
                      <EuiSpacer size="m" />
                      {hierarchyComponent}
                    </EuiPanel>
                  </div>
                </EuiResizablePanel>

                <EuiResizablePanel initialSize={65} minSize="40%" paddingSize="none">
                  <EuiPanel hasBorder={false} hasShadow={false} paddingSize="m">
                    <AccordionShim id={desktopInfoId} title="About Open Energy Ontology" initialIsOpen={false}>
                      <TssOeoInfo />
                    </AccordionShim>

                    <EuiSpacer size="l" />

                    {/* Search + Buttons (Desktop) */}
                    <EuiFlexGroup alignItems="center" gutterSize="s">
                      <EuiFlexItem>
                        <TssAutocomplete onChange={handleAutocompleteChange} />
                      </EuiFlexItem>

                      {/* Button 1: Copy Term IRI */}
                      <EuiFlexItem grow={false}>
                        <EuiToolTip content="Copy Term IRI (Permalink)">
                          <EuiButtonIcon
                            display="base"
                            iconType="link"
                            size="m"
                            aria-label="Copy Term IRI"
                            onClick={copyTermIri}
                            isDisabled={!selectedEntity.iri}
                          />
                        </EuiToolTip>
                      </EuiFlexItem>

                      {/* Button 2: Share View */}
                      <EuiFlexItem grow={false}>
                        <EuiToolTip content="Share link to this view">
                          <EuiButtonIcon
                            display="base"
                            iconType="share"
                            size="m"
                            aria-label="Share view"
                            onClick={shareCurrentView}
                            isDisabled={!selectedEntity.iri}
                          />
                        </EuiToolTip>
                      </EuiFlexItem>
                    </EuiFlexGroup>

                    <EuiSpacer size="l" />

                    <EuiPanel paddingSize="m">
                      <EuiText>
                        <div style={{ marginTop: 0 }}>Entity Metadata</div>
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
