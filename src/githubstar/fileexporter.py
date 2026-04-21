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

import html
import json
from collections import OrderedDict

from .topicsinfo import TopicsInfo


class StarsExporter(object):
    def sortRepos(repos, orderby, orderdirection):
        match orderby, orderdirection:
            case "timeupdated", "asc":
                repos.sort(key=lambda x: (x.pushed_at))
            case "timeupdated", "desc":
                repos.sort(key=lambda x: (x.pushed_at), reverse=True)
            case "reponame", "asc":
                repos.sort(key=lambda x: (x.name if x.name else ""))
            case "reponame", "desc":
                repos.sort(key=lambda x: (x.name if x.name else ""), reverse=True)
            case "starscount", "asc":
                repos.sort(key=lambda x: (x.stargazers_count))
            case "starscount", "desc":
                repos.sort(key=lambda x: (x.stargazers_count), reverse=True)
            case "forkscount", "asc":
                repos.sort(key=lambda x: (x.forks_count))
            case "forkscount", "desc":
                repos.sort(key=lambda x: (x.forks_count), reverse=True)
            case "language", "asc":
                repos.sort(key=lambda x: (x.language if x.language else ""))
            case "language", "desc":
                repos.sort(
                    key=lambda x: (x.language if x.language else ""), reverse=True
                )
            case "timestarred", "asc":
                repos.reverse()

    def sortReposInLists(starredLists, orderby, orderdirection):
        for list in starredLists:
            StarsExporter.sortRepos(list.repos, orderby, orderdirection)

    OTHERS_GROUP_NAME = "Others"

    def groupRepos(repos, args, groupby):
        groups = {}
        for repo in repos:
            if groupby == "language":
                key = repo.language or StarsExporter.OTHERS_GROUP_NAME
                if key not in groups:
                    groups[key] = []
                groups[key].append(repo)
            elif groupby == "topic":
                repoGrouped = False
                for key in repo.topics:
                    if key in TopicsInfo.hotTopicsSet:
                        key = TopicsInfo.topicToLanMap.get(key, None) or key
                        if key not in groups:
                            groups[key] = []
                        groups[key].append(repo)
                        repoGrouped = True
                if repo.language:
                    languageLower = repo.language.lower()
                    lanTopic = (
                        TopicsInfo.lanToTopicMap.get(languageLower, None)
                        or languageLower
                    )
                    if (
                        lanTopic not in repo.topics
                        and lanTopic in TopicsInfo.hotTopicsSet
                    ):
                        if languageLower not in groups:
                            groups[languageLower] = []
                        groups[languageLower].append(repo)
                        repoGrouped = True
                if not repoGrouped:
                    if StarsExporter.OTHERS_GROUP_NAME not in groups:
                        groups[StarsExporter.OTHERS_GROUP_NAME] = []
                    groups[StarsExporter.OTHERS_GROUP_NAME].append(repo)
        groups = OrderedDict(sorted(groups.items(), key=lambda d: d[0]))
        if StarsExporter.OTHERS_GROUP_NAME in groups:
            groups.move_to_end(StarsExporter.OTHERS_GROUP_NAME)
        for _, repos in groups.items():
            StarsExporter.sortRepos(repos, args.orderby, args.orderdirection)
        return groups

    def getGroupByText(groupby):
        if groupby == "language":
            return "languages"
        elif groupby == "topic":
            return "topics"
        else:
            return "Index"

    def exportToFile(
        args, repos, starredTopics, starredLists, filePathName, showOrderNum
    ):
        StarsExporter.sortReposInLists(starredLists, args.orderby, args.orderdirection)
        if args.groupby in ["language", "topic"]:
            groupByText = StarsExporter.getGroupByText(args.groupby)
            groups = StarsExporter.groupRepos(repos, args, args.groupby)
            match args.format:
                case "bookmark":
                    StarsExporter.exportBookmarkGrouped(
                        args.username, filePathName, groups, starredTopics, starredLists
                    )
                case "md":
                    StarsExporter.exportMdGrouped(
                        args.username,
                        filePathName,
                        groups,
                        starredTopics,
                        starredLists,
                        showOrderNum,
                        groupByText,
                    )
                case "json":
                    StarsExporter.exportJsonGrouped(
                        filePathName, groups, starredTopics, starredLists
                    )
                case _:
                    StarsExporter.exportHTMLGrouped(
                        args.username,
                        filePathName,
                        groups,
                        starredTopics,
                        starredLists,
                        showOrderNum,
                        groupByText,
                    )
        else:
            StarsExporter.sortRepos(repos, args.orderby, args.orderdirection)
            match args.format:
                case "bookmark":
                    StarsExporter.exportBookmark(
                        args.username, filePathName, repos, starredTopics, starredLists
                    )
                case "md":
                    StarsExporter.exportMd(
                        args.username,
                        filePathName,
                        repos,
                        starredTopics,
                        starredLists,
                        showOrderNum,
                    )
                case "json":
                    StarsExporter.exportJson(
                        filePathName, repos, starredTopics, starredLists
                    )
                case _:
                    StarsExporter.exportHTML(
                        args.username,
                        filePathName,
                        repos,
                        starredTopics,
                        starredLists,
                        showOrderNum,
                    )

    DESC_LENGTH_LIMIT = 200

    star_img = """<svg aria-label="star" role="img" height="10" viewBox="0 0 16 16" version="1.1" width="10" data-view-component="true"
         class="octicon octicon-star">
            <path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 
            1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 
            0 0 1 8 .25Zm0 2.445L6.615 5.5a.75.75 0 0 1-.564.41l-3.097.45 2.24 2.184a.75.75 0 0 1 .216.664l-.528 3.084 2.769-1.456a.75.75 
            0 0 1 .698 0l2.77 1.456-.53-3.084a.75.75 0 0 1 .216-.664l2.24-2.183-3.096-.45a.75.75 0 0 1-.564-.41L8 2.694Z"></path>
        </svg>"""
    fork_img = """<svg aria-label="fork" role="img" height="10" viewBox="0 0 16 16" version="1.1" width="10" data-view-component="true" 
        class="octicon octicon-repo-forked">
            <path d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 
            2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 
            0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"></path>
        </svg>"""

    def exportHTMLTopics(f, starredTopics):
        if len(starredTopics) > 0:
            f.write("<H4>Starred topics</H4>\n")
            f.write("<ul>\n")
            for topicInfo in starredTopics:
                f.write(
                    "<li>"
                    + "<a href='"
                    + topicInfo.url
                    + "' target='blank'>"
                    + topicInfo.name
                    + "</a></li>\n"
                )
            f.write("</ul><br><hr>\n")

    def exportHTMLListsTitles(f, starredLists):
        if len(starredLists) > 0:
            f.write("<H4>Starred lists</H4>\n")
            f.write("<ul>\n")
            for listInfo in starredLists:
                f.write(
                    "<li>"
                    + "<a href='#starredList_"
                    + listInfo.name
                    + "'>"
                    + listInfo.name
                    + "("
                    + str(len(listInfo.repos))
                    + ")"
                    + "</a></li>\n"
                )
            f.write(
                "</ul><br><a href='#starred_repositories'>Jump to starred repositories</a><br><br><hr>\n"
            )

    def exportHTMLListsBodies(f, starredLists, showOrderNum):
        if len(starredLists) > 0:
            for listInfo in starredLists:
                if len(listInfo.repos) > 0:
                    f.write("<DL><p>\n")
                    f.write(
                        "<DT><a id='starredList_"
                        + listInfo.name
                        + "'></a>"
                        + listInfo.name
                        + "</DT>"
                    )
                    if len(listInfo.description) > 0:
                        f.write(
                            "<DT><font color='gray' size='2'>"
                            + listInfo.description
                            + "</font></DT>"
                        )
                    f.write("<DD>&nbsp;</DD>\n")
                    f.write(
                        "<font size='1'><a href='#page_content_index'>[🔝 back to top]</a></font><br><br>\n"
                    )
                    ordernum = 0
                    for repo in listInfo.repos:
                        ordernum += 1
                        StarsExporter.exportHtmlItem(f, repo, ordernum, showOrderNum)
                    f.write("</DL><hr><p>\n")

    def exportHTML(
        username, filename, repos, starredTopics, starredLists, showOrderNum
    ):
        with open(filename, "w+", encoding="utf-8") as f:
            f.write("<HTML>\n")
            f.write(
                '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n'
            )
            f.write("<Title>Imported From Github</Title>\n")
            f.write(
                """<style>
                a {text-decoration: none;}
                a:hover{text-decoration:underline;}
                ul {list-style-type:none;}
    	        ul li{display:inline-block;padding-right: 20px;}
            </style>\n"""
            )
            f.write("<a id='page_content_index'></a>\n")
            f.write("<H3 FOLDED>Github Stars by " + username + "</H3>\n")
            StarsExporter.exportHTMLTopics(f, starredTopics)
            StarsExporter.exportHTMLListsTitles(f, starredLists)
            StarsExporter.exportHTMLListsBodies(f, starredLists, showOrderNum)
            f.write("<a id='starred_repositories'></a>")
            f.write("<H4>Starred repositories</H4>\n")
            f.write("<DL><p>\n")
            ordernum = 0
            for repo in repos:
                ordernum += 1
                StarsExporter.exportHtmlItem(f, repo, ordernum, showOrderNum)
            f.write("</DL><p>\n")
            f.write("</HTML>")

    def exportHTMLGrouped(
        username,
        filename,
        groups,
        starredTopics,
        starredLists,
        showOrderNum,
        groupByText,
    ):
        with open(filename, "w+", encoding="utf-8") as f:
            f.write("<HTML>\n")
            f.write(
                '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n'
            )
            f.write("<Title>Imported From Github</Title>\n")
            f.write(
                """<style>
        a {text-decoration: none;}
        a:hover{text-decoration:underline;}
    	ul {list-style-type:none;}
    	ul li{display:inline-block;padding-right: 20px;}
    </style>\n"""
            )
            f.write("<a id='page_content_index'></a>\n")
            f.write("<H3 FOLDED>Github Stars by " + username + "</H3>\n")
            StarsExporter.exportHTMLTopics(f, starredTopics)
            StarsExporter.exportHTMLListsTitles(f, starredLists)
            StarsExporter.exportHTMLListsBodies(f, starredLists, showOrderNum)
            f.write("<a id='starred_repositories'></a>")
            f.write("<H4>Starred repositories grouped by " + groupByText + "</H4>\n")
            f.write("<ul>\n")
            for key in groups.keys():
                f.write("<li>" + "<a href='#" + key + "'>" + key.title() + "</li>\n")
            f.write("</ul>\n")
            for key, group in groups.items():
                f.write("<DL><p>\n")
                f.write(
                    "<DT><a id='"
                    + key
                    + "'></a>"
                    + key.title()
                    + "</DT><DD>&nbsp;</DD><font size='1'><a href='#page_content_index'>[🔝 back to top]</a></font><br><br>\n"
                )
                ordernum = 0
                for repo in group:
                    ordernum += 1
                    StarsExporter.exportHtmlItem(f, repo, ordernum, showOrderNum)
                f.write("</DL><hr><p>\n")
            f.write("</HTML>")

    def exportHtmlItem(f, repo, ordernum, showOrderNum):
        link = "<DT>" + ((str(ordernum) + ".&nbsp;") if showOrderNum else " ")
        link = (
            link
            + "<A target='blank' HREF=\""
            + repo.html_url
            + '">'
            + repo.full_name
            + "</A></DT>\n"
        )
        if repo.description:
            link += (
                "<DD>"
                + html.escape(repo.description[: StarsExporter.DESC_LENGTH_LIMIT])
                if repo.description
                else "&nbsp;" + "</DD>\n"
            )
        link += (
            "<DD><font color='gray' size='1'>"
            + (repo.language + "&nbsp;&nbsp;&nbsp;" if repo.language else "&nbsp;")
            + StarsExporter.star_img
            + str(repo.stargazers_count)
            + "&nbsp;&nbsp;"
            + StarsExporter.fork_img
            + str(repo.forks_count)
            + "&nbsp;&nbsp;Updated on "
            + repo.pushed_at.strftime("%Y-%m-%d")
            + "</font></DD>\n"
        )
        link += "<DD>&nbsp;</DD>\n"
        f.write(link)

    def exportBookmarkTopics(f, starredTopics):
        if len(starredTopics) > 0:
            f.write("<DT><H3 FOLDED>Starred Topics</H3>\n")
            f.write("<DL><p>\n")
            for topic in starredTopics:
                f.write(
                    "<DT>"
                    + "<A target='blank' HREF=\""
                    + topic.url
                    + '">'
                    + topic.name
                    + "</A></DT>\n"
                )
            f.write("</DL><p>\n")

    def exportBookmarkLists(f, starredLists):
        if len(starredLists) > 0:
            f.write("<DT><H3 FOLDED>Starred Lists</H3>\n")
            f.write("<DL><p>\n")
            for list in starredLists:
                f.write("   <DT><H3 FOLDED>" + list.name + "</H3>\n")
                f.write("   <DL><p>\n")
                for repo in list.repos:
                    f.write(
                        "       <DT>"
                        + "<A target='blank' HREF=\""
                        + repo.html_url
                        + '">'
                        + repo.full_name
                        + "</A></DT>\n"
                    )
                f.write("   </DL><p>\n")
            f.write("</DL><p>\n")

    def exportBookmark(username, filename, repos, starredTopics, starredLists):
        with open(filename, "w+", encoding="utf-8") as f:
            f.write("<HTML>\n")
            f.write(
                '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n'
            )
            f.write("<Title>Imported From Github</Title>\n")
            f.write(
                """<style>
                a {text-decoration: none;}
                a:hover{text-decoration:underline;}
            </style>\n"""
            )
            f.write(
                "<DL>\n<DT><H3 FOLDED>Github Stars by " + username + "</H3>\n<DL>\n"
            )
            StarsExporter.exportBookmarkTopics(f, starredTopics)
            StarsExporter.exportBookmarkLists(f, starredLists)
            f.write("<DT><H3 FOLDED>Starred Repos</H3>\n")
            f.write("<DL><p>\n")
            for repo in repos:
                f.write(
                    "<DT>"
                    + "<A target='blank' HREF=\""
                    + repo.html_url
                    + '">'
                    + repo.full_name
                    + "</A></DT>\n"
                )
            f.write("</DL><p>\n</DL>\n</DL>\n")
            f.write("</HTML>")

    def exportBookmarkGrouped(username, filename, groups, starredTopics, starredLists):
        with open(filename, "w+", encoding="utf-8") as f:
            f.write("<HTML>\n")
            f.write(
                '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n'
            )
            f.write("<Title>Imported From Github</Title>\n")
            f.write(
                """<style>
                a {text-decoration: none;}
                a:hover{text-decoration:underline;}
            </style>\n"""
            )
            f.write(
                "<DL>\n<DT><H3 FOLDED>Github Stars by " + username + "</H3>\n<DL>\n"
            )
            StarsExporter.exportBookmarkTopics(f, starredTopics)
            StarsExporter.exportBookmarkLists(f, starredLists)
            f.write("<DT><H3 FOLDED>Starred Repos</H3>\n")
            f.write("<DL><p>\n")
            for key, repos in groups.items():
                f.write("   <DT><H3 FOLDED>" + key.title() + "</H3>\n")
                f.write("   <DL><p>\n")
                for repo in repos:
                    f.write(
                        "       <DT>"
                        + "<A target='blank' HREF=\""
                        + repo.html_url
                        + '">'
                        + repo.full_name
                        + "</A></DT>\n"
                    )
                f.write("   </DL><p>\n")
            f.write("</DL><p>\n</DL>\n</DL>\n")
            f.write("</HTML>")

    def exportMdTopics(f, starredTopics):
        if len(starredTopics) > 0:
            f.write("\n## Starred topics\n")
            for topicInfo in starredTopics:
                f.write("  - [" + topicInfo.name + "](" + topicInfo.url + ")\n")

    def exportMdListsTitles(f, starredLists):
        if len(starredLists) > 0:
            f.write("\n## Starred lists\n")
            for listInfo in starredLists:
                f.write(
                    "  - ["
                    + listInfo.name
                    + "("
                    + str(len(listInfo.repos))
                    + ")](#starredList_"
                    + listInfo.name.replace(" ", "-")
                    + ")\n"
                )
            f.write("\n ## [Jump to starred repositories](#starred_repositories)\n\n")

    def exportMdListsBodies(f, starredLists, showOrderNum):
        if len(starredLists) > 0:
            for listInfo in starredLists:
                if len(listInfo.repos) > 0:
                    f.write(
                        "\n## "
                        + listInfo.name
                        + "\n<a id='starredList_"
                        + listInfo.name.replace(" ", "-")
                        + "'></a>\n[🔝 back to top](#page_content_index)\n"
                    )
                    StarsExporter.exportMdItem(f, listInfo.repos, showOrderNum)

    def exportMd(username, filename, repos, starredTopics, starredLists, showOrderNum):
        with open(filename, "w+", encoding="utf-8") as f:
            f.write(
                "# GitHub Stars by " + username + "<a id='page_content_index'></a>\n"
            )
            f.write(
                """<style>
            	ul {list-style-type:none;}
            	ul li{display:inline-block;padding-right: 20px;}
            </style>\n\n"""
            )
            StarsExporter.exportMdTopics(f, starredTopics)
            StarsExporter.exportMdListsTitles(f, starredLists)
            StarsExporter.exportMdListsBodies(f, starredLists, showOrderNum)
            f.write("\n## Starred repositories<a id='starred_repositories'></a>\n")
            StarsExporter.exportMdItem(f, repos, showOrderNum)

    def exportMdGrouped(
        username,
        filename,
        groups,
        starredTopics,
        starredLists,
        showOrderNum,
        groupByText,
    ):
        with open(filename, "w+", encoding="utf-8") as f:
            f.write(
                "# GitHub Stars by " + username + "<a id='page_content_index'></a>\n"
            )
            f.write(
                """<style>
            	ul {list-style-type:none;}
            	ul li{display:inline-block;padding-right: 20px;}
            </style>\n\n"""
            )
            StarsExporter.exportMdTopics(f, starredTopics)
            StarsExporter.exportMdListsTitles(f, starredLists)
            StarsExporter.exportMdListsBodies(f, starredLists, showOrderNum)
            f.write(
                "\n## Starred repositories grouped by "
                + groupByText
                + "<a id='starred_repositories'></a>\n"
            )
            for key in groups.keys():
                f.write("  - [" + key.title() + "](#" + key.replace(" ", "-") + ")\n")
            for key, repos in groups.items():
                f.write(
                    "\n## "
                    + key.title()
                    + "<a id='"
                    + key.replace(" ", "-")
                    + "'></a>\n[🔝 back to top](#page_content_index)\n"
                )
                StarsExporter.exportMdItem(f, repos, showOrderNum)

    def exportMdItem(f, repos, showOrderNum):
        star_img = "⭐"
        fork_img = "🔌"
        ordernum = 0
        for repo in repos:
            ordernum += 1
            link = (
                "### "
                + ((str(ordernum) + ". ") if showOrderNum else " ")
                + "["
                + repo.full_name
                + "]("
                + repo.html_url
                + ")"
                + "\n\n"
            )
            link += (
                html.escape(repo.description[: StarsExporter.DESC_LENGTH_LIMIT])
                if repo.description
                else ""
            ) + "  \n"
            link += (
                "<font color='gray'>"
                + (repo.language + "&nbsp;&nbsp;&nbsp;" if repo.language else "&nbsp;")
                + star_img
                + str(repo.stargazers_count)
                + "&nbsp;&nbsp;"
                + fork_img
                + str(repo.forks_count)
                + "&nbsp;&nbsp;Updated on "
                + repo.pushed_at.strftime("%Y-%m-%d")
                + "</font>\n\n"
            )
            f.write(link)

    def exportJsonStarredTopics(f, starredTopics):
        f.write('"starred_topics": [\n')
        count = 0
        for topic in starredTopics:
            jsonString = f"""        {{
            "name": "{topic.name}",
            "html_url": "{topic.url}"
        }}"""
            count += 1
            if count < len(starredTopics):
                jsonString += ",\n"
            f.write(jsonString)
        f.write("\n],\n")

    def repoInLists2jsonstring(repo):
        description = json.dumps(repo.description or "", ensure_ascii=False)
        return f"""        {{
            "name": "{repo.name}",
            "full_name": "{repo.full_name}",
            "description": {description},
            "language": "{repo.language}",
            "html_url": "{repo.html_url}",
            "forks_count": {repo.forks_count},
            "stargazers_count": {repo.stargazers_count},
            "pushed_at": "{repo.pushed_at}"
        }}"""

    def exportJsonStarredLists(f, starredLists):
        f.write('"starred_lists": [\n')
        groupsPos = 0
        for list in starredLists:
            f.write('{\n    "name":"' + list.name + '",')
            f.write('\n    "description":"' + list.description + '",')
            f.write('\n    "html_url":"' + list.url + '",')
            f.write('\n    "repositories": [\n')
            reposPos = 0
            for repo in list.repos:
                jsonString = StarsExporter.repoInLists2jsonstring(repo)
                reposPos += 1
                if reposPos < len(list.repos):
                    jsonString += ",\n"
                f.write(jsonString)
            f.write("\n    ]\n}")
            groupsPos += 1
            if groupsPos < len(starredLists):
                f.write(",")
        f.write("\n],")

    def repo2jsonstring(repo):
        description = json.dumps(repo.description or "", ensure_ascii=False)
        private = "true" if repo.private else "false"
        topics = json.dumps(repo.topics, ensure_ascii=False)
        # no include repo.subscribers_count because will slow down the convert
        return f"""  {{
            "id": {repo.id},
            "name": "{repo.name}",
            "full_name": "{repo.full_name}",
            "private":  {private},
            "description": {description},
            "language": "{repo.language}",
            "html_url": "{repo.html_url}",
            "size": {repo.size},
            "topics": {topics},
            "forks_count": {repo.forks_count},
            "stargazers_count": {repo.stargazers_count},
            "watchers_count": {repo.watchers_count},
            "created_at": "{repo.created_at}",
            "pushed_at": "{repo.pushed_at}"
        }}"""

    def exportJsonGrouped(filename, groups, starredTopics, starredLists):
        with open(filename, "w+", encoding="utf-8") as f:
            f.write("{\n")
            StarsExporter.exportJsonStarredTopics(f, starredTopics)
            StarsExporter.exportJsonStarredLists(f, starredLists)
            f.write('"starred_repositories": [\n')
            groupsPos = 0
            for key, repos in groups.items():
                f.write('{\n"groupname":"' + key.title() + '",')
                f.write('\n"repositories": [\n')
                reposPos = 0
                for repo in repos:
                    jsonString = StarsExporter.repo2jsonstring(repo)
                    reposPos += 1
                    if reposPos < len(repos):
                        jsonString += ",\n"
                    f.write(jsonString)
                f.write("\n]\n}")
                groupsPos += 1
                if groupsPos < len(groups):
                    f.write(",")
            f.write("\n]\n}")

    def exportJson(filename, repos, starredTopics, starredLists):
        with open(filename, "w+", encoding="utf-8") as f:
            f.write("{\n")
            StarsExporter.exportJsonStarredTopics(f, starredTopics)
            StarsExporter.exportJsonStarredLists(f, starredLists)
            f.write('"starred_repositories": [\n')
            count = 0
            for repo in repos:
                jsonString = StarsExporter.repo2jsonstring(repo)
                count += 1
                if count < len(repos):
                    jsonString += ",\n"
                f.write(jsonString)
            f.write("\n]\n}")
