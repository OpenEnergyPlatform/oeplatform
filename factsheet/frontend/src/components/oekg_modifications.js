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
    const { data } = await axios.get(conf.toep + `sirop/get_oekg_modifications/`);
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
        <Box sx={{ width: '100%' }}>
            {  
                modifications.map((row, index) => 
                    <Box>
                       <div style={{ backgroundColor: "#001c30e6", color: "white" }}>
                            <Stack direction="row" alignItems="center" justifyContent={'space-between'}>
                                <Typography variant="h6" gutterBottom style={{ margin: "10px" }}>
                                    {index + 1 }
                                </Typography>
                                <Typography variant="h6" gutterBottom style={{ margin: "10px" }}>
                                    {row.fields.timestamp}
                                </Typography>
                                <Typography variant="h6" gutterBottom style={{ margin: "10px" }}>
                                    {row.fields.user}
                                </Typography>
                            </Stack>
                        </div>
                        <ReactDiffViewer oldValue={row.fields.old_state} newValue={row.fields.new_state} splitView={true} />
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