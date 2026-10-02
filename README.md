# ethanwtodd.com

The site at [ethanwtodd.com](https://ethanwtodd.com), the documentation index at
[docs.ethanwtodd.com](https://docs.ethanwtodd.com), and the wiring that puts the
generated API references underneath it. Hugo, no theme, no npm.

This repository is the whole public web surface. The system configuration on the
router takes exactly one flake input for all of it.

## Outputs

| Output | What it is | Served at |
|--------|------------|-----------|
| `packages.default` | The Hugo site | `ethanwtodd.com` |
| `packages.docs` | Documentation index plus each project's Doxygen output | `docs.ethanwtodd.com` |
| `packages.cv-import` | The CV converter, on its own | — |

```sh
nix build           # the site
nix build .#docs    # docs.ethanwtodd.com, references included
nix develop         # hugo, python3, and cv-import
hugo server -D      # preview
```

## The CV page is generated

`/cv/` is not written here. `scripts/cv_import.py` parses the LaTeX and BibTeX
sources in [Curriculum-Vitae](https://github.com/ewtodd/Curriculum-Vitae) — an
input of this flake — into `data/cv.json`, and copies the committed `CV.pdf` to
`static/cv/CV.pdf`. Both are gitignored; `layouts/cv.html` renders the data.

Updating the published CV is therefore:

```sh
nix flake update curriculum-vitae
```

In the dev shell, `cv-import` regenerates the data from `../Curriculum-Vitae` if
you have that checked out beside this repository, and from the pinned input
otherwise. If `data/cv.json` is missing entirely the page still builds and falls
back to linking the source repository, so a broken import can never take the
site down with it.

The parser understands the subset of moderncv and biblatex that CV actually
uses. Anything it does not recognise is passed through as text rather than
dropped.

## Adding a project

One markdown file in `content/projects/`. The front matter drives the card on
the home page, the specification panel on the project page, and — if it has a
`docs` key — the card on the documentation index.

```yaml
title: "Name"
description: "One sentence, used for meta description and as the card text."
summary: "Optional, replaces description on cards."
weight: 50
status: "Active"
role: "Author"
license: "MIT"
stack: ["C++", "Nix"]
repo: "https://github.com/ewtodd/…"
docs: "https://docs.ethanwtodd.com/…/"   # optional
```

A project joins `docs.ethanwtodd.com` by gaining a `docs` URL here **and** an
entry in the flake's `docs` derivation for its generated output. Nothing in the
system configuration changes.

## This repository owns the Doxygen theme

`assets/css/doxygen.css` is the only copy of the theme for every generated API
reference. The projects carry no stylesheet at all: they build as plain
doxygen-awesome, which is the output you read warnings against, and
`nix build .#docs` here adds the theme when it assembles the host.

The dependency runs one way. This flake has the projects as inputs; neither of
them knows this repository exists. So the design changes here, once, for all of
them, and no project has to be touched or re-pinned to pick it up.

Doxygen has no hook for adding a stylesheet to output it has already written,
so the link is inserted into the generated pages, anchored on the closing
`</head>`. That puts it last in the cascade, ahead of anything a project might
still ship of its own, which is what keeps the published look independent of
what any project has been updated to. The derivation fails if a page is missed.

## Layout

```
assets/css/main.css     the whole visual system, Kanagawa base16
assets/js/site.js       progressive enhancement only; the site works without it
content/                markdown; /cv/ and /docs/ are layout-only stubs
layouts/                baseof, home, section, page, cv, docsindex
layouts/partials/       nav, footer, head, eyebrow, project-card, reference, terminal
layouts/_shortcodes/    terminal
scripts/cv_import.py    LaTeX + BibTeX → data/cv.json
```

`layouts/docsindex.html` is deliberately self-contained — inlined CSS, absolute
links, no `baseof` — because the same file is served both as `/docs/` here and
as the root of `docs.ethanwtodd.com`.

## Design

Kanagawa base16, dark only, matching `doc/theme/custom.css` in the
Analysis-Utilities and MUSIC repositories so the portfolio and the generated
references read as one system. The visual language is a technical drawing: a
faint grid under everything, hairline rules, corner ticks on panels, and mono
uppercase labels used the way a drawing sheet uses annotations.

No web fonts. A page makes one request for CSS, one for a small script, and
nothing else.
