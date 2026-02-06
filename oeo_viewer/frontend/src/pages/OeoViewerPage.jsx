// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useMemo, useState } from "react";
import {
  EuiPageTemplate,
  EuiPanel,
  EuiResizableContainer,
  EuiSpacer,
  EuiText,
  useEuiTheme,
  useCurrentEuiBreakpoint,
  useGeneratedHtmlId,
  EuiButtonEmpty,
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

function AccordionShim({ id, title, initialIsOpen = false, isOpen, onToggle, children }) {
  const [uncontrolledOpen, setUncontrolledOpen] = useState(initialIsOpen);
  const controlled = typeof isOpen === "boolean";
  const open = controlled ? isOpen : uncontrolledOpen;

  const setOpen = (next) => {
    if (!controlled) setUncontrolledOpen(next);
    onToggle?.(next);
  };

  return (
    <EuiPanel color="transparent" hasShadow={false} paddingSize="s" style={{ paddingInline: 0 }}>
      <EuiButtonEmpty
        onClick={() => setOpen(!open)}
        aria-controls={id}
        aria-expanded={open}
        flush="left"
        iconType={open ? "arrowDown" : "arrowRight"}
        iconSide="left"
      >
        {title}
      </EuiButtonEmpty>
      <div id={id} hidden={!open} style={{ marginTop: 8 }}>
        {children}
      </div>
    </EuiPanel>
  );
}

export default function OeoViewerPage() {
  const { euiTheme } = useEuiTheme();
  const bp = useCurrentEuiBreakpoint();
  const isMobile = bp === "xs" || bp === "s";

  const [autoSelection, setAutoSelection] = useState(null);
  const [selectedIri, setSelectedIri] = useState("");
  const [pathOpen, setPathOpen] = useState(false);

  const mobileInfoId = useGeneratedHtmlId({ prefix: "oeoInfoMobile" });
  const mobileHierarchyId = useGeneratedHtmlId({ prefix: "oeoHierarchyMobile" });
  const mobilePathId = useGeneratedHtmlId({ prefix: "oeoPathMobile" });
  const desktopInfoId = useGeneratedHtmlId({ prefix: "oeoInfoDesktop" });
  const desktopPathId = useGeneratedHtmlId({ prefix: "oeoPathDesktop" });

  const handleAutocompleteChange = (sel) => {
    setAutoSelection(sel);
    const iri = getIriFromSelection(sel);
    setSelectedIri(iri);
    if (iri) setPathOpen(true);
  };

  const handleHierarchyClick = (...args) => {
    let iri = "";
    if (args.length >= 3) iri = args[2]?.iri || args[2]?.entity?.iri || "";
    else if (args.length === 1) {
      const a = args[0];
      iri = typeof a === "string" ? a : a?.entity?.iri || a?.iri || "";
    }
    if (!iri) return;
    setSelectedIri(iri);
  };

  const handleNavigateToOntology = (...args) => {
    let target = "";
    if (args.length >= 3) target = args[2]?.iri || args[2]?.entity?.iri || "";
    else if (args.length === 1) {
      const a = args[0];
      target = typeof a === "string" ? a : a?.entity?.iri || a?.iri || "";
    }
    try {
      const u = new URL(target);
      if (u.protocol === "http:" || u.protocol === "https:") {
        window.open(target, "_blank", "noopener,noreferrer");
      }
    } catch { }
  };

  const fullHierarchy = (
    <TssHierarchy
      iri=""
      keepExpansionStates={true}
      onNavigateToEntity={handleHierarchyClick}
      onNavigateToOntology={handleNavigateToOntology}
    />
  );

  const pathHierarchy =
    selectedIri ? (
      <TssHierarchy
        iri={selectedIri}
        showSiblingsOnInit={true}
        onNavigateToEntity={handleHierarchyClick}
        onNavigateToOntology={handleNavigateToOntology}
      />
    ) : null;

  return (
    <EuiPageTemplate paddingSize="m" grow={false} restrictWidth={1400}>
      <EuiPageTemplate.Section grow={false}>
        <HowToUseViewer />
        <EuiSpacer size="m" />

        {isMobile ? (
          <EuiPanel hasShadow={false} color="transparent" paddingSize="s">
            <AccordionShim id={mobileHierarchyId} title="Full hierarchy" initialIsOpen={true}>
              <div style={{ padding: euiTheme.size.s }}>{fullHierarchy}</div>
            </AccordionShim>

            <EuiSpacer size="m" />

            <AccordionShim id={mobilePathId} title="Path to selected entity" isOpen={pathOpen} onToggle={setPathOpen}>
              <div style={{ padding: euiTheme.size.s }}>{pathHierarchy}</div>
            </AccordionShim>

            <EuiSpacer size="m" />

            <AccordionShim id={mobileInfoId} title="Open Energy Ontology — Info" initialIsOpen={false}>
              <TssOeoInfo />
            </AccordionShim>

            <EuiSpacer size="m" />

            <TssAutocomplete onChange={handleAutocompleteChange} />

            <EuiSpacer size="m" />

            <EuiPanel paddingSize="m">
              <EuiText>
                <h3 style={{ marginTop: 0 }}>Metadata</h3>
              </EuiText>

              {selectedIri ? (
                <TssMetadata iri={selectedIri} tabs={{ crossRef: false, termDepiction: false, terminologyInfo: false }} />
              ) : (
                <EuiText size="s" color="subdued" aria-live="polite">
                  <p>Use the autocomplete search to display the metadata here.</p>
                </EuiText>
              )}
            </EuiPanel>
          </EuiPanel>
        ) : (
          <EuiResizableContainer style={{ minHeight: 520 }}>
            {(EuiResizablePanel) => (
              <>
                <EuiResizablePanel initialSize={30} minSize="22%" tabIndex={0} paddingSize="none">
                  <div style={{ position: "sticky", top: 16, maxHeight: "calc(100vh - 160px)", overflow: "auto" }}>
                    <EuiPanel hasShadow={false} color="subdued" paddingSize="s">
                      <EuiText size="s">
                        <h3 style={{ marginTop: 0 }}>Full hierarchy</h3>
                      </EuiText>

                      {fullHierarchy}

                      <EuiSpacer size="m" />

                      <AccordionShim id={desktopPathId} title="Path to selected entity" isOpen={pathOpen} onToggle={setPathOpen}>
                        {pathHierarchy}
                      </AccordionShim>
                    </EuiPanel>
                  </div>
                </EuiResizablePanel>

                <EuiResizablePanel initialSize={70} minSize="40%" paddingSize="none">
                  <EuiPanel hasBorder={false} hasShadow={false} paddingSize="m" style={{ position: "relative", zIndex: 1 }}>
                    <AccordionShim id={desktopInfoId} title="Open Energy Ontology — Info" initialIsOpen={false}>
                      <TssOeoInfo />
                    </AccordionShim>

                    <EuiSpacer size="m" />

                    <TssAutocomplete onChange={handleAutocompleteChange} />

                    <EuiSpacer size="m" />

                    <EuiPanel paddingSize="m">
                      <EuiText>
                        <h3 style={{ marginTop: 0 }}>Metadata</h3>
                      </EuiText>

                      {selectedIri ? (
                        <TssMetadata iri={selectedIri} tabs={{ crossRef: false, termDepiction: false, terminologyInfo: false }} />
                      ) : (
                        <EuiText size="s" color="subdued" aria-live="polite">
                          <p>Use the autocomplete search to display the metadata here.</p>
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
