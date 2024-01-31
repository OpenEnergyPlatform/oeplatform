### Changes

- Publish Options for Draft Tables: Implemented hidden publish options for draft tables, visible only for reviewed and unpublished tables.  [(PR#1526)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1526)

- Publish Options for Draft Tables: Added a schema selection dropdown and a confirm publish button to enhance user interaction in the draft tables section.  [(PR#1526)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1526)

- API Functionality Expansion for Publishing Status: Enhanced the API with update_publish_status function, allowing the change of a table's publish status.  [(PR#1526)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1526)

- API Functionality Expansion for Publishing Status: Updated the OEDBTable query action to utilize set_is_published, streamlining the table publishing process.[(PR#1526)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1526)

- UI Feature for Publishing Draft Tables: Developed a new UI feature enabling users to publish draft tables directly from the interface.  [(PR#1526)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1526)

- UI Feature for Publishing Draft Tables: Integrated JavaScript to handle publish actions, including schema selection and confirmation steps, ensuring a seamless user experience.  [(PR#1526)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1526)

- The oemetadata on the oep is now stored including null / none values. Users reported that it otherwise is confusing and hinders there metadata workflow. This is related to the update in [omi v0.2.0](https://pypi.org/project/omi/0.2.0/) [(PR#1541)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1541)

- Update schema.json for metaEdit module and update omi version in requirements.txt. This change makes the metadata edit / download results more robust. [(PR#1550)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1550)

- Enhance the ontology/oeo pages based on user feedback [(#1552)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1552)

### Features

- Add a htmx based page loading after initial page is visible to the user. [(#1503)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1503)

- Add http api list endpoint for factsheets (both framework & model) and datasets in the scenario topic [(#1553)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1553)

### Bugs

### Removed
