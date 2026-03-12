# Manage DataLad Siblings

Helper commands are preview-first: they show the planned `datalad` command without executing it. Pass `--yes` to execute.

## GitHub

Preview:

```bash
projio sibling -C . github
```

Execute:

```bash
projio sibling -C . github --yes
```

Override the target repo name:

```bash
projio sibling -C . github --project my-repo --yes
```

## GitLab

```bash
projio sibling -C . gitlab
projio sibling -C . gitlab --project sirotalab/my-repo --yes
```

## RIA

```bash
projio sibling -C . ria
projio sibling -C . ria --alias mydataset --yes
```

## Configuration

Sibling defaults live in `.projio/config.yml` under `helpers.sibling`:

```yaml
helpers:
  sibling:
    github:
      sibling: github
      credential: github
      project_template: "{project_name}"
    gitlab:
      sibling: gitlab
      credential: gitlab-lrz
      project_template: "sirotalab/{project_name}"
    ria:
      sibling: origin
      alias_strategy: basename
      storage_url: ria+file:///storage/share/git/ria-store
      shared: group
```

Credential names can safely live in `.projio/config.yml`. Actual secrets should remain in DataLad's credential store or in environment variables.

## Check infrastructure state

```bash
projio auth -C . doctor
```

Reports GitHub access protocol, GitLab site config, configured remotes, and RIA storage URL.
