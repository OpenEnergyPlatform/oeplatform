# Login

This app handles the user authentication using django allauth and implements a user profile that provide an overview on tables and helps to manage the datasets draft or published state. Additionally the profile pages include the permission groups to manage data table resource access permissions as group with other users. The last feature is the user profile, including a view showing the api token with functionality to reset it as well as a Form to provide additional user data like adding a user image.

## Setup

- install latest requirements in the python environment
- run python migrations `python manage.py migrate` to setup the new django allauth models (tables)
- check your iptables setting on the server to enable server to server connection using the service static ip address

## App Components

The components of each app implement the django app structure and implement a MVVM pattern for web applications. This includes the files model.py, views.py, urls.py,  Then there are migrations that specify the django table structure and is also a core django feature. The templates include all HTML page payouts including django template syntax to render pages with dynamic server data and JavaScript. Additionally there might be other folders and python modules available.w

### Views

::: login.views
