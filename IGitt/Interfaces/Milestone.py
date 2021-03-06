"""
This module contains the milestone abstraction class which provides properties
and actions related to milestones.
"""
from datetime import datetime
from IGitt.Interfaces.Repository import Repository
from IGitt.Interfaces import IGittObject
from IGitt.Interfaces import MilestoneStates


class Milestone(IGittObject):
    """
    Represents a milestone for GitHub or GitLab or any similar collection of
    issues.
    """
    @property
    def number(self) -> int:
        """
        Returns the milestone "number" or id.
        """
        raise NotImplementedError

    @property
    def project(self) -> Repository:
        """
        Returns the repository this milestone is linked with.
        """
        raise NotImplementedError

    @property
    def title(self) -> str:
        """
        Retrieves the title of the milestone.
        """
        raise NotImplementedError

    @title.setter
    def title(self, new_title):
        """
        Sets the title of the milestone.

        :param new_title: The new title.
        """
        raise NotImplementedError

    @property
    def description(self) -> str:
        """
        Retrieves the main description of the milestone.
        """
        raise NotImplementedError

    @description.setter
    def description(self, new_description):
        """
        Sets the description of the milestone

        :param new_description: The new description .
        """
        raise NotImplementedError

    @property
    def state(self) -> MilestoneStates:
        """
        Get's the state of the milestone.

        :return: Either MilestoneStates.OPEN or MilestoneStates.CLOSED.
        """
        raise NotImplementedError

    def close(self):
        """
        Closes the milestone.

        :raises RuntimeError: If something goes wrong (network, auth...).
        """
        raise NotImplementedError

    def reopen(self):
        """
        Reopens the milestone.

        :raises RuntimeError: If something goes wrong (network, auth...).
        """
        raise NotImplementedError

    @property
    def created(self) -> datetime:
        """
        Retrieves a timestamp on when the milestone was created.
        """
        raise NotImplementedError

    @property
    def updated(self) -> datetime:
        """
        Retrieves a timestamp on when the milestone was updated the last time.
        """
        raise NotImplementedError

    @property
    def start_date(self) -> datetime:
        """
        Retrieves a timestamp on when the milestone was started.
        """
        raise NotImplementedError

    @start_date.setter
    def start_date(self, new_date: datetime):
        """
        Sets the start date of the milestone.

        :param new_date: The new start date.
        """
        raise NotImplementedError

    @property
    def due_date(self) -> datetime:
        """
        Retrieves a timestamp on when the milestone is due.
        """
        raise NotImplementedError

    @due_date.setter
    def due_date(self, new_date: datetime):
        """
        Sets the due date of the milestone.

        :param new_date: The new due date.
        """
        raise NotImplementedError

    def delete(self):
        """
        Deletes the milestone.
        This is not possible with GitLab api v4.

        :raises RuntimeError: If something goes wrong (network, auth...).
        """
        raise NotImplementedError

    @staticmethod
    def create(token, repository, title, body=''):
        """
        Create a new milestone in repository.
        """
        raise NotImplementedError

    @property
    def issues(self) -> set:
        """
        Retrieves a set of issue objects that are assigned to this milestone.
        """
        raise NotImplementedError

    @property
    def merge_requests(self) -> set:
        """
        Retrieves a set of merge request objects that are assigned to this
        milestone.
        """
        raise NotImplementedError
