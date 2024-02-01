### Changes

- Publish Options for Draft Tables: Implemented hidden publish options for draft tables, visible only for reviewed and unpublished tables.  [(PR#1526)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1526)

- Publish Options for Draft Tables: Added a schema selection dropdown and a confirm publish button to enhance user interaction in the draft tables section.  [(PR#1526)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1526)

- API Functionality Expansion for Publishing Status: Enhanced the API with update_publish_status function, allowing the change of a table's publish status.  [(PR#1526)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1526)

- API Functionality Expansion for Publishing Status: Updated the OEDBTable query action to utilize set_is_published, streamlining the table publishing process.[(PR#1526)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1526)

- UI Feature for Publishing Draft Tables: Developed a new UI feature enabling users to publish draft tables directly from the interface.  [(PR#1526)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1526)

- UI Feature for Publishing Draft Tables: Integrated JavaScript to handle publish actions, including schema selection and confirmation steps, ensuring a seamless user experience.  [(PR#1526)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1526)

- The oemetadata on the oep is now stored including null / none values. Users reported that it otherwise is confusing and hinders there metadata workflow. This is related to the update in [omi v0.2.0](https://pypi.org/project/omi/0.2.0/) [(PR#1541)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1541)

- Update schema.json for metaEdit module and update omi version in requirements.txt. This change makes the metadata edit / download results more robust. [(PR#1550)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1550)

- Scenario Bundle: Add more tooltips in scenario tab  [(#1555)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1555)

- Enhance the ontology/oeo pages based on user feedback [(#1552)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1552)

- Improve the profile tables page and adjust the data publishing feature so that it is less strict and only checks for an open license and does not require a full open peer review. Tables that are already published (not in model_draft) are also checked, but only a warning is displayed if the open license is missing. [(#1565)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1565)

### Features

- Add a htmx based page loading after initial page is visible to the user. [(#1503)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1503)
- Scenario Bundle: Sort scenario years in ascending order [(#1557)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1557)

- Add http api list endpoint for factsheets (both framework & model) and datasets in the scenario topic [(#1553)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1553)

- Introduction of an automatic license check module that attempts to check whether the license specified in the metadata for a particular table is open. It normalises the license name in the metadata (whitespaces become "-", everything is capitalised) and compares it with the official SPDX license list. [(#1565)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1565)

### Bugs

- Scenario Bundles: Fix repeated DOIs [(#1556)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1556)

- Clicking on tags opens a list of tagged tables again [(#1561)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1561)

### Removed
