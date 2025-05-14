// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani>
// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani>
// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani>
// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien>
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
//
// SPDX-License-Identifier: MIT

import React, { PureComponent, Fragment, useState, useEffect } from "react";
import { Route } from 'react-router-dom';
import Grid from '@mui/material/Grid';
import TextField from '@mui/material/TextField';
import CustomAutocomplete from './customAutocomplete.js';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import Autocomplete from '@mui/material/Autocomplete';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import uuid from "react-uuid";
import Box from '@mui/material/Box';
import CustomTreeViewWithCheckBox from './customTreeViewWithCheckbox.js';
import CustomAutocompleteWithoutAddNew from './customAutocompleteWithoutAddNew.js';
import HtmlTooltip from '../styles/oep-theme/components/tooltipStyles.js'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { styled } from '@mui/material/styles';
import IconButton from '@mui/material/IconButton';
import LCC from '../data/countries.json';
import { makeStyles, Theme } from '@material-ui/core/styles';
import BundleScenariosGridItem from '../styles/oep-theme/components/editBundleScenariosForms.js';
import axios from 'axios';
import CSRFToken from './csrfToken';
import conf from "../conf.json";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const getNodeIds = (nodes) => {
  let ids = [];

  nodes?.forEach(({ value, children }) => {
    ids = [...ids, value, ...getNodeIds(children)];
  });
  return ids;
};

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          <Typography>{children}</Typography>
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `simple-tab-${index}`,
    'aria-controls': `simple-tabpanel-${index}`,
  };
}

