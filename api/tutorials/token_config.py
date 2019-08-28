from subprocess import run
# untrack the change to this file (prevent pushing token to github)
run(['git', 'update-index', '--assume-unchanged', __file__])

oep_url = 'http://oep.iks.cs.ovgu.de/'
# Paste your token here
oep_token = ''


def get_oep_token():
    """
    Function which will warn the user if the oep token is empty
    :return oep token of user:
    """
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
