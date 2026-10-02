// ontology/frontend/src/features/terminology/components/TssEntityNavButtons.jsx
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React from "react";
import { useQuery } from "react-query";
import { EuiButton, EuiFlexGroup, EuiFlexItem, EuiLoadingSpinner, EuiText } from "@elastic/eui";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssEntityNavButtons({ iri, ontologyId, entityType = "class", onNavigate }) {
    const { apiBase } = useTssConfig();

    const encodedIri = encodeURIComponent(encodeURIComponent(iri));

    // Map the entity type to the correct API path segment
    const typePath = entityType === "property" ? "properties"
        : entityType === "individual" ? "individuals"
            : "terms";

    const baseUrl = ontologyId
        ? `${apiBase}ontologies/${ontologyId}/${typePath}/${encodedIri}`
        : `${apiBase}${typePath}/${encodedIri}`;

    const { data: parents, isLoading: loadingParents } = useQuery(
        ["entityParents", ontologyId, iri, entityType],
        () => fetch(`${baseUrl}/parents`).then((res) => (res.ok ? res.json() : null)),
        { enabled: !!iri }
    );

    const { data: children, isLoading: loadingChildren } = useQuery(
        ["entityChildren", ontologyId, iri, entityType],
        () => fetch(`${baseUrl}/hierarchicalChildren`).then((res) => (res.ok ? res.json() : null)),
        { enabled: !!iri }
    );

    const parentTerms = parents?._embedded?.terms || parents?._embedded?.properties || parents?._embedded?.individuals || [];
    const childTerms = children?._embedded?.terms || children?._embedded?.properties || children?._embedded?.individuals || [];

    if (loadingParents || loadingChildren) return <EuiLoadingSpinner size="m" />;
    if (parentTerms.length === 0 && childTerms.length === 0) return null;

    return (
        <EuiFlexGroup wrap responsive={false} gutterSize="s" alignItems="center">
            {parentTerms.length > 0 && (
                <EuiFlexItem grow={false}>
                    <EuiFlexGroup gutterSize="xs" wrap responsive={false}>
                        {parentTerms.map((parent) => (
                            <EuiFlexItem key={parent.iri} grow={false}>
                                <EuiButton size="s" iconType="arrowUp" onClick={() => onNavigate(parent)}>
                                    {parent.label || parent.short_form}
                                </EuiButton>
                            </EuiFlexItem>
                        ))}
                    </EuiFlexGroup>
                </EuiFlexItem>
            )}

            {parentTerms.length > 0 && childTerms.length > 0 && (
                <EuiFlexItem grow={false}><EuiText color="subdued" size="s">|</EuiText></EuiFlexItem>
            )}

            {childTerms.length > 0 && (
                <EuiFlexItem grow={false}>
                    <EuiFlexGroup gutterSize="xs" wrap responsive={false}>
                        {childTerms.map((child) => (
                            <EuiFlexItem key={child.iri} grow={false}>
                                <EuiButton size="s" iconType="arrowDown" iconSide="right" onClick={() => onNavigate(child)}>
                                    {child.label || child.short_form}
                                </EuiButton>
                            </EuiFlexItem>
                        ))}
                    </EuiFlexGroup>
                </EuiFlexItem>
            )}
        </EuiFlexGroup>
    );
}
