import * as React from 'react';
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
import Chip from '@mui/material/Chip';
import ReadMoreIcon from '@mui/icons-material/ReadMore';

import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';

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
          <Checkbox
                color="primary"
                indeterminate={numSelected > 0 && numSelected < rowCount}
                checked={rowCount > 0 && numSelected === rowCount}
                onChange={onSelectAllClick}
              />
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
  const { numSelected } = props;

  return (
    <Toolbar
      sx={{
          bgcolor: '#04678F20',
          color: 'white',
          display: 'flex',
      }}
    >
      <Button variant="outlined" key="Compare" sx={{ marginLeft: '5px', textTransform: 'none' }}>Show all</Button>
      <Button variant="outlined" key="Compare" sx={{ marginLeft: '5px', textTransform: 'none' }}>Comparison criteria</Button>
      <Typography
        sx={{ flex: '1 1 70%' }}
        color="inherit"
        variant="subtitle1"
        component="div"
      >
        {numSelected > 1 && <Button variant="contained" key="Compare" sx={{ marginLeft: '10px', color: 'white', textTransform: 'none'  }}>Compare {numSelected} factsheets</Button>}
      </Typography>
      <Link to={`factsheet/fs/new`} onClick={() => this.forceUpdate} style={{  color: '#005374' }} >
        <Button variant="contained" key="Add" sx={{ marginLeft: '5px', textTransform: 'none' }}>Add a new</Button>
      </Link>
    </Toolbar>
  );
}

EnhancedTableToolbar.propTypes = {
  numSelected: PropTypes.number.isRequired,
};

export default function CustomTable(props) {
  const [order, setOrder] = React.useState('asc');
  const [orderBy, setOrderBy] = React.useState('study name');
  const [selected, setSelected] = React.useState([]);
  const [page, setPage] = React.useState(0);
  const [dense, setDense] = React.useState(false);
  const [rowsPerPage, setRowsPerPage] = React.useState(5);
  const [open, setOpen] = React.useState([]);

 
  const [rows, setRows] = React.useState(props.factsheets);

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
    const selectedIndex = selected.indexOf(name);
    let newSelected = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, name);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1),
      );
    }

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

  const isSelected = (name) => selected.indexOf(name) !== -1;

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

  return (
    <Box sx={{ width: '100%' }}>
      <Paper sx={{ width: '97%', marginLeft: '30px', marginTop: '30px', mb: 2 }}>
        <EnhancedTableToolbar numSelected={selected.length} />
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
            <TableBody>
              {visibleRows.map((row, index) => {
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
                      <Checkbox
                        onClick={(event) => handleClick(event, row.study_name)}
                        color="primary"
                        checked={isItemSelected}
                        inputProps={{
                          'aria-labelledby': labelId,
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="subtitle1" gutterBottom style={{ marginTop: '10px' }}>{row.study_name}</Typography>
                    </TableCell>
                    <TableCell ><Typography variant="subtitle1" gutterBottom style={{ marginTop: '2px' }}>{row.acronym}</Typography></TableCell>
                    <TableCell ><Typography variant="subtitle1" gutterBottom style={{ marginTop: '2px' }}>{row.date_of_publication !== null && String(row.date_of_publication).substring(0, 10)}</Typography></TableCell>
                    <TableCell >
                      {row.institutions.map((v) => (
                        <Chip label={v} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />
                      ))}
                    </TableCell>
                    <TableCell >
                        {row.scenarios.map((v) => (
                          <Chip label={v} variant="outlined" sx={{ 'marginLeft': '5px', 'marginTop': '2px' }} size="small" />
                        ))}
                    </TableCell>
                    <TableCell>
                      <IconButton
                        aria-label="expand row"
                        size="small"
                        onClick={() => open.includes(index) ? setOpen((prevOpen) => prevOpen.filter((i) => i !== index)) : setOpen((prevOpen) => [...prevOpen, index])}
                      >
                        {open === index ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
                      </IconButton>
                    </TableCell>
                    <TableCell sx={{ textAlign: 'center' }}>
                      <Link to={`factsheet/fs/${row.uid}`} onClick={() => this.forceUpdate} >
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