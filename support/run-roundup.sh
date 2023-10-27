#!/bin/sh
#
#
# Convenience script to run the Roundup outside of Docker or GitHub Action.
# This assumes that the `roundup` executable is on your PATH. Run this inside of a
# checked-out project directory, whether it's Python or Java.
#
# Typical usage:
#
# cd roundup-action
# python3 -m venv venv
# venv/bin/pip install --quiet --upgrade pip setuptools wheel
# venv/bin/pip install --editable .
# export PATH=${PWD}/venv/bin:${PWD}/support:${PATH}
# cd ../some-package-i-want-to-roundup
# run-roundup.sh unstable preparation,unitTest
#
# If you don't give any steps (like `preparation,unitTest`) you get a default
# set. HOWEVER, only skip steps if you know what you're doing! For example, in
# Python repositories, the `preparation`` step sets the PATH to include the
# venv against which the project's being roudned up. Skip that and later steps
# which rely on that environment may fail.
#
# Note: you'll need a ~/.secrets/github-roundup.token containing a GitHub API
# token with the scopes repo:status, repo_deployment, and public_repo. You'll
# also need a ~/.secrets/roundup.sh file with Bourne shell statements that
# export your PyPI and Sonatype OSSRTH usernames and passwords, such as:
#
# export pypi_username=USERNAME
# export pypi_password=PASSWORD
# export ossrh_username=USERNAME
# export ossrh_password=PASSWORD
#
# You'll also need these on your PATH:
#
# gem install --silent github_changelog_generator --version 1.16.4
# pip install --quiet sphinx==3.2.1 sphinx-argparse==0.2.5 sphinx-rtd-theme==0.5.0 twine==3.4.2
#
# i.e., the executables `github_changelog_generator` and `sphinx-build`
# with `sphinx_rtd_theme` enabled.
#
# You'll also need the `deploy.sh` script:
#
# curl --location 'https://github.com/X1011/git-directory-deploy/raw/master/deploy.sh' > $HOME/bin/deploy.sh
# chmod 755 $HOME/bin/deploy.sh
#
# Then add `~/bin` to your PATH.


# Constantly
defaultSteps="preparation,unitTest,integrationTest,changeLog,requirements,docs,versionBump,build,githubRelease,artifactPublication,docPublication,versionCommit,cleanup"

# Check args
if [ "$#" -lt 2 -o "$#" -gt 3 ]; then
    echo "Usage `basename $0` {stable|unstable} OWNER/REPO [step,step,…]" 1>&2
    echo "Where OWNER = GitHub owner or organization and REPO = repository name" 1>&2
    echo "Default steps are: $defaultSteps" 1>&2
    exit 1
fi
if [ "$1" != "stable" -a "$1" != "unstable" ]; then
    echo "First argument must be 'stable' or 'unstable'" 1>&2
    exit 1
fi

# Check for required files
if [ ! -f "${HOME}/.secrets/github-roundup.token" ]; then
    echo "No github-roundup.token file found; aborting" 1>&2
    exit 1
fi
if [ ! -f "${HOME}/.secrets/roundup.sh" ]; then
    echo "No roundup.sh found; aborting" 1>&2
    exit 1
fi
. ${HOME}/.secrets/roundup.sh

# Check required env vars
if [ -z "${pypi_username} " -o -z "${pypi_password}" ]; then
    echo "The pypi_username and pypi_password must be set in ~/.secrets/roundup.sh, always" 1>&2
    exit 1
fi
if [ -z "${ossrh_username}" -o -z "${ossrh_password}" ]; then
    echo "The ossrh_username and ossrh_password mut be set in ~/.secrets/roundup.sh, always" 1>&2
fi

# Set additional env vars
[ "$1" == "stable" ] && stable=true || stable=false
export ADMIN_GITHUB_TOKEN=`cat ${HOME}/.secrets/github-roundup.token`
export GITHUB_TOKEN=$ADMIN_GITHUB_TOKEN
export ROUNDUP_STABLE="$stable"
export ROUNDUP_STEPS=${3:-$defaultSteps}
export GITHUB_REPOSITORY=$2
export GITHUB_WORKSPACE=${PWD}
# Yes GITHUB_ACTIONS should be true to fully simulate things, but we specifically want to check if we need
# to update credentials in /root (GitHub Actions) or $HOME (everywhere else)
export GITHUB_ACTIONS=false
export CI=true

# These are set by GitHub Actions but are otherwise not needed by Roundup…YET.
export ACTIONS_CACHE_URL=''
export ACTIONS_RUNTIME_TOKEN=''
export ACTIONS_RUNTIME_URL=''
export GITHUB_ACTION=''
export GITHUB_ACTOR=''
export GITHUB_API_URL=''
export GITHUB_BASE_REF=''
export GITHUB_ENV=''
export GITHUB_EVENT_NAME=''
export GITHUB_EVENT_PATH=''
export GITHUB_GRAPHQL_URL=''
export GITHUB_HEAD_REF=''
export GITHUB_JOB=''
export GITHUB_PATH=''
export GITHUB_REF=''
export GITHUB_REPOSITORY_OWNER=''
export GITHUB_RUN_ID=''
export GITHUB_RUN_NUMBER=''
export GITHUB_SERVER_URL=''
export GITHUB_SHA=''
export GITHUB_WORKFLOW=''
export INPUT_MODE=''
export RUNNER_OS=''
export RUNNER_TEMP=''
export RUNNER_TOOL_CACHE=''
export RUNNER_WORKSPACE=''

# Do it (assuming "roundup" is on the PATH)
exec roundup --debug --assembly env
