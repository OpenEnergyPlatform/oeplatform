<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr>
SPDX-FileCopyrightText: 2025 Eike Broda <https://github.com/ebroda>
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg

SPDX-License-Identifier: CC0-1.0
-->

# Bootstrap 5 Theme Generation
We use a custom bootstrap theme to style the platform. If I did everything correctly, you never need to touch this, but this is very unlikely, so this is how to generate a new bootstrap.min.css, which contains the theme.

You need to do this steps, if you change values within the `_variables.scss`.
I used [Bootstrap Build](https://bootstrap.build/) to create `_variables.scss`. If you need to change anything, you can import this theme into this tool.

## Preparation
Since we do not have any `npm`-based environment within this platform, which is required by Bootstrap, this is packed into a Docker container. First, we need to build this container.

```sh
docker build -t bootstrap-build .
```

Afterwards, we have a ready build container, which can be used to build our `bootstrap.min.css` file.
```shell
docker run -v $(pwd)/_variables.scss:/_variables.scss -v $(pwd)/scss:/scss bootstrap-build > bootstrap.min.css
```

To check what changes are in the updated bootstrap.min.css, you can use the script ``build_an_diff.sh`` (here of #1856):
```shell
me@local:/app/theming/$ sh build_and_diff.sh
Build current minimized bootstrap.min.css ... 
Re-running docker with sudo prefix ... done and successful.

Checking diff ... the diff between the current bootstrap.min.css and the newly compressed file is:

6335c6335
> main.main .content .content__container.content__container--profile .profile-sidebar__img img,main.main .content .content__container.content__container--profile .profile-sidebar__img svg{object-fit:cove}
---
< main.main .content .content__container.content__container--profile .profile-sidebar__img img,main.main .content .content__container.content__container--profile .profile-sidebar__img svg{object-fit:cover}

Found 1 change(s)

If this diff is fine for you, copy the bootstrap.min.css to ../base/static/css/bootstrap.min.css, e.g.
mv bootstrap.min.css ../base/static/css/bootstrap.min.css 
```

If you're fine with the changed, copy the file `bootstrap.min.css` manually into `base/static/css/`, as indicated.

## Build css without docker

1. navigate into the `theming` directory
1. locally clone bootstrap: `git clone --depth=1 --branch v5.2.0 https://github.com/twbs/bootstrap.git`
1. build css: `sass --no-source-map --style=compressed oepstrap.scss ../base/static/css/bootstrap.min.css`
