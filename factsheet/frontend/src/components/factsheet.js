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
import CustomAutocompleteWithoutEdit from './customAutocompleteWithoutEdit';
import Scenario from './scenario.js';
// import CustomTreeViewWithCheckBox from './customTreeViewWithCheckbox.js';
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
// import study_keywords from '../data/study_keywords.json';
// import scenario_years from '../data/scenario_years.json';
// import sectors_json from   '../data/sectors.json';
// import energyTransformations from '../data/energyTransformations';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import StepContent from '@mui/material/StepContent';
import CircularProgress from '@mui/material/CircularProgress';
import Badge from '@mui/material/Badge';

import { Route, Routes, useNavigate } from 'react-router-dom';

import Chip from '@mui/material/Chip';

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

  const [activeStep, setActiveStep] = React.useState(0);
  const steps = getSteps();

  const { id, fsData } = props;
  const [openSavedDialog, setOpenSavedDialog] = useState(false);
  const [openUpdatedDialog, setOpenUpdatedDialog] = useState(false);
  const [openExistDialog, setOpenExistDialog] = useState(false);
  const [emptyAcronym, setEmptyAcronym] = useState(false);
  const [openRemoveddDialog, setOpenRemovedDialog] = useState(false);
  const [mode, setMode] = useState(id === "new" ? "edit" : "overview");
  const [factsheetObject, setFactsheetObject] = useState({});
  const [factsheetName, setFactsheetName] = useState(id !== 'new' ? '' : '');
  const [acronym, setAcronym] = useState(id !== 'new' ? fsData.acronym : '');
  const [uid, setUID] = useState(id !== 'new' ? fsData.uid : '');
  const [prevUID, setPrevUID] = useState(id !== 'new' ? fsData.acronym : '');
  const [studyName, setStudyName] = useState(id !== 'new' ? fsData.study_name : '');
  const [abstract, setAbstract] = useState(id !== 'new' ? fsData.abstract : '');
  const [selectedSectors, setSelectedSectors] = useState(id !== 'new' ? fsData.sectors : []);
  const [expandedSectors, setExpandedSectors] = useState(id !== 'new' ? [] : []);
  const [institutions, setInstitutions] = useState([]);
  const [authors, setAuthors] = useState([]);
  const [fundingSources, setFundingSources] = useState([]);
  const [contactPersons, setContactPersons] = useState([]);
  const [isCreated, setIsCreated] = useState(false);
  const [scenarioRegions, setScenarioRegions] = useState([]);
  const [scenarioInteractingRegions, setScenarioInteractingRegions] = useState([]);
  const [scenarioYears, setScenarioYears] = useState([]);
  const [models, setModels] = useState([]);
  const [frameworks, setFrameworks] = useState([]);

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };
  
  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };
  
  const handleReset = () => {
    setActiveStep(0);
  };

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


 // const [sectors, setSectors] = useState(sectors_json);

  const [sectors, setSectors] = useState([]);
  const [filteredSectors, setFilteredSectors] = useState(id !== 'new' ? fsData.sectors : []);
  const [selectedSectorDivisions, setSelectedSectorDivisions] = useState(id !== 'new' ? fsData.sector_divisions : []);
  const [selectedAuthors, setSelectedAuthors] = useState(id !== 'new' ? fsData.authors : []);
  const [selectedInstitution, setSelectedInstitution] = useState(id !== 'new' ? fsData.institution : []);
  const [selectedFundingSource, setSelectedFundingSource] = useState(id !== 'new' ? fsData.funding_sources : []);
  const [selectedContactPerson, setselectedContactPerson] = useState(id !== 'new' ? fsData.contact_person : []);
  const [report_title, setReportTitle] = useState(id !== 'new' ? fsData.report_title : '');
  const [date_of_publication, setDateOfPublication] = useState(id !== 'new' ? fsData.date_of_publication : '01-01-1900');
  const [doi, setDOI] = useState(id !== 'new' ? fsData.report_doi : '');
  const [place_of_publication, setPlaceOfPublication] = useState(id !== 'new' ? fsData.place_of_publication : '');
  const [link_to_study, setLinkToStudy] = useState(id !== 'new' ? fsData.link_to_study : '');
  const [scenarios, setScenarios] = useState(id !== 'new' ? fsData.scenarios : [{
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
  const [expandedEnergyCarriers, setExpandedEnergyCarriers] = useState([]);
  const [selectedEnergyTransformationProcesses, setSelectedEnergyTransformationProcesses] = useState(id !== 'new' ? fsData.energy_transformation_processes : []);
  const [expandedEnergyTransformationProcesses, setExpandedEnergyTransformationProcesses] = useState([]);
  const [selectedStudyKewords, setSelectedStudyKewords] = useState(id !== 'new' ? fsData.study_keywords : []);
  // const [selectedStudyKewords, setSelectedStudyKewords] = useState(id !== 'new' ? [] : []);
  const [selectedModels, setSelectedModels] = useState(id !== 'new' ? fsData.models : []);
  const [selectedFrameworks, setSelectedFrameworks] = useState(id !== 'new' ? fsData.frameworks : []);
  const [removeReport, setRemoveReport] = useState(false);
  const [addedEntity, setAddedEntity] = useState(false);
  const [openAddedDialog, setOpenAddedDialog] = React.useState(false);
  const [openEditDialog, setOpenEditDialog] = React.useState(false);
  const [editedEntity, setEditedEntity] = useState(false);
  const [scenarioTabValue, setScenarioTabValue] = React.useState(0);
  const [energyTransformationProcesses, setEnergyTransformationProcesses] = React.useState([]);
  const [energyCarriers, setEnergyCarries] = React.useState([]);

  const StudyKeywords = [
    'resilience',
    'life cycle analysis',
    'CO2 emissions',
    'Greenhouse gas emissions',
    'Reallabor',
    '100% renewables',
    'acceptance',
    'sufficiency',
    '(changes in) demand',
    'degree of electrifiaction',
    'regionalisation',
    'total gross electricity generation',
    'total net electricity generation',
    'peak electricity generation'
  ];

  const handleScenarioTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setScenarioTabValue(newValue);
  }

  const populateFactsheetElements = async () => {
    const { data } = await axios.get(conf.toep + `factsheet/populate_factsheets_elements/`);
    return data;
  };

  const getNodeIds = (nodes) => {
    let ids = [];
  
    nodes?.forEach(({ value, children }) => {
      ids = [...ids, value, ...getNodeIds(children)];
    });
    return ids;
  };

  useEffect(() => {
    populateFactsheetElements().then((data) => {
      setEnergyTransformationProcesses(data.energy_transformation_processes);
      setEnergyCarries(data.energy_carriers);
      let energy_carriers_ids = [];
      data.energy_carriers.forEach(({ value, children }) => {
        energy_carriers_ids = [...energy_carriers_ids, value, ...getNodeIds(children)];
      });
      setExpandedEnergyCarriers(energy_carriers_ids);

      let energy_transformation_processes_ids = [];
      data.energy_transformation_processes.forEach(({ value, children }) => {
        energy_transformation_processes_ids = [...energy_transformation_processes_ids, value, ...getNodeIds(children)];
      });
      setExpandedEnergyTransformationProcesses(energy_transformation_processes_ids);

      });
  }, []);

  const handleSaveFactsheet = () => {
    factsheetObjectHandler('name', factsheetName);
    if (acronym !== '') {
      if (id === 'new' && !isCreated) {
        const new_uid = uuid()
        axios.post(conf.toep + 'factsheet/add/',
        {
          id: id,
          uid: new_uid,
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
          report_doi: doi,
          place_of_publication: place_of_publication,
          link_to_study: link_to_study,
          authors: JSON.stringify(selectedAuthors),
          scenarios: JSON.stringify(scenarios),
          models: JSON.stringify(selectedModels),
          frameworks: JSON.stringify(selectedFrameworks),
        }).then(response => {
        if (response.data === 'Factsheet saved') {
          navigate('/factsheet/fs/' + new_uid);
          setIsCreated(true);
          setOpenSavedDialog(true);
          setUID(new_uid);
        }
        else if (response.data === 'Factsheet exists') {
          setOpenExistDialog(true);
        }
      });
      } else {
        console.log(uid);
        axios.get(conf.toep + `factsheet/get/`, { params: { id: uid } }).then(res => {
          axios.post(conf.toep + 'factsheet/update/',
          {
            fsData: res.data,
            id: id,
            uid: uid,
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
            report_doi: doi,
            place_of_publication: place_of_publication,
            link_to_study: link_to_study,
            authors: JSON.stringify(selectedAuthors),
            scenarios: JSON.stringify(scenarios),
            models: JSON.stringify(selectedModels),
            frameworks: JSON.stringify(selectedFrameworks),
            energy_transformation_processes: JSON.stringify(selectedEnergyTransformationProcesses),
          }).then(response => {
            if (response.data === "factsheet updated!") {
              setUID(uid);
              setOpenUpdatedDialog(true);
            }
            else if (response.data === 'Factsheet exists') {
              setOpenExistDialog(true);
            }
          });
        });
      }
     
    } else {
      setEmptyAcronym(true);
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
    setEmptyAcronym(false);
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
    console.log(selectedList, name, idx);
    const newScenarios = [...scenarios];
    const obj = newScenarios.find(el => el.id === idx);
    if (obj)
      obj[name] = selectedList
    setScenarios(newScenarios);
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
    const { data } = await axios.get(conf.toep + `factsheet/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000238' } });
    return data;
  };

  const getFundingSources = async () => {
    const { data } = await axios.get(conf.toep + `factsheet/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00090001' } });
    return data;
  };

  const getContactPersons = async () => {
    const { data } = await axios.get(conf.toep + `factsheet/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000107' } });
    return data;
  };

  const getAuthors = async () => {
    const { data } = await axios.get(conf.toep + `factsheet/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000064' } });
    return data;
  };

  const getScenarioRegions = async () => {
    const { data } = await axios.get(conf.toep + `factsheet/get_entities_by_type/`, { params: { entity_type: 'OBO.BFO_0000006' } });
    return data;
  };

  const getScenarioInteractingRegions = async () => {
    const { data } = await axios.get(conf.toep + `factsheet/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00020036' } });
    return data;
  };

  const getScenarioYears = async () => {
    const { data } = await axios.get(conf.toep + `factsheet/get_entities_by_type/`, { params: { entity_type: 'OBO.OEO_00020097' } });
    return data;
  };

  const getModels = async () => {
    const { data } = await axios.get(conf.toep + `factsheet/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000274' } });
    return data;
  };

  const getFrameworks = async () => {
    const { data } = await axios.get(conf.toep + `factsheet/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000172' } });
    return data;
  };

  useEffect(() => {
    getInstitution().then((data) => {
      const tmp = [];
      data.map( (item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }) );
      setInstitutions(tmp);
      });
  }, []);

  useEffect(() => {
    getFundingSources().then((data) => {
      const tmp = [];
      data.map( (item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }) )
      setFundingSources(tmp);
      });
  }, []);

  useEffect(() => {
    getContactPersons().then((data) => {
      const tmp = [];
      data.map( (item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }) )
      setContactPersons(tmp);
      });
  }, []);

  useEffect(() => {
    getAuthors().then((data) => {
      const tmp = [];
      data.map( (item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }) )
      setAuthors(tmp);
      });
  }, []);

  useEffect(() => {
    getScenarioRegions().then((data) => {
      const tmp = [];
      data.map( (item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }) )
      setScenarioRegions(tmp);
      });
  }, []);

  useEffect(() => {
    getScenarioInteractingRegions().then((data) => {
      const tmp = [];
      data.map( (item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }) )
      setScenarioInteractingRegions(tmp);
      });
  }, []);

  useEffect(() => {
    getScenarioYears().then((data) => {
      const tmp = [];
      data.map( (item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }) )
      setScenarioYears(tmp);
      });
  }, []);

  useEffect(() => {
    getModels().then((data) => {
      const tmp = [];
      data.map( (item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }) )
      setModels(tmp);
      });
  }, []);

  useEffect(() => {
    getFrameworks().then((data) => {
      const tmp = [];
      data.map( (item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }) )
      setFrameworks(tmp);
      });
  }, []);


  const HandleAddNewInstitution = (newElement) => {
    axios.post(conf.toep + 'factsheet/add_entities/',
    {
      entity_type: 'OEO.OEO_00000238',
      entity_label: newElement.name,
      entity_iri: newElement.iri
    }).then(response => {
    if (response.data === 'A new entity added!') {
      setOpenAddedDialog(true);
      setAddedEntity(['Institution', newElement.name ]);
      getInstitution().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setInstitutions(tmp);
        });
    }
    });
  } 


  const HandleEditInstitution = (oldElement, newElement, editIRI) => {
    console.log(editIRI);
    axios.post(conf.toep + 'factsheet/update_an_entity/',
    {
      entity_type: 'OEO.OEO_00000238',
      entity_label: oldElement,
      new_entity_label: newElement,
      entity_iri: editIRI
    }).then(response => {
    if (response.data === 'entity updated!') {
      setOpenEditDialog(true);
      setEditedEntity(['Institution', oldElement, newElement ]);
      getInstitution().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setInstitutions(tmp);
        });
    }
    });
  } 

  const HandleAddNewFundingSource = (newElement) => {
    axios.post(conf.toep + 'factsheet/add_entities/',
    {
      entity_type: 'OEO.OEO_00090001',
      entity_label: newElement.name,
      entity_iri: newElement.iri
    }).then(response => {
    if (response.data === 'A new entity added!')
      setOpenAddedDialog(true);
      setAddedEntity(['Funding source', newElement.name ]);
      getFundingSources().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setFundingSources(tmp);
        });
    });
  } 

  const HandleEditFundingSource = (oldElement, newElement, editIRI) => {
    console.log(editIRI)
    axios.post(conf.toep + 'factsheet/update_an_entity/',
    {
      entity_type: 'OEO.OEO_00090001',
      entity_label: oldElement,
      new_entity_label: newElement,
      entity_iri: editIRI
    }).then(response => {
    if (response.data === 'entity updated!') {
      setOpenEditDialog(true);
      setEditedEntity(['Funding source', oldElement, newElement ]);
      getFundingSources().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setFundingSources(tmp);
        });
    }
    });
  } 

  const HandleAddNewContactPerson = (newElement) => {
    axios.post(conf.toep + 'factsheet/add_entities/',
    {
      entity_type: 'OEO.OEO_00000107',
      entity_label: newElement.name,
      entity_iri: newElement.iri
    }).then(response => {
    if (response.data === 'A new entity added!')
      setOpenAddedDialog(true);
      setAddedEntity(['Contact person', newElement.name ]);

      getContactPersons().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setContactPersons(tmp);
        });
    });
  } 

  const HandleEditContactPerson = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'factsheet/update_an_entity/',
    {
      entity_type: 'OEO.OEO_00000107',
      entity_label: oldElement,
      new_entity_label: newElement,
      entity_iri: editIRI
    }).then(response => {
    if (response.data === 'entity updated!') {
      setOpenEditDialog(true);
      setEditedEntity(['Contact person', oldElement, newElement ]);
      getAuthors().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setAuthors(tmp);
        });
    }
    });
  } 

  const HandleAddNewAuthor = (newElement) => {
    axios.post(conf.toep + 'factsheet/add_entities/',
    {
      entity_type: 'OEO.OEO_00000064',
      entity_label: newElement.name,
      entity_iri: newElement.iri
    }).then(response => {
    if (response.data === 'A new entity added!')
      setOpenAddedDialog(true);
      setAddedEntity(['Author', newElement.name ]);

      getAuthors().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setAuthors(tmp);
        });
    });
  }

  const HandleEditAuthors = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'factsheet/update_an_entity/',
    {
      entity_type: 'OEO.OEO_00000064',
      entity_label: oldElement,
      new_entity_label: newElement,
      entity_iri: editIRI
    }).then(response => {
    if (response.data === 'entity updated!') {
      setOpenEditDialog(true);
      setEditedEntity(['Author', oldElement, newElement ]);
      getAuthors().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setAuthors(tmp);
        });
    }
    });
  }

  const HandleAddNewRegion = (newElement) => {
    axios.post(conf.toep + 'factsheet/add_entities/',
    {
      entity_type: 'OBO.BFO_0000006', 
      entity_label: newElement.name,
      entity_iri: newElement.iri
    }).then(response => {
    if (response.data === 'A new entity added!')
      setOpenAddedDialog(true);
      setAddedEntity(['Spatial region', newElement.name ]);

      getScenarioRegions().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setScenarioRegions(tmp);
        });
    });
  }

  const HandleEditRegion = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'factsheet/update_an_entity/',
    {
      entity_type: 'OBO.BFO_0000006',
      entity_label: oldElement,
      new_entity_label: newElement,
      entity_iri: editIRI
    }).then(response => {
    if (response.data === 'entity updated!') {
      setOpenEditDialog(true);
      setEditedEntity(['Spatial region', oldElement, newElement ]);
      getScenarioRegions().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setScenarioRegions(tmp);
        });
    }
    });
  }

  const HandleAddNewInteractingRegion = (newElement) => {
    axios.post(conf.toep + 'factsheet/add_entities/',
    {
      entity_type: 'OEO.OEO_00020036',
      entity_label: newElement.name,
      entity_iri: newElement.iri
    }).then(response => {
    if (response.data === 'A new entity added!')
      setOpenAddedDialog(true);
      setAddedEntity(['Interacting region', newElement.name ]);

      getScenarioInteractingRegions().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setScenarioInteractingRegions(tmp);
        });
    });
  }
  
  const HandleEditInteractingRegion = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'factsheet/update_an_entity/',
    {
      entity_type: 'OEO.OEO_00020036',
      entity_label: oldElement,
      new_entity_label: newElement,
      entity_iri: editIRI
    }).then(response => {
    if (response.data === 'entity updated!') {
      setOpenEditDialog(true);
      setEditedEntity(['Interacting region', oldElement, newElement ]);
      getScenarioInteractingRegions().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setScenarioInteractingRegions(tmp);
        });
    }
    });
  }

  const HandleAddNNewScenarioYears = (newElement) => {
    axios.post(conf.toep + 'factsheet/add_entities/',
    {
      entity_type: 'OBO.OEO_00020097',
      entity_label: newElement.name,
      entity_iri: newElement.iri
    }).then(response => {
    if (response.data === 'A new entity added!')
      setOpenAddedDialog(true);
      setAddedEntity(['Scenario year', newElement.name ]);

      getScenarioYears().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setScenarioYears(tmp);
        });
    });
  }

  const HandleEditScenarioYears = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'factsheet/update_an_entity/',
    {
      entity_type: 'OBO.OEO_00020097',
      entity_label: oldElement,
      new_entity_label: newElement,
      entity_iri: editIRI
    }).then(response => {
    if (response.data === 'entity updated!') {
      setOpenEditDialog(true);
      setEditedEntity(['Scenario year', oldElement, newElement ]);
      getScenarioYears().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setScenarioYears(tmp);
        });
    }
    });
  }

  const HandleAddNewModel = (newElement) => {
    axios.post(conf.toep + 'factsheet/add_entities/',
    {
      entity_type: 'OEO.OEO_00000274',
      entity_label: newElement.name,
      entity_iri: newElement.iri
    }).then(response => {
    if (response.data === 'A new entity added!')
      setOpenAddedDialog(true);
      setAddedEntity(['Model', newElement.name ]);

      getModels().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setModels(tmp);
        });
    });
  }

  const HandleEditModels = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'factsheet/update_an_entity/',
    {
      entity_type: 'OEO.OEO_00000274',
      entity_label: oldElement,
      new_entity_label: newElement,
      entity_iri: editIRI
    }).then(response => {
    if (response.data === 'entity updated!') {
      setOpenEditDialog(true);
      setEditedEntity(['Model', oldElement, newElement ]);
      getModels().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setModels(tmp);
        });
    }
    });
  }

  const HandleAddNewFramework = (newElement) => {
    axios.post(conf.toep + 'factsheet/add_entities/',
    {
      entity_type: 'OEO.OEO_00000172',
      entity_label: newElement.name,
      entity_iri: newElement.iri
    }).then(response => {
    if (response.data === 'A new entity added!')
      setOpenAddedDialog(true);
      setAddedEntity(['Framework', newElement.name ]);

      getFrameworks().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setFrameworks(tmp);
        });
    });
  }

  const HandleEditFramework = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'factsheet/update_an_entity/',
    {
      entity_type: 'OEO.OEO_00000172',
      entity_label: oldElement,
      new_entity_label: newElement,
      entity_iri: editIRI
    }).then(response => {
    if (response.data === 'entity updated!') {
      setOpenEditDialog(true);
      setEditedEntity(['Framework', oldElement, newElement ]);
      getFrameworks().then((data) => {
        const tmp = [];
          data.map( (item) => tmp.push(item) )
          setFrameworks(tmp);
        });
    }
    });
  }

  const sectorDivisionsHandler = (sectorDivisionsList) => {
    console.log(sectorDivisionsList);
    
    setSelectedSectorDivisions(sectorDivisionsList);
    //const selectedSectorDivisionsIDs = sectorDivisionsList.map(item => item.id);
    //const sectorsBasedOnDivisions = sectors.filter(item  => sectorDivisionsList.map(item => item.id).includes(item.sector_divisions_id) );
    //setFilteredSectors(sectorsBasedOnDivisions);
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
    setSelectedFundingSource(fundingSourceList);
  };

  const contactPersonHandler = (contactPersonList) => {
    setselectedContactPerson(contactPersonList);
  };

  const handleClickCloseRemoveReport = () => {
    setRemoveReport(false);
  }

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

  const energyCarriersHandler = (energyCarriersList, nodes) => {
    const zipped = []
    energyCarriersList.map((v) => zipped.push({"value": findNestedObj(nodes, 'value', v).value, "label": findNestedObj(nodes, 'value', v).label, "class": findNestedObj(nodes, 'value', v).class}));
    setSelectedEnergyCarriers(zipped);
  };


  const expandedEnergyCarriersHandler = (expandedEnergyCarriersList) => {
    setExpandedEnergyCarriers(expandedEnergyCarriersList);
  };

  const sectorsHandler = (sectorsList, nodes) => {
    const zipped = []
    sectorsList.map((v) => zipped.push({"value": findNestedObj(nodes, 'value', v).value, "label": findNestedObj(nodes, 'value', v).label, "class": findNestedObj(nodes, 'value', v).class}));
    console.log(zipped);
    setSelectedSectors(zipped);
  };

  const expandedSectorsHandler = (expandedSectorsList) => {
    const zipped = []
    expandedSectorsList.map((v) => zipped.push({ "value": v, "label": v }));
    setExpandedSectors(zipped);
  };

  const energyTransformationProcessesHandler = (energyProcessesList, nodes) => {
    const zipped = []
    energyProcessesList.map((v) => zipped.push({"value": findNestedObj(nodes, 'value', v).value, "label": findNestedObj(nodes, 'value', v).label, "class": findNestedObj(nodes, 'value', v).class}));
    setSelectedEnergyTransformationProcesses(zipped);
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
        <CustomAutocomplete type="Funding source" showSelectedElements={true} editHandler={HandleEditFundingSource} addNewHandler={HandleAddNewFundingSource} manyItems optionsSet={fundingSources} kind='What are the funding sources of this study?' handler={fundingSourceHandler} selectedElements={selectedFundingSource}/>
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
            <CustomAutocomplete type="Contact person" showSelectedElements={true}  editHandler={HandleEditContactPerson} addNewHandler={HandleAddNewContactPerson}  manyItems optionsSet={contactPersons} kind='Who is the contact person for this factsheet?' handler={contactPersonHandler} selectedElements={selectedContactPerson}/>
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
                {/* <CustomAutocompleteWithoutEdit type="sector_division" showSelectedElements={true} manyItems optionsSet={sector_divisions_json} kind='Do you use a predefined sector division? ' handler={sectorDivisionsHandler} selectedElements={selectedSectorDivisions}/> */}
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
              {/* <CustomTreeViewWithCheckBox showFilter={false} size="260px" checked={selectedSectors} expanded={expandedSectors} handler={sectorsHandler} expandedHandler={expandedSectorsHandler} data={sectors_json} title={"Which sectors are considered in the study?"} toolTipInfo={['A sector is generically dependent continuant that is a subdivision of a system.', 'http://openenergy-platform.org/ontology/oeo/OEO_00000367']} /> */}
              <Typography variant="subtitle1" gutterBottom style={{ marginTop:'30px', marginBottom:'10px' }}>
                What additional keywords describe your study?
              </Typography>
              <div style={{ marginTop: "10px" }}>
                <FormGroup>
                    <div>
                      {
                        selectedStudyKewords.map((item) => <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes(item.name)} onChange={handleStudyKeywords} label={item.name} name={item.name} />)
                      }
                  </div>
                </FormGroup>
              </div>
          </Grid>
          <Grid item xs={6} style={{ marginBottom: '10px' }}>
            {/* <CustomTreeViewWithCheckBox showFilter={true} size="200px" checked={selectedEnergyCarriers} expanded={expandedEnergyCarriers} handler={energyCarriersHandler} expandedHandler={expandedEnergyCarriersHandler} data={energyCarriers} title={"What energy carriers are considered?"} toolTipInfo={['An energy carrier is a material entity that has an energy carrier disposition.', 'http://openenergy-platform.org/ontology/oeo/OEO_00020039']} /> */}
            {/* <CustomTreeViewWithCheckBox showFilter={true} size="200px" checked={selectedEnergyTransformationProcesses} expanded={expandedEnergyTransformationProcesses} handler={energyTransformationProcessesHandler} expandedHandler={expandedEnergyTransformationProcessesHandler} data={energyTransformationProcesses} title={"Which energy transformation processes are considered?"} */}
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
          <CustomAutocomplete type="Author" showSelectedElements={true} editHandler={HandleEditAuthors}  addNewHandler={HandleAddNewAuthor}  manyItems optionsSet={authors} kind='Authors' handler={authorsHandler} selectedElements={selectedAuthors}  />
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
                    label={item.acronym !== '' ? item.acronym.substring(0,14) : 'Scenario ' + (Number(i) + Number(1)) }
                    key={'Scenario_tab_' + item.id}
                    style={{ borderTop: '1px dashed #cecece', borderLeft: '1px dashed #cecece', borderBottom: '1px dashed #cecece', marginBottom: '5px',  backgroundColor:'#FCFCFC', width:'150px' }}
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
                    style={{ width: '90%', overflow: 'auto', borderTop: '1px solid #cecece', borderRight: '1px solid #cecece', borderBottom: '1px solid #cecece',  backgroundColor:'#FCFCFC' }}
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
                      scenarioRegion={scenarioRegions}
                      scenarioInteractingRegion={scenarioInteractingRegions}
                      scenarioYears={scenarioYears}
                      HandleEditRegion={HandleEditRegion}
                      HandleAddNewRegion={HandleAddNewRegion}
                      HandleEditInteractingRegion={HandleEditInteractingRegion}
                      HandleAddNewInteractingRegion={HandleAddNewInteractingRegion}
                      HandleEditScenarioYear={HandleEditScenarioYears}
                      HandleAddNNewScenarioYear={HandleAddNNewScenarioYears}
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
          {/* <CustomAutocompleteWithoutEdit type="Model" manyItems showSelectedElements={true} optionsSet={models_json} kind='Models' handler={modelsHandler} selectedElements={selectedModels}/> */}
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          {/* <CustomAutocompleteWithoutEdit type="Frameworks"  manyItems showSelectedElements={true}  optionsSet={frameworks_json} kind='Frameworks' handler={frameworksHandler} selectedElements={selectedFrameworks}/> */}
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

function getSteps() {
  return ['Basic information',
  'Study details',
  'Scenarios',
  'Models',
  'Frameworks'
  ];
  }

function getStepContent(step: number) {
  switch (step) {
    case 0:
          return (
              <div style={{
                display: 'flex',
                alignItems: 'stretch',
                flexWrap: 'wrap',
                padding: '10px',
              }}>
                <TextField size="small" style={{  width: '40%',  marginTop: '10px',  backgroundColor:'#FCFCFC' }} id="outlined-basic" label="What is the name of the study?" variant="standard" value={studyName} onChange={handleStudyName}/>
                <div  style={{ marginLeft: '10px', marginTop: '30px'  }}>
                  <HtmlTooltip
                    title={
                      <Typography color="inherit" variant="caption">
                        {'A study is a project with the goal to investigate something.'} <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00020011">More info from Open Enrgy Ontology (OEO)...</a>
                      </Typography>
                    }
                  >
                    <InfoOutlinedIcon sx={{ color: '#bdbdbd' }}/>
                  </HtmlTooltip>
                </div>
                <TextField  size="small"  style={{  width: '40%', marginTop: '10px',  marginLeft: '15%', backgroundColor:'#FCFCFC' }} id="outlined-basic" label="What is the acronym or short title?" variant="standard" value={acronym} onChange={handleAcronym} />
                <div style={{ marginLeft: '10px', marginTop: '40px'}}>
                  <HtmlTooltip
                    title={
                      <Typography color="inherit" variant="caption">
                        {'An acronym is an abbreviation of the title by using the first letters of each part of the title.'} <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000048">More info from Open Enrgy Ontology (OEO)...</a>
                      </Typography>
                    }
                  >
                    <InfoOutlinedIcon sx={{ color: '#bdbdbd' }}/>
                  </HtmlTooltip>
                </div>
                <CustomAutocomplete width="40%" type="institution" showSelectedElements={true} editHandler={HandleEditInstitution} addNewHandler={HandleAddNewInstitution} manyItems optionsSet={institutions} kind='Which institutions are involved in this study?' handler={institutionHandler} selectedElements={selectedInstitution}/>
                <div style={{ marginLeft: '10px',  marginRight: '15%', marginTop: '20px'  }}>
                <HtmlTooltip
                  title={
                    <Typography color="inherit" variant="caption">
                      {'An institution is an organisation that serves a social purpose.'}<br />
                      <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000238">More info from Open Enrgy Ontology (OEO)...</a>
                    </Typography>
                  }
                >
                  <InfoOutlinedIcon sx={{ color: '#bdbdbd' }}/>
                </HtmlTooltip>
                </div>
                <CustomAutocomplete width="40%" type="contact person" showSelectedElements={true}  editHandler={HandleEditContactPerson} addNewHandler={HandleAddNewContactPerson}  manyItems optionsSet={contactPersons} kind='Who is the contact person for this factsheet?' handler={contactPersonHandler} selectedElements={selectedContactPerson}/>
                <div style={{ marginTop: '40px'  }}>
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
                    <InfoOutlinedIcon sx={{ color: '#bdbdbd' }}/>
                  </HtmlTooltip>
                </div>
                <TextField size="small" variant="standard" style={{ marginTop:'20px', width: '40%',  backgroundColor:'#FCFCFC'  }} id="outlined-basic" label="Report title"  value={report_title} onChange={handleReportTitle} />
                <TextField size="small" variant="standard" style={{ width: '40%', marginTop:'20px', marginBottom:'20px', backgroundColor:'#FCFCFC',  marginLeft: '17%' }} id="outlined-basic" label="Link to study report" value={link_to_study} onChange={handleLinkToStudy} />
                <CustomAutocomplete width="40%" type="author" showSelectedElements={true} editHandler={HandleEditAuthors}  addNewHandler={HandleAddNewAuthor}  manyItems optionsSet={authors} kind='Authors' handler={authorsHandler} selectedElements={selectedAuthors}  />
              </div>

          );
    case 1:
          return (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
            }}>
              <CustomAutocomplete width="60%"  type="Funding source" showSelectedElements={true} editHandler={HandleEditFundingSource} addNewHandler={HandleAddNewFundingSource} manyItems optionsSet={fundingSources} kind='What are the funding sources of this study?' handler={fundingSourceHandler} selectedElements={selectedFundingSource}/>
              <div style={{ marginTop: '10px' }}>
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
              <div style={{ width: '35%' }}></div>
              <TextField size="small" variant="standard" style={{ width: '60%', MarginBottom: '10px', marginTop: '20px', backgroundColor:'#FCFCFC' }} id="outlined-basic" label="Please describe the research questions of the study in max 400 characters." multiline rows={4} maxRows={10} value={abstract} onChange={handleAbstract}/>
              <div style={{ width: '35%' }}></div>
              <CustomAutocompleteWithoutEdit width="40%"  type="sector_division" showSelectedElements={true} manyItems optionsSet={fundingSources} kind='Do you use a predefined sector division? ' handler={sectorDivisionsHandler} selectedElements={selectedSectorDivisions}/>
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
                <div style={{ width: '40%' }}></div>
                <Typography variant="subtitle1" gutterBottom style={{ marginTop:'30px', marginBottom:'10px' }}>
                What additional keywords describe your study?
                </Typography>
                <div style={{ marginTop: "10px", width: '80%' }}>
                  <FormGroup>
                      <div >
                        {
                          StudyKeywords.map((item) => <FormControlLabel control={<Checkbox size="small" color="default" />} checked={selectedStudyKewords.includes(item)} onChange={handleStudyKeywords} label={item} name={item} />)
                        }
                    </div>
                  </FormGroup>
                </div>
                <TextField size="small" variant="standard" style={{ marginTop:'20px', width: '40%' }} id="outlined-basic" label="Title"  value={report_title} onChange={handleReportTitle} />
                <LocalizationProvider dateAdapter={AdapterDayjs}>
                  <Stack spacing={3}  style={{ marginTop:'20px', marginLeft:'15%', width: '40%' }}>
                    <DesktopDatePicker
                        label='Date of publication'
                        inputFormat="YYYY-MM-DD"
                        value={date_of_publication}
                        onChange={(newValue) => {
                          setDateOfPublication(newValue);
                          factsheetObjectHandler('date_of_publication', newValue);
                        }}
                        renderInput={(params) => <TextField {...params} size="small" variant="standard" />}
                      />
                  </Stack>
                </LocalizationProvider>
                <TextField ssize="small" variant="standard" style={{ width: '25%', marginTop:'20px' }} id="outlined-basic" label="DOI" value={doi} onChange={handleDOI} />
                <TextField size="small" variant="standard" style={{ width: '25%', marginLeft:'12%', marginTop:'20px' }} id="outlined-basic" label="Place of publication" value={place_of_publication} onChange={handlePlaceOfPublication} />
                <TextField size="small" variant="standard" style={{ width: '25%', marginLeft:'12%', marginTop:'20px' }} id="outlined-basic" label="Link to study report" value={link_to_study} onChange={handleLinkToStudy} />
            </div>
          );
    case 2:
          return (
            renderScenario()
          );
    case 3:
      return (
        <CustomAutocompleteWithoutEdit type="Model" manyItems showSelectedElements={true} optionsSet={fundingSources} kind='Models' handler={modelsHandler} selectedElements={selectedModels}/>
      );
    case 4:
      return (
        <CustomAutocompleteWithoutEdit type="Frameworks"  manyItems showSelectedElements={true}  optionsSet={fundingSources} kind='Frameworks' handler={frameworksHandler} selectedElements={selectedFrameworks}/>
      );
    default:
    return 'Unknown step';
  }
  }

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
              <Button  disableElevation={true} size="medium" style={{ 'height': '42px', 'textTransform': 'none', 'marginTop': '10px', 'marginRight': '10px', 'zIndex': '1000' }} variant="contained" color="secondary" > <ShareIcon /> </Button>
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
              <AlertTitle>Duplicate!</AlertTitle>
              Another factsheet with this acronym exists. Please choose another acronym!
            </Alert>
          </Snackbar>
          <Snackbar
            open={emptyAcronym}
            autoHideDuration={600}
          >
            <Alert variant="filled" severity="error" sx={{ width: '100%' }}>
              <AlertTitle>Empty acronym!</AlertTitle>
              Please enter the acronym for this factsheet!
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
                <Grid container style={{ marginTop: '10px', marginLeft:'10px' }}>
                  <Grid item xs={10} style={{ padding: '20px', border: '1px solid #cecece', borderRadius: '2px',  backgroundColor:'#FCFCFC', 'height':'80vh', 'overflow': 'auto' }}>
                    {/* <CustomTabs
                      factsheetObjectHandler={factsheetObjectHandler}
                      items={items}
                    /> */}
                    <Stepper activeStep={activeStep} orientation="vertical">
                      {steps.map((label, index) => (
                      <Step key={label}>
                        <StepLabel><b>{label}</b></StepLabel>
                        <StepContent>
                        <Typography>{getStepContent(index)}</Typography>
                        <div >
                          <div>
                          <Button
                              style={{ marginTop: '20px', marginRight: '5px' }}
                              disabled={activeStep === 0}
                              onClick={handleBack}
                              variant="outlined"
                              size="small"
                          >
                            Back
                          </Button>
                          <Button
                            style={{ marginTop: '20px' }}
                            variant="contained"
                            color="primary"
                            onClick={handleNext}
                            size="small"
                          >
                            {activeStep === steps.length - 1 ? 'Finish' : 'Next'}
                          </Button>
                          </div>
                        </div>
                        </StepContent>
                      </Step>
                      ))}
                    </Stepper>
                  </Grid>
                  <Grid item xs={2} style={{ padding: '20px', borderTop: '1px solid #cecece', borderRight: '1px solid #cecece', borderBottom: '1px solid #cecece', borderRadius: '2px',  backgroundColor:'#FCFCFC', 'height':'80vh', 'overflow': 'auto' }} >
                    <div style={{ marginTop: '10%' }}>
                      <div>
                        <Box sx={{  marginLeft: '30%', position: 'relative', display: 'inline-flex' }}>
                          <CircularProgress variant="determinate" value="35" size="6rem" />
                          <Box
                            sx={{
                              top: 0,
                              left: 0,
                              bottom: 0,
                              right: 0,
                              position: 'absolute',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                          >
                            <Typography variant="h6" component="div" color="text.secondary">
                              {`${Math.round(35)}%`}
                            </Typography>
                          </Box>
                        </Box>
                      </div>
                      <div style={{  marginLeft: '31%', position: 'relative', display: 'inline-flex' }}>
                        <Typography variant="subtitle2" component="div" color="text.secondary">
                          To be completed!
                        </Typography>
                      </div>
                      <div style={{ marginTop: '10%', marginLeft: '5%' }}>
                        <Typography variant="subtitle2" component="div" color="text.secondary">
                          Your factsheet should contain information about the study and the scenarios used in it. As you add more information to your factsheet, other studies and scenarios that are similar to those you've already described will appear below.
                        </Typography>
                      </div>
                      <div style={{ marginTop: '10%', marginLeft: '1%', paddingTop: '10px'}}>
                        <Badge color="primary" badgeContent={3} 
                               anchorOrigin={{
                                vertical: 'top',
                                horizontal: 'right',
                              }}>
                          <Typography variant="subtitle2" component="div" color="text.secondary" style={{ paddingRight: '10px' }}>
                            Found similarities, so far:
                          </Typography>
                        </Badge>
                        
                      </div>
                    <div style={{ marginTop: '5%', marginLeft: '1%', paddingTop: '10px'}}>
                      <Chip
                          label="Study 1"
                          color="primary" variant="contained" 
                          style={{ marginLeft: '5px', marginTop: '5px' }}
                          size="small"
                      />
                      <Chip
                          label="Scenario 2"
                          color="primary" variant="outlined" 
                          style={{ marginLeft: '5px', marginTop: '5px' }}
                          size="small"
                      />
                      <Chip
                          label="Scenario 7"
                          color="primary" variant="outlined" 
                          style={{ marginLeft: '5px', marginTop: '5px' }}
                          size="small"
                      />
                    </div>
                    </div>
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
              backgroundColor:'#f3f3f361',
              display: "flex"
            }}
            class="bgimg"
            >
                  <Box
                    sx={{
                      'marginTop': '10px',
                      'overflow': 'auto',
                      'marginBottom': '20px',
                      'marginLeft': '10px',
                      'marginRight': '10px',
                      'overflow': 'scroll',
                      'width': '95%',
                      'height':'65vh'
                    }}
                  >
                    <Typography variant="h6" gutterBottom component="div">
                      <b> {acronym} </b>
                    </Typography>
                    <Typography variant="subtitle2" gutterBottom component="div">
                    <b>Study name: </b>
                      {studyName !== undefined && studyName}
                    </Typography>
                    {/* <Typography variant="subtitle2" gutterBottom component="div">
                    <b>Acronym: </b>
                     {acronym}
                    </Typography> */}
                    <Typography variant="subtitle2" gutterBottom component="div">
                    <b>Contact person(s): </b>
                        {selectedContactPerson.map((v, i) => (
                        <Chip label={v.name} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />
                      ))}
                    </Typography>
                    <Typography variant="subtitle2" gutterBottom component="div">
                    <b>Abstract: </b>
                       {abstract !== undefined && abstract}
                    </Typography>
                    <Typography variant="subtitle2" gutterBottom component="div">
                    <b>Study report information: </b>
                    </Typography>
                    <Typography sx={{ 'marginLeft': '20px' }} variant="subtitle2" gutterBottom component="div">
                    <b>Title: </b>
                      {report_title !== undefined && report_title}
                    </Typography>
                    <Typography sx={{ 'marginLeft': '20px' }} variant="subtitle2" gutterBottom component="div">
                    <b>DOI: </b>
                       {doi !== undefined && doi}
                    </Typography>
                    <Typography sx={{ 'marginLeft': '20px' }} variant="subtitle2" gutterBottom component="div">
                    <b>Link: </b>
                      {link_to_study !== undefined && link_to_study}
                    </Typography>
                    <Typography sx={{ 'marginLeft': '20px' }} variant="subtitle2" gutterBottom component="div">
                    <b>Date of publication: </b>
                       {date_of_publication !== '01-01-1900' && date_of_publication.toString()}
                    </Typography>
                    <Typography sx={{ 'marginLeft': '20px' }} variant="subtitle2" gutterBottom component="div">
                    <b>Place of publication: </b>
                       {place_of_publication !== undefined && place_of_publication}
                    </Typography>
                    <Typography sx={{ 'marginLeft': '20px' }} variant="subtitle2" gutterBottom component="div">
                    <b>Authors:  </b>  
                        {selectedAuthors.map((v, i) => (
                           <Chip label={v.name} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />
                        ))}
                    </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="subtitle2" gutterBottom component="div">
                  <b>Institutions: </b>
                      {selectedInstitution.map((v, i) => (
                      <Chip label={v.name} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />
                      ))}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="subtitle2" gutterBottom component="div">
                  <b>Funding sources:  </b>  
                      {selectedFundingSource.map((v, i) => (
                        <Chip label={v.name} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />
                      ))}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="subtitle2" gutterBottom component="div">
                  <b>Sector divisions: </b>
                      {selectedSectorDivisions.map((v, i) => (
                        <Chip label={v.name} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />
                      ))}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="subtitle2" gutterBottom component="div">
                  <b>Sectors: </b>
                      {selectedSectors.map((v, i) => (
                        <Chip label={v.label} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />
                      ))}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="subtitle2" gutterBottom component="div">
                  <b>Energy carriers: </b>   
                      {selectedEnergyCarriers.map((v, i) => (
                        <Chip label={v.label} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />
                      ))}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="subtitle2" gutterBottom component="div">
                  <b>Energy Transformation Processes: </b>   
                      {selectedEnergyTransformationProcesses.map((v, i) => (
                        <Chip label={v.label} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />
                      ))}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="subtitle2" gutterBottom component="div">
                  <b>Keywords: </b>  
                      {selectedStudyKewords.map((v, i) => (
                       <Chip label={v} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />
                      ))}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="subtitle2" gutterBottom component="div">
                      <b>Scenarios: </b>  
                      {scenarios.map((v, i) => { return <div> 
                        {v.acronym !== '' && <Chip label={v.acronym} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />}
                        <Typography sx={{ 'marginLeft': '20px', 'marginTop': '10px' }} variant="subtitle2" gutterBottom component="div">
                        <b>Name: </b>  
                          {v.name}
                        </Typography>
                        <Typography sx={{ 'marginLeft': '20px' }} variant="subtitle2" gutterBottom component="div">
                        <b>Abstract: </b>  
                          {v.abstract}
                        </Typography>
                        <Typography sx={{ 'marginLeft': '20px' }} variant="subtitle2" gutterBottom component="div">
                        <b>Keywords:</b>  
                          {v.keywords.map( (e) =>  <Chip label={e} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />)}
                        </Typography>
                        <Typography sx={{ 'marginLeft': '20px' }} variant="subtitle2" gutterBottom component="div">
                        <b>Years:</b>  
                          {v.scenario_years.map( (e) =>  <Chip label={e.name} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />)}
                        </Typography>
                        <Typography sx={{ 'marginLeft': '20px' }} variant="subtitle2" gutterBottom component="div">
                        <b>Regions:</b>  
                          {v.regions.map( (e) =>  <Chip label={e.name} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />)}
                        </Typography>
                        <Typography sx={{ 'marginLeft': '20px' }} variant="subtitle2" gutterBottom component="div">
                        <b>Interacting regions:</b>  
                          {v.interacting_regions.map( (e) =>  <Chip label={e.name} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />)}
                        </Typography>
                        <Typography sx={{ 'marginLeft': '20px' }} variant="subtitle2" gutterBottom component="div">
                        <b>Input datasets:</b>  
                          {v.input_datasets.map( (e) =>  <Chip label={e.value.label} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />)}
                        </Typography>
                        <Typography sx={{ 'marginLeft': '20px' }} variant="subtitle2" gutterBottom component="div">
                        <b>Output datasets:</b>  
                          {v.output_datasets.map( (e) =>  <Chip label={e.value.label} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />)}
                        </Typography>
                       
                      </div>  
                      }
                      )}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="subtitle2" gutterBottom component="div">
                      <b>Models: </b>  
                      {selectedModels.map((v, i) => (
                       <Chip label={v.name} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />
                      ))}
                  </Typography>
                  <Typography sx={{ 'marginTop': '10px' }} variant="subtitle2" gutterBottom component="div">
                      <b>Frameworks: </b>  
                      {selectedFrameworks.map((v, i) => (
                       <Chip label={v.name} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />
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
