import React, { useState, useEffect } from 'react';
import Grid from '@mui/material/Grid';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import CustomSwap from './customSwapButton.js';
import CustomTabs from './customTabs.js';
import CustomAutocomplete from './customAutocomplete.js';
import Scenario from './scenario.js';
import CustomTreeViewWithCheckBox from './customTreeViewWithCheckbox.js'
import Snackbar from '@mui/material/Snackbar';
import Typography from '@mui/material/Typography';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DesktopDatePicker } from '@mui/x-date-pickers/DesktopDatePicker';
import Stack from '@mui/material/Stack';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import Fab from '@mui/material/Fab';
import AddIcon from '@mui/icons-material/Add';
import Checkbox from '@mui/material/Checkbox';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import conf from "../conf.json";
import Tooltip, { TooltipProps, tooltipClasses } from '@mui/material/Tooltip';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import { styled } from '@mui/material/styles';
import SaveIcon from '@mui/icons-material/Save';
import uuid from "react-uuid";
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import modelsList from './models_list.json';
import frameworksList from './frameworks_list.json';
import study_keywords from '../data/study_keywords.json';
import scenario_years from '../data/scenario_years.json';
import {sectors_json} from '../data/sectors.js';
import sector_divisions from '../data/sector_divisions.json';

import {energy_carriers_json} from '../data/energy_carriers.js';
import { Route, Routes, useNavigate } from 'react-router-dom';
import authors from '../data/authors.json';

