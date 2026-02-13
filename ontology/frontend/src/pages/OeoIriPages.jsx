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
} from "@elastic/eui";

import TssEntityInfo from "../features/terminology/components/TssEntityInfo";
import TssEntityRelations from "../features/terminology/components/TssEntityRelations";
import TssIriWidget from "../features/terminology/components/TssIriWidget";
import TssEntityNavButtons from "../features/terminology/components/TssEntityNavButtons";

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

  const fetchIri = resolveIri(ontology, short_form);
  const displayIri = `https://openenergyplatform.org/ontology/${ontology}/${short_form}`;

  const [entityType, setEntityType] = useState("class");

  const tabs = [
    { id: 'class', name: 'Class' },
    { id: 'property', name: 'Property' },
    { id: 'individual', name: 'Individual' },
  ];

  const handleNavigateToEntity = (event) => {
    let nextId = event.short_form;

    if (!nextId && event.iri) {
      const parts = event.iri.split("/");
      nextId = parts[parts.length - 1];
    }

    if (nextId) {
      navigate(`/${ontology}/${nextId}`);
      window.scrollTo(0, 0);
    }
  };

  return (
    <EuiPageTemplate paddingSize="m">
      <EuiPageTemplate.Section>
        <EuiSpacer size="m" />

        {/* Quick Navigation Buttons */}
        <TssEntityNavButtons
          iri={fetchIri}
          ontologyId={ontology}
          onNavigate={handleNavigateToEntity}
        />

        <EuiSpacer size="m" />
        <EuiFlexGroup justifyContent="spaceBetween" alignItems="flexEnd">
          <EuiFlexItem grow={false}>
            <EuiTitle size="l">
              <h1>
                {ontology ? ontology.toUpperCase() : "Ontology"} Entity: <span style={{ color: "#0071c1" }}>{short_form}</span>
              </h1>
            </EuiTitle>
            <EuiSpacer size="s" />
            <TssIriWidget iri={displayIri} />
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
          />

          <EuiSpacer size="xl" />

          <EuiTitle size="s"><h3>Relations & Hierarchy</h3></EuiTitle>
          <EuiSpacer size="s" />
          <TssEntityRelations
            iri={fetchIri}
            ontologyId={ontology}
            entityType={entityType === "individual" ? "individual" : "term"}
            onNavigateToEntity={handleNavigateToEntity}
          />
        </EuiPanel>
      </EuiPageTemplate.Section>
    </EuiPageTemplate>
  );
}
