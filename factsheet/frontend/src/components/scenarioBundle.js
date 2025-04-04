import React, { useState, useEffect, useRef } from 'react';
import Grid from '@mui/material/Grid';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import ColorToggleButton from './customSwapButton.js';
import CustomTabs from './customTabs.js';
import CustomAutocomplete from './customAutocomplete.js';
import CustomAutocompleteWithoutEdit from './customAutocompleteWithoutEdit.js';
import Scenario from './scenario.js';
import CustomTreeViewWithCheckBox from './customTreeViewWithCheckbox.js';
import Snackbar from '@mui/material/Snackbar';
import Typography from '@mui/material/Typography';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline.js';
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
import ContentCopyOutlinedIcon from '@mui/icons-material/ContentCopyOutlined';
import AddIcon from '@mui/icons-material/Add.js';
import Checkbox from '@mui/material/Checkbox';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import conf from "../conf.json";
import { colors, Tooltip } from '@mui/material';
import HtmlTooltip from '../styles/oep-theme/components/tooltipStyles.js'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline.js';
import { styled } from '@mui/material/styles';
import SaveIcon from '@mui/icons-material/Save.js';
import uuid from "react-uuid";
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import CircularProgress from '@mui/material/CircularProgress';
import Badge from '@mui/material/Badge';
import { Route, Routes, useNavigate } from 'react-router-dom';
import ShareIcon from '@mui/icons-material/Share.js';
import sunburstKapsule from 'sunburst-chart';
import fromKapsule from 'react-kapsule';
import Select from '@mui/material/Select';
import CustomAutocompleteWithoutAddNew from './customAutocompleteWithoutAddNew.js';
import IconButton from '@mui/material/IconButton';
import Divider from '@mui/material/Divider';
import { makeStyles, Theme } from '@material-ui/core/styles';
import BreadcrumbsNavGrid from '../styles/oep-theme/components/breadcrumbsNavigation.js';
import TableContainer from '@mui/material/TableContainer';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import Toolbar from '@mui/material/Toolbar';
import { ContentTableCell, FirstRowTableCell } from '../styles/oep-theme/components/tableStyles.js';
import InfoListItem from '../styles/oep-theme/components/infoListItem.js'
import BundleScenariosGridItem from '../styles/oep-theme/components/editBundleScenariosForms.js';
import AttachmentIcon from '@mui/icons-material/Attachment.js';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined.js';
import FeedOutlinedIcon from '@mui/icons-material/FeedOutlined.js';
import LinkIcon from '@mui/icons-material/Link.js';
import Chip from '@mui/material/Chip';
import Container from '@mui/material/Container';
import Backdrop from '@mui/material/Backdrop';

import CSRFToken from './csrfToken.js';

import '../styles/App.css';
import { TableRow } from '@mui/material';
import variables from '../styles/oep-theme/variables.js';

