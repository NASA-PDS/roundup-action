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
RUN        pip uninstall --no-input --yes pds-github-util && python3 setup.py install --optimize=2
ENTRYPOINT ["/usr/local/bin/roundup"]
