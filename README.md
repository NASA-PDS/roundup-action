# 🤠 PDS Engineering Actions: Roundup

This is an [action for GitHub](https://github.com/features/actions) that does a "roundup"; that is, continuous integration and continuous delivery of [PDS](https://pds.nasa.gov/) software. (Somehow we got started on this "Western" kind of terminology and dadgum, we're stickin' with it 🤠.)


## ℹ️ Using this Action

To use this action in your own workflow, just provide it `with` any of the following parameters:

-   `assembly` — Tells what kind if roundup we're doing, such as `stable` (production) or `integration`; defaults to `unstable` or "development" releases; for details about assemblies, see below.
-   `packages` — A comma-separated list of extra packages (see "Environment", below) needed to complete your assembly.

For Maven-based roundups *only*, you can also specify these optional `with` parameters:

-   `maven-test-phases` — A comma-separated list of Maven phases for testing, defaults to `test`
-   `maven-doc-phases` — A comma-separated list of Maven phases for documentation generation, defaults to `package,site,site:stage`
-   `maven-build-phases` — A comma-separated list of Maven phases for building the software, defaults to `compile`
-   `maven-stable-artifact-phases` — A comma-separated list of Maven phases for stable artifact publication, defaults to `clean,package,site,deploy`
-   `maven-unstable-artifact-phases` — A comma-separated list of Maven phases for unstable artifact publication, defaults to `clean,site,deploy`

You'll also need this environment variable:

-   `ADMIN_GITHUB_TOKEN` — an access token that has administrative permissions in the repository; see below

Depending on the roundup, you may also need the following environment variables:

-   `pypi_username` — Username to use when registering a Python package
-   `pypi_password` — Password for `pypi_username`
-   `ossrh_username` — Username to use for uploading a snapshot [OSSRH](https://central.sonatype.org/pages/ossrh-guide.html) artifact
-   `ossrh_password` — Password for `ossrh_username`
-   `CODE_SIGNING_KEY` — GPG **private** key (base64 encoded) with which to sign artifacts


### 🍃 Environment

The Roundup Action uses the [NASA-PDS](https://github.com/NASA-PDS) [Github Actions Base](https://github.com/NASA-PDS/github-actions-base) as its starting environment. As of the time of this writing, this is [Alpine Linux 3.12](https://www.alpinelinux.org), [Python 3.8.5](https://www.python.org/), and [Apache Maven 3.6.3](https://maven.apache.org/), which in turns gives you [OpenJDK 1.8.0_252](https://openjdk.java.net/) (with `JAVA_HOME` defaulting to `/usr/lib/jvm/default-jvm`).

If you need a newer or older Java, or any other packages present in order to complete the unit tests, build, documentation, etc., steps of your roundup, you can use the `packages` variable to specify additional [Alpine Linux Packages](https://pkgs.alpinelinux.org/packages) that will be installed prior to starting. For example:

    with:
        packages: openjdk11-jdk,pdfgrep

This causes the Roundup to use OpenJDK 11 and also installs the `pdfgrep` package.


#### ☕️ Java Note

If you install a JDK older than OpenJDK 1.8.0_252, you may need to also set the `JAVA_HOME` environment variable, as the default `/usr/lib/jvm/default-jvm` will point to the newest.


### 👮‍♂️ GitHub Admin Token

The Roundup action must have access to various target repositories. This is afforded by a token, `ADMIN_GITHUB_TOKEN` in the environment. Note that the [NASA-PDS](https://github.com/NASA-PDS) organization already has an `ADMIN_GITHUB_TOKEN` in its [collection of secrets](https://github.com/organizations/NASA-PDS/settings/secrets/actions), so any repository within the organization inherits it.

But if you need to override it or set up a new token, do the following:

1.  Vist your GitHub account's Settings.
2.  Go to "Developer Settings".
3.  Go to "Personal access tokens".
4.  Press "Generate new token"; authenticate if needed.
5.  Add a note for the token, such as "PDS Ping Repo Access"
6.  Check the following scopes:
    -   `repo:status`
    -   `repo_deployment`
    -   `public_repo`
7. Press "Generate new token"

Save the token (a hex string) and install it in your source repository or organization:

1.  Visit the source repository's or organization's web page on GitHub.
2.  Go to "Settings".
3.  Go to "Secrets".
4.  Press "New secret".
5.  Name the secret, such as `ADMIN_GITHUB_TOKEN`, and insert the token's saved hex string as the value.
6.  Press "Add secret".

You can now (and _should_) destroy any saved copies of the token's hex string.


### 🔑 Code Signing Key

Signing code artifacts helps ensure that the code is not just created by who we say created it but that it's unmodified and free from inserted hacks like trojans or viruses. (Of course, it says nothing about the code's _quality_, which may be questionable or could itself _be_ a trojan or virus.) The Roundup uses the code signing key to automatically make these assertions by signing code artifacts it sends to the [OSSRH](https://central.sonatype.org/pages/ossrh-guide.html) (in the future, we could also sign Python artifacts sent to the [PyPI](https://pypi.org/)).

The [NASA-PDS](https://github.com/NASA-PDS) organization includes a `CODE_SIGNING_KEY` that all repositories within it inherit.

**📒 Note:** Whether _automatically signing artifacts_ is a safe practice is left for future discussion! 😩

To set up a your own code signing key for the Roundup action, first create an OpenPGP-compatible key pair using ``gpg`` or similar tool; for example, with [GnuPG 2.2](https://www.gnupg.org/), run ``gpg --full-generate-key``:

-   For the kind of key, choose "RSA (sign only)".
-   For the key length, 1024 bits is fine; 4096 is great.
-   For the expiration period, 0 is the least secure, and is what PDS recommends.
-   For the real name, your own name or a group moniker like `PDS Engineering Node` works.
-   For the email address, use your email address or a group email such as `pds-dev@jpl.nasa.gov`.
-   For the comment, mention that it's a code-signing key only; for example, use `SIGNING KEY ONLY from automated processes; trust accordingly`.
-   For the passphrase, skip it; use **no passphrase**.

Note the hex identifier of the generated key pair; use that to export the **private** key and encode it as [base-64](https://en.wikipedia.org/wiki/Base64), which you can then copy and paste into your repository's (or your organization's) secrets. For example, [macOS](https://www.apple.com/macos/) users could type:

    gpg --export-secret-keys HEX-KEY-ID | base64 | pbcopy

This puts the encoded private key onto your pasteboard, ready for pasting into GitHub. Use it as the value for `CODE_SIGNING_KEY`; see the demonstration `yaml` file below.

**📒 Note:** Don't forget to upload the corresponding _public_ key to various keyservers, such as keys.gnupg.net, keys.openpgp.org, keyserver.ubuntu.com pool.sks-keyservers.net, etc.


### 🧩 Assemblies

There are several different flavors of roundups that you can specify `with` the `assembly` parameter in your workflow. The flavor of assembly tells if you're doing a stable versus an unstable software release and what steps of the roundup to perform. They are as follows:

-   `stable` — this is the "standard" PDS assembly for stable software releases. It does the steps of unit testing, integration testing, documentation generation, software building, artifact publication, requirements generation, changelog generation, GitHub releasing, and documentation publication. Because it's a "stable" assembly, it sends all this to production servers; that means non-SNAPSHOT releases to OSSRH for Maven artifacts, the production PyPI for Python artifacts, etc.
-   `unstable` — this is the same as the `stable` PDS assembly but for unstable software releases. It does all the same steps as the stable assembly, but OSSRH artifacts are marked as `SNAPSHOT`s, the `test.pypi.org` is used instead of `pypi.org`, etc. This is the default if you don't specify an assembly.
-   `integration` — this is the same as the `unstable` PDS assembly, but omits the requirements generation and changelog generation steps.
-   `noop` — this is an assembly that does nothing, i.e., "no operation".
-   `env` — this is an assembly whose steps are defined by environment variables:
    -   `ROUNDUP_STABLE` set to `1` or `true` for a stable assembly, unstable otherwise
    -   `ROUNDUP_STEPS` set to a comam-separated list of step names to execute, such as `test,docs`


### 🛫 Releases

The Roundup includes built-in support to make official releases of software, publishing artifacts to well-known repositories, and including release archives on GitHub. The [PDS Java Template Repository](https://github.com/NASA-PDS/pds-template-repo-java) (historically called the "generic template") and the [PDS Python Template Repository](https://github.com/NASA-PDS/pds-template-repo-python) (historically called the Python template) have the correct GitHub Actions workflows to support this. If you create a new PDS repository from those templates, you're all set to roundup! Yee-haw!

To make an offical release of software version `VERSION`, create a branch called `release/VERSION` and push it to GitHub. For example, to release version 2.0.17 of your software based on the latest `main`:
```console
$ git checkout main
$ git pull
$ git branch --track release/2.0.17
$ git push origin release/2.0.17
```


## 💁‍♀️ Demonstration

The following is a brief example how a workflow that shows how this action can be used:

```yaml
name: 📦 Unstable CI/CD

on:
    push:
      branches:
          - main
        paths-ignore:
            - 'CHANGELOG.md'
            - 'docs/requirements/**'
jobs:
    unstable-roundup:
        name: 🤠 Unstable Roundup
        runs-on: ubuntu-latest
        if: github.actor != 'pdsen-ci'
        steps:
            - 
                name: 💳 Checking out repository
                uses: actions/checkout@v2
                with:
                    lfs: true
                    fetch-depth: 0
                    token: ${{secrets.ADMIN_GITHUB_TOKEN}}
            -
                name: 🐄 Rounding it up
                uses: NASA-PDS/roundup-action@main
                with:
                    assembly: unstable
                    packages: cowpoke,chili-sort,lasso
                env:
                    ADMIN_GITHUB_TOKEN: ${{secrets.pat}}
                    CODE_SIGNING_KEY:   ${{secrets.CODE_SIGNING_KEY}}
                    ossrh_username:     jocowboy
                    ossrh_password:     ${{secrets.OSSRH_PASSWORD}}
                    pypi_username:      snakewrangler
                    pypi_password:      ${{secrets.PYPI_PASSWORD}}
```


## 🔧 Development

Make a local image for testing:

    docker image build --tag pds-roundup:latest .

You can then poke around in it:

    docker container run --interactive --tty --rm --name roundup --volume ${PWD}:/mnt --entrypoint /bin/sh pds-roundup:latest

But you could also invoke it the way GitHub Actions does; for example:

    docker container run --interactive --tty --rm --name roundup-dev --workdir /github/workspace \
        --env INPUT_MODE --env HOME --env GITHUB_JOB --env GITHUB_REF --env GITHUB_SHA --env GITHUB_REPOSITORY \
        --env GITHUB_REPOSITORY_OWNER --env GITHUB_RUN_ID --env GITHUB_RUN_NUMBER --env GITHUB_ACTOR \
        --env GITHUB_WORKFLOW --env GITHUB_HEAD_REF --env GITHUB_BASE_REF --env GITHUB_EVENT_NAME \
        --env GITHUB_SERVER_URL --env GITHUB_API_URL --env GITHUB_GRAPHQL_URL \
        --env GITHUB_ACTION --env GITHUB_EVENT_PATH --env GITHUB_PATH --env GITHUB_ENV --env RUNNER_OS \
        --env RUNNER_TOOL_CACHE --env RUNNER_TEMP --env RUNNER_WORKSPACE --env ACTIONS_RUNTIME_URL \
        --env ACTIONS_RUNTIME_TOKEN --env ACTIONS_CACHE_URL --env GITHUB_ACTIONS=true --env CI=true \
        --env GITHUB_WORKSPACE=/github/workspace \
        --env GITHUB_TOKEN=$(cat my-dev-token.txt) \
        --env ADMIN_GITHUB_TOKEN=$(cat my-dev-token.txt) \
        --env pypi_username=joe_cowboy4life \
        --env pypi_password=s3cr3t \
        --env ossrh_username=java_cowboy4life \
        --env ossrh_password=m0rec0ff33 \
        --env GITHUB_REPOSITORY=joecowboy/test-repo \
        --volume /Users/joe/Documents/Development/test-repo:"/github/workspace" \
        pds-roundup --debug --assembly unstable

Or build it to run outside of a container; for example:

    python3 -m venv venv
    venv/bin/pip install --quiet --upgrade setuptools wheel pip
    venv/bin/pip install --editable .

Then add `venv/bin/pip` to your `PATH` and use the convenience script, `support/run-roundup.sh`:

    cd my-project-directory
    ../roundup-action/support/run-roundup.sh unstable

Note that to use `run-roundup.sh` you need to set quite a few other environment variables, prepare some files, and ensure certain commands are on the `PATH`. See the comments in the script for details.
