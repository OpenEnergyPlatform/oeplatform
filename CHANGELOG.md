Modify html either to display title or table name along with schema name(#731)
Changes related to display title along with the table name while rendering
Bump version
Cycle changelog
Fix select_from parser
exclude studies from tag check
Redirect image paths to static files
Merge branch 'feature/static-tutorial-titles' into hotfix/final_workshop2021
Merge remote-tracking branch 'origin/hotfix/upload-wizard-column-mapping' into hotfix/final_workshop2021
always show first id column
allow edit of id in metadata editor
fix column mapping in upload wizard
Reworked static urls and removed build process
Updated examples repository
Merge remote-tracking branch 'origin/feature/icons#722' into hotfix/final_workshop2021
Sort tags by popularity
Fix mixed label colors and names
Add new icon for tutorials #722
Update icon for tutorials #722
Update title colour #722
Fix database spelling #722
Merge branch 'feature/logos#722' into hotfix/workshop2021
Merge branch 'feature/RevampedHomepage' into hotfix/workshop2021
Remove duplicate "Permissions" button
Include new incons in welcome page #722
Add new icons for welcome page #722
Update new OEP logo white #772
Add new OEP icon white for header bar #722
Update about images #722
Rename and move about images #722
Update new image #722
Add new OpenEnergyFamily GroupPhoto #722
Update OEP logo SVG and PNG #722
Update favicon.ico #722
updates the homepage to newer version and changes layout
Updates current.md
corrects a spelling mistake
corrects css from the previous commit
removes: Documentation block, reorganizes: Tutorials block
Include study in tag exemption
Make query builder collapsible
Add horizontal line below filter buttons
Reintroduce button for datapackage download
Reintroduce missing data components
Merge branch 'release/v0.8.0'
Update version
Merge pull request #707 from OpenEnergyPlatform/release/v0.8.0
Extract title before name
Merge branch 'hotfixes/v0.7.1_release_fixes' into release/v0.8.0
Merge branch 'develop' into feature/title_issue
Fix extraction of labels
Merge pull request #689 from OpenEnergyPlatform/feature/FilteredDownload
Merge branch 'develop' into feature/FilteredDownload
Merge pull request #700 from OpenEnergyPlatform/feature/display_metadata_in_content-div
Merge pull request #690 from OpenEnergyPlatform/feature/legal-foo
Merge pull request #695 from OpenEnergyPlatform/fix/framework-factsheets_include_user_feedback
Merge pull request #686 from OpenEnergyPlatform/feature/documentations-addons
Merge branch 'develop' into feature/display_metadata_in_content-div
Fix typo in privacy policy
Merge remote-tracking branch 'origin/develop' into develop
Merge branch 'fix/tutorials_editor_fix_code-blocks' into develop
Remove print statement
Merge pull request #701 from OpenEnergyPlatform/fix/remove_sidebar_from_jupyter_tutorials
Merge branch 'develop' into fix/dataedit-changes
Merge pull request #687 from OpenEnergyPlatform/fix/mirror_schemas
Merge pull request #702 from OpenEnergyPlatform/fix/depricated-link-documentation
Merge pull request #703 from OpenEnergyPlatform/fix/ReferenceSchemaDescriptionUpdate
reverts auto formating
updates current.md
Updates Schema Reference description according to is635
Fix deprectated doc link on top of site #694
remove sidebar fom jupyter tutorials detail view
adds the revamped index html page
improve UI: move meta widget from sidebar to data content
restructure sidebar content
Add todo: include css for syntax highliting
update changelog
add new req. - Pygments
add button to go back
add button to go back
enable fenced code blocks and breaklines
remove duplicate data
Exclude framework version from overview, remove duplicate logo text
Add reminder for open data and tou #157
Remove obsolete datasecurity page #545
Remove link to obsolete legal page #545
Update tou introductions #546
Add link to privacy policy in registration #544
Rename imprint privacy policy #544
Rephrase privacy policy #544
updates Changelog
updates changelog
completes smoke testing
update changelog
fix if scope
Add English tou with disclaimer #546
adds first working implementation
update filters+ text search description text
change behavior when clicking a tag label (that is listed on a table), click now creates http.get for single tag search
Apply http.get parameter to url when click a schema (after user applied filter for tag)
Register schemas in mirror command
Link advanced API and Error pages #335
Add status code description #335
Add link to advanced api #335
Fix provided to display proper title and name
Delete table register on table delete
Make `download` redirects to API
Catch missing tutorial id
Merge remote-tracking branch 'origin/feature/tutorials_img_upload'
Bump version number
Merge branch 'feature/tutorials_img_upload'
Bump version number
Merge remote-tracking branch 'oep2/releases/v0.7.0' into releases/v0.7.0
Make metadata converter more robust
Fix mirror command
Set ontology folder only if unset
Load base directory form settings
Fix table registration
Register table at creation
Catch missing titles in tutorial extraction
Merge branch 'releases/v0.7.0' into feature/tutorial-titles
Merge pull request #682 from OpenEnergyPlatform/bugfix/edit-permission-buttons-677
Merge branch 'releases/v0.7.0' of github.com:OpenEnergyPlatform/oeplatform into bugfix/edit-permission-buttons-677
fixes #677: edit buttons disabled if no permission
Re-add missing field in dataview
remove base url
Add transition method for legacy databases
Merge branch 'feature/tutorials_img_upload' of https://github.com/OpenEnergyPlatform/oeplatform into feature/tutorials_img_upload
fix url
Merge branch 'develop' into feature/tutorials_img_upload
update model
create new model to store uploaded images with id
extend easyMDE options: add image upload icon, activate image upload->https://github.com/Ionaru/easy-markdown-editor#configuration
Create ApiView for image upload endpoint, handels post requests, also attempts to validate the image using pillow, returns the relative file path
add new endpoint rout for image uploads
use model to create id for uploaded image
Fix array field migrations in factsheets
Merge pull request #657 from OpenEnergyPlatform/fix/markdown-escape-html
Merge pull request #625 from OpenEnergyPlatform/fix/framework-fs
Merge pull request #673 from OpenEnergyPlatform/fix/meta_search_659
Merge branch 'develop' into fix/framework-fs
Merge remote-tracking branch 'origin/develop' into fix/meta_search_659
Catch non-existing resources
Update only tables in visible schemas
Add merging migration
Update changelog
Update search index when metadata or tags change
Remove obsolete dependency
Rebase onto develop
Include tags in search
Use prefix match instead of simple one
Fix umlaut handling in search feature
Include metadata in search field
Merge pull request #663 from OpenEnergyPlatform/feature/new_meta_editor
proper tooltips
Merge branch 'develop' into feature/new_meta_editor
Update dataedit/templates/dataedit/dataview.html
Update dataedit/templates/dataedit/dataview.html
Update dataedit/templates/dataedit/dataview.html
Merge pull request #666 from OpenEnergyPlatform/feature/remove_dataedit_page
Merge pull request #648 from OpenEnergyPlatform/fix/readmeUpdate#624
Merge branch 'develop' into feature/remove_dataedit_page
Merge pull request #601 from OpenEnergyPlatform/docs/deployment-pipeline
Merge branch 'develop' into docs/deployment-pipeline
Merge branch 'develop' into feature/remove_dataedit_page
Update changelog
Merge remote-tracking branch 'origin/develop' into fix/dataedit-afterrelease-fixes
Merge pull request #617 from OpenEnergyPlatform/features/download_datapackage_305
Merge branch 'develop' into features/download_datapackage_305
Merge branch 'develop' into docs/deployment-pipeline
Merge pull request #651 from OpenEnergyPlatform/feature/aboutlogos#424
Added sorting
Updating to latest development branch
Merge branch 'develop' into feature/aboutlogos#424
Merge pull request #649 from OpenEnergyPlatform/fix/Inconsistantvariable#623
Merge branch 'develop' into fix/readmeUpdate#624
Merge branch 'develop' into fix/Inconsistantvariable#623
Merge branch 'develop' into feature/aboutlogos#424
Merge branch 'develop' into fix/markdown-escape-html
Merge pull request #655 from OpenEnergyPlatform/fix/frontpage-typo
Comitting Migrations
Revmove dataedit_choices page and link to it #666
Redirect dataedit url to schemas #666
load schem from local static file until schema in metadata repository is updated
Merge branch 'develop' into fix/frontpage-typo
Patch dataedit site content #666
Mention GitHub in Link to OEFamily #664
Rename data in topbar, link it to schemas #664
Link to API doc, not dataedit on frontpage #664
changelog
get metadata directly from github
add field formats
hide / readonly for some elements
fill missing values in metadata so fields show up
add popover also for headings
updated metadata schema from repository
autocorrect simple metadata problems
fix edit metadata reverse url
change button positions
dataview: change edit button
error message
basic api interaction
removed django_jsonform, we use pure javascript library
add buttons
remove old metaeditor view
merged current.md
remoe oem_creator references
merged oem_creator folder into dataedit app
enable save_mode and ecape html, new bug in code blocks with html contend (also excaped), checkbox not rendered as expected
add describtion information in the popover
Rename output datapackage file 2 in api/views.py #305
Rename output datapackage file in api/views.py #305
comments
removing of the dowonload button benaeth the form because it was implemented in the edit JSOn button
Merge pull request #632 from OpenEnergyPlatform/feature/csv-upload-346
ugly monkey patch: convert description into popover
Merge branch 'develop' into feature/csv-upload-346
Merge pull request #653 from OpenEnergyPlatform/feature/dataview-popups-167
Merge branch 'develop' into feature/dataview-popups-167
Fix typo on frontpage #620
fix: validate datatype: only if not empty
added simple validator for new tablename and column names
make sure primary key is not nullable
removed unused function (del)
add changelog
catch missing metadata
add description/unit popover to fields in dataview
Merge branch 'develop' into features/download_datapackage_305
Add empty metadata, rename files
fixed: strict
removed static
Merge branch 'feature/csv-upload-346' of github.com:OpenEnergyPlatform/oeplatform into feature/csv-upload-346
fixed: revoke metadata data url
added download button in json editor
Merge branch 'oem_creator_branch' of github.com:OpenEnergyPlatform/oeplatform into oem_creator_branch
fixed: revoke metadata data url
small layout twaeks
Merge branch 'develop' into feature/aboutlogos#424
add download couldnt figured out how to get the value in the html
removed the description, running test for the output,moved the add bar and put the tool description into the middle
Update current.md
#646: add proper tooltips
replaced question mark with info
Updates README.md and reverts changes to oeplatform/securitysettings.py.default
added downlaod metadata button that uses the API
csv upload: select null value for each column #640
corrects the inconsistant(with readme) variable request
upload wizard: question mark for tooltip #646
csv upload: add delete table option #647
updates Readme for PostGIS installation
added downlaod metadata button that uses the API
comments
UI tweaks, formatting
cleanup, BUGFIX: upload was limited to preview
layout
slightly improved example generator
add titles
fixed papaparse link
remove (None) precision from data type definition
Merge branch 'feature/csv-upload-346' of github.com:OpenEnergyPlatform/oeplatform into feature/csv-upload-346
add papaparse lib, use simple datalist for datatype type hints
Merge branch 'develop' into feature/csv-upload-346
Hotfix link on OEFamily image #631
Description for metadatatool. Download button is still missing.
working version of wizard
add png data to explain the metadata tool , add some feature to summarize it in a easier way (putting away the editjson button) download button and differnts colors for backgroun are still missing
improve how to filter instructions
improved visual presentation
apply array fields to model
add array fields to enable adding mulitple values
fix wrong data output
Remove duplicate input fields frim edit view e.g. Licence, Version, model_name, ...
Removing static tutorial information in favour of parsing meta.json
Adapted file format of meta.json to a list
Generating meta.json with title information on build
add link to go backwards
add consitend naming
Add information on how to work with tags and filter to the sidebar, the user can access the add tags function from dataview/schema, add basic frontend
add link to go backwards
Merge branch 'develop' into fix/dataedit-afterrelease-fixes
change datatype to char
Exclude unreachable fields in openness, add missing input field, mind versions is accessed from two input filds in gernal information and overview
Add missing input field
Merge branch 'develop' into docs/deployment-pipeline
update to choose between string and null at the tool multible item selection at the language section
add default for metada
Merge branch 'fix/framework-fs' of https://github.com/OpenEnergyPlatform/oeplatform into fix/framework-fs
fix broken logo view, 403 might still occur on production? #608
Merge branch 'develop' into fix/framework-fs
add missing other field
add missing form field, add documentation on time formats
add missing form field, add documentation on time formats
add missing fields, add documentation on time formats
change of format from date to string to show 2017-01-01T23:00+01
Merge branch 'develop' into oem_creator_branch
include bootstap4 theme
Restructure form and success button, Add csrf token and include bootstrap4
creating a download button
update requirments with django_jsonforms for travis ci
update current.md and add django jquery in requirments.txt
Creating a new app in django oem_creator Creating an interface for setting  a metadata syntax based on  oemetadata/metadata/latest/metadata_key_description.md and the template in oemetadata/metadata/v140/example.json unnecessary paths in static
include changes and link PR in changelog
Merge branch 'develop' into fix/dataedit-afterrelease-fixes
Bump version
Merge pull request #619 from OpenEnergyPlatform/feature/aboutlogos#424
Merge branch 'develop' into feature/aboutlogos#424
Add proper error messages for invalid table names
Validate table name on table creation
Merge pull request #615 from OpenEnergyPlatform/feature/tutorials-video-mergable
Merge branch 'develop' into feature/tutorials-video-mergable
Merge pull request #622 from OpenEnergyPlatform/fix/tutorial-xss-vulnerability
added min.js
Escape HTML code in tutorial editor
ui collapsable cards
Add "DatatypeMismatch" to transparent errors
Make v0 metadata support more robust
Add test for #621
Properly quote more qualifiers
Properly quote qualifiers in sql string
data types parsing and progress bar
working draft
progress on wizard
Added youtube link conversion
create table buttons
Merge branch 'develop' into feature/csv-upload-346
wizard as django view
only enable wizard on writing permission
moved to namespace wizard
Add missing partner institutes #424
Add MODEX and LOD logo to about page #424
Change name for datapackage file
Add button for datapackage download
Update changelog
Implement download for datapackages
Remove old text from changelog
Translate headings to english
first draft csv upload
reverted first draft for csv upload
upload csv: improved warnings
upload csv UI improvement
minimal implmentation for csv upload web interface using the api
minimal extension to api POST to accept raw csv
Fixed a UX bug, where Create instead of Save was written
Fixed a bug, where tutorials could not be created due to empty TextField
Inital implementation of video content within tutorial section
Merge pull request #489 from OpenEnergyPlatform/feature/tutorials
Remove martor dependency
update requirements
remove martor app from django
Merge branch 'develop' into feature/tutorials
Merge branch 'develop' into docs/deployment-pipeline
Merge branch 'releases/v0.6.3'
Adapt tests and docs to new omi version
Bump version
Add changelog
Merge branch 'master' into develop
Merge pull request #611 from OpenEnergyPlatform/bugfix/oeo-sc-page
Use dynamic url generation
Add trailing slash to url resolv
Merge branch 'develop' into bugfix/oeo-sc-page
Merge branch 'develop' into bugfix/oeo-sc-page
Merge pull request #613 from OpenEnergyPlatform/fix/pw-change-612
Return 404 for unknown ontologies
Add urls that are regularly called but do not resolve
Create metatables after table creation
Render text/plain mail
Remove unused context
Fix variable names for base url in mails
Add missing changelog
Merge branch 'develop' into bugfix/oeo-sc-page
Update version number
Add missing setting to securitysettings
Add Ontology to navigation bar #610
Add question mark #610
Add Daniel to OEO-SC list #610
Fix linebreak link #610
Change defaults for content negotiation
Catch missing files in ontology view
Remove martor due to styling bugs and added martor
Open ontology files in byte mode
Revert direct file use
Use direct file header
Use UTF-8 in responses content type
Use UTF-8 in responses
Encode ontologies to utf-8 before responding
Read file before responding
Set missing URL
Implement import lists in view
Implement iri resolution for imports
Implement iri resolution for submodules
Merge branch 'develop' of github.com:OpenEnergyPlatform/oeplatform into develop
Allow arbitrary resources after ontology
Merge pull request #609 from OpenEnergyPlatform/feature/oeo-steering-committe-subpage
Merge branch 'develop' into feature/oeo-steering-committe-subpage
Fix module handling for ontologies
Implement view area for oeo release
Merge branch 'feature/oeo-steering-committe-subpage' of github.com:OpenEnergyPlatform/oeplatform into feature/oeo-steering-committe-subpage
Add list of SC members to page #598
Add overview for ontologies
Merge branch 'develop' into docs/deployment-pipeline
Remove additional ontology resource
Move OEO overview to seperate page
List ontologies in table
Add oeo url, too
Add oeo prerelease urls
update RELEASE_PROCEDURE
update changelog
update RELEASE_PROCEDURE
Merge branch 'develop' into docs/deployment-pipeline
Update RELEASE_PROCEDURE.md
Merge branch 'develop' into feature/tutorials
Styling of Tutorials migrated to reworked design
Add missing version conversions
Extract reference date from list if necessary
Properly display None ind metawidget
Update changelog
Disallow direct access of study factsheets
Use correct exception in activation form
Update version number
Add missing changes to log
Remove dependency on bool(np.array) from table list
Merge pull request #605 from OpenEnergyPlatform/feature/oeo-steering-committe-subpage
Merge branch 'develop' into feature/oeo-steering-committe-subpage
Use link instead of button for OEO-SC
Merge pull request #606 from OpenEnergyPlatform/feature/oefamily#596
Merge branch 'develop' into feature/oefamily#596
Use correct logos for projects, adjust width
Merge pull request #599 from OpenEnergyPlatform/feauture/ffs-implement-feedback
Merge branch 'feauture/ffs-implement-feedback' of https://github.com/OpenEnergyPlatform/oeplatform into feauture/ffs-implement-feedback
include other fields in ffs, add missing values
add missing other formfiled
Merge branch 'develop' into feauture/ffs-implement-feedback
add missing value
Apply changes in batches
Fix typo #604
Add content from wiki page #604
workaround: avoid renaming model to framework in helptext
Add missing logos #596
Add research projects and missing partners #596
Update About Us #596
Add image of the modules of the Open Energy Family #596
Merge pull request #597 from OpenEnergyPlatform/features/fine-tune-redesign
Update changelog
Allow filter with multiple tags
Replace link text to database
Merge branch 'develop' into feauture/ffs-implement-feedback
Do not close passed connections
Catch context in steams
Close connections after stream closes
Handle errors in cursor wrapper
Fix GeneratorEncoder
Fix tests
Check whether first fetch was successful
Enable server side cursors for API
create new subpage for oeo-s-c
add button to access the oeo-s-c subpage
update urls with oeo-s-c
Fix matching function in operands
add new section and contend
add user documentation
cursor:pointer on table rows
Removing limit from get_tags
Moving Apply Filters and Reset Filters button
update changelog
Update current Changelog
update model fields
update model fields
update model fields
update model fields
update fields, update tooltip text, all data from developement feedback
add new fields from developer feedback
add option to geospatial scope choice
update field model
update requirements
Hide profile management buttons for anonymous users
Fix special characters in alembic
Prevent error on missing fields in metadata
Merge branch 'feature/tutorials' of https://github.com/OpenEnergyPlatform/oeplatform into feature/tutorials
update imports
update imports
reinsert template
new file with martor settings
update imports
import mator settings, small correction
remove migration
remove migration
Create migrations
restrict url access for authenticated user in CRUD views
include user authentication for C~~R~~UD methods
delete unused imports
update package list
add new url, remove deprecate url
change field type
resolve numeric choice field, change markdown-field type
Update documentation
Rename choices
Include link to tutorials app
Fix display of static tutorial title
Fix pep error
Remove delte button from static tutorials-detailview, Change behavior of edit button in statictutorials-detailview
Add tutorial name to display
update requirements
fix ci error
Add more docstrings
Mention missing field in model
Cleanup code
Add Documentation
New entry for tutorials app added via pr 489
Add new Imports, Dynamic tutorials now resolve correctly and return the full dataset as dict, Refactor class name to CreateNewTutorial, Add Generic edit views insted of TemplateView and refactor code, Input to markdownfield is now converted to html and stored in db. this is implemented using markdown2, Edit functionality is now working as expected, Delete function now implemented
Add url name to ListView, New url for delete view, Refactor ViewClass name for NewTutorials to CreateNewTutorials
Code formatting, Add delete
Add options for choices fields, Add new fields to Tutorial model
Add new model fields to form
add static folder tutorials from examples repo have to be retrived and added to the satic folder
add new fields to tutorials table
Add link to edit template from detail template
Move initial queryset inside function, Add new calss with methodes to edit a Tutorial, rename redirect url attribute in class create and edit
Add url edit
Add docstring templates, Retrieve data from django DB, Serialize retrieved data to json formatted, Include new tutorila data to TutorialsList
Add dummy function, Add class attributes for form and redirect destination, Create new post method and restructure get method
Format code, add markdownx field media for mardown preview
Move markdownx url to oeplatform/urls.py
add django-markdown url for tutorials app
create table for model:Tutorial
Reordered routes to match the correct ones
Changed block identifier to new format
Added documentation about the additional build step, which is needed for Jupyter playbooks
New page with form for new tutorial
New form for new tutorial
Fix some pep error, Add exception if tutorial files missing, New view that handels post request from form
Add markdownx url, Add add-tutrorial url
Add new link to add-tutorial page
Add missing Fields according to mockup, Add markdownfield
Add django-markdownx
Fixed bug with notebooks build
Added basic implementation for static notebooks
Added basic implementation of list and detail view for tutorials
Added tutorials app
Added commands to handle examples submodule and build static html files
Merge branch 'develop' into feature/tutorials
Update version number
Transfer descriptions from #526
Split map forms
Merge pull request #581 from OpenEnergyPlatform/fix/view-forms-bootstrap
Merge branch 'develop' into fix/view-forms-bootstrap
Merge pull request #582 from OpenEnergyPlatform/fix/handle-invalid-metadata
Merge branch 'develop' into fix/handle-invalid-metadata
Update documentation link in header
Comment "bundles" card on index page
Merge pull request #577 from OpenEnergyPlatform/feature/fix-tooltips-fs-558
Fix tooltips in factsheets
Use Metadata v1.4 as default if invalid metadata is provided.
Show full metadatastrin in textarea when json error
Merge pull request #579 from OpenEnergyPlatform/features/about-oep-424
Merge remote-tracking branch 'origin/develop' into features/about-oep-424
Align logos in "About OEP"
Add IEE logo
Migrated View Forms to Bootstrap 4
Merge pull request #477 from OpenEnergyPlatform/feature/metadata-api-314
Add missing omi dependency
Merge branch 'develop' into feature/metadata-api-314
Merge pull request #578 from OpenEnergyPlatform/features/what-is-ontology-542
Update current.md
Merge branch 'develop' into features/what-is-ontology-542
Move link to html tag
Add link on front page
Move explanatory text to side-bar and add infos
Show text for non-admins in permission template
Allow null for typical computation time
Add links for all buttons on landing page #424
Add text for landing page #424
Fix typo in profile template
Update texts in password reset mail
Update activation mail
Update base email template
Add edit button to user profile
Merge pull request #541 from OpenEnergyPlatform/features/captcha
Merge branch 'develop' into features/captcha
Fix edit function for scenario factsheets
Shorten Introduction
Use UserManager for user handling
Use UserManager instead of BaseUserManager
Format logo table
Add logos
Add content from #424
A few minor changes
Add text from #542
Add infrastructure for ontology info page
Start ontology app
Merge pull request #543 from OpenEnergyPlatform/feature/django3
Move edit link out of header
Merge branch 'develop' into feature/django3
Merge pull request #534 from OpenEnergyPlatform/fix/factsheets-styling
Merge pull request #539 from OpenEnergyPlatform/fix/dataedit-tag-editing
Merge branch 'develop' into features/captcha
Added Edit button at taggable setting component to be able to edit tags within the dataedit view
Add migration for 3e05a65
Removed Content from Sidebar
Reworked Detail Sites of Factsheets
Merge pull request #537 from OpenEnergyPlatform/fix/group_names_515
Merge pull request #511 from OpenEnergyPlatform/feature/geometry_api_507
Merge branch 'develop' into feature/geometry_api_507
Merge pull request #521 from OpenEnergyPlatform/fix/null-in-maps
Merge pull request #532 from OpenEnergyPlatform/fix/unreleased-xss-vulnerability
Merge branch 'develop' into feature/geometry_api_507
Merge branch 'develop' into fix/null-in-maps
Merge pull request #533 from OpenEnergyPlatform/fix/table-counts
Merge pull request #535 from OpenEnergyPlatform/fix/schema-descriptions
Added missing schema descriptions
Moving Tags into sidebar
Prevent tags from messing with table count
Harden medatada display
Make metadata safe again
Moving Fields into sidebar
Fixing Site Header within Factsheets
Merge pull request #531 from OpenEnergyPlatform/fix/missing-icons
Fixed bug, where the wrong sidebar was shown on the choices page
Replaced glyphicons with Font Awesome icons.
Removed unused css.
Removed unused dataedit/search.html.
Reordering DataView
General Restructuring
remove migration
remove migration
Create migrations
Redirect to activation page after account creation
restrict url access for authenticated user in CRUD views
include user authentication for C~~R~~UD methods
include user authentication for C~~R~~UD methods
delete unused imports
update package list
add new url, remove deprecate url
change field type
remove deprecate installed app, add new installed app
resolve numeric choice field, change markdown-field type
Merge branch 'develop' into fix/null-in-maps
Use django form for group management
Merge pull request #520 from Dhruvin14/fix/Misleading-heading-in-dataedit
Added description
Merge branch 'develop' into fix/Misleading-heading-in-dataedit
Improve metadata docs
Add documentation on metadata API
Adapt tests to raw json api
Use raw json in post requests, too
Call JSON-Parser for metadata
Fixed Filter
Update Changelog
Add more metadata interfaces to API
Add comment option to table creation
Update documentation
Rename choices
Include link to tutorials app
Add case parser to api
Reworked Schema and Table list, moved search to overview list, reworked sidebar in dataedit
Cleaned schemalist and tablelist
Fixed index.html
Skip null in map handling
Fix display of static tutorial title
Fix pep error
Remove delte button from static tutorials-detailview, Change behavior of edit button in statictutorials-detailview
Add tutorial name to display
Update changelog
Merge branch 'develop' into feature/metadata-api-314
Fix script clash in dataedit
Merge branch 'develop' into feature/metadata-api-314
Merge branch 'develop' into fix/Misleading-heading-in-dataedit
Misleading heading in dataedit is fixed.  Close #404
Replace staticfiles by static
Move js to after-body block
Merge branch 'develop' into feature/django3
Merge pull request #498 from OpenEnergyPlatform/feature/recline_alternatives
Remove obolete if-clause
Fix fontawesome to patched branch (temp - #517)
Drop tests for python 3.8
Upgrade postgis version
Upgrade ubuntu version for travis
Remove django-gis from tests
Drop support for python<3.6
Ubdate django version
Move javascript to bottom of file
Translate cursor description to supported format
Replace staticfiles with just static
Add Axes to default auth backends
Remove dependency for django_ajax
Fix basic factsheet for django3
Remove usage of static()
Remove usage of render_to_response
Merge pull request #514 from OpenEnergyPlatform/feature/bootstrap4
Implemented a generated theme within the application
Added Tooling and Documentation for Theming Creation
Merge branch 'develop' into feature/tutorials
update requirements
fix ci error
Delete obsolete template
Merge branch 'develop' into feature/recline_alternatives
Redirect to view after creation
Disable search field in data view
Fix with of data tables
Add view functionality for maps
Fixed Navbars
Applied Bootstrap Migration Guide
Introduced django-bootstrap4 and font-awesome-5 (Broken)
Update requirements.txt
Add issue number to changelog
Add more docstrings
Mention missing field in model
Cleanup code
Add menus for view selection
Compare to None in doctests instead of printing None
Fix typo and import in doctest
Add Documentation
Merge pull request #499 from OpenEnergyPlatform/feature/plotly-graph
New entry for tutorials app added via pr 489
Add new Imports, Dynamic tutorials now resolve correctly and return the full dataset as dict, Refactor class name to CreateNewTutorial, Add Generic edit views insted of TemplateView and refactor code, Input to markdownfield is now converted to html and stored in db. this is implemented using markdown2, Edit functionality is now working as expected, Delete function now implemented
Add url name to ListView, New url for delete view, Refactor ViewClass name for NewTutorials to CreateNewTutorials
Code formatting, Add delete
Add options for choices fields, Add new fields to Tutorial model
Add new model fields to form
New html that confirms a deletion
add static folder tutorials from examples repo have to be retrived and added to the satic folder
add new fields to tutorials table
Fix test in docstring of `try_parse_metadata`
Merge branch 'feature/recline_alternatives' into feature/plotly-graph
Improve display of dataedit.models.View class instances
Fix default value assignment of DataViewModel object
Fix import bug due do multiple definition of class View
Provide the columns id to the dropdown of the graph form
Compare to OMI structure in tests
Allow metadata to be dict or string
Merge pull request #509 from OpenEnergyPlatform/fix/readme_wind_user
Merge pull request #510 from OpenEnergyPlatform/feature/plotly-graph-ajax
Merge branch 'develop' of github.com:OpenEnergyPlatform/oeplatform into feature/metadata-api-314
Adapt how-to documentation to GIS-API
Update changelog
Adapt column description to pass udt_name
Fix passing of values from django to JS
Draw columns from view
Connect plotly graph to API
Save Graph View on form return
Rename the Graph View and Form
Remove TableGraph model
Add link to edit template from detail template
Move initial queryset inside function, Add new calss with methodes to edit a Tutorial, rename redirect url attribute in class create and edit
Add url edit
Update README for windows env variable
Add docstring templates, Retrieve data from django DB, Serialize retrieved data to json formatted, Include new tutorila data to TutorialsList
Merge branch 'develop' into feature/tutorials
Move parsing method from views to actions
Add type handler for geoalchemy types
Add dummy function, Add class attributes for form and redirect destination, Create new post method and restructure get method
Format code, add markdownx field media for mardown preview
Move markdownx url to oeplatform/urls.py
add django-markdown url for tutorials app
create table for model:Tutorial
Merge pull request #502 from OpenEnergyPlatform/feature/doctests_in_ci_481
Merge pull request #505 from OpenEnergyPlatform/fix/rename-contribute
Update changelog
Rename CONTRIBUTE to CONTRIBUTING
Merge pull request #423 from OpenEnergyPlatform/features/streamline-metatables
Exclude black in tox instead of travis
Exclude check env from travis
Remove JS-debugger
Set markers iff map is defined
Reordered routes to match the correct ones
Changed block identifier to new format
Added documentation about the additional build step, which is needed for Jupyter playbooks
Merge branch 'develop' into feature/tutorials
New page with form for new tutorial
New form for new tutorial
Fix some pep error, Add exception if tutorial files missing, New view that handels post request from form
Add markdownx url, Add add-tutrorial url
Add new link to add-tutorial page
Add missing Fields according to mockup, Add markdownfield
Add django-markdownx
Remove print from tests
Improve token handling in tests
Omit npm tests
Add link to create a new graph
Add template for editing TableGraph
Set the columns of the TableGraphForm
Create automatic form for the option of the TableGraph object
Add view for new graph
Merge pull request #458 from OpenEnergyPlatform/feature/design-rework-welcome-page-2
Merge pull request #500 from OpenEnergyPlatform/feature/explicit_columns_484
Merge pull request #501 from Dhruvin14/fix/broken-link-schemas-page
Implement missing api operators
Reformat tests
Reformat docs env
Merge branch 'feature/explicit_columns_484' into feature/doctests_in_ci_481
Merge branch 'feature/explicit_columns_484' into feature/metadata-api-314
Broken schemas link README.md is updated(#453) https://github.com/OpenEnergyPlatform/oeplatform/issues/453
Merge branch 'develop' into feature/metadata-api-314
Merge pull request #493 from OpenEnergyPlatform/feature/add-constraint-table-492
Update changelog
Make columns explicit in select statements
Merge branch 'develop' into feature/add-constraint-table-492
Update current.md
Add token to passenv in tox
Add response to assertion for easier debugging
Name test user in travis
Fix documentatiion for id handling
Create metaschema _sandbox in travis
Create sandbox schema in travis
Retrieve API token and pass it to tox
Use environment variable to retrieve test token
Create TableGraph model
Define a div for graph
Add js function load_graph
Fix type sanity tests
Merge branch 'develop' into feature/doctests_in_ci_481
Update current.md
Merge pull request #495 from OpenEnergyPlatform/feature/api-change-types-494
Inject `_type` into query dicts
Explicitly pass environment variables to tox
Pass environment variables to tox
Remain in root folders during tests
Move runserver to background
Hardwire path to manage.py for travis
Move runserver to travis
Do not use a subroutine in tests
Start server before doctests
Fix doctests
Move doctests to py-environment
Use get instead of indexing for better error messages
Check success of teardown method
Remove reference to old id constraint
Add status code checks to documentation
Check success of teardown method
Add doctests to travis
Fix docs config
Fix another typo
Fix typo
Set defaults in metatable
Add constraint table
Merge pull request #483 from OpenEnergyPlatform/feature/aliases_in_api_482
Merge pull request #460 from OpenEnergyPlatform/hotfix/oedb_nullable_column
Added footer
Merge pull request #480 from OpenEnergyPlatform/feature/docs-badge
Add comments explaining assertions in test teardown
Add comments explaining assertions in test setup
Update api/tests/test_regression/test_issue_482.py
Update api/tests/test_regression/test_issue_482.py
Merge branch 'develop' into features/streamline-metatables
Refactored Template Structure for body
Refactored Head
Make markers clickable
Remove obsolete editor.js
Implement filter functionalities
Merge pull request #488 from OpenEnergyPlatform/fix/windows-install-#487
Update README.md
Merge pull request #469 from OpenEnergyPlatform/feature/add-contribute-#468
Merge pull request #470 from OpenEnergyPlatform/feature/contrib-django-structure
Remove obsolete editor.js
Optimize query handling in table view
Add first recline replacement for tables
Remove obsolete templates
Add issue number to changelog
Update changelog
Add tests for alias handling
Fix for missing alias handling
Fixed bug with notebooks build
Added basic implementation for static notebooks
Fix link in badge
Add badge for docs
Added basic implementation of list and detail view for tutorials
Added tutorials app
Added commands to handle examples submodule and build static html files
Merge pull request #418 from OpenEnergyPlatform/fix/missing_tutorial_links
Merge branch 'develop' into fix/missing_tutorial_links
Circumvent possible injection vulnerability in SQLAlchemy
Add more tests for metadata API
Implement tests for metadata API
Fix cursor handling in metadata methods
Use existing connection for metadata handling
Add OMI requirement
Implement REST-methods for metadata functionalities
Merge branch 'develop' into feature/add-contribute-#468
Add step to pull latest changes
Merge pull request #440 from OpenEnergyPlatform/feature/factsheets
Merge branch 'develop' into feature/factsheets
Fix README.md
Merge pull request #465 from OpenEnergyPlatform/feature/improve-first-install-instructions-#464
Fix typos
Add mention to CONTRIBUTE file
Update header
Add description for django project structure
Add windows command
Rework dummy user section
Merge pull request #461 from OpenEnergyPlatform/feature/api_metadata_#314
Update changelog
Create contribute file
Rework alembic setup
Rework the database section of README instruction
Modify securitysettings.py.default file and .travis.yml for environment variables names
Merge branch 'develop' into feature/improve-first-install-instructions-#464
Rework database setup
Update README.md description and title
Rework virtualenv setup
Create conda file
fixed changelog
added line to changelog
first draft to upload and download metadata via api
bugfix: nullable column in oedb in alembic
Implemented second Welcome Site mockup from Bryan
Merge pull request #452 from OpenEnergyPlatform/release/v0.5.0
Merge branch 'develop' into release/v0.5.0
Merge branch 'develop' into feature/factsheets
Merge pull request #443 from OpenEnergyPlatform/feature/german2english
Merge pull request #441 from OpenEnergyPlatform/feature/metadata_v1_4
Add new migration
Merge branch 'develop' into feature/factsheets
Merge pull request #432 from OpenEnergyPlatform/fix/factsheet-remodel
Fix pasting error #441
Add missing double quotes in metadata widget #441
Add handling of none type None #441
Remove variables names in format string #441
Remove fields assignation after post request
Change formatting of strings for python 3.5
Fix travis error
Update changelog
Detect metadata version before assigning post request values
Implement create_empty function for metadata 1.4
Add metadata template v1.3
Add hidden fields in edit_view, in hidden divs
Add missing semi-columns
Manage clone's last element in the list
Fix bug in the element index extraction
Create a js function to remove an element from a list
Add classes for labels
Remove obsolete code
Create function to add element in lists
Harmonize label assignement
Add functions to format the labels
solve pullrequest remarks
solved pull request remarks
Implement cloning of list element
Remove simple dict fields and add list field for keywords
Add id as argument of create_box
Fix case when user delete an entry in the middle of a list
Modified query_dict mapping to metadata template
Add comments and docstrings
Fix content assignement to nested dicts
Use widget renderer instead of template
Fix relative import
Write a function which merge the query dict into the metadata
Temporarily display lists via widget.py
Add information on the types of metadata fields' values
Modify rendering of "fields" and "licence" fields
Add list of metadata fields which should not be rendered
Refactor comment or comment_on_table with metadata
Take camelCase naming into account #441
Translate German text to English on contact page #442
Make URLs in metadata clickable #441
Merge branch 'develop' into feature/metadata_v1_4
Add list display in metadata edition mode
Add function to render metadata edition automatically
Set "beginners" links to wiki
add hyperlink to OEP-Wiki as Documentation #436
insert About the OEP on landing page #436
Set links to tutorials
Set correct links in welcome page buttons
Comment bundle links
Fixed tile alignment
Fixed Mobile Menu
Fixed styling issues
Work on styles
Started implementing welcome page
Add comments to make code more human-readable
Create a function to get the metadata version of a json variable
Add display for list of string as metadata field value
Add missing migrations
remove comment
Merge branch 'develop' into feature/factsheets
small framework changes
Display metadata automatically, regardless of metadata version
Merge branch 'develop' into fix/factsheet-remodel
Merge pull request #438 from OpenEnergyPlatform/fix/add-missing-migrations
Add missing migrations in develop branch
Merge pull request #437 from OpenEnergyPlatform/feature/ignore-vscode-ide-folder
Ignore vscode ide folder
Merge pull request #433 from Dhruvin14/fix/oep-homepage-link
closes some issues, will reference later
updated framework factsheet
Merge branch 'develop' into HEAD
https://github.com/OpenEnergyPlatform/oeplatform/issues/387 Issue 387 fixed
add makemigrations to .travis
Merge pull request #429 from OpenEnergyPlatform/feature/oedialect
update README to make sure django-bootstrap3 is uninstalled before new version is installed from git in requirements.txt
closes #85 , fixes views
Use more readable tuple concatenation
Merge pull request #430 from OpenEnergyPlatform/feature/metadata-tooltip
update
Merge branch 'develop' into feature/factsheet-remodel
Update changelog
Fix tooltips for dataedit columns
Merge branch 'develop' into feature/oedialect
Merge pull request #428 from OpenEnergyPlatform/fix/update-requirements
Move default schema to security settings
Reformat using black
Add missing types of timestamp and time
closes #84 solves bootstrap3 bug falsely displaying checkbox label
More fine grained handling of temporal data
Move unversioned schema configuration to settings
Fix time handler
Fix quoting for string values
Correctly handle float as FLOAT
Allow kwargs in datatype API
Fix conflict version of psycopg2
Change psycopg2 version
Fix domain handling for SQLAlchemy 1.3
Implement cast expressions
Fix handling for decimals
closes #82
Update requirements.txt
Update requirements.txt
closes remaining issue of #50
closes remaining issues of #38
Quick fix for remaining task of #36
Fix negation in api
Closes #74 -- links to websites in factsheets clickable
quick fix (?) for #401
Merge pull request #422 from OpenEnergyPlatform/fix/remove-tutorials
Update the readme to link to the new location of tutorials
Remove tutorial notebooks
Merge pull request #417 from OpenEnergyPlatform/feature/fix-dev-install
Fix choice for ContactForm
Merge branch 'develop' into features/captcha
Closes #311
Close #311
Merge pull request #415 from OpenEnergyPlatform/hotfix/sqlalchemy_vulnerability
Merge branch 'develop' into feature/fix-dev-install
Add missing link to oep-api tutorials and oep-data-publication tutorial
Fix oedb-like database default name
Highlight deploy section in README
Remove test database description
Update oedb-like database setup in README
Change name of local oep database
Update requirements.txt
Merge pull request #375 from OpenEnergyPlatform/fix-requirements
Reintroduce alembic to requirements
Update django database setup in README
Merge branch 'develop' into fix-requirements
Change name of the default django database
Update README.md
Update requirements.txt to avoid fresh install errors
Remove dependency for sphinxcontrib-spelling
Remove dependency for pyenchant and py37
Use correct python envs in travis
Remove report, codecov, clean from tox
Remove `sphinx.ext.pngmath` from docs
Fix check and docs env in tox
Use django test environment in tox
Remove isort env from tox
Add report env to tox
Add db passwords to travis config
Git use django environment for alembic
Revert a19f8eb9
Fix dataedit-import in alembic environment
Travis: Install dependencies before migration... for real
Travis: Install dependencies before migration
Add requirements to global dependencies
Fix postgis in travis config
Remove dependency for pypi(2)
Fix postgres handling for travis
Setup travis with tox
Reformat with black
Remove comment function
Implement complete table as default view
Plot all geometries loaded from table
Fix dataview
Install egoio from pypi
Merge branch 'master' into develop
Update changelog
Sorting imports
Reformat code using black
Implement captchas for contact form
Overwrite Interval types
Handle domains with tuple keys
Overwrite Interval types
Merge branch 'master' into develop
Use dictionary access to get fields from table objects
Implement distance_centroid operator
Replace remaining mail_address by email
Reset to old domain definition
Use proper field in detachment form
Remove DEFAULT_FROM_EMAIL from settings.py
Add missing type maps in tests
Use dictionary access to get fields from table objects
Implement distance_centroid operator
Update requirements.txt
Merge remote-tracking branch 'origin/develop' into develop
Add migration for nullable messages
Allow NULL in message field
Fix meta search update
Invert popularity order
Fix typo
Add table for meta_search to structures
Add meta_search to alembic
Add tag popularity to alembic
Fix broken merge
Merge pull request #392 from OpenEnergyPlatform/feature/errorMessages
Update changelog
Merge pull request #393 from OpenEnergyPlatform/feature/alembic
Merge remote-tracking branch 'origin/feature/popular-tags' into feature/popular-tags
Merge migrations
add tag usage information to modelview
remove print
Improved popularity rating function
Sort tags by popularity and only show popular tags in popular tags panel
Added counter for tag usage
Merge branch 'feature/alembic' into feature/fix-tag-filter
Also show empty schemas
Actually add metadata structure to base
Move sqlalchemy Metadata to base functionalities
Add migration for_insert_base
Add table_tag migration
Fix tag migration
Add tables tags
Reorder alembic migrations
Merge branch 'develop' into feature/alembic
Merge migrations
Merge remote-tracking branch 'heimbrodt/feature/fix-tag-filter' into feature/popular-tags
Remove disfunctional commit field
Remove obsolete scripts from base template
change text of 500 error message. refers to https://github.com/OpenEnergyPlatform/oeplatform/issues/289
add newline
change texts of error message 500 and add 404 error message relates to issue: https://github.com/OpenEnergyPlatform/oeplatform/issues/289
Replace remaining mail_address by email
Reset to old domain definition
Use proper field in detachment form
Remove DEFAULT_FROM_EMAIL from settings.py
Add missing type maps in tests
Pass anonymous user
Add missing type maps in tests
Fix nullable in table creation
Better error message in tests
Use correct syntax for columns in tests
Merge branch 'develop' into releases/0.4.0
Bump version to 0.4.0
Merge branch 'develop' into hotfix/forgotten_password
Merge pull request #380 from OpenEnergyPlatform/feature/schema-whitelist
Merge pull request #384 from OpenEnergyPlatform/feature/mod-gitignore
Merge branch 'develop' into feature/mod-gitignore
Merge pull request #377 from OpenEnergyPlatform/hotfix/missing-data-#317
Merge pull request #365 from johannwagner/fix/django-version
Merge branch 'develop' into fix/django-version
Merge pull request #386 from OpenEnergyPlatform/feature/validate-column-#349
Merge branch 'develop' of github.com:OpenEnergyPlatform/oeplatform into develop
Merge branch 'feature/travis' into develop
Suppress prompts in travis tests
Fix wrong email field in tests
Use correct syntax for upper bound
Add upper bound for django version
Fix typo in securitysettings
Fix double creation of django db
Merge remote-tracking branch 'origin/feature/travis' into feature/travis
Add setup for oedb to travis script
Use environment variable for django db as well
Restructure securitysettings.py.default
Fix botched merge
Add alembic to travis
Add migrations and alembic folder
Add migration handling by alembic
Fix postgis
Add sudo for postgis installation
Install postgris
Start config for travis ci
raise APIError if any column name is not a valid identifier
added pycharm .idea folder to gitignore
Remove workshop and reorder schema white list #225
add default parameter in settings #379
bugfix: typo
#317 handle dataview alert if table is empty
changes to requirements
Use proper email field in profiles
Add change-mail-function to activation alert
Streamline login forms
Implement 'forgotten password' functionality
Pass NoSuchTableError through API
Merge pull request #359 from OpenEnergyPlatform/feature/bugfix
Adress latest security issue in django
Pass user in do_fetch
Close cursors correctly in close_all
Merge branch 'master' into develop
Require Login for close_all
Extend error message with hint to newer oedialect version
Generate URL-name automatically
Move rollback handling to session handler
Enable users to close all their sessions
Ignore KeyError on subsequently closed queries
Merge branch 'master' into develop
Merge branch 'master' of github.com:OpenEnergyPlatform/oeplatform
Check if connections still exists before closing
Correctly pass user in connection wrapper
Add changelog
Add connection limits to settings
Introduce connection limit
Pass user in internal select
Fix user bound connections in internal select
Set upper bound for django package
Added Documentation for User Creation
Set upper bound for django package
Merge branch 'feature/pooling' into develop
Implement connection pooling
Implement connection pooling
typo in Tutorialnamen
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Simplify regex in url matching
Improve error messages on nonexistent columns
fix links to tutorials in /dataedit #289
fix spelling #289
fix broken link to glossary #257
Fix wording from issue #289 Rephrase "You if you are logged in, you can add tags to this schema to improve the searchability of this dataset." to "If you are logged in, you can add tags to this schema to improve the searchability of this dataset."
Remove obsolete settings
Condense constraint_type-statement and straighten if-clause
Require `type` field if `constraint_type` is missing
Update README.md
Add API to robots.txt
Add API to robots.txt
Replace npmcdn.com with unpkg.com
Add API to robots.txt
Merge pull request #352 from OpenEnergyPlatform/feature/texttypos
Merge pull request #290 from OpenEnergyPlatform/hotfix/typo
Merge pull request #135 from npmcdn-to-unpkg-bot/npmcdn-to-unpkg
Merge pull request #355 from OpenEnergyPlatform/feature/issue289-3
Merge pull request #353 from OpenEnergyPlatform/feature/textwording
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Simplify regex in url matching
Improve error messages on nonexistent columns
fix broken link to glossary #257
Remove obsolete settings
Condense constraint_type-statement and straighten if-clause
Require `type` field if `constraint_type` is missing
Update README.md
Simplify regex in url matching
Improve error messages on nonexistent columns
Actually close cursor
Set LOGIN_URL
Fixed django version and updated code, which was deprecated.
fix typo #289
fix links to tutorials in /dataedit #289
Revert trying to fix activation redirection bug
Try to fix activation redirect bug
Set success_url for password change
Migrate default for is_native to database
fix spelling #289
Merge pull request #354 from OpenEnergyPlatform/feature/glossary
fix broken link to glossary #257
Fix wording from issue #289 Rephrase "You if you are logged in, you can add tags to this schema to improve the searchability of this dataset." to "If you are logged in, you can add tags to this schema to improve the searchability of this dataset."
fix the first typo from #289
Reuse code in meta table creation
add tag usage information to modelview
remove print
Merge branch 'master' into develop
Allow logout in middleware trap
Send activation mail on user creation
Make new users native by default
Remove obsolete settings
Merge branch 'master' into develop
Remove dummy mail
Remove infinite loop if user is neither native nor verified
Commit user in creation
Temporarily remove 'Forgot Password'-Button
Add missing template
Implement verification mails
Require repeated email
Restructure profiles
Rename passed property in profiles
Hide links in foreign profiles
Add form to retrieve information for detachment
Hide token - for real this time
Hide Token by default and add link for password change
Reintroduce missing url resolution for profiles
Remove obsolete urls
Merge branch 'master' into feature/detach_logins
Improved popularity rating function
Sort tags by popularity and only show popular tags in popular tags panel
Added counter for tag usage
Condense constraint_type-statement and straighten if-clause
Require `type` field if `constraint_type` is missing
Update README.md
Merge branch 'develop' into feature/alembic
Cast integer to biginteger to enable filters
Fixed map polygon loading via api
Merge https://github.com/openego/oeplatform into develop
Add redundant argument
Allow loading cursors via flags
Move load_cursor up
Move load_cursor-function to view
Allow executions without cursor_id
Allow dictionaries as expressions
Serialize JSON correctly
Use centralized function for execution of queries
Set pool recycling
Calculate relative path for production
Merge branch 'develop'
Fix bumpversion.sh
Bump version to 0.3.1
Commit on version bump
Show changelogs on index page
Store version in separate file
Add changelogs to changelogs
Use smaller header in versioning
Remove header from version template
Add version handling for change logs
Parse `character_maximum_length` to integer
Add changelogs
Add download functionality for csv
Use proper quoting for csv-return
Implement form='csv' flag for rows
Merge branch 'develop'
Adapt Tests to stream functionality
Move type parsing to separate function
Use streaming function for rows
Commit artificial connections
Close connection decently after applying changes
Introduce playground schemas
Remove spammy logger
Do not close non-artificial connections when no cursor_id was passed
Move parameter to correct function
Remove spammy debug messages
Move streaming to separate function
Fix version for django-axes
Return row sets via streaming response
Set data directly in QueryDict
Use BigInt for BigSerial
Chose columns for primary keys from all possible sources
Use colun clause in return statements
Unpack returning values in insert clauses
Pass schema to permission check
Fix column creation API
Pass connection_id trough contexts
Add missing type handlers for geometry structures and bigserial
Store connection id for artificial connections
Replace immutable dict by a mutable one
Use mutable dict for production
Fix schema handling in permissions handler
Merge branch 'feature/permissions' into develop
Revert changes from 90894d1cba749cb0ecef7f5279f0ab3f0b6b5198
Assert permissions in API methods
Add auto-generated connection id to context
Merge branch 'develop'
Add documentation for condition items
Fold where clauses recursively
Move compound selects to later section
Describe compound selects in sphinx-doc
Check validity of table name iff existent
Fix logging
Log incoming requests in debug log
Validate whether identifiers are strings
Harden SQL-API
Fix advanced/update
Prevent delete from returning a description
Implement Update
Refactor table loading to independent function
Remove obsolete function definitions
Merge remote-tracking branch 'origin/develop' into develop
Merge where clauses into a single list
Use schema when loading tables for column expressions
Add catch for nonexisting tables
Use correct meta tables when applying changes
Merge branch 'feature/dingo_ready_api' into develop
Add missing templatetags
Implement password change
Fix forms for user updates
Add edit forms for user profiles
Detach user creation from openmod
Use blank instead of null for affiliation
Revisit design of snippet modal
Autogenerate snippets for download via python
Add missing sessions handler
FIx compatibility for python 3.4
Use proper function for application of changes
Merge branch 'develop' into feature/dingo_ready_api
Drop unused drop function
Move application of changes on tables to separate function
Store connections and cursor in session context
Directly use Leaflet for drawing maps
Move session functionalities to separate module
Allow selects as expressions
Implement drop command for sequences
Fix literal columns and groupings
Fix insert with from_select
Implement handling for 'in'-operator
Add fallback for missing colums
Use streaming for fetch_many, too
Implement streaming and remember known tables
Fixed dynamic map polygon loading
Implement 'is not' operator
Implement nextval-function
Use sqlalchemy for table creation
Implement autoincrement handling for 'auto' settings
Use default schemas in get_* methods
Unfold elements in group_by-clause
Add concatenation operator
Implement parser for labels
Extend functionalities for operators
Handle groupings in compund selects
Specify dialect for compilation
Implement compound select; Auto-apply delete in sandbox
Implement command `get_columns`
Make 'sandbox' default schema
Avoid cursor clash in change application
Enable reuse of cursors in apply_changes
Use proper id-column for updates; Autocommit in sandbox schema only
typo in Tutorialnamen
Lift requirement that tables neet a column 'id'
Use correct variable for filtering
Filter csv according to tags
Merge https://github.com/openego/oeplatform into develop
Merge pull request #288 from openego/release/0.2.0
Merge pull request #287 from openego/release/0.2.0
Make tutorials more obvious
Merge branch 'master' into release/0.2.0
Prevent non-open-source models from having an open license
Add migration for license change
Prevent non-open-source models from having an open license
Prevent overflowing panels
Merge remote-tracking branch 'origin/feature/tutorial' into release/0.2.0
Merge branch 'feature/fs2csv' into release/0.2.0
Display additional fields correctly
DIsplay error messages on missing fields
Better file name for csv-export
Export fs ordered
Move download button
Implement csv-export for factsheets
Add shapely to requirements.txt
Add missing migrations
Add fields for methodical focus to factsheets
Merge https://github.com/openego/oeplatform into develop
Order tags by name
Show tags in framework fs
Add tag handling to forms in fs edit
Hide model clas fields again
Fix link in FS overview
Move tags to the end of FS list
Limit tags in modelview to 4
Move text to actual tag description
Add link to tag handling to model overview.
Add more explanation to right box in FS
Fix typo in model definition
Simplify model overview
Make fields in modellist more subtle
Add tag handling to framework FS
Merge branch 'master' of https://github.com/openego/oeplatform
Use Modelview base for all factsheet templates
Fix addition of tags on model FS
Prune long strings in overview
Update right panel text according to #213
Update FS-overview texts according to #213
Add default fields accoding to #201
Add tag manager to factsheets
Add missing migration
Prevent header from overlapping content at bottom
Prevent header from overlapping content
Disallow \r
Disallow linebreaks again
Disallow linebreaks
Merge branch 'master' of https://github.com/openego/oeplatform
Use proper ordering for Model FS
Merge pull request #278 from openego/features/factsheet_tables
Move 'add' button to the top
Add list for scenarios
Use proper ordering for Framework FS
Enable Filtering and sorting for Framework-FS
Add missing fields  introduced in 75d9acbe to Factsheets
Add migration for updated model fields
Merge remote-tracking branch 'origin/beritRLI-patch-1' into features/factsheet_tables
Move `help_text` to ArrayField from contained Field
additional help text
Display names should always be visible
Implement filtering by tags
Tags to modellist table
Imlement column selection for model overview
Add all fields to model overview table
check help texts
einige help texte angepasst
Remove settings that hinder initial installation
Add schemas using alembic
Add alembic requirement
Add alembic usage to documentation
Add meta tables to alembic migrations
Add django command for alembic
Initialize alembic setup
Show styled tags in Model Factsheets
Allow tagging and untagging of model FS in edit mode, show tags in ModelFS
Add Tag handling to Factsheet structures
Add a tabular overview to model-FS overview
Add field for license agreement
Remove functionality for unvalidated data
Remove unused jquery file
Remove Javascript files and link to online resources
Check whether requested table exists
Merge pull request #274 from openego/hotfix/270_multiple_conditions
Merge branch 'master' into develop
Use pgerror-code[1] instead of fragile Regex
Add tests for error message for reference of missing columns as discussed in #271
Merge branch 'master' into hotfix/270_multiple_conditions
Add error message of reference to nonexistent column
Add tests for #270
Load where-clauses as lists and handle them as such
Merge pull request #272 from openego/hotfix/271_varchar_condition
Add tests for #271
Fix faulty string handling in value expressions
Use proper logging for sql statements
Return proper metadata on delete
Implement rollback for raw connections
Fixed reference in migration dataedit/0013
Added missing migration dataedit/0013
Merge https://github.com/openego/oeplatform into develop
Change reference from modelview/0035_auto_20160426 to 0035_auto_20170724
Use random identifications for connections and cursors
Use existing functions for cursor creation in internal selects
Fix subsequent selects
Reintroduce delete to advanced API
Disallow CORS on insert
Add commit functionality to connection
Add some hierarchy to API-urls
Replace assertions by Exceptions
Reintroduce insert to advanced API
Lift restriction on id types
Make operator handling case insensitive
Return HTTP400 if table in from item does not exist
Fix close_cursor
add tutorial 4
Format geometries in fetch method
Implement limit handling
Fix handling of groupings in functions
use integer for curser identification
delete html
update notebooks
Allow lists as from items
Implement labeling in clauses
Load connection_id from request
delete not needed files
Merge remote-tracking branch 'origin/master'
Add Error messages for missing functions
Merge branch 'master' into hotfix/error_messages
Add star handling to api
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
included the missing column example in tut 2
Checked for unclear steps and explained them in Tutorial 1
Merge pull request #264 from openego/features/api-arrays
Merge pull request #265 from openego/hotfix/error_messages
Add tutorial for array handling
add link to API tutorial Wiki
add yml for api env
Fix list handling in order_by clauses
divide OEP API tutorial
Merge https://github.com/openego/oeplatform into develop
Added simple optimized loading for map data
Merge pull request #256 from openego/hotfix/error_messages
Return error message on unknown expression type
Merge pull request #255 from openego/hotfix/quote_tables
Merge pull request #254 from openego/hotfix/quote_tables
Quote your stuff properly
Merge pull request #250 from openego/hotfix/error_messages_247
Clean up exception handling
Add comment
Move error handling
Add more error messages
Add migrations and alembic folder
Add migration handling by alembic
Remove unused svn-link
Simplify cors handling
Actually allow CORS on /search
Lift CORS-restrictions on /search subresource
Format the data access choices properly
Remove container class from dataview frame
Add scrollbars to panels
Fix wrong template link
Reintroduced condition lists as conjunctions
Return more error messages
Merge branch 'feature/loading_indicator_237' into feature/api
Rename overview -> choices
Rename overview -> choices
Add loading indicator in model view
Add images
Make API more present on OEP
Remove test syntax from cleanup
Exclude Table deletion from Advanced documentation
Extend documentation on functions
Wrap connection handler in try: finally:
Fix postgis
Add sudo for postgis installation
Install postgris
Start config for travis ci
Doctests for functions
Allow + as a function
Document from items and joins
Allow aliases on all from items
Simplify operator handling
Write about API expressions
Add error message for malformed queries
Handle different request formats
Reference advanced doc in How-To
Start documentation for advanced queries
Use query as keyword for subqueries for consitency
Use list for subqueries
Handle exceptions in advanced API
Merge branch 'develop' into feature/api
Use proper notation levels for headings
Merge pull request #244 from openego/feature/api-errors
Merge remote-tracking branch 'origin/develop' into develop
Merge migrations
Adapt test to enforced id data type
Use get-method in actions.py
Separate handling for API-Internal KeyErrors
Encapsulate connections in try ... finally
Replace unnecessary connection usage
Return error message, if 'new' is used in a PUT-Request
Return KeyError as JSON-Response
Catch missing error message in metadate import
Fix quoting in meta tables
Remove connection pool limit
Merge pull request #243 from openego/hotfix/id_in_api_tables
Merge branch 'hotfix/id_in_api_tables'
Merge pull request #242 from openego/hotfix/group_management_241
Add test for wrong type in  id column
Add test for missing id column
UDT_name is not there (yet)
Fix user removal in groups
Fix user addition in groups
Prevent users from deleting the last admin of a group
Prevent users from changing their own permissions
Prevent doubled entries in group permissions
Require login for list of existing groups
Adapt tests to new API
Compare to result of lower() instead of lower
prevent alternations on id column
Enforce type 'bigserial' on id column
Catch case of missing 'id' column
Fix user removal in groups
Fix user addition in groups
Prevent users from deleting the last admin of a group
Prevent users from changing their own permissions
Prevent doubled entries in group permissions
Require login for list of existing groups
Removed alert
Added tooltip for column description in table
add first tutorial WIP
add heatmap from notebook result
add images
Create readme.md
Created separate database column for filter
Add notes on schemas and permissions
remove unused urls
Merge branch 'develop' into release/v0_1
Fix dump downloads
Merge pull request #235 from openego/wolfbunke-patch-2
Merge pull request #234 from openego/wolfbunke-patch-1
Handle inconsistency in v1.3
Fix translation v1.1->v1.2
Make robust against missing metadata in v0
Catch errors before parsing
Make robust against missing license field in v1.2->v1.3
Fix error handling for faulty metadata
Swap parameters in isinstance
catch case of missing resources
Merge pull request #224 from openego/feature/metadata_v1_3
Use proper labels in metadata edit
Add columns to default comment
Fix handling for metadata v1.3
Fix handling for metadata v1.3
update of text
delete comment
Raise Exception - don't return it
Drop meta tables before dropping tables.
Merge branch 'develop'
Grant admin permissions to admin groups
Introduce admin groups
Catch case that user/group already has a permission object
Refactor permission template
Show only those options that do not exceed the users permission level
Grand admin permissions to admins
Implement autocompletion for group selection
Implement user autocompletion for user selection
Catch anonymous users in permission handling... again
Catch anonymous users in permission handling
Merge branch 'develop'
Adapt js-Backend to new API
Fix  function translation
Translate function handling to sqlalchemy
Add wrapper dictionary to Column.post in doctests
Implement tests for Rows.delete
Implement Rows.delete
Use SQL-Alchemy for data_select
Implement tests for Table.delete
Implement deletion for tables
Use bulk insert to speed up tests
Test bulk insert
Implement bulk insert
Implement tests for api.Column.post
Implement tests for api.Column.post
Implement renaming of tables
Implement permission tests for Tables
Implement permission tests for Rows
Implement permission tests for Columns
Restrict permissions on Column.put
Remove debug output from dataview
check whether user is anonymous to get admin permissions
Use is_anonymous as a function
Move engine handler to separate file
Add missing error file
Move API-exception to separate class
Remove direct parser dependency from actions
Implement test for Rows.get with limit and where-geq
Implement test for Rows.get with offset
Do not restrict schemas for GET-requests except on public and meta-schemas
Implement tests for Column.put
Adapt doctests to API-changes
Do not omit query returned by order_by, limit and offset
Fix tests for Table.post
Fix Column.put query structure and handling of insert and update tables
Unify test structure
Implement schema whitelist for api
Close unused connections, remove parenthesis in groupby-clause
Move schema reset to class setup
Implement tests for Rows.get
Remove print statements
Implement tests for Rows.post
Fix handling of geometries in Row.post
Implement tests for Rows.put including geometries
Fix geometry objects in return values
Add tests for api.views.Rows.put
Harden ubdate_data against injections including keys
Harden ubdate_data against injections
Catch conflicting ids on Rows.put
Add missing test files
Add another user for permission testing
Implement tests for api.views.Table.put
Restructure tests into separate files
Adapt tests to new api structure
Unify the tests into a single function
Merge branch 'develop' into feature/api
Adapt to new ego.io-structure
Use authorisation in tests
Reintroduce missing query
Reintroduce missing query
Adapt doctests to new error messages for constraint violation.
Check constraints on insert table
Merge https://github.com/openego/oeplatform into develop
Implement deletion with separate table
Adapt dtd and ordinal position in regard of _delete-column and add example for delete
Implement delete for rows
use close() in finally-clause when commiting
Proper connection pooling
Do not include row in error message
HowTo: Add examples for ALTER TABLE
Implement Column.post as ALTER TABLE ... ALTER COLUMN ...
Use APIError instead of ValidationError in api.parser
HowTo: Add example table and comments
Comment in evaluation in Doctest
Actually apply changes send via POST
Move id generation to subresource /new
Execute ADD COLUMN commands on the edit table, too
HowTo: Add example for GET-request via id
Implement PUT for columns
Show table structure after inserts
Add parameters to output
HowTo: Add doctests for offset and column
HowTo: Add paragraph on optional parameters
Use regex to parse where clause
Use parameters only if necessary
Secure where clauses against injections
Check whether offset and limit exists before validating them
Allow more convenient  operator syntax in where clauses
Catch "expected" Exceptions in API
Secure Rows.get against injections.
Replace operator EQUAL -> EQUALS
Do not check for None but emptyness
Pass multiple colums or order instructions as lists
HowTo: Write about adding rows via PUT
Use only to ommit inherited rows
Make descriptions on inserts optional
Ad doctest for API-select
Remove interpretation of empty lists as clauses
Make Rows.post return the new id
Add setup and cleanup for doctests
Fix dict-handling in API
Use request.data instead of parsing request.body
Move doctest to the right section
Reintroduce missing import
Merge branch 'develop' into feature/api
Add defaults to validation fields
Merge branch 'master' into develop
Merge branch 'master' into develop
Start doctests for API
Explain why query is still POST
Adabt dataview to new API
Fix cursor wrapper for POST-Requests
Add GET-request that return column descriptions
Introduce APIError-class for consistent Exception handling
Implement REST-conformant GET for specific rows
Auto-grant admin permissions for table creator
Fix objects passes in permission handling
Remove comment tables
Adapt get_X_table_name to new structure
Use DBTable-object to identify table
Add wrapper to all post/put functions
Fix return in permission wrapper
Use right permission levels for permission wrapper
Implement permission wrapper
Fix application of updates
Implement method to apply changes in diff-tables
Implement put for rows
Implement put for rows
Restructure PUT and POST API for rows
HowTo: Fix types in example table and mention primary key
HowTo: Rename model_draft -> example_schema
HowTo: Insert pk constraint for table creation
Make constraint_name optional
HowTo: Select data
HowTo: Insert data
Start how-to documentation
use request.data instead of parsing request.body
Make data insertion a POST-request
Make character_maximum_length and is_nullable optional on create_table
Remove fetch_all field from request
Remove fetch_all field
Dirty fix for brocken data_search
Fix parens for list-like function operands
Fix merge issues
Merge branch 'feature/dingo_ready_api' into feature/api
Configure API-Views as django rest interface
Configure Token Authentication
Restructure imports
Deny permission on drop table
Restructure imports
Remove unused code
Add geoalchemy2 to api
Fix merge
Merge branch 'develop' into feature/api
Require admin permission in order to grant/revoke permissions
Rename 'get_permission_level' to 'get_table_permission_level'
Move permission level detection to respective classes
Use user_id when identifying user to delete
Implement group permissions on tables
Make user permissions on tables work properly
Add missing template
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Reenable model_draft
Merge pull request #231 from openego/feature/group_management
Require Login for Posts
Implement deletions for groups
Add note that users have to login
Redirect after group creation
Show description in group view
Add headers to group management templates
Hide forms user does not habe permission to use
Require permissions for editing groups
Fix wrong links in group member view
Restructure membership list
Display memberships as list
Update Group Management
Implement user permission form for tables
Add migration
Remove Table inheritance
Merge branch 'feature/download' into feature/group_management
Add better structure to group management
Refactor group management
Merge pull request #227 from openego/hotfix/rename_whitelist
Merge branch 'develop' into feature/group_management
Adapt whitelist
Fixed map view with different map projections #222
Remove print statements
Add robots.txt
Require Login for meta_edit
fix typo extent #196
update views.py #196
update views.py #196
add new attributes to dataview for meta_version 1.3 #196
add new attributes for meta_version 1.3 #196
Lock users/IPs after a fixed number of attempts
Remove redundant implementations
Rename legacy to advanced
Add missing imports
Merge branch 'feature/api' into feature/dingo_ready_api
Reformat code
Remove print
Fix condition handling
Remove redundant operator_binary handling in parse_condition
Fix function parser
Implement fetch and grouping
Add cursor handlint
Fix 500 to 404. Referencing Issue #220
Main Functionality implemented. Referencing Issue #220.
Merge pull request #217 from openego/hotfix/close_literature_edit
Require login for factsheets
Merge pull request #216 from openego/hotfix/close_literature_edit
Add submit button to misc field
Merge pull request #215 from openego/hotfix/close_literature_edit
Fix login page
Require login for literature edit
Implement cursor handling
Fixed Tests.  Referencing Issue #210.
Implement missing transaction handlers
Migrate dataedit models
Add revision template
Add download button
Authentication for dumps uses .pgpass
Add file sizes to download page
Implement download template
Improved Revision scheme
Minor changes
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Added filter to data views
Added PUT.  Referencing Issue #190.
Move quote definition to prevent cyclic import
Fix type
Fix missing quotes is select statement, again
Fix missing quotes is select statement
Fix language in index.html
Fix typos and language
Group links in Factsheet image
Hardcode style for mini logo
Remove unfunctional forms
Move image for django magic
Remoe redundant field from contact form
New overview texts for fact sheets
Remove random "xx"
Fix link to factsheets in index.html
Add open_eGo image to about page
Remove placeholders from factsheets
Merge branch 'master' of https://github.com/openego/oeplatform
Merge remote-tracking branch 'origin/master'
Remove placeholders from factsheets
Add text and  image to factsheet overview
Fix typo that hides contributors
Flush dynamic form boxes left
Fix Metadata design
Merge remote-tracking branch 'origin/develop' into develop
Make OEP-flows size relative
Merge pull request #206 from openego/feature/metadata_v1_2
Merge pull request #205 from openego/feature/formulations
Merge branch 'develop' into feature/formulations
Remove Placeholder on Factsheet overview
Add text on schema list
Implement downwards compatibility for initial Metadata version
Implement POST-Requests for Metadata v1.2
Implement view for metadata
Edit list template
Update meta_edit template
Restructure dynamic forms
html-ized the text
Merge remote-tracking branch 'refs/remotes/origin/develop' into develop
Fixed possible crash
Restructured the data-view #185
Merge branch 'feature/formulations' into develop
new text for extra page under discussion
Merge oeplatform illustration into feature/formulations
Change illustrating SVG's size
Replace OEP logo with illustrating SVG
Add links to illustration SVG
Put oep illustration under version control
Merge remote-tracking branch 'origin/feature/formulations' into feature/formulations
Add static files to index.html
Merge branch 'feature/formulations' into develop
Structure logos in "About us"
Fix merge
Add load staticfiles to index.html
Merge pull request #203 from openego/feature/formulations
Merge branch 'develop' into feature/formulations
spelling and grammar mistakes; deleted my questions
Edit text on literature overview references #174
Add separate page for  discussions closes #174
Merge remote-tracking branch 'origin/feature/formulations' into feature/formulations
Add Links to Open Data / Open Knowledge closes #174
Merge branch 'feature/impressum' into feature/formulations
about link added
deleted Project partners, you ll find this information the the "about" page
Merge remote-tracking branch 'origin/feature/impressum' into feature/impressum
Add page for internal server errors closes #121
Minor Changes on phrasing
Merge remote-tracking branch 'origin/develop' into develop
Divide contact form into technical and misc matters Referencing  #194
Merge branch 'feature/formulations' of https://github.com/openego/oeplatform into feature/formulations
Dropdown for wiki and glossary
Update index.html
add text to first sentence
Change color of  profile links
update text
New Text
minor spelling mistake
Add separate texts for FS lists
Changes of my changes - cut the first sentence in two
Merge branch 'feature/impressum' of https://github.com/openego/oeplatform into feature/impressum
Merge branch 'feature/impressum' of https://github.com/openego/oeplatform into feature/impressum
First review - relation openmod - eGo adapted
Initial Tex
Merge remote-tracking branch 'origin/feature/impressum' into feature/impressum
Fixed Operators.  Referencing Issue #190.
Merge branch 'master' of https://github.com/openego/oeplatform
Merge pull request #192 from openego/hotfix/broken-mw-package
Merge pull request #191 from openego/hotfix/broken-mw-package
Only superusers can  delete tags
Only superusers can  delete tags
Comment authentication interface
Replace broken mediawiki package in login app
Added documentation for GET.  Referencing Issue #190.
Added optional parameters.  Referencing Issue #190.
Added support for get data from tables. Changed response_dict.  Referencing Issue #190.
logo and links from openegoproject.wordpress.com
change of text
Added documentation. Referencing Issue #184.
Added exception logging. Added exception storage in database. Added exception display. Removed disabled button. Referencing Issue #184.
Added CREATE TABLE Documentation. Added Rollback for failed database interactions. Fixed some naming issues. Reworked CREATE TABLE, now uses constraint definitions.  Referencing Issue #184.
Add placeholders for logos
Merge branch 'feature/api' of https://github.com/openego/oeplatform into feature/api
Documentation Part 1. Referencing Issue #184.
Merge branch 'hotfix/fix-unittest-mocking' into develop
Merge branch 'hotfix/fix-unittest-mocking' into feature/api
Fix recursion error caused by unittest
Merge remote-tracking branch 'origin/develop' into develop
Rename revision to release Closes #143
Rename unchecked to unverified Closes #141
Add osm to white list Closes #140
Fix style of Scenario FS buttons Closes #139
Add titles and logo
Fixed Alignment and Handling of wrong Requests. Referencing Issue #184
Merge branch 'feature/api' of https://github.com/openego/oeplatform into feature/api
Moved API-Changes to sidebar of dataedit. Referencing Issue #184
Reintroduce legacy API
add Names of instituts
Completion Group Management
Adapt impressum References #174
Added Documentation. Referencing Issue #184
Added WebInterface to review API Changes to Columns and Constraints. Referencing Issue #184
Completed Group Management
Reduced Input Values. Fixed NOTNULL Bug. Referencing Issue #184
Changed Error Handling. Referencing Issue #184
Edit Views/Functions
Edit data security clause References #174
Added documentation. Referencing Issue #184
Added rudimentary error handling. Fix of NOT NULL. Referencing Issue #184
Added constraints support. Referencing Issue #184
Added possibility to rename and redefine columns. Referencing Issue #184
Edit  group managment view
Added Session Commit. Referencing Issue #184
Created Put-Method. Referencing Issue #184
Edit form, models and view
Add contact form References #174
Merge pull request #178 from openego/wolfbunke-patch-1
Merge remote-tracking branch 'refs/remotes/openego/develop' into develop
Add Permission and Group-Permission View
Show header in factsheet overview Closes #151
Make schema name in data view a link Closes #159
Order references by name Closes #165
Fix missing JSON-Response in GET-call
Implement GET-Requests for Table structures
Merge pull request #180 from tom-heimbrodt/develop
Merge remote-tracking branch 'refs/remotes/openego/develop' into develop
Only logged in users can change tags
Merge remote-tracking branch 'origin/develop' into develop
Adapt securitysettings.py for local user handling
Update README.md
Implement debug authentication system
Added Tag Management #176
Merge remote-tracking branch 'refs/remotes/openego/develop' into develop
Merge branch 'master' of https://github.com/openego/oeplatform
Merge pull request #179 from openego/develop
Merge remote-tracking branch 'origin/develop' into develop
Show only tables that are accessible
Update contact.html
Update terms_of_use.html
Replace path handling by call to configure
Fix path handling for RTD
Add legal and information pages to base app
Merge remote-tracking branch 'origin/develop' into develop
Add docstrings to login/views.py
Fill index.rst with content
Add docstrings to login/views.py
Add autodoc to api.rst
Add docstrings to modelview/views.py
Add docstrings to api/views.py
Add docstrings to dataedit/views.py
Add AGPL v3 License
Merge remote-tracking branch 'remotes/origin/master' into develop
Merge remote-tracking branch 'origin/develop' into develop
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Add postgres extensions to README.md
Removed `makemigrations` from setup guide
Merge branch 'master' of https://github.com/openego/oeplatform
Remove model_draft from schema whitelist
Remove prints
Merge branch 'master' of https://github.com/openego/oeplatform
Merge pull request #173 from openego/develop
Fix tag duplicates in lists
Merge branch 'master' of https://github.com/openego/oeplatform
Merge branch 'develop'
Merge branch 'master' of https://github.com/openego/oeplatform
Merge remote-tracking branch 'origin/develop' into develop
Use sqlalchemy structures for tag handling
minor correction (one word deleted)
Text adapter to FS and DB
Replace text in right column
Merge branch 'master' of https://github.com/openego/oeplatform
Replace text in right column
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Merge pull request #171 from openego/feature/design
Merge pull request #170 from openego/feature/design
wrong directory
wrong directory
wrong directory
wrong directory
New Design Setup
New Design Prototype
Add files via upload
Move tag handling to oedb
Replace menu entry for discussion
Merge branch 'master' of https://github.com/openego/oeplatform
Merge branch 'develop'
Rename menu entry references, fix online editing
Merge branch 'develop'
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Implement schema whitelist
Merge branch 'master' of https://github.com/openego/oeplatform
Merge branch 'develop'
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Allow anonymous user
Fix table creation via API
Implemented hander for editing metadata
Replace npmcdn.com with unpkg.com
Inital meta data edit
Merge branch 'master' of https://github.com/openego/oeplatform
Merge pull request #131 from openego/develop
Enable filter on fields
Enable sorting in data view
Write explanatory text for table list and data view
Add API to docs
Remove shapely from requirements for RTD
Mock shapely out of RDT
Rename doc folder
Merge branch 'master' of https://github.com/openego/oeplatform
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Migrate changes in login
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Merge branch 'master' into develop
Add tokens to profiles
Merge branch 'master' of https://github.com/openego/oeplatform
Default redirect to main page on login without next
Merge branch 'master' of https://github.com/openego/oeplatform
Merge branch 'develop'
Fix translation to geoJSON in backend
Merge branch 'master' of https://github.com/openego/oeplatform
Merge branch 'master' of https://github.com/openego/oeplatform
Merge branch 'master' of https://github.com/openego/oeplatform
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Speed up label selection
Merge pull request #115 from openego/develop
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Make limit in displayed tags optional
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Fall back to table name on empty label
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Fix label extraction
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
FIx hidden table names
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Show readable labels in table view.
Full metadata support on insert and update
Make different usages of jQuery compatible
Dynamic loading of comments
Move meta table creation to function
Remove comment form
Merge templates for comments and data
Merge branch 'feature/column_editor' into develop
Link to comment table
Input types of grid edits depent on datatype
Add view for comment tables, implement csv-upload
Implement cell edit
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Revisit dump handling
Merge branch 'master' of https://github.com/openego/oeplatform
Fix Exception on tag creation
Merge branch 'master' of https://github.com/openego/oeplatform
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Align tags more naturally
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Revisit tag handling
Merge branch 'master' of https://github.com/openego/oeplatform
Merge branch 'develop'
Add oep user for wiki auth
Merge branch 'master' of https://github.com/openego/oeplatform
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Write edits to _edit meta table
Write edits to _edit meta table
Automatically create meta structures
Dynamic ordering w.r.t. primary key
Refactor parser
Lighten up field descriptions, call count as function
Translate geometry fields to GeoJSON
Remove unnecessary variable assignment and print
Disallow tag creation for anonymous users; Enhance tag contrast
Allow tags on tables, disallow taghandling by anonymous users.
Add common template for tagged elements
Show tags in table lists
Alter text on Sidebar
Remove unused paginator
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Merge branch 'develop'
Link ref_id to corresponding literature
Make solr path a setting
Merge branch 'master' of https://github.com/openego/oeplatform
Merge pull request #108 from openego/develop
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Add tag selection for tables
Add doctype to base/base.html
Add tag filter to search
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Rename label to tag
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Add geoalchemy
Refactor dataedit.view
Remove old structures, sort tables and schemas
Add a description for references
Hide add button for anonymous users
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Remove useless map from search window
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Make robust against missing comment table
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Remove unused template tag import
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Add init files for template tags
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Fix requirements.txt
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Reenable display of comments
Better display of table and schema list
Use REST api  to fetch data in view
Merge branch 'feature/search' into develop
Merge branch 'feature/api' into develop
Set api url
Ease mapping between js objects and json; Minor fixes
Replace whitespaces in api; Minor fixes
Fix bug in data selection
Use recline Multiview
Adapt api to django
Create api documentation
Fix auth backend
Merge feature/literature
Merge feature/data-edit_view
Merge feature/users
Enable BibTeX upload
Add missing files
Implement literature handler
Initial literature app
FIx display of comments
Add missing file
Show comments on table in view
Implement authentication on openmod wiki
Add missing files
Add non-interactive maps to search
Add missing files
Add missing files
Initial Tag setup
Merge branch 'master' of https://github.com/openego/oeplatform
Merge pull request #106 from openego/develop
Remove unused URLs
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Fix missing media root
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Use media root as dump path
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Fix revision download
Add missing properties to security settings
Merge pull request #105 from zarch/fix_requirements
Merge pull request #104 from zarch/fix_settings
Change db variable to dbname
Add missing packages required by dataedit app
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Implement data dumper
Fix style
Implement table paging
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Add recline files
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Fix more hardcoded db names
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Remove obsolete argument
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Fix more hardcoded db name
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Fix wrong hardcoded db name
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Migrate from CKAN to Django
Merge branch 'master' of https://github.com/openego/oeplatform
Merge pull request #79 from openego/release/v0.0.2
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Help text are correctly display when clicking in the blue box
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Study has now  no separate menu point and editing study can be done using the scenario fact sheet
Fixing a bug whith the Assumption section when editing a scenario
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Model validation field have now the correct name
Adding a link to studies factsheets Renamed differents section/fields and fixing some bugs
Splitting Energyscenario factsheet : Fix an error when selecting an existing study
Split of Energyscenario Factsheet
Hide some fields if not estimated is selected and if not check if the fields are filled
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
add missing migration
Import os package to exemplary security settings
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Merge branch 'develop' of https://github.com/openego/oeplatform
Enable upload on framework FS
Merge branch 'master' of https://github.com/openego/oeplatform
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Enable upload in new models, rename transmissions
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Merge branch 'develop' of https://github.com/openego/oeplatform into develop
Fix networks_electricity fields
Merge pull request #53 from openego/release
Merge pull request #52 from openego/release
bash: :x : commande introuvable
Merge branch 'release' of https://github.com/openego/oeplatform
rename 'Empirical Data' tab, restrict image size
bash: :x : commande introuvable
Mention Python3
Merge branch 'release' of https://github.com/openego/oeplatform
enable logo upload
Refactor view code
Merge branch 'release' of https://github.com/openego/oeplatform
Make label classes consistent
Use actually saved model to determine pk
Repair migrations
Allow migrations in ignore file
Add migrations
add missing file
Add output format to models
Represent arrays by several fields
Change "Apporach to uncertainity" add to TextField
Add headlines
Make "Mathematical objective text" nullable
Add field "Supported model types"
Make factsheet design more consistent.
additional software can be null, doc_qual can be 'not available'
Merge branch 'release' of https://github.com/openego/oeplatform
Remove pointers again
Add correct pointer for models and frameworks
Fix 500 error on submit, display model types as options
Merge branch 'release' of https://github.com/openego/oeplatform
Changes in eff is not mandatory
Merge pull request #41 from openego/release
Merge branch 'release' of https://github.com/openego/oeplatform
Use CharFields instead of URLFields
Fix errors in MF coverage tab
Change type of mathematical objective (other) field to CharField
Added other textfield to "approach to uncertainty"
Apply bootstrap css to fields in FS forms
Remove print
Merge branch 'release' of https://github.com/openego/oeplatform
Fix several display errors
Remove print
Merge branch 'release' of https://github.com/openego/oeplatform
Delete obsolete submit buttons on scenarios
Merge branch 'release' of https://github.com/openego/oeplatform
Merge branch 'release' of https://github.com/openego/oeplatform
Delete obsolete submit buttons
Merge pull request #39 from openego/release
More visible errors, relabel and move submit button
Merge pull request #34 from openego/release
Merge pull request #33 from openego/release
Convert checkbox labels to string
Adapt licence field
Allow null as documentation URL
Use TextField for large Inputs
Hide Openness fields, Correct labels
Rename fields in model factsheet
Update README.md
Create README.md
Add comments to default securitysettings
Spell 'Other' consistently, 'new window' icon on external link
Merge pull request #17 from openego/feature/factsheet
Open source toggles hide/show in framework FS
Select fields can uncover text fields
add django specific folders to gitignore
Make github plots more robust
Remove print
Add other fields to integration
Add integration category on models, rename CAES and PHS
Add headings for edit views, new tooltips for frameworks
Redesigned factsheets
Removed 'Does this belong into the scenario fact sheet?'
Fix list representation
Remove 'comma-separated' from factsheets
Restructured factsheet designs
Add comment that design will change
Fix labels on ArrayFields
Fix git images for frameworks
New index message, fixed git images for model
Removed obsolete oil, added Discussion to menu
Add missing files
Add form style sheet
remove more prints
remove print
Design factsheets
Add class structure for scenario factsheets
Commited missed files
Added model and framework factsheets
Change energy models according to factsheets
Remove obsolete constructors
Remove obsolete init
fix url imports
Adapt settings for deployment
Capsuled page for teaser access
merge fixed user login
Add mandatory is_staff field
Secured base site
Added login to entire site for internal deployment
Added user creation forms
Merge pull request #16 from openego/feature/user-login
Fixed bug in model edit
Added buttons for user login/logout
Merge branch 'develop' of https://github.com/openego/oeplatform into feature/user-login
Merge pull request #15 from openego/feature/modeledit
Removed obsolete style
Implemented list of model factsheets, users can add new model factsheets
Added an edit view for model factsheets
Merge pull request #14 from openego/feature/tablehier
Merge branch 'develop' of https://github.com/openego/oeplatform into feature/tablehier
Added check for doubled primary keys
Merge pull request #13 from openego/feature/tablehier
Merge branch 'develop' of https://github.com/openego/oeplatform into feature/data-handler
Added proper link hierarchy for databases, schemas and tables
Removed debug print
Added MEDIA_ROOR/URL to settings
merge feature/data-edit
Table overview and pending data promt
Edited the user class in models.py
Merge pull request #11 from openego/feature/models
Redesigned visual model fact sheets
implemented and styled model fact sheets
Translated model fact sheet into django model
Started simple welcome page
removed debug print
Merge branch 'feature/data-edit' of https://github.com/openego/oeplatform into feature/data-edit
Delete base.html~
Enabled csv-import, deletion and editing of pending data
Merge branch 'feature/data-edit' of https://github.com/openego/oeplatform into feature/data-edit
merged develop
Merge pull request #7 from openego/feature/mainframe
Started implementation of main frame
Introduced template inheritance
Delete views.py~
Added missing files
Started data view and edit
Added requirements.txt
moved settings to appropiate folder
tracked .gitignore
extended .gitignore for python, renamed securitysettings.py
Merge pull request #1 from openego/hotfix/empty-security-settings
Create securitysettings.py
Added settings.py without security informations
Removed settings
Intitalised platform project
