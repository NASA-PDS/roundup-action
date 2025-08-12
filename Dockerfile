# 🤠 PDS Engineering: Roundup
# ============================

# Note: the github-actions-base image's `stable` tag should eventually be
# on Python 3.13, but for now the image tagged `python3.13` will do fine.

FROM nasapds/github-actions-base:python3.13


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
    python3 -m venv --system-site-packages /usr/src/rel &&\
    : Normally we would use lasso.releasers~=${lasso_releasers} but we are transitioning Python 3.13 &&\
    : should be → /usr/src/rel/bin/pip install --quiet lasso.releasers~=${lasso_releasers} ← &&\
    : so do this for now: &&\
    /usr/src/rel/bin/pip install --quiet git+https://github.com/NASA-pds/lasso-releasers.git@python3.13 &&\
    ln -s /usr/src/rel/bin/maven-release /usr/local/bin &&\
    ln -s /usr/src/rel/bin/nodejs-release /usr/local/bin &&\
    ln -s /usr/src/rel/bin/python-release /usr/local/bin &&\
    ln -s /usr/src/rel/bin/snapshot-release /usr/local/bin &&\
    : &&\
    : Next, lasso.requirements, which for some reason needs an upgraded pip AND ALSO cannot use system-site-packages &&\
    : because Sphinx 8.2.3 in the base image requires packaging ≥ 23.0 and lasso-requirements needs packaging ≅ 20.9 &&\
    python3 -m venv /usr/src/req &&\
    /usr/src/req/bin/pip install --quiet --upgrade pip &&\
    : Normally we would use lasso-requirements~=${lasso_requirements} but we are transitioning Python 3.13 &&\
    : should be → /usr/src/req/bin/pip install --quiet lasso-requirements~=${lasso_requirements} ← &&\
    : so do this for now: &&\
    /usr/src/req/bin/pip install --quiet git+https://github.com/NASA-pds/lasso-requirements.git@python3.13 &&\
    ln -s /usr/src/req/bin/requirement-report /usr/local/bin &&\
    : &&\
    : Now lasso.issues &&\
    python3 -m venv /usr/src/iss &&\
    : Normally we would use lasso.issues~=${lasso_issues} but we are transitioning Python 3.13 &&\
    : should be → /usr/src/iss/bin/pip install --quiet lasso.issues~=${lasso_issues} ← &&\
    : so do this for now: &&\
    /usr/src/iss/bin/pip install --quiet git+https://github.com/NASA-pds/lasso-issues.git@python3.13 &&\
    ln -s /usr/src/iss/bin/add-version-label-to-open-bugs /usr/local/bin &&\
    ln -s /usr/src/iss/bin/milestones /usr/local/bin &&\
    ln -s /usr/src/iss/bin/move-issues /usr/local/bin &&\
    ln -s /usr/src/iss/bin/pds-issues /usr/local/bin &&\
    ln -s /usr/src/iss/bin/pds-labels /usr/local/bin &&\
    : &&\
    : Now install the Roundup Action &&\
    python3 -m venv /usr/src/roundup-venv &&\
    /usr/src/roundup-venv/bin/pip install --quiet /usr/src/roundup &&\
    :