import '../styles/App.css';

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
  const navigate = useNavigate();

  const { id, fsData } = props;
  const [openSavedDialog, setOpenSavedDialog] = useState(false);
  const [openUpdatedDialog, setOpenUpdatedDialog] = useState(false);
  const [openExistDialog, setOpenExistDialog] = useState(false);
  const [openRemoveddDialog, setOpenRemovedDialog] = useState(false);
  const [mode, setMode] = useState(id === "new" ? "edit" : "overview");
  const [factsheetObject, setFactsheetObject] = useState({});
  const [factsheetName, setFactsheetName] = useState(id !== 'new' ? '' : '');
  const [acronym, setAcronym] = useState(id !== 'new' ? fsData.acronym : '');
  const [prevAcronym, setPrevAcronym] = useState(id !== 'new' ? fsData.acronym : '');
  const [studyName, setStudyName] = useState(id !== 'new' ? fsData.study_name : '');
  const [abstract, setAbstract] = useState(id !== 'new' ? fsData.abstract : '');
  const [selectedSectors, setSelectedSectors] = useState(id !== 'new' ? [] : []);
  const [expandedSectors, setExpandedSectors] = useState(id !== 'new' ? [] : []);
  const [institutions, setInstitutions] = useState([]);
  const [fundingSources, setFundingSources] = useState([]);
  const [contactPersons, setContactPersons] = useState([]);
  const [isCreated, setIsCreated] = useState(false);
  

  const HtmlTooltip = styled(({ className, ...props }: TooltipProps) => (
    <Tooltip {...props} classes={{ popper: className }} />
  ))(({ theme }) => ({
    [`& .${tooltipClasses.tooltip}`]: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      color: 'white',
      maxWidth: 520,
      fontSize: theme.typography.pxToRem(20),
      border: '1px solid black',
      padding: '20px'
    },
  }));

  const wrapInTooltip = (name, description, link) => <span> <HtmlTooltip
              placement="top"
              title={
                <React.Fragment>
                <Typography color="inherit" variant="caption">
                  Description of <b>{name}</b> from Open Energy Ontology (OEO): TDB ...
                <br />
                <a href={link}>More info from Open Enrgy Knowledge Graph (OEKG)...</a>
                </Typography>
                </React.Fragment>
              }
              >
              <HelpOutlineIcon sx={{ fontSize: '24px', color: '#bdbdbd', marginLeft: '-10px' }}/>
          </HtmlTooltip>
          <span
            style={{ marginLeft: '5px', marginTop: '-20px' }}
          >
          {name}
          </span>
        </span>

  
  const [sectors, setSectors] = useState(sectors_json);
  const [filteredSectors, setFilteredSectors] = useState(id !== 'new' ? sectors : []);
  const [selectedSectorDivisions, setSelectedSectorDivisions] = useState(id !== 'new' ? fsData.sector_divisions : []);
  const [selectedAuthors, setSelectedAuthors] = useState(id !== 'new' ? fsData.authors : []);
  const [selectedInstitution, setSelectedInstitution] = useState(id !== 'new' ? fsData.institution : []);
  const [selectedFundingSource, setSelectedFundingSource] = useState(id !== 'new' ? fsData.funding_sources : []);
  const [selectedContactPerson, setselectedContactPerson] = useState(id !== 'new' ? fsData.contact_person : []);
  const [report_title, setReportTitle] = useState(id !== 'new' ? '' : '');
  const [date_of_publication, setDateOfPublication] = useState(id !== 'new' ? '04-07-2022' : '04-07-2022');
  const [doi, setDOI] = useState(id !== 'new' ? '' : '');
  const [place_of_publication, setPlaceOfPublication] = useState(id !== 'new' ? '' : '');
  const [link_to_study, setLinkToStudy] = useState(id !== 'new' ? '' : '');
  const [scenarios, setScenarios] = useState(id !== 'new' ? [] : [{
    id: uuid(),
    name: '',
    acronym: '',
    abstract: '',
    regions: [],
    interacting_regions: [],
    scenario_years: [],
    keywords: [],
    input_datasets: [],
    output_datasets: [],
    }
  ]);
  const [scenariosObject, setScenariosObject] = useState({});
  const [selectedEnergyCarriers, setSelectedEnergyCarriers] = useState(id !== 'new' ? fsData.energy_carriers : []);
  const [expandedEnergyCarriers, setExpandedEnergyCarriers] = useState(id !== 'new' ? [] : []);
  const [selectedEnergyTransformationProcesses, setSelectedEnergyTransformationProcesses] = useState(id !== 'new' ? [] : []);
  const [expandedEnergyTransformationProcesses, setExpandedEnergyTransformationProcesses] = useState(id !== 'new' ? [] : []);
  const [selectedStudyKewords, setSelectedStudyKewords] = useState(id !== 'new' ? [] : []);
  const [selectedModels, setSelectedModels] = useState(id !== 'new' ? [] : []);
  const [selectedFrameworks, setSelectedFrameworks] = useState(id !== 'new' ? [] : []);
  const [removeReport, setRemoveReport] = useState(false);
  const [addedEntity, setAddedEntity] = useState(false);
  const [openAddedDialog, setOpenAddedDialog] = React.useState(false);
  const [openEditDialog, setOpenEditDialog] = React.useState(false);
  const [editedEntity, setEditedEntity] = useState(false);
  
  const [scenarioTabValue, setScenarioTabValue] = React.useState(0);

  const [energyTransformationProcesses, setEnergyTransformationProcesses] = React.useState([]);


  const handleScenarioTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setScenarioTabValue(newValue);
  }

  const populateFactsheetElements = async () => {
    const { data } = await axios.get(conf.toep + `factsheet/populate_factsheets_elements/`);
    
    return data;
  };

  useEffect(() => {
    populateFactsheetElements().then((data) => {
      const energy_transformation_processes_json = data.energy_transformation_processes;
      setEnergyTransformationProcesses(data.energy_transformation_processes);
      });
  }, []);
  

  const handleSaveFactsheet = () => {
    factsheetObjectHandler('name', factsheetName);
    if (id === 'new' && !isCreated) {
      axios.post(conf.toep + 'factsheet/add/',
      {
        id: id,
        study_name: studyName,
        name: factsheetName,
        acronym: acronym,
        abstract: abstract,
        institution: JSON.stringify(selectedInstitution),
        funding_source: JSON.stringify(selectedFundingSource),
        contact_person: JSON.stringify(selectedContactPerson),
        sector_divisions: JSON.stringify(selectedSectorDivisions),
        sectors: JSON.stringify(selectedSectors),
        expanded_sectors: JSON.stringify(expandedSectors),
        energy_carriers: JSON.stringify(selectedEnergyCarriers),
        expanded_energy_transformation_processes: JSON.stringify(expandedEnergyTransformationProcesses),
        expanded_energy_carriers: JSON.stringify(expandedEnergyCarriers),
        energy_transformation_processes: JSON.stringify(selectedEnergyTransformationProcesses),
        study_keywords: JSON.stringify(selectedStudyKewords),
        report_title: report_title,
        date_of_publication: date_of_publication,
        doi: doi,
        place_of_publication: place_of_publication,
        link_to_study: link_to_study,
        authors: JSON.stringify(selectedAuthors),
        scenarios: JSON.stringify(scenarios),
        models: JSON.stringify(selectedModels),
        frameworks: JSON.stringify(selectedFrameworks),
      }).then(response => {
      if (response.data === 'Factsheet saved') {
        navigate('/factsheet/fs/' + acronym);
        setIsCreated(true);
        setOpenSavedDialog(true);
        setPrevAcronym(acronym);
      }
      else if (response.data === 'Factsheet exists') {
        setOpenExistDialog(true);
      }
    });

    } else {
      console.log(selectedFundingSource);
      console.log(selectedInstitution);
      axios.get(conf.toep + `factsheet/get/`, { params: { id: prevAcronym } }).then(res => {
        axios.post(conf.toep + 'factsheet/update/',
        {
          fsData: res.data,
          id: id,
          study_name: studyName,
          name: factsheetName,
          acronym: acronym,
          abstract: abstract,
          institution: JSON.stringify(selectedInstitution),
          funding_source: JSON.stringify(selectedFundingSource),
          contact_person: JSON.stringify(selectedContactPerson),
          sector_divisions: JSON.stringify(selectedSectorDivisions),
          sectors: JSON.stringify(selectedSectors),
          expanded_sectors: JSON.stringify(expandedSectors),
          energy_carriers: JSON.stringify(selectedEnergyCarriers),
          expanded_energy_transformation_processes: JSON.stringify(expandedEnergyTransformationProcesses),
          expanded_energy_carriers: JSON.stringify(expandedEnergyCarriers),
          study_keywords: JSON.stringify(selectedStudyKewords),
          report_title: report_title,
          date_of_publication: date_of_publication,
          doi: doi,
          place_of_publication: place_of_publication,
          link_to_study: link_to_study,
          authors: JSON.stringify(selectedAuthors),
          scenarios: JSON.stringify(scenarios),
          models: JSON.stringify(selectedModels),
          frameworks: JSON.stringify(selectedFrameworks),
          energy_transformation_processes: JSON.stringify(selectedEnergyTransformationProcesses),
        }).then(response => {
          if (response.data === "factsheet updated!") {
            setPrevAcronym(acronym);
            setOpenUpdatedDialog(true);
          }
          else if (response.data === 'Factsheet exists') {
            setOpenExistDialog(true);
          }
        });
      });
      

    }
  };

  const handleRemoveFactsheet = () => {
    axios.post(conf.toep + 'factsheet/delete/', null, { params: { id: id } }).then(response => setOpenRemovedDialog(true));
  }

  const handleCloseSavedDialog = () => {
    setOpenSavedDialog(false);
  };

  const handleCloseExistDialog = () => {
    setOpenExistDialog(false);
  };

  const handleCloseUpdatedDialog = () => {
    setOpenUpdatedDialog(false);
  };

  const handleCloseRemovedDialog = () => {
    setOpenRemovedDialog(false);
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

  const handleClickOpenSavedDialog = () => {
    openSavedDialog(true);
  };

  const handleClickOpenUpdatedDialog = () => {
    openSavedDialog(true);
  };

  const handleClickOpenRemovedDialog = () => {
    setOpenRemovedDialog(true);
  };

  const handleClickCloseRemovedDialog = () => {
    setOpenRemovedDialog(false);
  };

  const handleAddedMessageClose = (event: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
      }
      setOpenAddedDialog(false);
  };

  const handleEditMessageClose = (event: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
      }
      setOpenEditDialog(false);
  };

  

  const handleScenariosInputChange = ({ target }) => {
    const { name, value } = target;
    const element = name.split('_')[0];
    const id = name.split('_')[1];
    const newScenarios = [...scenarios];
    const obj = newScenarios.find(el => el.id === id);
    if (obj)
      obj[element] =  value
    setScenarios(newScenarios);
    factsheetObjectHandler('scenarios', JSON.stringify(newScenarios));
  };

  const handleScenariosAutoCompleteChange = (selectedList, name, idx) => {
    const newScenarios = [...scenarios];
    const obj = newScenarios.find(el => el.id === idx);
    if (obj)
      obj[name] = selectedList
    setScenarios(newScenarios);
    factsheetObjectHandler('scenarios', JSON.stringify(newScenarios));
  };

  const scenariosInputDatasetsHandler = (scenariosInputDatasetsList, id) => {
    const newScenarios = [...scenarios];
    const obj = newScenarios.find(el => el.id === id);
    if (obj)
      obj.input_datasets = scenariosInputDatasetsList
    setScenarios(newScenarios);
    factsheetObjectHandler('scenarios', JSON.stringify(newScenarios));
  };

  const scenariosOutputDatasetsHandler = (scenariosOutputDatasetsList, id) => {
    const newScenarios = [...scenarios];
    const obj = newScenarios.find(el => el.id === id);
    if (obj)
      obj.output_datasets = scenariosOutputDatasetsList
    setScenarios(newScenarios);
    factsheetObjectHandler('scenarios', JSON.stringify(newScenarios));
  };

  const handleAddScenario = () => {
    const newScenarios = [...scenarios];
    newScenarios.push({
        id: uuid(),
        name: '',
        acronym: '',
        abstract: '',
        regions: [],
        interacting_regions: [],
        scenario_years: [],
        keywords: [],
        input_datasets: [],
        output_datasets: [],
      });
    setScenarios(newScenarios);
  };

  const removeScenario = (id) => {
    let newScenarios = [...scenarios].filter((obj => obj.id !== id));;
    setScenarios(newScenarios);
    factsheetObjectHandler('scenarios', JSON.stringify(newScenarios));
    setRemoveReport(true);
  };

  const handleSwap = (mode) => {
    setMode(mode);
  };

  const factsheetObjectHandler = (key, obj) => {
    let newFactsheetObject = factsheetObject;
    newFactsheetObject[key] = obj
    setFactsheetObject(newFactsheetObject);
  }

  const scenariosObjectHandler = (key, obj) => {
    let newScenariosObject = scenariosObject;
    newScenariosObject[key] = obj
    setScenariosObject(newScenariosObject);
  }

  const renderFactsheet = () => {
    return <div>'studyName'</div>
  } 

  const getInstitution = async () => {
    const { data } = await axios.get(conf.toep + `factsheet/get_entities_by_type/`, { params: { entity_type: 'OEO_00000238' } });
    return data;
  };

  const getFundingSources = async () => {
    const { data } = await axios.get(conf.toep + `factsheet/get_entities_by_type/`, { params: { entity_type: 'OEO_00090001' } });
    return data;
  };

  const getContactPersons = async () => {
    const { data } = await axios.get(conf.toep + `factsheet/get_entities_by_type/`, { params: { entity_type: 'OEO_00000107' } });
    return data;
  };

  useEffect(() => {
    getInstitution().then((data) => {
      const tmp = [];
      data.map( (item) => tmp.push({ 'id': item.replaceAll('_', ' '), 'name': item.replaceAll('_', ' ') }) )
      setInstitutions(tmp);
      });
  }, []);


  useEffect(() => {
    getFundingSources().then((data) => {
      const tmp = [];
      data.map( (item) => tmp.push({ 'id': item.replaceAll('_', ' '), 'name': item.replaceAll('_', ' ') }) )
      setFundingSources(tmp);
      });
  }, []);

  useEffect(() => {
    getContactPersons().then((data) => {
      const tmp = [];
      data.map( (item) => tmp.push({ 'id': item.replaceAll('_', ' '), 'name': item.replaceAll('_', ' ') }) )
      setContactPersons(tmp);
      });
  }, []);

  const HandleAddNewInstitution = (newElement) => {
    axios.post(conf.toep + 'factsheet/add_entities/',
    {
      entity_type: 'OEO_00000238',
      entity_label: newElement.name,
    }).then(response => {
    if (response.data === 'A new entity added!') {
      setOpenAddedDialog(true);
      setAddedEntity(['Institution', newElement.name ]);
      getInstitution().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push({ 'id': item.replaceAll('_', ' '), 'name': item.replaceAll('_', ' ') }) )
          setInstitutions(tmp);
        });
    }
    });
  } 

  const HandleEditInstitution = (oldElement, newElement) => {
    axios.post(conf.toep + 'factsheet/update_an_entity/',
    {
      entity_type: 'OEO_00000238',
      entity_label: oldElement,
      new_entity_label: newElement
    }).then(response => {
    if (response.data === 'entity updated!') {
      setOpenEditDialog(true);
      setEditedEntity(['Institution', oldElement, newElement ]);
      getInstitution().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push({ 'id': item.replaceAll('_', ' '), 'name': item.replaceAll('_', ' ') }) )
          setInstitutions(tmp);
        });
    }
    });
  } 

  const HandleAddNewFundingSource = (newElement) => {
    axios.post(conf.toep + 'factsheet/add_entities/',
    {
      entity_type: 'OEO_00090001',
      entity_label: newElement.name,
    }).then(response => {
    if (response.data === 'A new entity added!')
      setOpenAddedDialog(true);
      setAddedEntity(['Funding source', newElement.name ]);
      getFundingSources().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push({ 'id': item.replaceAll('_', ' '), 'name': item.replaceAll('_', ' ') }) )
          setFundingSources(tmp);
        });
        
    });
  } 

  const HandleAddNewContactPerson = (newElement) => {
    axios.post(conf.toep + 'factsheet/add_entities/',
    {
      entity_type: 'OEO_00000107',
      entity_label: newElement.name,
    }).then(response => {
    if (response.data === 'A new entity added!')
      setOpenAddedDialog(true);
      setAddedEntity(['Contact person', newElement.name ]);

      getContactPersons().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push({ 'id': item.replaceAll('_', ' '), 'name': item.replaceAll('_', ' ') }) )
          setContactPersons(tmp);
        });
        
    });
  } 
  

