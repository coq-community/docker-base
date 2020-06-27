# docker-keeper

This python script is devised to help maintain Docker Hub repositories
of stable and dev (nightly build) Docker images from a YAML-specified,
single-branch GitLab repository - typically created as a fork of the
following repo: <https://gitlab.com/erikmd/docker-keeper-template>.

This script is meant to be run by GitLab CI.

## Syntax

```
keeper.py write-artifacts
    Generate artifacts in the 'generated' directory.
    This requires having file 'images.yml' in the current working directory.

keeper.py --version
    Print the script version.

keeper.py --upstream-version
    Print the upstream version from https://gitlab.com/erikmd/docker-keeper

keeper.py --help
    Print this documentation.
```

## Usage

* Fork <https://gitlab.com/erikmd/docker-keeper-template>.

* Follow the instructions of the README.md in your fork.
