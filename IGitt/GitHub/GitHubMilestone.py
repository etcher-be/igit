"""
This contains the Milestone implementation for GitHub
"""
from datetime import datetime

from IGitt.GitHub import GitHubMixin
from IGitt.Interfaces.Milestone import Milestone
from IGitt.GitHub import GitHubToken
from IGitt.Interfaces import post

class GitHubMilestone(GitHubMixin, Milestone):
    """
    This class represents a milestone on GitHub.
    """

    def __init__(self, token: GitHubToken, owner: str, project: str,
                    number: int):
        """
        Creates a new GitHubMilestone object with the given credentials.

        :param token: A Token object to be used for authentication.
        :param owner: The owner of the project
        :param project: The full name of the project.
        :param number: The milestones number.
        :raises RuntimeError: If something goes wrong (network, auth, ...)
        """
        self._token = token
        self._owner = owner
        self._project = project
        self._number = number
        self._url = '/repos/{owner}/{project}/milestones/{milestone_number}'.format(owner=owner,
            project=project, milestone_number=number)

    @staticmethod
    def create(token: GitHubToken, owner: str, project: str,
                title: str, state: str='open', description: str=None,
                 due_on: datetime=None):
        """
        Create a new milestone with given title
        :return: GitHubMilestone object of the newly created milestone.
        """
        url = '/repos/{owner}/{project}/milestones'.format(owner=owner,
                project=project)
        milestone = post(token, GitHubMilestone.absolute_url(url), {'title': title, 'state': state, 'description': description, 'due_on': due_on})
        return GitHubMilestone.from_data(milestone, token, owner, project, milestone['number'])
        # TODO Understand whats different now
