# JavaScript integration

!!! Note

    The information provided here is only relevant if you encounter issues in the vite (nodejs) setup. During development the javascript server is running automatically and in production only a bundled version of the code is shipped which keeps the production environment clean.

We integrate nodejs into the django project to support JavaScript and enhance
developer experience, enhance consistency for JavaScript modules and more.

## Benefits

- [HotModuleReplacing (HMR)](https://vite.dev/guide/features.html#hot-module-replacement)
  which is one of the main benefits for development as devs can write and see
  the results of code changes in JavaScript code much faster.

- [Dependency resolving & Pre-Bundling](https://vite.dev/guide/features.html#hot-module-replacement)

- Option to go for type script

- Enables us to get npm packages

## Build tool

Currently we not 100% set on what build tool we will role out for all parts of
the oeplatform apps. Webpack is a proven and more complicated to setup tool
while vite seems to be less overhead and supports all our needs also. That is
why we opt for vite for now and test it for current development tasks.

### Setup Integration

To setup vite we follow <https://github.com/MrBin99/django-vite>.

We will have to install the pypi package, update requirements.txt, modify django
settings and add django-vite to base templates and specific tags to react
templates.

To setup the javascript server we have to create and configure `vite.config.mjs`
config file for the vite server and initiate a npm project creating and
maintaining a `package.json`. This sets up java script for the whole django
project, but also requires devs to set this up until we offer a docker image
which will automate this process. Once the npm environment is setup we must run
`npm install` and make sure vite is installed as well as the vite-react plugin
is added (see the [vite getting started guide](https://vite.dev/guide/)).

## Integration status

The following apps integrate:

- Webpack
  - oeo-viewer
  - factsheet (also supported by vite integration)

- Vite
  - Open peer review (dataedit js client)
  - factsheet (scenario bundles react client)

- None so far
  - MetaBuilder (dataedit js client)
