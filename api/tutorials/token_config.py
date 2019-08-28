"""
This file will help you manage your OEP token (required to push changes in the database)

We recommend that you store your token in an environment variable "OEP_TOKEN".
However, if you do not know how to do that or you do not want to do that you can assign
your token to the variable `oep_token` in this file.

WARNING : Do not push the changes to this file online if you chose the second option,
 or your token will be visible by everyone
"""
from os import environ
from subprocess import run
# untrack the changes to this file (prevent pushing token to github)
run(['git', 'update-index', '--assume-unchanged', __file__])

oep_url = 'http://oep.iks.cs.ovgu.de/'

# Paste your token here if you do not know how to setup an environment variable
OEP_TOKEN = ''


def get_oep_token():
    """
    Function which will warn the user if the oep token is empty
    :return oep token of user:
    """

    # Prioritize the environment variable
    oep_token = environ.get("OEP_TOKEN", OEP_TOKEN)

    if not oep_token:
        raise(
            Warning(
                'The OEP token you provided in the api/token_config.py file is empty.\n'
                'Please sign in to https://openenergy-platform.org/user/login/?next=/ '
                'to retrieve your token \n(then click on your username on the top right '
                'of the page to display your information).\n Then copy-paste your token in '
                'the api/token_config.py file.'
            )
        )

    return oep_token
