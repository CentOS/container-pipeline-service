#!/usr/bin/env python

"""
This module contains a class aimed for inspecting given docker
registry using its REST APIs.
It can
 - list all images in registry
 - filter images and list provided a namespace
 - find tags of the repository
"""

import json
import logging

import requests

# catalog API
CATALOG = "{}/v2/_catalog"


class InspectRegistry(object):
    """
    Class for aggregating operations needed to inspect registry
    """

    def __init__(self, registry, secure, logger=None):
        # configure logger
        self.logger = logger or logging.getLogger('console')
        # we need registry name for docker pull operations
        self.registry = registry
        # we need this for REST API calls
        self.reg_url = self.registry_url(secure)

    def registry_url(self, secure):
        """
        if secure registry return https://registry else
        http://registry
        """
        if secure:
            return "https://{}".format(self.registry)
        return "http://{}".format(self.registry)

    def get_call(self, url, params=None):
        """
        Performs GET call on given URL

        returns json loaded reposnse and headers
        """
        try:
            r = requests.get(url, params)
        except requests.exceptions.RequestException as e:
            self.logger.critical(
                "Failed to process URL: {} with params: {}".format(
                    url, params))
            self.logger.critical(str(e))
            return None, None
        else:
            try:
                content = json.loads(r.text)
            except ValueError as e:
                self.logger.critical(
                    "Failed to load json from {}".format(r.text))
                return None, None
            else:
                return content, r.headers

    def find_repos(self, page=30):
        """
        Find repositories in configured registry

        Returns: list of all images with tags available in registry
                 None if REST calls failed
        """
        # the repositories in registry could grow large in number
        # using pagination for same
        # lets hit registry catalog to get first len(page) repos
        params = {"n": page}

        # using https:// based registry URL for REST calls
        url = CATALOG.format(self.reg_url)

        # call catalog call with parameters for pagination
        resp, headers = self.get_call(url, params)

        # if failed to get repos, return None
        if not resp:
            self.logger.fatal(
                "Failed to retrieve repositories from registry catalog.")
            return None

        # sample response = {"repositories":["repo1", "repo2"]}
        # retrieve repositories from response
        repositories = resp.get("repositories", None)

        # if no repositories are present, return None
        if not repositories:
            self.logger.info(
                "No repositories available in configured registry.")
            return None
        # else, repositories now have a list of <= 30 repos

        # now lets do pagination
        while True:
            next_page = headers.get("Link", None)
            if not next_page:
                break

            # form next page required parameters, need last element last page
            params = {"n": page, "last": repositories[-1]}

            # call next page
            resp, headers = self.get_call(url, params)
            # check if we received repositories
            if not resp:
                self.logger.critical(
                    "Failed to paginate while retrieving repos from registry."
                    "URL: {}, Params: {}".format(url, params))
                self.logger.critical(
                    "Continuing with already retrieved repositories.")
            # if we received next page, add to retrieved repositories
            repositories.extend(resp.get("repositories", []))

        self.logger.info(
            "Total {} repos available in registry.".format(len(repositories)))

        # now return the available repositories
        return repositories

    def subset_repos_on_namespace(self, repos, namespaces=[]):
        """
        Return only matching configured namespaced repositories
        """
        # no filtering, return all repos
        if not namespaces:
            return repos

        srepos = [repo for repo in repos if repo.startswith(tuple(namespaces))]

        # remove duplicates if any
        return list(set(srepos))

    def find_repo_tags(self, repo, api="{}/v2/{}/tags/list"):
        """
        Given a repository name, find the available tags for it
        Returns a list of tags available for given repository
        """
        url = api.format(self.reg_url, repo)
        tags, _ = self.get_call(url)
        if not tags:
            self.logger.critical(
                "Failed to retrieve tags for {}.".format(repo))
            return None
        # reponse has {"name": <image_of_repo>, "tags": ["tag1", "tag2"]}
        return tags["tags"]

    def images_of_repo(self, repo):
        """
        Given a repo name, finds all the tags for repo and form
        URL for images in given repository

        Returns a list of REGISTRY/REPO:TAG available for given repo
        """
        # first find available tags for given repository
        tags = self.find_repo_tags(repo)
        if not tags:
            # return None, if failed to retrieve tags
            return None
        # now form the image registry URL
        # we are using registry URL without https:// for docker pull ops
        url = self.registry + "/" + repo + ":{}"
        images = [url.format(tag) for tag in tags]
        return images

    def list_all_images(self, namespaces=[]):
        """
        Lists all images in given registry with registry URL which is
        compatible with docker pull command (no https://) and puts each
        image for scanning
        """
        repositories = self.find_repos()
        if not repositories:
            return []

        repositories = self.subset_repos_on_namespace(
            repositories, namespaces)

        if not repositories:
            return []

        all_images = []
        for repo in repositories:
            images = self.images_of_repo(repo)
            if not images:
                continue
            all_images.extend(images)
        return all_images


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print "Please provide registry-name and True for secure-registry",
        print "OR False for insecure-registry."
        sys.exit(1)
    registry = sys.argv[1].strip()
    secure = sys.argv[2].strip()
    if secure in ["True", "true"]:
        secure = True
    else:
        secure = False

    inspect_reg = InspectRegistry(registry, secure)
    print "Finding containers in registry.."
    images = inspect_reg.list_all_images()
    for image in images:
        print image
