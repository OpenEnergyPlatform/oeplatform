# Release procedure
Here we will describe a process that takes place after a contributor has successfully integrated
his changes to the codebase as well as extension to the documentation etc. into the "develop" branch 
(by merging pull-requests). 

## Definition of Release
Changes/extensions in the codebase, e.g. as new features or bugfixes, have a value for our 
application. We document all changes in a [CHANGELOG](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/versions/changelogs/current.md). In the release procedure these changes are deployed on a webserver. Afterwards 
the user can use the newly released version online. For this we use two environments that are 
visible to the public for testing and production.

## Release Cycle
We make a new release every first monday of a month. All features and bugfixes which are integrated 
in the develop branch until then will
be released.

## Release Contend Management
We use projects on github to organize the release. Issues and pull requests can be assigned to a 
[release-project](https://github.com/OpenEnergyPlatform/oeplatform/projects) on github by linking 
the project in the issue/pr. With the project feature of github, all tasks that are linked to 
the project are organized via a Kanban board.

The project can be linked in an issue or pull request via the menu "Projects"


## Required accounts and admin privileges

## Basic-Steps for deploy and release (publishing a new release)
Before see How to [Contribute](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/CONTRIBUTING.md)

1. Make a release candidate branch (e.g., `release/vx.x.x`)
   and pull request it into `master` with the following updates:
   1. Update the oeplatform/versions/changelogs/ `current.md` (see the examples of previous releases)
	  - Change filename to release version (x_x_x.md)
  1. Confirm that the PR passes all tests and checks
  1. Tag the release number
  1. Once successful, delete the tag, and merge the candidate PR into `master` on Github
1. Switch to the now-updated master branch: `git checkout master` and `git pull upstream master`
1. Tag the release number: `git tag v<release version>`, e.g., `git tag v1.2.0`
   - `versioneer` automatically updates the version number based on the tag
   - this is now the official tagged commit
1. Push the tag upstream: `git push upstream --tags`
1. Make a new release on Github
   - make sure that you choose the tag name defined above
   - copy the release summary from changelog into the description box
1. Add a new line "# Next Release" at the top of `RELEASE_NOTES.md` and commit to `master`
1. Announce it on our mailing list: https://groups.io/g/pyam
   - again, copy the rendered HTML from the Github release directly in the email

1. As stated in the [django deployment documentation](https://docs.djangoproject.com/en/3.0/howto/deployment/), every django app has to be served by an external web server. Please make sure to follow the security advise given in the deployment documentation, if you want to host your own version of the Open Energy Platform.
   1. ???

And that's it! Whew... 
