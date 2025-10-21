
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later


import React from "react";
import {
    EuiFlyout,
    EuiFlyoutHeader,
    EuiFlyoutBody,
    EuiPanel,
    EuiFlexGroup,
    EuiFlexItem,
    EuiTitle,
    EuiButtonIcon,
    EuiToolTip,
    EuiCopy,
} from "@elastic/eui";
import TssMetadata from "./TssMetadata";

function openIriInNewTab(iri) {
    try {
        const u = new URL(iri);
        if (u.protocol === "http:" || u.protocol === "https:") {
            window.open(iri, "_blank", "noopener,noreferrer");
        }
    } catch {
        /* non-URL IRI (urn:, etc.) — ignore */
    }
}

export default function EntityFlyout({ iri, isOpen, onClose, title = "Selected element" }) {
    if (!isOpen) return null;

    return (
        <EuiFlyout ownFocus onClose={onClose} size="m" aria-labelledby="entity-flyout-title">
            <EuiFlyoutHeader hasBorder>
                <EuiFlexGroup alignItems="center" gutterSize="s" responsive={false} justifyContent="spaceBetween">
                    <EuiFlexItem grow={false}>
                        <EuiTitle size="s">
                            <h2 id="entity-flyout-title">{title}</h2>
                        </EuiTitle>
                    </EuiFlexItem>

                    <EuiFlexItem grow={false}>
                        <EuiFlexGroup gutterSize="s" alignItems="center" responsive={false}>
                            <EuiFlexItem grow={false}>
                                <EuiToolTip content="Open IRI in new tab">
                                    <EuiButtonIcon
                                        iconType="popout"
                                        aria-label="Open IRI in new tab"
                                        onClick={() => openIriInNewTab(iri)}
                                    />
                                </EuiToolTip>
                            </EuiFlexItem>
                            <EuiFlexItem grow={false}>
                                <EuiCopy textToCopy={iri}>
                                    {(copy) => (
                                        <EuiToolTip content="Copy IRI">
                                            <EuiButtonIcon iconType="copyClipboard" aria-label="Copy IRI" onClick={copy} />
                                        </EuiToolTip>
                                    )}
                                </EuiCopy>
                            </EuiFlexItem>
                            <EuiFlexItem grow={false}>
                                <EuiToolTip content="Close">
                                    <EuiButtonIcon iconType="cross" aria-label="Close" onClick={onClose} />
                                </EuiToolTip>
                            </EuiFlexItem>
                        </EuiFlexGroup>
                    </EuiFlexItem>
                </EuiFlexGroup>
            </EuiFlyoutHeader>

            <EuiFlyoutBody>
                <EuiPanel paddingSize="m">
                    <TssMetadata iri={iri} tabs={{ termDepiction: false, terminologyInfo: false }} />
                </EuiPanel>
            </EuiFlyoutBody>
        </EuiFlyout>
    );
}
