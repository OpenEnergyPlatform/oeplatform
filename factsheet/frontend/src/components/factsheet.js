import React, { useState, useEffect, useRef } from 'react';
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
import CustomTreeViewWithCheckBox from './customTreeViewWithCheckbox.js';
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
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import StepContent from '@mui/material/StepContent';
import CircularProgress from '@mui/material/CircularProgress';
import Badge from '@mui/material/Badge';
import { Route, Routes, useNavigate } from 'react-router-dom';
import ShareIcon from '@mui/icons-material/Share';
import sunburstKapsule from 'sunburst-chart';
import fromKapsule from 'react-kapsule';
import Select from '@mui/material/Select';
import CustomAutocompleteWithoutAddNew from './customAutocompleteWithoutAddNew.js';
import IconButton from '@mui/material/IconButton';
import oep_models from '../data/models.json';
import oep_frameworks from '../data/frameworks.json';
import Divider from '@mui/material/Divider';
import { makeStyles, Theme } from '@material-ui/core/styles';
import BreadcrumbsNavGrid from '../styles/oep-theme/components/breadcrumbsNavigation.js';
import TableContainer from '@mui/material/TableContainer';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import { ContentTableCell, FirstRowTableCell } from '../styles/oep-theme/components/tableStyles.js';

import MenuBookOutlinedIcon from '@mui/icons-material/MenuBookOutlined';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import FeedOutlinedIcon from '@mui/icons-material/FeedOutlined';
import LinkIcon from '@mui/icons-material/Link';

import Chip from '@mui/material/Chip';
import ListAltOutlinedIcon from '@mui/icons-material/ListAltOutlined';
import Container from '@mui/material/Container';
import Backdrop from '@mui/material/Backdrop';

