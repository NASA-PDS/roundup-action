# 🤠 PDS Engineering: Roundup
# ============================

FROM nasapds/github-actions-base:stable


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
    pip install 'lasso.releasers~=1.0.0' 'lasso.requirements~=1.0.0' &&\
    pip install 'lasso-issues~=1.3.1' &&\
    pip install /usr/src/roundup &&\
    :
