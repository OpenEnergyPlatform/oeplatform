// src/components/Scenario.jsx
import React, { useState, useEffect, useCallback } from "react";
import { Grid, Box, Typography, TextField, IconButton, Autocomplete } from "@mui/material";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import AddIcon from "@mui/icons-material/Add";
import uuid from "react-uuid";
import CustomAutocomplete from "./customAutocomplete.jsx";
import CustomAutocompleteWithoutAddNew from "./customAutocompleteWithoutAddNew.jsx";
import CustomTreeViewWithCheckBox from "./customTreeViewWithCheckbox.jsx";
import HtmlTooltip from "../styles/oep-theme/components/tooltipStyles";
import BundleScenariosGridItem from "../styles/oep-theme/components/editBundleScenariosForms.jsx";
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

  // Handlers for input/output dataset arrays
  const addInputDatasetItem = () =>
    setScenariosInputDatasetsObj((prev) => [
      ...prev,
      { key: uuid(), idx: prev.length, value: { label: "", url: "" } },
    ]);
  const removeInputDataset = (key) => {
    const filtered = scenariosInputDatasetsObj.filter((e) => e.key !== key);
    setScenariosInputDatasetsObj(filtered);
    scenariosInputDatasetsHandler(filtered, data.id);
  };
  const updateInputDatasetName = (value, key, index) => {
    setScenariosInputDatasetsObj((prev) => {
      const copy = [...prev];
      // prevent duplicates
      if (
        copy.some(
          (d, i) =>
            i !== index &&
            (d.value.label === value.label || d.value.url === value.url)
        )
      ) {
        console.warn("Duplicate dataset detected. Update aborted.");
        return prev;
      }
      copy[index] = { key, idx: index, value };
      scenariosInputDatasetsHandler(copy, data.id);
      return copy;
    });
  };

  const addOutputDatasetItem = () =>
    setScenariosOutputDatasetsObj((prev) => [
      ...prev,
      { key: uuid(), idx: prev.length, value: { label: "", url: "" } },
    ]);
  const removeOutputDataset = (key) => {
    const filtered = scenariosOutputDatasetsObj.filter((e) => e.key !== key);
    setScenariosOutputDatasetsObj(filtered);
    scenariosOutputDatasetsHandler(filtered, data.id);
  };
  const updateOutputDatasetName = (value, key, index) => {
    setScenariosOutputDatasetsObj((prev) => {
      const copy = [...prev];
      if (
        copy.some(
          (d, i) =>
            i !== index &&
            (d.value.label === value.label || d.value.url === value.url)
        )
      ) {
        console.warn("Duplicate dataset detected. Update aborted.");
        return prev;
      }
      copy[index] = { key, idx: index, value };
      scenariosOutputDatasetsHandler(copy, data.id);
      return copy;
    });
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
    <Typography variant="body2">
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
              value={data.name}
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
              value={data.acronym}
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
              value={data.abstract}
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
              handler={(list, nodes) =>
                scenarioDescriptorHandler(list, nodes, data.id)
              }
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

        {/* Input datasets */}
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Input dataset(s)"
          tooltipText="Endogenous data is a data item whose quantity..."
          hrefLink="https://openenergyplatform.org/ontology/oeo/OEO_00000364"
          TooltipComponent={HtmlTooltip}
          customSpan={
            <IconButton color="primary" size="small" onClick={addInputDatasetItem}>
              <AddIcon />
            </IconButton>
          }
          renderField={() =>
            scenariosInputDatasetsObj.map((item, idx) => (
              <Grid
                container
                spacing={2}
                alignItems="center"
                key={item.key}
                sx={{ mb: 1 }}
              >
                <Grid item xs={11}>
                  <Autocomplete
                    disableCloseOnSelect
                    options={dataTableList}
                    getOptionLabel={(o) => o.label}
                    value={dataTableList.find((o) => o.label === item.value.label) || null}
                    onChange={(_, val) =>
                      updateInputDatasetName(val, item.key, idx)
                    }
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Name"
                        size="small"
                        variant="outlined"
                        fullwidth
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={1}>
                  <IconButton
                    color="primary"
                    size="small"
                    onClick={() => removeInputDataset(item.key)}
                  >
                    <DeleteOutlineIcon />
                  </IconButton>
                </Grid>
              </Grid>
            ))
          }
        />

        {/* Output datasets */}
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Output dataset(s)"
          tooltipText="Exogenous data is a data item whose quantity..."
          hrefLink="https://openenergyplatform.org/ontology/oeo/OEO_00030030"
          TooltipComponent={HtmlTooltip}
          customSpan={
            <IconButton color="primary" size="small" onClick={addOutputDatasetItem}>
              <AddIcon />
            </IconButton>
          }
          renderField={() =>
            scenariosOutputDatasetsObj.map((item, idx) => (
              <Grid
                container
                spacing={2}
                alignItems="center"
                key={item.key}
                sx={{ mb: 1 }}
              >
                <Grid item xs={11}>
                  <Autocomplete
                    disableCloseOnSelect
                    options={dataTableList}
                    getOptionLabel={(o) => o.label}
                    value={dataTableList.find((o) => o.label === item.value.label) || null}
                    onChange={(_, val) =>
                      updateOutputDatasetName(val, item.key, idx)
                    }
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Name"
                        size="small"
                        variant="outlined"
                        fullwidth
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={1}>
                  <IconButton
                    color="primary"
                    size="small"
                    onClick={() => removeOutputDataset(item.key)}
                  >
                    <DeleteOutlineIcon />
                  </IconButton>
                </Grid>
              </Grid>
            ))
          }
        />
      </Grid>
    </Typography>
  );
}
