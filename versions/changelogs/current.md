### Changes

### Features
- Open Peer Review: Add functionality that updates the red/green dot (progress indicator) if all fields are accepted for each metadata tab [(#13)](https://github.com/OpenEnergyPlatform/oeplatform/pull/13)
- Add initial version of new documentation created using mkdocs and hosted on gh-pages [(#1347)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1347)
- Open Peer Review: Add functionality that switches to the next category tab if the selected field is not part of the current category [(#1328)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1328)
- Add funder logo in about page [#1344](https://github.com/OpenEnergyPlatform/oeplatform/pull/1344)

### Bugs
- Open Peer Review: Fix a bug that disables review controls for fields that have not yet been peer reviewed. The bug was triggered when the user clicks on an accepted (green) field and then clicks again on a gray field. [(#1362)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1362)
- If a new value was accepted as part of a field review, store the value as accepted value in the op-review datamodel [(#1322)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1322)
- Open Peer Review: Fix a bug in the review backend to handle reviews that are finished in one go (without any feedback). [(#1333)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1333)
- The django-compressor integration now updates the compressed sources and cache as expected [(#1338)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1338)

### Removed
