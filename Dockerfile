# 🤠 PDS Engineering: Roundup
# ============================

FROM nasapds/pds-github-actions-base:latest


# Metadata
# --------

LABEL "com.github.actions.name"="PDS Roundup"


# Image Details
# -------------

WORKDIR    /usr/src/roundup
COPY       README.md CHANGELOG.md LICENSE.txt setup.cfg setup.py ./
COPY       src/ ./src
RUN        python3 setup.py --quiet install --optimize=2
ENTRYPOINT ["/usr/local/bin/roundup"]