import StudyKeywords from './scenarioBundleUtilityComponents/StudyDescriptors.js';
import handleOpenURL from './scenarioBundleUtilityComponents/handleOnClickTableIRI.js';
import { RichTreeView } from '@mui/x-tree-view/RichTreeView';

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
  const [notTheOwner, setNotTheOwner] = useState(false);
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
  const [models, setModels] = useState([]);
  const [frameworks, setFrameworks] = useState([]);
  const [sunburstData, setSunburstData] = useState([]);

  const [openBackDrop, setOpenBackDrop] = React.useState(false);


  const scenarioYears = Array.from({ length: 101 }, (_, i) => ({
    id: 2000 + i,
    name: String(2000 + i)
  }));

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
    <HelpOutlineIcon sx={{ fontSize: '24px', color: '#708696', marginLeft: '-10px' }} />
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
  const [selectedInstitution, setSelectedInstitution] = useState(id !== 'new' ? fsData.institution : []);
  const [selectedFundingSource, setSelectedFundingSource] = useState(id !== 'new' ? fsData.funding_sources : []);
  const [selectedContactPerson, setselectedContactPerson] = useState(id !== 'new' ? fsData.contact_person : []);
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

  const [publications, setPublications] = useState(id !== 'new' ? fsData.publications : [{
    id: uuid(),
    report_title: '',
    authors: [],
    doi: '',
    link_to_study_report: '',
    date_of_publication: '',
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
  const [publicatioTabValue, setPublicationTabValue] = React.useState(0);

  const [technologies, setTechnologies] = React.useState([]);
  const [selectedTechnologies, setSelectedTechnologies] = useState(id !== 'new' ? fsData.technologies : []);
  const [selectedTechnologiesTree, setSelectedTechnologiesTree] = useState(id !== 'new' ? fsData.technologies : []);
  const [allNodeIds, setAllNodeIds] = useState([]);
  
  const [expandedTechnologyList, setExpandedTechnologyList] = useState([]);

  const [scenarioDescriptors, setScenarioTypes] = React.useState([]);
  const [selectedScenarioDescriptors, setSelectedScenarioDescriptors] = useState([]);

  const [modelsList, setModelsList] = useState([]);

  const getModelList = async () => {
    const { data } = await axios.get(conf.toep + `api/v0/factsheet/models/`, {
      headers: { 'X-CSRFToken': CSRFToken() }
    });
    return data;
  };


  useEffect(() => {
    getModelList().then((data) => {
      const tmp = [];
      data.map((item) => tmp.push({ 'url': item.url, 'name': item.model_name, 'acronym':item.acronym, 'institutions': item.institutions, 'license': item.license, 'id': item.id }));
      setModelsList(tmp);
    });
  }, []);

  const [frameworksList, setFrameworkList] = useState([]);
  
  const getFrameworkList = async () => {
    const { data } = await axios.get(conf.toep + `api/v0/factsheet/frameworks/`, {
      headers: { 'X-CSRFToken': CSRFToken() }
    });
    return data;
  };

  useEffect(() => {
    getFrameworkList().then((data) => {
      const tmp = [];
      data.map((item) => tmp.push({ 'url': item.url, 'name': item.model_name, 'acronym':item.acronym, 'institutions': item.institutions, 'license': item.license, 'id': item.id }));
      setFrameworkList(tmp);
    });
  }, []);



  const handleScenarioTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setScenarioTabValue(newValue);
  }

  const handlePublicationTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setPublicationTabValue(newValue);
  }


  const populateFactsheetElements = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/populate_factsheets_elements/`);
    return data;
  };

  const getNodeIds = (nodes) => {
    let ids = [];

    nodes?.forEach(({ value, children }) => {
      ids = [...ids, value, ...getNodeIds(children)];
    });
    return ids;
  };

  let idCounter = 1;
  function generateUniqueId() {
    return idCounter++;
  }

  function filterByValue(referenceList, obj) {
    const referenceSet = new Set(referenceList.map(item => item.value));
  
    function recursiveFilter(node) {
      const uniqueId = generateUniqueId();
  
      if (Array.isArray(node.children)) {
        node.children = node.children.map(recursiveFilter).filter(child => child !== null);
      }
  
      if (referenceSet.has(node.value) || (node.children && node.children.length > 0)) {
        return { ...node, id: uniqueId };
      }
  
      return null;
    }
  
    return obj.map(recursiveFilter).filter(node => node !== null);
  }


  useEffect(() => {
    populateFactsheetElements().then((data) => {

      function parse(arr) {
        return arr.map(obj => {
          Object.keys(obj).forEach(key => {
            if (key === 'label') {
              obj[key] = <span>
                <HtmlTooltip
                  title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {obj.definition}
                        <br />
                        <a href={obj.iri}>More info from Open Energy Ontology (OEO)....</a>
                      </Typography>
                    </React.Fragment>
                  }
                >
                  <InfoOutlinedIcon sx={{ color: '#708696', marginRight: "7px" }} />
                </HtmlTooltip>
                {obj.label}
              </span>;
            }
          })

          return obj;
        })
      }


      const all_technologies = parse(data.technologies['children']);
      setTechnologies(all_technologies);

      // setTechnologies(data.technologies['children']);
      
      // rephrase scenario descriptors to - types
      setScenarioTypes(data.scenario_descriptors);
      const sectors_with_tooltips = data.sectors.map(item =>
      ({
        ...item,
        label: <span>
          <HtmlTooltip
            title={
              <React.Fragment>
                <Typography color="inherit" variant="subtitle1">
                  {item.sector_difinition}
                  <br />
                  <a href={item.iri}>More info from Open Energy Ontology (OEO)....</a>
                </Typography>
              </React.Fragment>
            }
          >
            <InfoOutlinedIcon sx={{ color: '#708696', marginRight: "7px" }} />
          </HtmlTooltip>
          {item.label}
        </span>
      })
      );

      setSectors(sectors_with_tooltips);
      setFilteredSectors(sectors_with_tooltips);
      //setFilteredSectors([]);

      const sector_d = data.sector_divisions;
      sector_d.push({ "label": "Others", "name": "Others", "class": "Others", "value": "Others" });
      setSectorDivisions(sector_d);

      myChartRef.current = Sunburst
      const sampleData = {
        name: "root",
        label: "Energy carrier",
        children: []
      }
      setSunburstData(sampleData);


      const filteredResult = filterByValue(selectedTechnologies, technologies);
      // setSelectedTechnologiesTree(filteredResult[0]);
      // setSelectedTechnologies(s)

      function getAllNodeIds(nodes) {
        let ids = [];
        nodes.forEach(node => {
          ids.push(node.id);
          if (node.children) {
            ids = ids.concat(getAllNodeIds(node.children));
          }
        });
        return ids;
      }

      const allIds = getAllNodeIds(filteredResult[0]["children"]);
      setAllNodeIds(allIds);

    }, []);

  }, []); // Todo: check if the empty dependency array raises errors

  const handleSaveFactsheet = () => {
    setOpenBackDrop(true);
    factsheetObjectHandler('name', factsheetName);
    if (acronym !== '') {
      if (id === 'new' && !isCreated) {
        const new_uid = uuid()
        axios.post(conf.toep + 'scenario-bundles/add/',
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
            scenarios: JSON.stringify(scenarios),
            publications: JSON.stringify(publications),
            models: JSON.stringify(selectedModels),
            frameworks: JSON.stringify(selectedFrameworks),
          },
          {
            headers: { 'X-CSRFToken': CSRFToken() }
          }
        ).then(response => {
          if (response.status === 200) {
            // Handle successful response

            if (response.data === 'Factsheet saved') {
              navigate('/factsheet/fs/' + new_uid);
              setIsCreated(true);
              setOpenSavedDialog(true);
              setUID(new_uid);
              setOpenBackDrop(false);
            }
            else if (response.data === 'Factsheet exists') {
              setOpenExistDialog(true);
              setOpenBackDrop(false);
            }

          }

        }).catch(error => {
          if (error.response && error.response.status === 403) {
            // Handle "Access Denied" error
            const redirectUrl = conf.toep + "/user/login/?next=/scenario-bundles/id/new";
            window.location.href = redirectUrl;
          }
        });
      } else {
        axios.get(conf.toep + `scenario-bundles/get/`, { params: { id: uid } }).then(res => {
          axios.post(conf.toep + 'scenario-bundles/update/',
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
              scenarios: JSON.stringify(scenarios),
              publications: JSON.stringify(publications),
              models: JSON.stringify(selectedModels),
              frameworks: JSON.stringify(selectedFrameworks),
            },
            {
              headers: { 'X-CSRFToken': CSRFToken() }
            }
          ).then(response => {
            if (response.data === "factsheet updated!") {
              setUID(uid);
              setOpenUpdatedDialog(true);
              setOpenBackDrop(false);
            }
            else if (response.data === 'Factsheet exists') {
              setOpenExistDialog(true);
              setOpenBackDrop(false);
            }
          })
            .catch(error => {
              console.error('API Error:', error.message);
              if (error.response && error.response.status === 403) {
                // Handle "Access Denied" error
                setNotTheOwner(true);
              }
            })
            .finally(() => {
              // Close the backdrop regardless of success or error
              setOpenBackDrop(false);
            });
        });
      }

    } else {
      setEmptyAcronym(true);
      setOpenBackDrop(false);
    }
  };

  const handleRemoveFactsheet = () => {
    axios.post(conf.toep + 'scenario-bundles/delete/', null, { params: { id: id } }, { headers: { 'X-CSRFToken': CSRFToken() } }
    ).then(response => setOpenRemovedDialog(true));
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

  const handleReportTitle = (event, index) => {
    const updatePublications = [...publications];
    updatePublications[index].report_title = event.target.value;
    setPublications(updatePublications);
  };

  const handleDOI = (event, index) => {
    const updatePublications = [...publications];
    updatePublications[index].doi = event.target.value;
    setPublications(updatePublications);
  };

  const handleFactsheetName = e => {
    setFactsheetName(e.target.value);
    factsheetObjectHandler('name', e.target.value);
  };

  // const handlePlaceOfPublication = e => {
  //   setPlaceOfPublication(e.target.value);
  //   factsheetObjectHandler('place_of_publication', e.target.value);
  // };

  const handleLinkToStudy = (event, index) => {
    const updatePublications = [...publications];
    updatePublications[index].link_to_study_report = event.target.value;
    setPublications(updatePublications);
  };

  // const handleDateOfPublication = e => {
  //   setDateOfPublication(e.target.value);
  //   factsheetObjectHandler('date_of_publication', e.target.value);
  // };

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
      obj[element] = value
    setScenarios(newScenarios);
    factsheetObjectHandler('scenarios', JSON.stringify(newScenarios));
  };

  const handleScenariosAutoCompleteChange = (selectedList, name, idx) => {
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
      descriptors: [],
      input_datasets: [],
      output_datasets: [],
    });
    setScenarios(newScenarios);
  };

  const handleAddPublication = () => {
    const newPublications = [...publications];
    newPublications.push({
      id: uuid(),
      report_title: '',
      authors: [],
      doi: '',
      link_to_study_report: '',
      date_of_publication: '',
    });
    setPublications(newPublications);
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
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000238' } });
    return data;
  };

  const getFundingSources = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00090001' } });
    return data;
  };

  const getContactPersons = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000107' } });
    return data;
  };

  const getAuthors = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000064' } });
    return data;
  };

  const getScenarioRegions = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_entities_by_type/`, { params: { entity_type: 'OBO.BFO_0000006' } });
    return data;
  };

  const getScenarioInteractingRegions = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00020036' } });
    return data;
  };

/*   const getScenarioYears = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_entities_by_type/`, { params: { entity_type: 'OBO.OEO_00020097' } });
    return data;
  }; */

  const getModels = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000274' } });
    return data;
  };

  const getFrameworks = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000172' } });
    return data;
  };

  useEffect(() => {
    getInstitution().then((data) => {
      const tmp = [];
      data.map((item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }));
      setInstitutions(tmp);
    });
  }, []);

  useEffect(() => {
    getFundingSources().then((data) => {
      const tmp = [];
      data.map((item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }))
      setFundingSources(tmp);
    });
  }, []);

  useEffect(() => {
    getContactPersons().then((data) => {
      const tmp = [];
      data.map((item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }))
      setContactPersons(tmp);
    });
  }, []);

  useEffect(() => {
    getAuthors().then((data) => {
      const tmp = [];
      data.map((item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }))
      setAuthors(tmp);
    });
  }, []);

  useEffect(() => {
    getScenarioRegions().then((data) => {
      const tmp = [];
      data.map((item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }))
      setScenarioRegions(tmp);
    });
  }, []);

  useEffect(() => {
    getScenarioInteractingRegions().then((data) => {
      const tmp = [];
      data.map((item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }))
      setScenarioInteractingRegions(tmp);
    });
  }, []);

