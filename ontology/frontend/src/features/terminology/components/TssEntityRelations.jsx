// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

// ontology/frontend/src/features/terminology/components/TssEntityRelations.jsx
import React from "react";
import { EntityRelationsWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssEntityRelations({
    iri,
    ontologyId,
    entityType = "term", // "term" often works best for relations to show instances too
    onNavigateToEntity
}) {
    const { apiBase, ontology: configOntology } = useTssConfig();
    const activeOntology = ontologyId || configOntology;

    return (
        <EntityRelationsWidget
            api={apiBase}
            ontologyId={activeOntology}
            iri={iri}
            entityType={entityType}
            hasTitle={false}
            showBadges={true}
            parameter=""
            onNavigateToDisambiguate={() => { }}
            onNavigateToEntity={onNavigateToEntity || (() => { })}
            onNavigateToOntology={() => { }}
        />
    );
}
