import React, { useState, useEffect } from 'react';
import Grid from '@mui/material/Grid';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import ForwardToInboxIcon from '@mui/icons-material/ForwardToInbox';
import TextField from '@mui/material/TextField';
import MailOutlineIcon from '@mui/icons-material/MailOutline';
import CustomSwap from './customSwapButton.js';
import CustomTabs from './customTabs.js';
import ShareIcon from '@mui/icons-material/Share';
import '../styles/App.css';
import CustomAutocomplete from './customAutocomplete.js';
import CustomAutocompleteWithAddNew from './customAutocompleteWithAddNew.js';
import VerticalTabs from './customVerticalTabs.js';
import Scenario from './scenario.js';
import CustomDatePicker from './customDatePicker.js'
import Typography from '@mui/material/Typography';
import AddBoxIcon from '@mui/icons-material/AddBox';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import axios from 'axios';
import { useLocation, useHistory, useNavigate } from 'react-router-dom'
import { Route, Routes, Link } from 'react-router-dom';
import dayjs from 'dayjs';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { DesktopDatePicker } from '@mui/x-date-pickers/DesktopDatePicker';
import { MobileDatePicker } from '@mui/x-date-pickers/MobileDatePicker';
import Stack from '@mui/material/Stack';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import Fab from '@mui/material/Fab';
import FileCopyIcon from '@mui/icons-material/FileCopyOutlined';
import IconButton from '@mui/material/IconButton';
import Checkbox from '@mui/material/Checkbox';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import { useRef } from "react";
import conf from "../conf.json";

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`vertical-tabpanel-${index}`}
      aria-labelledby={`vertical-tab-${index}`}
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

