
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
                            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
                            gap: 12,
                        }}
                    >
                        <EuiText size="s">
                            <p><strong>Browse the full hierarchy (left column)</strong></p>
                            <ul>
                                <li>Expand nodes to explore classes in the ontology.</li>
                                <li>Click a term to open a details flyout — this won’t change the right-side selection.</li>
                                <li>Use badges to jump to the defining ontology in a new tab.</li>
                            </ul>
                        </EuiText>

                        <EuiText size="s">
                            <p><strong>Search & inspect a specific term (right column)</strong></p>
                            <ul>
                                <li>Use <em>Autocomplete</em> to find a term by label or IRI snippet.</li>
                                <li>Selected terms show <em>Metadata</em> and a local <em>Hierarchy</em> or <em>Graph View</em> for context.</li>
                                <li>Hide/show metadata tabs to focus on what you need; copy the IRI for reuse.</li>
                            </ul>
                        </EuiText>
                    </div>
                </>
            )}
        </EuiPanel>
    );
}
