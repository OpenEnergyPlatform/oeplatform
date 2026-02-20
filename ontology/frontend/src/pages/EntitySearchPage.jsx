// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React from "react";
import { useParams } from "react-router-dom";
import { EuiPageTemplate, EuiPanel, EuiTitle, EuiSpacer } from "@elastic/eui";
import TssSearchResultsList from "../features/terminology/components/TssSearchResultsList";

export default function EntitySearchPage() {
    const { ontology } = useParams();
    const targetOntology = ontology || "oeo";

    // 1. Single source of truth for entity navigation
    const triggerHardReload = (shortForm) => {
        if (shortForm) {
            // Open your local Django detail page in a NEW tab
            window.open(`/ontology/${targetOntology}/${shortForm}/`, "_blank", "noopener,noreferrer");
        }
    };

    // 2. Navigation to an external ontology page (clicking a badge)
    const handleNavigateToOntology = (...args) => {
        let url = "";

        // Extract the URL or the short ID
        if (args.length >= 3 && args[2]?.iri) {
            url = args[2].iri;
        } else if (args[0] && typeof args[0] === "object") {
            url = args[0].url || args[0].iri || args[0].ontologyIri || "";
            // Fallback if we only got an object with an ID
            if (!url && (args[0].ontologyId || args[0].ontology_name)) {
                const id = args[0].ontologyId || args[0].ontology_name;
                url = `https://terminology.tib.eu/ts/ontologies/${id}`;
            }
        } else if (typeof args[0] === "string") {
            // TSS usually passes just the short string here (e.g., "bfo")
            if (args[0].startsWith("http")) {
                url = args[0];
            } else {
                url = `https://terminology.tib.eu/ts/ontologies/${args[0]}`;
            }
        }

        if (url && (url.startsWith("http://") || url.startsWith("https://"))) {
            window.open(url, "_blank", "noopener,noreferrer");
        } else {
            console.warn("TSS: Could not resolve ontology URL from click:", args);
        }
    };

    // 3. Handled by the widget when clicking a card title
    const handleNavigateToEntity = (event) => {
        if (event && typeof event.preventDefault === 'function') {
            event.preventDefault();
        }

        let nextId = event.short_form;
        if (!nextId && event.iri) {
            const parts = event.iri.split("/");
            nextId = parts[parts.length - 1];
        }

        if (nextId) triggerHardReload(nextId);
    };

    // 4. SMART Interceptor
    const handleInterceptIriClick = (e) => {
        const anchor = e.target.closest("a");
        if (!anchor) return;

        // If the user clicked an EUI Badge, prevent the browser from following
        // any broken hrefs it might have, but DO NOT stop propagation.
        // This guarantees the widget's handleNavigateToOntology still fires!
        if (anchor.classList.contains("euiBadge") || anchor.closest(".euiBadge")) {
            e.preventDefault();
            return;
        }

        const href = anchor.getAttribute("href");
        if (!href || href === "#" || href.startsWith("/")) return;

        // Block the widget's internal bad routing attempts
        if (href.includes("ontologies/") && href.includes("?iri=")) {
            e.preventDefault();
            e.stopPropagation();
            return;
        }

        // External HTTP links (Raw IRIs)
        if (href.startsWith("http")) {
            const separator = href.includes("#") ? "#" : "/";
            const parts = href.split(separator).filter(Boolean);
            const potentialShortForm = parts[parts.length - 1];

            // Only hijack it if it actually looks like an entity ID (e.g., has an underscore)
            if (potentialShortForm && potentialShortForm.includes("_")) {
                e.preventDefault();
                e.stopPropagation();

                // // OPEN THE EXTERNAL SOURCE IN A NEW TAB:
                // window.open(href, "_blank", "noopener,noreferrer");

                // OR, IF YOU STILL WANT IT TO GO TO YOUR DJANGO PAGE IN A NEW TAB, DO THIS INSTEAD:
                window.open(`/ontology/${targetOntology}/${potentialShortForm}/`, "_blank", "noopener,noreferrer");
            }
        }
    };

    return (
        <EuiPageTemplate paddingSize="m">
            <EuiPageTemplate.Section>
                <EuiTitle size="l">
                    <h1>Open Energy Ontology Search</h1>
                </EuiTitle>
                <EuiSpacer size="m" />

                <EuiPanel paddingSize="l">
                    <div onClickCapture={handleInterceptIriClick}>
                        <TssSearchResultsList
                            ontologyId={targetOntology}
                            onNavigateToEntity={handleNavigateToEntity}
                            onNavigateToOntology={handleNavigateToOntology}
                        />
                    </div>
                </EuiPanel>
            </EuiPageTemplate.Section>
        </EuiPageTemplate>
    );
}
