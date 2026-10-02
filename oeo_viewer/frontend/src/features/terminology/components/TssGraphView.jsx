// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React from "react";
import { GraphViewWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssGraphView({ iri, onNavigateTo }) {
    const { apiBase, ontology } = useTssConfig();

    if (!iri) return null;

    return (
        <GraphViewWidget
            api={apiBase}
            ontologyId={ontology}
            iri={iri}
            // Both navigate and node clicks should trigger the same selection update in your viewer
            onNavigateTo={onNavigateTo}
            onNodeClick={onNavigateTo}
            targetIri=""
        />
    );
}
