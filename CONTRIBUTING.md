Thank you very much for your interest in contributing to grlc! It's people like you that truly make the Semantic Web more accessible to everyone :)

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

## Questions

Please open an issue at the [issue tracker](https://github.com/CLARIAH/grlc/issues) and tag it as **question**
