# 🤠 PDS Engineering: Roundup
# ============================

FROM nasapds/pds-github-actions-base:latest


# Metadata
# --------

LABEL "com.github.actions.name"="PDS Roundup"

# Let's Have Nice Things
# ----------------------

ENV PYTHONUNBUFFERED=1


# Image Details
# -------------

WORKDIR    /usr/src/roundup
COPY       README.md CHANGELOG.md LICENSE.txt setup.cfg setup.py ./
COPY       src/ ./src
ENTRYPOINT ["/usr/local/bin/roundup"]

RUN : &&\
    pip uninstall --no-input --yes pds-github-util &&\
    pip install 'git+git://github.com/nasa-pds-engineering-node/pds-github-util@stable#egg=pds_github_util' &&\
    python3 setup.py install --optimize=2 &&\
    :
