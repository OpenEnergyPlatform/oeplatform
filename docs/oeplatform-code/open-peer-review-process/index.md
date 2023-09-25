Developer documentation of the Open Peer Review Process 
=======================================================

Purpose and Objective of the Code:
---------------------------------

This code is part of the Open Peer Review Process system and is responsible for working with JSON schemas and loading metadata. The PeerReviewView class includes methods for loading a JSON schema, parsing keys, and loading metadata from the database. This code serves to ensure the correct structure, validation of metadata, and data processing during the review process.

<ins>Used Libraries and Technologies:<ins>

>1. Python: The programming language in which the presented code is written.
>2. JSON: The data format used for structuring metadata.
>3. Django: The code is likely developed based on the Django framework, as it contains classes and methods characteristic of this framework (for example, LoginRequiredMixin and View).
>4. Special libraries and modules: The presence of OEMETADATA_V160_SCHEMA and load_metadata_from_db indicates the use of additional libraries or modules specific to the project.

Description of the Review Process for Users
-------------------------------------------

>**Uploading Metadata:**
Any registered user can upload metadata to the database page in the model_draft schema.

>**Review Process:**
Other users, who are not the authors of the metadata, can review each field of the metadata. The reviewer has three possible actions:  
> <span style="text-decoration: underline;">Accept:</span> Agreeing with the current data of the field   
> <span style="text-decoration: underline;">Suggest:</span> Proposing corrections for the field  
> <span style="text-decoration: underline;">Deny:</span> Rejecting, if the field does not meet the criteria or is not appropriate in content

>**Author’s Feedback:**
The author of the metadata can view the reviewers' feedback on their page and respond to it, either agreeing with the suggestions or proposing their own changes.

>**Interaction and Agreement:**
The reviewer and the author continue interacting until an agreement is reached and all fields obtain the accept status. A response can only be sent after evaluating all fields that do not yet have the accept status.

>**Choosing Badge and Updating Metadata:**
After all fields are agreed upon, the reviewer selects the appropriate badge, and the metadata in the JSON file is updated accordingly.

>**Exclusivity of the Process:**
If the review process has already begun, other users cannot join it until it is completed.


Table of contents:
-----------------

**Class PeerReviewView**

Description:
>The PeerReviewView class is designed for processing and managing the viewing and reviewing of metadata associated with a specific table. This class provides methods for loading and analyzing metadata, sorting them by categories, obtaining field descriptions, and handling requests for viewing and submitting reviews.

Purpose:
>The main purpose of this class is to provide tools for user metadata review and for updating metadata based on proposed changes.

Methods:
>1. load_json(self, schema, table)
Loading metadata from the database.
>2. load_json_schema(self)
Retrieving the JSON schema for metadata. 
>3. parse_keys(self, val, old="")
Parsing keys from a dictionary or list of metadata. 
>4. sort_in_category(self, schema, table)
Sorting metadata by categories and adding suggestions and comments from the reviewer. 
>5. get_all_field_descriptions(self, json_schema, prefix="")
Collecting descriptions, examples, and badge information for each field of metadata from the JSON schema. 
>6. get(self, request, schema, table, review_id=None)
Handling GET requests for displaying the review page. 
>7. get_review_for_key(self, key, review_data)
Retrieving review data for a specific key. 
>8. recursive_update(self, metadata, review_data)
Recursively updating metadata based on review data. 
>9. set_nested_value(self, metadata, keys, value)
Setting a nested value in metadata. 
>10. post(self, request, schema, table, review_id=None)
Handling POST requests for saving or submitting a review.

**Class PeerReviewContributorView**

Description:
>The PeerReviewContributorView class inherits from PeerReviewView and extends its functionality to handle viewing and participating in the review process from the perspective of the metadata author. This class provides methods for processing requests for viewing and submitting contributions from participants.

Purpose:
>The purpose of this class is to provide additional mechanisms for managing participant interaction in the process of reviewing metadata, as well as for processing and saving their contributions.

Methods:

>1. get(self, request, schema, table, review_id)
Handling GET requests to display the contributor's contribution page.
>2. post(self, request, schema, table, review_id)
Handling POST requests for saving or submitting a contributor's contribution. 


Database Interaction
--------------------

**class PeerReview Model**

Purpose and Application:
>The PeerReview model is designed to store and process data related to the metadata review process. It is used during the creation, update, and analysis of reviews at various stages of the review process.

Main Fields:
>1.table (CharField): Stores the name of the metadata table.  
2.schema (CharField): Contains the name of the database schema.  
3.reviewer (ForeignKey to User): Reference to the user performing the review.  
4.contributor (ForeignKey to User): Reference to the user who is the author of the metadata.  
5.is_finished (BooleanField): Flag indicating the completion of the review process.  
6.date_started (DateTimeField): Date and time when the review started.  
7.date_submitted (DateTimeField): Date and time when the metadata was submitted for review.  
8.date_finished (DateTimeField): Date and time when the review was completed.  
9.review (JSONField): JSON structure containing review data.  

