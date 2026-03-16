# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDS Roundup Action is a GitHub Action that performs continuous integration and delivery ("roundup") for NASA Planetary Data System (PDS) software projects. It supports three build contexts: Python, Maven (Java), and Node.js. The action runs inside a Docker container based on Alpine Linux with pre-installed tools.

## Architecture

### Context-Based Design

The roundup uses a **context pattern** to detect and handle different project types:

- **Context Detection** (`context.py`): Automatically detects project type by looking for marker files:
  - Python: `setup.cfg` or `setup.py`
  - Maven: `pom.xml` or `project.xml`
  - Node.js: `package.json` or `package-lock.json`

- **Context Factory** (`util.py:contextFactories()`): Returns the appropriate context class based on detected files

### Assembly System

An **Assembly** (`assembly.py`) defines which steps to execute and whether it's a stable or unstable release:

- `stable` — Production release (non-SNAPSHOT for Maven, production PyPI, version without suffix for npm)
- `unstable` — Development release (SNAPSHOT for Maven, test.pypi.org, `-unstable` suffix for npm)
- `integration` — Like unstable but omits requirements and changelog generation
- `noop` — Does nothing (used for testing)
- `env` — Steps defined by environment variables `ROUNDUP_STABLE` and `ROUNDUP_STEPS`

Each assembly executes a predefined sequence of **Steps**.

### Step System

Steps (`step.py`) are individual operations in the roundup pipeline. Standard PDS steps:

1. `preparation` — Set up environment (create venv, install deps, configure credentials)
2. `unitTest` — Run unit tests
3. `integrationTest` — Run integration tests (mostly TBD)
4. `docs` — Generate documentation
5. `versionBump` — Update version numbers from `release/X.Y.Z` tag
6. `build` — Build artifacts (wheel, jar, npm package)
7. `artifactPublication` — Publish to PyPI/OSSRH/npmjs.com
8. `requirements` — Generate PDS requirements file
9. `changeLog` — Generate changelog using `github_changelog_generator`
10. `githubRelease` — Create GitHub release and tags
11. `docPublication` — Upload docs as release asset and to gh-pages (stable only)
12. `versionCommit` — Commit the bumped version
13. `cleanup` — Bump to next dev version, delete release tag

Each context (Python/Maven/Node.js) implements context-specific versions of these steps.

### Context-Specific Implementations

- **Python Context** (`_python.py`):
  - Uses venv with system-site-packages
  - Runs tests via tox or `setup.py test`
  - Builds wheels with `bdist_wheel`
  - Uses twine for PyPI uploads
  - Version stored in `VERSION.txt`

- **Maven Context** (`_maven.py`):
  - Creates Maven `settings.xml` with OSSRH credentials
  - Imports GPG key for code signing
  - Executes configurable Maven phases (test, build, deploy, etc.)
  - Version stored in `pom.xml` files

- **Node.js Context** (`_nodejs.py`):
  - Creates `.npmrc` with authentication token
  - Version stored in `package.json`
  - Uses npm for building and publishing
  - Handles `-unstable` suffix for development releases

## Development

### Local Testing

Build and test the Docker image locally:

```bash
# Build the image
docker image build --tag pds-roundup:latest .

# Interactive shell for exploration
docker container run --interactive --tty --rm --name roundup \
  --volume ${PWD}:/mnt --entrypoint /bin/sh pds-roundup:latest

# Run as GitHub Actions does (requires many environment variables)
# See README.md "Development" section for full example
```

### Local Development with Virtual Environment

```bash
# Create and activate venv
python3 -m venv venv
venv/bin/pip install --quiet --upgrade setuptools wheel pip
venv/bin/pip install --editable .

# Add to PATH and use support script
export PATH="${PWD}/venv/bin:${PATH}"
cd /path/to/test-project
../roundup-action/support/run-roundup.sh unstable
```

### Running Tests

The project structure suggests tests would be in a `test` directory (excluded in `setup.cfg`), but specific test commands are not documented. If tests exist:

```bash
pip install --editable .[dev]
pytest  # or tox if configured
```

## Key Design Patterns

### Version Bumping Flow

For stable releases:
1. User creates `release/X.Y.Z` tag
2. `versionBump` step extracts X.Y.Z from tag and writes to version file
3. `versionCommit` step commits the version file
4. `githubRelease` creates `vX.Y.Z` tag at HEAD
5. `cleanup` bumps minor version (X.(Y+1).0) for next dev cycle

### Tag Management

- Release tags: `release/X.Y.Z` (trigger stable builds)
- Version tags: `vX.Y.Z` (created by roundup)
- Dev/SNAPSHOT tags: Pruned before releases
- Release tags deleted after cleanup

### Error Handling

- Stable builds fail hard on errors
- Unstable builds are more tolerant (e.g., duplicate PyPI uploads ignored)
- Each step can implement its own error handling

## Environment Variables

Required for operation (depending on context):
- `ADMIN_GITHUB_TOKEN` — GitHub token with repo access
- `GITHUB_REPOSITORY` — Owner/repo name
- `CODE_SIGNING_KEY` — Base64-encoded GPG private key (Maven)
- `pypi_username`, `pypi_password` — PyPI credentials (Python)
- `ossrh_username`, `ossrh_password` — OSSRH credentials (Maven)
- `NPMJS_COM_TOKEN` — npm token with @nasapds scope access (Node.js)

## GitHub Actions Inputs

Configurable via workflow `with` parameters:
- `assembly` — Type of roundup (stable/unstable/integration/noop/env)
- `packages` — Comma-separated Alpine packages to install
- `maven-*-phases` — Maven phases for different operations
- `documentation-dir` — Override default doc directory

## Dependencies

Fixed versions in `setup.cfg` that must match `nasapds/github-actions-base`:
- github3.py, lxml, packaging, requests, sphinx, twine, wheel
- External tools: `maven-release`, `python-release`, `nodejs-release`, `requirement-report`, `github_changelog_generator`

## Git Workflow

The roundup makes commits and pushes to `origin main`:
- Uses `pdsen-ci@jpl.nasa.gov` / `PDSEN CI Bot` for commits
- Commits: version files, changelogs, requirements
- Always uses `--force` for push to `HEAD:main` (to handle detached HEAD in Actions)
- Configures `/github/workspace` as safe directory for git 2.36+
