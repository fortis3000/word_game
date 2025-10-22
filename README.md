Standartized DS project template
==============================

Project Organization
------------

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported


Logging
-------

This project provides a general-purpose logger utility in `src/utils/logger.py`.

**Usage Example:**

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("This is an info message.")
logger.error("This is an error message.")
```

You can attach this logger to any module or script in the project.
    └── src                <- Source code for use in this project.
        ├── __init__.py    <- Makes src a Python module
        │
        ├── data           <- Scripts to download or generate data
        │   └── make_dataset.py
        │
        ├── features       <- Scripts to turn raw data into features for modeling
        │   └── build_features.py
        │
        ├── models         <- Scripts to train models and then use trained models to make
        │   │                 predictions
        │   ├── predict_model.py
        │   └── train_model.py
        │
        └── visualization  <- Scripts to create exploratory and results oriented visualizations
            └── visualize.py



--------

## Goals
- Reduce time to establish a repo specifically for DS needs.
- To align data scientists in terms of skills and tools used.
- Make project standard, easier to observe and predictable.

## Description:

### Project structure

The current architecture is based on [Cookiecutter DS](https://github.com/drivendata/cookiecutter-data-science) approach. The reasoning behind it you can find [here](http://drivendata.github.io/cookiecutter-data-science/).

### Code versioning tools
To track, keep and share your codings [git](https://git-scm.com/) and [GitHub](https://github.com/) services are required.

### Default programming language
To leverage modern programming stack it is recommended to start with [Python 3.12](https://www.python.org/downloads/release/python-3120/) as default.

### Dependency management
To follow Single-Source-Of-Truth concept it makes sense to use [pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) to store project configuration. `pyproject.toml` configuration file allows to use the same configuration on different project steps: CI/CD, dev, test, prod etc.

#### uv
Newly announced [uv tool](https://github.com/astral-sh/uv).

To create new virtual environment:
```bash
uv venv -p 3.12
```

You might need to install or provide path to python 3.12 first.

Activate an environment on macOS and Linux:
```bash
source .venv/bin/activate
```

On Windows:
```shell
.venv\Scripts\activate
```

To build an requirements file from `pyproject.toml` use the following command: 
```bash
uv pip compile pyproject.toml --extra dev --extra lint -o requirements.txt
```

To install compiled file:
```bash
uv pip sync requirements.txt
```

#### Poetry
To manage Python dependencies using the same file we can use [poetry](https://python-poetry.org/).

### Codestyle: ruff
Both for code linting and formatting Ruff package is proposed to use. See [here](https://docs.astral.sh/ruff/) for more details.

Commands:
```bash
ruff format . --config pyproject.toml
ruff check .  --config pyproject.toml

ruff check . --fix
```

### CI/CD: GitHub Actions

As a baseline, CI with integrated code style is provided (see `.github/workflows/ci.yml`). The current setup is based on using public Actions and configuring CI with `pyproject.toml` file. It is also possible to use custom Actions.

### Test suite:
TO BE DONE (pytest)


## Getting started
1. Create repo from the template

While creating repo, choose the current one as a template. Check [tutorial](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository) for more details.

It is also possible to use this repository as a template in GitHub interface.

2. Install, compile and activate virtual environment
See [uv](#uv)

3. Change parameters `pyproject.toml` if needed.
4. Tweak CI configuration `.github/workflows/ci.yml` if needed.
5. Put you source code in `src` folder.
6. Enjoy coding :)

## Best practices

### Makefile
Codestyle functionality could be applied locally using the Makefile created and the following command:

```bash
make precommit
```

or using `.sh` file directly:

```bash
bash ./precommit.sh
```

### Cli with typer
TO BE DONE
