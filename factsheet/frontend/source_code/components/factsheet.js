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
import '../styles/App.css';

import CustomAutocomplete from './customAutocomplete.js';
import CustomAutocompleteWithAddNew from './customAutocompleteWithAddNew.js';
import axios from "axios"

function Factsheet(props) {
  const {factsheetName} = props;
  const jsonld = require('jsonld');

  const [factsheetJSON, setFactsheetJSON] = useState({
    "@context": {
      "@base": "https://openenergy-platform.org/oekg/",
      "oeo": "https://openenergy-platform.org/ontology/oeo/",
      "foaf": "http://xmlns.com/foaf/0.1/",
      "dc": "http://purl.org/dc/elements/1.1/"
    },
    "@id": "KS-2050",
    "@type": "oeo:OEO_00010250",
    "foaf:name": "Klimaschutzszenario 2050",
    "dc:description": "The project develops a vision of the future in the form of three scenarios that meet the ambitious climate protection goals of the Federal Republic of Germany when considering all sectors and uses the national potential of renewable energies",
    "oeo:OEO_00000506": [],
    "oeo:OEO_00000505": [],
    "oeo:OEO_00000509": []
  });

  const [factsheetRDF, setFactsheetRDF] = useState({});
  const [factsheetDjangoObject, setFactsheetDjangoObject] = useState({});
  const [openOverView, setOpenOverView] = useState(false);
  const [openJSON, setOpenJSON] = useState(false);
  const [openTurtle, setOpenTurtle] = useState(false);
  const [mode, setMode] = useState("wizard");
  const [factsheetObject, setFactsheetObject] = useState({});

  const handleSaveJSON = () => {
    //props.onChange(oekg);
    setOpenJSON(true);
  };
  const handleCloseJSON = () => {
    setOpenJSON(false);
  };

  const handleClickOpenTurtle = () => {
    setOpenTurtle(true);
    convert2RDF();
  };

  const handleCloseTurtle = () => {
    setOpenTurtle(false);
  };

  const handleCloseOverView = () => {
    setOpenOverView(false);
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



    const [selectedSectors, setSelectedSectors] = useState([]);
    const [selectedAuthors, setSelectedAuthors] = useState([]);
    const [selectedInstitution, setSelectedInstitution] = useState([]);
    const [selectedFundingSource, setSelectedFundingSource] = useState([]);

    const sectors = [
      { id: 'Agriculture forestry and land use sector', name: 'Agriculture forestry and land use sector' },
      { id: 'Energy demand sector', name: 'Energy demand sector' },
      { id: 'Energy transformation sector', name: 'Energy transformation sector' },
      { id: 'Industry sector', name: 'Industry sector' },
      { id: 'Waste and wastewater sector', name: 'Waste and wastewater sector' }
    ];

    const authors = [
      { id: 'Lüdwig', name: 'Lüdwig' },
      { id: 'Chris', name: 'Chris' },
      { id: 'Hanna', name: 'Hanna' },
      { id: 'Mirjam', name: 'Mirjam' },
      { id: 'Lukas', name: 'Lukas' },
      { id: 'Alex', name: 'Alex' },
      { id: 'Markus', name: 'Markus' },
      { id: 'Martin', name: 'Martin' },
      { id: 'Adel', name: 'Adel' },
      { id: 'Jonas', name: 'Jonas' }
    ];

    const funding_source = [
      { id: 'PTJ', name: "Projektträger Jülich"},
      { id: 'RLI', name: "Reiner Lemoine Institut"},
      { id: 'OvGU', name: "Otto von Guericke University Magdeburg"}
    ];

    const institution = [
      { id: 'Öko-Institut', name: "Öko-Institut"},
      { id: 'Frauenhofer', name: "Frauenhofer"},
    ];

    const sectorsHandler = (sectorsList) => {
      setSelectedSectors(sectorsList);
      factsheetObjectHandler('sectors', sectorsList);
    };

    const authorsHandler = (authorsList) => {
      setSelectedAuthors(authorsList);
      factsheetObjectHandler('authors', authorsList);
    };

    const institutionHandler = (institutionList) => {
      setSelectedInstitution(institutionList);
      factsheetObjectHandler('institution', institutionList);
    };

    const fundingSourceHandler = (fundingSourceList) => {
      setSelectedFundingSource(fundingSourceList);
      factsheetObjectHandler('funding_source', fundingSourceList);
    };


    const items = {
      titles: ['Responsibilities', 'Publication', 'Scenarios', 'Models and Frammeworks'],
      contents: [
        <div>
          <CustomAutocomplete optionsSet={authors} kind='author' handler={authorsHandler} selectedElements={selectedAuthors}/>
          <CustomAutocomplete optionsSet={institution} kind='institution' handler={institutionHandler} selectedElements={selectedInstitution}/>
          <CustomAutocomplete optionsSet={funding_source} kind='funding source' handler={fundingSourceHandler} selectedElements={selectedFundingSource}/>
          <CustomAutocompleteWithAddNew optionsSet={funding_source} kind='funding source' handler={fundingSourceHandler} selectedElements={selectedFundingSource}/>

        </div >,

        <CustomAutocomplete optionsSet={sectors} kind='sector' handler={sectorsHandler} selectedElements={selectedSectors}/>,
        'Regions', 'Energy carriers', 'Scenarios', 'Models',
        'Frameworks', 'Inputs', 'Outputs',
        'Publications' ]
    }

    const convert2RDF = async () => {

      factsheetJSON["oeo:OEO_00000506"] = [];
      selectedFundingSource.map(fundingSource => {
        factsheetJSON["oeo:OEO_00000506"].push({
          "@id": fundingSource.id.replaceAll(" ", "_"),
        });
      });

      factsheetJSON["oeo:OEO_00000505"] = [];
      selectedSectors.map(sector => {
        factsheetJSON["oeo:OEO_00000505"].push({
          "@id": sector.id.replaceAll(" ", "_"),
        });
      });

      factsheetJSON["oeo:OEO_00000509"] = [];
      selectedAuthors.map(author => {
        factsheetJSON["oeo:OEO_00000509"].push({
          "@id": author.id.replaceAll(" ", "_"),
        });
      });

      const nquads = await jsonld.toRDF(factsheetJSON, {format: 'application/n-quads'});
      setFactsheetRDF(nquads);
      return(nquads);
    }

    useEffect(() => {
      convert2RDF().then((nquads) => setFactsheetRDF(nquads));
    }, []);



    const getFS = axios.create({
      baseURL: "http://localhost:8000/api/v0/get_factsheet/",
      params: { id: 42 }
    });

    useEffect(() => {
      getFS.get().then((response) => {
        setFactsheetDjangoObject(response.data);
      });
    }, []);


    return (
      <div>
        <Grid container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
      >
          <Grid item xs={8} >
          <div>
               <CustomSwap handleSwap={handleSwap} />
          </div >
          <div>
               {factsheetDjangoObject.id}
          </div >

          </Grid>
          <Grid item xs={4} >
            <div style={{ 'textAlign': 'right' }}>
              <Button disableElevation={true} startIcon={<MailOutlineIcon />}   style={{ 'textTransform': 'none', 'marginTop': '10px', 'zIndex': '1000' }} variant="outlined" color="primary" onClick={handleSaveJSON} >Save</Button>
              <Button disableElevation={true} startIcon={<ForwardToInboxIcon />}   style={{ 'textTransform': 'none', 'marginTop': '10px', 'marginLeft': '5px', 'marginRight': '10px','zIndex': '1000'  }} variant="contained" color="primary" onClick={handleClickOpenTurtle}>Submit</Button>
            </div >
          </Grid>
          <Grid item xs={12}>
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
                <Button variant="contained" onClick={handleCloseTurtle} autoFocus>
                  Download
                </Button>
                <Button variant="contained" autoFocus onClick={handleCloseTurtle}>
                  Cancel
                </Button>
              </DialogActions>
            </Dialog>
            <Dialog
              fullWidth
              maxWidth="lg"
              open={openJSON}
              onClose={handleCloseJSON}
              aria-labelledby="responsive-dialog-title"
            >
              <DialogTitle id="responsive-dialog-title">
                <b>Save </b>
              </DialogTitle>
              <DialogContent>
                <DialogContentText>
                  <div>
                      {/* <pre>{JSON.stringify(oekg, null, '\t')}</pre> */}
                    <pre>{JSON.stringify({factsheetObject}, null, '\t')}</pre>
                  </div>
                </DialogContentText>
              </DialogContent>
              <DialogActions>
                <Button variant="contained" onClick={handleCloseJSON} autoFocus>
                  Download
                </Button>
                <Button variant="contained" autoFocus onClick={handleCloseJSON}>
                  Cancel
                </Button>
              </DialogActions>
            </Dialog>




                {mode === "wizard" &&
                  <div className='wizard'>
                      <Grid container >
                        <Grid item xs={12} >
                          <div style={{ "textAlign": "center", "fontSize": "25px" }}>
                            <b> {factsheetName} </b>
                          </div>
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