function Factsheet(props) {
  const location = useLocation();
  const { id, fsData } = props;
  const jsonld = require('jsonld');
  const [factsheetJSON, setFactsheetJSON] = useState({
    "@context": {
      "@base": "https://openenergy-platform.org/oekg/",
      "oeo": "https://openenergy-platform.org/ontology/oeo/",
      "foaf": "http://xmlns.com/foaf/0.1/",
      "dc": "http://purl.org/dc/elements/1.1/"
    },
    "@id": "KS-2050",
    "@type": "oeo:OEO_00010250",
    "foaf:name": "Klimaschutzszenario 2050",
    "dc:description": "The project develops a vision of the future in the form of three scenarios that meet the ambitious climate protection goals of the Federal Republic of Germany when considering all sectors and uses the national potential of renewable energies",
    "oeo:OEO_00000506": [],
    "oeo:OEO_00000505": [],
    "oeo:OEO_00000509": []
  });
  const [factsheetRDF, setFactsheetRDF] = useState({});
  const [factsheet, setFactsheet] = useState({});
  const [loading, setLoading] = useState(true);
  const [openOverView, setOpenOverView] = useState(false);
  const [openJSON, setOpenJSON] = useState(false);
  const [openTurtle, setOpenTurtle] = useState(false);
  const [openSavedDialog, setOpenSavedDialog] = useState(false);
  const [openUpdatedDialog, setOpenUpdatedDialog] = useState(false);
  const [openRemoveddDialog, setOpenRemovedDialog] = useState(false);
  const [mode, setMode] = useState("wizard");
  const [factsheetObject, setFactsheetObject] = useState({});
  const [factsheetName, setFactsheetName] = useState(id !== 'new' ? fsData.name : '');
  const [acronym, setAcronym] = useState(id !== 'new' ? fsData.acronym : '');
  const [studyName, setStudyName] = useState(id !== 'new' ? fsData.study_name : '');
  const [abstract, setAbstract] = useState(id !== 'new' ? fsData.abstract : '');
  const [selectedSectors, setSelectedSectors] = useState([]);
  const [selectedAuthors, setSelectedAuthors] = useState(id !== 'new' ? fsData.authors : []);
  const [selectedInstitution, setSelectedInstitution] = useState(id !== 'new' ? fsData.institution : []);
  const [selectedFundingSource, setSelectedFundingSource] = useState(id !== 'new' ? fsData.funding_source : []);
  const [selectedContactPerson, setselectedContactPerson] = useState(id !== 'new' ? fsData.contact_person : []);
  const [report_title, setReportTitle] = useState(id !== 'new' ? fsData.report_title : []);
  const [date_of_publication, setDateOfPublication] = useState(id !== 'new' ? fsData.date_of_publication : '2022-04-07');
  const [doi, setDOI] = useState(id !== 'new' ? fsData.doi : '');
  const [place_of_publication, setPlaceOfPublication] = useState(id !== 'new' ? fsData.place_of_publication : '');
  const [link_to_study, setLinkToStudy] = useState(id !== 'new' ? fsData.link_to_study : '');

  const [scenarios, setScenarios] = useState(id !== 'new' ? Object.keys(fsData.scenarios_name).length : 1);
  const [scenarioObject, setScenarioObject] = useState({});
  const [scenariosName, setScenariosName] = useState(id !== 'new' ? fsData.scenarios_name : {});
  const [scenariosAcronym, setScenariosAcronym] = useState(id !== 'new' ? fsData.scenarios_acronym : {});
  const [scenariosAbstract, setScenariosAbstract] = useState(id !== 'new' ? fsData.scenarios_abstract : {});

  const [selectedRegion, setSelectedRegion] = useState(id !== 'new' ? fsData.scenarios_region : {});
  const [selectedInteractingRegion, setSelectedInteractingRegion] = useState(id !== 'new' ? fsData.scenarios_interacting_region : {});
  const [selectedScenariosYears, setSelectedScenariosYears] = useState(id !== 'new' ? fsData.scenarios_years : {});
  const [selectedScenariosKeywords, setSelectedScenariosKeywords] = useState(id !== 'new' ? fsData.scenarios_keywords : {});

  const [selectedEnergyCarriers, setSelectedsetEnergyCarriers] = useState([]);
  const [selectedEnergyTransportation, setSelectedEnergyTransportation] = useState([]);
  const [selectedScenarioInputDatasetRegion, setSelectedScenarioInputDatasetRegion] = useState([]);
  const [selectedScenarioOutputDatasetRegion, setSelectedScenarioOutputDatasetRegion] = useState([]);

  const [scenarioAbstract, setScenarioAbstract] = useState('');
  const [scenarioAcronym, setScenarioAcronym] = useState('');
  const [scenarioInputDatasetName, setScenarioInputDatasetName] = useState('');
  const [scenarioOutputDatasetName, setScenarioOutputDatasetName] = useState('');
  const [scenarioInputDatasetIRI, setScenarioInputDatasetIRI] = useState('');
  const [scenarioOutputDatasetIRI, setScenarioOutputDatasetIRI] = useState('');
  const navigate = useNavigate();
  const handleSaveJSON = () => {
    //props.onChange(oekg);
    setOpenJSON(true);
  };

  const [scenarioTabValue, setScenarioTabValue] = React.useState(0);

  const handleScenarioTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setScenarioTabValue(newValue);
  }

  const handleSaveFactsheet = () => {
    factsheetObjectHandler('name', factsheetName);
    if (id === 'new') {
      factsheetObjectHandler('scenarios_name', JSON.stringify(scenariosName));
      factsheetObjectHandler('scenarios_acronym', JSON.stringify(scenariosAcronym));
      factsheetObjectHandler('scenarios_abstract', JSON.stringify(scenariosAbstract));

      axios.post(conf.localhost + 'factsheet/add/', null,
      {  params:
        factsheetObject
      }).then(response => setOpenSavedDialog(true));

    } else {
      axios.post(conf.localhost + 'factsheet/update/', null,
      {  params:
          {
            id: id,
            study_name: studyName,
            name: factsheetName,
            acronym: acronym,
            abstract: abstract,
            institution: JSON.stringify(selectedInstitution),
            funding_source: JSON.stringify(selectedFundingSource),
            contact_person: JSON.stringify(selectedContactPerson),
            report_title: report_title,
            date_of_publication: date_of_publication,
            doi: doi,
            place_of_publication: place_of_publication,
            link_to_study: link_to_study,
            authors: JSON.stringify(selectedAuthors),
            scenarios_name: JSON.stringify(scenariosName),
            scenarios_acronym: JSON.stringify(scenariosAcronym),
            scenarios_abstract: JSON.stringify(scenariosAbstract),
            scenarios_region: JSON.stringify(selectedRegion),
            scenarios_interacting_region: JSON.stringify(selectedInteractingRegion),
            scenarios_years: JSON.stringify(selectedScenariosYears),
            scenarios_keywords: JSON.stringify(selectedScenariosKeywords),
          }
      }).then(response => setOpenUpdatedDialog(true));
    }
  };

  const handleRemoveFactsheet = () => {
    axios.post(conf.localhost + 'factsheet/delete/', null, { params: { id: id } }).then(response => setOpenRemovedDialog(true));
  }

  const handleCloseJSON = () => {
    setOpenJSON(false);
  };

  const handleCloseSavedDialog = () => {
    setOpenSavedDialog(false);
  };

  const handleCloseUpdatedDialog = () => {
    setOpenUpdatedDialog(false);
  };

  const handleCloseRemovedDialog = () => {
    setOpenRemovedDialog(false);
  };

  const handleScenarioInpuDatasetName = e => {
    setScenarioInputDatasetName(e.target.value);
    factsheetObjectHandler('scenario_input_dataset_name', e.target.value);
  };

  const handleScenarioInputDatasetIRI = e => {
    setScenarioInputDatasetIRI(e.target.value);
    factsheetObjectHandler('scenario_input_dataset_IRI', e.target.value);
  };

  const handleScenarioOutputDatasetName = e => {
    setScenarioOutputDatasetName(e.target.value);
    factsheetObjectHandler('scenario_output_dataset_name', e.target.value);
  };

  const handleScenariooutputDatasetIRI = e => {
    setScenarioOutputDatasetIRI(e.target.value);
    factsheetObjectHandler('scenario_output_dataset_IRI', e.target.value);
  };


  const handleScenariostName = ({ target }) => {
    const { name: key, value } = target;
    setScenariosName(state => ({
      ...state,
      [key.split('_')[1]]: value
    }));
  };

  const handleScenariosAcronym = ({ target }) => {
    const { name: key, value } = target;
    setScenariosAcronym(state => ({
      ...state,
      [key.split('_')[1]]: value
    }));
  };

  const handleScenariosAbstract = ({ target }) => {
    const { name: key, value } = target;
    setScenariosAbstract(state => ({
      ...state,
      [key.split('_')[1]]: value
    }));
  };

  const handleScenarioAcronym = e => {
    setScenarioAcronym(e.target.value);
    factsheetObjectHandler('scenario_acronym', e.target.value);
  };

  const handleScenarioAbstract = e => {
    setScenarioAbstract(e.target.value);
    factsheetObjectHandler('scenario_abstract', e.target.value);
  };

  const handleAcronym = e => {
    setAcronym(e.target.value);
    factsheetObjectHandler('acronym', e.target.value);
  };

  const handleStudyName = e => {
    setStudyName(e.target.value);
    factsheetObjectHandler('study_name', e.target.value);
  };

  const handleAbstract = e => {
    setAbstract(e.target.value);
    factsheetObjectHandler('abstract', e.target.value);
  };

  const handleReportTitle = e => {
    setReportTitle(e.target.value);
    factsheetObjectHandler('report_title', e.target.value);
  };

  const handleDOI = e => {
    setDOI(e.target.value);
    factsheetObjectHandler('doi', e.target.value);
  };

  const handleFactsheetName = e => {
    setFactsheetName(e.target.value);
    factsheetObjectHandler('name', e.target.value);
  };

  const handlePlaceOfPublication = e => {
    setPlaceOfPublication(e.target.value);
    factsheetObjectHandler('place_of_publication', e.target.value);
  };

  const handleLinkToStudy = e => {
    setLinkToStudy(e.target.value);
    factsheetObjectHandler('link_to_study', e.target.value);
  };

  const handleDateOfPublication = e => {
    setDateOfPublication(e.target.value);
    factsheetObjectHandler('date_of_publication', e.target.value);
  };

  const handleClickOpenTurtle = () => {
    setOpenTurtle(true);
    convert2RDF();
  };

  const handleClickOpenSavedDialog = () => {
    openSavedDialog(true);
  };

  const handleClickOpenUpdatedDialog = () => {
    openSavedDialog(true);
  };

  const handleClickOpenRemovedDialog = () => {
    openRemoveddDialog(true);
  };

  const handleCloseTurtle = () => {
    setOpenTurtle(false);
  };

  const handleCloseOverView = () => {
    setOpenOverView(false);
  };

  const handleAddScenario = () => {
    setScenarios(scenarios + 1);
  };

  const handleSwap = (mode) => {
    console.log(mode);
    setMode(mode);
    if (mode === "wizard") {

    }
    else if (mode === "overview") {
    setOpenOverView(true);
    }
  };

    const factsheetObjectHandler = (key, obj) => {
      let newFactsheetObject = factsheetObject;
      newFactsheetObject[key] = obj
      setFactsheetObject(newFactsheetObject);
    }

    const scenariosObjectHandler = (key, obj) => {
      let newFactsheetObject = factsheetObject;
      newFactsheetObject[key] = obj
      setFactsheetObject(newFactsheetObject);
    }

    const renderFactsheet = (factsheetContent) => {
      if (Object.keys(factsheetContent).length !== 0) {
        return Object.keys(factsheetContent).map((item) => (
          <div style={{ marginTop: '30px', marginLeft: '50px', marginBottom: '10px' }}>
             <b> {item.charAt(0).toUpperCase() + item.slice(1)} </b>
             {
               factsheetContent[item].map((v) => (
                   <div style={{ marginLeft: '25px' }}>
                    <span> {v.name} </span>
                   </div>
             ))
           }
          </div>
        ))
      }
    }

    const sectors = [
      { id: 'Agriculture forestry and land use sector', name: 'Agriculture forestry and land use sector' },
      { id: 'Energy demand sector', name: 'Energy demand sector' },
      { id: 'Energy transformation sector', name: 'Energy transformation sector' },
      { id: 'Industry sector', name: 'Industry sector' },
      { id: 'Waste and wastewater sector', name: 'Waste and wastewater sector' }
    ];

    const sector_divisions = [
      { id: 'Europian', name: 'Europian' },
      { id: 'Germany', name: 'Germany' },
    ];

    const authors = [
      { id: 'Julia Repenning',  name: 'Julia Repenning' },
      { id: 'Lukas Emele',  name: 'Lukas Emele' },
      { id: 'Ruth Blanck',  name: 'Ruth Blanck' },
      { id: 'Hannes Böttcher',  name: 'Hannes Böttcher' },
      { id: 'Günter Dehoust',  name: 'Günter Dehoust' },
      { id: 'Hannah Förster',  name: 'Hannah Förster' },
      { id: 'Benjamin Greiner',  name: 'Benjamin Greiner' },
      { id: 'Ralph Harthan',  name: 'Ralph Harthan' },
      { id: 'Klaus Henneberg',  name: 'Klaus Henneberg' },
      { id: 'Hauke Hermann',  name: 'Hauke Hermann' },
      { id: 'Wolfram Jörß',  name: 'Wolfram Jörß' },
      { id: 'Charlotte Loreck',  name: 'Charlotte Loreck' },
      { id: 'Sylive Ludig',  name: 'Sylive Ludig' },
      { id: 'Felix Chri. Matthes',  name: 'Felix Chri. Matthes' },
      { id: 'Margarethe Scheffler',  name: 'Margarethe Scheffler' },
      { id: 'Katja Schumachen',  name: 'Katja Schumachen' },
      { id: 'Kirsten Wiegmann',  name: 'Kirsten Wiegmann' },
      { id: 'Carina Zell-Ziegler',  name: 'Carina Zell-Ziegler' },
      { id: 'Sibylle Braungardt',  name: 'Sibylle Braungardt' },
      { id: 'Wolfgang Eichhammer',  name: 'Wolfgang Eichhammer' },
      { id: 'Rainer Elsland',  name: 'Rainer Elsland' },
      { id: 'Tobias Fleiter',  name: 'Tobias Fleiter' },
      { id: 'Johannes Hartwig',  name: 'Johannes Hartwig' },
      { id: 'Judit Kockat',  name: 'Judit Kockat' },
      { id: 'Ben Pfluger',  name: 'Ben Pfluger' },
      { id: 'Wolfgang Schade',  name: 'Wolfgang Schade' },
      { id: 'Barbara Schlomann',  name: 'Barbara Schlomann' },
      { id: 'Frank Sensfuß',  name: 'Frank Sensfuß' },
      { id: 'Hans-Joachim Ziesing',  name: 'Hans-Joachim Ziesing' }
    ];

    const funding_source = [
      { id: 'Bundesministerium für Umwelt, Naturschutz, Bau und Reaktorsicherheit', name:'Bundesministerium für Umwelt, Naturschutz, Bau und Reaktorsicherheit' },
    ];

    const institution = [
      { id: 'Öko-Institut', name: "Öko-Institut"},
      { id: 'Frauenhofer ISI', name: "Frauenhofer ISI"},
    ];

    const scenario_years = [
      { id: '2010', name: "2010"},
      { id: '2015', name: "2015"},
      { id: '2020', name: "2020"},
      { id: '2025', name: "2025"},
      { id: '2030', name: "2030"},
      { id: '2035', name: "2035"},
      { id: '2040', name: "2040"},
      { id: '2045', name: "2045"},
      { id: '2050', name: "2050"},
    ];

    const scenario_keywords = [
      { id: '100% renewables', name: "100% renewables"},
      { id: 'acceptance', name: "acceptance"},
      { id: 'sufficiency', name: "sufficiency"},
      { id: 'Negative Emissionen', name: "Negative Emissionen"},
      { id: 'grid restrictions', name: "grid restrictions"},
      { id: 'Grid / infrastructure extension', name: "Grid / infrastructure extension"},
    ];

    const contact_person = [
      { id: 'Lukas Emele', name: 'Lukas Emele' },
      { id: 'Julia Repenning', name: 'Julia Repenning' },
    ];

    const scenario_region = [
      { id: 'Germany', name: 'Germany' },
      { id: 'France', name: 'France' },
    ];

    const scenario_input_dataset_region = [
      { id: '1', name: 'Germany' },
      { id: '2', name: 'France' },
    ];

    const scenario_interacting_region = [
      { id: 'France', name: 'France' },
      { id: 'Spain', name: 'Spain' },
    ];

    const energy_carriers = [
      { id: '1', name: 'Gas' },
      { id: '3', name: 'Electricity' },
    ];

    const energy_transportation = [
      { id: '1', name: 'Fuel' },
    ];

    const sectorsHandler = (sectorsList) => {
      setSelectedSectors(sectorsList);
      factsheetObjectHandler('sectors', sectorsList);
    };

    const authorsHandler = (authorsList) => {
      setSelectedAuthors(authorsList);
      factsheetObjectHandler('authors', JSON.stringify(authorsList));
    };

    const institutionHandler = (institutionList) => {
      setSelectedInstitution(institutionList);
      factsheetObjectHandler('institution', JSON.stringify(institutionList));
    };

    const fundingSourceHandler = (fundingSourceList) => {
      setSelectedFundingSource(fundingSourceList);
      factsheetObjectHandler('funding_source', JSON.stringify(fundingSourceList));
    };

    const contactPersonHandler = (contactPersonList) => {
      setselectedContactPerson(contactPersonList);
      factsheetObjectHandler('contact_person', JSON.stringify(contactPersonList));
    };

    const scenarioRegionHandler = (regionList, idx) => {
      let newSelectedRegion = selectedRegion;
      newSelectedRegion[idx] = regionList;
      factsheetObjectHandler('scenarios_region', JSON.stringify(newSelectedRegion));
    };

    const scenarioInteractingRegionHandler = (interactionRegionList, idx) => {
      let newSelectedInteractionRegion = selectedInteractingRegion;
      newSelectedInteractionRegion[idx] = interactionRegionList;
      factsheetObjectHandler('scenarios_interacting_region', JSON.stringify(newSelectedInteractionRegion));
    };

    const scenariosYearsHandler = (scenarioYearsList, idx) => {
      let newSelectedScenarioYears = selectedScenariosYears;
      newSelectedScenarioYears[idx] = scenarioYearsList;
      factsheetObjectHandler('scenarios_years', JSON.stringify(newSelectedScenarioYears));
    };

    const scenariosKeywordsHandler = (scenarioKeywordsList, idx) => {
      let newSelectedScenarioKeywords = selectedScenariosKeywords;
      newSelectedScenarioKeywords[idx] = scenarioKeywordsList;
      factsheetObjectHandler('scenarios_keywords', JSON.stringify(newSelectedScenarioKeywords));
    };

    const energyCarrierHandler = (energyCarrierList) => {
      setSelectedsetEnergyCarriers(energyCarrierList);
      factsheetObjectHandler('scenario_energy_carriers', JSON.stringify(selectedEnergyCarriers));
    };

    const energyTransportationHandler = (energyTransportationList) => {
      setSelectedEnergyTransportation(energyTransportationList);
      factsheetObjectHandler('scenario_energy_transportation', JSON.stringify(selectedEnergyTransportation));
    };

    const scenarioInputDatasetRegionHandler = (inputDatasetRegionList) => {
      setSelectedScenarioInputDatasetRegion(inputDatasetRegionList);
      factsheetObjectHandler('scenario_input_dataset_region', JSON.stringify(selectedScenarioInputDatasetRegion));
    };

    const scenarioOutputDatasetRegionHandler = (outputDatasetRegionList) => {
      setSelectedScenarioOutputDatasetRegion(outputDatasetRegionList);
      factsheetObjectHandler('scenario_output_dataset_region', JSON.stringify(selectedScenarioOutputDatasetRegion));
    };

    function a11yProps(index: number) {
      return {
        id: `vertical-tab-${index}`,
        'aria-controls': `vertical-tabpanel-${index}`,
      };
    }

    const renderStudy = () => {
      return <Grid container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
      >
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <TextField style={{  width: '90%' }} id="outlined-basic" label="What is the name of the study?" variant="outlined" value={studyName} onChange={handleStudyName}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <TextField style={{  width: '90%' }} id="outlined-basic" label="What is the acronym or short title?" variant="outlined" value={acronym} onChange={handleAcronym} />
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '0px' }}>
          <CustomAutocomplete manyItems optionsSet={institution} kind='Which institutions are involved in this study?' handler={institutionHandler} selectedElements={selectedInstitution}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '0px' }}>
          <CustomAutocomplete manyItems optionsSet={funding_source} kind='What are the funding sources of this study?' handler={fundingSourceHandler} selectedElements={selectedFundingSource}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <TextField style={{ width: '90%', MarginBottom: '10px', marginTop: '5px' }} id="outlined-basic" label="Please describe the research questions of the study in max 400 characters." variant="outlined" multiline rows={4} maxRows={10} value={abstract} onChange={handleAbstract}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <CustomAutocomplete manyItems optionsSet={contact_person} kind='Who is the contact person for this factsheet?' handler={contactPersonHandler} selectedElements={selectedContactPerson}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
        </Grid>
        <Grid
          container
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          style={{ 'padding': '20px', 'border': '1px solid #cecece', width: '97%' }}
        >
            <Grid item xs={12} >
              <Typography variant="subtitle1" gutterBottom style={{ marginTop:'10px', marginBottom:'5px' }}>
                Study content description:
              </Typography>
            </Grid>
            <Grid item xs={6} style={{ marginBottom: '10px' }}>
              <CustomAutocomplete manyItems optionsSet={sectors} kind='Do you use a predefined sector division? ' handler={sectorsHandler} selectedElements={selectedSectors}/>
            </Grid>
            <Grid item xs={6} style={{ marginBottom: '10px' }}>
              <CustomAutocomplete manyItems optionsSet={sector_divisions} kind='Which sectors are considered in the study?' handler={sectorsHandler} selectedElements={[]}/>
            </Grid>
            <Grid item xs={6} style={{ marginBottom: '10px' }}>
            <CustomAutocomplete manyItems optionsSet={sectors} kind='What energy carriers are considered?' handler={sectorsHandler} selectedElements={selectedSectors}/>
            </Grid>
            <Grid item xs={6} style={{ marginBottom: '10px' }}>
            <CustomAutocomplete manyItems optionsSet={sectors} kind='Which energy transformation processes are considered?' handler={sectorsHandler} selectedElements={selectedSectors}/>
            </Grid>
            <Grid item xs={12} style={{ marginBottom: '10px' }}>
            <Typography variant="subtitle1" gutterBottom style={{ marginTop:'10px', marginBottom:'5px' }}>
              What additional keywords describe your study?
            </Typography>
            <div>
              <FormGroup>
                  <div>
                    <FormControlLabel control={<Checkbox />} label="resilience" />
                    <FormControlLabel control={<Checkbox />} label="life cycle analysis" />
                    <FormControlLabel control={<Checkbox />} label="CO2 emissions" />
                    <FormControlLabel control={<Checkbox />} label="life cycle analysis" />
                    <FormControlLabel control={<Checkbox />} label="Greenhouse gas emissions" />
                    <FormControlLabel control={<Checkbox />} label="Reallabor" />
                    <FormControlLabel control={<Checkbox />} label="100% renewables" />
                    <FormControlLabel control={<Checkbox />} label="acceptance" />
                    <FormControlLabel control={<Checkbox />} label="sufficiency" />
                    <FormControlLabel control={<Checkbox />} label="(changes in) demand" />
                    <FormControlLabel control={<Checkbox />} label="degree of electrifiaction" />
                    <FormControlLabel control={<Checkbox />} label="regionalisation" />
                    <FormControlLabel control={<Checkbox />} label="total gross electricity generation" />
                    <FormControlLabel control={<Checkbox />} label="total net electricity generation" />
                    <FormControlLabel control={<Checkbox />} label="peak electricity generation" />
                </div>
              </FormGroup>
            </div>
            </Grid>
        </Grid>
        <Grid
          container
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          style={{ 'padding': '20px', 'border': '1px solid #cecece', width: '97%' }}
        >
          <Grid item xs={12} >
            <Typography variant="subtitle1" gutterBottom style={{ marginTop:'10px', marginBottom:'20px' }}>
              Report:
            </Typography>
          </Grid>
          <Grid item xs={6} >
            <TextField style={{ marginTop:'-20px', width: '90%' }} id="outlined-basic" label="Title" variant="outlined" value={report_title} onChange={handleReportTitle} />
          </Grid>
          <Grid item xs={6} >
            <LocalizationProvider dateAdapter={AdapterDayjs}>
              <Stack spacing={3} style={{ width: '90%' }}>
                <DesktopDatePicker
                    label='Date of publication'
                    inputFormat="MM/DD/YYYY"
                    value={date_of_publication}
                    onChange={(newValue) => {
                      setDateOfPublication(newValue);
                      factsheetObjectHandler('date_of_publication', newValue);
                    }}
                    renderInput={(params) => <TextField {...params} />}
                  />
              </Stack>
            </LocalizationProvider>
          </Grid>
          <Grid item xs={6} >
            <TextField style={{ width: '90%' }} id="outlined-basic" label="DOI" variant="outlined" value={doi} onChange={handleDOI} />
          </Grid>
          <Grid item xs={6} >
            <TextField style={{ width: '90%', marginTop:'20px' }} id="outlined-basic" label="Place of publication" variant="outlined" value={place_of_publication} onChange={handlePlaceOfPublication} />
          </Grid>
          <Grid item xs={6} >
            <TextField style={{ width: '90%', marginTop:'-60px' }} id="outlined-basic" label="Link to study report" variant="outlined" value={link_to_study} onChange={handleLinkToStudy} />
          </Grid>
          <Grid item xs={6} >
            <CustomAutocomplete manyItems optionsSet={authors} kind='Authors' handler={authorsHandler} selectedElements={selectedAuthors} manyItems />
          </Grid>
        </Grid>
      </Grid>
    }

    const renderScenario = () => {
      return  <div>
                <div style={{ textAlign: 'left', marginBottom: '20px' }}>
                <IconButton variant="outlined" color="primary" aria-label="upload picture" component="label" onClick={handleAddScenario}>
                  <AddBoxIcon />
                </IconButton>
                <IconButton color="primary" aria-label="upload picture" component="label">
                  <ContentCopyIcon />
                </IconButton>
                <IconButton color="error" aria-label="upload picture" component="label">
                  <DeleteOutlineIcon />
                </IconButton>
                </div >
                <Box sx={{ flexGrow: 1, bgcolor: 'background.paper', display: 'flex', height:'60vh', overflow: 'auto' }} >
                  <Tabs
                    orientation="vertical"
                    variant="scrollable"
                    value={scenarioTabValue}
                    onChange={handleScenarioTabChange}
                    aria-label="Vertical tabs example"
                    sx={{ borderRight: 1, borderColor: 'divider' }}
                     key={'Scenario_tabs'}
                  >
                  {Array(scenarios).fill().map((item, i) =>
                    <Tab label={'Scenario ' + (i + 1)} {...a11yProps(i)} key={'Scenario_tab_' + (i + 1)}  style={{ borderTop: '1px dashed #cecece', borderLeft: '1px dashed #cecece', borderBottom: '1px dashed #cecece' }}  key={'Scenario_panel_' + (i + 1)}/>
                  )}
                  </Tabs>
                  {Array(scenarios).fill().map((item, i) =>
                    <TabPanel value={scenarioTabValue} index={i} style={{ width: '90%', overflow: 'auto', borderTop: '1px solid #cecece', borderRight: '1px solid #cecece', borderBottom: '1px solid #cecece' }}  key={'Scenario_panel_' + (i + 1)} >
                      <Scenario
                        idx={i}
                        handleScenariostName={handleScenariostName}
                        handleScenariosAcronym={handleScenariosAcronym}
                        handleScenariosAbstract={handleScenariosAbstract}
                        scenariosName={scenariosName}
                        scenariosAcronym={scenariosAcronym}
                        scenariosAbstract={scenariosAbstract}
                        scenario_region={scenario_region}
                        scenarioRegionHandler={scenarioRegionHandler}
                        selectedRegion={selectedRegion[i] !== undefined ? selectedRegion[i] :[]}
                        scenarioRegion={scenario_region}
                        scenarioRegionHandler={scenarioRegionHandler}
                        scenarioSelectedRegion={selectedRegion[i] !== undefined ? selectedRegion[i] :[]}
                        scenarioInteractingRegion={scenario_interacting_region}
                        scenarioInteractingRegionHandler={scenarioInteractingRegionHandler}
                        scenarioSelectedInteractingRegion={selectedInteractingRegion[i] !== undefined ? selectedInteractingRegion[i] :[]}
                        scenariosYears={scenario_years}
                        scenariosYearsHandler={scenariosYearsHandler}
                        scenariosSelectedYears={selectedScenariosYears[i] !== undefined ? selectedScenariosYears[i] :[]}
                        scenarioskeywords={scenario_keywords}
                        scenariosKeywordsHandler={scenariosKeywordsHandler}
                        scenariosSelectedkeywords={selectedScenariosKeywords[i] !== undefined ? selectedScenariosKeywords[i] :[]}
                        scenariosInputDatasets={[]}
                        scenariosOutputDatasets={[]}
                      />
                    </TabPanel>
                  )}
                </Box>
              </div >
      }

    const items = {
      titles: ['Study', 'Scenarios', 'Models', 'Frameworks'],
      contents: [
        renderStudy(),
        renderScenario(),
        <CustomAutocomplete optionsSet={sectors} kind='Models' handler={sectorsHandler} selectedElements={selectedSectors}/>,
        <CustomAutocomplete optionsSet={sectors} kind='Frameworks' handler={sectorsHandler} selectedElements={selectedSectors}/>,
        ]
    }
    const convert2RDF = async () => {
      factsheetJSON["oeo:OEO_00000505"] = [];
      selectedSectors.map(sector => {
        factsheetJSON["oeo:OEO_00000505"].push({
          "@id": sector.id.replaceAll(" ", "_"),
        });
      });

      factsheetJSON["oeo:OEO_00000509"] = [];
      selectedAuthors.map(author => {
        factsheetJSON["oeo:OEO_00000509"].push({
          "@id": author.id.replaceAll(" ", "_"),
        });
      });

      const nquads = await jsonld.toRDF(factsheetJSON, {format: 'application/n-quads'});
      setFactsheetRDF(nquads);
      return(nquads);
    }

    useEffect(() => {
      convert2RDF().then((nquads) => setFactsheetRDF(nquads));
    }, []);

    return (
      <div>
        <Grid container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
      >
          <Grid item xs={8} >
          <div>
               <CustomSwap handleSwap={handleSwap} />
          </div >
          </Grid>
          <Grid item xs={4} >
            <div style={{ 'textAlign': 'right' }}>
              <Button disableElevation={true} startIcon={<DeleteOutlineIcon />}   style={{ 'textTransform': 'none', 'marginTop': '10px', 'marginRight': '5px', 'zIndex': '1000' }} variant="outlined" color="error" onClick={handleRemoveFactsheet}>Remove</Button>
              <Button disableElevation={true} startIcon={<ShareIcon />}   style={{ 'textTransform': 'none', 'marginTop': '10px', 'marginRight': '5px', 'zIndex': '1000' }} variant="outlined" color="primary" >Share</Button>
              <Button disableElevation={true} startIcon={<MailOutlineIcon />}   style={{ 'textTransform': 'none', 'marginTop': '10px', 'zIndex': '1000' }} variant="outlined" color="primary" onClick={handleSaveFactsheet} >Save</Button>
              <Button disableElevation={true} startIcon={<ForwardToInboxIcon />}   style={{ 'textTransform': 'none', 'marginTop': '10px', 'marginLeft': '5px', 'marginRight': '10px','zIndex': '1000'  }} variant="contained" color="primary" onClick={handleClickOpenTurtle}>Submit</Button>
            </div >
          </Grid>
          <Grid item xs={12}>
            <Dialog
              fullWidth
              maxWidth="xl"
              open={openTurtle}
              onClose={handleClickOpenTurtle}
              aria-labelledby="responsive-dialog-title"
            >
              <DialogTitle id="responsive-dialog-title">
                <b>Linked Data format (serialization)</b>
              </DialogTitle>
              <DialogContent>
                <DialogContentText>
                  <div>
                    <pre>
                      Open Energy Knowledge Graph
                    </pre>
                    <pre style={{ "fontSize": "10px", "fontWeight": "bold" }}>
                      {factsheetRDF}
                    </pre>
                  </div>
                </DialogContentText>
              </DialogContent>
              <DialogActions>
                <Button variant="contained" onClick={handleCloseTurtle} >
                  Download
                </Button>
                <Button variant="contained" onClick={handleCloseTurtle}>
                  Cancel
                </Button>
              </DialogActions>
            </Dialog>


            <Dialog
              fullWidth
              maxWidth="md"
              open={openSavedDialog}
              onClose={handleClickOpenSavedDialog}
              aria-labelledby="responsive-dialog-title"
            >
              <DialogTitle id="responsive-dialog-title">
                <b>New Factsheet Saved!</b>
              </DialogTitle>
              <DialogContent>
                <DialogContentText>
                  <div>
                    <pre>
                      Your new factsheet has saved in the Open Energy Platform!
                    </pre>
                  </div>
                </DialogContentText>
              </DialogContent>
              <DialogActions>
                <Link to={`factsheet/`} onClick={() => this.reloadRoute()} state={{ testvalue: "hello" }} className="btn btn-primary" style={{ textDecoration: 'none', color: 'blue', marginRight: '10px' }}>
                <Button variant="outlined" >
                  Back to main page
                </Button>
                </Link>
              </DialogActions>
            </Dialog>
            <Dialog
              fullWidth
              maxWidth="md"
              open={openUpdatedDialog}
              onClose={handleClickOpenUpdatedDialog}
              aria-labelledby="responsive-dialog-title"
            >
              <DialogTitle id="responsive-dialog-title">
                <b>Factsheet Updated!</b>
              </DialogTitle>
              <DialogContent>
                <DialogContentText>
                  <div>
                    <pre>
                      Your factsheet has updated!
                    </pre>
                  </div>
                </DialogContentText>
              </DialogContent>
              <DialogActions>
                <Link to={`factsheet/`} onClick={() => this.reloadRoute()} className="btn btn-primary" style={{ textDecoration: 'none', color: 'blue', marginRight: '10px' }}>
                <Button variant="outlined" >
                  Back to main page
                </Button>
                </Link>
              </DialogActions>
            </Dialog>
            <Dialog
              fullWidth
              maxWidth="md"
              open={openRemoveddDialog}
              onClose={handleClickOpenRemovedDialog}
              aria-labelledby="responsive-dialog-title"
            >
              <DialogTitle id="responsive-dialog-title">
                <b>Factsheet Removed!</b>
              </DialogTitle>
              <DialogContent>
                <DialogContentText>
                  <div>
                    <pre>
                      Your factsheet has removed from the Open Energy Platform!
                    </pre>
                  </div>
                </DialogContentText>
              </DialogContent>
              <DialogActions>
                <Link to={`factsheet/`} onClick={() => this.reloadRoute()} className="btn btn-primary" style={{ textDecoration: 'none', color: 'blue', marginRight: '10px' }}>
                <Button variant="outlined" >
                  Back to main page
                </Button>
                </Link>
              </DialogActions>
            </Dialog>
            {mode === "wizard" &&
              <div className='wizard'>
                  <Grid container >
                    <Grid item xs={12} >
                      <div style={{ "textAlign": "center", "fontSize": "25px" }}>
                        <TextField style={{ width: '50%', marginBottom: '20px', }} inputProps={{min: 0, style: { textAlign: 'center', fontWeight: 'bold' }}} id="outlined-basic"  variant="standard" value={factsheetName} onChange={handleFactsheetName} />
                      </div>
                      <CustomTabs
                        factsheetObjectHandler={factsheetObjectHandler}
                        items={items}
                      />
                    </Grid>
                  </Grid>
              </div>
            }
            {mode === "overview" &&
              <div className='wizard'>
                  <Grid container >
                    <Grid item xs={12}>
                      <div style={{ "textAlign": "center", "fontSize": "25px" }}>
                        <b> {factsheetName} </b>
                      </div>
                      <div>
                        {renderFactsheet(factsheetObject)}
                      </div>
                    </Grid>
                  </Grid>
              </div>
            }
        </Grid>
      </Grid>
    </div>
  );
}

export default Factsheet;