/*   useEffect(() => {
    getScenarioYears().then((data) => {
      const tmp = [];
      data.map((item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }))
      setScenarioYears(tmp);
    });
  }, []); */

  useEffect(() => {
    getModels().then((data) => {
      const tmp = [];
      data.map((item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }))
      setModels(tmp);
    });
  }, []);

  useEffect(() => {
    getFrameworks().then((data) => {
      const tmp = [];
      data.map((item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }))
      setFrameworks(tmp);
    });
  }, []);


  const HandleAddNewInstitution = (newElement) => {
    axios.post(conf.toep + 'scenario-bundles/add_entities/',
      {
        entity_type: 'OEO.OEO_00000238',
        entity_label: newElement.name,
        entity_iri: newElement.iri
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'A new entity added!') {
        setOpenAddedDialog(true);
        setAddedEntity(['Institution', newElement.name]);
        getInstitution().then((data) => {
          const tmp = [];
          data.map((item) => tmp.push(item))
          setInstitutions(tmp);
        });
      }
    });
  }


  const HandleEditInstitution = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'scenario-bundles/update_an_entity/',
      {
        entity_type: 'OEO.OEO_00000238',
        entity_label: oldElement,
        new_entity_label: newElement,
        entity_iri: editIRI
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'entity updated!') {
        setOpenEditDialog(true);
        setEditedEntity(['Institution', oldElement, newElement]);
        getInstitution().then((data) => {
          const tmp = [];
          data.map((item) => tmp.push(item))
          setInstitutions(tmp);
        });
      }
    });
  }

  const HandleAddNewFundingSource = (newElement) => {
    axios.post(conf.toep + 'scenario-bundles/add_entities/',
      {
        entity_type: 'OEO.OEO_00090001',
        entity_label: newElement.name,
        entity_iri: newElement.iri
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'A new entity added!')
        setOpenAddedDialog(true);
      setAddedEntity(['Funding source', newElement.name]);
      getFundingSources().then((data) => {
        const tmp = [];
        data.map((item) => tmp.push(item))
        setFundingSources(tmp);
      });
    });
  }

  const HandleEditFundingSource = (oldElement, newElement, editIRI) => {
    console.log(editIRI)
    axios.post(conf.toep + 'scenario-bundles/update_an_entity/',
      {
        entity_type: 'OEO.OEO_00090001',
        entity_label: oldElement,
        new_entity_label: newElement,
        entity_iri: editIRI
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'entity updated!') {
        setOpenEditDialog(true);
        setEditedEntity(['Funding source', oldElement, newElement]);
        getFundingSources().then((data) => {
          const tmp = [];
          data.map((item) => tmp.push(item))
          setFundingSources(tmp);
        });
      }
    });
  }

  const HandleAddNewContactPerson = (newElement) => {
    axios.post(conf.toep + 'scenario-bundles/add_entities/',
      {
        entity_type: 'OEO.OEO_00000107',
        entity_label: newElement.name,
        entity_iri: newElement.iri
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'A new entity added!')
        setOpenAddedDialog(true);
      setAddedEntity(['Contact person', newElement.name]);

      getContactPersons().then((data) => {
        const tmp = [];
        data.map((item) => tmp.push(item))
        setContactPersons(tmp);
      });
    });
  }

  const HandleEditContactPerson = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'scenario-bundles/update_an_entity/',
      {
        entity_type: 'OEO.OEO_00000107',
        entity_label: oldElement,
        new_entity_label: newElement,
        entity_iri: editIRI
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'entity updated!') {
        setOpenEditDialog(true);
        setEditedEntity(['Contact person', oldElement, newElement]);
        getAuthors().then((data) => {
          const tmp = [];
          data.map((item) => tmp.push(item))
          setAuthors(tmp);
        });
      }
    });
  }

  const HandleAddNewAuthor = (newElement) => {
    axios.post(conf.toep + 'scenario-bundles/add_entities/',
      {
        entity_type: 'OEO.OEO_00000064',
        entity_label: newElement.name,
        entity_iri: newElement.iri
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'A new entity added!')
        setOpenAddedDialog(true);
      setAddedEntity(['Author', newElement.name]);

      getAuthors().then((data) => {
        const tmp = [];
        data.map((item) => tmp.push(item))
        setAuthors(tmp);
      });
    });
  }

  const HandleEditAuthors = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'scenario-bundles/update_an_entity/',
      {
        entity_type: 'OEO.OEO_00000064',
        entity_label: oldElement,
        new_entity_label: newElement,
        entity_iri: editIRI
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'entity updated!') {
        setOpenEditDialog(true);
        setEditedEntity(['Author', oldElement, newElement]);
        getAuthors().then((data) => {
          const tmp = [];
          data.map((item) => tmp.push(item))
          setAuthors(tmp);
        });
      }
    });
  }

  const HandleAddNewRegion = (newElement) => {
    axios.post(conf.toep + 'scenario-bundles/add_entities/',
      {
        'entity_type': 'OEO.OEO_00020032',
        'entity_label': newElement.name,
        'entity_iri': newElement.iri,
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'A new entity added!')
        setOpenAddedDialog(true);
      setAddedEntity(['Spatial region', newElement.name]);

      getScenarioRegions().then((data) => {
        const tmp = [];
        data.map((item) => tmp.push(item))
        setScenarioRegions(tmp);
      });
    });
  }

  const HandleEditRegion = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'scenario-bundles/update_an_entity/',
      {
        entity_type: 'OBO.BFO_0000006',
        entity_label: oldElement,
        new_entity_label: newElement,
        entity_iri: editIRI
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'entity updated!') {
        setOpenEditDialog(true);
        setEditedEntity(['Spatial region', oldElement, newElement]);
        getScenarioRegions().then((data) => {
          const tmp = [];
          data.map((item) => tmp.push(item))
          setScenarioRegions(tmp);
        });
      }
    });
  }

  const HandleAddNewInteractingRegion = (newElement) => {
    axios.post(conf.toep + 'scenario-bundles/add_entities/',
      {
        entity_type: 'OEO.OEO_00020036',
        entity_label: newElement.name,
        entity_iri: newElement.iri
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'A new entity added!')
        setOpenAddedDialog(true);
      setAddedEntity(['Interacting region', newElement.name]);

      getScenarioInteractingRegions().then((data) => {
        const tmp = [];
        data.map((item) => tmp.push(item))
        setScenarioInteractingRegions(tmp);
      });
    });
  }

  const HandleEditInteractingRegion = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'scenario-bundles/update_an_entity/',
      {
        entity_type: 'OEO.OEO_00020036',
        entity_label: oldElement,
        new_entity_label: newElement,
        entity_iri: editIRI
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'entity updated!') {
        setOpenEditDialog(true);
        setEditedEntity(['Interacting region', oldElement, newElement]);
        getScenarioInteractingRegions().then((data) => {
          const tmp = [];
          data.map((item) => tmp.push(item))
          setScenarioInteractingRegions(tmp);
        });
      }
    });
  }

/*   const HandleAddNNewScenarioYears = (newElement) => {
    axios.post(conf.toep + 'scenario-bundles/add_entities/',
      {
        entity_type: 'OBO.OEO_00020097',
        entity_label: newElement.name,
        entity_iri: newElement.iri
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'A new entity added!')
        setOpenAddedDialog(true);
      setAddedEntity(['Scenario year', newElement.name]);

      getScenarioYears().then((data) => {
        const tmp = [];
        data.map((item) => tmp.push(item))
        setScenarioYears(tmp);
      });
    });
  } */