import '../styles/App.css';
import { TableRow } from '@mui/material';

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
  const [expandedTechnologies, setExpandedTechnologies] = useState(id !== 'new' ? [] : []);
  
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
  const [sunburstData, setSunburstData] = useState([]);

  const [openBackDrop, setOpenBackDrop] = React.useState(false);
  const handleCloseBackDrop = () => {
    setOpenBackDrop(false);
  };
  const handleOpenBackDrop = () => {
    setOpenBackDrop(true);
  };
  

  const Sunburst = fromKapsule(sunburstKapsule);

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };
  
  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };
  
  const handleReset = () => {
    setActiveStep(0);
  };

  const handleStepClick = (i) => {
    setActiveStep(i);
  };

  const HtmlTooltip = styled(({ className, ...props }: TooltipProps) => (
    <Tooltip {...props} classes={{ popper: className }} />
  ))(({ theme }) => ({
    [`& .${tooltipClasses.tooltip}`]: {
      backgroundColor: '#e3eaef',
      color: 'black',
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
              <HelpOutlineIcon sx={{ fontSize: '24px', color: '#708696', marginLeft: '-10px' }}/>
          </HtmlTooltip>
          <span
            style={{ marginLeft: '5px', marginTop: '-20px' }}
          >
          {name}
          </span>
        </span>


 // const [sectors, setSectors] = useState(sectors_json);
  const myChartRef = useRef(0);

  const [sectors, setSectors] = useState([]);
  const [sectorDivisions, setSectorDivisions] = useState([]);
  const [filteredSectors, setFilteredSectors] = useState([]);
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
    descriptors: [],
    input_datasets: [],
    output_datasets: [],
    }
  ]);


  const [scenariosObject, setScenariosObject] = useState({});
  const [selectedStudyKewords, setSelectedStudyKewords] = useState(id !== 'new' ? fsData.study_keywords : []);
  const [selectedModels, setSelectedModels] = useState(id !== 'new' ? fsData.models : []);
  const [selectedFrameworks, setSelectedFrameworks] = useState(id !== 'new' ? fsData.frameworks : []);
  const [removeReport, setRemoveReport] = useState(false);
  const [addedEntity, setAddedEntity] = useState(false);
  const [openAddedDialog, setOpenAddedDialog] = React.useState(false);
  const [openEditDialog, setOpenEditDialog] = React.useState(false);
  const [editedEntity, setEditedEntity] = useState(false);
  const [scenarioTabValue, setScenarioTabValue] = React.useState(0);

  const [technologies, setTechnologies] = React.useState([]);
  const [selectedTechnologies, setSelectedTechnologies] = useState(id !== 'new' ? fsData.technologies : []);
  const [expandedTechnologyList, setExpandedTechnologyList] = useState([]);
  
  const [scenarioDescriptors, setScenarioDescriptors] = React.useState([]);
  const [selectedScenarioDescriptors, setSelectedScenarioDescriptors] = useState([]);


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
    const { data } = await axios.get(conf.toep + `sirop/populate_factsheets_elements/`);
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
      setTechnologies(data.technologies['children']);
      setScenarioDescriptors(data.scenario_descriptors);
      setSectors(data.sectors);
      setFilteredSectors(data.sectors);
      const sector_d = data.sector_divisions;
      sector_d.push({ "label": "Others", "name": "Others", "class": "Others", "value": "Others"});
      setSectorDivisions(sector_d);

      myChartRef.current = Sunburst
      const sampleData = {
        name: "root",
        label: "Energy carrier",
        children: []
      }
      setSunburstData(sampleData);
      });

  }, []);

  const handleSaveFactsheet = () => {
    setOpenBackDrop(true);
    factsheetObjectHandler('name', factsheetName);
    if (acronym !== '') {
      if (id === 'new' && !isCreated) {
        const new_uid = uuid()
        axios.post(conf.toep + 'sirop/add/',
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
          technologies: JSON.stringify(selectedTechnologies),
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
          setOpenBackDrop(false);
        }
        else if (response.data === 'Factsheet exists') {
          setOpenExistDialog(true);
        }
      });
      } else {
        axios.get(conf.toep + `sirop/get/`, { params: { id: uid } }).then(res => {
          axios.post(conf.toep + 'sirop/update/',
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
            technologies: JSON.stringify(selectedTechnologies),
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
            if (response.data === "factsheet updated!") {
              setUID(uid);
              setOpenUpdatedDialog(true);
              setOpenBackDrop(false);
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
    axios.post(conf.toep + 'sirop/delete/', null, { params: { id: id } }).then(response => setOpenRemovedDialog(true));
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
    const newScenarios = [...scenarios];
    const obj = newScenarios.find(el => el.id === idx);
    if (obj)
      obj[name] = selectedList
    console.log(newScenarios);
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
        descriptors: [],
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
    const { data } = await axios.get(conf.toep + `sirop/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000238' } });
    return data;
  };

  const getFundingSources = async () => {
    const { data } = await axios.get(conf.toep + `sirop/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00090001' } });
    return data;
  };

  const getContactPersons = async () => {
    const { data } = await axios.get(conf.toep + `sirop/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000107' } });
    return data;
  };

  const getAuthors = async () => {
    const { data } = await axios.get(conf.toep + `sirop/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000064' } });
    return data;
  };

  const getScenarioRegions = async () => {
    const { data } = await axios.get(conf.toep + `sirop/get_entities_by_type/`, { params: { entity_type: 'OBO.BFO_0000006' } });
    return data;
  };

  const getScenarioInteractingRegions = async () => {
    const { data } = await axios.get(conf.toep + `sirop/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00020036' } });
    return data;
  };

  const getScenarioYears = async () => {
    const { data } = await axios.get(conf.toep + `sirop/get_entities_by_type/`, { params: { entity_type: 'OBO.OEO_00020097' } });
    return data;
  };

  const getModels = async () => {
    const { data } = await axios.get(conf.toep + `sirop/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000274' } });
    return data;
  };

  const getFrameworks = async () => {
    const { data } = await axios.get(conf.toep + `sirop/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000172' } });
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
    axios.post(conf.toep + 'sirop/add_entities/',
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
    axios.post(conf.toep + 'sirop/update_an_entity/',
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
    axios.post(conf.toep + 'sirop/add_entities/',
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
    axios.post(conf.toep + 'sirop/update_an_entity/',
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
    axios.post(conf.toep + 'sirop/add_entities/',
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
    axios.post(conf.toep + 'sirop/update_an_entity/',
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
    axios.post(conf.toep + 'sirop/add_entities/',
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
    axios.post(conf.toep + 'sirop/update_an_entity/',
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
    axios.post(conf.toep + 'sirop/add_entities/',
    {
      'entity_type': 'OEO.OEO_00020032', 
      'entity_label': newElement.name,
      'entity_iri': newElement.iri,
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
    axios.post(conf.toep + 'sirop/update_an_entity/',
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
    axios.post(conf.toep + 'sirop/add_entities/',
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
    axios.post(conf.toep + 'sirop/update_an_entity/',
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
    axios.post(conf.toep + 'sirop/add_entities/',
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
    axios.post(conf.toep + 'sirop/update_an_entity/',
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
    axios.post(conf.toep + 'sirop/add_entities/',
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
    axios.post(conf.toep + 'sirop/update_an_entity/',
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
    axios.post(conf.toep + 'sirop/add_entities/',
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
    axios.post(conf.toep + 'sirop/update_an_entity/',
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
    setSelectedSectorDivisions(sectorDivisionsList);
    let sectorsBasedOnDivisions = sectors.filter(item  => sectorDivisionsList.map(item => item.class).includes(item.sector_division) );
    if (sectorDivisionsList.some(e => e.label == 'Others')) {
      sectorsBasedOnDivisions = sectors;
    }
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

  const scenarioDescriptorHandler = (descriptorList, nodes, id) => {
    const zipped = []
    descriptorList.map((v) => zipped.push({"value": findNestedObj(nodes, 'value', v).value, "label": findNestedObj(nodes, 'value', v).label, "class": findNestedObj(nodes, 'value', v).iri}));
    const newScenarios = [...scenarios];
    const obj = newScenarios.find(el => el.id === id);
    obj.descriptors = zipped;
    setScenarios(newScenarios);
    factsheetObjectHandler('scenarios', JSON.stringify(newScenarios));

  };

  const technologyHandler = (technologyList, nodes) => {
    const zipped = []
    technologyList.map((v) => zipped.push({"value": findNestedObj(nodes, 'value', v).value, "label": findNestedObj(nodes, 'value', v).label, "class": findNestedObj(nodes, 'value', v).iri}));
    setSelectedTechnologies(zipped);
  };

  const expandedTechnologyHandler = (expandedTechnologyList) => {
    const zipped = []
    expandedTechnologyList.map((v) => zipped.push({ "value": v, "label": v }));
    setExpandedTechnologyList(zipped);
  };

  const sectorsHandler = (sectorsList, nodes) => {
    const zipped = []
    sectorsList.map((v) => zipped.push({"value": findNestedObj(nodes, 'value', v).value, "label": findNestedObj(nodes, 'value', v).label, "class": findNestedObj(nodes, 'value', v).iri}));
    setSelectedSectors(zipped);
  };

  const expandedSectorsHandler = (expandedSectorsList) => {
    const zipped = []
    expandedSectorsList.map((v) => zipped.push({ "value": v, "label": v }));
    setExpandedSectors(zipped);
  };

  const expandedTechnologiesHandler = (expandedTechnologiesList) => {
    const zipped = []
    expandedTechnologiesList.map((v) => zipped.push({ "value": v, "label": v }));
    setExpandedTechnologies(zipped);
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
  const tabClasses = {root: classes.tab};

  const renderScenario = () => {
    return  <div>
              <Box sx={{ flexGrow: 1, display: 'flex', height:'72vh', overflow: 'auto' }} >
                <Tabs
                  orientation="vertical"
                  value={scenarioTabValue}
                  onChange={handleScenarioTabChange}
                  aria-label="Vertical tabs example"
                  sx={{ borderRight: 1, borderColor: 'divider' }}
                  key={'Scenario_tabs'}
                  classes={'tabs'} 
                >
                {scenarios.map((item, i) =>
                  <Tab
                    label={item.acronym !== '' ? item.acronym.substring(0,16) : 'Scenario ' + (Number(i) + Number(1)) }
                    key={'Scenario_tab_' + item.id}
                    classes={tabClasses}
                    style={{ border: '1px solid #cecece', marginBottom: '5px',  width:'250px' }}
                  />
                )}
                <Box sx={{ 'textAlign': 'center', 'marginTop': '5px', 'paddingLeft': '10px',  'paddingRight': '10px', }} >
                  <IconButton
                    color="primary"
                    aria-label="add"
                    size="small"
                    onClick={handleAddScenario}
                  >
                    <AddIcon  />
                  </IconButton>
                </Box>
                </Tabs>
                {scenarios.map((item, i) =>
                  <TabPanel
                    value={scenarioTabValue}
                    index={i}
                    style={{ width: '100%', overflow: 'auto' }}
                    key={'Scenario_panel_' + item.id}
                  >
                    <Scenario
                      descriptors={scenarioDescriptors['children']}
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
                      scenarioDescriptorHandler={scenarioDescriptorHandler}
                    />
                  </TabPanel>
                )}
              </Box>
            </div >
    }



const renderBasicInformation = () => (
    <Grid container justifyContent="space-between"
      alignItems="start"
      spacing={2}>

      <Grid item xs={2}  style={{ padding: '5px'}}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Study name: </b> </span>
        <span >
        <HtmlTooltip
            title={
            <React.Fragment>
              <Typography color="inherit" variant="subtitle1">
                {'A study is a project with the goal to investigate something.'}
                <br />
                <a href="http://openenergy-platform.org/ontology/oeo/OEO_00020011">More info...</a>
              </Typography>
            </React.Fragment>
          }
          >
          <InfoOutlinedIcon sx={{ color: '#708696' }}/>
          </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', overflow: "auto"  }}>
        <TextField InputProps={{ sx: { borderRadius: 0 } }} size="small" id="outlined-basic"  style={{  width: '100%' }} variant="outlined" value={studyName} onChange={handleStudyName}/>
      </Grid>

      <Grid item xs={2}  style={{ paddingTop: '15px', paddingLeft: '5px' }}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Acronym: </b> </span>
        <span >
        <HtmlTooltip
            title={
            <React.Fragment>
              <Typography color="inherit" variant="subtitle1">
                {'An acronym is an abbreviation of the title by using the first letters of each part of the title.'}
                <br />
                <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000048">More info...</a>
              </Typography>
            </React.Fragment>
          }
          >
          <InfoOutlinedIcon sx={{ color: '#708696' }}/>
          </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '10px', overflow: "auto"  }}>
      <TextField InputProps={{ sx: { borderRadius: 0 } }} size="small"  style={{  width: '100%' }} id="outlined-basic"  variant="outlined" value={acronym} onChange={handleAcronym} />
      </Grid>

      <Grid item xs={2}   style={{ paddingTop: '15px', paddingLeft: '5px' }}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Institutions: </b> </span>
        <span >
        <HtmlTooltip
          title={
          <React.Fragment>
            <Typography color="inherit" variant="subtitle1">
              {'An institution is an organisation that serves a social purpose.'}
              <br />
              <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000238">More info...</a>
            </Typography>
          </React.Fragment>
        }
        >
        <InfoOutlinedIcon sx={{ color: '#708696' }}/>
        </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '5px', overflow: "auto"  }}>
        <CustomAutocomplete width="100%" type="institution" showSelectedElements={true} editHandler={HandleEditInstitution} addNewHandler={HandleAddNewInstitution} manyItems optionsSet={institutions} handler={institutionHandler} selectedElements={selectedInstitution}/>
      </Grid>


      <Grid item xs={2}  style={{ paddingTop: '15px', paddingLeft: '5px' }}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b> Contact person: </b> </span>
        <span >
          <HtmlTooltip
            title={
            <React.Fragment>
              <Typography color="inherit" variant="subtitle1">
                {'A contact person is an agent that can be contacted for help or information about a specific service or good.'}
                <br />
                <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000107">More info...</a>
              </Typography>
            </React.Fragment>
          }
          >
          <InfoOutlinedIcon sx={{ color: '#708696' }}/>
          </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '5px', overflow: "auto"  }}>
      <CustomAutocomplete width="100%" type="contact person" showSelectedElements={true}  editHandler={HandleEditContactPerson} addNewHandler={HandleAddNewContactPerson}  manyItems optionsSet={contactPersons} handler={contactPersonHandler} selectedElements={selectedContactPerson}/>
      </Grid>

    </Grid>
    
  );

  const renderStudyDetail = () => (
    <Grid container justifyContent="space-between" alignItems="start" spacing={2} >
      
      <Grid item xs={2}  style={{ padding: '5px'}}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Funding sources: </b> </span>
        <span >
        {/* <HtmlTooltip
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
          <HelpOutlineIcon sx={{ color: '#708696' }}/>
        </HtmlTooltip> */}
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', overflow: "auto"  }}>
        <CustomAutocomplete width="100%"  type="Funding source" showSelectedElements={true} editHandler={HandleEditFundingSource} addNewHandler={HandleAddNewFundingSource} manyItems optionsSet={fundingSources} kind='' handler={fundingSourceHandler} selectedElements={selectedFundingSource}/>
      </Grid>

      <Grid item xs={2}  style={{ padding: '5px'}}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Abstract: </b> </span>
        <span >
        <HtmlTooltip
          title={
          <React.Fragment>
            <Typography color="inherit" variant="subtitle1">
              {'A summary of the resource.'}
              <br />
              <a href="https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#abstract">More info...</a>
            </Typography>
          </React.Fragment>
        }
        >
        <InfoOutlinedIcon sx={{ color: '#708696' }}/>
        </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', overflow: "auto"  }}>
        <TextField InputProps={{ sx: { borderRadius: 0 } }} size="small" variant="outlined" style={{ width: '100%', MarginBottom: '10px', marginTop: '20px' }} id="outlined-basic" label="" multiline rows={6} maxRows={10} value={abstract} onChange={handleAbstract}/>
      </Grid>

      <Grid item xs={2}  style={{ padding: '5px'}}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Study descriptors: </b> </span>
        <span >
        {/* <HtmlTooltip
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
          <HelpOutlineIcon sx={{ color: '#708696' }}/>
        </HtmlTooltip> */}
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', overflow: "auto"  }}>
      <div style={{ marginTop: "10px" }}>
          <FormGroup>
              <div >
                {
                  StudyKeywords.map((item) => <FormControlLabel control={<Checkbox size="small" color="default" />} checked={selectedStudyKewords.includes(item)} onChange={handleStudyKeywords} label={item} name={item} />)
                }
            </div>
          </FormGroup>
        </div>
      </Grid>
    </Grid>
  );

  const renderStudyPublications= () =>  (
    <Grid container justifyContent="space-between" alignItems="start" spacing={2} >
      
      <Grid item xs={2}  style={{ padding: '5px'}}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Report title: </b> </span>
        <span >
        <HtmlTooltip
            title={
            <React.Fragment>
              <Typography color="inherit" variant="subtitle1">
                {'A name given to the resource.'}
                <br />
                <a href="http://purl.org/dc/elements/1.1/title">More info...</a>
              </Typography>
            </React.Fragment>
          }
          >
          <InfoOutlinedIcon sx={{ color: '#708696' }}/>
          </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '5px', overflow: "auto", marginBottom:'10px'  }}>
        <TextField InputProps={{ sx: { borderRadius: 0 } }} size="small" variant="outlined" style={{ width: '70%' }} id="outlined-basic" label=""  value={report_title} onChange={handleReportTitle} />
      </Grid>

      <Grid item xs={2}  style={{ padding: '5px'}}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Authors: </b> </span>
        <span >
        <HtmlTooltip
          title={
          <React.Fragment>
            <Typography color="inherit" variant="subtitle1">
              {'An author is an agent that creates or has created written work.'}
              <br />
              <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000064">More info...</a>
            </Typography>
          </React.Fragment>
        }
        >
        <InfoOutlinedIcon sx={{ color: '#708696' }}/>
        </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', overflow: "auto"  }}>
        <CustomAutocomplete width="70%" type="author" showSelectedElements={true} editHandler={HandleEditAuthors}  addNewHandler={HandleAddNewAuthor}  manyItems optionsSet={authors} kind='' handler={authorsHandler} selectedElements={selectedAuthors}  />
      </Grid>

      <Grid item xs={2}  style={{ padding: '5px'}}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>DOI: </b> </span>
        <span >
          <HtmlTooltip
            title={
            <React.Fragment>
              <Typography color="inherit" variant="subtitle1">
                {'A DOI (digital object identifier) is a persistent identifier or handle used to uniquely identify objects, standardized by the International Organization for Standardization (ISO).'}
                <br />
                <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000133">More info...</a>
              </Typography>
            </React.Fragment>
          }
          >
          <InfoOutlinedIcon sx={{ color: '#708696' }}/>
          </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', overflow: "auto"  }}>
        <TextField InputProps={{ sx: { borderRadius: 0 } }} size="small" variant="outlined" style={{ width: '70%' }} id="outlined-basic" label="" value={doi} onChange={handleDOI} />
      </Grid>

      <Grid item xs={2}  style={{ padding: '5px'}}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Link to study report: </b> </span>
        <span >
        {/* <HtmlTooltip
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
          <HelpOutlineIcon sx={{ color: '#708696' }}/>
        </HtmlTooltip> */}
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', overflow: "auto"  }}>
        <TextField InputProps={{ sx: { borderRadius: 0 } }}  size="small" variant="outlined" style={{ width: '70%', marginTop:'10px' }} id="outlined-basic" label="" value={link_to_study} onChange={handleLinkToStudy} />
      </Grid>

      <Grid item xs={2}  style={{ padding: '5px'}}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Date of publication: </b> </span>
        <span >
        {/* <HtmlTooltip
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
          <HelpOutlineIcon sx={{ color: '#708696' }}/>
        </HtmlTooltip> */}
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', overflow: "auto"  }}>
      <LocalizationProvider dateAdapter={AdapterDayjs}>
          <Stack spacing={3}  style={{ marginTop:'10px', width: '70%', marginBottom:'40px' }}>
            <DesktopDatePicker
                label=''
                inputFormat="YYYY-MM-DD"
                value={date_of_publication}
                onChange={(newValue) => {
                  setDateOfPublication(newValue);
                }}
                renderInput={(params) => <TextField {...params} size="small" variant="outlined" />}
              />
          </Stack>
        </LocalizationProvider>
      </Grid>
    </Grid>
  );


  const renderSectorsAndTecnology = () => (
    <Grid container justifyContent="space-between" alignItems="start" spacing={2} >
      
      <Grid item xs={2}  style={{ padding: '5px'}}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Sector divisions: </b> </span>
        <span >
          <HtmlTooltip
              title={
              <React.Fragment>
                <Typography color="inherit" variant="subtitle1">
                  {'A sector division is a specific way to subdivide a system.'}
                  <br />
                  <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000368">More info...</a>
                </Typography>
              </React.Fragment>
            }
            >
            <InfoOutlinedIcon sx={{ color: '#708696' }}/>
          </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', overflow: "auto"  }}>
        <CustomAutocompleteWithoutAddNew showSelectedElements={true} optionsSet={sectorDivisions} kind='' handler={sectorDivisionsHandler} selectedElements={selectedSectorDivisions}/>
      </Grid>


      <Grid item xs={2}  style={{ padding: '5px'}}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Sectors: </b> </span>
        <span >
          <HtmlTooltip
            title={
            <React.Fragment>
              <Typography color="inherit" variant="subtitle1">
                {'A sector is generically dependent continuant that is a subdivision of a system.'}
                <br />
                <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000367">More info...</a>
              </Typography>
            </React.Fragment>
          }
          >
          <InfoOutlinedIcon sx={{ color: '#708696' }}/>
          </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', overflow: "auto"  }}>
      <CustomTreeViewWithCheckBox flat={true} 
                                    showFilter={false} 
                                    size="360px" 
                                    checked={selectedSectors} 
                                    expanded={expandedSectors} 
                                    handler={sectorsHandler} 
                                    expandedHandler={expandedSectorsHandler} 
                                    data={filteredSectors} 
                                    title={"Which sectors are considered in the study?"} 
                                    toolTipInfo={['A sector is generically dependent continuant that is a subdivision of a system.', 'http://openenergy-platform.org/ontology/oeo/OEO_00000367']} />
      </Grid>

      <Grid item xs={2}  style={{ padding: '5px'}}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Technology: </b> </span>
        <span >
          <HtmlTooltip
            title={
            <React.Fragment>
              <Typography color="inherit" variant="subtitle1">
                {'A technology is a plan specification that describes how to combine artificial objects or other material entities and processes in a specific way.'}
                <br />
                <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000407">More info...</a>
              </Typography>
            </React.Fragment>
          }
          >
          <InfoOutlinedIcon sx={{ color: '#708696' }}/>
          </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', overflow: "auto"  }}>
      <CustomTreeViewWithCheckBox showFilter={false}
                                    size="260px" 
                                    checked={selectedTechnologies} 
                                    expanded={getNodeIds(technologies['children'])} 
                                    handler={technologyHandler} 
                                    expandedHandler={expandedTechnologyHandler} 
                                    data={technologies} 
                                    title={"What technologies are considered?"} 
                                    toolTipInfo={['A technology is a plan specification that describes how to combine artificial objects or other material entities and processes in a specific way.', 'http://openenergy-platform.org/ontology/oeo/OEO_00000407']} 
                                    />
      </Grid>
    </Grid>
  );

  const renderModelsAndFrameworks = () => (
    <Grid container justifyContent="space-between" alignItems="start" spacing={2} >
      
    <Grid item xs={2}  style={{ padding: '5px'}}>
      <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Models: </b> </span>
      <span >
      <HtmlTooltip
            title={
            <React.Fragment>
              <Typography color="inherit" variant="subtitle1">
                {'A model is a generically dependent continuant that is used for computing an idealised reproduction of a system and its behaviours.'}
                <br />
                <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000274">More info...</a>
              </Typography>
            </React.Fragment>
          }
          >
          <InfoOutlinedIcon sx={{ color: '#708696' }}/>
      </HtmlTooltip>
      </span>
    </Grid>
    <Grid item xs={10} style={{ paddingTop: '0px', overflow: "auto"  }}>
      <CustomAutocompleteWithoutEdit  type="Model" manyItems showSelectedElements={true} optionsSet={oep_models} kind='Models' handler={modelsHandler} selectedElements={selectedModels}/>
    </Grid>

    <Grid item xs={2}  style={{ padding: '5px'}}>
      <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Frameworks: </b> </span>
      <span >
        <HtmlTooltip
              title={
              <React.Fragment>
                <Typography color="inherit" variant="subtitle1">
                  {'A software framework is a Software that is generic and can be adapted to a specific application.'}
                  <br />
                  <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000382">More info...</a>
                </Typography>
              </React.Fragment>
            }
            >
            <InfoOutlinedIcon sx={{ color: '#708696' }}/>
        </HtmlTooltip>
      </span>
    </Grid>
    <Grid item xs={10} style={{ paddingTop: '0px', overflow: "auto"  }}>
      <CustomAutocompleteWithoutEdit  type="Frameworks"  manyItems showSelectedElements={true}  optionsSet={oep_frameworks} kind='Frameworks' handler={frameworksHandler} selectedElements={selectedFrameworks}/>
    </Grid>
    </Grid>
  );

const items = {
  titles: ['Basic information', 'Study detail', 'Publications', 'Sectors and technology', 'Scenarios', 'Models and frameworks'],
  contents: [
    renderBasicInformation(),
    renderStudyDetail(),
    renderStudyPublications(),
    renderSectorsAndTecnology(),
    renderScenario(),
    renderModelsAndFrameworks()
    ]
}
const scenario_count = 'Scenarios'+' (' + scenarios.length + ')' ;
const renderScenariosOverview = () => (
  <Container maxWidth="lg">
    {
      scenarios.map((v, i) => 
      v.acronym !== '' && 
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <FirstRowTableCell>
                <div>
                  <span>Name</span>
                  <HtmlTooltip
                    title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'A study is a project with the goal to investigate something.'}
                        <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00020011">More info...</a>
                      </Typography>
                    </React.Fragment>
                    }
                    >
                    <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip>
                </div>
              </FirstRowTableCell>
              <ContentTableCell>
                {v.name}
              </ContentTableCell>
            </TableRow>
            <TableRow>
              <FirstRowTableCell>
                <div>
                  <span>Acronym</span>
                  <HtmlTooltip
                    title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'An acronym is an abbreviation of the title by using the first letters of each part of the title.'}
                        <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000048">More info...</a>
                      </Typography>
                    </React.Fragment>
                    }
                    >
                    <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip>
                </div>
              </FirstRowTableCell>
              <ContentTableCell>
                {v.acronym} 
              </ContentTableCell>
            </TableRow>
            <TableRow>
              <FirstRowTableCell>
                <div>
                  <span>Abstract</span>
                  <HtmlTooltip
                    title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'A summary of the resource.'}
                        <br />
                        <a href="https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#abstract">More info...</a>
                      </Typography>
                    </React.Fragment>
                    }
                    >
                    <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip>
                </div>
              </FirstRowTableCell>
              <ContentTableCell>
                {v.abstract}
              </ContentTableCell>
            </TableRow>
            <TableRow>
              <FirstRowTableCell>
                <div>
                  <span>Descriptors</span>
                  <HtmlTooltip
                    title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'A scenario is an information content entity that contains statements about a possible future development based on a coherent and internally consistent set of assumptions and their motivation.'}
                        <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000364">More info...</a>
                      </Typography>
                    </React.Fragment>
                    }
                    >
                    <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip>
                </div>
              </FirstRowTableCell>
              <ContentTableCell>
                {v.descriptors.map( (e) =>  <span> <span> {e.label} </span> <span>  <b className="separator-dot"> . </b> </span> </span>  )}
              </ContentTableCell>
            </TableRow>
            <TableRow>
              <FirstRowTableCell>
                <div>
                  <span>Years</span>
                  <HtmlTooltip
                    title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'A scenario year is a time step that has a duration of one year and is part of a scenario horizon.'}
                        <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00020097">More info...</a>
                      </Typography>
                    </React.Fragment>
                    }
                    >
                    <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip>
                </div>
              </FirstRowTableCell>
              <ContentTableCell>
              {v.scenario_years.map( (e) =>  <span> <span> {e.name} </span> <span>  <b className="separator-dot"> . </b> </span> </span>  )}
              </ContentTableCell>
            </TableRow>
            <TableRow>
              <FirstRowTableCell>
                <div>
                  <span>Regions</span>
                  <HtmlTooltip
                    title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'A study region is a spatial region that is under investigation and consists entirely of one or more subregions.'}
                        <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00020032">More info...</a>
                      </Typography>
                    </React.Fragment>
                    }
                    >
                    <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip>
                </div>
              </FirstRowTableCell>
              <ContentTableCell>
                {v.regions.map( (e) => <span> <span> {e.name} </span> <span> <b className="separator-dot"> . </b> </span> </span> )}
              </ContentTableCell>
            </TableRow>
            <TableRow>
              <FirstRowTableCell>
                <div>
                  <span>Interacting regions</span>
                  <HtmlTooltip
                    title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'An interacting region is a spatial region that interacts with a study region. It is part of a considered region, but not a study region.'}
                        <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00020036">More info...</a>
                      </Typography>
                    </React.Fragment>
                    }
                    >
                    <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip>
                </div>
              </FirstRowTableCell>
              <ContentTableCell>
                {v.interacting_regions.map( (e) =>  <span> <span> {e.name} </span> <span> <b className="separator-dot"> . </b> </span> </span> )}
              </ContentTableCell>
            </TableRow>
            <TableRow>
              <FirstRowTableCell>
                <div>
                  <span>Input datasets</span>
                  <HtmlTooltip
                    title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'Endogenous data is a data item whose quantity value is determined by a model.'}
                        <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00030030">More info...</a>
                      </Typography>
                    </React.Fragment>
                    }
                    >
                    <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip>
                </div>
              </FirstRowTableCell>
              <ContentTableCell>
                {v.input_datasets.map( (e) => <span> <span> {e.value.label} </span> <span>  <b className="separator-dot"> . </b> </span> </span> )}
              </ContentTableCell>
            </TableRow>
            <TableRow>
              <FirstRowTableCell>
                <div>
                  <span>Output datasets</span>
                  <HtmlTooltip
                    title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'Exogenous data is a data item whose quantity value is determined outside of a model and is imposed on a model.'}
                        <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00030029">More info...</a>
                      </Typography>
                    </React.Fragment>
                    }
                    >
                    <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                    </HtmlTooltip>
                </div>
              </FirstRowTableCell>
              <ContentTableCell>
              {v.output_datasets.map( (e) =>  <span> <span> {e.value.label} </span> <span>  <b className="separator-dot"> . </b> </span> </span>)}
              </ContentTableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
      )
    } 
  </Container>
)

const renderPublicationOverview = () => (
  <Container maxWidth="lg">
    <TableContainer>
      <Table>
        <TableBody>
          <TableRow>
            <FirstRowTableCell>
              <div>
                <span>Report title</span>
                <HtmlTooltip
                  title={
                  <React.Fragment>
                    <Typography color="inherit" variant="subtitle1">
                      {'A name given to the resource.'}
                      <br />
                      <a href="http://purl.org/dc/elements/1.1/title">More info...</a>
                    </Typography>
                  </React.Fragment>
                }
                >
                <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                </HtmlTooltip>
              </div>
            </FirstRowTableCell>
            <ContentTableCell>
              {report_title !== undefined ? report_title : ""} 
            </ContentTableCell>
          </TableRow>
          <TableRow>
            <FirstRowTableCell>
              <div>
                <span>Authors</span>
                <HtmlTooltip
                  title={
                  <React.Fragment>
                    <Typography color="inherit" variant="subtitle1">
                      {'An author is an agent that creates or has created written work.'}
                      <br />
                      <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000064">More info...</a>
                    </Typography>
                  </React.Fragment>
                }
                >
                <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                </HtmlTooltip>
              </div>
            </FirstRowTableCell>
            <ContentTableCell>
              {selectedAuthors.map((v, i) => (
                <span> <span> {v.name} </span> <span>   <b className="separator-dot"> . </b> </span> </span>
              ))}
            </ContentTableCell>
          </TableRow>
          <TableRow>
            <FirstRowTableCell>
              <div>
                <span>DOI</span>
                <HtmlTooltip
                  title={
                  <React.Fragment>
                    <Typography color="inherit" variant="subtitle1">
                      {'A DOI (digital object identifier) is a persistent identifier or handle used to uniquely identify objects, standardized by the International Organization for Standardization (ISO).'}
                      <br />
                      <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000133">More info...</a>
                    </Typography>
                  </React.Fragment>
                }
                >
                <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                </HtmlTooltip>
              </div>
            </FirstRowTableCell>
            <ContentTableCell>
              {selectedAuthors.map((v, i) => (
                <span> <span> {doi !== undefined ? doi : ''} </span> <span>   <b style={{ fontSize: '24px' }}></b> </span> </span> 
              ))}
            </ContentTableCell>
          </TableRow>
          <TableRow>
            <FirstRowTableCell>
              <div>
                <span>Date of publication</span>
                {/* <HtmlTooltip
                  title={
                  <React.Fragment>
                    <Typography color="inherit" variant="subtitle1">
                      {'A study is a project with the goal to investigate something.'}
                      <br />
                      <a href="http://www.geneontology.org/formats/oboInOwl#date">More info...</a>
                    </Typography>
                  </React.Fragment>
                }
                >
                <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                </HtmlTooltip> */}
              </div>
            </FirstRowTableCell>
            <ContentTableCell>
            <span> <span> {date_of_publication} </span> <span>   <b style={{ fontSize: '24px' }}></b> </span> </span>
            </ContentTableCell>
          </TableRow>
          <TableRow>
            <FirstRowTableCell>
              <div>
              <span>Link to study report</span>
                {/* <HtmlTooltip
                    title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'A study is a project with the goal to investigate something.'}
                        <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00020011">More info from Open Enrgy Ontology (OEO)...</a>
                      </Typography>
                    </React.Fragment>
                  }
                  >
                  <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip>
                */}
              </div>
            </FirstRowTableCell>
            <ContentTableCell>
              <span> <span> {date_of_publication} </span> <span>   <b style={{ fontSize: '24px' }}></b> </span> </span>
            </ContentTableCell>
          </TableRow>
          <TableRow>
            <FirstRowTableCell>
              <div>
                <span>Citation</span>
                <HtmlTooltip
                  title={
                  <React.Fragment>
                    <Typography color="inherit" variant="subtitle1">
                      {'A citation reference is a reference stating where a citation was taken from.'}
                      <br />
                      <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000085">More info...</a>
                    </Typography>
                  </React.Fragment>
                }
                >
                <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                </HtmlTooltip>
              </div>
            </FirstRowTableCell>
            <ContentTableCell>
              <span> <span> {date_of_publication} </span> <span>   <b style={{ fontSize: '24px' }}></b> </span> </span>
            </ContentTableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  </Container>
)
  
const renderSectorsAndTechnology = () => (
  <Grid container justifyContent="space-between"
        alignItems="start"
        spacing={2} 
        style={{ width: '100%', marginTop:'10px', border: '1px solid #80808038' }} >

      <Grid item xs={2}  style={{ padding: '5px' }}>
        <span style={{ color: '#294456', marginLeft:'20px' }}><b> Sector divisions: </b> </span>
        <span >
          <HtmlTooltip
            title={
            <React.Fragment>
              <Typography color="inherit" variant="subtitle1">
                {'A sector division is a specific way to subdivide a system.'}
                <br />
                <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000368">More info...</a>
              </Typography>
            </React.Fragment>
          }
          >
          <InfoOutlinedIcon sx={{ color: '#708696' }}/>
          </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', borderLeft: '1px solid #80808038' }}>
       {selectedSectorDivisions.map((v, i) => (
            <span> <span> {v.name} </span> <span>   <b className="separator-dot"> . </b> </span> </span>
        ))}
      </Grid>

      <Grid item xs={12} style={{ padding: '0px' }}>
        <Divider />
      </Grid>
      <Grid item xs={2}  style={{ padding: '5px' }}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Sectors: </b> </span>
        <span >
          <HtmlTooltip
            title={
            <React.Fragment>
              <Typography color="inherit" variant="subtitle1">
                {'A sector is generically dependent continuant that is a subdivision of a system.'}
                <br />
                <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000367">More info...</a>
              </Typography>
            </React.Fragment>
          }
          >
          <InfoOutlinedIcon sx={{ color: '#708696' }}/>
          </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', borderLeft: '1px solid #80808038' }}>
        {selectedSectors.map((v, i) => (
            <span> <span> {v.label} </span> <span>   <b className="separator-dot"> . </b> </span> </span>
        ))}
      </Grid>
      <Grid item xs={12} style={{ padding: '0px' }}>
        <Divider />
      </Grid>
      <Grid item xs={2}  style={{ padding: '5px' }}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Technologies: </b> </span>
        <span >
          <HtmlTooltip
            title={
            <React.Fragment>
              <Typography color="inherit" variant="subtitle1">
                {'A technology is a plan specification that describes how to combine artificial objects or other material entities and processes in a specific way.'}
                <br />
                <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000407">More info...</a>
              </Typography>
            </React.Fragment>
          }
          >
          <InfoOutlinedIcon sx={{ color: '#708696' }}/>
          </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', borderLeft: '1px solid #80808038' }}>
      {selectedTechnologies.map((v, i) => (
            <span> <span> {v.label} </span> <span>   <b className="separator-dot"> . </b> </span> </span>
        ))}
      </Grid>
    </Grid>
)

const renderModelsAndFrameworksOverview = () => (
  <Grid container justifyContent="space-between"
        alignItems="start"
        spacing={2} 
        style={{ width: '100%', marginTop:'10px', border: '1px solid #80808038' }} >

      <Grid item xs={2}  style={{ padding: '5px' }}>
        <span style={{ color: '#294456', marginLeft:'20px' }}><b> Models: </b> </span>
        <span >
          <HtmlTooltip
            title={
            <React.Fragment>
              <Typography color="inherit" variant="subtitle1">
                {'A model is a generically dependent continuant that is used for computing an idealised reproduction of a system and its behaviours.'}
                <br />
                <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000274">More info...</a>
              </Typography>
            </React.Fragment>
          }
          >
          <InfoOutlinedIcon sx={{ color: '#708696' }}/>
          </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', borderLeft: '1px solid #80808038' }}>
       {selectedModels.map((v, i) => (
            <span> <span> {v.name} </span> <span>   <b className="separator-dot"> . </b> </span> </span>
        ))}
      </Grid>

      <Grid item xs={12} style={{ padding: '0px' }}>
        <Divider />
      </Grid>
      <Grid item xs={2}  style={{ padding: '5px' }}>
        <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Frameworks: </b> </span>
        <span >
          <HtmlTooltip
            title={
            <React.Fragment>
              <Typography color="inherit" variant="subtitle1">
                {'A software framework is a Software that is generic and can be adapted to a specific application.'}
                <br />
                <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000382">More info...</a>
              </Typography>
            </React.Fragment>
          }
          >
          <InfoOutlinedIcon sx={{ color: '#708696' }}/>
          </HtmlTooltip>
        </span>
      </Grid>
      <Grid item xs={10} style={{ paddingTop: '0px', borderLeft: '1px solid #80808038' }}>
        {selectedFrameworks.map((v, i) => (
            <span> <span> {v.name} </span> <span>   <b className="separator-dot"> . </b> </span> </span>
        ))}
      </Grid>
    </Grid>
)

const overview_items = {
  titles: [scenario_count, 'Publications', 'Sectors and technology', 'Models and frameworks'],
  contents: [
    renderScenariosOverview(),
    renderPublicationOverview(),
    renderSectorsAndTechnology(),
    renderModelsAndFrameworksOverview(),
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
  'Publication',
  'Sectors',
  'Technologies',
  'Scenarios',
  'Models',
  'Frameworks',
  ];
  }

const handleNonFittingLabelFn = ((label, availablePx) => {
  const numFitChars = Math.round(availablePx / 7); // ~7px per char
  return `${label.slice(2, Math.round(numFitChars) - 3)}...`;
});

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
                    <InfoOutlinedIcon sx={{ color: '#708696' }}/>
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
                    <InfoOutlinedIcon sx={{ color: '#708696' }}/>
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
                  <InfoOutlinedIcon sx={{ color: '#708696' }}/>
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
                    <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip>
                </div>
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
                  <HelpOutlineIcon sx={{ color: '#708696' }}/>
                </HtmlTooltip>
              </div>
              <div style={{ width: '35%' }}></div>
              <TextField size="small" variant="standard" style={{ width: '60%', MarginBottom: '10px', marginTop: '20px', backgroundColor:'#FCFCFC' }} id="outlined-basic" label="Please describe the research questions of the study in max 400 characters." multiline rows={4} maxRows={10} value={abstract} onChange={handleAbstract}/>
              <div style={{ width: '35%' }}></div>
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
                    <HelpOutlineIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip>
                </div>
                <div style={{ marginTop: "10px", width: '80%' }}>
                  <Typography variant="subtitle1" gutterBottom style={{ marginTop:'30px', marginBottom:'10px' }}>
                  <b>Please select study descriptors.</b>
                  </Typography>
                </div>
                <div style={{ marginTop: "10px", width: '80%' }}>
                  <FormGroup>
                      <div >
                        {
                          StudyKeywords.map((item) => <FormControlLabel control={<Checkbox size="small" color="default" />} checked={selectedStudyKewords.includes(item)} onChange={handleStudyKeywords} label={item} name={item} />)
                        }
                    </div>
                  </FormGroup>
                </div>
                 </div>
          );
    case 2:
      return (
        <div>
            <TextField size="small" variant="standard" style={{ marginTop:'20px', width: '70%' }} id="outlined-basic" label="Title"  value={report_title} onChange={handleReportTitle} />
            <CustomAutocomplete width="70%" type="author" showSelectedElements={true} editHandler={HandleEditAuthors}  addNewHandler={HandleAddNewAuthor}  manyItems optionsSet={authors} kind='Authors' handler={authorsHandler} selectedElements={selectedAuthors}  />
            <TextField ssize="small" variant="standard" style={{ width: '70%', marginTop:'20px' }} id="outlined-basic" label="DOI" value={doi} onChange={handleDOI} />
            <TextField size="small" variant="standard" style={{ width: '70%', marginTop:'20px' }} id="outlined-basic" label="Place of publication" value={place_of_publication} onChange={handlePlaceOfPublication} />
            <TextField size="small" variant="standard" style={{ width: '70%', marginTop:'20px' }} id="outlined-basic" label="Link to study report" value={link_to_study} onChange={handleLinkToStudy} />
            <LocalizationProvider dateAdapter={AdapterDayjs}>
              <Stack spacing={3}  style={{ marginTop:'20px', width: '70%', marginBottom:'40px' }}>
                <DesktopDatePicker
                    label='Date of publication'
                    inputFormat="YYYY-MM-DD"
                    value={date_of_publication}
                    onChange={(newValue) => {
                      setDateOfPublication(newValue);
                    }}
                    renderInput={(params) => <TextField {...params} size="small" variant="standard" />}
                  />
              </Stack>
            </LocalizationProvider>
        </div>
      );
    case 3:
      return (
        <div>
            <CustomAutocompleteWithoutAddNew  width="50%" showSelectedElements={true} optionsSet={sectorDivisions} kind='Do you use a predefined sector division? ' handler={sectorDivisionsHandler} selectedElements={selectedSectorDivisions}/>
            <CustomTreeViewWithCheckBox flat={true} 
                                        showFilter={false} 
                                        size="360px" 
                                        checked={selectedSectors} 
                                        expanded={expandedSectors} 
                                        handler={sectorsHandler} 
                                        expandedHandler={expandedSectorsHandler} 
                                        data={filteredSectors} 
                                        title={"Which sectors are considered in the study?"} 
                                        toolTipInfo={['A sector is generically dependent continuant that is a subdivision of a system.', 'http://openenergy-platform.org/ontology/oeo/OEO_00000367']} />
        </div>
            );
    case 4:
      return (
        <div>
          <CustomTreeViewWithCheckBox showFilter={false}
                                      size="260px" 
                                      checked={selectedTechnologies} 
                                      expanded={getNodeIds(technologies['children'])} 
                                      handler={technologyHandler} 
                                      expandedHandler={expandedTechnologyHandler} 
                                      data={technologies} 
                                      title={"What technologies are considered?"} 
                                      toolTipInfo={['A technology is a plan specification that describes how to combine artificial objects or other material entities and processes in a specific way.', 'http://openenergy-platform.org/ontology/oeo/OEO_00000407']} 
                                      />
        
        </div>
      );
    case 5:
          return (
            renderScenario()
          );
    case 6:
      return (
        <CustomAutocompleteWithoutEdit  width="60%" type="Model" manyItems showSelectedElements={true} optionsSet={oep_models} kind='Models' handler={modelsHandler} selectedElements={selectedModels}/>
      );
    case 7:
      return (
        <CustomAutocompleteWithoutEdit  width="60%" type="Frameworks"  manyItems showSelectedElements={true}  optionsSet={oep_frameworks} kind='Frameworks' handler={frameworksHandler} selectedElements={selectedFrameworks}/>
      );
    // case 9:
    //   return (
    //     <div>
    //       <Sunburst 
    //         width="700" 
    //         data={sunburstData} 
    //         handleNonFittingLabel={handleNonFittingLabelFn}  
    //         minSliceAngle={0.4} 
    //         label={"label"} 
    //         sort={((a, b) => a.value - b.value)}
    //         excludeRoot={true}
    //         radiusScaleExponent={1}
    //       />
    //     </div>
    //   );
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
        <BreadcrumbsNavGrid acronym={acronym} id={id} mode={mode} />
        <Container maxWidth="xl">

          <Grid item xs={12}>
            <Backdrop
              sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
              open={openBackDrop}
              onClick={handleCloseBackDrop}
            >
              <CircularProgress color="inherit" />
            </Backdrop>
          </Grid>
        

          <Grid item xs={12}>
            <Grid container
              direction="row"
              justifyContent="space-between"
              alignItems="center"
              >
          <CustomSwap handleSwap={handleSwap} />
          <div style={{ 'textAlign': 'center' }}>
            {/* <Box sx={{ position: 'relative', display: 'inline-flex' }}>
              <CircularProgress variant="determinate" value={60} size={60} />
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
              <Typography variant="h6" component="div">
                <b>{`${Math.round(60)}%`}</b>
              </Typography>
              </Box>
            </Box> */}
          </div>
          <div style={{ 'textAlign': 'right' }}>
            {mode === 'edit' && <Tooltip title="Save factsheet">
              <Button disableElevation={true} size="small" style={{ 'height': '43px', 'textTransform': 'none', 'marginTop': '10px', 'marginRight': '5px', 'zIndex': '1000' }} variant="contained" color="primary" onClick={handleSaveFactsheet} startIcon={<SaveIcon />}> Save </Button>
            </Tooltip>}
            <Tooltip title="Share this factsheet">
              <Button  disableElevation={true} size="small" style={{ 'height': '43px', 'textTransform': 'none', 'marginTop': '10px', 'marginRight': '5px', 'zIndex': '1000' }} variant="outlined" color="primary" startIcon={<ShareIcon/>}> Share </Button>
            </Tooltip>
            <Tooltip title="Delete factsheet">
              <Button disableElevation={true} size="small" style={{ 'height': '43px', 'textTransform': 'none', 'marginTop': '10px', 'marginRight': '10px', 'zIndex': '1000' }} variant="outlined" color="primary" onClick={handleClickOpenRemovedDialog} startIcon={<DeleteOutlineIcon/>}> Delete </Button>
            </Tooltip>
          </div >
          </Grid>
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
              <Link to={`factsheet/`} onClick={() => { axios.post(conf.toep + 'sirop/delete/', null, { params: { id: id } }).then(response => setOpenRemovedDialog(true));
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
                  <Grid item xs={12} style={{ 'overflow': 'auto' }}>
                    <Divider style={{ marginBottom: '40px' }}/>
                    <CustomTabs
                      items={items}
                    />
                    {/* <Stepper activeStep={activeStep}  >
                      {steps.map((label, index) => (
                      <Step key={label} >
                        <StepLabel onClick={() => handleStepClick(index)}><b>{label}</b></StepLabel>
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
                    </Stepper> */}
                  </Grid>
                </Grid>
            </div>
          }

          {mode === "overview" &&
             <Grid container justifyContent="space-between"
             alignItems="start"
             spacing={2}>
             <Grid item xs={12} >
               <Divider style={{ marginBottom: '20px', marginTop: '20px' }}/>
              </Grid>
              <Grid item xs={12}  >
               <b style={{ color: 'clack', marginLeft:'20px', fontSize:'24px' }}>{studyName !== undefined && studyName}</b> 
              </Grid>
              <Grid item xs={3} >
                <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Acronym</b> </span>
                <span >
                <HtmlTooltip
                  title={
                  <React.Fragment>
                    <Typography color="inherit" variant="subtitle1">
                      {'An acronym is an abbreviation of the title by using the first letters of each part of the title.'}
                      <br />
                      <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000048">More info...</a>
                    </Typography>
                  </React.Fragment>
                }
                >
                <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                </HtmlTooltip>
                </span>
              </Grid>
              <Grid item xs={9} >
                {acronym}
              </Grid>

              <Grid item xs={3} >
                <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Contact person(s):</b> </span>
                <span >
                  <HtmlTooltip
                    title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'A contact person is an agent that can be contacted for help or information about a specific service or good.'}
                        <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000107">More info...</a>
                      </Typography>
                    </React.Fragment>
                  }
                  >
                  <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip>
                </span>
              </Grid>
              <Grid item xs={9} style={{ paddingTop: '10px' }}>
                {selectedContactPerson.map((v, i) => (
                           <span> <span> {v.name} </span> <span>  <b className="separator-dot"> . </b> </span> </span>
                          ))}
              </Grid>

              <Grid item xs={3} >
                <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Institutions: </b> </span>
                <span >
                  <HtmlTooltip
                    title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'An institution is an organisation that serves a social purpose.'}
                        <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00000238">More info...</a>
                      </Typography>
                    </React.Fragment>
                  }
                  >
                  <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip>
                </span>
              </Grid>
              <Grid item xs={9} style={{ paddingTop: '10px' }}>
                {selectedInstitution.map((v, i) => (
                           <span> <span> {v.name} </span> <span>   <b className="separator-dot"> . </b> </span> </span>
                ))}
              </Grid>

              <Grid item xs={3} >
                <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Funding sources: </b> </span>
                <span >
                  {/* <HtmlTooltip
                    title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'A study is a project with the goal to investigate something.'}
                        <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00020011">More info from Open Enrgy Ontology (OEO)...</a>
                      </Typography>
                    </React.Fragment>
                  }
                  >
                  <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip> */}
                </span>
              </Grid>
              <Grid item xs={9} style={{ paddingTop: '10px' }} >
              {selectedFundingSource.map((v, i) => (
                            <span> <span> {v.name} </span> <span>  <b className="separator-dot"> . </b> </span> </span>
                          ))}
              </Grid>

              <Grid item xs={3} >
                <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Descriptors: </b> </span>
                <span >
                  {/* <HtmlTooltip
                    title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'A study is a project with the goal to investigate something.'}
                        <br />
                        <a href="http://openenergy-platform.org/ontology/oeo/OEO_00020011">More info from Open Enrgy Ontology (OEO)...</a>
                      </Typography>
                    </React.Fragment>
                  }
                  >
                  <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                  </HtmlTooltip> */}
                </span>
              </Grid>
              <Grid item xs={9} style={{ paddingTop: '10px' }}>
               {selectedStudyKewords.map((v, i) => (
                          <span> <span> {v} </span> <span>   <b className="separator-dot"> . </b></span> </span>
                          ))}
              </Grid>

              <Grid item xs={3} >
                <span style={{ color: '#294456', marginLeft:'20px' }}> <b>Abstract: </b> </span>
                <span >
                <HtmlTooltip
                  title={
                  <React.Fragment>
                    <Typography color="inherit" variant="subtitle1">
                      {'A summary of the resource.'}
                      <br />
                      <a href="https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#abstract">More info...</a>
                    </Typography>
                  </React.Fragment>
                }
                >
                <InfoOutlinedIcon sx={{ color: '#708696' }}/>
                </HtmlTooltip>
                </span>
              </Grid>
              <Grid item xs={9} style={{ paddingTop: '10px' }}>
               <div  style={{ width:'90%' }}> {abstract !== undefined && abstract}  </div>
              </Grid>
              <Grid item xs={12} >
                <CustomTabs
                  items={overview_items}
                />
              </Grid>
               

            </Grid>}

        
        </Grid>
        </Container>
      </Grid>
    </div>
  );
}


export default Factsheet;
