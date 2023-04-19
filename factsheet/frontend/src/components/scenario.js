import React, { PureComponent, Fragment, useState, useEffect } from "react";
import { Route } from 'react-router-dom';
import Grid from '@mui/material/Grid';
import TextField from '@mui/material/TextField';
import CustomAutocomplete from './customAutocomplete.js';
import Typography from '@mui/material/Typography';
import Fab from '@mui/material/Fab';
import AddIcon from '@mui/icons-material/Add';
import Autocomplete from '@mui/material/Autocomplete';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import uuid from "react-uuid";
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import EmojiObjectsIcon from '@mui/icons-material/EmojiObjects';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import DialogContentText from '@mui/material/DialogContentText';
import Button from '@mui/material/Button';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';

//import oedb_iris from '../data/datasets_iris.json';
//import oedb_names from '../data/datasets_names.json';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

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
    scenariosKeywordsHandler,
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
    HandleAddNNewScenarioYear
   } = props;
    function createData(
      Model: string,
      Scenario: number,
      Region: number,
      Year: number,
      Capacity: number,
    ) {
      return { Model, Scenario, Region, Year, Capacity };
    }
    const rows = [
      createData('dea_technology_data_generation', 'WEM', 'Germany', 2015, 4.0),
      createData('dea_technology_data_generation', 'WAM', 'Germany', 2015, 4.3),
      createData('dea_technology_data_generation', 'WEM', 'Europe', 2015, 6.0),
      createData('dea_technology_data_generation', 'WAM', 'Europe', 2020, 4.3),
      createData('dea_technology_data_generation', 'WAM', 'Europe', 2020, 3.9),
    ];

    const [scenariosInputDatasetsObj, setScenariosInputDatasetsObj] = useState(data.input_datasets);
    const [scenariosOutputDatasetsObj, setScenariosOutputDatasetsObj] = useState(data.output_datasets);
    const [openRemoveddDialog, setOpenRemovedDialog] = useState(false);
    const [value, setValue] = React.useState(0);


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
      setScenariosInputDatasetsObj(prevScenariosInputDatasetsObj => [...prevScenariosInputDatasetsObj, { key: uid, idx: scenariosInputDatasetsObj.length, value: { label: '', iri: '' } } ]);
    };

    const updateInputDatasetIRI = (value, key, index) => {
      const updateScenariosInputDatasetsObj = scenariosInputDatasetsObj;
      updateScenariosInputDatasetsObj[index].value.label = value.name;
      updateScenariosInputDatasetsObj[index].value.iri = value.label;
      updateScenariosInputDatasetsObj[index].idx = index;
      updateScenariosInputDatasetsObj[index].key = key;
      setScenariosInputDatasetsObj(updateScenariosInputDatasetsObj);
      scenariosInputDatasetsHandler(updateScenariosInputDatasetsObj, data.id);
    };

    const updateInputDatasetName = (value, key, index) => {
      const updateScenariosInputDatasetsObj = scenariosInputDatasetsObj;
      updateScenariosInputDatasetsObj[index].value.label = value.label;
      updateScenariosInputDatasetsObj[index].value.iri = value.iri;
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
      setScenariosOutputDatasetsObj(prevScenariosOutputDatasetsObj => [...prevScenariosOutputDatasetsObj, { key: uid, idx: scenariosOutputDatasetsObj.length, value: { label: '', iri: '' } } ]);
    };

    const updateOutputDatasetIRI = (value, key, index) => {
      const updateScenariosOutputDatasetsObj = scenariosOutputDatasetsObj;
      updateScenariosOutputDatasetsObj[index].value.label = value.name;
      updateScenariosOutputDatasetsObj[index].value.iri = value.label;
      updateScenariosOutputDatasetsObj[index].idx = index;
      updateScenariosOutputDatasetsObj[index].key = key;
      setScenariosOutputDatasetsObj(updateScenariosOutputDatasetsObj);
      scenariosOutputDatasetsHandler(updateScenariosOutputDatasetsObj, data.id);
      };

    const updateOutputDatasetName = (value, key, index) => {
      const updateScenariosOutputDatasetsObj = scenariosOutputDatasetsObj;
      updateScenariosOutputDatasetsObj[index].value.label = value.label;
      updateScenariosOutputDatasetsObj[index].value.iri = value.iri;
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


    const options_db_names = ['oedb_iris'];
    const options_db_iris = ['oedb_names'];

    const [, updateState] = React.useState();
    const forceUpdate = React.useCallback(() => updateState({}), []);

    const handleRemoveScenario = () => {
      removeScenario(data.id);
      forceUpdate();
    }

    console.log(data);


    const mapping = 
          "@prefix rr: <http://www.w3.org/ns/r2rml#>. \n \
          @prefix oeo: <http://openenergy-platform.org/ontology/oeo/>. \n \
          <#Mapping> \n \
          rr:logicalTable [ \n \
            rr:tableName 'my_csv_file' \n \
          ]; \n \
          rr:subjectMap [ \n \
            rr:class oeo:PowerPlant ; \n \
            rr:template 'http://oeo.org/plants/{region}/{year}/{model}/{scenario}' ; \n \
            rr:termType rr:IRI ; \n \
            rr:column 'region' ; \n \
            rr:column 'year' ; \n \
            rr:column 'model' ; \n \
            rr:column 'scenario' ; \n \
          ]; \n \
          rr:predicateObjectMap [ \n \
            rr:predicate oeo:hasCapacity ; \n \
            rr:objectMap [ \n \
              rr:datatype xsd:double ; \n \
              rr:column 'capacity' ; \n \
            ]; \n \
          ]."


  return (
      <Grid container
            direction="row"
            justifyContent="space-between"
            alignItems="center"
      >
          <Grid item xs={12} style={{ textAlign: 'right', marginBottom: '30px' }}>
            <Dialog
              fullWidth
              maxWidth="lg"
              open={openRemoveddDialog}
              onClose={handleClickOpenRemovedDialog}
              aria-labelledby="responsive-dialog-title"
            >
              <DialogTitle>
                <b>Align your data to Open Energy Knowledge Graph</b>
              </DialogTitle>
              <DialogContent style={{ height:'700px' }}>
                <DialogContentText>
                  <div>
                    <b>
                    Wind_turbine_domestic_lod_geoss_tp_oeo
                    </b>
                    <TableContainer component={Paper}>
                          <Table sx={{ minWidth: 650 }} size="small" aria-label="a dense table">
                            <TableHead>
                              <TableRow>
                                <TableCell>Model</TableCell>
                                <TableCell align="right">Scenario</TableCell>
                                <TableCell align="right">Region</TableCell>
                                <TableCell align="right">Year</TableCell>
                                <TableCell align="right">Generating capacity (MW)</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {rows.map((row) => (
                                <TableRow
                                  key={row.name}
                                  sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                                >
                                  <TableCell component="th" scope="row">
                                    {row.Model}
                                  </TableCell>
                                  <TableCell align="right">{row.Scenario}</TableCell>
                                  <TableCell align="right">{row.Region}</TableCell>
                                  <TableCell align="right">{row.Year}</TableCell>
                                  <TableCell align="right">{row.Capacity}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                    <Box sx={{ width: '100%' }}>
                    <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                      <Tabs value={value} onChange={handleChange} aria-label="basic tabs example">
                        <Tab label="R2RML mapping" {...a11yProps(0)} />
                        <Tab label="Wizard" {...a11yProps(1)} />
                        <Tab label="Visual mapping" {...a11yProps(2)} />
                      </Tabs>
                    </Box>
                      <TabPanel value={value} index={0}>
                        <TextField style={{ width: '100%', Margin: '10px',  backgroundColor:'#FCFCFC' }} label="" variant="outlined" multiline rows={15} maxRows={50} value={mapping}/>
                      </TabPanel>
                      <TabPanel value={value} index={1}>
                        Wizard
                      </TabPanel>
                      <TabPanel value={value} index={2}>
                        Visual
                      </TabPanel>
                    </Box>
                  </div>
                </DialogContentText>
              </DialogContent>
              <DialogActions>
                <Button variant="contained" color="success" >
                  Save
                </Button>
                <Button variant="contained" onClick={handleClickCloseRemovedDialog}  >
                Cancel
                </Button>
              </DialogActions>
            </Dialog>
            <Fab color="primary" size="small" aria-label="upload picture" component="label" disabled>
              <ContentCopyIcon />
            </Fab>
            <Fab style={{ 'marginLeft': '5px' }} color="error" size="small" aria-label="upload picture" component="label" onClick={handleRemoveScenario} >
              <DeleteOutlineIcon />
            </Fab>
          </Grid>
          <Grid item xs={6} style={{ marginBottom: '30px' }}>
            <TextField size="small" variant='standard' style={{  width: '95%',  backgroundColor:'#FCFCFC' }} id="outlined-basic" label="What is the name of this scenario?" name={'name_' + data.id} key={'name_' + data.id} onChange={handleScenariosInputChange} value={data.name} />
          </Grid>
          <Grid item xs={6} style={{ marginBottom: '30px' }}>
            <TextField size="small" variant='standard' style={{  width: '95%',  backgroundColor:'#FCFCFC' }} id="outlined-basic" label="Please provide a unique acronym for this scenario." name={'acronym_' + data.id} key={'acronym_' + data.id} onChange={handleScenariosInputChange} value={data.acronym} />
          </Grid>
          <Grid item xs={12} style={{ marginTop: '0px' }}>
            <TextField size="small" variant='standard' style={{ width: '97%', MarginBottom: '10px', MarginTop: '20px',  backgroundColor:'#FCFCFC' }} id="outlined-basic" label="What is the storyline of this scenario? (max 400 characters)" multiline rows={4} maxRows={8} name={'abstract_' + data.id} key={'abstract_' + data.id} onChange={handleScenariosInputChange} value={data.abstract} />
          </Grid>
          <Grid item xs={5} style={{ marginTop: '15px', marginBottom: '10px' }}>
            <CustomAutocomplete  width="95%" type="spatial region" editHandler={HandleEditRegion} addNewHandler={HandleAddNewRegion}  showSelectedElements={true} selectedElements={data.regions} manyItems optionsSet={scenarioRegion} kind='Which spatial regions does this scenario focus on (study regions)?' handler={(e) => handleScenariosAutoCompleteChange(e, 'regions', data.id)} />
          </Grid>
          <Grid item xs={4} style={{  marginTop: '15px', marginBottom: '10px' }}>
           <CustomAutocomplete  width="95%" type="interacting region"  editHandler={HandleEditInteractingRegion} addNewHandler={HandleAddNewInteractingRegion} showSelectedElements={true} selectedElements={data.interacting_regions} manyItems optionsSet={scenarioInteractingRegion} kind='Are there other, interacting regions considered?' handler={(e) => handleScenariosAutoCompleteChange(e, 'interacting_regions', data.id)}/>
          </Grid>
          <Grid item xs={3} style={{  marginTop: '15px', marginBottom: '10px' }}>
            <CustomAutocomplete  width="95%" type="scenario year" editHandler={HandleEditScenarioYear} addNewHandler={HandleAddNNewScenarioYear} showSelectedElements={true} selectedElements={data.scenario_years} manyItems optionsSet={scenarioYears} kind='Which scenario years are considered?' handler={(e) => handleScenariosAutoCompleteChange(e, 'scenario_years', data.id)}  />
          </Grid>
          <Grid item xs={12} style={{ marginBottom: '15px', 'padding': '20px', width: '100%', border: '1px solid #cecece', width: '100%', borderRadius: '2px', backgroundColor:'#FCFCFC' }}>
            <Typography variant="subtitle1" gutterBottom style={{ marginTop:'10px', marginBottom:'5px' }}>
              What additional keywords describe your scenario?
            </Typography>
              <div>
               <FormGroup>
                  <div>
                    <FormControlLabel control={<Checkbox color="default" />} checked={data.keywords.includes("100% renewables")} onChange={scenarioKeywordsHandler} label="100% renewables" name={"100% renewables_" + data.id} />
                    <FormControlLabel control={<Checkbox color="default" />} checked={data.keywords.includes("acceptance")} onChange={scenarioKeywordsHandler} label="acceptance" name={"acceptance_" + data.id} />
                    <FormControlLabel control={<Checkbox color="default" />} checked={data.keywords.includes("sufficiency")} onChange={scenarioKeywordsHandler} label="sufficiency" name={"sufficiency_" + data.id} />
                    <FormControlLabel control={<Checkbox color="default" />} checked={data.keywords.includes("negative emissionen")} onChange={scenarioKeywordsHandler} label="negative emissionen" name={"negative emissionen_" + data.id} />
                    <FormControlLabel control={<Checkbox color="default" />} checked={data.keywords.includes("grid restrictions")} onChange={scenarioKeywordsHandler} label="grid restrictions" name={"grid restrictions_" + data.id} />
                    <FormControlLabel control={<Checkbox color="default" />} checked={data.keywords.includes("grid / infrastructure extension")} onChange={scenarioKeywordsHandler} label="grid / infrastructure extension" name={"grid / infrastructure extension_" + data.id} />
                  </div> 
               </FormGroup>
             </div>
         </Grid>
          <Grid
            container
            direction="row"
            justifyContent="space-between"
            alignItems="center"
            style={{ marginTop: '10px', 'padding': '20px', 'width': '100%', 'border':'1px solid #cecece', 'borderRadius': '2px', 'backgroundColor':'#FCFCFC' }}
          >
          <Grid item xs={12} >
            <Typography variant="subtitle1" gutterBottom style={{ marginTop:'10px', marginBottom:'10px' }}>
              Input dataset(s):
            </Typography>
          </Grid>
          {Object.keys(scenariosInputDatasetsObj).length > 0 &&  scenariosInputDatasetsObj.map((item, index) =>
            <Grid container xs={12} direction="row" >
              <Grid item xs={4} style={{ marginTop: '10px' }}>
                <Autocomplete
                  disableCloseOnSelect
                  options={options_db_names}
                  sx={{ width: '100%' }}
                  renderInput={(params) => <TextField {...params} label="Name" size="small"  variant='standard' />}
                  onChange={(event, value) => updateInputDatasetName(value, item.key, index)}
                  value={item.value.label}
                  size="small"
                  variant='standard'
                />
              </Grid>
              <Grid item xs={1} style={{ marginTop: '5px', textAlign: 'center' }}>
                <Typography variant="subtitle1" gutterBottom style={{ marginTop:'20px', marginBottom:'10px' }}>
                  OR
                </Typography>
              </Grid>
              <Grid item xs={6} style={{ marginTop: '10px' }}>
                <Autocomplete
                  disableCloseOnSelect
                  options={options_db_iris}
                  sx={{ width: '95%' }}
                  renderInput={(params) => <TextField {...params} label="IRI" size="small"  variant='standard' />}
                  onChange={(event, value) => updateInputDatasetIRI(value, item.key, index)}
                  value={ item.value.iri}
                />
              </Grid>
              <Grid item xs={1} style={{ marginTop: '20px' }}>
                <Fab
                  color="error"
                  aria-label="add"
                  size="small"
                  onClick={() => removeInputDataset(item.key, data.index)}
                  sx={{ transform: 'scale(0.8)' }}
                >
                  <DeleteOutlineIcon />
                </Fab>
                <Fab
                  color="success"
                  size="small"
                  sx={{ transform: 'scale(0.8)' }}
                  onClick={handleClickOpenRemovedDialog}
                  // disabled
                >
                  <EmojiObjectsIcon />
                </Fab>
              </Grid>
            </Grid>)
        }
        <Grid item xs={12} style={{'textAlign': 'left', marginTop: '15px' }}>
          <Fab
          color="primary"
          aria-label="add"
          size="small"
          onClick={() => addInputDatasetItem(uuid())}
          >
          <AddIcon />
          </Fab>
        </Grid>
        </Grid>

        <Grid
          container
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          style={{ marginTop: '30px', padding: '20px', border: '1px solid #cecece', width: '100%', borderRadius: '2px',  backgroundColor:'#FCFCFC' }}
        >

          <Grid item xs={12} >
            <Typography variant="subtitle1" gutterBottom style={{ marginTop:'10px', marginBottom:'10px' }}>
              Output dataset(s):
            </Typography>
          </Grid>

          {Object.keys(scenariosOutputDatasetsObj).length > 0 && scenariosOutputDatasetsObj.map((item, index) =>
            <Grid container xs={12} direction="row" >
              <Grid item xs={4} style={{ marginTop: '10px' }}>
                <Autocomplete
                  disableCloseOnSelect
                  options={options_db_names}
                  sx={{ width: '100%' }}
                  renderInput={(params) => <TextField {...params} label="Name" size="small"  variant='standard'/>}
                  onChange={(event, value) => updateOutputDatasetName(value, item.key, index)}
                  value={item.value.label}
                />
              </Grid>
              <Grid item xs={1} style={{ marginTop: '15px', textAlign: 'center' }}>
                <Typography variant="subtitle1" gutterBottom style={{ marginTop:'10px', marginBottom:'10px' }}>
                  OR
                </Typography>
              </Grid>
              <Grid item xs={6} style={{ marginTop: '10px' }}>
                <Autocomplete
                  disableCloseOnSelect
                  options={options_db_iris}
                  sx={{ width: '95%' }}
                  renderInput={(params) => <TextField {...params} label="IRI" size="small"  variant='standard'/>}
                  onChange={(event, value) => updateOutputDatasetIRI(value, item.key, index)}
                  value={item.value.iri}
                />
              </Grid>
              <Grid item xs={1} style={{ marginTop: '20px' }}>
                <Fab
                  color="error"
                  aria-label="add"
                  size="small"
                  onClick={() => removeOutputDataset(item.key, data.index)}
                  sx={{  transform: 'scale(0.8)' }}
                >
                  <DeleteOutlineIcon />
                </Fab>
                <Fab
                  color="success"
                  size="small"
                  sx={{ transform: 'scale(0.8)' }}
                  // disabled
                >
                  <EmojiObjectsIcon />
                </Fab>
              </Grid>
            </Grid>
          )}

          <Grid item xs={12} style={{'textAlign': 'left', marginTop: '20px' }}>
            <Fab
            color="primary"
            aria-label="add"
            size="small"
            onClick={() => addOutputDatasetItem(uuid())}
            >
            <AddIcon />
            </Fab>
          </Grid>

        </Grid>
      </Grid>

  );
}

