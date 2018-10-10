FROM debian:9
LABEL maintainer="erik@martin-dorel.org"

RUN apt-get update -y -q \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends \
    autoconf \
    automake \
    bubblewrap \
    build-essential \
    ca-certificates \
    curl \
    git \
    less \
    m4 \
    pkg-config \
    rlwrap \
    rsync \
    sudo \
    time \
    unzip \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  # Download the latest stable release of opam
  && version=$(curl -fsS https://api.github.com/repos/ocaml/opam/releases/latest \
  | grep '"tag_name":' | cut -d : -f 2 | tr -d \ ,\") \
  && [ -n "$version" ] \
  && binary="opam-${version}-$(uname -m)-$(uname -s | tr '[:upper:]' '[:lower:]')" \
  && curl -L https://github.com/ocaml/opam/releases/download/${version}/${binary} \
    -o /usr/local/bin/opam \
  && chmod a+x /usr/local/bin/opam

# Use Docker build args to set the UID/GID
ARG guest_uid=1000
ARG guest_gid=${guest_uid}

# Add Coq group and user with sudo perms
RUN groupadd -g ${guest_gid} coq \
  && useradd --no-log-init -m -s /bin/bash -g coq -G sudo -p '' -u ${guest_uid} coq \
  # Create dirs for user scripts
  && mkdir -p -v /home/coq/bin /home/coq/.local/bin \
  && chown coq:coq /home/coq/bin /home/coq/.local /home/coq/.local/bin

# Load travis.sh at login
COPY travis.sh /etc/profile.d/

WORKDIR /home/coq

USER coq

ENV NJOBS="2"
ENV COMPILER="4.05.0"
ENV COMPILER_EDGE="4.07.0+flambda"

RUN ["/bin/bash", "--login", "-c", "set -x \
  && opam init --auto-setup --yes --jobs=${NJOBS} --compiler=${COMPILER_EDGE} --disable-sandboxing \
  && eval $(opam env) \
  && opam repository add --all-switches --set-default coq-released https://coq.inria.fr/opam/released \
  && opam update -y \
  && opam install -y -j 1 opam-depext \
  && opam clean -a -c -s --logs \
  && opam config list && opam list"]

RUN ["/bin/bash", "--login", "-c", "set -x \
  && opam switch create -y ${COMPILER} \
  && eval $(opam env) \
  && opam install -y -j 1 opam-depext \
  && opam clean -a -c -s --logs \
  && opam config list && opam list"]

ENTRYPOINT ["opam", "exec", "--"]

CMD ["/bin/bash", "--login"]
