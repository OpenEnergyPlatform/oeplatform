// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useMemo } from "react";
import { SearchResultsListWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssSearchResultsList({
    ontologyId,
    query = "*",
    onNavigateToEntity,
    onNavigateToOntology,
}) {
    const { apiBase, ontology: configOntology } = useTssConfig();
    const activeOntology = ontologyId || configOntology;

    const parameter = useMemo(() => {
        return `collection=nfdi4energy&ontology=${activeOntology}&fieldList=description,label,iri,ontology_name,type,short_form`;
    }, [activeOntology]);

    return (
        <SearchResultsListWidget
            api={apiBase}
            ontologyId={activeOntology}
            parameter={parameter}
            query={query}
            initialItemsPerPage={10}
            itemsPerPageOptions={[10, 25, 50, 100]}
            // useLegacy={true}
            preselected={[]}
            targetLink="" // Keep this empty to prevent the widget from making bad native URLs
            onNavigateToEntity={onNavigateToEntity}
            onNavigateToOntology={onNavigateToOntology || (() => { })}
        />
    );
}
