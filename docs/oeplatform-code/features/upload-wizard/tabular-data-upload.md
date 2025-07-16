<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Upload

The process op uploading data to the oep is implemented in the OEP-WEB api and can be used via rest entirely. Recently some required enhancements have been identified and the API will be updated, old endpoints are redirected to prevent breaking 3rd party code.

More extensive testing will be introduced and some datasets related new endpoints are added. The core functionality which can be used to create tabular data resources in the postgresql database must be optimized but will be one of the main parts of the feature described in this section.

Building on the existing functionality and the collective feedback from its users we will rework the upload UI. In the end the OEP website implements a UI which uses all available api endpoints making the process of creating data less technical. This also adds a visualization for the data management as datasets which consist of multiple data resources can be edited and managed in general. We currently work out the details but it becomes clear that some parts of the ui will be relevant during creating and then later to come back and edit or extend the information which might require being able to reuse some ui elements in other pages of the oeplatform.

The interface can offer a central dashboard to create and maintain datasets to gain a very good data quality. Adding extensive metadata lining the resource to external objects or attaching them to scenario bundles helps to build a linked information object which in the end offers all information required to be transparent in use, reusable regarding license information and in general understandable.

## Method

We use an http api request/response cycle which requires batching requests for larger uploads.

There is an UI which enables uploading CSV datasets to the OEDB and registering the data resource in the OEP data-management system. Especially the creation of OEMetadata and Datasets is important on a low level. To extend this we will have to wait until we implement organizations and projects who wrap datasets and single table resources to establish a storage structure which reflects the linage and data grouping information. Data can then be identified by contributor, project and an extensive collection of metadata keys from the oemetadata available for a resource.

Reflecting on the point in time when a dataset or data resource is published it would be best to let the user actively decide at what point they want to submit it to bew reviewed. This would then also help the review process which would require a actively submitted request for review. This is similar to GitHubs pull requests. We dont need Review requests with draft states as all data will be in a draft state first. It should also be possible to review data which was not submitted for review but only as an option not in a highlighted way as when a review is requested.

Overall this leads to a coherent process of creating data providing descriptive metadata and then considering the data resource complete. For validation and general data and metadata quality checks then the community or specific reviewers can participate in reviews. Which should lead to good quality data repositories.

Some special functionality which was introduced during the SIROP project can also be placed prominently to enhance visibility and usability of such functionality. Especially for data annotation, subject (topic) annotations and linkage to the databus this rework should be a huge benefit. Adding the option to fill such information assets during the creation step of the data resource but only requiring a small amount of metadata. By also adding a quick action option we also enable user to just create a table resource and do all the other stuff later on. This is full flexibility which is only possible once the OEDB - OEP schema coupling is solved moving all further data structuring into the OEP application logic making all layers between database/table resource virtual keeping is simple to enable very less restrictive database usage. This still requires minimal validation to confirm the submitted data meets the technical requirements.

## UI

The main subject to restructure is the UI it will have to provide a clear, structured workspace to manage creating a dataset including multiple data resources and describing the data as tabular data structure enabling creating SQL and oemetadata compliant resource description which can be created on the OEDB (Postgresql table).

UI Elements

- Guide the User: Steps & Progress
- Detailed Interfaces dor each step:

    - Dataset information
    - Metadata Template (apply for all resources, add specifics later)
    - Add resource (setup table, upload form datapackage or csv, Setup data annotations)
    - User Review (show recommendations and errors in metadata) and submit for peer-review or keep in draft

- Offer Quick action to create a table resource without dataset information just by name and table structure (as it is currently)
- Link to external information like academy, specifications & show api endpoints for every section element?
