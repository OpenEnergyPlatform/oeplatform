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
import CustomDatePicker from './customDatePicker.js'
import Typography from '@mui/material/Typography';
import AddBoxIcon from '@mui/icons-material/AddBox';
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
  const [scenarioObject, setScenarioObject] = useState({});
  const [acronym, setAcronym] = useState('');
  const [studyName, setStudyName] = useState('');
  const [abstract, setAbstract] = useState('');
  const [scenarios, setScenarios] = useState(1);
  const [report_title, setReportTitle] = useState('');
  const [doi, setDOI] = useState('');
  const [place_of_publication, setPlaceOfPublication] = useState('');
  const [link_to_study, setLinkToStudy] = useState('');
  const [scenarioName, setScenarioName] = useState('');
  const [scenarioAbstract, setScenarioAbstract] = useState('');
  const [scenarioAcronym, setScenarioAcronym] = useState('');
  const [scenarioInputDatasetName, setScenarioInputDatasetName] = useState('');
  const [scenarioOutputDatasetName, setScenarioOutputDatasetName] = useState('');
  const [scenarioInputDatasetIRI, setScenarioInputDatasetIRI] = useState('');
  const [scenarioOutputDatasetIRI, setScenarioOutputDatasetIRI] = useState('');

  const handleSaveJSON = () => {
    //props.onChange(oekg);
    setOpenJSON(true);
  };

  const handleSaveFactsheet = () => {
    factsheetObjectHandler('name', factsheetName);
    axios.post('http://localhost:8000/factsheet/add/', null,
     {  params:
          factsheetObject
     });
  };

  const handleCloseJSON = () => {
    setOpenJSON(false);
  };

  const handleScenarioInpuDatasetName = e => {
    setScenarioInputDatasetName(e.target.value);
    factsheetObjectHandler('scenario_input_dataset_name', e.target.value);
  };

  const handleScenarioInputDatasetIRI = e => {
    setScenarioInputDatasetIRI(e.target.value);
    factsheetObjectHandler('scenario_input_dataset_IRI', e.target.value);
  };

  const handleScenarioOutputDatasetName = e => {
    setScenarioOutputDatasetName(e.target.value);
    factsheetObjectHandler('scenario_output_dataset_name', e.target.value);
  };

  const handleScenariooutputDatasetIRI = e => {
    setScenarioOutputDatasetIRI(e.target.value);
    factsheetObjectHandler('scenario_output_dataset_IRI', e.target.value);
  };

  const handleScenarioName = e => {
    setScenarioName(e.target.value);
    factsheetObjectHandler('scenario_name', e.target.value);
  };

  const handleScenarioAcronym = e => {
    setScenarioAcronym(e.target.value);
    factsheetObjectHandler('scenario_acronym', e.target.value);
  };

  const handleScenarioAbstract = e => {
    setScenarioAbstract(e.target.value);
    factsheetObjectHandler('scenario_abstract', e.target.value);
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

  const handlePlaceOfPublication = e => {
    setPlaceOfPublication(e.target.value);
    factsheetObjectHandler('place_of_publication', e.target.value);
  };

  const handleLinkToStudy = e => {
    setLinkToStudy(e.target.value);
    factsheetObjectHandler('link_to_study', e.target.value);
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

  const handleAddScenario = () => {
    setScenarios(scenarios + 1);
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
    const [selectedContactPerson, setselectedContactPerson] = useState([]);

    const [selectedRegion, setSelectedRegion] = useState([]);
    const [selectedInteractingRegion, setSelectedInteractingRegion] = useState([]);
    const [selectedEnergyCarriers, setSelectedsetEnergyCarriers] = useState([]);
    const [selectedEnergyTransportation, setSelectedEnergyTransportation] = useState([]);
    const [selectedScenarioInputDatasetRegion, setSelectedScenarioInputDatasetRegion] = useState([]);
    const [selectedScenarioOutputDatasetRegion, setSelectedScenarioOutputDatasetRegion] = useState([]);

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

    const contact_person = [
      { id: 'Alex', name: 'Alex' },
      { id: 'Markus', name: 'Markus' },
    ];

    const scenario_region = [
      { id: '1', name: 'Germany' },
      { id: '2', name: 'France' },
    ];

    const scenario_input_dataset_region = [
      { id: '1', name: 'Germany' },
      { id: '2', name: 'France' },
    ];

    const scenario_interacting_region = [
      { id: '1', name: 'Germany' },
      { id: '2', name: 'France' },
      { id: '3', name: 'Spain' },
    ];

    const energy_carriers = [
      { id: '1', name: 'Gas' },
      { id: '3', name: 'Electricity' },
    ];

    const energy_transportation = [
      { id: '1', name: 'Fuel' },
    ];

    const sectorsHandler = (sectorsList) => {
      setSelectedSectors(sectorsList);
      factsheetObjectHandler('sectors', sectorsList);
    };

    const authorsHandler = (authorsList) => {
      setSelectedAuthors(authorsList);
      factsheetObjectHandler('authors', authorsList);
      factsheetObjectHandler('authors', JSON.stringify(authorsList));
    };

    const institutionHandler = (institutionList) => {
      setSelectedInstitution(institutionList);
      factsheetObjectHandler('institution', JSON.stringify(selectedInstitution));
    };

    const fundingSourceHandler = (fundingSourceList) => {
      setSelectedFundingSource(fundingSourceList);
      factsheetObjectHandler('funding_source', JSON.stringify(selectedFundingSource));
    };

    const contactPersonHandler = (contactPersonList) => {
      setSelectedFundingSource(contactPersonList);
      factsheetObjectHandler('contact_person', JSON.stringify(selectedContactPerson));
    };

    const scenarioRegionHandler = (regionList) => {
      setSelectedRegion(regionList);
      factsheetObjectHandler('scenario_region', JSON.stringify(selectedRegion));
    };

    const interactingRegionHandler = (interactionRegionList) => {
      setSelectedInteractingRegion(interactionRegionList);
      factsheetObjectHandler('scenario_interacting_region', JSON.stringify(setSelectedInteractingRegion));
    };

    const energyCarrierHandler = (energyCarrierList) => {
      setSelectedsetEnergyCarriers(energyCarrierList);
      factsheetObjectHandler('scenario_energy_carriers', JSON.stringify(selectedEnergyCarriers));
    };

    const energyTransportationHandler = (energyTransportationList) => {
      setSelectedEnergyTransportation(energyTransportationList);
      factsheetObjectHandler('scenario_energy_transportation', JSON.stringify(selectedEnergyTransportation));
    };

    const scenarioInputDatasetRegionHandler = (inputDatasetRegionList) => {
      setSelectedScenarioInputDatasetRegion(inputDatasetRegionList);
      factsheetObjectHandler('scenario_input_dataset_region', JSON.stringify(selectedScenarioInputDatasetRegion));
    };

    const scenarioOutputDatasetRegionHandler = (outputDatasetRegionList) => {
      setSelectedScenarioOutputDatasetRegion(outputDatasetRegionList);
      factsheetObjectHandler('scenario_output_dataset_region', JSON.stringify(selectedScenarioOutputDatasetRegion));
    };

    const renderStudy = () => {
      return <Grid container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
      >
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <TextField style={{  width: '90%' }} id="outlined-basic" label="Name" variant="outlined" value={studyName} onChange={handleStudyName}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <TextField style={{  width: '90%' }} id="outlined-basic" label="Acronym" variant="outlined" value={acronym} onChange={handleAcronym} />
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <TextField style={{ width: '90%', MarginBottom: '10px' }} id="outlined-basic" label="Short abstract" variant="outlined" multiline rows={2} maxRows={10} value={abstract} onChange={handleAbstract}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <CustomAutocomplete optionsSet={institution} kind='Institution' handler={institutionHandler} selectedElements={selectedInstitution}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <CustomAutocomplete optionsSet={funding_source} kind='Funding source' handler={fundingSourceHandler} selectedElements={selectedFundingSource}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <CustomAutocomplete optionsSet={contact_person} kind='Contact person' handler={contactPersonHandler} selectedElements={selectedContactPerson}/>
        </Grid>
        <Grid
          container
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          style={{ 'padding': '20px', 'border': '1px solid #cecece', width: '97%' }}
        >
          <Grid item xs={12} >
            <Typography variant="subtitle1" gutterBottom style={{ marginTop:'10px', marginBottom:'10px' }}>
              Report:
            </Typography>
          </Grid>
          <Grid item xs={6} >
            <TextField style={{ marginTop:'-20px', width: '90%' }} id="outlined-basic" label="Title" variant="outlined" value={report_title} onChange={handleReportTitle} />
          </Grid>
          <Grid item xs={6} >
            <CustomAutocomplete optionsSet={authors} kind='Author' handler={authorsHandler} selectedElements={selectedAuthors}/>
          </Grid>
          <Grid item xs={6} >
            <CustomDatePicker label='Date of Publication' style={{ marginBottom:'10px' }}/>
          </Grid>
          <Grid item xs={6} >
            <TextField style={{ width: '90%' }} id="outlined-basic" label="DOI" variant="outlined" value={doi} onChange={handleDOI} />
          </Grid>
          <Grid item xs={6} >
            <TextField style={{ width: '90%', marginTop:'20px' }} id="outlined-basic" label="Place of publication" variant="outlined" value={place_of_publication} onChange={handlePlaceOfPublication} />
          </Grid>
          <Grid item xs={6} >
            <TextField style={{ width: '90%', marginTop:'20px' }} id="outlined-basic" label="Link to study report" variant="outlined" value={link_to_study} onChange={handleLinkToStudy} />
          </Grid>
        </Grid>
      </Grid>
    }

    const renderScenario = () => {
      return <Grid container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
      >
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <TextField style={{  width: '90%' }} id="outlined-basic" label="Name" variant="outlined" value={scenarioName} onChange={handleScenarioName}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <TextField style={{  width: '90%' }} id="outlined-basic" label="Acronym" variant="outlined" value={scenarioAcronym} onChange={handleScenarioAcronym}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <TextField style={{ width: '90%', MarginBottom: '10px' }} id="outlined-basic" label="Short abstract" variant="outlined" value={scenarioAbstract} onChange={handleScenarioAbstract} multiline rows={2} maxRows={10} />
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <CustomAutocomplete optionsSet={scenario_region} kind='Region' handler={scenarioRegionHandler} selectedElements={selectedRegion}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <CustomAutocomplete optionsSet={scenario_interacting_region} kind='Interacting region' handler={interactingRegionHandler} selectedElements={selectedInteractingRegion}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <CustomDatePicker label='Scenario year' style={{ marginBottom:'10px' }}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <CustomAutocomplete optionsSet={energy_carriers} kind='Energy carriers' handler={energyCarrierHandler} selectedElements={selectedEnergyCarriers}/>
        </Grid>
        <Grid item xs={6} style={{ marginBottom: '10px' }}>
          <CustomAutocomplete optionsSet={energy_transportation} kind='Energy transformation process' handler={energyTransportationHandler} selectedElements={selectedEnergyTransportation}/>
        </Grid>
        <Grid
          container
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          style={{ 'padding': '20px', 'border': '1px solid #cecece', width: '97%' }}
        >
          <Grid item xs={12} >
            <Typography variant="subtitle1" gutterBottom style={{ marginTop:'10px', marginBottom:'10px' }}>
              Input dataset:
            </Typography>
          </Grid>
          <Grid item xs={6} >
            <TextField style={{ width: '90%' }} id="outlined-basic" label="Name" variant="outlined" value={scenarioInputDatasetName} onChange={handleScenarioInpuDatasetName}/>
          </Grid>
          <Grid item xs={6} >
            <TextField style={{ width: '90%' }} id="outlined-basic" label="IRI" variant="outlined" value={scenarioInputDatasetIRI} onChange={handleScenarioInputDatasetIRI}/>
          </Grid>
          <Grid item xs={6}  style={{ marginTop:'20px' }}>
            <CustomAutocomplete optionsSet={scenario_input_dataset_region} kind='Region' handler={scenarioInputDatasetRegionHandler} selectedElements={selectedScenarioInputDatasetRegion} />
          </Grid>
          <Grid item xs={6} >
            <CustomDatePicker label='Scenario year' style={{ marginBottom:'10px' }}/>
          </Grid>
        </Grid>
        <Grid
          container
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          style={{ marginTop:'20px', 'padding': '20px', 'border': '1px solid #cecece', width: '97%' }}
        >
          <Grid item xs={12} >
            <Typography variant="subtitle1" gutterBottom style={{ marginTop:'10px', marginBottom:'10px' }}>
              Output dataset:
            </Typography>
          </Grid>
          <Grid item xs={6} >
            <TextField style={{ width: '90%' }} id="outlined-basic" label="Name" variant="outlined" value={scenarioOutputDatasetName} onChange={handleScenarioOutputDatasetName} />
          </Grid>
          <Grid item xs={6} >
            <TextField style={{ width: '90%' }} id="outlined-basic" label="IRI" variant="outlined" value={scenarioOutputDatasetIRI} onChange={handleScenariooutputDatasetIRI}/>
          </Grid>
          <Grid item xs={6}  style={{ marginTop:'20px' }}>
            <CustomAutocomplete optionsSet={institution} kind='Region' handler={scenarioOutputDatasetRegionHandler} selectedElements={selectedScenarioOutputDatasetRegion}/>
          </Grid>
          <Grid item xs={6} >
            <CustomDatePicker label='Scenario year' style={{ marginBottom:'10px' }}/>
          </Grid>
        </Grid>
      </Grid>
    }

    const items = {
      titles: ['Study', 'Scenarios', 'Models', 'Frammeworks'],
      contents: [
        renderStudy(),
        <Grid
          container
          direction="column"
          justifyContent="space-between"
          style={{ 'marginTop': '20px', 'padding': '20px', 'border': '1px solid #cecece', width: '97%' }}
        >
          <div style={{ 'textAlign': 'right' }}>
            <Button disableElevation={true} startIcon={<AddBoxIcon />}  style={{ 'textTransform': 'none', 'marginTop': '10px', 'marginLeft': '5px', 'zIndex': '1000'  }} variant="contained" color="primary" onClick={handleAddScenario}>Add</Button>
          </div >
          {Array(scenarios).fill().map((item, i) =>
              <Grid item xs={12}  style={{ 'marginTop':'20px', 'marginBottom':'20px', 'padding': '20px', 'border': '1px solid #cecece', 'backgroundColor': i % 2 === 0 ? '#ffffff':'rgb(250 250 250)' }}>
                <Typography variant="subtitle1" gutterBottom style={{ marginTop:'10px', marginBottom:'10px' }}>
                  Scenario {i + 1}
                </Typography>
                {renderScenario()}
              </Grid>

          )}
        </Grid>,
        <CustomAutocomplete optionsSet={sectors} kind='Models' handler={sectorsHandler} selectedElements={selectedSectors}/>,
        <CustomAutocomplete optionsSet={sectors} kind='Frameworks' handler={sectorsHandler} selectedElements={selectedSectors}/>,
        ]
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
              <Button disableElevation={true} startIcon={<MailOutlineIcon />}   style={{ 'textTransform': 'none', 'marginTop': '10px', 'zIndex': '1000' }} variant="outlined" color="primary" onClick={handleSaveFactsheet} >Save</Button>
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
