// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useState } from "react";
import {
    EuiPanel,
    EuiText,
    EuiButtonEmpty,
    EuiIcon,
    EuiSpacer,
} from "@elastic/eui";

/** A collapsible, top-of-page banner explaining how to use the viewer. */
export default function TopInfoBanner() {
    const [open, setOpen] = useState(false);

    return (
        <EuiPanel color="subdued" hasBorder paddingSize="m">
            <div style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <EuiIcon type="iInCircle" />
                    <EuiText size="s">
                        <strong>How to use the OEO Viewer</strong>
                    </EuiText>
                </div>
                <EuiButtonEmpty
                    size="s"
                    iconType={open ? "arrowUp" : "arrowDown"}
                    iconSide="right"
                    onClick={() => setOpen((o) => !o)}
                    aria-expanded={open}
                >
                    {open ? "Hide" : "Show"}
                </EuiButtonEmpty>
            </div>

            {open && (
                <>
                    <EuiSpacer size="s" />
                    <div
                        style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                            gap: 24,
                        }}
                    >
                        <EuiText size="s">
                            <p><strong>1. Browse & Navigate</strong></p>
                            <ul>
                                <li><strong>Full Hierarchy:</strong> Use the tree on the left to explore the asserted structure of the OEO.</li>
                                <li><strong>Search:</strong> Use the autocomplete bar to find specific terms by label or IRI.</li>
                                <li><strong>Selection:</strong> Clicking a result or a tree node loads the term details.</li>
                            </ul>
                        </EuiText>

                        <EuiText size="s">
                            <p><strong>2. Inspect & Visualize</strong></p>
                            <ul>
                                <li><strong>Metadata:</strong> View full definitions, annotations, and cross-references.</li>
                                <li><strong>Graph View:</strong> Switch to the <em>Graph View</em> tab to visualize complex relationships.</li>
                                <li><strong>Local Hierarchy:</strong> See immediate parents and children in the <em>Hierarchy</em> tab.</li>
                            </ul>
                        </EuiText>

                        <EuiText size="s">
                            <p><strong>3. Share & Cite</strong></p>
                            <ul>
                                <li><EuiIcon type="link" size="s" /> <strong>Copy IRI:</strong> Click this button to copy the stable, permanent OEP identifier for the term.</li>
                                <li><EuiIcon type="share" size="s" /> <strong>Share View:</strong> Click this button to copy a link to your current view configuration to share with others.</li>
                            </ul>
                        </EuiText>
                    </div>
                </>
            )}
        </EuiPanel>
    );
}
