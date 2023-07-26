import React, { PureComponent, Fragment, useState, useEffect } from "react";
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import conf from "../conf.json";
import axios from "axios";
import LinearProgress from '@mui/material/LinearProgress';
import { styled } from '@mui/material/styles';
import TableCell, { tableCellClasses } from '@mui/material/TableCell';

import Box from '@mui/material/Box';
import { DataGrid, GridColDef, GridValueGetterParams } from '@mui/x-data-grid';


const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 90 },
    {
      field: 'subject',
      headerName: 'Subject',
      width: 500,
    },
    {
      field: 'predicate',
      headerName: 'Predicate',
      width: 500,
    },
    {
      field: 'object',
      headerName: 'Object',
      width: 500,
    },
    {
      field: 'action',
      headerName: 'Action',
      width: 100,
    },
    {
      field: 'user',
      headerName: 'User',
      width: 200,
    },
    {
      field: 'timestamp',
      headerName: 'Timestamp',
      width: 200,
    },
  ];

export default function HistoryTable() {

    const [history, setHistory] = useState({});
    const [loading, setLoading] = useState(true);

    const getHistory= async () => {
    const { data } = await axios.get(conf.toep + `sirop/get_oekg_history/`);
        return data;
    };

    useEffect(() => {
        getHistory().then((data) => {
        setHistory(JSON.parse(data));
        setLoading(false);
        });
    }, []);



    if (loading === false) {
        return (
        <Box sx={{ width: '100%' }}>
        <DataGrid
            rows={history.map((row, index) => ({ id: index + 1, 
                subject: row.fields.triple_subject, 
                predicate: row.fields.triple_predicate, 
                object: row.fields.triple_object, 
                action: row.fields.type_of_action, 
                user: row.fields.user, 
                timestamp: row.fields.timestamp, 
            } ))}
            columns={columns}
            initialState={{
            pagination: {
                paginationModel: {
                pageSize: 20,
                },
            },
            }}
            pageSizeOptions={[5]}
            disableRowSelectionOnClick
        />
        </Box>
    );
    } else {
        return <LinearProgress />
    }

}