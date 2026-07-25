// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// Master-detail sector picker (OEKG scenario-bundles wayfinder WF-02 variant B,
// WF-06). Left pane = the sector divisions selected for this bundle, with the
// "Other" pseudo-division as a permanent peer row. Right pane = the options of
// the active row: a checkbox list of the division's member sectors
// (`kind: "individuals"`) or the OEO sector taxonomy as a tree
// (`kind: "tree"`, the "Other" row).
//
// Divisions and their options come from the backend
// (`scenario-bundles/populate_factsheets_elements/` → `sector_divisions`); this
// component only decides what is rendered and what ends up in the flat
// `sectors` selection, whose items keep the `{value, label, class}` shape the
// save path expects.

import React, { useEffect, useMemo, useState } from 'react';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Checkbox from '@mui/material/Checkbox';
import Chip from '@mui/material/Chip';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import CustomTreeViewWithCheckBox from '../customTreeViewWithCheckbox.jsx';

const paneStyle = (size) => ({
  height: size,
  overflow: 'auto',
  border: '1px solid #cecece',
  borderRadius: '4px'
});

// Flatten a tree of option nodes into a list (the tree pane needs lookups by
// both node value and IRI).
const flattenTree = (nodes = [], acc = []) => {
  nodes.forEach((node) => {
    if (!node) return;
    acc.push(node);
    if (node.children) flattenTree(node.children, acc);
  });
  return acc;
};

const nodeValue = (node) => String(node.value ?? node.label ?? '');
const nodeLabel = (node) => String(node.label ?? node.value ?? '');

