FROM debian:10-slim
LABEL maintainer="erik@martin-dorel.org"

ENV OPAM_VERSION="2.0.6"

RUN apt-get update -y -q \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends \
    autoconf \
    automake \
    bubblewrap \
    build-essential \
    ca-certificates \
    curl \
    git \
    # gnupg is temporarily installed and will not be kept in the image
    gnupg \
    less \
    m4 \
    openssh-client \
    pkg-config \
    rlwrap \
    rsync \
    sudo \
    time \
    unzip \
  && [ -n "${OPAM_VERSION}" ] \
  && binary="opam-${OPAM_VERSION}-$(uname -m)-$(uname -s | tr '[:upper:]' '[:lower:]')" \
  && cd /tmp \
  && curl -fSOL https://github.com/ocaml/opam/releases/download/${OPAM_VERSION}/${binary} \
  && curl -fSOL https://github.com/ocaml/opam/releases/download/${OPAM_VERSION}/${binary}.asc \
  && curl -fsSL https://keybase.io/altgr/pgp_keys.asc | gpg --batch --import \
  && gpg --batch --verify ${binary}.asc ${binary} \
  && set -x \
  && mv ${binary} /usr/local/bin/opam \
  && chmod a+x /usr/local/bin/opam \
  && rm -f ${binary}.asc \
  && rm -fr /root/.gnupg \
  && DEBIAN_FRONTEND=noninteractive apt-get purge -y -q --auto-remove gnupg \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

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
ENV COMPILER_EDGE="4.09.0+flambda"

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
