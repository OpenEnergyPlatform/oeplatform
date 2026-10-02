// ontology/frontend/src/features/terminology/components/TssEntityInfo.jsx
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React from "react";
import { EntityInfoWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssEntityInfo({
    iri,
    ontologyId,
    entityType = "class",
    onNavigateToEntity,
    onNavigateToOntology,
    activeLang
}) {
    // We still grab config values, but we will let the local activeLang override the config lang
    const { apiBase, ontology: configOntology, lang: configLang } = useTssConfig();
    const activeOntology = ontologyId || configOntology;

    // Prioritize the dropdown selection, fallback to the global config
    const currentLang = activeLang || configLang;
    const parameter = currentLang ? `lang=${encodeURIComponent(currentLang)}` : "";

    return (
        <EntityInfoWidget
            api={apiBase}
            ontologyId={activeOntology}
            iri={iri}
            entityType={entityType}
            hasTitle={false}
            showBadges={true}
            parameter={parameter} // <--- PASS IT HERE
            onNavigateToDisambiguate={() => { }}
            onNavigateToEntity={onNavigateToEntity || (() => { })}
            onNavigateToOntology={onNavigateToOntology || (() => { })}
        />
    );
}
