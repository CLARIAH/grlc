<!--
SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez

SPDX-License-Identifier: MIT
-->

Thank you very much for your interest in contributing to grlc! It's people like you that truly make the Semantic Web more accessible to everyone :)

## Communication channels

If you would like to get in touch with the grlc developers, and with other users of grlc, you can reach us in two ways:
 - Via Twitter, by using the grlc handle (**@grlcldapi**). Follow this account to hear about updates.
 - Via the grlc [mailing list](https://groups.google.com/g/grlc-list/). Sign up to the mailing list to ask questions and make suggestions.

## Filing bug reports

The official channel to file bug reports is via our GitHub's [issue tracker](https://github.com/CLARIAH/grlc/issues). When doing so make sure that:
- Your issue title briefly describes the bug
- You include log output (try `docker logs grlc_grlc_1` if you daemonized your instance)
- Name the file/module if known/available
- You tag your issue as **bug**

## Sending feature requests

As with bug reports, for requesting features please use the [issue tracker](https://github.com/CLARIAH/grlc/issues) as well and this time:
- Describe briefly the feature in the title
- Describe the desired feature
- Describe your use case so we understand what you are using grlc for
- Name the file/module if known/available
- Tag the issue as **enhancement**

## Sending pull requests

If you would like to contribute to the code directly, please send in a [pull request (PR)](https://github.com/CLARIAH/grlc/pulls). Please make sure that:
 - The title of your PR briefly describes the content
 - Describe in detail what your PR contributes
 - If your PR addresses a specific issue, indicate the issue number
 - Assign @albertmeronyo or @c-martinez as reviewer of your PR.

## Testing environment

To get started with hacking grlc, follow these steps to create a local testing environment (you'll need [docker](https://www.docker.com/) and [docker-compose](https://docs.docker.com/compose/)):

1. `docker pull clariah/grlc:latest`
2. `git clone https://github.com/CLARIAH/grlc`
3. `cd grlc`
4. Create a `docker-compose.yml` which matches your needs. For example:
```
version: '2'
services:
  grlc:
    build: ./
    restart: unless-stopped
    ports:
     - "8001:80"
    environment:
     - DEBUG=true
     - USERMAP_GID=1000
     - USERMAP_UID=1000
     - GRLC_GITHUB_ACCESS_TOKEN=xxx
     - GRLC_SERVER_NAME=grlc.io
```

5. `docker-compose up`
6. Your local grlc instance should be available at http://localhost:8001 and should respond to code modifications you make on `<GRLC_CLONE_PATH>`

You're good to pick any issue at the  [issue tracker](https://github.com/CLARIAH/grlc/issues) marked as **enhancement** and start implementing it :)

## Governance model

As creators of grlc, [@albertmeronyo](https://github.com/albertmeronyo) and [@c-martinez](http://github.com/c-martinez) are benevolent dictators for this project. This means that they have a final say of the direction of the project. This DOES NOT mean they are not willing to listen to suggestion (on the contrary, they *love* to hear new ideas)!

## Contributing

All grlc contributors will be listed in the [CONTRIBUTORS.md](CONTRIBUTORS.md) file. Also, [notes of new releases](https://github.com/CLARIAH/grlc/releases) will mention who contributed to that specific release.

## Questions

Please open an issue at the [issue tracker](https://github.com/CLARIAH/grlc/issues) and tag it as **question**
