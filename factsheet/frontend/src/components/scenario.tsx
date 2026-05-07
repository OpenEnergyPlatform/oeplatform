// src/components/Scenario.jsx
import React, { useState, useEffect, useCallback } from "react";
import { Grid, Box, Typography, TextField, IconButton, Autocomplete } from "@mui/material";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import CustomAutocompleteWithoutAddNew from "./customAutocompleteWithoutAddNew.jsx";
import CustomTreeViewWithCheckBox from "./customTreeViewWithCheckbox.jsx";
import HtmlTooltip from "../styles/oep-theme/components/tooltipStyles";
import BundleScenariosGridItem from "../styles/oep-theme/components/editBundleScenariosForms.jsx";
import { getCheckedWithParents } from './scenarioBundleUtilityComponents/treeUtils';
import axios from "axios";
import CSRFToken from "./csrfToken.js";
import conf from "../conf.json";
import LCC from "../data/countries.json";



export default function Scenario(props) {
  const {
    data,
    handleScenariosInputChange,
    handleScenariosAutoCompleteChange,
    scenariosInputDatasetsHandler,
    scenariosOutputDatasetsHandler,
    removeScenario,
    scenarioYears,
    descriptors,
    scenarioDescriptorHandler,
    // …any other handlers you passed
  } = props;

  // Local state
  const [scenariosInputDatasetsObj, setScenariosInputDatasetsObj] = useState(data.input_datasets);
  const [scenariosOutputDatasetsObj, setScenariosOutputDatasetsObj] = useState(data.output_datasets);
  const [dataTableList, setDataTableList] = useState([]);

  // Fetch data table list
  useEffect(() => {
    axios
      .get(`${conf.toep}api/v0/datasets/list_all/scenario/`, {
        headers: { "X-CSRFToken": CSRFToken() },
      })
      .then((res) => {
        const list = res.data.map((item) => ({
          url: item.url,
          label: item.human_readable_name || item.name,
          name: item.name,
          id: item.id,
        }));
        setDataTableList(list);
      })
      .catch(console.error);
  }, []);

  // Utility to flatten tree IDs
  const getNodeIds = (nodes) =>
    nodes?.reduce(
      (acc, { value, children }) => [...acc, value, ...getNodeIds(children)],
      []
    ) || [];

  // Helper to handle multiselect changes for input/output datasets
  // It converts the simple array from Autocomplete back to your { key, value } structure
  const handleMultiselectChange = (newValue, type) => {
    // 1. Convert the Autocomplete array back to your app's structure
    const updatedStructure = newValue.map((item, index) => ({
      key: item.id ? `dataset_${item.id}` : `new_${Date.now()}_${index}`, // Maintain stable keys if possible
      idx: index, // Ensure idx is set
      value: item
    }));

    // 2. Update Local State AND Call the Backend/Parent Handler
    if (type === 'input') {
      setScenariosInputDatasetsObj(updatedStructure);

      // logic form old code: scenariosInputDatasetsHandler(copy, data.id);
      // ADD THIS LINE:
      if (typeof scenariosInputDatasetsHandler === 'function') {
        scenariosInputDatasetsHandler(updatedStructure, data.id);
      }

    } else {
      setScenariosOutputDatasetsObj(updatedStructure);

      // logic form old code: scenariosOutputDatasetsHandler(copy, data.id);
      // ADD THIS LINE:
      if (typeof scenariosOutputDatasetsHandler === 'function') {
        scenariosOutputDatasetsHandler(updatedStructure, data.id);
      }
    }
  };

  // Sorted country list
  const options_LCC = LCC.slice().sort((a, b) =>
    a.name.localeCompare(b.name)
  );

  // Remove scenario
  const handleRemoveScenario = useCallback(() => {
    removeScenario(data.id);
  }, [data.id, removeScenario]);

  return (
    <Typography component="div" variant="body2">
      <Grid container spacing={2}>
        {/* Delete Button */}
        <BundleScenariosGridItem
          {...props}
          labelGridSize={11}
          fieldGridSize={1}
          renderField={() => (
            <IconButton
              size="small"
              color="error"
              sx={{ ml: "auto" }}
              onClick={handleRemoveScenario}
            >
              <DeleteOutlineIcon />
            </IconButton>
          )}
        />

        {/* Name */}
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Name"
          tooltipText="A study is a project with the goal to investigate something."
          hrefLink="https://openenergyplatform.org/ontology/oeo/OEO_00020011"
          TooltipComponent={HtmlTooltip}
          renderField={() => (
            <TextField
              size="small"
              variant="outlined"
              fullWidth
              name={`name_${data.id}`}
              value={data.name || ""}
              onChange={handleScenariosInputChange}
            />
          )}
        />

        {/* Acronym */}
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Acronym"
          tooltipText="An acronym is an abbreviation of the title..."
          hrefLink="https://openenergyplatform.org/ontology/oeo/OEO_00000048"
          TooltipComponent={HtmlTooltip}
          renderField={() => (
            <TextField
              size="small"
              variant="outlined"
              fullWidth
              name={`acronym_${data.id}`}
              value={data.acronym || ""}
              onChange={handleScenariosInputChange}
            />
          )}
        />

        {/* Abstract */}
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Abstract"
          tooltipText="A summary of the resource."
          hrefLink="https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#abstract"
          TooltipComponent={HtmlTooltip}
          renderField={() => (
            <TextField
              size="small"
              variant="outlined"
              fullWidth
              multiline
              rows={8}
              name={`abstract_${data.id}`}
              value={data.abstract || ""}
              onChange={handleScenariosInputChange}
            />
          )}
        />

        {/* Spatial regions */}
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Spatial regions"
          tooltipText="A study region is a spatial region..."
          hrefLink="https://openenergyplatform.org/ontology/oeo/OEO_00020032"
          TooltipComponent={HtmlTooltip}
          renderField={() => (
            <CustomAutocompleteWithoutAddNew
              width="100%"
              showSelectedElements
              optionsSet={options_LCC}
              handler={(e) =>
                handleScenariosAutoCompleteChange(e, "regions", data.id)
              }
              selectedElements={data.regions}
              noTooltip
            />
          )}
        />

        {/* Interacting regions */}
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Interacting regions"
          tooltipText="An interacting region is part of a considered region..."
          hrefLink="https://openenergyplatform.org/ontology/oeo/OEO_00020036"
          TooltipComponent={HtmlTooltip}
          renderField={() => (
            <CustomAutocompleteWithoutAddNew
              width="100%"
              showSelectedElements
              optionsSet={options_LCC}
              handler={(e) =>
                handleScenariosAutoCompleteChange(
                  e,
                  "interacting_regions",
                  data.id
                )
              }
              selectedElements={data.interacting_regions}
              noTooltip
            />
          )}
        />

        {/* Scenario years */}
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Scenario years"
          tooltipText="A scenario year is a time step of one year..."
          hrefLink="https://openenergyplatform.org/ontology/oeo/OEO_00020097"
          TooltipComponent={HtmlTooltip}
          renderField={() => (
            <CustomAutocompleteWithoutAddNew
              width="100%"
              showSelectedElements
              optionsSet={scenarioYears}
              handler={(e) =>
                handleScenariosAutoCompleteChange(
                  e,
                  "scenario_years",
                  data.id
                )
              }
              selectedElements={data.scenario_years}
              noTooltip
            />
          )}
        />

        {/* Descriptors Tree */}
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Scenario type"
          tooltipText="A scenario is an information content entity..."
          hrefLink="https://openenergyplatform.org/ontology/oeo/OEO_00000364"
          TooltipComponent={HtmlTooltip}
          renderField={() => (
            <CustomTreeViewWithCheckBox
              showFilter
              size="300px"
              checked={data.descriptors}
              expanded={getNodeIds(descriptors)}
              handler={(list, nodes) => {
                // Calculate parents based on the user's selection ('list') and the full tree ('descriptors')
                const listWithParents = getCheckedWithParents(list, descriptors);

                // Pass the extended list to your existing handler
                scenarioDescriptorHandler(listWithParents, nodes, data.id);
              }}
              expandedHandler={(list) =>
                scenarioDescriptorHandler(list, null, data.id)
              }
              data={descriptors}
              title=""
              toolTipInfo={[
                "A scenario is an information content entity...",
                "https://openenergyplatform.org/ontology/oeo/OEO_00000364",
              ]}
            />
          )}
        />

        {/* Input datasets - MULTISELECT REFACTOR */}
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Input dataset(s)"
          tooltipText="Endogenous data is a data item whose quantity..."
          hrefLink="https://openenergyplatform.org/ontology/oeo/OEO_00000364"
          TooltipComponent={HtmlTooltip}
          // We no longer need the customSpan '+' button because multiselect allows adding infinitely
          customSpan={null}
          renderField={() => (
            <Autocomplete
              multiple
              disableCloseOnSelect
              id="input-datasets-autocomplete"
              options={dataTableList}
              getOptionLabel={(option) => option.label || ""}

              // 1. We transform your state {key, value} into a simple array [value, value] for MUI
              value={scenariosInputDatasetsObj
                .map((item) => dataTableList.find((o) => o.label === item.value.label))
                .filter(Boolean) // Filter out undefined to prevent crashes
              }

              // 2. When selection changes, we rebuild your state structure
              onChange={(_, newValue) => handleMultiselectChange(newValue, 'input')}

              renderInput={(params) => (
                <TextField
                  {...params}
                  variant="outlined"
                  label="Select Input Datasets"
                  placeholder="Search datasets..."
                  size="small"
                  fullWidth // corrected lowercase 'fullwidth' warning
                />
              )}
            />
          )}
        />

        {/* Output datasets - MULTISELECT REFACTOR */}
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Output dataset(s)"
          tooltipText="Exogenous data is a data item whose quantity..."
          hrefLink="https://openenergyplatform.org/ontology/oeo/OEO_00030030"
          TooltipComponent={HtmlTooltip}
          customSpan={null}
          renderField={() => (
            <Autocomplete
              multiple
              disableCloseOnSelect
              id="output-datasets-autocomplete"
              options={dataTableList}
              getOptionLabel={(option) => option.label || ""}

              // 1. Transform State -> View
              value={scenariosOutputDatasetsObj
                .map((item) => dataTableList.find((o) => o.label === item.value.label))
                .filter(Boolean)
              }

              // 2. Transform View -> State
              onChange={(_, newValue) => handleMultiselectChange(newValue, 'output')}

              renderInput={(params) => (
                <TextField
                  {...params}
                  variant="outlined"
                  label="Select Output Datasets"
                  placeholder="Search datasets..."
                  size="small"
                  fullWidth
                />
              )}
            />
          )}
        />
      </Grid>
    </Typography>
  );
}
