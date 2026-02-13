// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

// ontology/frontend/src/features/terminology/components/TssEntityInfo.jsx
import React from "react";
import { EntityInfoWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssEntityInfo({
    iri,
    ontologyId,
    entityType = "class", // Default, but can be overridden
    onNavigateToEntity,
    onNavigateToOntology
}) {
    const { apiBase, ontology: configOntology } = useTssConfig();
    // const activeOntology = ontologyId || configOntology;

    // Check if it's an external term by looking at the IRI
    const isExternal = iri.includes("purl.obolibrary.org");

    return (
        <EntityInfoWidget
            api={apiBase}
            ontologyId={isExternal ? "" : ontologyId}
            iri={iri}
            entityType={entityType}
            hasTitle={false} // We handle the title in the page layout
            showBadges={true}
            useLegacy={true}
            parameter=""
            onNavigateToDisambiguate={() => { }}
            onNavigateToEntity={onNavigateToEntity || (() => { })}
            onNavigateToOntology={onNavigateToOntology || (() => { })}
        />
    );
}
