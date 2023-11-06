import React, { PureComponent, Fragment, useState, useEffect } from "react";
import conf from "../conf.json";
import axios from "axios";
import LinearProgress from '@mui/material/LinearProgress';
import Box from '@mui/material/Box';
import ReactDiffViewer from 'react-diff-viewer-continued';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';

export default function Diff() {
    const [modifications, setModifications] = useState({});
    const [loading, setLoading] = useState(true);

    const getModifications= async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_oekg_modifications/`);
        return data;
    };

    useEffect(() => {
        getModifications().then((data) => {
        setModifications(JSON.parse(data));
        setLoading(false);
        });
    }, []);

    if (loading === false) {
        return (
        <Box sx={{ width: '100%', height: '85vh', overflow:'auto' }}>
            {  
                modifications.map((row, index) => 
                    <Box>
                       <div style={{ backgroundColor: "#001c30e6", color: "white" }}>
                            <Stack direction="row" alignItems="center" justifyContent={'space-between'}>
                                <p style={{ margin: "10px" }}>
                                    <b>  Change number: </b> {index + 1 }
                                </p>
                                <p style={{ margin: "10px" }}>
                                    <b>  Bundle Id: </b> {row.fields.bundle_id}
                                </p>
                                <p style={{ margin: "10px" }}>
                                    <b>  Date and time: </b> {row.fields.timestamp}
                                </p>
                                <p style={{ margin: "10px" }}>
                                    <b>  User's Id: </b>  {row.fields.user}
                                </p>
                            </Stack>
                        </div>
                        <ReactDiffViewer oldValue={row.fields.old_state} newValue={row.fields.new_state} splitView={true} disableWordDiff={true} />
                        <Divider style={{ marginTop: "10px" }}/>
                    </Box>
                )
            }
            
        </Box>
    );
    } else {
        return <LinearProgress />
    }

}