// SPDX-FileCopyrightText: 2025 Adel Memariani <adel.memariani@ovgu.de>
// SPDX-FileCopyrightText: 2025 Adel Memariani <memarian@haskell2go.iks.cs.ovgu.de>
// SPDX-FileCopyrightText: 2025 Adel Memariani <memarian@winadms-mbp.speedport.ip>
// SPDX-FileCopyrightText: 2025 Adel Memariani <memariani.adel@gmail.com>
// SPDX-FileCopyrightText: 2025 Bryan Lancien <bryanlancien.ui@gmail.com>
// SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
//
// SPDX-License-Identifier: MIT

import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import Box from '@mui/material/Box';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import TableSortLabel from '@mui/material/TableSortLabel';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import Checkbox from '@mui/material/Checkbox';
import { visuallyHidden } from '@mui/utils';
import { styled } from '@mui/material/styles';
import { tableCellClasses } from '@mui/material/TableCell';
import Button from '@mui/material/Button';
import { Route, Routes, Link } from 'react-router-dom';
// import VisibilityIcon from '@mui/icons-material/Visibility';
// import ViewComfyAltIcon from '@mui/icons-material/ViewComfyAlt';
import FilterAltOutlinedIcon from '@mui/icons-material/FilterAltOutlined';
import ReplayIcon from '@mui/icons-material/Replay';
import Chip from '@mui/material/Chip';
// import ReadMoreIcon from '@mui/icons-material/ReadMore';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import CustomAutocompleteWithoutEdit from './customAutocompleteWithoutEdit';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import axios from 'axios';
import conf from "../conf.json";
import SelectAllIcon from '@mui/icons-material/SelectAll';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import AddIcon from '@mui/icons-material/Add';
import RuleIcon from '@mui/icons-material/Rule';
import HtmlTooltip from '../styles/oep-theme/components/tooltipStyles.js'
import Tooltip, { TooltipProps, tooltipClasses } from '@mui/material/Tooltip';
import Stack from '@mui/material/Stack';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DesktopDatePicker } from '@mui/x-date-pickers/DesktopDatePicker';
import TextField from '@mui/material/TextField';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Slider from '@mui/material/Slider';
import Backdrop from '@mui/material/Backdrop';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import Container from '@mui/material/Container';
import Grid from '@mui/material/Grid';
import ArrowCircleRightOutlinedIcon from '@mui/icons-material/ArrowCircleRightOutlined';
import FormatListBulletedOutlinedIcon from '@mui/icons-material/FormatListBulletedOutlined';
import ViewAgendaOutlinedIcon from '@mui/icons-material/ViewAgendaOutlined';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import BreadcrumbsNavGrid from '../styles/oep-theme/components/breadcrumbsNavigation.js';
import { CardItem, CardHeader, CardBody, CardRow } from '../styles/oep-theme/components/cardView.js';
import '../styles/App.css';
import variables from '../styles/oep-theme/variables.js';
import palette from '../styles/oep-theme/palette.js';
import CSRFToken from './csrfToken';
import StudyKeywords from './scenarioBundleUtilityComponents/StudyDescriptors.js';

const StyledTableCell = styled(TableCell)(({ theme }) => ({
  [`&.${tableCellClasses.head}`]: {
    backgroundColor: "#04678fa8",
    color: theme.palette.common.white,
    fontSize: 16,
    fontWeight: 600,
  },
  [`&.${tableCellClasses.body}`]: {
    fontSize: 14,
  },
}));

const StyledTableRow = styled(TableRow)(({ theme }) => ({

  '&:nth-of-type(odd)': {
    backgroundColor: theme.palette.action.hover,
    border: 0,
  },
  // hide last border
  '&:last-child td, &:last-child th': {
    border: 0,
  },
}));

function descendingComparator(a, b, orderBy) {
  if (b[orderBy] < a[orderBy]) {
    return -1;
  }
  if (b[orderBy] > a[orderBy]) {
    return 1;
  }
  return 0;
}

function getComparator(order, orderBy) {
  return order === 'desc'
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy);
}

