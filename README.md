# rocq/base

[![tags](https://img.shields.io/badge/tags%20on-docker%20hub-blue.svg)](https://hub.docker.com/r/rocq/base#supported-tags "Supported tags on Docker Hub")
[![pipeline status](https://gitlab.com/coq-community/docker-base/badges/master/pipeline.svg)](https://gitlab.com/coq-community/docker-base/-/pipelines)
[![pulls](https://img.shields.io/docker/pulls/rocq/base.svg)](https://hub.docker.com/r/rocq/base "Number of pulls from Docker Hub")
[![stars](https://img.shields.io/docker/stars/rocq/base.svg)](https://hub.docker.com/r/rocq/base "Star the image on Docker Hub")  
[![dockerfile](https://img.shields.io/badge/dockerfile%20on-github-blue.svg)](https://github.com/coq-community/docker-base "Dockerfile source repository")
[![coq](https://img.shields.io/badge/see%20also-rocq%2Frocq--prover-brightgreen.svg)](https://hub.docker.com/r/rocq/rocq-prover "Docker images of Rocq")

This repository provides parent images for [Docker](https://www.docker.com/) images of the [Coq](https://github.com/coq/coq) proof assistant.

These images are based on [Debian 12 Slim](https://hub.docker.com/_/debian/):

|   | GitHub repo                                                             | Type          | Docker Hub                                                       |
|---|-------------------------------------------------------------------------|---------------|------------------------------------------------------------------|
|   | [docker-coq-action](https://github.com/coq-community/docker-coq-action) | GitHub Action | N/A                                                              |
|   | [docker-rocq](https://github.com/coq-community/docker-rocq)             | Dockerfile    | [`rocq/rocq-prover`](https://hub.docker.com/r/rocq/rocq-prover/) |
| ⊙ | [docker-base](https://github.com/coq-community/docker-base)             | Dockerfile    | [`rocq/base`](https://hub.docker.com/r/rocq/base/)               |
| ↳ | Debian                                                                  | Linux distro  | [`debian`](https://hub.docker.com/_/debian/)                     |

This Dockerfile repository is [mirrored on GitLab](https://gitlab.com/coq-community/docker-base), but [issues](https://github.com/coq-community/docker-base/issues) and [pull requests](https://github.com/coq-community/docker-base/pulls) are tracked on GitHub.

<!-- tags -->
