// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "react-query";
import {
  EuiPageTemplate, EuiPanel, EuiSpacer, EuiTitle,
  EuiFlexGroup, EuiFlexItem, EuiButton, EuiBadge, EuiLoadingSpinner, EuiText, EuiSelect
} from "@elastic/eui";

import TssEntityInfo from "../features/terminology/components/TssEntityInfo";
import TssEntityRelations from "../features/terminology/components/TssEntityRelations";
import TssIriWidget from "../features/terminology/components/TssIriWidget";
import TssEntityNavButtons from "../features/terminology/components/TssEntityNavButtons";
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
  const { apiBase, lang } = useTssConfig();

  // Local state for the language dropdown
  const [activeLang, setActiveLang] = useState(lang || "en");

  // Redirect interceptor for "ugly" URLs
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

  // --- SUPERCHARGED QUERY ---
  const { data: entityData, isLoading: loadingData } = useQuery(
    ["entityData", short_form, fetchIri, activeLang],
    async () => {
      const fallback = { type: "class", label: short_form, description: null };
      if (!short_form || !fetchIri) return fallback;

      // 1. Search API (Mainly used to reliably figure out the type: class/property/individual)
      const searchRes = await fetch(`${apiBase}search?q=${short_form}&ontology=${ontology || "oeo"}&exact=true`);
      let derivedType = "class";
      let extractedLabel = short_form;

      if (searchRes.ok) {
        const searchData = await searchRes.json();
        const match = (searchData.response?.docs || []).find(d => {
          const sf = Array.isArray(d.short_form) ? d.short_form[0] : d.short_form;
          return sf === short_form;
        });

        if (match) {
          extractedLabel = Array.isArray(match.label) ? match.label[0] : match.label;
          if (match.type) {
            const types = Array.isArray(match.type) ? match.type : [match.type];
            if (types.includes("individual")) derivedType = "individual";
            else if (types.some(t => t.includes("property"))) derivedType = "property";
          }
        }
      }

      // 2. Entity API (This STRICTLY obeys ?lang= and is used to grab the translated label & description)
      const typePath = derivedType === "property" ? "properties"
        : derivedType === "individual" ? "individuals"
          : "terms";
      const encodedIri = encodeURIComponent(encodeURIComponent(fetchIri));

      let bestDescription = null;
      try {
        const entityRes = await fetch(`${apiBase}ontologies/${ontology || "oeo"}/${typePath}/${encodedIri}?lang=${activeLang}`);
        if (entityRes.ok) {
          const entityJson = await entityRes.json();

          // CRITICAL FIX: Overwrite the Search API label with the translated Entity API label!
          if (entityJson.label) {
            extractedLabel = entityJson.label;
          }

          if (entityJson.description && entityJson.description.length > 0) {
            bestDescription = entityJson.description[0];
          }
          else if (entityJson.annotation) {
            const eluc = entityJson.annotation["elucidation"] || entityJson.annotation["IAO_0000600"];
            const def = entityJson.annotation["definition"] || entityJson.annotation["IAO_0000115"];

            if (eluc && eluc.length > 0) bestDescription = eluc[0];
            else if (def && def.length > 0) bestDescription = def[0];
          }
        }
      } catch (e) {
        console.warn("Failed to fetch detailed entity description", e);
      }

      return {
        type: derivedType,
        label: extractedLabel || short_form,
        description: bestDescription
      };
    },
    { enabled: !!short_form && !!fetchIri }
  );

  const entityType = entityData?.type || "class";
  const entityLabel = entityData?.label || short_form;
  const entityDescription = entityData?.description;

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

  if (loadingData) {
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
              entityType={entityType}
              onNavigate={handleNavigateToEntity}
            />
          </EuiFlexItem>

          <EuiFlexItem grow={false}>
            <EuiFlexGroup gutterSize="s" alignItems="center">
              <EuiFlexItem grow={false}>
                <EuiSelect
                  options={[
                    { value: 'en', text: 'EN' },
                    { value: 'de', text: 'DE' },
                  ]}
                  value={activeLang}
                  onChange={(e) => setActiveLang(e.target.value)}
                  compressed
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
          </EuiFlexItem>
        </EuiFlexGroup>

        <EuiSpacer size="l" />

        <EuiFlexGroup justifyContent="spaceBetween" alignItems="flexStart">
          <EuiFlexItem>
            <EuiFlexGroup alignItems="center" gutterSize="s">
              <EuiFlexItem grow={false}>
                <EuiTitle size="l">
                  <h1 style={{ color: "#0071c1", margin: 0 }}>{entityLabel}</h1>
                </EuiTitle>
              </EuiFlexItem>
              <EuiFlexItem grow={false}>
                <EuiBadge color={entityType === "property" ? "warning" : entityType === "individual" ? "secondary" : "primary"}>
                  {entityType.toUpperCase()}
                </EuiBadge>
              </EuiFlexItem>
            </EuiFlexGroup>

            <EuiSpacer size="s" />

            <EuiText size="s" color="subdued">
              <strong>Ontology:</strong> {(ontology || "oeo").toUpperCase()} &nbsp;&bull;&nbsp; <strong>ID:</strong> {short_form}
            </EuiText>

            <EuiSpacer size="s" />
            <TssIriWidget iri={displayIri} />

            {entityDescription && (
              <>
                <EuiSpacer size="l" />
                <EuiText>
                  <p style={{ fontSize: "16px", lineHeight: "1.5" }}>
                    {entityDescription}
                  </p>
                </EuiText>
              </>
            )}

          </EuiFlexItem>
        </EuiFlexGroup>

        <EuiSpacer size="l" />

        <EuiPanel paddingSize="l">
          <EuiTitle size="s"><h3>Entity Information</h3></EuiTitle>
          <EuiSpacer size="s" />

          <TssEntityInfo
            iri={fetchIri}
            ontologyId={ontology}
            entityType={entityType}
            activeLang={activeLang} // <--- PASSING LANG HERE
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
            activeLang={activeLang} // <--- PASSING LANG HERE
            onNavigateToEntity={handleNavigateToEntity}
            onNavigateToOntology={handleNavigateToOntology}
          />
        </EuiPanel>
      </EuiPageTemplate.Section>
    </EuiPageTemplate>
  );
}