/*   const HandleEditScenarioYears = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'scenario-bundles/update_an_entity/',
      {
        entity_type: 'OBO.OEO_00020097',
        entity_label: oldElement,
        new_entity_label: newElement,
        entity_iri: editIRI
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'entity updated!') {
        setOpenEditDialog(true);
        setEditedEntity(['Scenario year', oldElement, newElement]);
        getScenarioYears().then((data) => {
          const tmp = [];
          data.map((item) => tmp.push(item))
          setScenarioYears(tmp);
        });
      }
    });
  } */

  const HandleAddNewModel = (newElement) => {
    axios.post(conf.toep + 'scenario-bundles/add_entities/',
      {
        entity_type: 'OEO.OEO_00000274',
        entity_label: newElement.name,
        entity_iri: newElement.iri
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'A new entity added!')
        setOpenAddedDialog(true);
      setAddedEntity(['Model', newElement.name]);

      getModels().then((data) => {
        const tmp = [];
        data.map((item) => tmp.push(item))
        setModels(tmp);
      });
    });
  }

  const HandleEditModels = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'scenario-bundles/update_an_entity/',
      {
        entity_type: 'OEO.OEO_00000274',
        entity_label: oldElement,
        new_entity_label: newElement,
        entity_iri: editIRI
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'entity updated!') {
        setOpenEditDialog(true);
        setEditedEntity(['Model', oldElement, newElement]);
        getModels().then((data) => {
          const tmp = [];
          data.map((item) => tmp.push(item))
          setModels(tmp);
        });
      }
    });
  }

  const HandleAddNewFramework = (newElement) => {
    axios.post(conf.toep + 'scenario-bundles/add_entities/',
      {
        entity_type: 'OEO.OEO_00000172',
        entity_label: newElement.name,
        entity_iri: newElement.iri
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'A new entity added!')
        setOpenAddedDialog(true);
      setAddedEntity(['Framework', newElement.name]);

      getFrameworks().then((data) => {
        const tmp = [];
        data.map((item) => tmp.push(item))
        setFrameworks(tmp);
      });
    });
  }

  const HandleEditFramework = (oldElement, newElement, editIRI) => {
    axios.post(conf.toep + 'scenario-bundles/update_an_entity/',
      {
        entity_type: 'OEO.OEO_00000172',
        entity_label: oldElement,
        new_entity_label: newElement,
        entity_iri: editIRI
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      if (response.data === 'entity updated!') {
        setOpenEditDialog(true);
        setEditedEntity(['Framework', oldElement, newElement]);
        getFrameworks().then((data) => {
          const tmp = [];
          data.map((item) => tmp.push(item))
          setFrameworks(tmp);
        });
      }
    });
  }

  const sectorDivisionsHandler = (sectorDivisionsList) => {
    setSelectedSectorDivisions(sectorDivisionsList);
    let sectorsBasedOnDivisions = sectors.filter(item => sectorDivisionsList.map(item => item.class).includes(item.sector_division));
    if (sectorDivisionsList.some(e => e.label == 'Others')) {
      sectorsBasedOnDivisions = sectors;
    }
    setFilteredSectors(sectorsBasedOnDivisions);
  };


  const authorsHandler = (authorsList, index) => {
    const updatePublications = [...publications];
    updatePublications[index].authors = authorsList;
    setPublications(updatePublications);
  };

  const dateOfPublicationHandler = (date, index) => {
    const updatePublications = [...publications];
    updatePublications[index].date_of_publication = date;
    setPublications(updatePublications);
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

    console.log(entireObj);

    const objFiltered = entireObj.map(item =>
    ({
      ...item,
      label: item.value
    })
    );


    function safeStringify(obj, indent = 2) {
      const cache = new Set();
      return JSON.stringify(obj, (key, value) => {
        if (typeof value === 'object' && value !== null) {
          if (cache.has(value)) {
            // Circular reference found, return a placeholder object
            return '[Circular Reference]';
          }
          // Store the value in our set
          cache.add(value);
        }
        return value;
      }, indent);
    }

    JSON.stringify(objFiltered, (_, nestedValue) => {
      if (nestedValue && nestedValue[keyToFind] === valToFind) {
        foundObj = nestedValue;
      }
      return nestedValue;
    });
    return foundObj;
  };


  const scenarioDescriptorHandler = (descriptorList, nodes, id) => {
    const zipped = []
    descriptorList.map((v) => zipped.push({ "value": findNestedObj(nodes, 'value', v).value, "label": findNestedObj(nodes, 'value', v).label, "class": findNestedObj(nodes, 'value', v).iri }));
    const newScenarios = [...scenarios];
    const obj = newScenarios.find(el => el.id === id);
    obj.descriptors = zipped;
    setScenarios(newScenarios);
    factsheetObjectHandler('scenarios', JSON.stringify(newScenarios));

  };

  const technologyHandler = (technologyList, nodes) => {
    const zipped = []
    console.log(technologyList);
    technologyList.map((v) => zipped.push({ "value": findNestedObj(nodes, 'value', v).value, "label": findNestedObj(nodes, 'value', v).label, "class": findNestedObj(nodes, 'value', v).iri }));
    setSelectedTechnologies(zipped);
  };

  const expandedTechnologyHandler = (expandedTechnologyList) => {
    const zipped = []
    expandedTechnologyList.map((v) => zipped.push({ "value": v, "label": v }));
    setExpandedTechnologyList(zipped);
  };

  const sectorsHandler = (sectorsList, nodes) => {
    const zipped = []
    sectorsList.map((v) => zipped.push({ "value": findNestedObj(nodes, 'value', v).value, "label": findNestedObj(nodes, 'value', v).value, "class": findNestedObj(nodes, 'value', v).iri }));
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
  const tabClasses = { root: classes.tab };

  const renderScenario = () => {
    return <div>
      <Box sx={{ flexGrow: 1, display: 'flex', overflow: 'auto' }} >
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
              label={item.acronym !== undefined && item.acronym !== '' ? item.acronym.substring(0, 16) : 'Scenario ' + (Number(i) + Number(1))}
              key={'Scenario_tab_' + item.id}
              classes={tabClasses}
              style={{ border: '1px solid #cecece', marginBottom: '5px' }}
            />
          )}
          <Box sx={{ 'textAlign': 'center', 'marginTop': '5px', 'paddingLeft': '10px', 'paddingRight': '10px', }} >
            <IconButton
              color="primary"
              aria-label="add"
              size="small"
              onClick={handleAddScenario}
            >
              <AddIcon />
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
              //HandleEditScenarioYear={HandleEditScenarioYears}
              //HandleAddNNewScenarioYear={HandleAddNNewScenarioYears}
              scenarioDescriptorHandler={scenarioDescriptorHandler}
            />
          </TabPanel>
        )}
      </Box>
    </div >
  }

  const removePublication = (id) => {
    console.log(id);
    let newSpublications = [...publications].filter((obj => obj.id !== id));;
    console.log(newSpublications);
    setPublications(newSpublications);
    setRemoveReport(true);
  };

  const renderPublications = () => {
    return <div>
      <Box sx={{ flexGrow: 1, display: 'flex', overflow: 'auto' }} >
        <Tabs
          orientation="vertical"
          value={publicatioTabValue}
          onChange={handlePublicationTabChange}
          aria-label="Vertical tabs example"
          sx={{ borderRight: 1, borderColor: 'divider' }}
          key={'Publications_tabs'}
          classes={'tabs'}
        >
          {publications.map((item, i) =>
            <Tab
              label={item.acronym !== undefined && item.acronym !== '' ? item.acronym.substring(0, 16) : 'Publication ' + (Number(i) + Number(1))}
              key={'Publication_tab_' + item.id}
              classes={tabClasses}
              style={{ border: '1px solid #cecece', marginBottom: '5px' }}
            />
          )}
          <Box sx={{ 'textAlign': 'center', 'marginTop': '5px', 'paddingLeft': '10px', 'paddingRight': '10px', }} >
            <IconButton
              color="primary"
              aria-label="add"
              size="small"
              onClick={handleAddPublication}
            >
              <AddIcon />
            </IconButton>
          </Box>
        </Tabs>
        {publications.map((item, i) =>
          <TabPanel
            value={publicatioTabValue}
            index={i}
            style={{ width: '100%', overflow: 'auto' }}
            key={'Publication_panel_' + item.id}
          >
            <Grid container justifyContent="space-between" alignItems="start" spacing={2} >
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
                      onClick={() => removePublication(item.id)}
                    >  
                    <DeleteOutlineIcon />
                  </IconButton>
                )}
              />
              <BundleScenariosGridItem
                {...props}
                spanValue="Report title"
                tooltipText="A name given to the resource."
                hrefLink="http://purl.org/dc/elements/1.1/title"
                linkText="More info..."
                renderField={() => (
                  <TextField
                    size="small"
                    id="outlined-basic"
                    style={{ width: '100%' }}
                    variant="outlined"
                    value={item.report_title}
                    onChange={(event) => handleReportTitle(event, i)}
                  />
                )}
                TooltipComponent={HtmlTooltip}
              />
              <BundleScenariosGridItem
                {...props}
                spanValue="Authors"
                tooltipText="An author is an agent that creates or has created written work."
                hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00000064"
                renderField={() => (
                  <CustomAutocomplete
                    width="100%"
                    type="author"
                    showSelectedElements={true}
                    editHandler={HandleEditAuthors}
                    addNewHandler={HandleAddNewAuthor}
                    manyItems
                    optionsSet={authors}
                    handler={(e) => authorsHandler(e, i)}
                    selectedElements={publications[i].authors}
                  />
                )}
                TooltipComponent={HtmlTooltip}
              />
              <BundleScenariosGridItem
                {...props}
                spanValue="DOI"
                tooltipText="A DOI (digital object identifier) is a persistent identifier or handle used to uniquely identify objects, standardized by the International Organization for Standardization (ISO)."
                hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00000133"
                renderField={() => (
                  <TextField
                    size="small"
                    id="outlined-basic"
                    style={{ width: '100%' }}
                    variant="outlined"
                    value={item.doi}
                    onChange={(event) => handleDOI(event, i)}
                  />
                )}
                TooltipComponent={HtmlTooltip}
              />
              <BundleScenariosGridItem
                {...props}
                showTooltip={false}
                spanValue="Link to study report"
                tooltipText="A funder is a sponsor that supports by giving money."
                hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00090001"
                renderField={() => (
                  <TextField
                    size="small"
                    id="outlined-basic"
                    style={{ width: '100%' }}
                    variant="outlined"
                    value={item.link_to_study_report}
                    onChange={(event) => handleLinkToStudy(event, i)}
                  />
                )}
                TooltipComponent={HtmlTooltip}
              />
              <BundleScenariosGridItem
                {...props}
                showTooltip={false}
                spanValue="Year of publication"
                tooltipText="A funder is a sponsor that supports by giving money."
                hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00090001"
                renderField={() => (
                  <LocalizationProvider dateAdapter={AdapterDayjs}>
                    <Stack spacing={3} style={{ width: '20rem' }}>
                      <DesktopDatePicker
                        label=''
                        views={['year']}
                        value={publications[i].date_of_publication}
                        onChange={(newValue) => {
                          const dateObj = new Date(newValue);
                          const dateString = dateObj.getFullYear() + '/' + (dateObj.getMonth() + 1) + '/' + String(dateObj.getDate())
                          const d = new Date(dateString);
                          dateOfPublicationHandler(dateString, i);
                        }}
                        renderInput={(params) => <TextField {...params} size="small" variant="outlined" />}
                      />
                    </Stack>
                  </LocalizationProvider>
                )}
                TooltipComponent={HtmlTooltip}
              />
            </Grid>
          </TabPanel>
        )}
      </Box>
    </div >
  }


  const renderBasicInformation = () => (
    <Grid container justifyContent="space-between"
      alignItems="start"
      spacing={2}>
      <BundleScenariosGridItem
        {...props}
        spanValue="Study name"
        tooltipText="A study is a project with the goal to investigate something."
        hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00020011"
        renderField={() => (
          <TextField
            size="small"
            id="outlined-basic"
            style={{ width: '100%' }}
            variant="outlined"
            value={studyName}
            onChange={handleStudyName}
          />
        )}
        TooltipComponent={HtmlTooltip}
      />
      <BundleScenariosGridItem
        {...props}
        spanValue="Acronym"
        tooltipText="An acronym is an abbreviation of the title by using the first letters of each part of the title."
        hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00000048"
        renderField={() => (
          <TextField
            size="small"
            id="outlined-basic"
            style={{ width: '100%' }}
            variant="outlined"
            value={acronym}
            onChange={handleAcronym}
          />
        )}
        TooltipComponent={HtmlTooltip}
      />
      <BundleScenariosGridItem
        {...props}
        spanValue="Institutions"
        tooltipText="An institution is an organisation that serves a social purpose."
        hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00000238"
        renderField={() => (
          <CustomAutocomplete
            width="100%"
            type="institution"
            showSelectedElements={true}
            editHandler={HandleEditInstitution}
            addNewHandler={HandleAddNewInstitution}
            manyItems
            optionsSet={institutions}
            handler={institutionHandler}
            selectedElements={selectedInstitution}
          />
        )}
        TooltipComponent={HtmlTooltip}
      />
      <BundleScenariosGridItem
        {...props}
        spanValue="Contact person"
        tooltipText="A contact person is an agent that can be contacted for help or information about a specific service or good."
        hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00000107"
        renderField={() => (
          <CustomAutocomplete
            width="100%"
            type="institution"
            showSelectedElements={true}
            editHandler={HandleEditContactPerson}
            addNewHandler={HandleAddNewContactPerson}
            manyItems
            optionsSet={contactPersons}
            handler={contactPersonHandler}
            selectedElements={selectedContactPerson}
          />
        )}
        TooltipComponent={HtmlTooltip}
      />
    </Grid>

  );

  const renderStudyDetail = () => (
    <Grid container justifyContent="space-between" alignItems="start" spacing={2} >

      <BundleScenariosGridItem
        {...props}
        showTooltip={false}
        spanValue="Funding sources"
        tooltipText="A funder is a sponsor that supports by giving money."
        hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00090001"
        renderField={() => (
          <CustomAutocomplete
            width="100%"
            type="Funding source"
            showSelectedElements={true}
            editHandler={HandleEditFundingSource}
            addNewHandler={HandleAddNewFundingSource}
            manyItems
            optionsSet={fundingSources}
            handler={fundingSourceHandler}
            selectedElements={selectedFundingSource}
          />
        )}
        TooltipComponent={HtmlTooltip}
      />
      <BundleScenariosGridItem
        {...props}
        spanValue="Abstract"
        tooltipText="A summary of the resource."
        hrefLink="https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#abstract"
        linkText="More info..."
        renderField={() => (
          <TextField
            size="small"
            id="outlined-basic"
            style={{ width: '100%' }}
            variant="outlined"
            multiline
            rows={6}
            maxRows={10}
            value={abstract}
            onChange={handleAbstract}
          />
        )}
        TooltipComponent={HtmlTooltip}
      />
      <BundleScenariosGridItem
        {...props}
        showTooltip={false}
        spanValue="Study descriptors"
        tooltipText="A funder is a sponsor that supports by giving money.."
        hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00090001"
        renderField={() => (
          <FormGroup>
            <div >
              {
                StudyKeywords.map((item) =>
                  <span >
                    {item[1] !== '' ? <HtmlTooltip
                      style={{ marginLeft: '10px' }}
                      placement="top"
                      title={
                        <React.Fragment>
                          <Typography color="inherit" variant="caption">
                            {item[2]}
                            <br />
                            <a href={item[1]}>More info from Open Enrgy Ontology (OEO)...</a>
                          </Typography>
                        </React.Fragment>
                      }
                    >
                      <FormControlLabel control={
                        <Checkbox size="small" color="default" />
                      } checked={selectedStudyKewords.includes(item[0])} onChange={handleStudyKeywords} label={item[0]} name={item[0]}
                      />
                    </HtmlTooltip>
                      :
                      <HtmlTooltip
                        style={{ marginLeft: '10px' }}
                        placement="top"
                        title={
                          <React.Fragment>
                            <Typography color="inherit" variant="caption">
                              {"There is not yet an OEO class for this descriptor."}
                              <br />
                              {"We are aware of that and we will add it in future."}
                            </Typography>
                          </React.Fragment>
                        }
                      >
                        <FormControlLabel control={
                          <Checkbox size="small" color="default" />
                        } checked={selectedStudyKewords.includes(item[0])} onChange={handleStudyKeywords} label={item[0]} name={item[0]}
                        />
                      </HtmlTooltip>
                    }
                  </span>
                )
              }
            </div>
          </FormGroup>
        )
        }
        TooltipComponent={HtmlTooltip}
      />
    </Grid >
  );




  const renderSectorsAndTecnology = () => (
    <Grid container justifyContent="space-between" alignItems="start" spacing={2} >

      <BundleScenariosGridItem
        {...props}
        spanValue="Sector divisions"
        tooltipText="A sector division is a specific way to subdivide a system."
        hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00000368"
        renderField={() => (
          <CustomAutocompleteWithoutAddNew
            showSelectedElements={true}
            optionsSet={sectorDivisions}
            kind=''
            handler={sectorDivisionsHandler}
            selectedElements={selectedSectorDivisions}
          />
        )}
        TooltipComponent={HtmlTooltip}
      />
      <BundleScenariosGridItem
        {...props}
        spanValue="Sectors"
        tooltipText="A sector is generically dependent continuant that is a subdivision of a system."
        hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00000367"
        renderField={() => (
          <CustomTreeViewWithCheckBox
            flat={true}
            showFilter={false}
            size="360px"
            checked={selectedSectors}
            expanded={expandedSectors}
            handler={sectorsHandler}
            expandedHandler={expandedSectorsHandler}
            data={filteredSectors}
            title={"Which sectors are considered in the study?"}
            toolTipInfo={['A sector is generically dependent continuant that is a subdivision of a system.', 'https://openenergy-platform.org/ontology/oeo/OEO_00000367']}
          />
        )}
        TooltipComponent={HtmlTooltip}
      />
      <BundleScenariosGridItem
        {...props}
        spanValue="Technologies"
        tooltipText="A technology is a plan specification that describes how to combine artificial objects or other material entities and processes in a specific way."
        hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00000407"
        renderField={() => (
          <CustomTreeViewWithCheckBox
            showFilter={false}
            size="360px"
            checked={selectedTechnologies}
            expanded={getNodeIds(technologies['children'])}
            handler={technologyHandler}
            expandedHandler={expandedTechnologyHandler}
            data={technologies}
            title={"What technologies are considered?"}
            toolTipInfo={['A technology is a plan specification that describes how to combine artificial objects or other material entities and processes in a specific way.', 'https://openenergy-platform.org/ontology/oeo/OEO_00000407']}
          />
        )}
        TooltipComponent={HtmlTooltip}
      />

    </Grid>
  );

  const renderModelsAndFrameworks = () => (
    <Grid container justifyContent="space-between" alignItems="start" spacing={2} >

      <BundleScenariosGridItem
        {...props}
        spanValue="Models"
        tooltipText="A model is a generically dependent continuant that is used for computing an idealised reproduction of a system and its behaviours."
        hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00000274"
        renderField={() => (
          <CustomAutocompleteWithoutEdit
            type="Model"
            manyItems
            showSelectedElements={true}
            optionsSet={modelsList}
            kind='Models'
            handler={modelsHandler}
            selectedElements={selectedModels}
          />
        )}
        TooltipComponent={HtmlTooltip}
      />
      <BundleScenariosGridItem
        {...props}
        spanValue="Frameworks"
        tooltipText="A software framework is a Software that is generic and can be adapted to a specific application."
        hrefLink="https://openenergy-platform.org/ontology/oeo/OEO_00000382"
        renderField={() => (
          <CustomAutocompleteWithoutEdit
            type="Frameworks"
            manyItems
            showSelectedElements={true}
            optionsSet={frameworksList}
            kind='Frameworks'
            handler={frameworksHandler}
            selectedElements={selectedFrameworks}
          />
        )}
        TooltipComponent={HtmlTooltip}
      />

    </Grid>
  );

  const items = {
    titles: ['Basic information', 'Study detail', 'Publications', 'Sectors and technology', 'Scenarios', 'Models and frameworks'],
    contents: [
      renderBasicInformation(),
      renderStudyDetail(),
      renderPublications(),
      renderSectorsAndTecnology(),
      renderScenario(),
      renderModelsAndFrameworks() 
    ]
  }
  const scenario_count = 'Scenarios' + ' (' + scenarios.length + ')';
