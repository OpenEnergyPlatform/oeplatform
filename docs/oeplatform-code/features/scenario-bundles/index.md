# Scenario Bundles feature

The scenario bundles feature is a response to the complex requirements for the transparent publication of scenarios in a complete and comprehensible manner. Various technologies are used to enable researchers to publish scenarios and any additional information. In addition, existing resources from the open energy platform are used and bundled together. This is intended to increase the visibility of available research work and enable comparability of the scenarios.

## What are Scenario Bundles in detail?

Please continue reading [here](https://openenergyplatform.github.io/organisation/family_members/templates-and-specification/scenario-bundles/).

## Technologies

User Interface

- We offer a modern user interface developed with the REACT library.

Backend & Web-API

- We build on the backend of the Open Energy Platform and use Django to implement functionalities such as saving and deleting scenario bundles and thus enable communication with the database. In addition, Django provides the WEB-API endpoints that are used to create a scenario bundle or query the database using JSON requests, for example.
- A Python integration of the SPARQL query language is used to interact with the Grpah database.

Database

- A graph database is used to store the complex data structure of the scenario bundles in the long term. We use Appache Jenna-Fuseki as a reliable technology.

## Code Documentation

### Django view for the scenario bundles

!!! note
Some of the information on this page may be changed in the future. To review the most recent information, please revisit.

`def create_factsheet(request, *args, **kwargs):`

#### ::: factsheet.views.create_factsheet

`def update_factsheet(request, *args, **kwargs):`

#### ::: factsheet.views.update_factsheet

`def factsheet_by_id(request, *args, **kwargs):`

#### ::: factsheet.views.factsheet_by_id

`def delete_factsheet_by_id(request, *args, **kwargs):`

#### ::: factsheet.views.delete_factsheet_by_id

`def add_entities(request, *args, **kwargs):`

#### ::: factsheet.views.add_entities

`def delete_entities(request, *args, **kwargs):`

#### ::: factsheet.views.delete_entities

`def update_an_entity(request, *args, **kwargs):`

#### ::: factsheet.views.update_an_entity

`def query_oekg(request, *args, **kwargs):`

#### ::: factsheet.views.query_oekg

`def get_entities_by_type(request, *args, **kwargs):`

#### ::: factsheet.views.get_entities_by_type

### The scenario bundle object construction and API in django

Below we describe how we construct the Scenario bundles in the scenario bundles django app. Using JSON as an input format the complex scenario bundle object becomes more manageable when working with WEB-technologies. Users will create a scenario bundle using a user interface with input text and selection fields this information is send and processed as JSON before it is stored in the OEKG using RDF´s triple notation.

You can read the following sections as: This is how django processes the data, and this is where the data is send once the user submits or changes a scenario bundles. The URL pointing out what django view will handle the JSON object below. This is very similar to what general web api´s do like REST-API´s. The exception here is that there is an CSRF Token involved which is required by the django backend to make sure requests are save and do not originate form an unsafe source allowing the scenario bundle frontend to send data to the backend.

The technology that drives this implementation is HTTP. The JSON objects and key:value information is send in packaged as a payload that is send along with each requests. A requests can be triggered by multiple actions for example a button that is pressed by the user. Based on the URL and the payload the backend can determine what functionality must be triggered. This can be for example creating a scenario bundle or retrieving a specific bundle by its ID.

!!! note
    Some of the information on this page may be changed in the future. To review the most recent information, please revisit.

#### Create a new bundle in OEKG

`https://openenergy-platform.org/scenario-bundles/add/`

An example of input parameters

```json
{
  "id": "new",
  "uid": "6157d6d6-7a7b-a61e-21d3-a8f936b19056",
  "study_name": "Example study name",
  "acronym": "Example acronym",
  "abstract": "Example abstract ...",
  "institution": [
    {
      "iri": "708ad5dc-7f8b-6c65-6a5f-0fc54fe8221b",
      "name": "Öko-Institut e.V."
    },
    {
      "iri": "8e1515b9-9b1f-fa06-a3a2-d552b0ea7dcd",
      "name": "Otto-von-Guericke-Universität Magdeburg"
    }
  ],
  "funding_source": [
    {
      "iri": "82dd628d-f748-560b-b0cd-06466cf90f1a",
      "name": "Bundesministerium für Umwelt, Naturschutz und nukleare Sicherheit"
    }
  ],
  "contact_person": [],
  "sector_divisions": [],
  "sectors": [
    {
      "label": "KSG sector buildings",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010067"
    },
    {
      "label": "KSG sector industry",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010066"
    },
    {
      "label": "CRF sector (IPCC 2006): wetlands",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010192"
    },
    {
      "label": "CRF sector (IPCC 2006): other product manufacture and use",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010172"
    },
    {
      "label": "CRF sector (IPCC 2006): manure management",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010180"
    },
    {
      "label": "CRF sector (IPCC 2006): multilateral operations",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010203"
    },
    {
      "label": "CRF sector (IPCC 2006): chemical industry - other",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010353"
    }
  ],
  "technologies": [
    {
      "label": "power generation technology",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010423"
    },
    {
      "label": "wind power technology",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010424"
    },
    {
      "label": "offshore wind power technology",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010426"
    },
    {
      "label": "solar thermal power technology",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010429"
    },
    {
      "label": "hydro power technology",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010431"
    },
    {
      "label": "run of river power technology",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010432"
    }
  ],
  "study_descriptors": [
    "life cycle analysis",
    "(changes in) demand",
    "degree of electrifiaction",
    "Reallabor",
    "regionalisation",
    "peak electricity generation"
  ],
  "report_title": "Example report title",
  "date_of_publication": " 2021",
  "report_doi": "5345-43-5634-6-346-46-43",
  "place_of_publication": "",
  "link_to_study": " https://openenergy-platform.org/",
  "authors": [],
  "scenarios": [
    {
      "id": "4974db65-542d-31cd-6f08-11ef9a58680a",
      "name": "Example scenario name 1 ",
      "acronym": "Example scenario acronym 1 ",
      "abstract": "Example scenario abstract 1 ... ",
      "regions": [
        {
          "name ": "Germany  ",
          "iri ": "https://www.omg.org/spec/LCC/Countries/ISO3166-1-CountryCodes/Germany "
        }
      ],
      "interacting_regions": [
        {
          "name ": "Spain  ",
          "iri ": "https://www.omg.org/spec/LCC/Countries/ISO3166-1-CountryCodes/Spain "
        }
      ],
      "scenario_years": [
        {
          "iri ": "33131404-e58e-12bc-170e-32aba1c83d99 ",
          "name ": "2021 "
        }
      ],
      "descriptors ": [
        {
          "label": "explorative scenario ",
          "class": "http://openenergy-platform.org/ontology/oeo/OEO_00020248 "
        },
        {
          "label": "policy scenario ",
          "class": "http://openenergy-platform.org/ontology/oeo/OEO_00020309 "
        },
        {
          "label": "climate scenario ",
          "class": "http://openenergy-platform.org/ontology/oeo/OEO_00030007"
        }
      ],
      "input_datasets": [
        {
          "key": "f2d32e9c-1fa0-4d66-9ffd-c297d4bb5c9a ",
          "idx": 0,
          "value ": {
            "label ": "abbb_transmission_capacity ",
            "iri ": "https://openenergy-platform.org/dataedit/view/scenario/abbb_transmission_capacity "
          }
        },
        {
          "key ": "ca9c82f3-9ba0-7d71-6601-dd520680bedb ",
          "idx ": 1,
          "value ": {
            "label ": "abbb_demand ",
            "iri ": "https://openenergy-platform.org/dataedit/view/scenario/abbb_demand "
          }
        }
      ],
      "output_datasets ": [
        {
          "key ": "0db015dd-1543-f0e9-9579-3602fb16a680 ",
          "idx ": 0,
          "value ": {
            "label ": "abbb_transformer ",
            "iri ": "https://openenergy-platform.org/dataedit/view/scenario/abbb_transformer "
          }
        }
      ]
    },
    {
      "id ": "1f4bb594-4b1c-dca4-2465-e04a54eec10b ",
      "name ": "Example scenario name 2 ",
      "acronym ": "Example scenario acronym 2 ",
      "abstract ": "Example scenario abstract 2 ... ",
      "regions ": [
        {
          "name ": "France  ",
          "iri ": "https://www.omg.org/spec/LCC/Countries/ISO3166-1-CountryCodes/France "
        }
      ],
      "interacting_regions ": [
        {
          "name ": "Germany  ",
          "iri ": "https://www.omg.org/spec/LCC/Countries/ISO3166-1-CountryCodes/Germany "
        }
      ],
      "scenario_years ": [],
      "descriptors ": [
        {
          "label ": "explorative scenario ",
          "class ": "http://openenergy-platform.org/ontology/oeo/OEO_00020248 "
        },
        {
          "label ": "with additional measures scenario ",
          "class ": "http://openenergy-platform.org/ontology/oeo/OEO_00020312 "
        },
        {
          "label ": "greenhouse gas emission scenario ",
          "class ": "http://openenergy-platform.org/ontology/oeo/OEO_00020317 "
        },
        {
          "label ": "climate scenario ",
          "class ": "http://openenergy-platform.org/ontology/oeo/OEO_00030007 "
        },
        {
          "label ": "economic scenario ",
          "class ": "http://openenergy-platform.org/ontology/oeo/OEO_00030008 "
        }
      ],
      "input_datasets ": [
        {
          "key ": "bfc811ee-11f5-6a5a-247d-6f66bb676dd9 ",
          "idx ": 0,
          "value ": {
            "label ": "abbb_transformer ",
            "iri ": "https://openenergy-platform.org/dataedit/view/scenario/abbb_transformer "
          }
        }
      ],
      "output_datasets ": [
        {
          "key ": "fbc30f51-7f32-9c21-dfb2-7534aeac538d ",
          "idx ": 0,
          "value ": {
            "label ": "ego_slp_parameters ",
            "iri ": "https://openenergy-platform.org/dataedit/view/scenario/ego_slp_parameters "
          }
        }
      ]
    }
  ],
  "models": [
    {
      "id ": "SciGrid: Open Source Reference Model of European Transmission Networks for Scientific Analysis ",
      "name ": "SciGrid: Open Source Reference Model of European Transmission Networks for Scientific Analysis "
    },
    {
      "id ": "Balmorel ",
      "name ": "Balmorel "
    },
    {
      "id ": "National Electricity Market Optimiser ",
      "name ": "National Electricity Market Optimiser "
    },
    {
      "id ": "urbs Bavaria ",
      "name ": "urbs Bavaria "
    }
  ],
  "frameworks": [
    {
      "id ": "Python for Power System Analysis toolbox (PyPSA) ",
      "name ": "Python for Power System Analysis toolbox (PyPSA) "
    },
    {
      "id ": "Framework for Integrated Energy System Assessment ",
      "name ": "Framework for Integrated Energy System Assessment "
    },
    {
      "id ": "Model Order Reduction for Gas and Energy Networks ",
      "name ": "Model Order Reduction for Gas and Energy Networks "
    },
    {
      "id ": "OMEGAlpes ",
      "name ": "OMEGAlpes "
    },
    {
      "id ": "Potsdam Integrated Assessment Modeling Framework (PIAM) ",
      "name ": "Potsdam Integrated Assessment Modeling Framework (PIAM) "
    }
  ]
}
```

#### Get a bundle in OEKG

Retrieve a bundle by its `uid`

`https://openenergy-platform.org/scenario-bundles/get/`

An example of input parameters

```json
"uid" : "6157d6d6-7a7b-a61e-21d3-a8f936b19056",
```

#### Remove a bundle from OEKG

`https://openenergy-platform.org/scenario-bundles/delete/`

To delete a bundle, the `uid` of the bundle should be provided.

An example of input parameters

```json
"uid" : "6157d6d6-7a7b-a61e-21d3-a8f936b19056",
```

#### Update a bundle in OEKG

`https://openenergy-platform.org/scenario-bundles/update/`

An example of input parameters

The `uid` should belong to an existing bundle in OEKG. The remaining fields are identical to those in the create bundle API.

```json
{
  "uid": "6157d6d6-7a7b-a61e-21d3-a8f936b19056",
  "study_name": "Example study name",
  "acronym": "Example acronym",
  "abstract": "Example abstract ...",
  "institution": [
    {
      "iri": "708ad5dc-7f8b-6c65-6a5f-0fc54fe8221b",
      "name": "Öko-Institut e.V."
    },
    {
      "iri": "8e1515b9-9b1f-fa06-a3a2-d552b0ea7dcd",
      "name": "Otto-von-Guericke-Universität Magdeburg"
    }
  ],
  "funding_source": [
    {
      "iri": "82dd628d-f748-560b-b0cd-06466cf90f1a",
      "name": "Bundesministerium für Umwelt, Naturschutz und nukleare Sicherheit"
    }
  ],
  "contact_person": [],
  "sector_divisions": [],
  "sectors": [
    {
      "label": "KSG sector buildings",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010067"
    },
    {
      "label": "KSG sector industry",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010066"
    },
    {
      "label": "CRF sector (IPCC 2006): wetlands",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010192"
    },
    {
      "label": "CRF sector (IPCC 2006): other product manufacture and use",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010172"
    },
    {
      "label": "CRF sector (IPCC 2006): manure management",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010180"
    },
    {
      "label": "CRF sector (IPCC 2006): multilateral operations",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010203"
    },
    {
      "label": "CRF sector (IPCC 2006): chemical industry - other",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010353"
    }
  ],
  "technologies": [
    {
      "label": "power generation technology",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010423"
    },
    {
      "label": "wind power technology",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010424"
    },
    {
      "label": "offshore wind power technology",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010426"
    },
    {
      "label": "solar thermal power technology",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010429"
    },
    {
      "label": "hydro power technology",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010431"
    },
    {
      "label": "run of river power technology",
      "class": "http://openenergy-platform.org/ontology/oeo/OEO_00010432"
    }
  ],
  "study_descriptors": [
    "life cycle analysis",
    "(changes in) demand",
    "degree of electrifiaction",
    "Reallabor",
    "regionalisation",
    "peak electricity generation"
  ],
  "report_title": "Example report title",
  "date_of_publication": " 2021",
  "report_doi": "5345-43-5634-6-346-46-43",
  "place_of_publication": "",
  "link_to_study": " https://openenergy-platform.org/",
  "authors": [],
  "scenarios": [
    {
      "id": "4974db65-542d-31cd-6f08-11ef9a58680a",
      "name": "Example scenario name 1 ",
      "acronym": "Example scenario acronym 1 ",
      "abstract": "Example scenario abstract 1 ... ",
      "regions": [
        {
          "name ": "Germany  ",
          "iri ": "https://www.omg.org/spec/LCC/Countries/ISO3166-1-CountryCodes/Germany "
        }
      ],
      "interacting_regions": [
        {
          "name ": "Spain  ",
          "iri ": "https://www.omg.org/spec/LCC/Countries/ISO3166-1-CountryCodes/Spain "
        }
      ],
      "scenario_years": [
        {
          "iri ": "33131404-e58e-12bc-170e-32aba1c83d99 ",
          "name ": "2021 "
        }
      ],
      "descriptors ": [
        {
          "label": "explorative scenario ",
          "class": "http://openenergy-platform.org/ontology/oeo/OEO_00020248 "
        },
        {
          "label": "policy scenario ",
          "class": "http://openenergy-platform.org/ontology/oeo/OEO_00020309 "
        },
        {
          "label": "climate scenario ",
          "class": "http://openenergy-platform.org/ontology/oeo/OEO_00030007"
        }
      ],
      "input_datasets": [
        {
          "key": "f2d32e9c-1fa0-4d66-9ffd-c297d4bb5c9a ",
          "idx": 0,
          "value ": {
            "label ": "abbb_transmission_capacity ",
            "iri ": "https://openenergy-platform.org/dataedit/view/scenario/abbb_transmission_capacity "
          }
        },
        {
          "key ": "ca9c82f3-9ba0-7d71-6601-dd520680bedb ",
          "idx ": 1,
          "value ": {
            "label ": "abbb_demand ",
            "iri ": "https://openenergy-platform.org/dataedit/view/scenario/abbb_demand "
          }
        }
      ],
      "output_datasets ": [
        {
          "key ": "0db015dd-1543-f0e9-9579-3602fb16a680 ",
          "idx ": 0,
          "value ": {
            "label ": "abbb_transformer ",
            "iri ": "https://openenergy-platform.org/dataedit/view/scenario/abbb_transformer "
          }
        }
      ]
    },
    {
      "id ": "1f4bb594-4b1c-dca4-2465-e04a54eec10b ",
      "name ": "Example scenario name 2 ",
      "acronym ": "Example scenario acronym 2 ",
      "abstract ": "Example scenario abstract 2 ... ",
      "regions ": [
        {
          "name ": "France  ",
          "iri ": "https://www.omg.org/spec/LCC/Countries/ISO3166-1-CountryCodes/France "
        }
      ],
      "interacting_regions ": [
        {
          "name ": "Germany  ",
          "iri ": "https://www.omg.org/spec/LCC/Countries/ISO3166-1-CountryCodes/Germany "
        }
      ],
      "scenario_years ": [],
      "descriptors ": [
        {
          "label ": "explorative scenario ",
          "class ": "http://openenergy-platform.org/ontology/oeo/OEO_00020248 "
        },
        {
          "label ": "with additional measures scenario ",
          "class ": "http://openenergy-platform.org/ontology/oeo/OEO_00020312 "
        },
        {
          "label ": "greenhouse gas emission scenario ",
          "class ": "http://openenergy-platform.org/ontology/oeo/OEO_00020317 "
        },
        {
          "label ": "climate scenario ",
          "class ": "http://openenergy-platform.org/ontology/oeo/OEO_00030007 "
        },
        {
          "label ": "economic scenario ",
          "class ": "http://openenergy-platform.org/ontology/oeo/OEO_00030008 "
        }
      ],
      "input_datasets ": [
        {
          "key ": "bfc811ee-11f5-6a5a-247d-6f66bb676dd9 ",
          "idx ": 0,
          "value ": {
            "label ": "abbb_transformer ",
            "iri ": "https://openenergy-platform.org/dataedit/view/scenario/abbb_transformer "
          }
        }
      ],
      "output_datasets ": [
        {
          "key ": "fbc30f51-7f32-9c21-dfb2-7534aeac538d ",
          "idx ": 0,
          "value ": {
            "label ": "ego_slp_parameters ",
            "iri ": "https://openenergy-platform.org/dataedit/view/scenario/ego_slp_parameters "
          }
        }
      ]
    }
  ],
  "models": [
    {
      "id ": "SciGrid: Open Source Reference Model of European Transmission Networks for Scientific Analysis ",
      "name ": "SciGrid: Open Source Reference Model of European Transmission Networks for Scientific Analysis "
    },
    {
      "id ": "Balmorel ",
      "name ": "Balmorel "
    },
    {
      "id ": "National Electricity Market Optimiser ",
      "name ": "National Electricity Market Optimiser "
    },
    {
      "id ": "urbs Bavaria ",
      "name ": "urbs Bavaria "
    }
  ],
  "frameworks": [
    {
      "id ": "Python for Power System Analysis toolbox (PyPSA) ",
      "name ": "Python for Power System Analysis toolbox (PyPSA) "
    },
    {
      "id ": "Framework for Integrated Energy System Assessment ",
      "name ": "Framework for Integrated Energy System Assessment "
    },
    {
      "id ": "Model Order Reduction for Gas and Energy Networks ",
      "name ": "Model Order Reduction for Gas and Energy Networks "
    },
    {
      "id ": "OMEGAlpes ",
      "name ": "OMEGAlpes "
    },
    {
      "id ": "Potsdam Integrated Assessment Modeling Framework (PIAM) ",
      "name ": "Potsdam Integrated Assessment Modeling Framework (PIAM) "
    }
  ]
}
```
