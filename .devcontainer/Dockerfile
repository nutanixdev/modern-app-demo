ARG VARIANT="3.11-bullseye"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

ENV PYTHONUNBUFFERED 1

ARG NODE_VERSION="none"
ARG OPENSHIFT_CLI_VERSION="latest"
ARG KNATIVE_CLI_VERSION="latest"

COPY .devcontainer/library-scripts/*.sh /tmp/library-scripts/

# Install node.js
RUN if [ "${NODE_VERSION}" != "none" ]; then \
        su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; \
    fi

# Install OpenShift CLI
RUN if [ "${OPENSHIFT_CLI_VERSION}" != "none" ]; then \
        bash /tmp/library-scripts/openshiftcli-linux.sh "${OPENSHIFT_CLI_VERSION}"; \
    fi 

# Install Knative CLI
RUN if [ "${KNATIVE_CLI_VERSION}" != "none" ]; then \
        bash /tmp/library-scripts/kncli-linux.sh "${KNATIVE_CLI_VERSION}"; \
    fi 

# [Optional] If your requirements rarely change, uncomment this section to add them to the image.
COPY requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
   && rm -rf /tmp/pip-tmp

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>



