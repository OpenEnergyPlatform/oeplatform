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
  } = props;

  const getNodeIds = (nodes) => {
    let ids = [];
    nodes?.forEach(({ value, children }) => {
      ids = [...ids, value, ...getNodeIds(children)];
    });
    return ids;
  };

  const [checked, setChecked] = useState(props.checked.map(i => i.label));
  const [searchTerm, setSearchTerm] = useState('');
  const [expanded, setExpanded] = useState(getNodeIds(data));

  const handleChange = (checked) => {
    setChecked(checked);
    handler(checked, data);
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

      // Recurse into children
      const filteredChildren = node.children ? filterNodes(node.children, term, expandedSet) : [];

      // Include this node if it matches or has matching children
      if (labelMatch || filteredChildren.length > 0) {
        if (filteredChildren.length > 0) {
          expandedSet.add(node.value); // Expand parent
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
  }, [searchTerm, data]);

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
          checked={checked}
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
        {checked.map((v) => (
          <Chip
            key={v}
            size="small"
            label={v}
            variant="outlined"
            sx={{ m: 0.5 }}
          />
        ))}
      </Box>
    </Box>
  );
}