const scenario_region = [
    { id: 'Germany', name: 'Germany' },
    { id: 'France', name: 'France' },
  ];

  const scenario_input_dataset_region = [
    { id: '1', name: 'Germany' },
    { id: 'Spain', name: 'Spain' },
    { id: '2', name: 'France' },
  ];

  const scenario_interacting_region = [
    { id: '1', name: 'Germany' },
    { id: 'France', name: 'France' },
    { id: 'Spain', name: 'Spain' },
  ];

  const sectorDivisionsHandler = (sectorDivisionsList) => {
    console.log(sectorDivisionsList);
    setSelectedSectorDivisions(sectorDivisionsList);
    const selectedSectorDivisionsIDs = sectorDivisionsList.map(item => item.id);
    const sectorsBasedOnDivisions = sectors.filter(item  => sectorDivisionsList.map(item => item.id).includes(item.sector_divisions_id) );
    setFilteredSectors(sectorsBasedOnDivisions);
  };

  const authorsHandler = (authorsList) => {
    setSelectedAuthors(authorsList);
  };

  const modelsHandler = (modelsList) => {
    setSelectedModels(modelsList);
  };

  const frameworksHandler = (frameworksList) => {
    setSelectedFrameworks(frameworksList);
  };

  const institutionHandler = (institutionList) => {
    setSelectedInstitution(institutionList);
  };

  const fundingSourceHandler = (fundingSourceList) => {
    console.log(fundingSourceList);
    setSelectedFundingSource(fundingSourceList);
  };

  const contactPersonHandler = (contactPersonList) => {
    setselectedContactPerson(contactPersonList);
  };

  const handleClickCloseRemoveReport = () => {
    setRemoveReport(false);
  }

  const energyCarriersHandler = (energyCarriersList) => {
    setSelectedEnergyCarriers(energyCarriersList);
  };

  const expandedEnergyCarriersHandler = (expandedEnergyCarriersList) => {
    setExpandedEnergyCarriers(expandedEnergyCarriersList);
  };

  const selectedSectorsHandler = (sectorsList) => {
    setSelectedSectors(sectorsList);
  };

  const expandedSectorsHandler = (expandedSectorsList) => {
    setExpandedSectors(expandedSectorsList);
  };

  const energyTransformationProcessesHandler = (energyProcessesList) => {
    setSelectedEnergyTransformationProcesses(energyProcessesList);
  };

  const expandedEnergyTransformationProcessesHandler = (expandedEnergyProcessesList) => {
    setExpandedEnergyTransformationProcesses(expandedEnergyProcessesList);
  };

  function a11yProps(index: number) {
    return {
      id: `vertical-tab-${index}`,
      'aria-controls': `vertical-tabpanel-${index}`,
    };
  }

  const handleStudyKeywords = (event) => {
    if (event.target.checked) {
      if (!selectedStudyKewords.includes(event.target.name)) {
        setSelectedStudyKewords([...selectedStudyKewords, event.target.name]);
      }
    } else {
      const filteredStudyKeywords = selectedStudyKewords.filter(i => i !== event.target.name);
      setSelectedStudyKewords(filteredStudyKeywords);
    }
    factsheetObjectHandler('study_keywords', JSON.stringify(selectedStudyKewords));
  }

  const scenarioKeywordsHandler = (event) => {
    const id = event.target.name.split("_")[1];
    const name = event.target.name.split("_")[0];
    const newScenarios = [...scenarios];
    const obj = newScenarios.find(el => el.id === id);
    if (obj)
      if (event.target.checked) {
        if (!obj.keywords.includes(name)) {
          obj.keywords = [...obj.keywords, name];
        }
      } else {
        obj.keywords = obj.keywords.filter(i => i !== name);
      }
    setScenarios(newScenarios);
    factsheetObjectHandler('scenarios', JSON.stringify(newScenarios));
  };

  const energyCarrierData = energy_carriers_json;

  const renderStudy = () => {
    return <Grid container
      direction="row"
      justifyContent="space-between"
      alignItems="center"
    >
      <Grid item xs={6} style={{ marginBottom: '10px' }}>
        <div style={{
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
          }}>
          <TextField style={{  width: '90%', backgroundColor:'#FCFCFC' }} id="outlined-basic" label="What is the name of the study?" variant="outlined" value={studyName} onChange={handleStudyName}/>
          <div>
            <HtmlTooltip
              style={{ marginLeft: '10px' }}
              placement="top"
              title={
                <React.Fragment>
                  <Typography color="inherit" variant="caption">
                    {'A study is a project with the goal to investigate something.'}
                    <br />
                    <a href="http://openenergy-platform.org/ontology/oeo/OEO_00020011">More info from Open Enrgy Ontology (OEO)...</a>
                  </Typography>
                </React.Fragment>
              }
            >
              <HelpOutlineIcon sx={{ color: '#bdbdbd' }}/>
            </HtmlTooltip>
          </div>
        </div>
      </Grid>
      <Grid item xs={6} style={{ marginBottom: '10px' }}>
        <div style={{
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
          }}>
          <TextField style={{  width: '90%',  backgroundColor:'#FCFCFC' }} id="outlined-basic" label="What is the acronym or short title?" variant="outlined" value={acronym} onChange={handleAcronym} />
          <div>
            <HtmlTooltip
              style={{ marginLeft: '10px' }}
              placement="top"
              title={
                <React.Fragment>
                  <Typography color="inherit" variant="caption">
                    {'An acronym is an abbreviation of the title by using the first letters of each part of the title.'}
                    <br />
                    <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000048">More info from Open Enrgy Ontology (OEO)...</a>
                  </Typography>
                </React.Fragment>
              }
            >
              <HelpOutlineIcon sx={{ color: '#bdbdbd' }}/>
            </HtmlTooltip>
          </div>
        </div>
      </Grid>
      <Grid item xs={6} >
        <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              flexWrap: 'wrap',
          }}>
          <CustomAutocomplete type="Institution" showSelectedElements={true} editHandler={HandleEditInstitution} addNewHandler={HandleAddNewInstitution} manyItems optionsSet={institutions} kind='Which institutions are involved in this study?' handler={institutionHandler} selectedElements={selectedInstitution}/>
          <div style={{ marginTop: '30px' }}>
            <HtmlTooltip
              style={{ marginLeft: '10px' }}
              placement="top"
              title={
                <React.Fragment>
                  <Typography color="inherit" variant="caption">
                    {'An institution is an organisation that serves a social purpose.'}
                    <br />
                    <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000238">More info from Open Enrgy Ontology (OEO)...</a>
                  </Typography>
                </React.Fragment>
              }
            >
              <HelpOutlineIcon sx={{ color: '#bdbdbd' }}/>
            </HtmlTooltip>
          </div>
        </div>
      </Grid>
      <Grid item xs={6} >
      <div style={{
            display: 'flex',
            alignItems: 'flex-start',
            flexWrap: 'wrap',
        }}>
        <CustomAutocomplete type="Funding source" showSelectedElements={true} addNewHandler={HandleAddNewFundingSource} manyItems optionsSet={fundingSources} kind='What are the funding sources of this study?' handler={fundingSourceHandler} selectedElements={selectedFundingSource}/>
        <div style={{ marginTop: '30px' }}>
          <HtmlTooltip
            style={{ marginLeft: '10px' }}
            placement="top"
            title={
              <React.Fragment>
                <Typography color="inherit" variant="caption">
                  {'A funder is a sponsor that supports by giving money.'}
                  <br />
                  <a href="http://openenergy-platform.org/ontology/oeo/OEO_00090001">More info from Open Enrgy Ontology (OEO)...</a>
                </Typography>
              </React.Fragment>
            }
          >
            <HelpOutlineIcon sx={{ color: '#bdbdbd' }}/>
          </HtmlTooltip>
        </div>
      </div>
      </Grid>
      <Grid item xs={6} style={{ marginTop: '0px' }}>
        <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              flexWrap: 'wrap',
          }}>
          <TextField style={{ width: '90%', MarginBottom: '10px', marginTop: '5px',  backgroundColor:'#FCFCFC' }} id="outlined-basic" label="Please describe the research questions of the study in max 400 characters." variant="outlined" multiline rows={7} maxRows={10} value={abstract} onChange={handleAbstract}/>
        <div style={{ marginTop: '20px' }}>

        </div>
      </div>
      </Grid>
      <Grid item xs={6} style={{ marginBottom: '10px' }}>
        <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              flexWrap: 'wrap',
          }}>
            <CustomAutocomplete type="Contact person" showSelectedElements={true} addNewHandler={HandleAddNewContactPerson}  manyItems optionsSet={contactPersons} kind='Who is the contact person for this factsheet?' handler={contactPersonHandler} selectedElements={selectedContactPerson}/>
        <div style={{ marginTop: '30px' }}>
          <HtmlTooltip
            style={{ marginLeft: '10px' }}
            placement="top"
            title={
              <React.Fragment>
                <Typography color="inherit" variant="caption">
                  {'A contact person is an agent that can be contacted for help or information about a specific service or good.'}
                  <br />
                  <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000107">More info from Open Enrgy Ontology (OEO)...</a>
                </Typography>
              </React.Fragment>
            }
          >
            <HelpOutlineIcon sx={{ color: '#bdbdbd' }}/>
          </HtmlTooltip>
        </div>
      </div>
      </Grid>
      <Grid item xs={6} style={{ marginBottom: '10px' }}>
      </Grid>
      <Grid
        container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        style={{ 'padding': '20px', 'border': '1px solid #cecece', width: '95%', borderRadius: '5px', backgroundColor:'#FCFCFC' }}
      >
            <Grid item xs={12} >
              <Typography variant="subtitle1" gutterBottom style={{ marginTop:'10px' }}>
                Study content description:
              </Typography>
            </Grid>
            <Grid item xs={6} >
              <div style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    flexWrap: 'wrap',
                }}>
                <CustomAutocomplete showSelectedElements={true} manyItems optionsSet={sector_divisions} kind='Do you use a predefined sector division? ' handler={sectorDivisionsHandler} selectedElements={selectedSectorDivisions}/>
                <div style={{ marginTop: '30px' }}>
                  <HtmlTooltip
                    style={{ marginLeft: '10px' }}
                    placement="top"
                    title={
                      <React.Fragment>
                        <Typography color="inherit" variant="caption">
                          {'A sector division is a specific way to subdivide a system.'}
                          <br />
                          <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000368">More info from Open Enrgy Ontology (OEO)...</a>
                        </Typography>
                      </React.Fragment>
                    }
                  >
                    <HelpOutlineIcon sx={{ color: '#bdbdbd' }}/>
                  </HtmlTooltip>
                  </div>
                </div>
              <CustomTreeViewWithCheckBox size="220px" checked={selectedSectors} expanded={expandedSectors} handler={selectedSectorsHandler} expandedHandler={expandedSectorsHandler} data={filteredSectors} title={"Which sectors are considered in the study?"} toolTipInfo={['A sector is generically dependent continuant that is a subdivision of a system.', 'http://openenergy-platform.org/ontology/oeo/OEO_00000367']} />
              <Typography variant="subtitle1" gutterBottom style={{ marginTop:'10px', marginBottom:'5px' }}>
                What additional keywords describe your study?
              </Typography>
              <div>
                <FormGroup>
                    <div>
                      {
                        study_keywords.map((item) => <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes(item.name)} onChange={handleStudyKeywords} label={item.name} name={item.name} />)
                      }
                  </div>
                </FormGroup>
              </div>
          </Grid>
          <Grid item xs={6} style={{ marginBottom: '10px' }}>
            <CustomTreeViewWithCheckBox size="270px" checked={selectedEnergyCarriers} expanded={expandedEnergyCarriers} handler={energyCarriersHandler} expandedHandler={expandedEnergyCarriersHandler} data={energyCarrierData} title={"What energy carriers are considered?"} toolTipInfo={['An energy carrier is a material entity that has an energy carrier disposition.', 'http://openenergy-platform.org/ontology/oeo/OEO_00020039']} />
            <CustomTreeViewWithCheckBox size="270px" checked={selectedEnergyTransformationProcesses} expanded={expandedEnergyTransformationProcesses} handler={energyTransformationProcessesHandler} expandedHandler={expandedEnergyTransformationProcessesHandler} data={energyTransformationProcesses} title={"Which energy transformation processes are considered?"}
            toolTipInfo={['Energy transformation is a transformation in which one or more certain types of energy as input result in certain types of energy as output.', 'http://openenergy-platform.org/ontology/oeo/OEO_00020003']} />
          </Grid>

      </Grid>
      <Grid
        container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        style={{ 'padding': '20px', 'marginTop': '20px', 'border': '1px solid #cecece', width: '95%', borderRadius: '5px', backgroundColor:'#FCFCFC' }}
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
          <CustomAutocomplete showSelectedElements={true}  manyItems optionsSet={authors} kind='Authors' handler={authorsHandler} selectedElements={selectedAuthors} manyItems />
        </Grid>
      </Grid>
    </Grid>
  }


  const renderScenario = () => {
    return  <div>
              <Box sx={{ flexGrow: 1, bgcolor: 'background.paper', display: 'flex', height:'72vh', overflow: 'auto' }} >
                <Tabs
                  orientation="vertical"
                  variant="scrollable"
                  value={scenarioTabValue}
                  onChange={handleScenarioTabChange}
                  aria-label="Vertical tabs example"
                  sx={{ borderRight: 1, borderColor: 'divider' }}
                  key={'Scenario_tabs'}
                >
                {scenarios.map((item, i) =>
                  <Tab
                    label={'Scenario ' + (Number(i) + Number(1)) }
                    key={'Scenario_tab_' + item.id}
                    style={{ borderTop: '1px dashed #cecece', borderLeft: '1px dashed #cecece', borderBottom: '1px dashed #cecece', marginBottom: '5px',  backgroundColor:'#FCFCFC' }}
                  />
                )}
                  <Box sx={{ 'textAlign': 'center', 'marginTop': '5px', 'paddingLeft': '10px',  'paddingRight': '10px', }} >
                    <Fab
                      color="primary"
                      aria-label="add"
                      size="small"
                      onClick={handleAddScenario}
                    >
                      <AddIcon  />
                    </Fab>
                  </Box>
                </Tabs>
                {scenarios.map((item, i) =>
                  <TabPanel
                    value={scenarioTabValue}
                    index={i}
                    style={{ width: '90%', overflow: 'auto', borderTop: '1px solid #cecece', borderRight: '1px solid #cecece', borderBottom: '1px solid #cecece' }}
                    key={'Scenario_panel_' + item.id}
                  >
                    <Scenario
                      data={item}
                      handleScenariosInputChange={handleScenariosInputChange}
                      handleScenariosAutoCompleteChange={handleScenariosAutoCompleteChange}
                      scenarioKeywordsHandler={scenarioKeywordsHandler}
                      scenariosInputDatasetsHandler={scenariosInputDatasetsHandler}
                      scenariosOutputDatasetsHandler={scenariosOutputDatasetsHandler}
                      removeScenario={removeScenario}
                      scenarioRegion={scenario_region}
                      scenarioSelectedRegions={scenario_region}
                      scenarioInteractingRegion={scenario_interacting_region}
                      scenarioYears={scenario_years}
                    />
                  </TabPanel>
                )}
              </Box>
            </div >
    }


  const items = {
    titles: ['Study', 'Scenarios', 'Models and Frameworks'],
    contents: [
      renderStudy(),
      renderScenario(),
      <Grid container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
      >
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <CustomAutocomplete manyItems showSelectedElements={true} optionsSet={modelsList} kind='Models' handler={modelsHandler} selectedElements={selectedModels}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <CustomAutocomplete manyItems showSelectedElements={true}  optionsSet={frameworksList} kind='Frameworks' handler={frameworksHandler} selectedElements={selectedFrameworks}/>
        </Grid>
      </Grid>,
      ]
  }

  const handleSaveMessageClose = (event: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
      }
      setOpenSavedDialog(false);
  };
  const handleUpdateMessageClose = (event: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
      }
      setOpenUpdatedDialog(false);
  };


  return (
    <div>
      <Grid container
      direction="row"
      justifyContent="space-between"
      alignItems="center"
    >
        <Grid item xs={4} >
        <div>
              <CustomSwap handleSwap={handleSwap} />
        </div >
        </Grid>
        <Grid item xs={4} >
        <div  style={{ 'textAlign': 'center', 'marginTop': '10px' }}>
          <Typography variant="h6" gutterBottom>
            <b>{acronym}</b>
          </Typography>
        </div>
        </Grid>
        <Grid item xs={4} >
          <div style={{ 'textAlign': 'right' }}>
            <Tooltip title="Save factsheet">
              <Button disableElevation={true} size="medium" style={{ 'height': '42px', 'textTransform': 'none', 'marginTop': '10px', 'marginRight': '10px', 'zIndex': '1000' }} variant="contained" color="success" onClick={handleSaveFactsheet} ><SaveIcon /> </Button>
              </Tooltip>
            {/* <Tooltip title="Share this factsheet">
              <Fab disableElevation={true} size="medium" style={{ 'textTransform': 'none', 'marginTop': '10px', 'marginRight': '10px', 'zIndex': '1000' }} variant="contained" color="secondary" > <ShareIcon /> </Fab>
            </Tooltip> */}
            <Tooltip title="Delete factsheet">
              <Button disableElevation={true} size="medium" style={{ 'height': '42px', 'textTransform': 'none', 'marginTop': '10px', 'marginRight': '10px', 'zIndex': '1000' }} variant="contained" color="error" onClick={handleClickOpenRemovedDialog}> <DeleteOutlineIcon /> </Button>
            </Tooltip>
          </div >
        </Grid>
        <Grid item xs={12}>
          <Snackbar
            open={openSavedDialog}
            autoHideDuration={6000}
            onClose={handleSaveMessageClose}
          >
            <Alert variant="filled" onClose={handleSaveMessageClose} severity="success" sx={{ width: '100%' }}>
              <AlertTitle>New message</AlertTitle>
              Factsheet saved <strong>successfully!</strong>
            </Alert>
          </Snackbar>
          <Snackbar
            open={openUpdatedDialog}
            autoHideDuration={6000}
            onClose={handleUpdateMessageClose}
          >
            <Alert variant="filled" onClose={handleUpdateMessageClose} severity="success" sx={{ width: '100%' }}>
              <AlertTitle>New message</AlertTitle>
              Factsheet updated <strong>successfully!</strong>
            </Alert>
          </Snackbar>
          <Snackbar
            open={openExistDialog}
            autoHideDuration={6000}
            onClose={handleCloseExistDialog}
          >
            <Alert variant="filled" onClose={handleCloseExistDialog} severity="error" sx={{ width: '100%' }}>
              <AlertTitle>Duplicate</AlertTitle>
              Another factsheet with this acronym exists. Please choose another acronym!
            </Alert>
          </Snackbar>
          <Snackbar
            open={openAddedDialog}
            autoHideDuration={6000}
            onClose={handleAddedMessageClose}
          >
            <Alert variant="filled" onClose={handleAddedMessageClose} severity="info" sx={{ width: '100%' }}>
              <AlertTitle>A new entity added to the OEKG</AlertTitle>
              <p>
                Type: <strong>{addedEntity[0]}  </strong>
                Name: <strong>{addedEntity[1]} </strong>
              </p>
              <p>It will be assigned to your factsheet upon saving!</p>
            </Alert>
          </Snackbar>
          <Snackbar
            open={openEditDialog}
            autoHideDuration={6000}
            onClose={handleEditMessageClose}
          >
            <Alert variant="filled" onClose={handleEditMessageClose} severity="info" sx={{ width: '100%' }}>
              <AlertTitle>An entity has been edited in OEKG</AlertTitle>
              <p>
                Type: <strong>{editedEntity[0]}  </strong>
                Old label: <strong>{editedEntity[1]} </strong>
                New label: <strong>{editedEntity[2]} </strong>
              </p>
            </Alert>
          </Snackbar>
          <Dialog
            maxWidth="md"
            open={removeReport}
            onClose={handleClickCloseRemoveReport}
            aria-labelledby="responsive-dialog-title"
          >
            <DialogTitle id="responsive-dialog-title">
              <b>Remove</b>
            </DialogTitle>
            <DialogContent>
              <DialogContentText>
                <div>
                  <pre>
                    Your selected scenario is now removed from your factsheet!
                  </pre>
                </div>
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button variant="contained" onClick={handleClickCloseRemoveReport} >
                Ok
              </Button>
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
              <b>Warning!</b>
            </DialogTitle>
            <DialogContent>
              <DialogContentText>
                <div>
                  <pre>
                    Are you sure about removing the <b>{acronym}</b> from Open Energy Platform?
                  </pre>
                </div>
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Link to={`factsheet/`} onClick={() => { axios.post(conf.toep + 'factsheet/delete/', null, { params: { id: id } }).then(response => setOpenRemovedDialog(true));
                this.reloadRoute();}} className="btn btn-primary" style={{ textDecoration: 'none', color: 'blue', marginRight: '10px' }}>
              <Button variant="contained" color="error" >
                Yes
              </Button>
              </Link>
              <Button variant="contained" onClick={handleClickCloseRemovedDialog}  >
              Cancel
              </Button>
            </DialogActions>
          </Dialog>

          {mode === "edit" &&
            <div className='wizard'>
                <Grid container >
                  <Grid item xs={12} >
                    <CustomTabs
                      factsheetObjectHandler={factsheetObjectHandler}
                      items={items}
                    />
                  </Grid>
                </Grid>
            </div>
          }
          {mode === "overview" &&
            <div style={{
              'marginTop': '10px',
              'overflow': 'auto',
              'marginBottom': '20px',
              'marginLeft': '10px',
              'marginRight': '10px',
              border: '1px dashed #cecece',
              padding: '20px',
              overflow: 'scroll',
              borderRadius: '5px',
              backgroundColor:'#FCFCFC',
              display: "flex"
            }}>
                  <Box
                    sx={{
                      'marginTop': '10px',
                      'overflow': 'auto',
                      'marginBottom': '20px',
                      'marginLeft': '10px',
                      'marginRight': '10px',
                      'overflow': 'scroll',
                      'width': '45%'
                    }}
                  >
                    <Typography variant="body1" gutterBottom component="div">
                      Study name:
                      <b> {studyName}</b>
                    </Typography>
                    <Typography variant="body1" gutterBottom component="div">
                      Acronym:
                      <b> {acronym}</b>
                    </Typography>
                    <Typography variant="body1" gutterBottom component="div">
                      Contact person(s):
                        {selectedContactPerson.map((v, i) => (
                        <span><b> {v.name}</b> {i + 1 !== selectedContactPerson.length && ',' } </span>  
                      ))}
                    </Typography>
                    <Typography variant="body1" gutterBottom component="div">
                      Abstract:
                      <b> {abstract}</b>
                    </Typography>
                    <Typography variant="body1" gutterBottom component="div">
                      Study report information:
                    </Typography>
                    <Typography sx={{ 'marginLeft': '20px' }} variant="body1" gutterBottom component="div">
                      Title:
                      <b> {report_title}</b>
                    </Typography>
                    <Typography sx={{ 'marginLeft': '20px' }} variant="body1" gutterBottom component="div">
                      DOI:
                      <b> {doi}</b>
                    </Typography>
                    <Typography sx={{ 'marginLeft': '20px' }} variant="body1" gutterBottom component="div">
                      Link:
                      <b> {link_to_study}</b>
                    </Typography>
                    <Typography sx={{ 'marginLeft': '20px' }} variant="body1" gutterBottom component="div">
                      Date of publication:
                      <b> {date_of_publication != undefined && date_of_publication.toString()}</b>
                    </Typography>
                    <Typography sx={{ 'marginLeft': '20px' }} variant="body1" gutterBottom component="div">
                      Place of publication:
                      <b> {place_of_publication}</b>
                    </Typography>
                    <Typography sx={{ 'marginLeft': '20px' }} variant="body1" gutterBottom component="div">
                        Authors:   
                        {selectedAuthors.map((v, i) => (
                          <span><b> {v.name}</b> {i + 1 !== authors.length && ',' } </span>  
                        ))}
                    </Typography>
                  </Box>  
                  <Box
                      sx={{
                      'marginTop': '10px',
                      'overflow': 'auto',
                      'marginLeft': '10px',
                      'marginRight': '10px',
                      'overflow': 'scroll',
                      'width': '45%'
                    }}
                  >
                  <Typography sx={{ 'marginTop': '10px' }} variant="body1" gutterBottom component="div">
                      Institutions:
                      {selectedInstitution.map((v, i) => (
                      <span> <b>{v.name}</b> {i + 1 !== selectedInstitution.length && ',' } </span>  
                      ))}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="body1" gutterBottom component="div">
                      Funding sources:   
                      {selectedFundingSource.map((v, i) => (
                        <span><b> {v.name}</b> {i + 1 !== selectedFundingSource.length && ',' } </span>  
                      ))}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="body1" gutterBottom component="div">
                      Sector divisions:   
                      {selectedSectorDivisions.map((v, i) => (
                        <span><b> {v.name}</b> {i + 1 !== selectedSectorDivisions.length && ',' } </span>  
                      ))}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="body1" gutterBottom component="div">
                      Sectors:   
                      {selectedSectors.map((v, i) => (
                        <span><b> {v}</b> {i + 1 !== selectedSectors.length && ',' } </span>  
                      ))}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="body1" gutterBottom component="div">
                      Energy carriers:   
                      {selectedEnergyCarriers.map((v, i) => (
                        <span><b> {v}</b> {i + 1 !== selectedEnergyCarriers.length && ',' } </span>  
                      ))}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="body1" gutterBottom component="div">
                      Energy Transformation Processes:   
                      {selectedEnergyTransformationProcesses.map((v, i) => (
                        <span><b> {v}</b> {i + 1 !== selectedEnergyTransformationProcesses.length && ',' } </span>  
                      ))}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="body1" gutterBottom component="div">
                      Keywords:   
                      {selectedStudyKewords.map((v, i) => (
                        <span><b> {v}</b> {i + 1 !== selectedStudyKewords.length && ',' } </span>  
                      ))}
                  </Typography>
                </Box>
            </div>
          }
      </Grid>
    </Grid>
  </div>
  );
}

export default Factsheet;
