// ontology/frontend/src/features/terminology/components/TssEntityRelations.jsx
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useMemo } from "react";
import { EntityRelationsWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssEntityRelations({
    iri,
    ontologyId,
    entityType = "term", // "term" often works best for relations to show instances too
    onNavigateToEntity,
    onNavigateToOntology
}) {
    const { apiBase, ontology: configOntology, lang } = useTssConfig();
    const activeOntology = ontologyId || configOntology;

    const mergedParameter = useMemo(() => {
        return lang ? `lang=${encodeURIComponent(lang)}` : "";
    }, [lang]);

    const callbackProps = {
        ...(onNavigateToEntity ? { onNavigateToEntity } : {}),
        ...(onNavigateToOntology ? { onNavigateToOntology } : {}),
    };

    return (
        <EntityRelationsWidget
            api={apiBase}
            ontologyId={activeOntology}
            iri={iri}
            entityType={entityType}
            hasTitle={false}
            showBadges={true}
            parameter={mergedParameter}
            termLink=""

            onNavigateToDisambiguate={() => { }}
            {...callbackProps}
        />
    );
}
