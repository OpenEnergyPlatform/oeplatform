// ontology/frontend/src/pages/OeoIriPages.jsx
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  EuiPageTemplate,
  EuiPanel,
  EuiSpacer,
  EuiTitle,
  EuiTabs,
  EuiTab,
  EuiFlexGroup,
  EuiFlexItem,
  EuiCallOut,
  EuiButton,
} from "@elastic/eui";

import TssEntityInfo from "../features/terminology/components/TssEntityInfo";
import TssEntityRelations from "../features/terminology/components/TssEntityRelations";
import TssIriWidget from "../features/terminology/components/TssIriWidget";
import TssEntityNavButtons from "../features/terminology/components/TssEntityNavButtons";
import TssDescription from "../features/terminology/components/TssDescription";

function resolveIri(ontology, shortForm) {
  if (!shortForm) return "";

  const oboPrefixes = ["UO", "BFO", "RO", "IAO", "PATO", "ENVO", "CHEBI", "NCBITaxon"];
  const prefix = shortForm.split("_")[0];

  if (oboPrefixes.includes(prefix)) {
    return `http://purl.obolibrary.org/obo/${shortForm}`;
  }

  return `https://openenergyplatform.org/ontology/${ontology}/${shortForm}`;
}

export default function OeoIriPages() {
  const { ontology, short_form } = useParams();
  const navigate = useNavigate();

  // The actual IRI used for fetching and external tools
  const fetchIri = resolveIri(ontology, short_form);
  // The IRI displayed in the UI
  const displayIri = `https://openenergyplatform.org/ontology/${ontology}/${short_form}`;

  const [entityType, setEntityType] = useState("class");

  const tabs = [
    { id: 'class', name: 'Class' },
    { id: 'property', name: 'Property' },
    { id: 'individual', name: 'Individual' },
  ];

  // Robust handler adapting your Viewer logic for React Router navigation
  const handleNavigateToEntity = (...args) => {
    let iri = "";
    let type = "class";

    // 1. Extract IRI and Type exactly like in the Viewer
    if (args.length >= 3) {
      iri = args[2]?.iri || args[2]?.entity?.iri || "";
      type = args[1] || "class";
    } else if (args.length === 1) {
      const a = args[0];
      iri = typeof a === "string" ? a : a?.entity?.iri || a?.iri || "";
      type = a?.type || "class";

      // Edge case: if it's an object from the Search or Info widget with short_form
      if (!iri && typeof a === "object") {
        let extractedShortForm = Array.isArray(a.short_form) ? a.short_form[0] : a.short_form;
        if (!extractedShortForm && a.obo_id) {
          let oboId = Array.isArray(a.obo_id) ? a.obo_id[0] : a.obo_id;
          extractedShortForm = oboId.replace(":", "_");
        }
        if (extractedShortForm) {
          setEntityType(type);
          navigate(`/${ontology || "oeo"}/${extractedShortForm}`);
          window.scrollTo(0, 0);
          return;
        }
      }
    }

    // 2. We have the IRI, now parse the short_form to navigate
    if (iri) {
      const separator = iri.includes("#") ? "#" : "/";
      const parts = iri.split(separator).filter(Boolean);
      const shortForm = parts[parts.length - 1];

      if (shortForm) {
        setEntityType(type); // Automatically switch the tab (Class/Property/Individual)
        navigate(`/${ontology || "oeo"}/${shortForm}`);
        window.scrollTo(0, 0);
      }
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

  return (
    <EuiPageTemplate paddingSize="m">
      <EuiPageTemplate.Section>
        <EuiSpacer size="m" />

        <EuiFlexGroup alignItems="center" justifyContent="spaceBetween">
          <EuiFlexItem grow={false}>
            {/* Quick Navigation Buttons (Parent/Child) */}
            <TssEntityNavButtons
              iri={fetchIri}
              ontologyId={ontology}
              onNavigate={handleNavigateToEntity}
            />
          </EuiFlexItem>

          <EuiFlexItem grow={false}>
            <EuiButton
              href={`/viewer/oeo/?iri=${encodeURIComponent(fetchIri)}&type=${encodeURIComponent(entityType)}`}
              iconType="visMapCoordinate"
              size="s"
              fill
            >
              Explore this term in OEO Viewer
            </EuiButton>
          </EuiFlexItem>
        </EuiFlexGroup>

        <EuiSpacer size="l" />

        <EuiFlexGroup justifyContent="spaceBetween" alignItems="flexEnd">
          <EuiFlexItem grow={false}>
            <EuiTitle size="l">
              <h1>
                <span style={{ color: "#0071c1" }}>{short_form}</span>
              </h1>
            </EuiTitle>
            <EuiSpacer size="s" />
            <TssIriWidget iri={displayIri} />
            <EuiSpacer size="s" />
            <TssDescription
              iri={fetchIri}
              ontologyId={ontology}
            />

            <EuiSpacer size="s" />
          </EuiFlexItem>

          <EuiFlexItem grow={false} style={{ minWidth: 280 }}>
            <EuiCallOut
              title="Empty details?"
              color="primary"
              iconType="iInCircle"
              size="s"
            >
              <p style={{ fontSize: "12px", margin: 0 }}>Try selecting a different entity type below.</p>
            </EuiCallOut>
            <EuiSpacer size="s" />
            <EuiTabs size="s">
              {tabs.map((tab) => (
                <EuiTab
                  key={tab.id}
                  isSelected={entityType === tab.id}
                  onClick={() => setEntityType(tab.id)}
                >
                  {tab.name}
                </EuiTab>
              ))}
            </EuiTabs>
          </EuiFlexItem>
        </EuiFlexGroup>

        <EuiSpacer size="m" />

        <EuiPanel paddingSize="l">
          <EuiTitle size="s"><h3>Entity Information</h3></EuiTitle>
          <EuiSpacer size="s" />
          <TssEntityInfo
            iri={fetchIri}
            ontologyId={ontology}
            entityType={entityType}
            onNavigateToEntity={handleNavigateToEntity}
            onNavigateToOntology={handleNavigateToOntology}
          />

          <EuiSpacer size="xl" />

          <EuiTitle size="s"><h3>Relations & Hierarchy</h3></EuiTitle>
          <EuiSpacer size="s" />
          <TssEntityRelations
            iri={fetchIri}
            ontologyId={ontology}
            entityType={entityType === "individual" ? "individual" : "term"}
            onNavigateToEntity={handleNavigateToEntity}
            onNavigateToOntology={handleNavigateToOntology}
          />
        </EuiPanel>
      </EuiPageTemplate.Section>
    </EuiPageTemplate>
  );
}
