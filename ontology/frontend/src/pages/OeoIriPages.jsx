// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "react-query";
import {
  EuiPageTemplate, EuiPanel, EuiSpacer, EuiTitle,
  EuiFlexGroup, EuiFlexItem, EuiButton, EuiBadge, EuiLoadingSpinner, EuiText
} from "@elastic/eui";

import TssEntityInfo from "../features/terminology/components/TssEntityInfo";
import TssEntityRelations from "../features/terminology/components/TssEntityRelations";
import TssIriWidget from "../features/terminology/components/TssIriWidget";
import TssEntityNavButtons from "../features/terminology/components/TssEntityNavButtons";
import TssDescription from "../features/terminology/components/TssDescription";
import { useTssConfig } from "../features/terminology/hooks/useTssConfig";

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
  const { apiBase } = useTssConfig();

  // Redirect interceptor for "ugly" URLs from Search Widget
  useEffect(() => {
    if (!short_form) return;
    const decoded = decodeURIComponent(short_form);
    if (decoded.startsWith("http")) {
      const separator = decoded.includes("#") ? "#" : "/";
      const parts = decoded.split(separator).filter(Boolean);
      const cleanShortForm = parts[parts.length - 1];
      if (cleanShortForm) navigate(`/${ontology}/${cleanShortForm}`, { replace: true });
    }
  }, [short_form, ontology, navigate]);

  const isCleanShortForm = short_form && !decodeURIComponent(short_form).startsWith("http");
  const fetchIri = isCleanShortForm ? resolveIri(ontology, short_form) : "";
  const displayIri = isCleanShortForm ? `https://openenergyplatform.org/ontology/${ontology}/${short_form}` : "";

  // --- AUTO-DETECT ENTITY TYPE FOR THE INFO WIDGET ---
  const { data: entityType, isLoading: loadingType } = useQuery(
    ["entityType", short_form],
    async () => {
      if (!short_form) return "class"; // fallback

      // We query the search index specifically for this exact short_form
      const res = await fetch(`${apiBase}search?q=${short_form}&ontology=${ontology || "oeo"}&exact=true`);
      if (!res.ok) return "class";

      const data = await res.json();
      const docs = data.response?.docs || [];

      // Find the exact match
      const match = docs.find(d => {
        const sf = Array.isArray(d.short_form) ? d.short_form[0] : d.short_form;
        return sf === short_form;
      });

      if (match && match.type) {
        const types = Array.isArray(match.type) ? match.type : [match.type];

        // The backend returns various property types (objectproperty, dataproperty, etc.)
        if (types.includes("individual")) return "individual";
        if (types.some(t => t.includes("property"))) return "property";
      }
      return "class"; // Default fallback (which the TSS library often calls "term")
    },
    { enabled: !!short_form }
  );

  // Unified Handler for clicks inside the widgets
  const handleNavigateToEntity = (...args) => {
    let iri = "";
    if (args.length >= 3) {
      iri = args[2]?.iri || args[2]?.entity?.iri || "";
    } else if (args.length === 1) {
      const a = args[0];
      iri = typeof a === "string" ? a : a?.entity?.iri || a?.iri || "";
      if (!iri && typeof a === "object") {
        let extractedShortForm = Array.isArray(a.short_form) ? a.short_form[0] : a.short_form;
        if (!extractedShortForm && a.obo_id) {
          let oboId = Array.isArray(a.obo_id) ? a.obo_id[0] : a.obo_id;
          extractedShortForm = oboId.replace(":", "_");
        }
        if (extractedShortForm) {
          navigate(`/${ontology || "oeo"}/${extractedShortForm}`);
          window.scrollTo(0, 0);
          return;
        }
      }
    }
    if (iri) {
      const separator = iri.includes("#") ? "#" : "/";
      const parts = iri.split(separator).filter(Boolean);
      const sf = parts[parts.length - 1];
      if (sf) {
        navigate(`/${ontology || "oeo"}/${sf}`);
        window.scrollTo(0, 0);
      }
    }
  };

  const handleNavigateToOntology = (...args) => {
    let url = "";
    if (args.length >= 3 && args[2]?.iri) url = args[2].iri;
    else if (args[0] && typeof args[0] === "object") url = args[0].url || args[0].iri || args[0].ontologyIri || "";
    else if (typeof args[0] === "string") url = args[0];

    if (url && (url.startsWith("http://") || url.startsWith("https://"))) {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  };

  // Show a spinner while we figure out if it's a class, property, or individual
  if (loadingType) {
    return (
      <EuiPageTemplate paddingSize="m">
        <EuiFlexGroup justifyContent="center" alignItems="center" style={{ minHeight: "50vh" }}>
          <EuiLoadingSpinner size="xl" />
        </EuiFlexGroup>
      </EuiPageTemplate>
    );
  }

  return (
    <EuiPageTemplate paddingSize="m">
      <EuiPageTemplate.Section>
        <EuiSpacer size="m" />

        <EuiFlexGroup alignItems="center" justifyContent="spaceBetween">
          <EuiFlexItem grow={false}>
            <TssEntityNavButtons
              iri={fetchIri}
              ontologyId={ontology}
              entityType={entityType} // Passes the correct type down to fix the API paths
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
            <EuiFlexGroup alignItems="center" gutterSize="s">
              <EuiFlexItem grow={false}>
                <EuiTitle size="l">
                  <h1 style={{ color: "#0071c1" }}>{short_form}</h1>
                </EuiTitle>
              </EuiFlexItem>
              <EuiFlexItem grow={false}>
                {/* Visual indicator replaces the old tabs! */}
                <EuiBadge color={entityType === "property" ? "warning" : entityType === "individual" ? "secondary" : "primary"}>
                  {entityType.toUpperCase()}
                </EuiBadge>
              </EuiFlexItem>
            </EuiFlexGroup>
            <EuiSpacer size="s" />
            <TssIriWidget iri={displayIri} />
          </EuiFlexItem>
        </EuiFlexGroup>

        <EuiSpacer size="m" />

        <EuiPanel paddingSize="l">
          <EuiTitle size="s"><h3>Entity Information</h3></EuiTitle>
          <EuiSpacer size="s" />

          <TssDescription iri={fetchIri} ontologyId={ontology} />
          <EuiSpacer size="m" />

          {/* THE WIDGET NOW KNOWS EXACTLY WHAT IT IS LOADING */}
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
