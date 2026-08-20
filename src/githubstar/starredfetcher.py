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

import concurrent.futures
import logging
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .utils import Utils


def exceptionLineNo(exception):
    """Return the line number where an exception occurred, 0 if unavailable."""
    tb = exception.__traceback__
    return tb.tb_lineno if tb else 0


class TopicInfo:
    name = ""
    url = ""


class RepoInfo:
    full_name = ""
    name = ""
    html_url = ""
    description = ""
    language = ""
    stargazers_count = 0
    forks_count = 0
    pushed_at = datetime.fromisoformat("1970-01-01T11:11:11")


class ListInfo:
    name = ""
    url = ""
    description = ""
    count = 0
    repos = []


class StarredFetcher(object):
    def __init__(self, username):
        self.username = username
        self.starredTopics = []
        self.starredLists = []
        self.fetchListReposTaskDatas = []

    def fetchTopics(self):
        url = ""
        try:
            url = "https://github.com/stars/{username}/topics?direction=desc&page={page}&sort=created"
            page = 1
            itemsPerPage = 0
            while True:
                response = requests.get(url.format(username=self.username, page=page))
                response.raise_for_status()
                soup = BeautifulSoup(
                    response.text, "html.parser", multi_valued_attributes=None
                )
                listsContainer = soup.find(
                    "ul",
                    class_="repo-list list-style-none js-navigation-container js-active-navigation-container",
                )
                if listsContainer:
                    curItemsPerPage = 0
                    for li in listsContainer.find_all("li"):
                        topicInfo = TopicInfo()
                        topicLink = li.find(
                            "a",
                            class_="d-flex flex-md-items-center flex-auto no-underline",
                        )
                        if topicLink:
                            href = topicLink.get("href")
                            if href is not None:
                                topicInfo.url = "https://github.com" + str(href)
                        topicNameTag = li.find(
                            "p", class_="f3 lh-condensed mt-1 mt-md-0 mb-0"
                        )
                        if topicNameTag:
                            topicInfo.name = topicNameTag.text
                        self.starredTopics.append(topicInfo)
                        curItemsPerPage += 1
                    if itemsPerPage <= 0:
                        itemsPerPage = curItemsPerPage
                    elif curItemsPerPage < itemsPerPage:
                        break
                else:
                    break
                page += 1
        except Exception as exception:
            logging.error(
                f"{__class__} line {exceptionLineNo(exception)} : {url} generated an exception: {exception}"
            )

    def fetch(self):
        url = ""
        try:
            url = f"https://github.com/{self.username}?tab=stars"
            response = requests.get(url)
            response.raise_for_status()
            Utils.printProgress(3)
            soup = BeautifulSoup(
                response.text, "html.parser", multi_valued_attributes=None
            )
            if soup.find("div", class_="col-lg-3 mt-6 mt-lg-0"):
                self.fetchTopics()
            elif soup.find("div", class_="col-lg-3 tmp-mt-6 tmp-mt-lg-0"):
                self.fetchTopics()
            Utils.printProgress(5)
            listsContainer = soup.find(id="profile-lists-container")
            if listsContainer:
                for link in listsContainer.find_all("a"):
                    listInfo = ListInfo()
                    name = link.find(class_="f4 text-bold tmp-mr-3")
                    if name:
                        listInfo.name = name.text.strip()
                    href = link.get("href")
                    if href is not None:
                        listInfo.url = "https://github.com" + str(href)
                    description = link.find(
                        class_="color-fg-muted tmp-mr-3 wb-break-word"
                    )
                    if description:
                        listInfo.description = description.text.strip()
                    count = link.find(class_="color-fg-muted text-small no-wrap")
                    if count:
                        matchObj = re.match(r"(\d+)[\s+]repositor[y|ies]", count.text)
                        if matchObj:
                            listInfo.count = int(matchObj.group(1))
                            listInfo.repos = [RepoInfo()] * listInfo.count
                    self.starredLists.append(listInfo)
                self.getReposPerPage()
                Utils.printProgress(8)
                self.buildFetchListReposTaskDatas()
                self.fetchListRepos()
        except Exception as exception:
            logging.error(
                f"{__class__} line {exceptionLineNo(exception)} : {url} generated an exception: {exception}"
            )

    __REPOS_PER_PAGE = 30

    def getReposPerPage(self):
        try:
            reposPerPage = 0
            maxCount = 0
            maxCountIndex = 0
            curIndex = 0
            for listInfo in self.starredLists:
                if listInfo.count > 0 and listInfo.count > maxCount:
                    maxCount = listInfo.count
                    maxCountIndex = curIndex
                curIndex += 1
            response = requests.get(self.starredLists[maxCountIndex].url + "?page=1")
            response.raise_for_status()
            soup = BeautifulSoup(
                response.text, "html.parser", multi_valued_attributes=None
            )
            reposContainer = soup.find(id="user-list-repositories")
            if reposContainer:
                reposPerPage = len(
                    reposContainer.find_all(
                        "div",
                        class_="col-12 d-block width-full tmp-py-4 border-bottom color-border-muted",
                    )
                )
            if reposPerPage > 0:
                __REPOS_PER_PAGE = reposPerPage
        except Exception as exception:
            logging.error(
                f"{__class__} line {exceptionLineNo(exception)} : {exception}"
            )

    class FetchListReposTaskData:
        def __init__(self, listInfo, page_url, page_first_repo_index):
            self.listInfo = listInfo
            self.page_url = page_url
            self.page_first_repo_index = page_first_repo_index

    def buildFetchListReposTaskDatas(self):
        for listInfo in self.starredLists:
            if listInfo.count > 0:
                totalPage = (
                    listInfo.count + self.__REPOS_PER_PAGE - 1
                ) // self.__REPOS_PER_PAGE
                url = listInfo.url + "?page={page}"
                page = 1
                while page <= totalPage:
                    page_url = url.format(page=page)
                    page_first_repo_index = (page - 1) * self.__REPOS_PER_PAGE
                    self.fetchListReposTaskDatas.append(
                        StarredFetcher.FetchListReposTaskData(
                            listInfo, page_url, page_first_repo_index
                        )
                    )
                    page += 1

    def fetchListRepos(self):
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(32, (os.process_cpu_count() or 1) * 2)
        ) as executor:
            future_to_task = {
                executor.submit(self.fetchListReposTask, data): data
                for data in self.fetchListReposTaskDatas
            }
            for future in concurrent.futures.as_completed(future_to_task):
                data = future_to_task[future]
                result = future.result()

    __fetchListReposTask_lastExceptionLineNo = 0
    __fetchListReposTask_lastExceptionType = None

    def fetchListReposTask(self, data):
        try:
            response = requests.get(data.page_url)
            response.raise_for_status()
            soup = BeautifulSoup(
                response.text, "html.parser", multi_valued_attributes=None
            )
            reposContainer = soup.find(id="user-list-repositories")
            if reposContainer:
                repoIndex = 0
                for repo in reposContainer.find_all(
                    "div",
                    class_="col-12 d-block width-full tmp-py-4 border-bottom color-border-muted",
                ):
                    if repoIndex >= self.__REPOS_PER_PAGE:
                        logging.error(
                            f"{{__class__}}: {data.page_url} repos count exceed {self.__REPOS_PER_PAGE}"
                        )
                        break
                    repoInfo = RepoInfo()
                    nameBlock = repo.find("div", class_="d-inline-block mb-1")
                    if nameBlock:
                        link = nameBlock.find("a")
                        if link:
                            href = link.get("href")
                            if href is not None:
                                href = str(href)
                                repoInfo.html_url = "https://github.com" + href
                                repoInfo.full_name = href[1:]
                                repoInfo.name = repoInfo.full_name.split("/", 1)[1]
                    descBlock = repo.find(
                        "p", class_="d-inline-block col-9 color-fg-muted tmp-pr-4"
                    )
                    if descBlock:
                        repoInfo.description = descBlock.text
                        if repoInfo.description:
                            repoInfo.description = repoInfo.description.strip()
                    infoBlock = repo.find("div", class_="f6 color-fg-muted mt-2")
                    if infoBlock:
                        lanBlock = infoBlock.find(itemprop="programmingLanguage")
                        if lanBlock:
                            repoInfo.language = lanBlock.text
                        for linkBlock in infoBlock.find_all("a"):
                            href = linkBlock.get("href")
                            if href is not None and str(href).endswith("stargazers"):
                                repoInfo.stargazers_count = int(
                                    linkBlock.text.strip().replace(",", "")
                                )
                            elif href is not None and str(href).endswith("forks"):
                                repoInfo.forks_count = int(
                                    linkBlock.text.strip().replace(",", "")
                                )
                        updateTimeBlock = infoBlock.find("relative-time")
                        if updateTimeBlock:
                            updateTimeStr = str(updateTimeBlock["datetime"])
                            if updateTimeStr.endswith("Z"):
                                updateTimeStr = updateTimeStr[:-1]
                            repoInfo.pushed_at = datetime.fromisoformat(updateTimeStr)
                    data.listInfo.repos[data.page_first_repo_index + repoIndex] = (
                        repoInfo
                    )
                    repoIndex += 1
                return True
        except Exception as exception:
            if self.__fetchListReposTask_lastExceptionLineNo != exceptionLineNo(
                exception
            ) or self.__fetchListReposTask_lastExceptionType != type(exception):
                self.__fetchListReposTask_lastExceptionLineNo = exceptionLineNo(
                    exception
                )
                self.__fetchListReposTask_lastExceptionType = type(exception)
                logging.error(
                    f"{__class__} line {exceptionLineNo(exception)} : {data.page_url} generated an exception: {exception}"
                )
        return False