**class PeerReviewManager Model**

Purpose and Application:
>The PeerReviewManager model serves to manage the review process and track its state. It is applied to determine the current reviewer, the status of the review, and to filter reviews based on various parameters.

Main Fields:
>1.opr (ForeignKey to PeerReview): Reference to the associated review.  
2.current_reviewer (CharField): Indicates who is the reviewer at the moment (contributor or reviewer).  
3.status (CharField): Current status of the review (saved, submitted, finished).  
4.is_open_since (CharField): The number of days since the review started.  
5.prev_review (ForeignKey to PeerReview): Reference to the previous review in the process.  
6.next_review (ForeignKey to PeerReview): Reference to the next review in the process.  

**SQL Queries**
>The application utilizes Django ORM for forming and executing SQL queries, ensuring safety and convenience in database interaction. In particular, the filtering methods in the PeerReviewManager model generate complex SQL queries to extract the required data from the database.  


Error handling and exceptions
-----------------------------

1. AJAX Requests Handling:
>The code utilizes AJAX requests for interacting with the server. Errors arising during these requests are handled using error callback functions, where the error information is displayed to the user through the alert() function. This ensures user feedback in case of server or network issues.  
2. Form Data Validation:
>Before sending data to the server, validation checks are performed to ensure the user-input data is correct. For example, it checks whether the valuearea field is empty. If input errors are detected, the user receives a notification, and the data is not sent to the server.  
3. Exception Handling during JSON Parsing:
>When processing the server's response, expected to be in JSON format, a try-catch block is used to catch exceptions. This prevents application failure if the server returns invalid JSON.  
4. User Feedback:
>In case of errors, users are notified through modal windows (toasts) or alerts. This provides good feedback and lets the user know when something has gone wrong.  
5. Checking Element States:
>Before performing certain operations, the state of elements is checked, such as the presence of specific elements or their attributes. This helps prevent potential runtime errors and enhances the application's robustness.  
6. Error Logging:
>When errors occur, information about them is logged to the developer console using console.log(). This facilitates debugging and helps developers find and fix issues more quickly.  

The general approach involves preventing potential errors through data and state checks, handling exceptions and errors that might occur, subsequently informing the user, and logging for developers.  

Schemas and Data Models
-----------------------

Description:
>The JSON metadata schema describes various data attributes such as identifier, context, sources, spatial and temporal characteristics, resources, and licenses. This structure serves to validate and organize metadata uploaded to the system.  

Key Fields:
>1.id: A URL representing a unique identifier of the data.  
2.@id: A URI that identifies the version of the metadata.  
3.name, title: The name and title of the metadata.  
4.review: An object containing information about the review process and awards.  
5.context: An object including contact details, funding information, and other details.  
6.sources: An array of objects describing data sources and associated licenses.  
7.spatial, temporal: Objects describing the spatial and temporal characteristics of the data.  
8.resources: An array of objects representing data resources and their schemas.  
9.licenses: An array of objects describing the licenses applied to the data.  
10.contributors: An array of objects representing contributors and their contribution to the data.  
11.metaMetadata: An object containing metadata about the metadata, such as version and license.   

Processing and Updating Metadata:
>In the provided code, the recursive_update function recursively traverses the metadata structure and updates field values when necessary. This function is called within the post method of the class, which handles review submission and updates the review status in the database.  
In addition to this, the code includes functions and methods for loading metadata from the database, handling requests for viewing and submitting reviews, as well as updating and saving the review state in the PeerReview data model.

Changelogs
----------

Description:
>The CHANGELOG is a document that contains an organized and dated list of changes made in each version of the project. This list includes updates, bug fixes, new features, and other important notifications for users and developers.  

Purpose:
>The purpose of the CHANGELOG is to provide a clear and concise list of changes for each release, making it easier to track modifications and understand the current state of the project.  

[To view a detailed list of changes for each version, follow the link to the CHANGELOGS folder.](https://github.com/OpenEnergyPlatform/oeplatform/tree/develop/versions/changelogs)  




New Functional Features
-----------------------

1. Badge Calculation and Visualization
>Implementation of functionality for calculating the badge by comparing the filled fields with the metadata schema. Users will be provided with a visualization of the percentage of fields that have an "OK" status, allowing for easier navigation through the review process.  
2. Review Process Optimization
>Introduction of mechanisms for optimizing the review process, including limiting the number of fields requiring human verification. This will allow focusing on the most relevant or error-prone fields, thereby enhancing the user experience and encouraging the completion of the review.  
3. Role of the Accompanying Person
>Addition of a new role "accompanying person," endowed with extended rights of access and management of reviews. The accompanying person will have access to all reviews, be able to delete them, and will have special management tools in the user profile. The role of the accompanying person can be assigned based on the is_staff attribute.  
4. Displaying the Percentage 
>The system will feature functionality to display the percentage of fields that are in an "OK" state out of the total number of fields. This feature will provide users with a quick overview of the progress made in the review process, allowing them to easily assess how many fields have been successfully validated.  

