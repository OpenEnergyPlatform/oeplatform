<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>

SPDX-License-Identifier: CC0-1.0
-->

# API to manipulate dataset for in a scenario

## Basics

This functionality is part of the oeplatform web api and can be accessed sending POST requests to this endpoint:

- `https://openenergyplatform.org/api/v0/scenario-bundle/scenario/manage-datasets/`

You need a client to send http requests.

- Python: requests
- linux: curl
- Client software: HTTPie
- and more

For authorization you must use you API Token which can be optioned form the profile page on the OEP. In case you leaked it you can also reset the token. See section Access restrictions and future consideration.

The post request must contain a body with payload:

``` json
{
  "scenario_bundle": "1970ba29-155b-6e70-7c22-c12a33244a24",
  "scenario": "5d95247d-df75-a95b-7286-dd4b3bc1c92a",
  "datasets": [
    {
      "name": "eu_leg_data_2017_eio_ir_article23_t3",
      "type": "input"
    },
    {
      "name": "testetstetst",
      "type": "output"
    },
    {
      "name": "WS_23_24_B665_2025_01_23",
      "external_url": "https://databus.openenergyplatform.org/koubaa/LLEC_Dataset/WS_23_24_B665_2025_01_23/WS_23_24_B665_2025_01_23",
      "type": "output"
    },
  ]
}
```

- scenario_bundle: can be obtained from the scenario bundle website (copy from url)
- scenario: can also be obtained from the website; In the scenario tab there is a button to copy each scenario UID
- datasets: Is a list of all datasets you want to add
- name: you can lookup a table name that is available on the OEP and published in the scenario topic. The technical name is required here.
- type: Chose either "input" or "output" here, the dataset will be added to the related section in the scenario
- external_url: This parameter is OPTIONAL to be precise you dont have to use it if you are adding a dataset that is available on the OEP. You can use it to link external datasets but it requires you to first register them on the databus to get a persistent id. The databus offers a Publishing page. After the dataset is registered you can copy the file or version URL and add it to the external_url field.

- <https://databus.openenergyplatform.org/app/publish-wizard>
- The databus also offers a API in case you want to register in bulk

## Example using curl

``` bash
curl --request POST \
  --url https://openenergyplatform.org/api/v0/scenario-bundle/scenario/manage-datasets/ \
  --header 'Authorization: Token <YOUR TOKEN>' \
  --header 'Content-Type: application/json' \
  --data '{
  "scenario_bundle": "1970ba29-155b-6e70-7c22-c12a33244a24",
  "scenario": "5d95247d-df75-a95b-7286-dd4b3bc1c92a",
  "datasets": [
    {
      "name": "eu_leg_data_2017_eio_ir_article23_t3",
      "type": "input"
    },
    {
      "name": "testetstetst",
      "type": "output"
    },
    {
      "name": "WS_23_24_B665_2025_01_23",
      "external_url": "https://databus.openenergyplatform.org/koubaa/LLEC_Dataset/WS_23_24_B665_2025_01_23/WS_23_24_B665_2025_01_23",
      "type": "output"
    },
    {
      "name": "first_test_table",
      "type": "output"
    }
  ]
}'
```

## Access restrictions and future consideration

Currently only the person who created a scenario bundle is able to edit its content. Soon this will change and users will be able to assign a group to a bundle. Groups are also used to manage access to dataset resources on the OEP here we will use the same groups. Once this is implemented you will have to create/assign a group to you bundle and then you can collaborate on the editing.
