# Use API
# List with fzf
# Show CI status
# Merge on select

# >>> pulls = repo.get_pulls(state='open', sort='created', base='master')
# >>> for pr in pulls:
# ...    print(pr.number)


    # def merge(
    #     self,
    #     commit_message=github.GithubObject.NotSet,
    #     commit_title=github.GithubObject.NotSet,
    #     merge_method=github.GithubObject.NotSet,
    #     sha=github.GithubObject.NotSet,
    # ):




    # def is_merged(self):
    #     """
    #     :calls: `GET /repos/:owner/:repo/pulls/:number/merge <http://developer.github.com/v3/pulls>`_
    #     :rtype: bool
    #     """
    #     status, headers, data = self._requester.requestJson("GET", self.url + "/merge")
    #     return status == 204


    # def get_statuses(self):
    #     """
    #     :calls: `GET /repos/:owner/:repo/statuses/:ref <http://developer.github.com/v3/repos/statuses>`_
    #     :rtype: :class:`github.PaginatedList.PaginatedList` of :class:`github.CommitStatus.CommitStatus`
    #     """
    #     return github.PaginatedList.PaginatedList(
    #         github.CommitStatus.CommitStatus,
    #         self._requester,
    #         self._parentUrl(self._parentUrl(self.url)) + "/statuses/" + self.sha,
    #         None,
    #     )
    #
    # def get_combined_status(self):
    #     """
    #     :calls: `GET /repos/:owner/:repo/commits/:ref/status/ <http://developer.github.com/v3/repos/statuses>`_
    #     :rtype: :class:`github.CommitCombinedStatus.CommitCombinedStatus`
    #     """
    #     headers, data = self._requester.requestJsonAndCheck("GET", self.url + "/status")
    #     return github.CommitCombinedStatus.CommitCombinedStatus(
    #         self._requester, headers, data, completed=True
    #     )
