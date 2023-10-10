Developer documentation of the Open Peer Review Process 
=======================================================

General Description
-------------------
### What is this feature about? 

The Open Peer Review Process system facilitates collaborative review and validation of metadata through user interaction. It includes functionalities for uploading metadata, suggesting corrections, and reaching consensus on metadata fields. The system also features badge assignment and metadata updating upon agreement.  

### Who will use it & What are the use cases?

>1. Metadata Authors: Users who upload metadata for review, interact with reviewers to address suggestions, and make necessary adjustments.  
>2. Reviewers: Users who evaluate metadata fields, propose corrections, and collaborate with authors to reach agreement.  
>3. Accompanying Persons: Users with extended rights to access and manage reviews, potentially overseeing the review process.  

### Use Cases include: 

>1. Collaborative metadata validation and improvement.  
>2. Badge assignment based on field agreement.  
>3. Management and oversight of the review process.  

### What functionality is there (from a user POV, not technical)?

>1. Metadata Uploading and Reviewing: Users can upload metadata, propose corrections, and accept or deny fields.  
>2. Interactive Feedback: Authors and reviewers interact to agree on metadata fields.  
>3. Badge Assignment and Metadata Updating: Upon agreement, the appropriate badge is assigned, and metadata is updated.  
>4. Review Management: Accompanying persons have special tools for review oversight.  

Description of the Review Process for Users
-------------------------------------------

1. Uploading Metadata:  
> Any registered user can upload metadata to the database page in the model_draft schema.  
2. Review Process:  
>Other users, who are not the authors of the metadata, can review each field of the metadata. The reviewer has three possible actions:  
>   *  <span style="text-decoration: underline;">Accept:</span> Agreeing with the current data of the field  
 >  *  <span style="text-decoration: underline;">Suggest:</span> Proposing corrections for the field  
 >  *  <span style="text-decoration: underline;">Deny:</span> Rejecting, if the field does not meet the criteria or is not appropriate in content  
3. Author’s Feedback:  
>The author of the metadata can view the reviewers' feedback on their page and respond to it, either agreeing with the suggestions or proposing their own changes.  
4. Interaction and Agreement:  
>The reviewer and the author continue interacting until an agreement is reached and all fields obtain the accept status. A response can only be sent after evaluating all fields that do not yet have the accept status.  
5. Choosing Badge and Updating Metadata:  
>After all fields are agreed upon, the reviewer selects the appropriate badge, and the metadata in the JSON file is updated accordingly.  
6. Exclusivity of the Process:  
>If the review process has already begun, other users cannot join it until it is completed.  

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

A Meta Description
------------------

### What is the context (what other parts of the OEF are connected)?

This feature is an integral part of the Open Energy Platform (OEP) and interfaces with the database to load and update metadata, thereby ensuring data consistency across various modules of the OEP. It utilizes JSON for structuring metadata and is developed using the Django framework, as indicated by the presence of Django-specific classes and methods such as `LoginRequiredMixin` and `View`. The system integrates with the user permissions module to ensure role-specific access and functionalities. Additionally, it leverages specialized libraries and modules, such as `OEMETADATA_V160_SCHEMA`, to facilitate metadata handling.

Software Architecture & Implementation Details
----------------------------------------------

### Context  

The Open Peer Review Process is designed with a modular and scalable architecture, ensuring seamless integration with existing systems and adaptability to evolving technological requirements. Below, we delve into the technologies utilized and the connections established with pre-existing codebases.  

### Technologies  

1. Python:  
>The backbone of the application, Python is employed for developing core functionalities, defining data structures, and orchestrating interactions between different components.  

2. Django: 
>This high-level Python web framework is used to encourage rapid development and clean, pragmatic design, facilitating the creation of reusable and maintainable code.

3. JSON: 
>JSON plays a pivotal role in structuring and handling metadata, enabling efficient data interchange between the server and client-side components.

4. Jinja2: 
>Leveraged for templating, Jinja2 aids in generating dynamic HTML content, thereby enhancing user interface design and user experience.

5. mkdocstrings: 
>This library is vital for automatically collecting Python docstrings from the source code and rendering them into the project's documentation.

6. Special Libraries and Modules: 
>Libraries such as OEMETADATA_V160_SCHEMA and functions like load_metadata_from_db are integrated for enhanced metadata management and interaction with the database.

### Connection to Existing Code  
The Open Peer Review Process system is meticulously integrated into the Open Energy Platform (OEP). It interfaces with the OEP's database to load and update metadata, ensuring data consistency across various modules. The implementation leverages Django-specific classes and methods, such as LoginRequiredMixin and View, to enforce user permissions and manage user interactions.

Furthermore, the system utilizes existing modules and libraries, ensuring that the metadata adheres to predefined schemas and facilitating interaction with the database. The addition of new functionalities and roles, such as the "accompanying person," is executed in alignment with the established codebase, ensuring that the extended rights and functionalities are seamlessly incorporated.

### Conclusion  
By leveraging a diverse technology stack and ensuring meticulous integration with the existing codebase, the Open Peer Review Process exemplifies a robust and scalable architecture. This design philosophy not only facilitates current operations but also lays a solid foundation for future developments and enhancements.  


Changelogs
----------

Description:
>The CHANGELOG is a document that contains an organized and dated list of changes made in each version of the project. This list includes updates, bug fixes, new features, and other important notifications for users and developers.  

Purpose:
>The purpose of the CHANGELOG is to provide a clear and concise list of changes for each release, making it easier to track modifications and understand the current state of the project.  

[To view a detailed list of changes for each version, follow the link to the CHANGELOGS folder.](https://github.com/OpenEnergyPlatform/oeplatform/tree/develop/versions/changelogs)  

