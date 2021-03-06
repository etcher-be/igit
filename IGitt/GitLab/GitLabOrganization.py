"""
This module contains the Issue abstraction class which provides properties and
actions related to issues and bug reports.
"""
import re
from functools import lru_cache
from typing import Set
from typing import Optional
from typing import Union
from urllib.parse import quote_plus

from IGitt.GitLab import GitLabPrivateToken
from IGitt.GitLab import GitLabOAuthToken
from IGitt.GitLab import GL_INSTANCE_URL
from IGitt.GitLab import GitLabMixin
from IGitt.GitLab.GitLabUser import GitLabUser
from IGitt.GitLab.GitLabIssue import GitLabIssue
from IGitt.Interfaces import get
from IGitt.Interfaces import post
from IGitt.Interfaces import AccessLevel
from IGitt.Interfaces.Organization import Organization
from IGitt.Interfaces.Repository import Repository


class GitLabOrganization(GitLabMixin, Organization):
    """
    Represents an organization on GitLab.
    """
    @property
    def web_url(self):
        return '{}/{}'.format(GL_INSTANCE_URL, self.name)

    def __init__(self, token, name):
        """
        :param name: Name of the org.
        """
        self._token = token
        self._name = name
        self._url = '/groups/{name}'.format(name=quote_plus(name))
        self._is_user = None

    @property
    def identifier(self) -> int:
        """
        Returns the identifier of the organization.
        """
        return self.data['id']

    @property
    def description(self) -> str:
        """
        Returns the description of this organization.
        """
        return self.data['description']

    @lru_cache()
    def raw_members(self) -> list:
        """
        Gets all members including the ones of groups around subgroups as a
        list of dicts from the JSON responses.
        """
        members = list(get(self._token, self.url + '/members'))
        if '/' in self.name:
            members.extend(GitLabOrganization(
                self._token,
                self.name.rsplit('/', maxsplit=1)[0]).raw_members())

        return members

    @property
    def billable_users(self) -> int:
        """
        Number of paying/registered users on the organization.
        """
        try:
            # If the org is a user, this'll throw RuntimeError
            users = {user['username'] for user in get(self._token,
                                                      self.url + '/members')}

            for group in get(self._token, self.absolute_url('/groups')):
                gname = group['full_path']
                if (gname in self.name or self.name in gname) \
                        and self.name != gname:
                    users |= {
                        user['username']
                        for user in get(
                            self._token,
                            self.absolute_url('/groups/{name}/members'.format(
                                name=quote_plus(gname)
                            ))
                        )
                    }

            return len(users)
        except RuntimeError:
            return 1

    def _members(self, access_level):
        try:
            return {
                GitLabUser.from_data(user, self._token, user['id'])
                for user in self.raw_members()
                if user['access_level'] >= access_level
            }
        except RuntimeError:
            return {GitLabUser.from_data({'username': self.name},
                                         self._token, identifier=None)}

    @property
    def owners(self) -> Set[GitLabUser]:
        """
        Returns the user handles of all owner users.
        """
        return self._members(AccessLevel.OWNER.value)

    @property
    def masters(self) -> Set[GitLabUser]:
        """
        Returns the user handles of all master users.
        """
        return self._members(AccessLevel.ADMIN.value)

    @property
    def name(self) -> str:
        """
        The name of the organization.
        """
        return self._name

    @property
    @lru_cache(None)
    def suborgs(self) -> Set[Organization]:
        """
        Returns the sub-organizations within this organization, recursively.
        """
        result = set()
        for suborg_data in get(self._token, self.url + '/subgroups'):
            suborg = GitLabOrganization.from_data(
                suborg_data, self._token, suborg_data['full_path'])
            result |= {suborg} | suborg.suborgs
        return result

    @property
    @lru_cache(None)
    def repositories(self) -> Set[Repository]:
        """
        Returns the list of repositories contained in this organization
        including subgroup repositories, recursively.
        """
        from IGitt.GitLab.GitLabRepository import GitLabRepository

        return {GitLabRepository.from_data(repo, self._token, repo['id'])
                for repo in get(self._token, self.url + '/projects')
               }.union({
                   repo for org in self.suborgs for repo in org.repositories
               })

    def filter_issues(self,
                      state: Optional[str]=None,
                      label: Optional[str]=None,
                      assignee: Optional[str]=None
                     ) -> Set[GitLabIssue]:
        """
        Filters the issues in the organization based on properties

        :param state: 'opened' or 'closed' or 'all'
        :param label: Label of the issue
        :param assignee: username of issue assignee
        :return: Set of GitLabIssue objects
        """
        params = dict()
        if state:
            params['state'] = state
        if label:
            params['labels'] = label
        if assignee:
            params['assignee_id'] = GitLabUser(self._token,
                                               assignee).identifier
        url = re.compile(r'https://(?:[^/]+)/(.+)/issues/(\d+)')
        return {GitLabIssue.from_data(issue, self._token,
                                      url.match(issue['web_url']).group(0),
                                      issue['iid'])
                for issue in get(self._token, self.url + '/issues', params)}

    @property
    def issues(self) -> Set[GitLabIssue]:
        """
        Returns the list of issue objects in this organization.
        """
        return self.filter_issues(state='opened')

    @staticmethod
    def create(token: Union[GitLabOAuthToken, GitLabPrivateToken],
               name: str,
               path: str,
               parent_id: Optional[int]=None,
               description: Optional[str]=None,
               visibility: str='private',
               lfs_enabled: bool=False,
               request_access_enabled: bool=False) -> Organization:
        """
        Creates a new organization from the given parameters.

        :param token:
            The credentials to be used for authorization.
        :param name:
            The name of the organization.
        :param path:
            The path of the organization.
        :param parent_id:
            The parent organization id to create nested organization.
        :param description:
            The description of the organization.
        :param visibility:
            Controls the visibility of the organization. Can be either
            'private', 'public' or 'internal'.
        :param lfs_enabled:
            Enables Git Large File System for projects in this organization.
        :param request_access_enabled:
            Allow users to request member access on the organization.
        """
        url = '/groups'
        org = post(
            token,
            GitLabOrganization.absolute_url(url),
            {'name': name,
             'path': path,
             'description': description,
             'visibility': visibility,
             'lfs_enabled': lfs_enabled,
             'request_access_enabled': request_access_enabled,
             'parent_id': parent_id}
        )
        return GitLabOrganization.from_data(org, token, org['name'])
