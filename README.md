# validating-base

![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/alexfayers/validating_base?label=version)
![Lines of code](https://img.shields.io/tokei/lines/github/alexfayers/validating_base)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/alexfayers/validating_base/CI.yml?label=tests)
![GitHub last commit](https://img.shields.io/github/last-commit/alexfayers/validating_base)

An epic project called validating-base, by alexfayers!

- [validating-base](#validating-base)
  - [Features](#Features)
  - [Installation](#Installation)
    - [pip](#pip)
    - [pipx](#pipx)
  - [Usage](#usage)
  - [Documentation](#Documentation)
  - [Contributing](#Contributing)

## Features

- [x] Installable via pip
- [x] Command-line interface
- [x] Interactive documentation
- [ ] Some new planned feature

## Installation

### pip

```bash
$ pip install git+https://github.com/alexfayers/validating_base
```

### [pipx](https://pypa.github.io/pipx/)

```bash
$ pipx install git+https://github.com/alexfayers/validating_base
```

## Usage

You can use validating-base as an importable module:

```py
from validating_base import BaseClass

app = BaseClass("config.toml")

# cool stuff here...
```

Or as a command line interface:

```bash
$ python3 -m validating-base
# or
$ validating-base
```

## Documentation

Interactive documentation for validating-base can be found within the [docs](./docs/index.html) folder.

## Contributing

If you want to contribute to validating-base, you'll need [poetry](https://python-poetry.org/) and [tox](https://tox.wiki/en/latest/).

Then you can clone the repository and install the development dependencies like so:

```bash
$ git clone https://github.com/alexfayers/validating_base
$ cd validating_base
$ poetry install --with dev
```

Run tests like this:

```bash
$ tox
```

And lint and format your code like this:

```bash
$ tox -e lint
```
