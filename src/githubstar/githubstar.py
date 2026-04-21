# githubstar - Export Github starred repos list to file
# Copyright (C) 2026 kevinapps@github
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import os.path
import sys
from argparse import ArgumentParser
from math import ceil

from github import Github
from urllib3 import Retry

from .fileexporter import StarsExporter
from .starredfetcher import StarredFetcher
from .utils import Utils
from .version import VERSION


def getFilePathName(args):
    if args.destname:
        filename = args.destname
    else:
        dateBackup = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        prefixname = "github-stars-" + args.username
        match args.format:
            case "bookmark":
                filename = prefixname + "-" + "bookmark" + "-" + dateBackup + ".html"
            case "md":
                filename = prefixname + "-" + dateBackup + ".md"
            case "json":
                filename = prefixname + "-" + dateBackup + ".json"
            case _:
                filename = prefixname + "-" + dateBackup + ".html"
    if args.destpath:
        if os.path.exists(args.destpath) and os.path.isdir(args.destpath):
            filename = os.path.normpath(os.path.join(args.destpath + "\\", filename))
        else:
            print("Invalid destpath:" + args.destpath, file=sys.stderr)
            sys.exit()
    return filename


def starred_repos(user):
    starred = user.get_starred()
    total_pages = ceil(starred.totalCount / 30)
    for page_num in range(0, total_pages):
        for repo in starred.get_page(page_num):
            yield repo
        Utils.printProgress(int(75 * (page_num + 1) / total_pages), 22)


def retryConfig(backoff_factor=1.0, total=8):
    """urllib3 will sleep for:
        {backoff factor} * (2 ** ({number of total retries} - 1))
    Recalculates and Overrides Retry.DEFAULT_BACKOFF_MAX"""
    Retry.DEFAULT_BACKOFF_MAX = backoff_factor * 2 ** (total - 1)
    return Retry(total=total, backoff_factor=backoff_factor)


def parse_args():
    parser = ArgumentParser(
        prog="githubstar",
        description="Export a GitHub user's starred list to local file.",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument(
        "--username",
        dest="username",
        required=True,
        help="[required]username to export from",
    )
    parser.add_argument(
        "--token",
        dest="token",
        required=False,
        help="token from https://github.com/settings/tokens, to avoid rate-limiting, can also store in environment as 'GITHUB_TOKEN'.",
    )
    parser.add_argument(
        "--format",
        dest="format",
        default="html",
        required=False,
        choices=["html", "bookmark", "md", "json"],
        help="output format, default: html",
    )
    parser.add_argument(
        "--groupby",
        dest="groupby",
        default="none",
        required=False,
        choices=["none", "language", "topic"],
        help="default: none",
    )
    parser.add_argument(
        "--orderby",
        dest="orderby",
        default="timestarred",
        required=False,
        choices=[
            "timestarred",
            "timeupdated",
            "reponame",
            "starscount",
            "forkscount",
            "language",
        ],
        help="default: timestarred",
    )
    parser.add_argument(
        "--orderdirection",
        dest="orderdirection",
        default="desc",
        required=False,
        choices=["desc", "asc"],
        help="default: desc",
    )
    parser.add_argument(
        "--ordernum",
        dest="showOrderNum",
        default="true",
        required=False,
        choices=["true", "false"],
        help="show order number before repository name or not, default: true",
    )
    parser.add_argument(
        "--excludeprivate",
        dest="excludeprivate",
        default="false",
        required=False,
        choices=["true", "false"],
        help="exclude private repositories, default: false",
    )
    parser.add_argument(
        "--destpath",
        dest="destpath",
        required=False,
        help="path to store the exported file",
    )
    parser.add_argument(
        "--destname",
        dest="destname",
        required=False,
        help="filename of the exported file",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.username:
        print("Please set `--username` to a valid GitHub user name.", file=sys.stderr)
        sys.exit(1)

    showOrderNum = args.showOrderNum == "true"
    timestart = datetime.datetime.now().timestamp()
    filePathName = getFilePathName(args)
    token = args.token
    if not token:
        token = os.getenv("GITHUB_TOKEN")

    Utils.printProgress(0)
    fetcher = StarredFetcher(args.username)
    fetcher.fetch()
    Utils.printProgress(20)

    gh = (
        Github(token, retry=retryConfig())
        if args.token
        else Github(retry=retryConfig())
    )
    user = gh.get_user(args.username)
    Utils.printProgress(21)
    repos = []
    for repo in starred_repos(user):
        if repo.private and args.excludeprivate == "true":
            continue
        repos.append(repo)

    StarsExporter.exportToFile(
        args,
        repos,
        fetcher.starredTopics,
        fetcher.starredLists,
        filePathName,
        showOrderNum,
    )

    Utils.printProgress(100)
    print(
        "\nExport completed, time cost:",
        str(int(datetime.datetime.now().timestamp() - timestart)),
        "secs.",
    )


if __name__ == "__main__":
    main()