function stableSort(array, comparator) {
  const stabilizedThis = array.map((el, index) => [el, index]);
  stabilizedThis.sort((a, b) => {
    const order = comparator(a[0], b[0]);
    if (order !== 0) {
      return order;
    }
    return a[1] - b[1];
  });
  return stabilizedThis.map((el) => el[0]);
}

const headCells = [
  {
    id: 'study name',
    numeric: false,
    disablePadding: true,
    label: 'Study name',
    align: 'left'
  },
  {
    id: 'acronym',
    numeric: true,
    disablePadding: false,
    label: 'Acronym',
    align: 'left'
  },
  {
    id: 'scenarios',
    numeric: true,
    disablePadding: false,
    label: 'Scenarios',
    align: 'left'
  },

  // {
  //   id: 'institutions',
  //   numeric: true,
  //   disablePadding: false,
  //   label: 'Institutions',
  //   align: 'left'
  // },
  // {
  //   id: 'date of publications',
  //   numeric: true,
  //   disablePadding: false,
  //   label: 'Date of publications',
  //   align: 'left'
  // },
  {
    id: 'Date of publication',
    numeric: true,
    disablePadding: false,
    label: 'Year of publication',
    align: 'left'
  },
  {
    id: 'More details',
    numeric: true,
    disablePadding: false,
    label: '',
    align: 'right'
  },
  // {
  //   id: 'more',
  //   numeric: false,
  //   disablePadding: true,
  //   label: '',
  //   align: 'left'
  // }
];

function EnhancedTableHead(props) {
  const { onSelectAllClick, order, orderBy, numSelected, rowCount, onRequestSort } =
    props;
  const createSortHandler = (property) => (event) => {
    onRequestSort(event, property);
  };


  return (
    <TableHead>
      <TableRow>
        {headCells.map((headCell) => (
          <StyledTableCell
            variant="light"
            key={headCell.id}
            align={headCell.align}
            padding={headCell.disablePadding ? 'none' : 'normal'}
            sortDirection={orderBy === headCell.id ? order : false}
            sx={{ paddingLeft: "20px" }}
          >
            <TableSortLabel
              active={orderBy === headCell.id}
              direction={orderBy === headCell.id ? order : 'asc'}
              onClick={createSortHandler(headCell.id)}
            >
              {headCell.label}
              {orderBy === headCell.id ? (
                <Box component="span" sx={visuallyHidden}>
                  {order === 'desc' ? 'sorted descending' : 'sorted ascending'}
                </Box>
              ) : null}
            </TableSortLabel>
          </StyledTableCell>
        ))}
      </TableRow>
    </TableHead>
  );
}

EnhancedTableHead.propTypes = {
  numSelected: PropTypes.number.isRequired,
  onRequestSort: PropTypes.func.isRequired,
  onSelectAllClick: PropTypes.func.isRequired,
  order: PropTypes.oneOf(['asc', 'desc']).isRequired,
  orderBy: PropTypes.string.isRequired,
  rowCount: PropTypes.number.isRequired,
};

