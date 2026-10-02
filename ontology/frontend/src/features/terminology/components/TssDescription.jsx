// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React from "react";
import { DescriptionWidget } from "@ts4nfdi/terminology-service-suite";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssDescription({ iri, ontologyId }) {
    const { apiBase, ontology: configOntology } = useTssConfig();
    const activeOntology = ontologyId || configOntology;

    if (!iri) return null;

    return (
        <DescriptionWidget
            api={apiBase}
            ontologyId={activeOntology}
            iri={iri}
            useLegacy={true}
        />
    );
}
