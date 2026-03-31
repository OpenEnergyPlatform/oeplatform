// ontology/frontend/src/features/terminology/components/TssEntityInfo.jsx
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React from "react";
import { EntityInfoWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssEntityInfo({
    iri,
    ontologyId,
    entityType = "class", // Now automatically passed down from the page
    onNavigateToEntity,
    onNavigateToOntology
}) {
    const { apiBase, ontology: configOntology } = useTssConfig();
    const activeOntology = ontologyId || configOntology;

    return (
        <EntityInfoWidget
            api={apiBase}
            ontologyId={activeOntology} // ALWAYS use the ontology context!
            iri={iri}
            entityType={entityType}
            hasTitle={false}
            showBadges={true}
            parameter=""
            onNavigateToDisambiguate={() => { }}
            onNavigateToEntity={onNavigateToEntity || (() => { })}
            onNavigateToOntology={onNavigateToOntology || (() => { })}
        />
    );
}