export default function Scenario(props) {
  const {
    data,
    handleScenariosInputChange,
    handleScenariosAutoCompleteChange,
    scenariosInputDatasetsHandler,
    scenariosOutputDatasetsHandler,
    removeScenario,
    scenarioRegion,
    scenarioInteractingRegion,
    scenarioYears,
    scenarioKeywordsHandler,
    HandleEditRegion,
    HandleAddNewRegion,
    HandleEditInteractingRegion,
    HandleAddNewInteractingRegion,
    HandleEditScenarioYear,
    HandleAddNNewScenarioYear,
    descriptors,
    scenarioDescriptorHandler
  } = props;

  const [scenariosInputDatasetsObj, setScenariosInputDatasetsObj] = useState(data.input_datasets);
  const [scenariosOutputDatasetsObj, setScenariosOutputDatasetsObj] = useState(data.output_datasets);


  const [openRemoveddDialog, setOpenRemovedDialog] = useState(false);
  const [value, setValue] = React.useState(0);

  const [expandedDesciptorList, setExpandedDesciptorList] = useState([]);

  const [dataTableList, setDataTableList] = useState([]);

  const findNestedObj = (entireObj, keyToFind, valToFind) => {
    let foundObj;
    JSON.stringify(entireObj, (_, nestedValue) => {
      if (nestedValue && nestedValue[keyToFind] === valToFind) {
        foundObj = nestedValue;
      }
      return nestedValue;
    });
    return foundObj;
  };

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  const handleClickOpenRemovedDialog = () => {
    setOpenRemovedDialog(true);
  };

  const handleClickCloseRemovedDialog = () => {
    setOpenRemovedDialog(false);
  };
  const addInputDatasetItem = uid => {
    setScenariosInputDatasetsObj(prevScenariosInputDatasetsObj => [...prevScenariosInputDatasetsObj, { key: uid, idx: scenariosInputDatasetsObj.length, value: { label: '', url: '' } }]);
  };


  const updateInputDatasetName = (element, key, index) => {
    const updateScenariosInputDatasetsObj = [...scenariosInputDatasetsObj]; // Create a copy to avoid mutating state directly
  
    // Check if the dataset is already present
    const isDuplicate = updateScenariosInputDatasetsObj.some((dataset, idx) => {
      return (dataset.value.label === element.label || dataset.value.url === element.url) && idx !== index;
    });
  
    if (isDuplicate) {
      console.warn("Duplicate dataset detected. Update aborted.");
      return; // Exit the function to prevent updating with duplicate data
    }
  
    // Proceed with the update
    updateScenariosInputDatasetsObj[index].value.label = element.label;
    updateScenariosInputDatasetsObj[index].value.url = element.url;
    updateScenariosInputDatasetsObj[index].idx = index;
    updateScenariosInputDatasetsObj[index].key = key;
  
    setScenariosInputDatasetsObj(updateScenariosInputDatasetsObj);
    scenariosInputDatasetsHandler(updateScenariosInputDatasetsObj, data.id);
  };
  
  const removeInputDataset = (uid, idx) => {
    const updateScenariosInputDatasetsObj = scenariosInputDatasetsObj.filter(e => e.key != uid);
    setScenariosInputDatasetsObj(updateScenariosInputDatasetsObj);
    scenariosInputDatasetsHandler(updateScenariosInputDatasetsObj, data.id);
  };

  const addOutputDatasetItem = uid => {
    setScenariosOutputDatasetsObj(prevScenariosOutputDatasetsObj => [...prevScenariosOutputDatasetsObj, { key: uid, idx: scenariosOutputDatasetsObj.length, value: { label: '', url: '' } }]);
  };


  const updateOutputDatasetName = (value, key, index) => {
    const updateScenariosOutputDatasetsObj = [...scenariosOutputDatasetsObj]; // Create a copy to avoid mutating state directly
  
    // Check if the dataset is already present
    const isDuplicate = updateScenariosOutputDatasetsObj.some((dataset, idx) => {
      return (dataset.value.label === value.label || dataset.value.url === value.url) && idx !== index;
    });
  
    if (isDuplicate) {
      console.warn("Duplicate dataset detected. Update aborted.");
      return; // Exit the function to prevent updating with duplicate data
    }
  
    // Proceed with the update
    updateScenariosOutputDatasetsObj[index].value.label = value.label;
    updateScenariosOutputDatasetsObj[index].value.url = value.url;
    updateScenariosOutputDatasetsObj[index].idx = index;
    updateScenariosOutputDatasetsObj[index].key = key;
    setScenariosOutputDatasetsObj(updateScenariosOutputDatasetsObj);
    scenariosOutputDatasetsHandler(updateScenariosOutputDatasetsObj, data.id);
  };

  const removeOutputDataset = (uid, idx) => {
    const updateScenariosOutputDatasetsObj = scenariosOutputDatasetsObj.filter(e => e.key != uid);
    setScenariosOutputDatasetsObj(updateScenariosOutputDatasetsObj);
    scenariosOutputDatasetsHandler(updateScenariosOutputDatasetsObj, data.id);
  };


  const expandDescriptorsHandler = (expandedDescriptorList) => {
    const zipped = []
    expandedDescriptorList.map((v) => zipped.push({ "value": v, "label": v }));
    setExpandedDesciptorList(zipped);
  };



  const options_LCC = LCC.sort((a, b) => a.name.localeCompare(b.name));

  const [, updateState] = React.useState();
  const forceUpdate = React.useCallback(() => updateState({}), []);

  const handleRemoveScenario = () => {
    removeScenario(data.id);
    forceUpdate();
  }

  const useStyles = makeStyles((theme: Theme) => ({
    root: {
      flexGrow: 1,
      backgroundColor: theme.palette.background.paper,
    },
    tab: {
      background: '#e3eaef',
      '&.Mui-selected': {
        background: '#001c30e6',
        color: 'white'
      }
    },
  }));
  const classes = useStyles();
  const tabClasses = { root: classes.tab };

  const getDataTableList = async () => {
    const { data } = await axios.get(conf.toep + `api/v0/datasets/list_all/scenario/`, {
      headers: { 'X-CSRFToken': CSRFToken() }
    });
    return data;
  };

  useEffect(() => {
    getDataTableList().then((data) => {
      const tmp = [];
      data.map((item) => tmp.push({ 'url': item.url, 'label': `${item.human_readable_name ? item.human_readable_name : item.name}`,'name': item.name, 'id': item.id }));
      setDataTableList(tmp);
    });
  }, []);

  function handleInputChange(event, value) {
    console.log(value);
  }

  return (
    <Typography variant="body2">
      <Grid
        container
        direction="row"
        justifyContent="space-between"
        alignItems="start"
        spacing={2}
      >

        <BundleScenariosGridItem
          {...props}
          labelGridSize={11}
          fieldGridSize={1}
          renderField={() => (
            <IconButton 
                size="small"
                variant="outlined" 
                color="error" 
                style={{ marginLeft: '90%' }}
                onClick={handleRemoveScenario}>  
              <DeleteOutlineIcon />
            </IconButton>
          )}
        />

        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Name"
          tooltipText="A study is a project with the goal to investigate something."
          hrefLink="http://openenergy-platform.org/ontology/oeo/OEO_00020011"
          renderField={() => (
            <TextField
              size="small"
              variant='outlined'
              style={{ width: '100%' }}
              id="outlined-basic"
              label=""
              name={'name_' + data.id}
              key={'name_' + data.id}
              onChange={handleScenariosInputChange}
              value={data.name}
            />
          )}
          TooltipComponent={HtmlTooltip}
        />
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Acronym"
          tooltipText="An acronym is an abbreviation of the title by using the first letters of each part of the title."
          hrefLink="http://openenergy-platform.org/ontology/oeo/OEO_00000048"
          renderField={() => (
            <TextField
              size="small"
              variant='outlined'
              style={{ width: '100%' }}
              id="outlined-basic"
              label=""
              name={'acronym_' + data.id}
              key={'acronym_' + data.id}
              onChange={handleScenariosInputChange}
              value={data.acronym}
            />
          )}
          TooltipComponent={HtmlTooltip}
        />
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Abstract"
          tooltipText="A summary of the resource."
          hrefLink="https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#abstract"
          linkText="More info..."
          renderField={() => (
            <TextField
              size="small"
              variant='outlined'
              style={{ width: '100%' }}
              id="outlined-basic"
              label=""
              multiline
              rows={8}
              maxRows={14}
              name={'abstract_' + data.id}
              key={'abstract_' + data.id}
              onChange={handleScenariosInputChange}
              value={data.abstract}
            />
          )}
          TooltipComponent={HtmlTooltip}
        />
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Spatial regions"
          tooltipText="A study region is a spatial region that is under investigation and consists entirely of one or more subregions."
          hrefLink="http://openenergy-platform.org/ontology/oeo/OEO_00020032"
          renderField={() => (
            <CustomAutocompleteWithoutAddNew
              width="100%"
              showSelectedElements={true}
              optionsSet={options_LCC}
              kind=''
              handler={(e) => handleScenariosAutoCompleteChange(e, 'regions', data.id)}
              selectedElements={data.regions}
              noTooltip={true}
            />
          )}
          TooltipComponent={HtmlTooltip}
        />
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Interacting regions"
          tooltipText="An interacting region is a spatial region that interacts with a study region. It is part of a considered region, but not a study region."
          hrefLink="http://openenergy-platform.org/ontology/oeo/OEO_00020036"
          renderField={() => (
            <CustomAutocompleteWithoutAddNew
              width="100%"
              showSelectedElements={true}
              optionsSet={options_LCC}
              kind=''
              handler={(e) => handleScenariosAutoCompleteChange(e, 'interacting_regions', data.id)}
              selectedElements={data.interacting_regions}
              noTooltip={true}
            />
          )}
          /* <CustomAutocomplete  width="100%" type="interacting region"
           editHandler={HandleEditInteractingRegion}
            addNewHandler={HandleAddNewInteractingRegion}
             showSelectedElements={true}
             selectedElements={data.interacting_regions}
             manyItems optionsSet={scenarioInteractingRegion}
             kind='' handler={(e) => handleScenariosAutoCompleteChange(e, 'interacting_regions', data.id)}/> */
          TooltipComponent={HtmlTooltip}
        />
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Scenario years"
          tooltipText="A scenario year is a time step that has a duration of one year and is part of a scenario horizon."
          hrefLink="http://openenergy-platform.org/ontology/oeo/OEO_00020097"
          renderField={() => (
            <CustomAutocompleteWithoutAddNew
              width="100%"
              type="scenario year"
              showSelectedElements={true}
              selectedElements={data.scenario_years}
              manyItems 
              noTooltip
              optionsSet={scenarioYears}
              kind=''
              handler={(e) => handleScenariosAutoCompleteChange(e, 'scenario_years', data.id)}
            />
          )}
          TooltipComponent={HtmlTooltip}
        />
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Scenario type"
          tooltipText="A scenario is an information content entity that contains statements about a possible future development based on a coherent and internally consistent set of assumptions and their motivation."
          hrefLink="http://openenergy-platform.org/ontology/oeo/OEO_00000364"
          renderField={() => (
            <CustomTreeViewWithCheckBox
              showFilter={true}
              size="300px"
              checked={data.descriptors}
              expanded={getNodeIds(descriptors)}
              handler={(list, nodes, id) => scenarioDescriptorHandler(list, nodes, data.id)}
              expandedHandler={expandDescriptorsHandler}
              data={descriptors}
              title={""}
              toolTipInfo={['A scenario is an information content entity that contains statements about a possible future development based on a coherent and internally consistent set of assumptions and their motivation.', 'http://openenergy-platform.org/ontology/oeo/OEO_00000364']}
            />
          )}
          TooltipComponent={HtmlTooltip}
        />
        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Input dataset(s)"
          tooltipText="Endogenous data is a data item whose quantity value is determined by a model."
          hrefLink="http://openenergy-platform.org/ontology/oeo/OEO_00000364"
          customSpan={
            <span>
              <IconButton
                color="primary"
                aria-label="add"
                onClick={() => addInputDatasetItem(uuid())}
              >
                <AddIcon />
              </IconButton>
            </span>}
          renderField={() =>
            Object.keys(scenariosInputDatasetsObj).length > 0 &&  scenariosInputDatasetsObj.map((item, index) => (
              <Grid container direction="row" spacing={2} justifyContent="space-between" alignItems="start" style={{ marginBottom: '10px' }}>
                <Grid item xs={11} >
                  <Autocomplete
                    disableCloseOnSelect
                    options={dataTableList}
                    renderInput={(params) => <TextField {...params} label="Name" size="small" variant='outlined' />}
                    onChange={(event, value) => updateInputDatasetName(value, item.key, index)}
                    value={item.value.label}

                  />
                </Grid>
                <Grid item xs={1} >
                  <IconButton
                    color="primary"
                    aria-label="add"
                    onClick={() => removeInputDataset(item.key, data.index)}
                  >
                    <DeleteOutlineIcon />
                  </IconButton>
                </Grid>
              </Grid>
            ))
          }
          TooltipComponent={HtmlTooltip}
        />

        <BundleScenariosGridItem
          {...props}
          labelGridSize={3}
          fieldGridSize={9}
          spanValue="Output dataset(s)"
          tooltipText="Exogenous data is a data item whose quantity value is determined outside of a model and is imposed on a model."
          hrefLink="http://openenergy-platform.org/ontology/oeo/OEO_00030029"
          customSpan={
            <span>
              <IconButton
                color="primary"
                aria-label="add"
                onClick={() => addOutputDatasetItem(uuid())}
              >
                <AddIcon />
              </IconButton>
            </span>}
          renderField={() =>
            Object.keys(scenariosOutputDatasetsObj).length > 0 && scenariosOutputDatasetsObj.map((item, index) => (
              <Grid container direction="row" spacing={2} justifyContent="space-between" alignItems="start" style={{ marginBottom: '10px' }}>
                <Grid item xs={11} >
                  <Autocomplete
                    disableCloseOnSelect
                    options={dataTableList}
                    renderInput={(params) => <TextField {...params} label="name" size="small" variant='outlined' />}
                    onChange={(event, value) => updateOutputDatasetName(value, item.key, index)}
                    value={item.value.label}
                  />
                </Grid>
                <Grid item xs={1}>
                  <IconButton
                    color="primary"
                    aria-label="add"
                    onClick={() => removeOutputDataset(item.key, data.index)}
                  >
                    <DeleteOutlineIcon />
                  </IconButton>
                </Grid>
              </Grid>
            ))
          }
          TooltipComponent={HtmlTooltip}
        />
      </Grid>
    </Typography>
  );
}