console.log(scenarios);

const renderScenariosOverview = () => (
  <Container maxWidth="lg2" sx={{ padding: '0px !important' }}>
    {scenarios.map((v, i) =>
      v.acronym !== '' ? (
        <React.Fragment key={i}>
          <Button startIcon={<ContentCopyOutlinedIcon />} variant="outlined" onClick={() => navigator.clipboard.writeText(v.id)}>
            Copy Scenario UID
            <HtmlTooltip
              title={
                <React.Fragment>
                  <Typography color="inherit" variant="subtitle1">
                    {'This can be used to copy the universal identifier for the scenario object below. You need the scenario UID if you want to edit the scenario using Web-API functionality.'}
                    <br />
                    <a href="https://openenergyplatform.github.io/oeplatform/oeplatform-code/web-api/oekg-api/scenario-dataset/">How to use the Web-API</a>
                  </Typography>
                </React.Fragment>
              }
            >
              <InfoOutlinedIcon sx={{ color: '#708696' }} />
            </HtmlTooltip>
          </Button>

          <TableContainer>
            <Table>
              <TableBody>
                <TableRow>
                  <FirstRowTableCell>
                    <div>
                      <span>Scenario name</span>
                      <HtmlTooltip
                        title={
                          <React.Fragment>
                            <Typography color="inherit" variant="subtitle1">
                              {'A scenario is an information content entity that contains statements about a possible future development based on a coherent and internally consistent set of assumptions and their motivation.'}
                              <br />
                              <a href="https://openenergy-platform.org/ontology/oeo/OEO_00000364">More info from Open Energy Ontology (OEO)...</a>
                            </Typography>
                          </React.Fragment>
                        }
                      >
                        <InfoOutlinedIcon sx={{ color: '#708696' }} />
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
                              <a href="https://openenergy-platform.org/ontology/oeo/OEO_00000048">More info from Open Energy Ontology (OEO)...</a>
                            </Typography>
                          </React.Fragment>
                        }
                      >
                        <InfoOutlinedIcon sx={{ color: '#708696' }} />
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
                        <InfoOutlinedIcon sx={{ color: '#708696' }} />
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
                      <span>Scenario type</span>
                      <HtmlTooltip
                        title={
                          <React.Fragment>
                            <Typography color="inherit" variant="subtitle1">
                              {'A scenario is an information content entity that contains statements about a possible future development based on a coherent and internally consistent set of assumptions and their motivation.'}
                              <br />
                              <a href="https://openenergy-platform.org/ontology/oeo/OEO_00000364">More info from Open Energy Ontology (OEO)....</a>
                            </Typography>
                          </React.Fragment>
                        }
                      >
                        <InfoOutlinedIcon sx={{ color: '#708696' }} />
                      </HtmlTooltip>
                    </div>
                  </FirstRowTableCell>
                  <ContentTableCell>
                    {v.descriptors.map((e) => <span> <span> <Chip sx={{ marginTop: "5px" }} label={e.label} size="small" variant="outlined" onClick={() => handleOpenURL(e.class)} /> </span> <span>  <b className="separator-dot">  </b> </span> </span>)}
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
                              <a href="https://openenergy-platform.org/ontology/oeo/OEO_00020097">More info from Open Energy Ontology (OEO)...</a>
                            </Typography>
                          </React.Fragment>
                        }
                      >
                        <InfoOutlinedIcon sx={{ color: '#708696' }} />
                      </HtmlTooltip>
                    </div>
                  </FirstRowTableCell>
                  <ContentTableCell>
                    {v.scenario_years.sort((a, b) => a.id - b.id).map((e) => <span> <span> {e.name} </span> <span>  <b className="separator-dot"> . </b> </span> </span>)}
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
                              <a href="https://openenergy-platform.org/ontology/oeo/OEO_00020032">More info from Open Energy Ontology (OEO)...</a>
                            </Typography>
                          </React.Fragment>
                        }
                      >
                        <InfoOutlinedIcon sx={{ color: '#708696' }} />
                      </HtmlTooltip>
                    </div>
                  </FirstRowTableCell>
                  <ContentTableCell>
                    {v.regions.map((e) => <span> <span> {e.name} </span> <span> <b className="separator-dot"> . </b> </span> </span>)}
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
                              <a href="https://openenergy-platform.org/ontology/oeo/OEO_00020036">More info from Open Energy Ontology (OEO)...</a>
                            </Typography>
                          </React.Fragment>
                        }
                      >
                        <InfoOutlinedIcon sx={{ color: '#708696' }} />
                      </HtmlTooltip>
                    </div>
                  </FirstRowTableCell>
                  <ContentTableCell>
                    {v.interacting_regions.map((e) => <span> <span> {e.name} </span> <span> <b className="separator-dot"> . </b> </span> </span>)}
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
                              {'Exogenous data is a data item whose quantity value is determined outside of a model and is imposed on a model.'}
                              <br />
                              <a href="https://openenergy-platform.org/ontology/oeo/OEO_00030029">More info from Open Energy Ontology (OEO)...</a>
                            </Typography>
                          </React.Fragment>
                        }
                      >
                        <InfoOutlinedIcon sx={{ color: '#708696' }} />
                      </HtmlTooltip>
                    </div>
                  </FirstRowTableCell>
                  <ContentTableCell>
                    {v.input_datasets.map((e) => <span> <span> <Chip label={e.value.label} size="small" variant="outlined" onClick={() => handleOpenURL(e.value.url)} /> </span> <span>  <b className="separator-dot">  </b> </span> </span>)}
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
                              {'Output data is endogenous data that is determined by a model calculation and presented as a result.'}
                              <br />
                              <a href="https://openenergy-platform.org/ontology/oeo/OEO_00020013">More info from Open Energy Ontology (OEO)...</a>
                            </Typography>
                          </React.Fragment>
                        }
                      >
                        <InfoOutlinedIcon sx={{ color: '#708696' }} />
                      </HtmlTooltip>
                    </div>
                  </FirstRowTableCell>
                  <ContentTableCell>
                    {v.output_datasets.map((e) => <span> <span>  <Chip sx={{ marginTop: "5px" }} label={e.value.label} size="small" variant="outlined" onClick={() => handleOpenURL(e.value.url)} /> </span> <span>  <b className="separator-dot">  </b> </span> </span>)}
                  </ContentTableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </React.Fragment>
      ) : null
    )}
  </Container>
);


  const renderPublicationOverview = () => (
    <Container maxWidth="lg2" sx={{ padding: '0px !important' }}>
      {
        publications.map((v, i) =>
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
                        <InfoOutlinedIcon sx={{ color: '#708696' }} />
                      </HtmlTooltip>
                    </div>
                  </FirstRowTableCell>
                  <ContentTableCell>
                    {v.report_title !== undefined ? v.report_title : ""}
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
                              <a href="https://openenergy-platform.org/ontology/oeo/OEO_00000064">More info...</a>
                            </Typography>
                          </React.Fragment>
                        }
                      >
                        <InfoOutlinedIcon sx={{ color: '#708696' }} />
                      </HtmlTooltip>
                    </div>
                  </FirstRowTableCell>
                  <ContentTableCell>
                    {v.authors.map((a, i) => (
                      <span> <span> {a.name} </span> <span>   <b className="separator-dot"> . </b> </span> </span>
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
                              <a href="https://openenergy-platform.org/ontology/oeo/OEO_00000133">More info...</a>
                            </Typography>
                          </React.Fragment>
                        }
                      >
                        <InfoOutlinedIcon sx={{ color: '#708696' }} />
                      </HtmlTooltip>
                    </div>
                  </FirstRowTableCell>
                  <ContentTableCell>
                    <span> <span> {v.doi !== undefined ? v.doi : ''} </span> <span>   <b style={{ fontSize: '24px' }}></b> </span> </span>
                  </ContentTableCell>
                </TableRow>

                <TableRow>
                  <FirstRowTableCell>
                    <div>
                      <span>Year of publication</span>
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
                    <span> <span> {v.date_of_publication.split('/')[0]} </span> <span>   <b style={{ fontSize: '24px' }}></b> </span> </span>
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
                            <a href="https://openenergy-platform.org/ontology/oeo/OEO_00020011">More info from Open Enrgy Ontology (OEO)...</a>
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
                    <span> <span>
                      <a href={v.link_to_study_report} >
                        <AttachmentIcon fontSize="large" />
                      </a>
                    </span> <span>   <b style={{ fontSize: '24px' }}></b> </span> </span>
                  </ContentTableCell>
                </TableRow>
                {/* <TableRow>
                <FirstRowTableCell>
                  <div>
                    <span>Citation</span>
                    <HtmlTooltip
                      title={
                      <React.Fragment>
                        <Typography color="inherit" variant="subtitle1">
                        {'A citation reference is a reference stating where a citation was taken from.'}
                        <br />
                        <a href="https://openenergy-platform.org/ontology/oeo/OEO_00000085">More info...</a>
                      </Typography>
                    </React.Fragment>
                    }
                    >
                      <InfoOutlinedIcon sx={{ color: '#708696' }} />
                    </HtmlTooltip>
                  </div>
                </FirstRowTableCell>
                <ContentTableCell>
                  <span> <span> {date_of_publication} </span> <span>   <b style={{ fontSize: '24px' }}></b> </span> </span>
                </ContentTableCell>
              </TableRow> */}
              </TableBody>
            </Table>
          </TableContainer >
        )
      }
    </Container >
  )

  const renderSectorsAndTechnology = () => (
    <TableContainer>
      <Table>
        <TableBody>
          <TableRow>
            <FirstRowTableCell>
              <div>
                <span>Sector divisions</span>
                <HtmlTooltip
                  title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'A sector division is a specific way to subdivide a system.'}
                        <br />
                        <a href="https://openenergy-platform.org/ontology/oeo/OEO_00000368">More info...</a>
                      </Typography>
                    </React.Fragment>
                  }
                >
                  <InfoOutlinedIcon sx={{ color: '#708696' }} />
                </HtmlTooltip>
              </div>
            </FirstRowTableCell>
            <ContentTableCell>
              {selectedSectorDivisions.map((v, i) => (
                <span> <span> <Chip label={v.name} size="small" variant="outlined" onClick={() => handleOpenURL(v.class)} /> </span> <span>   <b className="separator-dot">  </b></span> </span>
              ))}
            </ContentTableCell>
          </TableRow>
          <TableRow>
            <FirstRowTableCell>
              <div>
                <span>Sectors</span>
                <HtmlTooltip
                  title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'A sector is generically dependent continuant that is a subdivision of a system.'}
                        <br />
                        <a href="https://openenergy-platform.org/ontology/oeo/OEO_00000367">More info...</a>
                      </Typography>
                    </React.Fragment>
                  }
                >
                  <InfoOutlinedIcon sx={{ color: '#708696' }} />
                </HtmlTooltip>
              </div>
            </FirstRowTableCell>
            <ContentTableCell>
              {selectedSectors.map((v, i) => (
                <span> <span> <Chip label={v.label} size="small" variant="outlined" onClick={() => handleOpenURL(v.class)} /> </span> <span>   <b className="separator-dot">  </b></span> </span>
              ))}
            </ContentTableCell>
          </TableRow>
          <TableRow>
            <FirstRowTableCell>
              <div>
                <span>Technologies</span>
                <HtmlTooltip
                  title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'A technology is a plan specification that describes how to combine artificial objects or other material entities and processes in a specific way.'}
                        <br />
                        <a href="https://openenergy-platform.org/ontology/oeo/OEO_00000407">More info...</a>
                      </Typography>
                    </React.Fragment>
                  }
                >
                  <InfoOutlinedIcon sx={{ color: '#708696' }} />
                </HtmlTooltip>
              </div>
            </FirstRowTableCell>
            <ContentTableCell>
             {/*  {selectedTechnologies.map((v, i) => (
                <span> <span> <Chip label={v.value} size="small" variant="outlined" onClick={() => handleOpenURL(v.class)} /> </span> <span>   <b className="separator-dot">  </b></span> </span>
              ))} */}
              <RichTreeView items={selectedTechnologiesTree} expandedItems={allNodeIds} />
            </ContentTableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )

  const renderModelsAndFrameworksOverview = () => (
    <TableContainer>
      <Table>
        <TableBody>
          <TableRow>
            <FirstRowTableCell>
              <div>
                <span>Models</span>
                <HtmlTooltip
                  title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'A model is a generically dependent continuant that is used for computing an idealised reproduction of a system and its behaviours.'}
                        <br />
                        <a href="https://openenergy-platform.org/ontology/oeo/OEO_00000274">More info...</a>
                      </Typography>
                    </React.Fragment>
                  }
                >
                  <InfoOutlinedIcon sx={{ color: '#708696' }} />
                </HtmlTooltip>
              </div>
            </FirstRowTableCell>
            <ContentTableCell>
              {selectedModels.map((v) => (
                <><Chip
                  size='small'
                  key={v.id}
                  label={v.acronym ? v.acronym : v.name}
                  variant="outlined"
                  sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px' }} onClick={() => handleOpenURL(v.url)} /><b className="separator-dot"> . </b></>
                ))
              }

            </ContentTableCell>
          </TableRow>
          <TableRow>
            <FirstRowTableCell>
              <div>
                <span>Frameworks</span>
                <HtmlTooltip
                  title={
                    <React.Fragment>
                      <Typography color="inherit" variant="subtitle1">
                        {'A software framework is a Software that is generic and can be adapted to a specific application.'}
                        <br />
                        <a href="https://openenergy-platform.org/ontology/oeo/OEO_00000382">More info...</a>
                      </Typography>
                    </React.Fragment>
                  }
                >
                  <InfoOutlinedIcon sx={{ color: '#708696' }} />
                </HtmlTooltip>
              </div>
            </FirstRowTableCell>
            <ContentTableCell>
              {selectedFrameworks.map((v) => (
                  <><Chip
                    size='small'
                    key={v.id}
                    label={v.acronym ? v.acronym : v.name}
                    variant="outlined"
                    sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px' }} onClick={() => handleOpenURL(v.url)} /><b className="separator-dot"> . </b></>
                  ))
                }
            </ContentTableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
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

  return (
    <div>
      <Grid container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
      >
        <BreadcrumbsNavGrid acronym={acronym} id={id} mode={mode} />
        <Container maxWidth="lg2">
          <Grid item xs={12}>
            <Backdrop
              sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
              open={openBackDrop}
              onClick={handleCloseBackDrop}
            >
              <CircularProgress color="inherit" />
            </Backdrop>
          </Grid>
          <Toolbar sx={{ marginBottom: theme => theme.spacing(4) }}>

            <Grid item xs={12}>
              <Grid container
                direction="row"
                justifyContent="space-between"
                alignItems="center"
              >
                <ColorToggleButton handleSwap={handleSwap} />
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
                    <Button disableElevation={true} size="small" sx={{ mr: 1 }} variant="contained" color="primary" onClick={handleSaveFactsheet} startIcon={<SaveIcon />}> Save </Button>
                  </Tooltip>}
                  <Tooltip title="Share this factsheet">
                    <Button disableElevation={true} size="small" sx={{ mr: 1 }} variant="outlined" color="primary" startIcon={<ShareIcon />} disabled> Share </Button>
                  </Tooltip>
                  <Tooltip title="Delete factsheet">
                    <Button disableElevation={true} size="small" variant="outlined" color="primary" onClick={handleClickOpenRemovedDialog} startIcon={<DeleteOutlineIcon />}> Delete </Button>
                  </Tooltip>
                </div >
              </Grid>
            </Grid>
          </Toolbar>

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
              open={notTheOwner}
              autoHideDuration={600}
            >
              <Alert variant="filled" severity="error" sx={{ width: '100%' }}>
                <AlertTitle>Access denied!</AlertTitle>
                You cannot edit scenario bundles that you do not own!
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
                <b>Removed!</b>
              </DialogTitle>
              <DialogContent>
                <DialogContentText>
                  <div>
                    <pre>
                      The item is now removed from your bundle!
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
                <Link to={`scenario-bundles/main`} onClick={() => {
                  axios.post(conf.toep + 'scenario-bundles/delete/', null, { params: { id: id }, headers: { 'X-CSRFToken': CSRFToken() } }).then(response => setOpenRemovedDialog(true));
                  this.reloadRoute();
                }} className="btn btn-primary" style={{ textDecoration: 'none', color: 'blue', marginRight: '10px' }}>
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
                <Grid container style={{ marginTop: '10px' }}>
                  <Grid item xs={12} style={{ 'overflow': 'auto' }}>
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
              <>
                <Grid container justifyContent="space-between"
                  alignItems="start"
                  spacing={2}>
                  <Grid item xs={12}  >
                    <b style={{ fontSize: variables.fontSize.lg }}>{studyName !== undefined && studyName}</b>
                  </Grid>
                </Grid>
                <Typography variant='small'>
                  <Grid container sx={{ padding: '1rem 0 2rem' }}>
                    <InfoListItem>
                      <Grid item xs={3} >
                        <span>Acronym</span>
                        <span >
                          <HtmlTooltip
                            title={
                              <React.Fragment>
                                <Typography color="inherit" variant="subtitle1">
                                  {'An acronym is an abbreviation of the title by using the first letters of each part of the title.'}
                                  <br />
                                  <a href="https://openenergy-platform.org/ontology/oeo/OEO_00000048">More info...</a>
                                </Typography>
                              </React.Fragment>
                            }
                          >
                            <InfoOutlinedIcon sx={{ color: '#708696' }} />
                          </HtmlTooltip>
                        </span>
                      </Grid>
                      <Grid item xs={9} >
                        {acronym}
                      </Grid>
                    </InfoListItem>
                    <InfoListItem>
                      <Grid item xs={3} >
                        <span>Contact person(s)</span>
                        <span >
                          <HtmlTooltip
                            title={
                              <React.Fragment>
                                <Typography color="inherit" variant="subtitle1">
                                  {'A contact person is an agent that can be contacted for help or information about a specific service or good.'}
                                  <br />
                                  <a href="https://openenergy-platform.org/ontology/oeo/OEO_00000107">More info...</a>
                                </Typography>
                              </React.Fragment>
                            }
                          >
                            <InfoOutlinedIcon sx={{ color: '#708696' }} />
                          </HtmlTooltip>
                        </span>
                      </Grid>
                      <Grid item xs={9} style={{ paddingTop: '10px' }}>
                        {selectedContactPerson.map((v, i) => (
                          <span> <span> {v.name} </span> <span>  <b className="separator-dot"> . </b> </span> </span>
                        ))}
                      </Grid>
                    </InfoListItem>
                    <InfoListItem>
                      <Grid item xs={3} >
                        <span>Institutions</span>
                        <span >
                          <HtmlTooltip
                            title={
                              <React.Fragment>
                                <Typography color="inherit" variant="subtitle1">
                                  {'An institution is an organisation that serves a social purpose.'}
                                  <br />
                                  <a href="https://openenergy-platform.org/ontology/oeo/OEO_00000238">More info...</a>
                                </Typography>
                              </React.Fragment>
                            }
                          >
                            <InfoOutlinedIcon sx={{ color: '#708696' }} />
                          </HtmlTooltip>
                        </span>
                      </Grid>
                      <Grid item xs={9} style={{ paddingTop: '10px' }}>
                        {selectedInstitution.map((v, i) => (
                          <span> <span> {v.name} </span> <span>   <b className="separator-dot"> . </b> </span> </span>
                        ))}
                      </Grid>
                    </InfoListItem>
                    <InfoListItem>
                      <Grid item xs={3} >
                        <span>Funding sources</span>
                        <span >
                          {/* <HtmlTooltip
                        title={
                        <React.Fragment>
                          <Typography color="inherit" variant="subtitle1">
                            {'A study is a project with the goal to investigate something.'}
                            <br />
                            <a href="https://openenergy-platform.org/ontology/oeo/OEO_00020011">More info from Open Enrgy Ontology (OEO)...</a>
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
                    </InfoListItem>
                    <InfoListItem>
                      <Grid item xs={3} >
                        <span>Descriptors</span>
                        <span >
                          {/* <HtmlTooltip
                        title={
                        <React.Fragment>
                          <Typography color="inherit" variant="subtitle1">
                            {'A study is a project with the goal to investigate something.'}
                            <br />
                            <a href="https://openenergy-platform.org/ontology/oeo/OEO_00020011">More info from Open Enrgy Ontology (OEO)...</a>
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
                          <span> <span> <Chip label={v} size="small" variant={StudyKeywords.filter((i) => i[0] == v)[0][1] === "" ? "" : "outlined"} onClick={() => handleOpenURL(StudyKeywords.filter((i) => i[0] == v)[0][1])} /> </span> <span>   <b className="separator-dot">  </b></span> </span>
                        ))}
                      </Grid>
                    </InfoListItem>
                    <InfoListItem>
                      <Grid item xs={3} >
                        <span>Abstract</span>
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
                            <InfoOutlinedIcon sx={{ color: '#708696' }} />
                          </HtmlTooltip>
                        </span>
                      </Grid>
                      <Grid item xs={9} style={{ paddingTop: '10px' }}>
                        <div>{abstract !== undefined && abstract}</div>
                      </Grid>
                    </InfoListItem>
                  </Grid>
                </Typography>
                <Grid container>
                  <Grid item xs={12} >
                    <CustomTabs
                      items={overview_items}
                    />
                  </Grid>
                </Grid>
              </>
            }
          </Grid>
        </Container>
      </Grid>
    </div>
  );
}


export default Factsheet;
