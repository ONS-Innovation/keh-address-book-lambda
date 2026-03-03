# Contributing

Thanks for your interest in contributing to the Address Book Lambda. We're happy to have you here.

Please take a moment to review this document before submitting your first pull request. We also strongly recommend that you check for open issues and pull requests to see if someone else is working on something similar.

If you need any help, feel free to reach out to the development team.

## About this repository

The Address Book Lambda is a GitHub Scraping utility designed to gather organisation users' emails for use within the [Digital Landscape](https://github.com/ONSdigital/keh-digital-landscape).

This repository contains:

- Lambda code (Python)
- Terraform (AWS infrastructure) and Concourse (automated deployment)
- GitHub Actions (linting + formatting)
- MkDocs (supplementary docs)

## Structure

```bash
.
├── .github
│   └── workflows # GitHub Actions
├── concourse # CICD
├── docs # MkDocs
├── src # Lambda definition
├── terraform # AWS Infrastructure
├── tests # Automated tests
└── README.md # Getting Started
```

## Development

To get started with development, please see the instructions in the [README](./README.md).

To get a further understanding of the project, we have docs available within the [`./docs` directory](./docs/)
or on our [MkDocs deployment](https://ons-innovation.github.io/keh-address-book-lambda/).

## Documentation

A guide on our documentation is available within the [README](./README.md).

## Commit Convention

Before you create a Pull Request, please check whether your commits comply with
the commit conventions used in this repository.

When you create a commit we kindly ask you to follow the convention
`category(scope or module): message` in your commit message while using one of
the following categories:

- `feat / feature`: all changes that introduce completely new code or new
  features
- `fix`: changes that fix a bug (ideally you will additionally reference an
  issue if present)
- `refactor`: any code-related change that is not a fix nor a feature
- `docs`: changing existing or creating new documentation (i.e. README, docs for
  usage of a library or CLI usage)
- `build`: all changes regarding the build of the software, changes to
  dependencies or the addition of new dependencies
- `test`: all changes regarding tests (adding new tests or changing existing
  ones)
- `ci`: all changes regarding the configuration of continuous integration (i.e.
  GitHub Actions, CI system)
- `chore`: all changes to the repository that do not fit into any of the above
  categories

  e.g. `feat(components): add new prop to the avatar component`

If you are interested in the detailed specification you can visit
https://www.conventionalcommits.org/ or check out the
[Angular Commit Message Guidelines](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#-commit-message-guidelines).

## Pull Request Template

Please squash your commits into a single commit when merging your pull request.

Ensure the title of the pull request is descriptive, concise and follows the branch naming convention.

```bash
TICKET-NUMBER - description
```

e.g. `KEH-123 - Added new feature`

## Branch Naming Convention

Please use the following naming convention for your branches:

```bash
TICKET-NUMBER-description
```

e.g. `KEH-123-add-new-feature`

For patches or bug fixes, please use the following naming convention:

```bash
TICKET-NUMBER-PATCH-NUMBER
```

e.g. `KEH-123-patch-1`

## Testing

All tests are available in the [`./tests` directory](./tests/).

Documentation about our tests (i.e. how to run them) is available in the [README](./README.md).

## Continuous Integration

For a pull request to be merged, all Continuous Integration (CI) actions must pass. These actions ensure code quality, proper formatting, and functional correctness. Please review any failed CI checks and address the reported issues before requesting a merge.

Please ensure that all tests are passing when submitting a pull request. If you're adding new features, please include tests.
