<!--
SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Frontend Workflow <span class="badge badge--warning">Draft</span>

If you need or wish to work on the visual part of the platform, here are some resources to help you started with.

Be sure to know the existing OEP styling, in order to keep the visual consistent throughout the platform. You can double-check by reviewing the website or going through the the [design system](design-system.md). Try to keep [accessibility](accessibility.md) in mind as well.

## Main workflow

This is the workflow used for working on the biggest part of the app. But if you need to work with the factsheets, you can directly check the content below about [React and MUI](#react-and-mui).

### Theming module

Since we use [Bootstrap v5.2.0 :fontawesome-solid-arrow-up-right-from-square:](https://getbootstrap.com/docs/5.2/getting-started/introduction/){:target="_blank"} as a front-end library, you first need to have it installed in order to be able to use it. See [documentation :fontawesome-solid-arrow-up-right-from-square:](https://github.com/OpenEnergyPlatform/oeplatform/tree/develop/theming){:target="_blank"}.

Once installed, you can view the content of the Bootstrap library's content inside `/theming/bootstrap`.

### BEM approach

We use the BEM (Block-Element-Modifier) methodology to create descriptive and maintainable class names for our styles. It helps us structure our CSS by dividing components into blocks (standalone components), elements (parts of a block), and modifiers (variations or states of a block or element):

`block__element--modifier`

For example, we can create a `button` element, and create variants, such as `button--filled` and `button--outlined`.

We can also create a `table` block, then work on the `table__header` element and style for `table__header--large` and `table__header--small`.

This approach is particularly useful working with SCSS instead of CSS.

### @extend

On top of BEM, we use Sass’s `@extend` feature to leverage Bootstrap’s existing styles. This approach ensures we adhere to the design language established by Bootstrap. It helps maintain consistency and reduces the risk of CSS specificity issues. Additionally, using `@extend` makes our style sheets smaller by reusing rulesets from Bootstrap, improving the overall performance of our application. Example:

```
.button--filled {
  @extend .btn;
  @extend .btn-primary;
}
```

If you user modifiers, remember to use the two classes:

```
<thead class="table__header table__header--large">
    ...
</thead>
```

This hybrid approach of BEM + @extend means you can safely remove the Bootstrap classes from the HTML elements and only keep the BEM classes. But in some cases it is not possible to remove an original Bootstrap class, as a class can be used to dynamically change the styling through JavaScript. It is the case for some components such as nav or tabs.

### Add new component or layout

If a component or layout doesn't exist yet inside the `/theming` directory, you can create a file inside the components or layouts folder:

```
/theming/scss/components/_<new-component-name>.scss
```

Then add it to the path inside `/theming/oepstrap.scss`, before working on the styling.

```
@use 'scss/components/<new-component-name>';
```

### Overwrite a Bootstrap variable

Try as much as possible to use the existing Bootstrap variables (`/theming/bootstrap/scss/_variables.scss`) or the ones that are already overwritten (`/theming/_variables.scss`), but if you still need to change/overwrite a variable, you need to do it in 2 places:

- `/theming/_variables.scss`: update the variable with a new value
````
$blue-500: #2972A6;
````

- `/theming/scss/base/_index.scss`: add the variable to `@forward`
```
$blue-500: $blue-500
```

## React and MUI

If you need to work with React, for example inside the `/factsheet` directory, the workflow is different, i.e. BEM doesn't apply here, but the goal from a UI perspective remains the same: the whole app should look uniform, even if the libraries used in the background are different.

### MUI

[MUI :fontawesome-solid-arrow-up-right-from-square:](https://mui.com/material-ui/all-components/){:target="_blank"} provides a set of pre-built components specifically designed for React. It uses a component-based approach where each UI element is encapsulated within a React component. It handles styling internally using CSS-in-JS, which means styles are defined directly in JS files instead of CSS or SCSS files.

There is a basic OEP theme inside `/factsheet/frontend/src/styles/oep-theme.js` with the main color palettes, typographic rules and styling for some main components such as buttons and tables. The styles are similar to the ones used in the theming module, but they don't cover as many uses cases yet, though. They can then be used inside the components in `/factsheet/frontend/src/components`. Try to mostly use this theme in a .js format, but if you need to add extra CSS, you can add them to `/factsheet/frontend/src/styles/App.css`.
