// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React from "react";
import { useQuery } from "react-query";
import { EuiButton, EuiFlexGroup, EuiFlexItem, EuiLoadingSpinner, EuiText } from "@elastic/eui";
import { useTssConfig } from "../hooks/useTssConfig";

export default function TssEntityNavButtons({ iri, ontologyId, onNavigate }) {
    const { apiBase } = useTssConfig();

    // URL-encode the IRI as required by the TIB API path
    const encodedIri = encodeURIComponent(encodeURIComponent(iri));

    // Construct base URL (handle global vs specific ontology routing)
    const baseUrl = ontologyId
        ? `${apiBase}ontologies/${ontologyId}/terms/${encodedIri}`
        : `${apiBase}terms/${encodedIri}`;

    // Fetch Parents
    const { data: parents, isLoading: loadingParents } = useQuery(
        ["entityParents", ontologyId, iri],
        () => fetch(`${baseUrl}/parents`).then((res) => (res.ok ? res.json() : null)),
        { enabled: !!iri }
    );

    // Fetch Children
    const { data: children, isLoading: loadingChildren } = useQuery(
        ["entityChildren", ontologyId, iri],
        () => fetch(`${baseUrl}/hierarchicalChildren`).then((res) => (res.ok ? res.json() : null)),
        { enabled: !!iri }
    );

    // Extract the arrays from the HAL JSON response format
    const parentTerms = parents?._embedded?.terms || [];
    const childTerms = children?._embedded?.terms || [];

    if (loadingParents || loadingChildren) {
        return <EuiLoadingSpinner size="m" />;
    }

    if (parentTerms.length === 0 && childTerms.length === 0) {
        return null; // Don't render anything if no hierarchy exists
    }

    return (
        <EuiFlexGroup wrap responsive={false} gutterSize="s" alignItems="center">
            {/* Parents (Up) */}
            {parentTerms.length > 0 && (
                <EuiFlexItem grow={false}>
                    <EuiFlexGroup gutterSize="xs" wrap responsive={false}>
                        {parentTerms.map((parent) => (
                            <EuiFlexItem key={parent.iri} grow={false}>
                                <EuiButton
                                    size="s"
                                    iconType="arrowUp"
                                    onClick={() => onNavigate(parent)}
                                >
                                    {parent.label || parent.short_form}
                                </EuiButton>
                            </EuiFlexItem>
                        ))}
                    </EuiFlexGroup>
                </EuiFlexItem>
            )}

            {/* Separator if both exist */}
            {parentTerms.length > 0 && childTerms.length > 0 && (
                <EuiFlexItem grow={false}>
                    <EuiText color="subdued" size="s">|</EuiText>
                </EuiFlexItem>
            )}

            {/* Children (Down) */}
            {childTerms.length > 0 && (
                <EuiFlexItem grow={false}>
                    <EuiFlexGroup gutterSize="xs" wrap responsive={false}>
                        {childTerms.map((child) => (
                            <EuiFlexItem key={child.iri} grow={false}>
                                <EuiButton
                                    size="s"
                                    iconType="arrowDown"
                                    iconSide="right"
                                    onClick={() => onNavigate(child)}
                                >
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
