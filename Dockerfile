# 🤠 PDS Engineering: Roundup
# ============================

FROM nasapds/github-actions-base:stable


# Metadata
# --------

LABEL "com.github.actions.name"="PDS Roundup"


# Let's Have Nice Things
# ----------------------

ENV PYTHONUNBUFFERED=1
ENV lasso_releasers=1.0.1
ENV lasso_requirements=1.0.0
ENV lasso_issues=1.3.1


# Image Details
# -------------

WORKDIR    /usr/src/roundup
COPY       README.md CHANGELOG.md LICENSE.txt setup.cfg setup.py ./
COPY       src/ ./src
ENTRYPOINT ["/usr/src/roundup-venv/bin/roundup"]

RUN : &&\
    : Set up each dependency in its own venv and symlink the bins into /usr/local/bin &&\
    : &&\
    : First up, lasso.releasers &&\
    python3 -m venv /usr/src/rel &&\
    /usr/src/rel/bin/pip install --quiet lasso.releasers~=${lasso_releasers} &&\
    ln -s /usr/src/rel/bin/maven-release /usr/local/bin &&\
    ln -s /usr/src/rel/bin/nodejs-release /usr/local/bin &&\
    ln -s /usr/src/rel/bin/python-release /usr/local/bin &&\
    ln -s /usr/src/rel/bin/snapshot-release /usr/local/bin &&\
    : &&\
    : Next, lasso.requirements, which for some reason needs both an upgraded pip and &&\
    : the packaging package too &&\
    python3 -m venv /usr/src/req &&\
    /usr/src/req/bin/pip install --quiet --upgrade pip &&\
    : Do not upgrade packaging past v20 as requirement-report 1.0.0 does not work with newer versions &&\
    : And YES, lasso.requirements should declare its own dependencies &&\
    /usr/src/req/bin/pip install --quiet packaging~=20.9 &&\
    /usr/src/req/bin/pip install --quiet lasso.requirements~=${lasso_requirements} &&\
    ln -s /usr/src/req/bin/requirement-report /usr/local/bin &&\
    : &&\
    : Now lasso.issues &&\
    python3 -m venv /usr/src/iss &&\
    /usr/src/iss/bin/pip install --quiet lasso.issues~=${lasso_issues} &&\
    ln -s /usr/src/iss/bin/add-version-label-to-open-bugs /usr/local/bin &&\
    ln -s /usr/src/iss/bin/milestones /usr/local/bin &&\
    ln -s /usr/src/iss/bin/move-issues /usr/local/bin &&\
    ln -s /usr/src/iss/bin/pds-issues /usr/local/bin &&\
    ln -s /usr/src/iss/bin/pds-labels /usr/local/bin &&\
    : &&\
    : Now twine which must be version 6.0.1 since older ones do not work with PyPI and newer ones are buggy &&\
    python3 -m venv /usr/src/twine &&\
    /usr/src/twine/bin/pip install --quiet twine==6.0.1 &&\
    rm -f /usr/local/bin/twine &&\
    ln -s /usr/src/twine/bin/twine /usr/local/bin &&\
    : &&\
    : Now install the Roundup Action &&\
    python3 -m venv /usr/src/roundup-venv &&\
    /usr/src/roundup-venv/bin/pip install --quiet /usr/src/roundup &&\
    :
