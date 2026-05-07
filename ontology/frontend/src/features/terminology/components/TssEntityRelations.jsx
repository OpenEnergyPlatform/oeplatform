// ontology/frontend/src/features/terminology/components/TssEntityRelations.jsx
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useMemo } from "react";
import { EntityRelationsWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssEntityRelations({
    iri,
    ontologyId,
    entityType = "term",
    onNavigateToEntity,
    onNavigateToOntology,
    activeLang
}) {
    const { apiBase, ontology: configOntology, lang: configLang } = useTssConfig();
    const activeOntology = ontologyId || configOntology;

    const currentLang = activeLang || configLang;

    const mergedParameter = useMemo(() => {
        return currentLang ? `lang=${encodeURIComponent(currentLang)}` : "";
    }, [currentLang]);

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
            parameter={mergedParameter} // <--- PASS IT HERE
            termLink=""
            onNavigateToDisambiguate={() => { }}
            {...callbackProps}
        />
    );
}
