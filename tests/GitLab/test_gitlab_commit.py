import os
import unittest

import vcr

from IGitt.GitLab import GitLabOAuthToken
from IGitt.GitLab.GitLabCommit import GitLabCommit
from IGitt.Interfaces.CommitStatus import CommitStatus, Status

my_vcr = vcr.VCR(match_on=['method', 'scheme', 'host', 'port', 'path'],
                 filter_query_parameters=['access_token'],
                 filter_post_data_parameters=['access_token'],
                 filter_headers=['Link'])


class GitLabCommitTest(unittest.TestCase):

    def setUp(self):
        self.token = GitLabOAuthToken(os.environ.get('GITLAB_TEST_TOKEN', ''))
        self.commit = GitLabCommit(self.token,
                                   'gitmate-test-user/test',
                                   '3fc4b860e0a2c17819934d678decacd914271e5c')

    def test_sha(self):
        self.assertIn('3fc4b86', self.commit.sha)

    @my_vcr.use_cassette('tests/GitLab/cassettes/gitlab_commit_message.yaml')
    def test_message(self):
        self.assertEqual(self.commit.message, 'Update README.md')

    @my_vcr.use_cassette('tests/GitLab/cassettes/gitlab_commit_repository.yaml')
    def test_repository(self):
        self.assertEqual(self.commit.repository.full_name,
                         'gitmate-test-user/test')

    @my_vcr.use_cassette('tests/GitLab/cassettes/gitlab_commit_parent.yaml')
    def test_parent(self):
        self.assertEqual(self.commit.parent.sha,
                         '674498fd415cfadc35c5eb28b8951e800f357c6f')

    @my_vcr.use_cassette('tests/GitLab/cassettes/gitlab_commit_status.yaml')
    def test_set_status(self):
        self.commit = GitLabCommit(self.token,
                                   'gitmate-test-user/test',
                                   '3fc4b860e0a2c17819934d678decacd914271e5c')
        status = CommitStatus(Status.FAILED, 'Theres a problem',
                              'gitmate/test')
        self.commit.set_status(status)
        self.assertEqual(self.commit.get_statuses(
            ).pop().description, 'Theres a problem')

    @my_vcr.use_cassette('tests/GitLab/cassettes/gitlab_combined_commit_status.yaml')
    def test_combined_status(self):
        self.assertEqual(self.commit.combined_status, Status.FAILED)
        commit = GitLabCommit(self.token,
                              'gitmate-test-user/test',
                              'a37bb904b39a4aabee24f52ff98a0a988a41a24a')
        self.assertEqual(commit.combined_status, Status.PENDING)
        commit = GitLabCommit(self.token,
                              'gitmate-test-user/test',
                              '99f484ae167dcfcc35008ba3b5b564443d425ee0')
        self.assertEqual(commit.combined_status, Status.SUCCESS)

    @my_vcr.use_cassette('tests/GitLab/cassettes/gitlab_commit_get_patch.yaml')
    def test_get_patch_for_file(self):
        patch = self.commit.get_patch_for_file('README.md')
        self.assertEqual(patch, '--- a/README.md\n'
                                '+++ b/README.md\n'
                                '@@ -1,2 +1,4 @@\n'
                                ' # test\n'
                                ' a test repo\n'
                                '+\n'
                                '+a tst pr\n')

    @my_vcr.use_cassette('tests/GitLab/cassettes/gitlab_commit_comment.yaml')
    def test_comment(self):
        self.commit = GitLabCommit(self.token,
                                   'gitmate-test-user/test',
                                   '3fc4b860e0a2c17819934d678decacd914271e5c')
        self.commit.comment('An issue is here')
        self.commit.comment("Here in line 4, there's a spelling mistake!",
                            'README.md', 4)
        self.commit.comment("Here in line 4, there's a spelling mistake!",
                            'README.md', 4, mr_number=6)
        self.commit.comment('test comment', 'READNOT.md', mr_number=6)
        self.commit.comment('test comment', 'READNOT.md', 4)

    @my_vcr.use_cassette('tests/GitLab/cassettes/gitlab_commit_unified_diff.yaml')
    def test_unified_diff(self):
        self.assertEqual(self.commit.unified_diff,
                         '--- a/README.md\n'
                         '+++ b/README.md\n'
                         '@@ -1,2 +1,4 @@\n'
                         ' # test\n'
                         ' a test repo\n'
                         '+\n'
                         '+a tst pr\n')
