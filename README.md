# githubstar

Export GitHub starred repositories, lists and topics to HTML, JSON, Markdown, or bookmark, grouped by language or topic, ordered by time, stargazer count etc.

## Installation

- Using [pip](https://pypi.org/project/githubstar/)

```
$ pip install githubstar
```

- Using Binaries (x64 architecture only) from [Release page](https://github.com/kevinapps/githubstar/releases)

- You can also clone the repo and build from source

## Quick Start

Run with a username

```
$ githubstar --username <username>
```

Run with username, GitHub access token, and default options

```
$ export GITHUB_TOKEN=<Access-Token>
$ githubstar --username <username>
```

or

```
$ githubstar --username <username> --token <Access-Token>
```

Export to json format

```
$ githubstar --username <username> --token <Access-Token> --format json
```

Run with language grouping and bookmark format

```
$ githubstar --username <username> --token <Access-Token> --format bookmark --groupby language
```

## Usage

```
$ githubstar -h

usage: githubstar [-h] [--version] --username USERNAME [--token TOKEN] [--format {html,json,md,bookmark}]
                [--groupby {none,language,topic}]
                [--orderby {timestarred,timeupdated,alphabet,starscount,forkscount,language}]
                [--orderdirection {desc,asc}] [--ordernum {true,false}] [--excludeprivate {true,false}]
                [--destpath DESTPATH] [--destname DESTNAME]

Export a GitHub user's starred list to local file.

options:
  -h, --help            show this help message and exit
  --version             show the program's version number and exit
  --username USERNAME   [required]username to export for
  --token TOKEN         the token from https://github.com/settings/tokens, to avoid rate limiting, can also store in
                        environment as 'GITHUB_TOKEN'.
  --format {html,json,md,bookmark}
                        output format, default: html
  --groupby {none,language,topic}
                        default: none
  --orderby {timestarred,timeupdated,reponame,starscount,forkscount,language}
                        default: timestarred
  --orderdirection {desc,asc}
                        default: desc
  --ordernum {true,false}
                        choose whether to display the order number before the repository name, default: true
  --excludeprivate {true,false}
                        exclude private repositories, default: false
  --destpath DESTPATH   path to store the exported file
  --destname DESTNAME   filename of the exported file
```

## FAQ

- What does 'RateLimitExceededException' mean?

  The GitHub API rate limiting has been reached. An access token is needed in this case. Check out this link [https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting](https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting) for more details.

- Where to get the access token?

  Log in with your GitHub account and go to the following pages to generate an access token. Either a fine-grained token or a classic token is acceptable.
  - [https://github.com/settings/personal-access-tokens](https://github.com/settings/personal-access-tokens)
  - [https://github.com/settings/tokens](https://github.com/settings/tokens)

## License

This project is licensed under the GNU Affero General Public License v3.0.

You can find the full license text in the [LICENSE](LICENSE) file.
