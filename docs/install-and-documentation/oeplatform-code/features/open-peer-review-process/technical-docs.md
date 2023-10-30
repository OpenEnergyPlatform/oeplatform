## Views
Django views.

### PeerReviewView
View for the reviewer role of the Open Peer Review process.
#### ::: dataedit.views.PeerReviewView  


### PeerRreviewContributorView
View for the contributor role of the Open Peer Review process.

#### ::: dataedit.views.PeerRreviewContributorView  

## Helper Functions
Separated functionality that can be imported in other modules. It contains several functions that help with recurring tasks in the peer review system.

### ::: dataedit.helper  

## Metadata Functions
Provide functionality that is related to retrieving and updating the oemetadata resource from the database. The oemetadata is the object of a review.  
### Save Metadata to Database
#### ::: dataedit.metadata.save_metadata_to_db

### Load Metadata from Database
#### ::: dataedit.metadata.load_metadata_from_db  

## Models
Django models.

### PeerReview
The model of the Open Peer Review defines what data is stored in the django database about each existing review. Next to the review itself it stores additional data about the the reviewer and contributor user and more. It is used in the PeerReviewManger.

!!! note
    This model also provides functionality that is directly related to the model. 
    It is up to discussion if we want to keep the functionality inside the model.
#### ::: dataedit.models.PeerReview  

### PeerReviewManager
The Manager is introduced to be able to store additional information about the peer review process and separate it from the PeerReview model. The process is started by submitting a review and the manager maintains the order of which user has to take the next action to be able to hold and activate the process. 


!!! note
    This model also provides functionality that is directly related to the model. 
    It is up to discussion if we want to keep the functionality inside the model.
#### ::: dataedit.models.PeerReviewManager  
