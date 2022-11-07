import React, { PureComponent, Fragment, useState, useEffect } from "react";
import Grid from '@mui/material/Grid';
import CardContent from "@mui/material/CardContent";
import Card from "@mui/material/Card";
import Factsheet from './components/factsheet.js'
import CustomCard from './components/customCard.js'
import Typography from "@mui/material/Typography";
import ApolloClient from 'apollo-boost';
import { ApolloProvider } from 'react-apollo';
import CardActions from "@mui/material/CardActions";
import Box from "@mui/material/Box";
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import AddBoxIcon from '@mui/icons-material/AddBox';
import axios from "axios"

import './styles/App.css';
import CustomSearchInput from "./components/customSearchInput"


const client = new ApolloClient({
  uri: 'http://localhost:8000/graphql/',
});

function App() {

  const [fs, setFs] = React.useState(1);
  const [factsheets, setFactsheets] = React.useState([]);
  const [loading, setLoading] = useState(true);
  const [openFactsheetName, setOpenFactsheetName] = useState(false);
  const [factsheetName, setFactsheetName] = useState('');
  const [showFactsheetForm, setShowFactsheetForm] = useState(false);

  const handleNewFactsheet = (fs) => {
    setFs(fs);
  };

  const handleOpenFactsheetName = () => {
    setOpenFactsheetName(true);
  };

  const handleCloseFactsheetName = () => {
    setOpenFactsheetName(false);
  };

  const handleCreateFactsheet = (name) => {
    setOpenFactsheetName(false);
    setShowFactsheetForm(true);
  };

  const handleChangeFactsheetName = e => {
    setFactsheetName(e.target.value);
  };

  const searchHandler = (v) => {
    console.log(v);
  };

  const getData = async () => {
    const { data } = await axios.get(`http://localhost:8000/factsheet/all/`);
    let factsheets = data.replaceAll('\\', '').replaceAll('"[', '[').replaceAll(']"', ']');
    setFactsheets(JSON.parse(JSON.stringify(factsheets)));
    setLoading(false)
  };
  useEffect(() => {
    getData();
  }, []);

  const card =  (
      <Fragment>
        <CardContent>
          <Typography variant="h5" component="div">
            Factsheet
          </Typography>
          <Typography sx={{ mb: 1.5 }} color="text.secondary">
            Institution
          </Typography>
          <Typography variant="body2">
            Scenario years
            <br />
            Description
          </Typography>
        </CardContent>
        <CardActions>
          <Button size="small">More</Button>
        </CardActions>
      </Fragment>
    );


  return (
    <ApolloProvider client={client}>
      <div >
            {!showFactsheetForm && <Grid container spacing={2} direction="row" justifyContent="space-between">
              <Grid item xs={10}>
                <CustomSearchInput searchHandler={searchHandler} data={[{ name: 'A', label: 'Anguilla', phone: '1-264' },
                { name: 'B', label: 'Albania', phone: '355' },
                { name: 'C', label: 'Armenia', phone: '374' }]}/>
              </Grid>

              <Grid item xs={2}>
                  <Button disableElevation={true} startIcon={<AddBoxIcon />}   style={{ 'textTransform': 'none', 'margin': '10px', 'margiBottom' : '10px', 'height': '55px', 'zIndex': '1000', 'float': 'right' }} variant="contained" color="primary" onClick={handleOpenFactsheetName} >Add a new Factsheet</Button>
              </Grid>
            </Grid>}

            {!showFactsheetForm && <Grid container spacing={2} direction="row">
              <Grid item xs={12}>
                  <Box
                    sx={{
                      display: "flex",
                      "& > :not(style)": {
                        m: 1,
                        width: '25%',
                        height: 250,
                      }
                    }}
                  >
                    {!loading &&  <CustomCard title={eval(factsheets)[0].fields.factsheetData.abstract} />}
                    {!loading &&  <CustomCard title={eval(factsheets)[1].fields.factsheetData.abstract} />}
                    {!loading &&  <CustomCard title={eval(factsheets)[2].fields.factsheetData.abstract} />}
                    {!loading &&  <CustomCard title={eval(factsheets)[3].fields.factsheetData.abstract} />}
                    {!loading &&  <CustomCard title={eval(factsheets)[4].fields.factsheetData.abstract} />}
                    {!loading &&  <CustomCard title={eval(factsheets)[5].fields.factsheetData.abstract} />}
                    {!loading &&  <CustomCard title={eval(factsheets)[6].fields.factsheetData.abstract} />}
                    {!loading &&  <CustomCard title={eval(factsheets)[7].fields.factsheetData.abstract} />}
                    <Card variant="outlined">{card}</Card>
                    <Card variant="outlined">{card}</Card>
                    <Card variant="outlined">{card}</Card>
                  </Box>
              </Grid>
              <Grid item xs={12}>
                  <Box
                    sx={{
                      display: "flex",
                      "& > :not(style)": {
                        m: 1,
                        width: '25%',
                        height: 250,
                      }
                    }}
                  >
                    <Card variant="outlined">{card}</Card>
                    <Card variant="outlined">{card}</Card>
                    <Card variant="outlined">{card}</Card>
                    <Card variant="outlined">{card}</Card>
                  </Box>
              </Grid>

              <Grid item xs={12}>
                <Dialog
                  fullWidth
                  maxWidth="lg"
                  open={openFactsheetName}
                  onClose={handleOpenFactsheetName}
                  aria-labelledby="responsive-dialog-title"
                >
                <DialogTitle id="responsive-dialog-title">
                  <b>Create a new factsheet! </b>
                </DialogTitle>
                <DialogContent>
                  <DialogContentText>
                    <TextField style={{ "marginTop": "10px" }} id="outlined-basic" label="Name" variant="outlined" value={factsheetName} onChange={handleChangeFactsheetName} fullWidth />
                  </DialogContentText>
                </DialogContent>
                <DialogActions>
                  <Button variant="contained" onClick={handleCreateFactsheet} autoFocus >
                    create
                  </Button>
                  <Button variant="contained" autoFocus >
                    Cancel
                  </Button>
                </DialogActions>
              </Dialog>
            </Grid>

            </Grid>}



          {showFactsheetForm && <Grid item xs={12}>
            <Factsheet factsheetName={factsheetName}/>
          </Grid>}

    </div>
    </ApolloProvider>
  );
}

export default App;
