"""
Contains a class representing the GitLab merge request.

Unlike GitHub, GitLab maintains a seperate API for merge requests and issues.
So, each method behaves through the inherent data shared through self._data and
self._url, like a mixin.

All the methods from GitLabIssue are used inherently but with the _url and
_data properties of GitLabMergeRequest object.
"""
import re

from datetime import datetime
from functools import lru_cache
from urllib.parse import quote_plus

from IGitt.GitLab import get
from IGitt.GitLab import put
from IGitt.GitLab.GitLabCommit import GitLabCommit
from IGitt.GitLab.GitLabIssue import GitLabIssue
from IGitt.Interfaces.MergeRequest import MergeRequest


class GitLabMergeRequest(MergeRequest, GitLabIssue):
    """
    A Merge Request on GitLab.
    """

    def __init__(self, oauth_token: str, repository: str, mr_iid: int):
        """
        Creates a new GitLabMergeRequest object.

        :param oauth_token: The OAuth token to authenticate with.
        :param repository: The repository containing the MR.
        :param mr_iid: The unique identifier for GitLab MRs.
        """
        self._token = oauth_token
        self._repository = repository
        self._iid = mr_iid
        self._url = '/projects/{repo}/merge_requests/{iid}'.format(
            repo=quote_plus(repository), iid=self._iid)
        self._data = get(self._token, self._url)

    @property
    def number(self) -> int:
        """
        Returns the MR "number" or id.

        >>> from os import environ
        >>> mr = GitLabMergeRequest(environ['GITLAB_TEST_TOKEN'],
        ...                         'gitmate-test-user/test', 2)
        >>> mr.number
        2

        :return: The number of the issue.
        """
        return self._iid

    @property
    def base_branch_name(self) -> str:
        """
        Retrieves the base branch name of the merge request, i.e. the one it
        should be merged into.

        :return: A string.
        """
        return self._data['target_branch']

    @property
    def base(self) -> GitLabCommit:
        """
        Retrieves the base commit as a GitLabCommit object.

        >>> from os import environ
        >>> pr = GitLabMergeRequest(environ['GITLAB_TEST_TOKEN'],
        ...                         'gitmate-test-user/test', 2)
        >>> pr.base.sha
        '198dd16f8249ea98ed41876efe27d068b69fa215'

        :return: A GitLabCommit object.
        """
        return GitLabCommit(self._token, self._repository,
                            quote_plus(self.base_branch_name))

    @property
    def head_branch_name(self) -> str:
        """
        Retrieves the head branch name of the merge request, i.e. the one which
        should be merged.

        :return: A string.
        """
        return self._data['source_branch']

    @property
    def head(self) -> GitLabCommit:
        """
        Retrieves the head commit as a GitLabCommit object.

         >>> from os import environ
        >>> pr = GitLabMergeRequest(environ['GITLAB_TEST_TOKEN'],
        ...                         'gitmate-test-user/test', 2)
        >>> pr.head.sha
        '99f484ae167dcfcc35008ba3b5b564443d425ee0'

        :return: A GitLabCommit object.
        """
        return GitLabCommit(self._token, self._repository,
                            quote_plus(self.head_branch_name))

    @property
    @lru_cache(None)
    def commits(self):
        """
        Retrieves a tuple of commit objects that are included in the PR.

        >>> from os import environ
        >>> pr = GitLabMergeRequest(environ['GITLAB_TEST_TOKEN'],
        ...                         'gitmate-test-user/test', 2)
        >>> assert ([commit.sha for commit in pr.commits] == [
        ...     '99f484ae167dcfcc35008ba3b5b564443d425ee0',
        ...     'bbd11b50412d34072f1889e4cea04a32de183605'])

        :return: A tuple of commit objects.
        """
        commits = get(self._token, self._url + '/commits')
        return tuple(GitLabCommit(self._token, self._repository, commit['id'])
                     for commit in commits)

    @property
    def repository(self):
        """
        Retrieves the repository where this comes from.

        >>> from os import environ
        >>> pr = GitLabMergeRequest(environ['GITLAB_TEST_TOKEN'],
        ...                         'gitmate-test-user/test', 2)
        >>> pr.repository.full_name
        'gitmate-test-user/test'

        :return: The repository object.
        """
        from .GitLabRepository import GitLabRepository
        return GitLabRepository(self._token, self._repository)

    @property
    def affected_files(self):
        """
        Retrieves affected files from a GitLab merge request.

        >>> from os import environ
        >>> pr = GitLabMergeRequest(environ['GITLAB_TEST_TOKEN'],
        ...                         'gitmate-test-user/test', 7)
        >>> pr.affected_files
        {'README.md'}

        :return: A set of filenames.
        """
        changes = get(self._token, self._url + '/changes')['changes']
        return {change['old_path'] for change in changes}

    @property
    def diffstat(self):
        """
        Gets additions and deletions of a merge request.

        >>> from os import environ
        >>> pr = GitLabMergeRequest(environ['GITLAB_TEST_TOKEN'],
        ...                         'gitmate-test-user/test', 7)
        >>> pr.diffstat
        (2, 0)

        :return: An (additions, deletions) tuple.
        """
        changes = get(self._token, self._url + '/changes')['changes']
        results = []
        expr = re.compile(r'@@ [0-9+,-]+ [0-9+,-]+ @@')
        for change in changes:
            diff = change['diff']
            start_index = expr.search(diff).end()
            results += diff[start_index:].split('\n')

        additions = len([line for line in results if line.startswith('+')])
        deletions = len([line for line in results if line.startswith('-')])

        return additions, deletions

    @property
    def created(self) -> datetime:
        """
        Retrieves a timestamp on when the merge request was created.

        >>> from os import environ
        >>> pr = GitLabMergeRequest(environ['GITLAB_TEST_TOKEN'],
        ...                         'gitmate-test-user/test', 2)
        >>> pr.created
        datetime.datetime(2017, 6, 7, 3, 51, 41, 112000)
        """
        return datetime.strptime(self._data['created_at'],
                                 '%Y-%m-%dT%H:%M:%S.%fZ')

    @property
    def updated(self) -> datetime:
        """
        Retrieves a timestamp on when the merge request was updated the last
        time.

        >>> from os import environ
        >>> pr = GitLabMergeRequest(environ['GITLAB_TEST_TOKEN'],
        ...                         'gitmate-test-user/test', 2)
        >>> pr.updated
        datetime.datetime(2017, 6, 7, 3, 51, 41, 112000)
        """
        return datetime.strptime(self._data['updated_at'],
                                 '%Y-%m-%dT%H:%M:%S.%fZ')

    def close(self):
        """
        Closes the merge request.

        :raises RuntimeError: If something goes wrong (network, auth...).
        """
        self._data = put(self._token, self._url, {'state_event': 'close'})

    def reopen(self):
        """
        Reopens the merge request.

        :raises RuntimeError: If something goes wrong (network, auth...).
        """
        self._data = put(self._token, self._url, {'state_event': 'reopen'})

    @property
    def state(self) -> str:
        """
        Get's the state of the merge request.

        >>> from os import environ
        >>> mr = GitLabMergeRequest(environ['GITLAB_TEST_TOKEN'],
        ...                         'gitmate-test-user/test', 7)
        >>> mr.state
        'reopened'

        So if we close it:

        >>> mr.close()
        >>> mr.state
        'closed'

        And reopen it:

        >>> mr.reopen()
        >>> mr.state
        'reopened'

        :return: Either 'opened', 'merged' or 'reopened'.
        """
        return self._data['state']