function EnhancedTableToolbar(props) {
  const { numSelected, handleOpenQuery, handleShowAll, handleOpenAspectsOfComparison, handleChangeView, alignment, selected, logged_in } = props;
  const [isDisabled, setIsDisabled] = useState(true); 
  return (
    <div>
      <Grid
        container
        display="flex"
        flexDirection="row"
        justifyContent="center"
        sx={{ py: 2 }}
      >
        <Grid
          item
          lg={6}
          sx={{ borderLeft: variables.border.light, px: 2 }}
        >
          <Typography variant="body2">
            <a href="http://openenergyplatform.org/ontology/oeo/OEO_00020227">Scenario bundles</a> weave together important information about one or more <a href="http://openenergyplatform.org/ontology/oeo/OEO_00000364">scenarios</a>. They inform about <a href="http://openenergyplatform.org/ontology/oeo/OEO_00020011">studies</a> made based on a scenario, including publications (= <a href="http://openenergyplatform.org/ontology/oeo/OEO_00020012">study report</a>).
          </Typography>
          <Typography variant="body2">
            If there is quantitative <a href="http://openenergyplatform.org/ontology/oeo/OEO_00030029">input data</a> and / or <a href="http://openenergy-platform.org/ontology/oeo/OEO_00020013">output data</a> available on the OEP, the scenario bundles can link to that data, too.
            They can also inform about <a href="http://openenergyplatform.org/ontology/oeo/OEO_00020353">models</a> (if available as a <a href="https://openenergyplatform.org/factsheets/models/">model factsheet</a>) and frameworks (if available as a <a href="https://openenergyplatform.org/factsheets/frameworks/">framework factsheet</a>) that were used to project a scenario into the future (= <a href="http://openenergyplatform.org/ontology/oeo/OEO_00010262">scenario projection</a>).
          </Typography>
          <Typography variant="body2">
            In a nutshell: A scenario bundle provides you with all relevant information to understand a scenario's context and to ease a potential re-use of quantitative data for your own purposes.
          </Typography>
          <Typography variant="body2">
            The scenario bundles are stored in the Open Energy Knowledge Graph (OEKG). The OEKG can be queried using the SPARQL language. We provide a <a href="/oekg/gui/">User Interface</a> to simplify this rather technical task. 
            If you want to send your own SPARQL query you can do this by send a request to the http-api endpoint. 
          </Typography>
        </Grid>
      </Grid>
      <Toolbar sx={{ marginBottom: theme => theme.spacing(4) }}>
        <Grid container justifyContent="space-between"
          spacing={2}>

          <Grid item xs={12} md={4}>
            {/* <Tooltip title="Show all">
              <Button variant="outlined" size="small"><SelectAllIcon onClick={handleShowAll}/></Button>
            </Tooltip> */}
            <Button variant="outlined" size="small" key="Query" sx={{ marginLeft: '8px' }} onClick={handleOpenQuery} startIcon={<FilterAltOutlinedIcon />}>Filter</Button>
            <Button disabled={true}size="small" key="resetFilterButton" sx={{ marginLeft: '8px' }} startIcon={<ReplayIcon />} onClick={handleShowAll}>Reset</Button>
            <Tooltip title="Compare">

              {numSelected > 1 ? <Link to={`scenario-bundles/compare/${[...selected].join('#')}`} onClick={() => this.forceUpdate} style={{ color: 'white' }}>
                <Button size="small"
                  style={{ 'marginLeft': '5px', 'color': 'white', 'textTransform': 'none' }}
                  variant="contained"
                  key="compareScenariosBtn"
                  startIcon={<CompareArrowsIcon />}
                >
                  Compare scenarios
                </Button>
              </Link>
                :
                <Button size="small"
                  style={{ 'marginLeft': '5px', 'color': 'white', 'textTransform': 'none' }}
                  variant="contained"
                  key="compareScenariosBtn"
                  startIcon={<CompareArrowsIcon />}
                  onClick={handleOpenAspectsOfComparison}
                >
                  Compare scenarios
                </Button>
              }

            </Tooltip>
          </Grid>
          <Grid item xs={6} md={4}>
            <ToggleButtonGroup
              color="primary"
              value={alignment}
              exclusive
              onChange={handleChangeView}
              aria-label="Platform"
              size="small"
            >
              <ToggleButton value="list"><FormatListBulletedOutlinedIcon />List</ToggleButton>
              <ToggleButton value="cards"><ViewAgendaOutlinedIcon />Cards</ToggleButton>
            </ToggleButtonGroup>
          </Grid>
          <Grid item xs={6} md={4}>
            <HtmlTooltip
              style={{ marginLeft: '10px' }}
              placement="top"
              title={
                <React.Fragment>
                  <div>
                    <b>{logged_in === "NOT_LOGGED_IN" ? "Please login first!" : "Create a new Scenario Bundle!"}</b>
                  </div>
                </React.Fragment>
              }
            >
              <span>
                <Button disabled={logged_in === "NOT_LOGGED_IN"} component={Link} variant="contained" size="small" className="linkButton" to={`scenario-bundles/id/new`} onClick={() => this.forceUpdate}>
                  <AddIcon />
                  Create new
                </Button>
              </span>
            </HtmlTooltip>
          </Grid>
        </Grid>
      </Toolbar>
    </div>
  );
}

