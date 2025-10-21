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
import EntityFlyout from "../features/terminology/components/EntityFlyout";
import HowToUseViewer from "../features/terminology/components/HowToUseViewer";

function getIriFromSelection(sel) {
  if (!sel) return "";
  const item = Array.isArray(sel) ? sel[0] : sel;
  return item?.iri || "";
}

/** Lightweight accordion replacement */
function AccordionShim({ id, title, initialIsOpen = false, children }) {
  const [open, setOpen] = useState(initialIsOpen);
  return (
    <EuiPanel color="transparent" hasShadow={false} paddingSize="s" style={{ paddingInline: 0 }}>
      <EuiButtonEmpty
        onClick={() => setOpen((o) => !o)}
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

  // Autocomplete -> Metadata only
  const [autoSelection, setAutoSelection] = useState(null);
  const metaIri = useMemo(() => getIriFromSelection(autoSelection), [autoSelection]);

  // Flyout (driven only by hierarchy clicks)
  const [flyoutIri, setFlyoutIri] = useState("");
  const [flyoutOpen, setFlyoutOpen] = useState(false);

  // IDs for accordions
  const mobileInfoId = useGeneratedHtmlId({ prefix: "oeoInfoMobile" });
  const mobileHierarchyId = useGeneratedHtmlId({ prefix: "oeoHierarchyMobile" });
  const desktopInfoId = useGeneratedHtmlId({ prefix: "oeoInfoDesktop" });

  // Hierarchy click → ONLY open flyout
  const handleHierarchyClick = (...args) => {
    let iri = "";
    if (args.length >= 3) iri = args[2]?.iri || args[2]?.entity?.iri || "";
    else if (args.length === 1) {
      const a = args[0];
      iri = typeof a === "string" ? a : a?.entity?.iri || a?.iri || "";
    }
    if (!iri) {
      // eslint-disable-next-line no-console
      console.warn("onNavigateToEntity: unexpected payload", args);
      return;
    }
    setFlyoutIri(iri);
    setFlyoutOpen(true);
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

  return (
    <EuiPageTemplate paddingSize="m" grow={false} restrictWidth={1400}>
      <EuiPageTemplate.Section grow={false}>
        {/* 🔹 Top-of-page info banner (collapsed by default) */}
        <HowToUseViewer />
        <EuiSpacer size="m" />
        {isMobile ? (
          <>
            {/* --- Mobile layout --- */}
            <EuiPanel hasShadow={false} color="transparent" paddingSize="s">
              <AccordionShim id={mobileHierarchyId} title="Full hierarchy" initialIsOpen={true}>
                <div style={{ padding: euiTheme.size.s }}>
                  <TssHierarchy
                    onNavigateToEntity={handleHierarchyClick}
                    onNavigateToOntology={handleNavigateToOntology}
                  />
                </div>
              </AccordionShim>

              <EuiSpacer size="m" />

              <AccordionShim id={mobileInfoId} title="Open Energy Ontology — Info" initialIsOpen={false}>
                <TssOeoInfo />
              </AccordionShim>

              <EuiSpacer size="m" />

              {/* Autocomplete updates ONLY the metadata below */}
              <TssAutocomplete onChange={setAutoSelection} />

              <EuiSpacer size="m" />
              <EuiPanel paddingSize="m">
                <EuiText>
                  <h3 style={{ marginTop: 0 }}>Metadata</h3>
                </EuiText>

                {/* Placeholder when no IRI yet */}
                {metaIri ? (
                  <TssMetadata iri={metaIri} tabs={{ crossRef: false, termDepiction: false, terminologyInfo: false }} />
                ) : (
                  <EuiText size="s" color="subdued" aria-live="polite">
                    <p>Use the autocomplete search to display the metadata here.</p>
                  </EuiText>
                )}
              </EuiPanel>
            </EuiPanel>
          </>
        ) : (
          // --- Desktop layout ---
          <EuiResizableContainer style={{ minHeight: 520 }}>
            {(EuiResizablePanel) => (
              <>
                {/* Left: hierarchy */}
                <EuiResizablePanel initialSize={30} minSize="22%" tabIndex={0} paddingSize="none">
                  <div style={{ position: "sticky", top: 16, maxHeight: "calc(100vh - 160px)", overflow: "auto" }}>
                    <EuiPanel hasShadow={false} color="subdued" paddingSize="s">
                      <EuiText size="s">
                        <h3 style={{ marginTop: 0 }}>Full hierarchy</h3>
                      </EuiText>
                      <TssHierarchy
                        onNavigateToEntity={handleHierarchyClick}
                        onNavigateToOntology={handleNavigateToOntology}
                      />
                    </EuiPanel>
                  </div>
                </EuiResizablePanel>

                {/* Right: content (autocomplete + metadata) */}
                <EuiResizablePanel initialSize={70} minSize="40%" paddingSize="none">
                  <EuiPanel hasBorder={false} hasShadow={false} paddingSize="m" style={{ position: "relative", zIndex: 1 }}>
                    <AccordionShim id={desktopInfoId} title="Open Energy Ontology — Info" initialIsOpen={false}>
                      <TssOeoInfo />
                    </AccordionShim>

                    <EuiSpacer size="m" />
                    <TssAutocomplete onChange={setAutoSelection} />

                    <EuiSpacer size="m" />
                    <EuiPanel paddingSize="m">
                      <EuiText>
                        <h3 style={{ marginTop: 0 }}>Metadata</h3>
                      </EuiText>

                      {/* Placeholder when no IRI yet */}
                      {metaIri ? (
                        <TssMetadata iri={metaIri} tabs={{ crossRef: false, termDepiction: false, terminologyInfo: false }} />
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

      {/* Flyout (opened ONLY by hierarchy clicks) */}
      <EntityFlyout
        iri={flyoutIri}
        isOpen={flyoutOpen}
        onClose={() => setFlyoutOpen(false)}
        title="Selected element"
      />
    </EuiPageTemplate>
  );
}
