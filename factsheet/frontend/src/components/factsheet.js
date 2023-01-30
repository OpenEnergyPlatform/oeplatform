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

import CustomTreeViewWithCheckBox from './customTreeViewWithCheckbox.js'
import Snackbar, { SnackbarOrigin } from '@mui/material/Snackbar';
import ErrorIcon from '@mui/icons-material/Error';
import Typography from '@mui/material/Typography';
import AddBoxOutlinedIcon from '@mui/icons-material/AddBoxOutlined';
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
import Fab from '@mui/material/Fab';
import AddIcon from '@mui/icons-material/Add';

import Checkbox from '@mui/material/Checkbox';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import { useRef } from "react";
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

  const [selectedSectors, setSelectedSectors] = useState(id !== 'new' ? fsData.sectors : []);
  const [expandedSectors, setExpandedSectors] = useState(id !== 'new' ? fsData.expanded_sectors : []);

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

  const [sectors, setSectors] = useState([
    { id: 1, value : 'CRF sector (IPCC 2006): agricultural soils', label : wrapInTooltip('CRF sector (IPCC 2006): agricultural soils', 'description', 'link'), sector_divisions_id: 2 },
    { id: 2, value : 'CRF sector (IPCC 2006): agriculture', label : wrapInTooltip('CRF sector (IPCC 2006): agriculture', 'description', 'link'),  sector_divisions_id: 2 },
    { id: 3, value : 'CRF sector (IPCC 2006): agriculture - other', label : wrapInTooltip('CRF sector (IPCC 2006): agriculture - other', 'description', 'link'), sector_divisions_id: 2 },
    { id: 4, value : 'CRF sector (IPCC 2006): agriculture, forestry and fishing', label : wrapInTooltip('CRF sector (IPCC 2006): agriculture, forestry and fishing', 'description', 'link'), sector_divisions_id: 2 },
    { id: 5, value : 'CRF sector (IPCC 2006): biological treatment of solid waste', label : wrapInTooltip('CRF sector (IPCC 2006): biological treatment of solid waste', 'description', 'link'), sector_divisions_id: 2 },
    { id: 6, value : 'CRF sector (IPCC 2006): cement production', label : wrapInTooltip('CRF sector (IPCC 2006): cement production', 'description', 'link'), sector_divisions_id: 2 },
    { id: 7, value : 'CRF sector (IPCC 2006): chemical industry', label : wrapInTooltip('CRF sector (IPCC 2006): chemical industry', 'description', 'link'), sector_divisions_id: 2 },
    { id: 8, value : 'CRF sector (IPCC 2006): enteric fermentation', label : wrapInTooltip('CRF sector (IPCC 2006): enteric fermentation', 'description', 'link'), sector_divisions_id: 2 },
    { id: 9, value : 'CRF sector (IPCC 2006): field burning of agricultural residues', label : wrapInTooltip('CRF sector (IPCC 2006): field burning of agricultural residues', 'description', 'link'), sector_divisions_id: 2 },
    { id: 10, value : 'CRF sector (IPCC 2006): forest land', label : wrapInTooltip('CRF sector (IPCC 2006): forest land', 'description', 'link'), sector_divisions_id: 2 },
    { id: 11, value : 'CRF sector (IPCC 2006): fuel combustion', label : wrapInTooltip('CRF sector (IPCC 2006): fuel combustion', 'description', 'link'), sector_divisions_id: 2 },
    { id: 12, value : 'CRF sector (IPCC 2006): fuel combustion - other', label : wrapInTooltip('CRF sector (IPCC 2006): fuel combustion - other', 'description', 'link'), sector_divisions_id: 2 },
    { id: 13, value : 'CRF sector (IPCC 2006): fuel combustion - other sectors', label : wrapInTooltip('CRF sector (IPCC 2006): fuel combustion - other sectors', 'description', 'link'), sector_divisions_id: 2 },
    { id: 14, value : 'CRF sector (IPCC 2006): fugitive emissions from fuels', label : wrapInTooltip('CRF sector (IPCC 2006): fugitive emissions from fuels', 'description', 'link'), sector_divisions_id: 2 },
    { id: 15, value : 'CRF sector (IPCC 2006): grassland', label : wrapInTooltip('CRF sector (IPCC 2006): grassland', 'description', 'link'), sector_divisions_id: 2 },
    { id: 16, value : 'CRF sector (IPCC 2006): harvested wood products', label : wrapInTooltip('CRF sector (IPCC 2006): harvested wood products', 'description', 'link'), sector_divisions_id: 2 },
    { id: 17, value : 'CRF sector (IPCC 2006): incineration and open burning of waste', label : wrapInTooltip('CRF sector (IPCC 2006): incineration and open burning of waste', 'description', 'link'), sector_divisions_id: 2 },
    { id: 18, value : 'CRF sector (IPCC 2006): indirect CO2', label : wrapInTooltip('CRF sector (IPCC 2006): indirect CO2', 'description', 'link'), sector_divisions_id: 2 },
    { id: 19, value : 'CRF sector (IPCC 2006): industrial processes and product use', label : wrapInTooltip('CRF sector (IPCC 2006): industrial processes and product use', 'description', 'link'), sector_divisions_id: 2 },
    { id: 20, value : 'CRF sector (IPCC 2006): industrial processes and product use - other', label : wrapInTooltip('CRF sector (IPCC 2006): industrial processes and product use - other', 'description', 'link'), sector_divisions_id: 2 },
    { id: 21, value : 'CRF sector (IPCC 2006): international aviation', label : wrapInTooltip('CRF sector (IPCC 2006): international aviation', 'description', 'link'), sector_divisions_id: 2 },
    { id: 22, value : 'CRF sector (IPCC 2006): international bunkers', label : wrapInTooltip('CRF sector (IPCC 2006): international bunkers', 'description', 'link'), sector_divisions_id: 2 },
    { id: 23, value : 'CRF sector (IPCC 2006): international bunkers and multilateral operations', label : wrapInTooltip('CRF sector (IPCC 2006): international bunkers and multilateral operations', 'description', 'link'), sector_divisions_id: 2 },
    { id: 24, value : 'CRF sector (IPCC 2006): iron and steel production', label : wrapInTooltip('CRF sector (IPCC 2006): iron and steel production', 'description', 'link'), sector_divisions_id: 2 },
    { id: 25, value : 'CRF sector (IPCC 2006): land use, land-use change and forestry', label : wrapInTooltip('CRF sector (IPCC 2006): land use, land-use change and forestry', 'description', 'link'), sector_divisions_id: 2 },
    { id: 26, value : 'CRF sector (IPCC 2006): land use, land-use change and forestry - other', label : wrapInTooltip('CRF sector (IPCC 2006): land use, land-use change and forestry - other', 'description', 'link'), sector_divisions_id: 2 },
    { id: 27, value : 'CRF sector (IPCC 2006): liming', label : wrapInTooltip('CRF sector (IPCC 2006): liming', 'description', 'link'), sector_divisions_id: 2 },
    { id: 28, value : 'CRF sector (IPCC 2006): manufacture of solid fuels and other energy industries', label : wrapInTooltip('CRF sector (IPCC 2006): manufacture of solid fuels and other energy industries', 'description', 'link'), sector_divisions_id: 2 },
    { id: 29, value : 'CRF sector (IPCC 2006): manufacturing industries and construction', label : wrapInTooltip('CRF sector (IPCC 2006): manufacturing industries and construction', 'description', 'link'), sector_divisions_id: 2 },
    { id: 30, value : 'CRF sector (IPCC 2006): manure management', label : wrapInTooltip('CRF sector (IPCC 2006): manure management', 'description', 'link'), sector_divisions_id: 2 },
    { id: 31, value : 'CRF sector (IPCC 2006): maritime navigation', label : wrapInTooltip('CRF sector (IPCC 2006): maritime navigation', 'description', 'link'), sector_divisions_id: 2 },
    { id: 32, value : 'CRF sector (IPCC 2006): metal industry', label : wrapInTooltip('CRF sector (IPCC 2006): metal industry', 'description', 'link'), sector_divisions_id: 2 },
    { id: 33, value : 'CRF sector (IPCC 2006): mineral industry', label : wrapInTooltip('CRF sector (IPCC 2006): mineral industry', 'description', 'link'), sector_divisions_id: 2 },
    { id: 34, value : 'CRF sector (IPCC 2006): multilateral operations', label : wrapInTooltip('CRF sector (IPCC 2006): multilateral operations', 'description', 'link'), sector_divisions_id: 2 },
    { id: 35, value : 'CRF sector (IPCC 2006): non-energy products from fuels and solvent use', label : wrapInTooltip('CRF sector (IPCC 2006): non-energy products from fuels and solvent use', 'description', 'link'), sector_divisions_id: 2 },
    { id: 36, value : 'CRF sector (IPCC 2006): CO2 captured', label: wrapInTooltip('CRF sector (IPCC 2006): CO2 captured', 'description', 'link'), sector_divisions_id: 2 },
    { id: 37, value : 'CRF sector (IPCC 2006): CO2 emissions from biomass', label: wrapInTooltip('CRF sector (IPCC 2006): CO2 emissions from biomass', 'description', 'link'), sector_divisions_id: 2 },
    { id: 38, value : 'CRF sector (IPCC 2006): CO2 transport and storage', label: wrapInTooltip('CRF sector (IPCC 2006): CO2 transport and storage', 'description', 'link'), sector_divisions_id: 2 },
    { id: 39, value : 'CRF sector (IPCC 2006): commercial and institutional', label:wrapInTooltip('CRF sector (IPCC 2006): commercial and institutional', 'description', 'link') , sector_divisions_id: 2 },
    { id: 40, value : 'CRF sector (IPCC 2006): cropland', label: wrapInTooltip('CRF sector (IPCC 2006): cropland', 'description', 'link') , sector_divisions_id: 2 },
    { id: 41, value : 'CRF sector (IPCC 2006): domestic aviation', label: wrapInTooltip('CRF sector (IPCC 2006): domestic aviation', 'description', 'link') , sector_divisions_id: 2 },
    { id: 42, value : 'CRF sector (IPCC 2006): domestic navigation', label: wrapInTooltip('CRF sector (IPCC 2006): domestic navigation', 'description', 'link'), sector_divisions_id: 2 },
    { id: 43, value : 'CRF sector (IPCC 2006): electronics industry', label: wrapInTooltip('CRF sector (IPCC 2006): electronics industry', 'description', 'link') , sector_divisions_id: 2 },
    { id: 44, value : 'CRF sector (IPCC 2006): energy', label: wrapInTooltip('CRF sector (IPCC 2006): energy', 'description', 'link'), sector_divisions_id: 2 },
    { id: 45, value : 'CRF sector (IPCC 2006): energy industry', label: wrapInTooltip('CRF sector (IPCC 2006): energy industry', 'description', 'link'), sector_divisions_id: 2 },
    { id: 46, value : 'agriculture, forestry and land use sector', label: wrapInTooltip('Agriculture, forestry and land use sector', 'description', 'link'), sector_divisions_id: 11 },
    { id: 47, value : 'energy demand sector', label: wrapInTooltip('Energy demand sector', 'description', 'link'), sector_divisions_id: 11,
      children: [
          { id: 48, value : 'building sector', label: wrapInTooltip('Building sector', 'description', 'link') },
          { id: 49, value : 'commercial sector', label: wrapInTooltip('Commercial sector', 'description', 'link') },
          { id: 50, value : 'heating and cooling sector', label: wrapInTooltip('Heating and cooling sector', 'description', 'link') },
          { id: 51, value : 'household sector', label: wrapInTooltip('Household sector', 'description', 'link') },
          { id: 52, value : 'transport sector', label: wrapInTooltip('Transport sector', 'description', 'link') },
      ]
    },
    { id: 53, value : 'energy transformation sector', label: wrapInTooltip('Energy transformation sector', 'description', 'link'), sector_divisions_id: 11,
      children: [
          { id: 54, value : 'electricity sector', label: wrapInTooltip('Electricity sector', 'description', 'link') },
      ]
    },
    { id: 55, value : 'industry sector', label: wrapInTooltip('Industry sector', 'description', 'link'), sector_divisions_id: 11 },
    { id: 56, value : 'EU emission sector: effort sharing', label: wrapInTooltip('EU emission sector: effort sharing', 'description', 'link'), sector_divisions_id: 3 },
    { id: 57, value : 'EU emission sector: ETS', label: wrapInTooltip('EU emission sector: ETS', 'description', 'link'), sector_divisions_id: 3 },
    { id: 58, value : 'EU emission sector: ETS aviation', label: wrapInTooltip('EU emission sector: ETS aviation', 'description', 'link'), sector_divisions_id: 3 },
    { id: 59, value : 'EU emission sector: ETS stationary', label: wrapInTooltip('EU emission sector: ETS stationary', 'description', 'link'), sector_divisions_id: 3 },
    { id: 60, value : 'EU emission sector: LULUCF', label: wrapInTooltip('EU emission sector: LULUCF', 'description', 'link'), sector_divisions_id: 3 },
    { id: 61, value : 'KSG sector agriculture', label: wrapInTooltip('KSG sector agriculture', 'description', 'link'), sector_divisions_id: 7 },
    { id: 62, value : 'KSG sector buildings', label: wrapInTooltip('KSG sector buildings', 'description', 'link'), sector_divisions_id: 7 },
    { id: 63, value : 'KSG sector energy industry', label: wrapInTooltip('KSG sector energy industry', 'description', 'link'), sector_divisions_id: 7 },
    { id: 64, value : 'KSG sector industry', label: wrapInTooltip('KSG sector industry', 'description', 'link'), sector_divisions_id: 7 },
    { id: 65, value : 'KSG sector land use, land-use change and forestry', label: wrapInTooltip('KSG sector land use, land-use change and forestry', 'description', 'link'), sector_divisions_id: 7 },
    { id: 66, value : 'KSG sector transport', label: wrapInTooltip('KSG sector transport', 'description', 'link'), sector_divisions_id: 7 },
    { id: 67, value : 'KSG sector waste management and other', label: wrapInTooltip('KSG sector waste management and other', 'description', 'link'), sector_divisions_id: 7 },
  ]);

  const [filteredSectors, setFilteredSectors] = useState(id !== 'new' ? sectors : []);

  const [selectedSectorDivisions, setSelectedSectorDivisions] = useState(id !== 'new' ? fsData.sector_divisions : []);

  const [selectedAuthors, setSelectedAuthors] = useState(id !== 'new' ? fsData.authors : []);
  const [selectedInstitution, setSelectedInstitution] = useState(id !== 'new' ? fsData.institution : []);
  const [selectedFundingSource, setSelectedFundingSource] = useState(id !== 'new' ? fsData.funding_source : []);
  const [selectedContactPerson, setselectedContactPerson] = useState(id !== 'new' ? fsData.contact_person : []);
  const [report_title, setReportTitle] = useState(id !== 'new' ? fsData.report_title : []);
  const [date_of_publication, setDateOfPublication] = useState(id !== 'new' ? fsData.date_of_publication : '2022-04-07');
  const [doi, setDOI] = useState(id !== 'new' ? fsData.doi : '');
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
  const [expandedEnergyCarriers, setExpandedEnergyCarriers] = useState(id !== 'new' ? fsData.expanded_energy_carriers : []);

  const [selectedEnergyTransformationProcesses, setSelectedEnergyTransformationProcesses] = useState(id !== 'new' ? fsData.energy_transformation_processes : []);
  const [expandedEnergyTransformationProcesses, setExpandedEnergyTransformationProcesses] = useState(id !== 'new' ? fsData.expanded_energy_transformation_processes : []);

  const [selectedStudyKewords, setSelectedStudyKewords] = useState(id !== 'new' ? fsData.study_keywords : []);
  const [selectedScenarioInputDatasetRegion, setSelectedScenarioInputDatasetRegion] = useState([]);
  const [selectedScenarioOutputDatasetRegion, setSelectedScenarioOutputDatasetRegion] = useState([]);

  const [selectedModels, setSelectedModels] = useState(id !== 'new' ? fsData.models : []);
  const [selectedFrameworks, setSelectedFrameworks] = useState(id !== 'new' ? fsData.frameworks : []);

  const [removeReport, setRemoveReport] = useState(false);
  const navigate = useNavigate();
  const handleSaveJSON = () => {
    //props.onChange(oekg);
    setOpenJSON(true);
  };

  const [scenarioTabValue, setScenarioTabValue] = React.useState(0);

  const sector_divisions = [
    { id: 1, name: 'CRF sectors (IPCC 1996)' },
    { id: 2, name: 'CRF sectors (IPCC 2006)' },
    { id: 3, name: 'EU emission sector division' },
    { id: 4, name: 'Eurostat energy balances' },
    { id: 5, name: 'German energy balances' },
    { id: 6, name: 'GovReg sector division' },
    { id: 7, name: 'KSG' },
    { id: 8, name: 'MMR' },
    { id: 9, name: 'Nace_ sectors' },
    { id: 10, name: 'Renewable_ energy_ directive_ sectors' },
    { id: 11, name: 'Other' },
  ];

  const [factsheetJSON, setFactsheetJSON] = useState({
    "@context": {
      "@base": "https://openenergy-platform.org/oekg/",
      "oeo": "https://openenergy-platform.org/ontology/oeo/",
      "foaf": "http://xmlns.com/foaf/0.1/",
      "dc": "http://purl.org/dc/elements/1.1/"
    },
    "@type": "oeo:OEO_00010250",
    "oeo:OEO_00000506": [],
    "oeo:OEO_00000505": [],
    "oeo:OEO_00000509": []
  });


  const handleScenarioTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setScenarioTabValue(newValue);
  }
  const handleSaveFactsheet = () => {
    factsheetObjectHandler('name', factsheetName);
    if (id === 'new') {
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
      setOpenSavedDialog(true)
    });

    } else {
      axios.post(conf.toep + 'factsheet/update/',
      {
        fsData: fsData,
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
        setOpenUpdatedDialog(true)
      });

    }
  };

  const handleRemoveFactsheet = () => {

    axios.post(conf.toep + 'factsheet/delete/', null, { params: { id: id } }).then(response => setOpenRemovedDialog(true));
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
    setOpenRemovedDialog(true);
  };

  const handleClickCloseRemovedDialog = () => {
    setOpenRemovedDialog(false);
  };

  const handleCloseTurtle = () => {
    setOpenTurtle(false);
  };

  const handleCloseOverView = () => {
    setOpenOverView(false);
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
    console.log(newScenarios);

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
      let newScenariosObject = scenariosObject;
      newScenariosObject[key] = obj
      setScenariosObject(newScenariosObject);
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



    const authors = [
      { id: 'Karen C. Wood',  name: 'Karen C. Wood' },
      { id: 'Russell K. Tookes',  name: 'Russell K. Tookes' },
      { id: 'Amy W. Fry',  name: 'Amy W. Fry' },
      { id: 'Christin Weiss',  name: 'Christin Weiss' },
      { id: 'Leonie Koch',  name: 'Leonie Koch' },
      { id: 'Peter Shuster',  name: 'Peter Shuster' },
      { id: 'Benjamin Greiner',  name: 'Benjamin Greiner' },
      { id: 'Mathias Schmid',  name: 'Mathias Schmid' },
      { id: 'Sarah Decker',  name: 'Sarah Decker' },
      { id: 'Anne Maurer',  name: 'Anne Maurer' },
      { id: 'Lucas Sanger',  name: 'Lucas Sanger' },
      { id: 'Dirk Fuerst',  name: 'Dirk Fuerst' },
      { id: 'Alexander Fisher',  name: 'Alexander Fisher' },
    ];

    const funding_source = [
      { id: 'Rainbow Records', name:'Rainbow Records' },
      { id: 'Steak and Ale', name:'Steak and Ale' },
      { id: 'Excella', name:'Excella' },
    ];

    const institution = [
      { id: 'Buena Vista Garden Maintenance', name: "Buena Vista Garden Maintenance"},
      { id: 'Magik Lamp', name: "Magik Lamp"},
      { id: 'Zephyr Investments', name: "Zephyr Investments"},
    ];

    const scenario_years = [
      { id: '2010', name: '2010'},
      { id: '2011', name: '2011'},
      { id: '2012', name: '2012'},
      { id: '2013', name: '2013'},
      { id: '2014', name: '2014'},
      { id: '2015', name: '2015'},
      { id: '2016', name: '2016'},
      { id: '2017', name: '2017'},
      { id: '2018', name: '2018'},
      { id: '2019', name: '2019'},
      { id: '2020', name: '2020'},
      { id: '2021', name: '2021'},
      { id: '2022', name: '2022'},
      { id: '2023', name: '2023'},
      { id: '2024', name: '2024'},
      { id: '2025', name: '2025'},
      { id: '2026', name: '2026'},
      { id: '2027', name: '2027'},
      { id: '2028', name: '2028'},
      { id: '2029', name: '2029'},
      { id: '2030', name: '2030'},
      { id: '2031', name: '2031'},
      { id: '2032', name: '2032'},
      { id: '2033', name: '2033'},
      { id: '2034', name: '2034'},
      { id: '2035', name: '2035'},
      { id: '2036', name: '2036'},
      { id: '2037', name: '2037'},
      { id: '2038', name: '2038'},
      { id: '2039', name: '2039'},
      { id: '2040', name: '2040'},
      { id: '2041', name: '2041'},
      { id: '2042', name: '2042'},
      { id: '2043', name: '2043'},
      { id: '2044', name: '2044'},
      { id: '2045', name: '2045'},
      { id: '2046', name: '2046'},
      { id: '2047', name: '2047'},
      { id: '2048', name: '2048'},
      { id: '2049', name: '2049'},
      { id: '2050', name: '2050'},
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
      { id: 'Karen C. Wood',  name: 'Karen C. Wood' },
      { id: 'Russell K. Tookes',  name: 'Russell K. Tookes' },
      { id: 'Amy W. Fry',  name: 'Amy W. Fry' },
      { id: 'Christin Weiss',  name: 'Christin Weiss' },
      { id: 'Leonie Koch',  name: 'Leonie Koch' },
      { id: 'Peter Shuster',  name: 'Peter Shuster' },
      { id: 'Benjamin Greiner',  name: 'Benjamin Greiner' },
      { id: 'Mathias Schmid',  name: 'Mathias Schmid' },
      { id: 'Sarah Decker',  name: 'Sarah Decker' },
      { id: 'Anne Maurer',  name: 'Anne Maurer' },
      { id: 'Lucas Sanger',  name: 'Lucas Sanger' },
      { id: 'Dirk Fuerst',  name: 'Dirk Fuerst' },
      { id: 'Alexander Fisher',  name: 'Alexander Fisher' },
    ];

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

    const energy_carriers = [
      {id: 1, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00000102',  name: 'compressed air'},
      {id: 2, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00000257',  name: 'liquid air'},
      {id: 3, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00140080',  name: 'final energy carrier'},
      {id: 4, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00000302',  name: 'nuclear fuel'},
      {id: 5, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00000071',  name: 'biodiesel'},
      {id: 6, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00000131',  name: 'fossil diesel fuel'},
      {id: 7, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00010226',  name: 'fossil industrial waste fuel'},
      {id: 8, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00000299',  name: 'fossil municipal waste fuel'},
      {id: 9, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00010015',  name: 'fossil hydrogen'},
      {id: 10, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00000077',  name: 'blast furnace gas'},
      {id: 11, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00000093',  name: 'coke oven gas'},
      {id: 12, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00000186',  name: 'gasworks gas'},
      {id: 13, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00000062',  name: 'associated gas'},
    ];

    const energy_transportation_process = [
      {id: 1, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00240009',  name: 'combined heat and power generation'},
      {id: 2, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00050001',  name: 'fuel-powered electricity generation'},
      {id: 3, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00010098',  name: 'marine current energy transformation'},
      {id: 4, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00010099',  name: 'marine tidal energy transformation'},
      {id: 5, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00010103',  name: 'marine wave energy transformation'},
      {id: 6, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00020048',  name: 'photovoltaic energy transformation'},
      {id: 7, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00010080',  name: 'solar-steam-electric process'},
      {id: 8, iri: 'http://openenergy-platform.org/ontology/oeo/OEO_00050020 ', name: 'steam-electric process'},
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

    const scenarioInputDatasetRegionHandler = (inputDatasetRegionList) => {
      setSelectedScenarioInputDatasetRegion(inputDatasetRegionList);
    };

    const scenarioOutputDatasetRegionHandler = (outputDatasetRegionList) => {
      setSelectedScenarioOutputDatasetRegion(outputDatasetRegionList);
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

    const energyCarrierData = [
      {
        value: 'air',
        label: 'Air',
        children: [
          {
            value: 'compressed air',
            label: 'Compressed air',
           },
          {
            value: 'liquid air',
            label: 'Liquid air',
           }
        ]
      },
      { value: 'final energy carrier',
        label: 'Final energy carrier'
      },
      { value: 'fissile material entity',
        label: 'Fissile material entity',
        children: [
          {
            value: 'nuclear fuel',
            label: 'Nuclear fuel',
            children: [
              { value: 'plutonium',
                label: 'Plutonium'
              },
              { value: 'thorium',
                label: 'Thorium'
              },
              { value: 'uranium',
                label: 'Uranium'
              }
            ]
           },
        ]
      },
      { value: 'fuel',
        label: 'Fuel',
        children: [
          { value: 'combustion fuel',
            label: 'Combustion fuel',
            children: [
              {
                value: 'diesel fuel',
                label: 'Diesel fuel',
                children: [
                  { value: 'biodiesel',
                    label: 'Biodiesel'
                  },
                  { value: 'fossil diesel fuel',
                    label: 'Fossil diesel fuel'
                  }
                ]
               },
               { value: 'fossil combustion fuel',
                 label: 'Fossil combustion fuel',
                 children: [
                     { value: 'fossil waste fuel',
                       label: 'Fossil waste fuel',
                       children: [
                           { value: 'fossil industrial waste fuel',
                             label: 'Fossil industrial waste fuel'
                           },
                           { value: 'fossil municipal waste fuel',
                             label: 'Fossil municipal waste fuel'
                           }
                       ]
                     },
                     { value: 'gaseous fossil fuel',
                       label: 'Gaseous fossil fuel',
                       children: [
                           { value: 'fossil hydrogen',
                             label: 'Fossil hydrogen'
                           },
                           { value: 'manufactured coal based gas',
                             label: 'Manufactured coal based gas',
                             children: [
                                 { value: 'blast furnace gas',
                                   label: 'Blast furnace gas'
                                 },
                                 { value: 'coke oven gas',
                                   label: 'Coke oven gas'
                                 },
                                 { value: 'gasworks gas',
                                   label: 'Gasworks gas'
                                 }
                             ]
                           },
                           { value: 'natural gas',
                             label: 'Natural gas',
                             children: [
                                 { value: 'associated gas',
                                   label: 'Associated gas'
                                 },
                                 { value: 'colliery gas',
                                   label: 'colliery gas'
                                 },
                                 { value: 'liquified natural gas',
                                   label: 'Liquified natural gas'
                                 },
                                 { value: 'non associated gas',
                                   label: 'Non associated gas'
                                 }
                             ]
                           }
                       ]
                     },
                     { value: 'liquid fossil fuel',
                       label: 'Liquid fossil fuel',
                       children: [
                           { value: 'crude oil',
                             label: 'Crude oil'
                           },
                           { value: 'gas diesel oil',
                             label: 'Gas diesel oil',
                             children: [
                                 { value: 'fossil diesel fuel 2',
                                   label: 'Fossil diesel fuel'
                                 },
                                 { value: 'heating oil',
                                   label: 'Heating oil'
                                 }
                             ]
                           },
                           { value: 'gasoline',
                             label: 'Gasoline',
                             children: [
                                 { value: 'aviation gasoline',
                                   label: 'Aviation gasoline'
                                 },
                                 { value: 'motor gasoline',
                                   label: 'Motor gasoline'
                                 }
                             ]
                           },
                           { value: 'kerosene',
                             label: 'Kerosene',
                             children: [
                                 { value: 'jet fuel',
                                   label: 'Jet fuel'
                                 },
                             ]
                           }
                       ]
                     },
                     { value: 'solid fossil fuel',
                       label: 'Solid fossil fuel',
                       children: [
                           { value: 'coal',
                             label: 'Coal',
                             children: [
                                 { value: 'hard coal',
                                   label: 'Hard coal',
                                   children: [
                                       { value: 'anthracite',
                                         label: 'Anthracite'
                                       },
                                       { value: 'coking coal',
                                         label: 'Coking coal'
                                       },
                                   ]
                                 },
                                 { value: 'lignite',
                                   label: 'Lignite'
                                 },
                                 { value: 'sub bituminous coal',
                                   label: 'Sub bituminous coal'
                                 },
                             ]
                           },
                           { value: 'peat',
                             label: 'Peat'
                           },
                       ]
                     },
                 ]
               },
               { value: 'gaseous combustion fuel',
                 label: 'Gaseous combustion fuel',
                 children: [
                     { value: 'ammonia',
                       label: 'Ammonia',
                       children: [
                           { value: 'synthetic ammonia',
                             label: 'Synthetic ammonia'
                           }
                       ]
                     },
                     { value: 'gaseous fossil fuel 2',
                       label: 'Gaseous fossil fuel',
                       children: [
                           { value: 'fossil hydrogen 2',
                             label: 'fossil hydrogen'
                           },
                           { value: 'manufactured coal based gas 2',
                             label: 'Manufactured coal based gas',
                             children: [
                                 { value: 'blast furnace gas 2',
                                   label: 'Blast furnace gas'
                                 },
                                 { value: 'coke oven gas 2',
                                   label: 'Coke oven gas'
                                 },
                                 { value: 'gasworks gas 2',
                                   label: 'Gasworks gas'
                                 }
                             ]
                           },
                           { value: 'natural gas natural gas',
                             label: 'Natural gas',
                             children: [
                                 { value: 'associated gas 2',
                                   label: 'Associated gas'
                                 },
                                 { value: 'colliery gas 2',
                                   label: 'Colliery gas'
                                 },
                                 { value: 'liquified natural gas 2',
                                   label: 'Liquified natural gas'
                                 },
                                 { value: 'non associated gas 2',
                                   label: 'Non associated gas'
                                 }
                             ]
                           },

                       ]
                     },
                     { value: 'gaseous renewable fuel',
                       label: 'Gaseous renewable fuel',
                       children: [
                           { value: 'gaseous biofuel',
                             label: 'Gaseous biofuel',
                             children: [
                                 { value: 'biogas',
                                   label: 'Biogas'
                                 },
                                 { value: 'biomethane',
                                   label: 'Biomethane'
                                 }
                             ]
                           }
                       ]
                     },
                     { value: 'gaseous synthetic fuel',
                       label: 'Gaseous synthetic fuel',
                       children: [
                           { value: 'synthetic ammonia 2',
                             label: 'Synthetic ammonia',
                           },
                           { value: 'synthetic hydrogen 2',
                             label: 'Synthetic hydrogen',
                           },
                           { value: 'synthetic methane 2',
                             label: 'Synthetic methane',
                           },
                       ]
                     },
                     { value: 'hydrogen',
                       label: 'Hydrogen',
                       children: [
                           { value: 'fossil hydrogen 3',
                             label: 'Fossil hydrogen',
                           },
                           { value: 'synthetic hydrogen',
                             label: 'Synthetic hydrogen',
                           },
                       ]
                     },
                     { value: 'methane',
                       label: 'Methane',
                       children: [
                           { value: 'synthetic methane 3',
                             label: 'Synthetic methane',
                           },
                       ]
                     },
                     { value: 'syngas',
                       label: 'Syngas',
                     },
                 ]
               },
               { value: 'gasoline fuel',
                 label: 'Gasoline fuel',
                 children: [
                   { value: 'biogasoline',
                     label: 'Biogasoline',
                   },
                   { value: 'gasoline 2',
                     label: 'Gasoline',
                     children: [
                         { value: 'aviation gasoline 4',
                           label: 'Aviation gasoline',
                         },
                         { value: 'motor gasoline 2',
                           label: 'Motor gasoline',
                         },
                     ]
                   },
                 ]
               },
               { value: 'hydrocarbon',
                 label: 'Hydrocarbon',
                 children: [
                     { value: 'methane ',
                       label: 'Methane',
                     },
                 ]
               },
               { value: 'liquid combustion fuel',
                 label: 'Liquid combustion fuel',
                 children: [
                     { value: 'ethanol',
                       label: 'Ethanol',
                     },
                     { value: 'liquid fossil fuel 2',
                       label: 'Liquid fossil fuel',
                       children: [
                           { value: 'crude oil 2',
                             label: 'Crude oil'
                           },
                           { value: 'gas diesel oil 3',
                             label: 'Gas diesel oil',
                             children: [
                                 { value: 'fossil diesel fuel 3',
                                   label: 'Fossil diesel fuel'
                                 },
                                 { value: 'heating oil 2',
                                   label: 'Heating oil'
                                 }
                             ]
                           },
                           { value: 'gasoline 3',
                             label: 'Gasoline',
                             children: [
                                 { value: 'aviation gasoline 3',
                                   label: 'Aviation gasoline'
                                 },
                                 { value: 'motor gasoline 3',
                                   label: 'Motor gasoline'
                                 }
                             ]
                           },
                           { value: 'kerosene 3',
                             label: 'Kerosene',
                             children: [
                                 { value: 'jet fuel 3',
                                   label: 'Jet fuel'
                                 },
                             ]
                           }
                       ]
                     },
                     { value: 'liquid renewable fuel',
                       label: 'Liquid renewable fuel',
                       children: [
                           { value: 'biofuel',
                             label: 'Biofuel',
                             children: [
                                 { value: 'biogenic waste fuel',
                                   label: 'Biogenic waste fuel',
                                   children: [
                                       { value: 'biogenic industrial waste fuel',
                                         label: 'Biogenic industrial waste fuel'
                                       },
                                       { value: 'biogenic municipal waste fuel',
                                         label: 'Biogenic municipal waste fuel'
                                       },
                                   ]
                                 },
                                 { value: 'gaseous biofuel 2',
                                   label: 'Gaseous biofuel',
                                   children: [
                                       { value: 'biogas 2',
                                         label: 'Biogas'
                                       },
                                       { value: 'biomethane 2',
                                         label: 'Biomethane'
                                       },
                                   ]
                                 },
                                 { value: 'liquid biofuel',
                                   label: 'Liquid biofuel',
                                   children: [
                                       { value: 'biodiesel 2',
                                         label: 'Biodiesel'
                                       },
                                       { value: 'biogasoline 2',
                                         label: 'Biogasoline'
                                       },
                                   ]
                                 },
                                 { value: 'solid biofuel',
                                   label: 'Solid biofuel',
                                   children: [
                                       { value: 'charcoal',
                                         label: 'Charcoal'
                                       },
                                       { value: 'wood',
                                         label: 'Wood'
                                       },
                                   ]
                                 },
                             ]
                           },
                           { value: 'gaseous renewable fuel 2',
                             label: 'Gaseous renewable fuel',
                             children: [
                                 { value: 'gaseous biofuel 3',
                                   label: 'Gaseous biofuel',
                                   children: [
                                       { value: 'biogas 3',
                                         label: 'Biogas'
                                       },
                                       { value: 'biomethane 3',
                                         label: 'Biomethane'
                                       },
                                   ]
                                 }
                             ]
                           },
                       ]
                     },
                     { value: 'liquid synthetic fuel',
                       label: 'Liquid synthetic fuel',

                     },
                 ]
               },
            ]
          },

        ]
      },
    ];

    const energyTransformationProcesses = [
      {
        value: 'electricity generation process',
        label: 'Electricity generation process',
        children: [
          {
            value: 'combined heat and power generation',
            label: 'Combined heat and power generation'
           },
          {
            value: 'fuel-powered electricity generation',
            label: 'fuel-powered electricity generation'
          },
          {
            value: 'hydroelectric energy transformation',
            label: 'Hydroelectric energy transformation',
            children: [
              {
                value: 'marine current energy transformation',
                label: 'Marine current energy transformation'
               },
              {
                value: 'marine tidal energy transformation',
                label: 'Marine tidal energy transformation'
              },
              {
                value: 'marine wave energy transformation',
                label: 'Marine wave energy transformation'
               }
            ]
          },
           {
             value: 'photovoltaic energy transformation',
             label: 'Photovoltaic energy transformation'
           },
           {
             value: 'solar-steam-electric process',
             label: 'Solar-steam-electric process'
           },
           {
             value: 'steam-electric process',
             label: 'Steam-electric process'
           },
           {
             value: 'wind energy transformation',
             label: 'Wind energy transformation'
           }
        ]
      },
      { value: 'energy transfer',
        label: 'Energy transfer',
        children: [
          {
            value: 'heat transfer',
            label: 'Heat transfer',
            children: [
              {
                value: 'ambient thermal energy transfer',
                label: 'Ambient thermal energy transfer'
              },
              {
                value: 'geothermal heat transfer',
                label: 'Geothermal heat transfer'
              },
              {
                value: 'grid-bound heating',
                label: 'Grid-bound heating',
                children: [
                  {
                    value: 'district heating',
                    label: 'District heating'
                  },
                  {
                    value: 'industrial grid-bound heating',
                    label: 'Industrial grid-bound heating'
                  }
                ]
              },
              {
                value: 'marine thermal energy transfer',
                label: 'Marine thermal energy transfer'
              }
            ]
          }
        ]
      },
      { value: 'heat generation process',
        label: 'Heat generation process',
        children: [
          { value: 'combined heat and power generation 2',
            label: 'Combined heat and power generation',
          },
          { value: 'combustion thermal energy transformation',
            label: 'Combustion thermal energy transformation',
          },
          { value: 'heat transfer 2',
            label: 'Heat transfer',
            children: [
              { value: 'ambient thermal energy transfer 2',
                label: 'Ambient thermal energy transfer',
              },
              { value: 'geothermal heat transfer 2',
                label: 'Geothermal heat transfer',
              },
              { value: 'grid-bound heating 2',
                label: 'Grid-bound heating',
                children: [
                  { value: 'district heating 2',
                    label: 'District heating',
                  },
                  { value: 'industrial grid-bound heating 2',
                    label: 'Industrial grid-bound heating',
                  }
                ]
              },
              { value: 'marine thermal energy transfer 2',
                label: 'Marine thermal energy transfer',
              },
            ]
          },
          { value: 'nuclear energy transformation',
            label: 'Nuclear energy transformation',
          },
          { value: 'solar thermal energy transformation',
            label: 'Solar thermal energy transformation',
          },
        ]
      },
      { value: 'hydro energy transformation 2',
        label: 'Hydro energy transformation',
        children: [
          { value: 'hydroelectric energy transformation 2',
            label: 'hydroelectric energy transformation',
            children: [
              { value: 'marine current energy transformation 2',
                label: 'Marine current energy transformation',
              },
              { value: 'marine tidal energy transformation 2',
                label: 'Marine tidal energy transformation',
              },
              { value: 'marine wave energy transformation 2',
                label: 'Marine wave energy transformation',
              },
            ]
          },
        ]
      },
      { value: 'power-to-gas process',
        label: 'Power-to-gas process',
        children: [
          { value: 'power-to-ammonia process',
            label: 'Power-to-ammonia process',
          },
          { value: 'power-to-methane process',
            label: 'Power-to-methane process',
          },
        ]
      },
      { value: 'solar energy transformation',
        label: 'Solar energy transformation',
        children: [
          { value: 'photovoltaic energy transformation 2',
            label: 'Photovoltaic energy transformation',
          },
          { value: 'solar chemical energy transformation',
            label: 'Solar chemical energy transformation',
          },
          { value: 'solar thermal energy transformation 2',
            label: 'Solar thermal energy transformation',
          },
          { value: 'Solar-steam-electric process',
            label: 'Solar-steam-electric process',
          },
        ]
      },
      { value: 'water electrolysis process',
        label: 'Water electrolysis process',
      },
    ];

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
            <CustomAutocomplete showSelectedElements={true} manyItems optionsSet={institution} kind='Which institutions are involved in this study?' handler={institutionHandler} selectedElements={selectedInstitution}/>
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
          <CustomAutocomplete showSelectedElements={true} manyItems optionsSet={funding_source} kind='What are the funding sources of this study?' handler={fundingSourceHandler} selectedElements={selectedFundingSource}/>
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
              <CustomAutocomplete showSelectedElements={true}  manyItems optionsSet={contact_person} kind='Who is the contact person for this factsheet?' handler={contactPersonHandler} selectedElements={selectedContactPerson}/>
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
                  <CustomAutocomplete showSelectedElements={false} manyItems optionsSet={sector_divisions} kind='Do you use a predefined sector division? ' handler={sectorDivisionsHandler} selectedElements={selectedSectorDivisions}/>
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
                        <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes("resilience")} onChange={handleStudyKeywords} label="resilience" name="resilience" />
                        <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes("life cycle analysis")} onChange={handleStudyKeywords} label="life cycle analysis" name="life cycle analysis" />
                        <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes("CO2 emissions")} onChange={handleStudyKeywords} label="CO2 emissions" name="CO2 emissions" />
                        <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes("Greenhouse gas emissions")} onChange={handleStudyKeywords} label="Greenhouse gas emissions" name="Greenhouse gas emissions" />
                        <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes("Reallabor")} onChange={handleStudyKeywords} label="Reallabor" name="Reallabor" />
                        <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes("100% renewables")} onChange={handleStudyKeywords} label="100% renewables" name="100% renewables" />
                        <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes("acceptance")} onChange={handleStudyKeywords} label="acceptance" name="acceptance" />
                        <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes("sufficiency")} onChange={handleStudyKeywords} label="sufficiency" name="sufficiency" />
                        <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes("(changes in) demand")} onChange={handleStudyKeywords} label="(changes in) demand" name="(changes in) demand" />
                        <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes("degree of electrifiaction")} onChange={handleStudyKeywords} label="degree of electrifiaction" name="degree of electrifiaction" />
                        <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes("regionalisation")} onChange={handleStudyKeywords} label="regionalisation" name="regionalisation" />
                        <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes("total gross electricity generation")} onChange={handleStudyKeywords} label="total gross electricity generation" name="total gross electricity generation" />
                        <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes("total net electricity generation")} onChange={handleStudyKeywords} label="total net electricity generation" name="total net electricity generation" />
                        <FormControlLabel control={<Checkbox color="default" />} checked={selectedStudyKewords.includes("peak electricity generation")} onChange={handleStudyKeywords} label="peak electricity generation" name="peak electricity generation"/>
                    </div>
                  </FormGroup>
                </div>
            </Grid>
            <Grid item xs={6} style={{ marginBottom: '10px' }}>
              <CustomTreeViewWithCheckBox size="205px" checked={selectedEnergyCarriers} expanded={expandedEnergyCarriers} handler={energyCarriersHandler} expandedHandler={expandedEnergyCarriersHandler} data={energyCarrierData} title={"What energy carriers are considered?"} toolTipInfo={['An energy carrier is a material entity that has an energy carrier disposition.', 'http://openenergy-platform.org/ontology/oeo/OEO_00020039']} />
              <CustomTreeViewWithCheckBox size="205px" checked={selectedEnergyTransformationProcesses} expanded={expandedEnergyTransformationProcesses} handler={energyTransformationProcessesHandler} expandedHandler={expandedEnergyTransformationProcessesHandler} data={energyTransformationProcesses} title={"Which energy transformation processes are considered?"}
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
    const convert2RDF = async () => {
      factsheetJSON["foaf:name"] = acronym;
      factsheetJSON["@id"] = acronym;
      factsheetJSON["dc:description"] = abstract;

      factsheetJSON["oeo:OEO_00000505"] = [];
      selectedSectors.map(sector => {
        factsheetJSON["oeo:OEO_00000505"].push({
          "@id": sector.replaceAll(" ", "_"),
        });
      });

      factsheetJSON["oeo:OEO_00000509"] = [];
      selectedAuthors.map(author => {
        factsheetJSON["oeo:OEO_00000509"].push({
          "@id": author.name.replaceAll(" ", "_"),
        });
      });

      const nquads = await jsonld.toRDF(factsheetJSON, {format: 'application/n-quads'});
      setFactsheetRDF(nquads);
      return(nquads);
    }

    useEffect(() => {
      convert2RDF().then((nquads) => setFactsheetRDF(nquads));
    }, []);

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
               <Tooltip title="Save factsheet">
               <Button disableElevation={true} style={{ 'textTransform': 'none', 'zIndex': '1000', height: '40px' }} variant="contained" color="success" onClick={handleSaveFactsheet} ><SaveIcon /> </Button>
               </Tooltip>
          </div >
          </Grid>
          <Grid item xs={4} >
          <div  style={{ 'textAlign': 'center', 'marginTop': '10px' }}>
            <Typography variant="h6" gutterBottom>
              {acronym}
            </Typography>
          </div>
          </Grid>
          <Grid item xs={4} >
            <div style={{ 'textAlign': 'right' }}>
              <Tooltip title="Delete factsheet">
                <Button disableElevation={true} style={{ 'textTransform': 'none', 'marginTop': '10px', 'marginRight': '5px', 'zIndex': '1000' }} variant="contained" color="error" onClick={handleClickOpenRemovedDialog}> <DeleteOutlineIcon /> </Button>
              </Tooltip>
              <Tooltip title="Share this factsheet">
                <Button disableElevation={true} style={{ 'textTransform': 'none', 'marginTop': '10px', 'marginRLeft': '5px', 'zIndex': '1000' }} variant="contained" color="secondary" > <ShareIcon /> </Button>
              </Tooltip>
              <Tooltip title="Submit this factsheet to the Open Energy Knowledge Graph">
                <Button disableElevation={true} style={{ 'textTransform': 'none', 'marginTop': '10px', 'marginLeft': '5px', 'marginRight': '10px','zIndex': '1000'  }} variant="contained" color="primary" onClick={handleClickOpenTurtle} > <ForwardToInboxIcon /> </Button>
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

            {mode === "wizard" &&
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
