// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import React from 'react';
import Chip from '@mui/material/Chip';
import AttachmentIcon from '@mui/icons-material/Attachment';

// Component: Recursively render the tree structure
const HierarchyViewer = ({ nodes, onLinkClick }) => {
    if (!nodes || nodes.length === 0) return null;

    return (
        <ul style={{ listStyle: 'none', paddingLeft: '1.2rem', margin: '5px 0' }}>
            {nodes.map((node) => (
                <li key={node.value} style={{ position: 'relative' }}>
                    {/* Connecting lines for tree look */}
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>

                        {/* Render the Label (contains the Tooltip from your data) */}
                        {node.label}

                        {/* Optional: Add a small link button if IRI exists */}
                        {node.iri && (
                            <Chip
                                label="Open"
                                icon={<AttachmentIcon style={{ fontSize: 14 }} />}
                                size="small"
                                variant="outlined"
                                onClick={() => onLinkClick(node.iri)}
                                sx={{ ml: 1, height: '20px', fontSize: '0.7rem', cursor: 'pointer' }}
                            />
                        )}
                    </div>

                    {/* Render Children */}
                    {node.children && (
                        <div style={{ borderLeft: '1px solid #ddd' }}>
                            <HierarchyViewer nodes={node.children} onLinkClick={onLinkClick} />
                        </div>
                    )}
                </li>
            ))}
        </ul>
    );
};

export default HierarchyViewer;
