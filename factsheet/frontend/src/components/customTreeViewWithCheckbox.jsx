import React, { useState, useMemo } from 'react';
import CheckboxTree from 'react-checkbox-tree';
import 'react-checkbox-tree/lib/react-checkbox-tree.css';
import '../styles/react-checkbox-tree.css';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CheckBoxOutlinedIcon from '@mui/icons-material/CheckBoxOutlined';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';

export default function CustomTreeViewWithCheckBox(props) {
  const {
    data,
    size,
    handler,
    checked = [], // Default to empty array if undefined
  } = props;

  const getNodeIds = (nodes) => {
    let ids = [];
    nodes?.forEach(({ value, children }) => {
      ids = [...ids, value, ...getNodeIds(children)];
    });
    return ids;
  };

  // --- FIX 1: Remove local 'checked' state ---
  // We now rely entirely on props.checked to be the "Source of Truth"

  const [searchTerm, setSearchTerm] = useState('');
  const [expanded, setExpanded] = useState(getNodeIds(data));

  // --- FIX 2: Update Handler ---
  // Don't set local state, just tell the parent what happened
  const handleChange = (newChecked) => {
    handler(newChecked, data);
  };

  const highlightLabel = (label, term) => {
    if (!term) return label;
    const regex = new RegExp(`(${term})`, 'gi');
    return <span dangerouslySetInnerHTML={{ __html: label.replace(regex, '<mark>$1</mark>') }} />;
  };

  const filterNodes = (nodes, term, expandedSet = new Set()) => {
    const filtered = [];

    for (const node of nodes) {
      const rawLabel = typeof node.value === 'string' ? node.value : node.rawLabel || '';
      const labelMatch = rawLabel.toLowerCase().includes(term.toLowerCase());

      const filteredChildren = node.children ? filterNodes(node.children, term, expandedSet) : [];

      if (labelMatch || filteredChildren.length > 0) {
        if (filteredChildren.length > 0) {
          expandedSet.add(node.value);
        }

        filtered.push({
          ...node,
          rawLabel,
          label: highlightLabel(rawLabel, term),
          children: filteredChildren,
        });
      }
    }
    return filtered;
  };

  const { filteredData, autoExpanded } = useMemo(() => {
    if (!searchTerm) return { filteredData: data, autoExpanded: expanded };

    const expandedSet = new Set();
    const filtered = filterNodes(data, searchTerm, expandedSet);
    return {
      filteredData: filtered,
      autoExpanded: Array.from(expandedSet),
    };
  }, [searchTerm, data, expanded]); // Added expanded to dependency array

  // --- Helper to get readable labels for the Chips ---
  // Since 'checked' is now a list of IDs/Values, we need to find the text label to display
  const getLabelForValue = (val, nodes) => {
    for (const node of nodes) {
      if (node.value === val) return node.label; // Found it
      if (node.children) {
        const found = getLabelForValue(val, node.children);
        if (found) return found;
      }
    }
    return val; // Fallback to ID if label not found
  };

  return (
    <Box>
      <TextField
        label="Search ..."
        variant="outlined"
        size="small"
        fullWidth
        margin="dense"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />

      <Box style={{ height: size, overflow: 'auto', border: '1px solid #cecece', width: '99%', borderRadius: '4px' }}>
        <CheckboxTree
          nodes={filteredData}
          // --- FIX 3: Use props directly ---
          // Ensure we handle cases where checked might be an array of objects vs strings
          // Assuming your parent fix now sends an array of ID strings:
          checked={Array.isArray(checked) ? checked.map(c => (typeof c === 'object' ? (c.value || c.label) : c)) : []}
          expanded={searchTerm ? autoExpanded : expanded}
          onCheck={handleChange}
          onExpand={(expanded) => setExpanded(expanded)}
          icons={{
            check: <CheckBoxIcon />,
            uncheck: <CheckBoxOutlineBlankIcon />,
            expandClose: <KeyboardArrowRightIcon />,
            expandOpen: <KeyboardArrowDownIcon />,
            halfCheck: <CheckBoxOutlinedIcon />,
          }}
          showNodeIcon={false}
          optimisticToggle={false}
          noCascade={true}
        />
      </Box>

      <Box mt={3} sx={{ marginTop: '10px', overflow: 'auto' }}>
        {/* --- FIX 4: Map IDs to Labels for Chips --- */}
        {Array.isArray(checked) && checked.map((val) => {
          // Handle if val is an object (legacy) or string (new logic)
          const valueStr = typeof val === 'object' ? val.label : val;
          const displayLabel = getLabelForValue(valueStr, data);

          return (
            <Chip
              key={valueStr}
              size="small"
              label={displayLabel}
              variant="outlined"
              sx={{ m: 0.5 }}
            />
          );
        })}
      </Box>
    </Box>
  );
}
