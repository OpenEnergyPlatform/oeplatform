# Bootstrap 5 Theme Generation

We use a custom bootstrap theme to style the platform. If I did everything correctly, you never need to touch this, but this is very unlikely, so this is how to generate a new bootstrap.min.css, which contains the theme.

You need to do this steps, if you change values within the `_variables.scss`.
I used [Bootstrap Build](https://bootstrap.build/) to create `_variables.scss`. If you need to change anything, you can import this theme into this tool.

## Preparation

Since we do not have any `npm`-based environment within this platform, which is required by Bootstrap, I packed this into a Docker container. First, we need to build this container.

```sh
docker build -t bootstrap-build .
```

Afterwards, we have a ready build container, which can be used to build our `bootstrap.min.css` file (first line).
Or you can directly overwrite the existing `bootstrap.min.css` file (second line). Or you copy manually the `bootstrap.min.css` this into `base/static/css/bootstrap.min.css`.

```sh
docker run -v $(pwd)/_variables.scss:/_variables.scss -v $(pwd)/scss:/scss bootstrap-build > bootstrap.min.css
docker run -v $(pwd)/_variables.scss:/_variables.scss -v $(pwd)/scss:/scss bootstrap-build > ../base/static/css/bootstrap.min.css
```

## Build css without docker

1. navigate into the `theming` directory
1. locally clone bootstrap: `git clone --depth=1 --branch v5.2.0 https://github.com/twbs/bootstrap.git`
1. build css: `sass --no-source-map --style=compressed oepstrap.scss ../base/static/css/bootstrap.min.css`
