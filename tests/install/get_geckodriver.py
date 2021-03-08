import os
from os.path import join
import tarfile
import requests

cur_folder = join(os.path.abspath(__file__))

install_dir = os.path.dirname(os.path.dirname(cur_folder))

driver_fname = "geckodriver"

if not os.path.exists(join(install_dir, driver_fname)):
    base_url = "https://github.com/mozilla/geckodriver/releases/download"

    # fetch the latest release tag name
    r = requests.get("https://api.github.com/repos/mozilla/geckodriver/releases/latest")
    version = r.json()['tag_name']

    filename = "geckodriver-{}-linux64.tar.gz".format(version)

    zipurl = "{base_url}/{version}/{filename}".format(
        filename=filename,
        base_url=base_url,
        version=version,
    )

    # download the webdriver's archive
    response = requests.get(zipurl, stream=True)
    if response.status_code == 200:
        # save the webdriver's archive
        with open(join(install_dir, filename), 'wb') as f:
            f.write(response.raw.read())

        # extract the webdriver archive into a file
        with tarfile.open(join(install_dir, filename), 'r') as tar:
            tar.extractall(join(install_dir))

    rm_cmd = "rm {}".format(join(install_dir, filename))
    os.system(rm_cmd)

else:
    print('{} already present'.format(driver_fname))