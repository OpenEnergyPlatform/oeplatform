// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { EuiPageTemplate, EuiPanel, EuiTitle, EuiSpacer } from "@elastic/eui";
import TssSearchResultsList from "../features/terminology/components/TssSearchResultsList";

export default function EntitySearchPage() {
    const { ontology } = useParams(); // Gets 'oeo', 'mrel', etc. from URL
    const navigate = useNavigate();

    const handleNavigateToEntity = (event) => {
        // 1. Try to get the short_form (e.g., OEO_00000123)
        let shortForm = event.short_form;

        // 2. Fallback: Parse IRI if short_form is missing
        if (!shortForm && event.iri) {
            const parts = event.iri.split("/");
            shortForm = parts[parts.length - 1];
        }

        if (shortForm) {
            // Navigate to the Detail Page within this app
            navigate(`/${ontology}/${shortForm}`);
        }
    };

    return (
        <EuiPageTemplate paddingSize="m">
            <EuiPageTemplate.Section>
                <EuiTitle size="l">
                    <h1>{ontology ? ontology.toUpperCase() : ""} Entity Search</h1>
                </EuiTitle>
                <EuiSpacer size="m" />

                <EuiPanel paddingSize="l">
                    {/* The configured wrapper handles the TSS widgets specifics */}
                    <TssSearchResultsList
                        ontologyId={ontology}
                        onNavigateToEntity={handleNavigateToEntity}
                    />
                </EuiPanel>
            </EuiPageTemplate.Section>
        </EuiPageTemplate>
    );
}