export default function SectorSelector({
  divisions = [],
  selectedDivisions = [],
  selectedSectors = [],
  onSectorsChange,
  size = '360px'
}) {
  // The "Other" row is served as a division with kind "tree"; it is not a real
  // OEO division, so it is never offered in the divisions dropdown and never
  // written to `sector_divisions` — it is always available here instead.
  const treeDivision = useMemo(
    () => divisions.find((d) => d.kind === 'tree'),
    [divisions]
  );

  const rows = useMemo(() => {
    const byIri = new Map(
      divisions.filter((d) => d.kind !== 'tree').map((d) => [String(d.iri || d.class), d])
    );
    const picked = selectedDivisions.map((selected) => {
      const key = String(selected.iri || selected.class);
      // A division the OEO no longer serves still gets a row, just no options.
      return (
        byIri.get(key) || {
          ...selected,
          iri: key,
          kind: 'individuals',
          options: []
        }
      );
    });
    return treeDivision ? [...picked, treeDivision] : picked;
  }, [divisions, selectedDivisions, treeDivision]);

  const [activeIri, setActiveIri] = useState(null);
  // Some divisions are long (CRF sectors IPCC 2006 has 108 members); the tree
  // pane brings its own search field, the checkbox pane gets this one.
  const [filter, setFilter] = useState('');

  useEffect(() => {
    const keys = rows.map((row) => String(row.iri || row.class));
    if (keys.length && !keys.includes(String(activeIri))) {
      setActiveIri(keys[0]);
    }
  }, [rows, activeIri]);

  const activeRow =
    rows.find((row) => String(row.iri || row.class) === String(activeIri)) || rows[0];

  const selectedIris = useMemo(
    () => new Set(selectedSectors.map((sector) => String(sector.class))),
    [selectedSectors]
  );

  const countSelected = (row) => {
    const options =
      row.kind === 'tree' ? flattenTree(row.options) : row.options || [];
    return options.filter((option) => selectedIris.has(String(option.iri))).length;
  };

  const countOptions = (row) =>
    row.kind === 'tree' ? flattenTree(row.options).length : (row.options || []).length;

  const toggleOption = (option) => {
    const iri = String(option.iri);
    if (selectedIris.has(iri)) {
      onSectorsChange(selectedSectors.filter((sector) => String(sector.class) !== iri));
    } else {
      const label = nodeLabel(option);
      onSectorsChange([
        ...selectedSectors,
        { value: label, label: label, class: option.iri }
      ]);
    }
  };

  const removeSector = (sector) =>
    onSectorsChange(
      selectedSectors.filter((item) => String(item.class) !== String(sector.class))
    );

  // The tree reports the values checked *within the tree*; selections made in
  // the other divisions must survive, so only tree members are replaced.
  const treeNodes = useMemo(
    () => (treeDivision ? flattenTree(treeDivision.options) : []),
    [treeDivision]
  );

  const handleTreeCheck = (checkedValues) => {
    const byValue = new Map(treeNodes.map((node) => [nodeValue(node), node]));
    const treeIris = new Set(treeNodes.map((node) => String(node.iri)));
    const kept = selectedSectors.filter(
      (sector) => !treeIris.has(String(sector.class))
    );
    const picked = [];
    (checkedValues || []).forEach((value) => {
      const node = byValue.get(String(value));
      if (!node) return;
      if (picked.some((item) => String(item.class) === String(node.iri))) return;
      picked.push({ value: nodeLabel(node), label: nodeLabel(node), class: node.iri });
    });
    onSectorsChange([...kept, ...picked]);
  };

  const treeChecked = useMemo(() => {
    const byIri = new Map(treeNodes.map((node) => [String(node.iri), node]));
    return selectedSectors
      .filter((sector) => byIri.has(String(sector.class)))
      .map((sector) => nodeValue(byIri.get(String(sector.class))));
  }, [treeNodes, selectedSectors]);

  const renderDetail = () => {
    if (!activeRow) {
      return (
        <Typography variant="caption" sx={{ p: 2, display: 'block', color: 'text.secondary' }}>
          Select a sector division above to pick its sectors, or use the
          &quot;Other&quot; row to browse the whole OEO sector hierarchy.
        </Typography>
      );
    }

    if (activeRow.kind === 'tree') {
      return (
        <CustomTreeViewWithCheckBox
          size={size}
          checked={treeChecked}
          handler={handleTreeCheck}
          data={activeRow.options || []}
        />
      );
    }

    const allOptions = activeRow.options || [];
    const options = filter
      ? allOptions.filter((option) =>
          nodeLabel(option).toLowerCase().includes(filter.toLowerCase())
        )
      : allOptions;
    if (!allOptions.length) {
      return (
        <Box sx={paneStyle(size)}>
          <Typography
            variant="caption"
            sx={{ p: 2, display: 'block', color: 'text.secondary' }}
          >
            The OEO does not define any sectors for this sector division (yet).
          </Typography>
        </Box>
      );
    }

    return (
      <Box>
        <TextField
          label="Search ..."
          variant="outlined"
          size="small"
          fullWidth
          margin="dense"
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
        />
        <Box sx={paneStyle(size)}>
          {!options.length && (
            <Typography
              variant="caption"
              sx={{ p: 2, display: 'block', color: 'text.secondary' }}
            >
              No sector of this division matches &quot;{filter}&quot;.
            </Typography>
          )}
          <FormGroup sx={{ px: 1 }}>
            {options.map((option) => (
              <Box key={option.iri} sx={{ display: 'flex', alignItems: 'center' }}>
                <FormControlLabel
                  sx={{ flexGrow: 1 }}
                  control={
                    <Checkbox
                      size="small"
                      color="default"
                      checked={selectedIris.has(String(option.iri))}
                      onChange={() => toggleOption(option)}
                    />
                  }
                  label={<Typography variant="body2">{nodeLabel(option)}</Typography>}
                />
                <Tooltip
                  placement="top"
                  title={
                    <Typography variant="caption" color="inherit">
                      {option.definition || 'No definition in the OEO.'}
                    </Typography>
                  }
                >
                  <InfoOutlinedIcon sx={{ color: '#708696', fontSize: '18px', mr: 1 }} />
                </Tooltip>
              </Box>
            ))}
          </FormGroup>
        </Box>
      </Box>
    );
  };

  return (
    <Box>
      <Grid container spacing={2}>
        <Grid item xs={12} md={5}>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            Sector divisions of this bundle
          </Typography>
          <Box sx={paneStyle(size)}>
            <List dense disablePadding>
              {rows.map((row) => {
                const key = String(row.iri || row.class);
                const isOther = row.kind === 'tree';
                return (
                  <ListItemButton
                    key={key}
                    selected={key === String(activeIri)}
                    onClick={() => {
                      setActiveIri(key);
                      setFilter('');
                    }}
                    divider
                  >
                    <ListItemText
                      primary={
                        <Typography variant="body2">
                          {isOther ? 'Other (all OEO sectors)' : row.label || row.name}
                        </Typography>
                      }
                      secondary={
                        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                          {countSelected(row)} of {countOptions(row)} selected
                        </Typography>
                      }
                    />
                  </ListItemButton>
                );
              })}
            </List>
          </Box>
        </Grid>
        <Grid item xs={12} md={7}>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            {activeRow
              ? activeRow.kind === 'tree'
                ? 'Sectors from the OEO sector hierarchy'
                : `Sectors of ${activeRow.label || activeRow.name}`
              : 'Sectors'}
          </Typography>
          {renderDetail()}
        </Grid>
      </Grid>

      <Box sx={{ mt: 1 }}>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          Selected sectors ({selectedSectors.length})
        </Typography>
        <Box>
          {selectedSectors.map((sector) => (
            <Chip
              key={String(sector.class)}
              size="small"
              variant="outlined"
              label={nodeLabel(sector)}
              onDelete={() => removeSector(sector)}
              sx={{ m: 0.5 }}
            />
          ))}
        </Box>
      </Box>
    </Box>
  );
}
