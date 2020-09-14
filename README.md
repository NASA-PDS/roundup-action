# 📡 PDS Engineering Actions: Roundup

This is an [action for GitHub](https://github.com/features/actions) that does a "roundup"; that is, continuous integration and continuous delivery of PDS software. (Somehow we got started on this "Western" kind of terminology and dadgum, we're sticin' with it 🤠.)


## ℹ️ Using this Action

To use this action in your own workflow, just provide it `with` the following parameters:

- `mode` — Tells what kind if roundup we're doing, such as `stable` (production); defaults to unstable or "development" releases.


Depending on the roundup mode, you may also need the following environment variables:

- `ADMIN_GITHUB_TOKEN` — an access token that has administrative permissions in the repository; see below
- `pypi_username` — Optional username to use when registering a package
- `pypi_password` — Password for `pypi_username`

Note that `GITHUB_TOKEN` is automatically provided by the GitHub Actions system.


### 👮‍♂️ GitHub Admin Token

This action must havea access to various target repositories. This is afforded by the `token`. To set up such a token:

1. Vist your GitHub account's Settings.
2. Go to "Developer Settings".
3. Go to "Personal access tokens".
4. Press "Generate new token"; authenticate if needed.
5. Add a note for the token, such as "PDS Ping Repo Access"
6. Check the following scopes:
    - `repo:status`
    - `repo_deployment`
    - `public_repo`
7. Press "Generate new token"

Save the token (a hex string) and install it in your source repository:

1. Visit the source repository's web page on GitHub.
2. Go to "Settings".
3. Go to "Secrets".
4. Press "New secret".
5. Name the secret, such as `ADMIN_GITHUB_TOKEN`, and insert the token's saved hex string as the value.
6. Press "Add secret".

You can now (and should) destroy any saved copies of the token's hex string.



## 💁‍♀️ Demonstration

The following is a brief example how a workflow that shows how this action can be used:

```yaml
```


## 🔧 Development

Make a local image for testing:

```console
docker image build --tag pds-roundup:latest .
docker container run --interactive --tty --rm --name roundup --volume ${PWD}:/mnt --entrypoint /bin/sh pds-roundup:latest
```

Or run it locally:

```console
env ADMIN_GITHUB_TOKEN=abc123 GITHUB_REPOSITORY=owner/repo GITHUB_WORKSPACE=/tmp PATH=${PWD}/bin:${PATH} ${PWD}/bin/roundup --debug --mode unstable
```