EnhancedTableToolbar.propTypes = {
  numSelected: PropTypes.number.isRequired,
};

export default function CustomTable(props) {
  const { factsheets } = props;

  const [order, setOrder] = useState('asc');
  const [orderBy, setOrderBy] = useState('study name');
  const [selected, setSelected] = useState(new Set());
  const [page, setPage] = useState(0);
  const [dense, setDense] = useState(false);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  const [open, setOpen] = useState([]);
  const [openQuery, setOpenQuery] = useState(false);
  const [openScenarioComparisonMessage, setOpenScenarioComparisonMessage] = useState(false);
  const [selectedInstitution, setSelectedInstitution] = useState([]);
  const [institutions, setInstitutions] = useState([]);
  const [selectedAuthors, setSelectedAuthors] = useState([]);
  const [authors, setAuthors] = useState([]);
  const [fundingSources, setFundingSources] = useState([]);
  const [selectedFundingSource, setSelectedFundingSource] = useState([]);
  const [startDateOfPublication, setStartDateOfPublication] = useState('2000');
  const [endDateOfPublication, setEndDateOfPublication] = useState('2050');
  const [selectedStudyKewords, setSelectedStudyKewords] = useState([]);
  const [scenarioYearValue, setScenarioYearValue] = React.useState([2020, 2050]);
  const [selectedAspects, setSelectedAspects] = useState([]);
  const [alignment, setAlignment] = React.useState('list');
  const [filteredFactsheets, setFilteredFactsheets] = useState([]);
  const [logged_in, setLogged_in] = React.useState('');

  const handleChangeView = (
    event: React.MouseEvent<HTMLElement>,
    newAlignment: string,
  ) => {
    newAlignment !== null && setAlignment(newAlignment);
  };

  const handleScenarioYearChange = (event, newValue) => {
    setScenarioYearValue(newValue);
  };
  const [rows, setRows] = useState(factsheets);

  const [openBackDrop, setOpenBackDrop] = useState(false);

  const handleClose = () => {
    setOpenBackDrop(false);
  };


  const handleRequestSort = (event, property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleSelectAllClick = (event) => {
    if (event.target.checked) {
      const newSelected = rows.map((n) => n.study_name);
      setSelected(newSelected);
      return;
    }
    setSelected([]);
  };

  const handleClick = (event, name) => {
    console.log(name);

    const newSelected = new Set(selected);
    if (newSelected.has(name)) newSelected.delete(name);
    else newSelected.add(name);

    // const selectedIndex = selected.indexOf(name);
    // let newSelected = [];

    // if (selectedIndex === -1) {
    //   newSelected = newSelected.concat(selected, name);
    // } else if (selectedIndex === 0) {
    //   newSelected = newSelected.concat(selected.slice(1));
    // } else if (selectedIndex === selected.length - 1) {
    //   newSelected = newSelected.concat(selected.slice(0, -1));
    // } else if (selectedIndex > 0) {
    //   newSelected = newSelected.concat(
    //     selected.slice(0, selectedIndex),
    //     selected.slice(selectedIndex + 1),
    //   );
    // }

    setSelected(newSelected);

  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleChangeDense = (event) => {
    setDense(event.target.checked);
  };

  const handleOpenQuery = (event) => {
    setOpenQuery(true);
  };

  const handleOpenAspectsOfComparison = (event) => {
    if (selected.size < 2) {
      setOpenScenarioComparisonMessage(true);
    }
  };

  const handleCloseAspectsForComparison = (event) => {
    setOpenScenarioComparisonMessage(false);
  };

  const handleShowAll = (event) => {
    setRows(factsheets);
    console.log(rows);
  };

  const handleCloseQuery = (event) => {
    setOpenQuery(false);
  };

  const handleReset = (event) => {
    setOpenQuery(false);
    setSelectedAuthors([]);
    setSelectedInstitution([]);
  };

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

  const getInstitution = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000238' } });
    return data;
  };

  const getAuthors = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000064' } });
    return data;
  };

  const getFundingSources = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00090001' } });
    return data;
  };

  const getLoggedInStatus = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/is_logged_in/`);
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
    getAuthors().then((data) => {
      const tmp = [];
      data.map((item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }))
      setAuthors(tmp);
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
    getLoggedInStatus().then((data) => {
      setLogged_in(data);
    });
  }, []);

  const institutionHandler = (institutionList) => {
    setSelectedInstitution(institutionList);
  };
  const authorsHandler = (authorsList) => {
    setSelectedAuthors(authorsList);
  };

  const fundingSourceHandler = (fundingSourceList) => {
    setSelectedFundingSource(fundingSourceList);
  };

  const handleConfirmQuery = (event) => {
    setOpenQuery(false);
    setOpenBackDrop(true);
    const criteria = {
      'institutions': selectedInstitution.map(i => 'OEKG:' + i.iri),
      'authors': selectedAuthors.map(i => 'OEKG:' + i.iri),
      'fundingSource': selectedFundingSource.map(i => 'OEKG:' + i.iri),
      'startDateOfPublication': startDateOfPublication,
      'endDateOfPublication': endDateOfPublication,
      'studyKewords': selectedStudyKewords,
      'scenarioYearValue': scenarioYearValue,
    }
    axios.post(conf.toep + 'scenario-bundles/query/',
      {
        'criteria': criteria,
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      }
    ).then(response => {
      const filteredResultList = response.data;
      const filteredStudyAcronyms = filteredResultList.map(i => i.study_acronym).map(j => j.value);
      const newFactsheetsList = factsheets.filter(item => filteredStudyAcronyms.includes(item.acronym));
      setFilteredFactsheets(newFactsheetsList);
      setOpenBackDrop(false);
    });
  };


  const isSelected = (name) => selected.has(name);

  const handleAspects = (event) => {
    if (event.target.checked) {
      if (!selectedAspects.includes(event.target.name)) {
        setSelectedAspects([...selectedAspects, event.target.name]);
      }
    } else {
      const filteredAspects = selectedAspects.filter(i => i !== event.target.name);
      setSelectedAspects(filteredAspects);
    }
  }

  // Avoid a layout jump when reaching the last page with empty rows.
  const emptyRows =
    page > 0 ? Math.max(0, (1 + page) * rowsPerPage - rows.length) : 0;

  const visibleRows = React.useMemo(
    () =>
      stableSort(rows, getComparator(order, orderBy)).slice(
        page * rowsPerPage,
        page * rowsPerPage + rowsPerPage,
      ),
    [order, orderBy, page, rowsPerPage],
  );


  const scenarioAspects = [
    "Descriptors",
    "Years",
    "Regions",
    "Interacting regions",
    "Input datasets",
    "Output datasets",
  ];

  const renderRows = (rs) => {
    const rowsToRender = filteredFactsheets.length == 0 ? factsheets : filteredFactsheets;
    return <TableBody >
      {rowsToRender.map((row, index) => {
        const isItemSelected = isSelected(row.study_name);
        const labelId = `enhanced-table-checkbox-${index}`;
        return (
          <React.Fragment>
            <StyledTableRow
              hover
              role="checkbox"
              aria-checked={isItemSelected}
              tabIndex={-1}
              key={row.study_name}
              selected={isItemSelected}
              sx={{ cursor: 'pointer', height: '60px' }}
            >
              <TableCell style={{ width: '400px' }}>
                <Link to={`scenario-bundles/id/${row.uid}`} onClick={() => this.forceUpdate} >
                  <Typography variant="body1" style={{ fontSize: '16px', cursor: 'pointer', color: "#294456" }}><b style={{ fontSize: '16px' }}>{row.study_name}</b></Typography>
                </Link>
              </TableCell >
              <TableCell style={{ width: '100px' }}>
                <Link to={`scenario-bundles/id/${row.uid}`} onClick={() => this.forceUpdate} >
                  <Typography variant="subtitle1" gutterBottom style={{ fontSize: '16px', cursor: 'pointer', color: "#294456" }}>
                    {row.acronym}
                  </Typography>
                </Link>
              </TableCell>
              <TableCell style={{ width: '300px', padding: "5px" }}>
                {row.scenarios.map((v) => (
                  <HtmlTooltip
                    style={{ marginLeft: '10px' }}
                    placement="top"
                    title={
                      <React.Fragment>
                        <div>
                          <b>Full name:</b> {v.full_name}
                          <Divider style={{ marginTop: '10px', marginBottom: '10px' }} />
                          <b>Abstract:</b> {v.abstract}
                        </div>
                      </React.Fragment>
                    }
                  >
                    <Chip size="small" color="primary" label={v.label} variant={selected.has(v.uid) ? "filled" : "outlined"} sx={{ 'marginLeft': '5px', 'marginTop': '4px' }} onClick={(event) => handleClick(event, v.uid)} />
                  </HtmlTooltip>
                ))}
              </TableCell>

              <TableCell style={{ width: '100px' }}>
                {row.collected_scenario_publication_dates.length === 0 ? (
                  <Typography variant="subtitle1" gutterBottom style={{ marginTop: '2px' }}>None</Typography>
                ) : (
                  row.collected_scenario_publication_dates.map((date_of_publication) => (
                    <Typography variant="subtitle1" gutterBottom style={{ marginTop: '2px' }}>
                      {date_of_publication !== null ? String(date_of_publication).substring(0, 4) : "None"}
                    </Typography>
                  ))
                )}
              </TableCell>

              <TableCell style={{ width: '40px' }}>
                <Stack direction="row" alignItems="center" justifyContent={'space-between'}>
                  <IconButton
                    aria-label="expand row"
                    size="small"
                    onClick={() => open.includes(index) ? setOpen((prevOpen) => prevOpen.filter((i) => i !== index)) : setOpen((prevOpen) => [...prevOpen, index])}
                  >
                    {open.includes(index) ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
                  </IconButton>
                </Stack>
              </TableCell >

            </StyledTableRow>
            <TableRow >
              <TableCell colSpan={8} >
                <Collapse in={open.includes(index)} timeout="auto" unmountOnExit>
                  <Box>
                    <Grid container
                      direction="row"
                      justifyContent="space-between"
                      alignItems="center"
                      paddingLeft="30px"
                      paddingRight="100px"
                      paddingBottom="10px"
                    >
                      <Grid item xs={12}>
                        <p><b>Abstract: </b> {row.abstract}</p>
                      </Grid>

                      <Grid item xs={12}>
                        <b>Institutions: </b>{row.institutions.map((v) => (
                          <span> <span> {v} </span> <span>   <b className="separator-dot"> . </b></span> </span>
                        ))}
                      </Grid>

                      <Grid item xs={12}>
                        <b>Funding sources: </b>{row.funding_sources.map((v) => (
                          <span> <span> {v} </span> <span>   <b className="separator-dot"> . </b></span> </span>
                        ))}
                      </Grid>

                      <Grid item xs={12} >
                        <b>Models and frameworks: </b>{row.models.map((v) => (
                          <span> <span> {v} </span> <span>   <b className="separator-dot"> . </b></span> </span>
                        ))}
                        {row.frameworks.map((v) => (
                          <span> <span> {v} </span> <span>   <b className="separator-dot"> . </b></span> </span>
                        ))}
                      </Grid>
                    </Grid>
                  </Box>
                </Collapse>
              </TableCell>
            </TableRow>
          </React.Fragment>
        );
      })}
    </TableBody>

  }

  const renderCards = (rs) => {
    const rowsToRender = filteredFactsheets.length == 0 ? factsheets : filteredFactsheets;
    return <Grid
      container
      justifyContent="space-between"
      alignItems="start"
      direction="row"
      sx={{ paddingBottom: variables.spacing[6] }}
    >
      {rowsToRender.map((row, index) => {
        const isItemSelected = isSelected(row.study_name);
        const labelId = `enhanced-table-checkbox-${index}`;
        return (
          <CardItem>
            <CardHeader>
              <Link
                to={`scenario-bundles/id/${row.uid}`}
                onClick={() => this.forceUpdate}
              >
                <Typography variant="link">
                  {row.study_name}
                </Typography>
              </Link>
            </CardHeader>
            <CardBody>
              <CardRow
                rowKey="Acronym"
                rowValue={
                  <Link
                    to={`scenario-bundles/id/${row.uid}`}
                    onClick={() => this.forceUpdate}
                  >
                    <Typography variant="link">
                      {row.acronym}
                    </Typography>
                  </Link>
                }
              />
              {row.collected_scenario_publication_dates !== null &&
                <CardRow
                  rowKey='Year of publication'
                  rowValue={row.collected_scenario_publication_dates
                    .map(date_of_publication => date_of_publication)
                    .join(' • ')}
                />
              }
              <CardRow
                rowKey='Abstract'
                rowValue={row.abstract}
              >
              </CardRow>
              <CardRow
                rowKey='Institutions'
                rowValue={
                  row.institutions.map((v) => (
                    <span>
                      <span> {v} </span>
                      <span>
                        <b className="separator-dot"> . </b>
                      </span>
                    </span>
                  ))
                }
              />
              <CardRow
                rowKey='Funding sources'
                rowValue={
                  row.funding_sources.map((v) => (
                    <span>
                      <span> {v} </span>
                      <span>
                        <b className="separator-dot"> . </b>
                      </span>
                    </span>
                  ))
                }
              />
              <CardRow
                rowKey='Models and frameworks'
                rowValue={
                  <>
                    {row.models.map((v) => (
                      <span>
                        <span> {v} </span>
                        <span>
                          <b className="separator-dot"> . </b>
                        </span>
                      </span>
                    ))}
                    {row.frameworks.map((v) => (
                      <span>
                        <span> {v} </span>
                        <span>
                          <b className="separator-dot"> . </b>
                        </span>
                      </span>
                    ))}
                  </>
                }
              />
              <CardRow
                rowKey="Scenarios"
                rowValue={row.scenarios.map((v) => (
                  <HtmlTooltip
                    style={{ marginLeft: '10px' }}
                    placement="top"
                    title={
                      <React.Fragment>
                        <div>
                          <b>Full name: </b> {v.full_name}
                          <Divider style={{ marginTop: '10px', marginBottom: '10px' }} />
                          <b>Abstract:</b> {v.abstract}
                        </div>
                      </React.Fragment>
                    }
                  >
                    <Chip
                      size="small"
                      color="primary"
                      label={v.label}
                      variant={selected.has(v.uid) ? "filled" : "outlined"}
                      sx={{ 'marginLeft': '5px', 'marginTop': '4px' }}
                      onClick={(event) => handleClick(event, v.uid)}
                    />
                  </HtmlTooltip>
                ))}
              />
            </CardBody>
          </CardItem>
        );
      })}
    </Grid>
  }

  return (
    <Box sx={{ width: '100%' }}>
      <BreadcrumbsNavGrid subheaderContent="Overview" />
      <Backdrop
        sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
        open={openBackDrop}
        onClick={handleClose}
      >
        <CircularProgress color="inherit" />
      </Backdrop>
      <Dialog
        maxWidth="md"
        open={openScenarioComparisonMessage}
        aria-labelledby="responsive-dialog-title"
        style={{ height: '85vh', overflow: 'auto' }}
      >
        <DialogTitle id="responsive-dialog-title">
          <b> Please select scenarios for comparison. </b>
        </DialogTitle >
        <DialogContent>
        </DialogContent>
        <DialogActions>
          <Button variant="outlined" onClick={handleCloseAspectsForComparison}  >
            Ok
          </Button>
        </DialogActions>
      </Dialog>


      <Dialog
        maxWidth="md"
        open={openQuery}
        aria-labelledby="responsive-dialog-title"
        style={{ height: '85vh', overflow: 'auto' }}
      >
        <DialogTitle id="responsive-dialog-title">
          <b>Please define the criteria for selecting factsheets.</b>
        </DialogTitle >
        <DialogContent>
          <DialogContentText>
            <div>
               <CustomAutocompleteWithoutEdit bgColor="white" width="100%" type="institution" showSelectedElements={true} manyItems optionsSet={institutions} kind='Which institutions are you interested in?' handler={institutionHandler} selectedElements={selectedInstitution} />
              <CustomAutocompleteWithoutEdit bgColor="white" width="100%" type="author" showSelectedElements={true} manyItems optionsSet={authors} kind='Which authors are you interested in?' handler={authorsHandler} selectedElements={selectedAuthors} />
              <CustomAutocompleteWithoutEdit bgColor="white" width="100%" type="Funding source" showSelectedElements={true} manyItems optionsSet={fundingSources} kind='Which funding sources are you interested in?' handler={fundingSourceHandler} selectedElements={selectedFundingSource} /> 
              <div>Date of publication:</div>
              <div style={{ display: 'flex', marginTop: "10px" }}>
                <LocalizationProvider dateAdapter={AdapterDayjs}>
                  <Stack spacing={3} style={{ width: '90%' }}>
                    <DesktopDatePicker
                      label='Start'
                      views={['year']}
                      value={startDateOfPublication.split('-')[0]}
                      renderInput={(params) => <TextField {...params} />}
                      onChange={(newValue) => {
                        const dateObj = new Date(newValue);
                        const dateString = dateObj.getFullYear() + '/' + (dateObj.getMonth() + 1) + '/' + String(dateObj.getDate())
                        setStartDateOfPublication(dateString.split('-')[0]);
                      }}
                    />
                  </Stack>
                </LocalizationProvider>
                <LocalizationProvider dateAdapter={AdapterDayjs}>
                  <Stack spacing={3} style={{ width: '90%', marginLeft: '10px' }}>
                    <DesktopDatePicker
                      label='End'
                      views={['year']}
                      value={endDateOfPublication.split('-')[0]}
                      renderInput={(params) => <TextField {...params} />}
                      onChange={(newValue) => {
                        const dateObj = new Date(newValue);
                        const dateString = dateObj.getFullYear() + '/' + (dateObj.getMonth() + 1) + '/' + String(dateObj.getDate())
                        setEndDateOfPublication(dateString.split('-')[0]);
                      }}
                    />
                  </Stack>
                </LocalizationProvider>
              </div>
              <div style={{ marginTop: "20px" }}>
                <div>Study descriptors:</div>
                <FormGroup>
                  <div >
                    {
                      StudyKeywords.map((item) => <FormControlLabel control={
                        <Checkbox size="small" color="default" />
                      } checked={selectedStudyKewords.includes(item[0])} onChange={handleStudyKeywords} label={item[0]} name={item[0]} />)
                    }
                  </div>
                </FormGroup>
              </div>

              <div style={{ marginTop: "20px" }}>
                <div>Scenario years:</div>
                <Slider
                  value={scenarioYearValue}
                  onChange={handleScenarioYearChange}
                  valueLabelDisplay="auto"
                  min={2000}
                  max={2200}
                />
              </div>
            </div>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button variant="contained" onClick={handleConfirmQuery} >
            Confirm
          </Button>
          <Button variant="outlined" onClick={handleCloseQuery}  >
            Cancel
          </Button>
        </DialogActions>
      </Dialog>

      <Container maxWidth="xl">
        <EnhancedTableToolbar logged_in={logged_in} numSelected={selected.size} selected={selected} alignment={alignment} handleChangeView={handleChangeView} handleOpenQuery={handleOpenQuery} handleShowAll={handleShowAll} handleOpenAspectsOfComparison={handleOpenAspectsOfComparison} />
        {alignment == "list" && <TableContainer>
          <Table
            sx={{ minWidth: 1400 }}
            aria-labelledby="tableTitle"
            size={dense ? 'small' : 'medium'}
          >
            <EnhancedTableHead
              numSelected={selected.length}
              order={order}
              orderBy={orderBy}
              onSelectAllClick={handleSelectAllClick}
              onRequestSort={handleRequestSort}
              rowCount={rows.length}
            />
            {renderRows(visibleRows)}
          </Table>
        </TableContainer>}
        {alignment == "list" && <TablePagination
          rowsPerPageOptions={[15, 25, 50]}
          component="div"
          count={rows.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />}


        {alignment == "cards" && renderCards(visibleRows)}
      </Container>
    </Box>
  );
}
