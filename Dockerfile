FROM debian:9
LABEL maintainer="erik@martin-dorel.org"

RUN apt-get update -y -q \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends \
    aspcud \
    autoconf \
    automake \
    build-essential \
    ca-certificates \
    curl \
    emacs25-nox \
    git \
    gosu \
    less \
    m4 \
    ocaml-best-compilers \
    ocaml-core \
    opam \
    pkg-config \
    rlwrap \
    rsync \
    sudo \
    time \
  && echo "ocamlc -version => $(ocamlc -version)" \
  && echo "opam --version => $(opam --version)" \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Use Docker build args to set the UID/GID
ARG guest_uid=1000
ARG guest_gid=${guest_uid}

# Add Coq group and user with sudo perms
RUN groupadd -g ${guest_gid} coq \
  && useradd --no-log-init -m -s /bin/bash -g coq -G sudo -p '' -u ${guest_uid} coq

# Load travis.sh at login
COPY travis.sh /etc/profile.d/

WORKDIR /home/coq

USER coq

# Create dirs for user scripts
# => one need not run "chown coq:coq bin .local .local/bin" afterwards
RUN mkdir -p -v bin .local/bin

ENV NJOBS="2"
ENV COMPILER="4.02.3"
ENV COQ_VERSION="8.8.1"

# Setup OPAM and Coq
RUN ["/bin/bash", "--login", "-c", "set -x \
  && opam init --auto-setup --yes --jobs=${NJOBS} --compiler=${COMPILER} \
  && eval $(opam config env) \
  && opam repository add coq-released https://coq.inria.fr/opam/released \
  && opam update -y \
  && opam pin add -n -k version coq ${COQ_VERSION} \
  && opam install -y -j ${NJOBS} depext coq \
  && opam config list && opam list"]
