# Login

This app handles the user authentication using django allauth and implements a user profile that provide an overview on tables and helps to manage the datasets draft or published state. Additionally the profile pages include the permission groups to manage data table resource access permissions as group with other users. The last feature is the user profile, including a view showing the api token with functionality to reset it as well as a Form to provide additional user data like adding a user image.

## Setup

First make sure to install django allauth package and install it into the existing project:

- install latest requirements.txt in the python environment

    `pip install -r requirements.txt`

- run python migrations to setup the new django allauth models (tables)

    `python manage.py migrate`

- check your iptables setting on the server to enable server to server connection using the service static ip address. Don`t forget to restart the iptables service to apply the updates.

Now edit your securitysettings.py and update it with the content form the securitysettings.py.default template file to setup the social provider used for 3rd Party Login flow. We use openIDConnect that is implemented by django allauth:

!!! Note
    Filling out the values in the dictionary depends on your Provider. They should provide documentation or provide you with the relevant credentials. In some cases the provider_id must be in line with the specification of the provider in others you can choose your own name here. The client_id & secret should also be provided as well as the server_url.

```python
SOCIALACCOUNT_PROVIDERS = {
    "openid_connect": {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        "APPS": [{
            "provider_id": "",
            "name": "",
            "client_id": "",
            "secret": "",
            "VERIFIED_EMAIL": True,
            "EMAIL_AUTHENTICATION": True,
            "settings": {"server_url": ""},
        }]
    }
}
```

## App Components

The components of each app implement the django app structure and implement a MVVM pattern for web applications. This includes the files model.py, views.py, urls.py,  Then there are migrations that specify the django table structure and is also a core django feature. The templates include all HTML page payouts including django template syntax to render pages with dynamic server data and JavaScript. Additionally there might be other folders and python modules available.w

### Views

**ProfileUpdateView**
::: login.views.ProfileUpdateView

### Forms

**3rd party Signup**
::: login.forms.UserSocialSignupForm

**Default Signup**
::: login.forms.CreateUserForm

**Edit existing user data**
::: login.forms.EditUserForm

### Adapters

::: login.adapters

### Models

**The user manager that handles oeplatform users and their system role**
::: login.models.OEPUserManager

**The user model of a oeplatform user**
::: login.models.myuser
