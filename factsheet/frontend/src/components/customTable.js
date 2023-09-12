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
import VisibilityIcon from '@mui/icons-material/Visibility';
import ViewComfyAltIcon from '@mui/icons-material/ViewComfyAlt';
import FilterAltOutlinedIcon from '@mui/icons-material/FilterAltOutlined';
import ReplayIcon from '@mui/icons-material/Replay';
import Chip from '@mui/material/Chip';
import ReadMoreIcon from '@mui/icons-material/ReadMore';
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


import '../styles/App.css';

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
    id: 'date of publications',
    numeric: true,
    disablePadding: false,
    label: 'Date of publications',
    align: 'left'
  },
  {
    id: 'institutions',
    numeric: true,
    disablePadding: false,
    label: 'Institutions',
    align: 'left'
  },
  {
    id: 'scenarios',
    numeric: true,
    disablePadding: false,
    label: 'Scenarios',
    align: 'left'
  },
  {
    id: 'more',
    numeric: false,
    disablePadding: true,
    label: '',
    align: 'left'
  },
  {
    id: 'details',
    numeric: true,
    disablePadding: false,
    label: '',
    align: 'right'
  }
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
        <StyledTableCell padding="checkbox">
         {/*  <Checkbox
                color="primary"
                indeterminate={numSelected > 0 && numSelected < rowCount}
                checked={rowCount > 0 && numSelected === rowCount}
                onChange={onSelectAllClick}
              /> */}
        </StyledTableCell>
        {headCells.map((headCell) => (
          <StyledTableCell
            key={headCell.id}
            align={headCell.align}
            padding={headCell.disablePadding ? 'none' : 'normal'}
            sortDirection={orderBy === headCell.id ? order : false}
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
  const { numSelected, handleOpenQuery, handleShowAll, handleOpenAspectsOfComparison} = props;

  return (
    <Toolbar
      sx={{
          bgcolor: '#04678F20',
          color: 'white',
          display: 'flex',
      }}
    >
      
      <Tooltip title="Show all">
        <Button variant="outlined" size="small"><SelectAllIcon onClick={handleShowAll}/></Button>
      </Tooltip>
      <Button variant="outlined" size="small" key="Query" sx={{ marginLeft: '8px'}} onClick={handleOpenQuery} startIcon={<FilterAltOutlinedIcon />}>Filter</Button>
      <Button size="small" key="resetFilterButton" sx={{ marginLeft: '8px'}} startIcon={<ReplayIcon />}>Reset</Button>
      <Button variant="contained" size="small" key="compareScenariosBtn" sx={{ marginLeft: '8px'}} startIcon={<CompareArrowsIcon />}>Compare scenarios</Button>

      <Typography
        sx={{ flex: '1 1 70%' }}
        color="inherit"
        variant="subtitle1"
        component="div"
      >
        {numSelected > 1 && <Tooltip title="Compare">

              <Button size="small" style={{ 'height': '43px', 'textTransform': 'none', 'marginTop': '5px', 'marginRight': '5px', 'zIndex': '1000', 'marginLeft': '5px', 'color': 'white', 'textTransform': 'none' }} variant="contained" key="Compare">
              <CompareArrowsIcon onClick={handleOpenAspectsOfComparison} />
              </Button>

          </Tooltip>}
      </Typography>
      <Button component={Link} variant="contained" size="small" className="linkButton" to={`sirop/factsheet/new`} onClick={() => this.forceUpdate}>
        <AddIcon/>
        Create new
      </Button>
    </Toolbar>
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
  const [openAspectsForComparison, setOpenAspectsForComparison] = useState(false);
  const [selectedInstitution, setSelectedInstitution] = useState([]);
  const [institutions, setInstitutions] = useState([]);
  const [selectedAuthors, setSelectedAuthors] = useState([]);
  const [authors, setAuthors] = useState([]);
  const [fundingSources, setFundingSources] = useState([]);
  const [selectedFundingSource, setSelectedFundingSource] = useState([]);
  const [startDateOfPublication, setStartDateOfPublication] = useState('01-01-1900');
  const [endDateOfPublication, setEndDateOfPublication] = useState('01-01-1900');
  const [selectedStudyKewords, setSelectedStudyKewords] = useState([]);
  const [scenarioYearValue, setScenarioYearValue] = React.useState([2020, 2050]);
  const [selectedAspects, setSelectedAspects] = useState([]);

  const [filteredFactsheets, setFilteredFactsheets] = useState([]);


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

    console.log(newSelected);
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
    setOpenAspectsForComparison(true);
  };

  const handleCloseAspectsForComparison = (event) => {
    setOpenAspectsForComparison(false);
  };

  const handleShowAll = (event) => {
    setRows(factsheets);
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
    const { data } = await axios.get(conf.toep + `sirop/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000238' } });
    return data;
  };

  const getAuthors = async () => {
    const { data } = await axios.get(conf.toep + `sirop/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00000064' } });
    return data;
  };

  const getFundingSources = async () => {
    const { data } = await axios.get(conf.toep + `sirop/get_entities_by_type/`, { params: { entity_type: 'OEO.OEO_00090001' } });
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
    getAuthors().then((data) => {
      const tmp = [];
      data.map( (item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }) )
      setAuthors(tmp);
      });
  }, []);

  useEffect(() => {
    getFundingSources().then((data) => {
      const tmp = [];
      data.map( (item) => tmp.push({ 'iri': item.iri, 'name': item.name, 'id': item.name }) )
      setFundingSources(tmp);
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
    axios.post(conf.toep + 'sirop/query/',
    {
      'criteria': criteria,
    }).then(response => {
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

  const scenarioAspects = [
    "Descriptors",
    "Years",
    "Regions", 
    "Interacting regions",
    "Input datasets",
    "Output datasets",
  ];

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

  const renderRows = (rs) => {
    const rowsToRender =  filteredFactsheets.length == 0 ? factsheets : filteredFactsheets;
    return <TableBody>
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
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell padding="checkbox">
                   
                  </TableCell>
                  <TableCell>
                    <Typography variant="subtitle1" gutterBottom style={{ marginTop: '10px' }}>{row.study_name}</Typography>
                  </TableCell>
                  <TableCell ><Typography variant="subtitle1" gutterBottom style={{ marginTop: '2px' }}>{row.acronym}</Typography></TableCell>
                  <TableCell ><Typography variant="subtitle1" gutterBottom style={{ marginTop: '2px' }}>{row.date_of_publication !== null && String(row.date_of_publication).substring(0, 10)}</Typography></TableCell>
                  <TableCell >
                    {row.institutions.map((v) => (
                      <Chip label={v} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" color="secondary"/>
                    ))}
                  </TableCell>
                  <TableCell >

                 

                      {row.scenarios.map((v) => (
                        <HtmlTooltip
                          style={{ marginLeft: '10px' }}
                          placement="top"
                          title={
                            <React.Fragment>
                              <Typography color="inherit" variant="caption">
                                Full name: {v.full_name}
                                <br />
                                Abstract: {v.abstract}
                              </Typography>
                            </React.Fragment>
                          }
                        >
                          <Chip color="primary" label={v.label} variant={selected.has(v.label) ? "filled" : "outlined"} sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} onClick={(event) => handleClick(event, v.label)}/>
                        </HtmlTooltip>
                      ))}
                  </TableCell>
                  <TableCell>
                    {/* <IconButton
                      aria-label="expand row"
                      size="small"
                      onClick={() => open.includes(index) ? setOpen((prevOpen) => prevOpen.filter((i) => i !== index)) : setOpen((prevOpen) => [...prevOpen, index])}
                    >
                      {open === index ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
                    </IconButton> */}
                  </TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>
                    <Link to={`sirop/factsheet/${row.uid}`} onClick={() => this.forceUpdate} >
                      <ReadMoreIcon sx={{ cursor: 'pointer', color: '#04678F', marginTop: '5px', fontSize: '35px' }}/>
                    </Link> 
                  </TableCell>
                </StyledTableRow>
              <TableRow>
                <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={8}>
                    <Collapse in={open.includes(index)} timeout="auto" unmountOnExit>
                      <Box sx={{ margin: 1 }}>
                        <Typography variant="subtitle1" gutterBottom component="div">
                          Details
                        </Typography>
                        <Table size="small" aria-label="purchases">
                          <TableHead>
                            <TableRow>
                              <TableCell>Publication</TableCell>
                              <TableCell>Funding sources</TableCell>
                              <TableCell>Models</TableCell>
                              <TableCell>Frameworks</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                              <TableRow >
                                <TableCell component="th" scope="row">
                                {row.acronym}
                                </TableCell>
                                <TableCell component="th" scope="row">
                                {row.acronym}
                                </TableCell>
                                <TableCell component="th" scope="row">
                                {row.acronym}
                                </TableCell>
                                <TableCell component="th" scope="row">
                                {row.acronym}
                                </TableCell>
                              </TableRow>
                          </TableBody>
                        </Table>
                      </Box>
                    </Collapse>
                  </TableCell>
              </TableRow>

            </React.Fragment>
            );

      })}
      {emptyRows > 0 && (
        <TableRow
          style={{
            height: (dense ? 33 : 53) * emptyRows,
          }}
        >
          <TableCell colSpan={6} />
        </TableRow>
      )}
    </TableBody>
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Backdrop
        sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
        open={openBackDrop}
        onClick={handleClose}
      >
        <CircularProgress color="inherit" />
      </Backdrop>
      <Dialog
        maxWidth="md"
        open={openAspectsForComparison}
        aria-labelledby="responsive-dialog-title"
        style={{ height: '85vh', overflow: 'auto' }}
      >
        <DialogTitle id="responsive-dialog-title">
          <b>  Which elements of the scenarios do you wish to compare? </b>
        </DialogTitle >
        <DialogContent>
         {/*  <Typography variant="h6" gutterBottom style={{ marginTop: '20px' }}>
            Which elements of the studies do you wish to compare?
          </Typography>
            <FormGroup>
              <FormControlLabel control={<Checkbox defaultChecked />} label="Descriptors" />
              <FormControlLabel control={<Checkbox />} label="Sectors" />
              <FormControlLabel control={<Checkbox />} label="Enrgy carriers" />
              <FormControlLabel control={<Checkbox />} label="Enrgy transformation processes" />
              <FormControlLabel control={<Checkbox />} label="Models" />
              <FormControlLabel control={<Checkbox />} label="Frameworks" />
            </FormGroup>
          <Divider /> */}
          <FormGroup>
              {
                scenarioAspects.map((item) => <FormControlLabel control={<Checkbox />} checked={selectedAspects.includes(item)} onChange={handleAspects} label={item} name={item}/>)
              }
              
            </FormGroup>
        </DialogContent>
        <DialogActions>
          <Button variant="contained" >
            <Link to={`sirop/compare/${[...selected].join('-')}CASPECTS${[...selectedAspects.map(i => i.substring(0, 3).toLowerCase())].join('-')}`} onClick={() => this.forceUpdate} style={{  color: 'white' }} >
              Show comparison
            </Link>
          </Button>
          <Button variant="outlined" onClick={handleCloseAspectsForComparison}  >
            Cancel
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
              <CustomAutocompleteWithoutEdit bgColor="white" width="100%" type="institution" showSelectedElements={true} manyItems optionsSet={institutions} kind='Which institutions are you interested in?' handler={institutionHandler} selectedElements={selectedInstitution}/>
              <CustomAutocompleteWithoutEdit bgColor="white" width="100%" type="author" showSelectedElements={true}  manyItems optionsSet={authors} kind='Which authors are you interested in?' handler={authorsHandler} selectedElements={selectedAuthors}  />
              <CustomAutocompleteWithoutEdit bgColor="white" width="100%"  type="Funding source" showSelectedElements={true} manyItems optionsSet={fundingSources} kind='Which funding sources are you interested in?' handler={fundingSourceHandler} selectedElements={selectedFundingSource}/>
              <div>Date of publication:</div>
              <div style={{ display:'flex', marginTop: "10px"}}>
                <LocalizationProvider dateAdapter={AdapterDayjs}>
                  <Stack spacing={3} style={{ width: '90%' }}>
                    <DesktopDatePicker
                        label='Start'
                        inputFormat="MM/DD/YYYY"
                        value={startDateOfPublication}
                        renderInput={(params) => <TextField {...params} />}
                        onChange={(newValue) => {
                          setStartDateOfPublication(newValue.toISOString().substring(0, 10));
                        }}
                      />
                  </Stack>
                </LocalizationProvider>
                <LocalizationProvider dateAdapter={AdapterDayjs}>
                  <Stack spacing={3} style={{ width: '90%', marginLeft: '10px' }}>
                    <DesktopDatePicker
                        label='End'
                        inputFormat="MM/DD/YYYY"
                        value={endDateOfPublication}
                        renderInput={(params) => <TextField {...params} />}
                        onChange={(newValue) => {
                          setEndDateOfPublication(newValue.toISOString().substring(0, 10));
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
                        StudyKeywords.map((item) => <FormControlLabel control={<Checkbox size="small" color="default" />} checked={selectedStudyKewords.includes(item)} onChange={handleStudyKeywords} label={item} name={item} />)
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
          <Button variant="contained"  onClick={handleConfirmQuery} >
            Confirm
          </Button>
          <Button variant="outlined" onClick={handleCloseQuery}  >
            Cancel
          </Button>
        </DialogActions>
      </Dialog>

      <Paper sx={{ width: '97%', marginLeft: '30px', marginTop: '30px', mb: 2 }}>
        <EnhancedTableToolbar numSelected={selected.size}  handleOpenQuery={handleOpenQuery} handleShowAll={handleShowAll} handleOpenAspectsOfComparison={handleOpenAspectsOfComparison}/>
        <TableContainer>
          <Table
            sx={{ minWidth: 750 }}
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
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={rows.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>
    </Box>
  );
}