# encoding: utf-8

'''Tests that pruning ``release/*`` tags leaves alone any tag whose workflow run has not finished.'''

import unittest
from types import SimpleNamespace
from unittest import mock

import requests

from pds.roundup import step, util
from pds.roundup.step import Step


API_URL = 'https://api.github.com'


def _response(runs):
    response = mock.Mock()
    response.json.return_value = {'workflow_runs': runs}
    return response


def _pages(*pages):
    '''A ``requests.get`` stand-in that serves ``pages`` of runs in order, one per call.'''
    return mock.Mock(side_effect=[_response(runs) for runs in pages])


class HasActiveWorkflowRunTest(unittest.TestCase):
    def _active(self, runs):
        with mock.patch.object(util.requests, 'get', return_value=_response(runs)):
            return util.has_active_workflow_run(API_URL, 'owner', 'repo', 'release/1.0.0', 'token')

    def test_in_progress_run_is_active(self):
        self.assertTrue(self._active([{'status': 'in_progress'}]))

    def test_queued_run_is_active(self):
        self.assertTrue(self._active([{'status': 'completed'}, {'status': 'queued'}]))

    def test_waiting_run_is_active(self):
        self.assertTrue(self._active([{'status': 'waiting'}]))

    def test_completed_runs_are_not_active(self):
        self.assertFalse(self._active([{'status': 'completed'}, {'status': 'completed'}]))

    def test_no_runs_is_not_active(self):
        self.assertFalse(self._active([]))

    def test_asks_for_the_runs_of_the_named_ref(self):
        with mock.patch.object(util.requests, 'get', return_value=_response([])) as get:
            util.has_active_workflow_run(API_URL, 'owner', 'repo', 'release/1.0.0', 'token')
        args, kwargs = get.call_args
        self.assertEqual(f'{API_URL}/repos/owner/repo/actions/runs', args[0])
        self.assertEqual('release/1.0.0', kwargs['params']['branch'])
        self.assertEqual('Bearer token', kwargs['headers']['Authorization'])

    def test_unreachable_github_is_assumed_active(self):
        with mock.patch.object(util.requests, 'get', side_effect=requests.ConnectionError('down')):
            self.assertTrue(util.has_active_workflow_run(API_URL, 'owner', 'repo', 'release/1.0.0', 'token'))

    def test_http_error_is_assumed_active(self):
        response = mock.Mock()
        response.raise_for_status.side_effect = requests.HTTPError('403')
        with mock.patch.object(util.requests, 'get', return_value=response):
            self.assertTrue(util.has_active_workflow_run(API_URL, 'owner', 'repo', 'release/1.0.0', 'token'))

    def test_unexpected_payload_is_assumed_active(self):
        response = mock.Mock()
        response.json.return_value = {'message': 'unexpected'}
        with mock.patch.object(util.requests, 'get', return_value=response):
            self.assertTrue(util.has_active_workflow_run(API_URL, 'owner', 'repo', 'release/1.0.0', 'token'))

    def test_malformed_payloads_are_assumed_active(self):
        for payload in ({'workflow_runs': None}, {'workflow_runs': ['oops']}, {'workflow_runs': 'oops'}, ['oops'], None):
            response = mock.Mock()
            response.json.return_value = payload
            with self.subTest(payload=payload), mock.patch.object(util.requests, 'get', return_value=response):
                self.assertTrue(util.has_active_workflow_run(API_URL, 'owner', 'repo', 'release/1.0.0', 'token'))

    def test_undecodable_body_is_assumed_active(self):
        response = mock.Mock()
        response.json.side_effect = ValueError('not json')
        with mock.patch.object(util.requests, 'get', return_value=response):
            self.assertTrue(util.has_active_workflow_run(API_URL, 'owner', 'repo', 'release/1.0.0', 'token'))

    def test_active_run_on_a_later_page_is_found(self):
        full_page = [{'status': 'completed'}] * util.WORKFLOW_RUNS_PER_PAGE
        get = _pages(full_page, [{'status': 'completed'}, {'status': 'in_progress'}])
        with mock.patch.object(util.requests, 'get', get):
            self.assertTrue(util.has_active_workflow_run(API_URL, 'owner', 'repo', 'release/1.0.0', 'token'))
        self.assertEqual([1, 2], [call.kwargs['params']['page'] for call in get.call_args_list])

    def test_all_pages_completed_is_not_active(self):
        full_page = [{'status': 'completed'}] * util.WORKFLOW_RUNS_PER_PAGE
        with mock.patch.object(util.requests, 'get', _pages(full_page, full_page, [{'status': 'completed'}])):
            self.assertFalse(util.has_active_workflow_run(API_URL, 'owner', 'repo', 'release/1.0.0', 'token'))

    def test_failure_on_a_later_page_is_assumed_active(self):
        full_page = [{'status': 'completed'}] * util.WORKFLOW_RUNS_PER_PAGE
        get = mock.Mock(side_effect=[_response(full_page), requests.ConnectionError('down')])
        with mock.patch.object(util.requests, 'get', get):
            self.assertTrue(util.has_active_workflow_run(API_URL, 'owner', 'repo', 'release/1.0.0', 'token'))

    def test_endless_listing_is_assumed_active(self):
        full_page = [{'status': 'completed'}] * util.WORKFLOW_RUNS_PER_PAGE
        get = mock.Mock(return_value=_response(full_page))
        with mock.patch.object(util.requests, 'get', get):
            self.assertTrue(util.has_active_workflow_run(API_URL, 'owner', 'repo', 'release/1.0.0', 'token'))
        self.assertEqual(util.WORKFLOW_RUNS_MAX_PAGES, get.call_count)


class DeleteTagsTest(unittest.TestCase):
    def _delete(self, tags, skip=None):
        git = mock.Mock(side_effect=lambda args: '\n'.join(tags) if args[:2] == ['tag', '--list'] else '')
        with mock.patch.object(util, 'invokeGIT', git):
            util.delete_tags('release/*', skip=skip)
        return [call.args[0] for call in git.call_args_list]

    def test_deletes_every_match_by_default(self):
        calls = self._delete(['release/1.0.0', 'release/2.0.0'])
        self.assertIn(['push', '--delete', 'origin', 'release/1.0.0'], calls)
        self.assertIn(['push', '--delete', 'origin', 'release/2.0.0'], calls)

    def test_skipped_tags_are_kept(self):
        calls = self._delete(['release/1.0.0', 'release/2.0.0'], skip=lambda tag: tag == 'release/2.0.0')
        self.assertIn(['push', '--delete', 'origin', 'release/1.0.0'], calls)
        self.assertNotIn(['push', '--delete', 'origin', 'release/2.0.0'], calls)
        self.assertNotIn(['tag', '--delete', 'release/2.0.0'], calls)


class PruneFinishedReleaseTagsTest(unittest.TestCase):
    '''An unstable roundup must not delete the tag of a stable run that is still going.'''

    def setUp(self):
        environ = {'GITHUB_REPOSITORY': 'owner/repo', 'ADMIN_GITHUB_TOKEN': 'token'}
        self.step = Step(SimpleNamespace(context=SimpleNamespace(environ=environ)))
        patcher = mock.patch.object(step.time, 'sleep')
        self.sleep = patcher.start()
        self.addCleanup(patcher.stop)

    def _prune(self, tags, runs_by_tag):
        def get(url, params, **kwargs):
            return _response(runs_by_tag.get(params['branch'], []))

        git = mock.Mock(side_effect=lambda args: '\n'.join(tags) if args[:2] == ['tag', '--list'] else '')
        with mock.patch.object(util, 'invokeGIT', git), mock.patch.object(util.requests, 'get', side_effect=get):
            self.step.prune_finished_release_tags()
        return [call.args[0] for call in git.call_args_list]

    def test_keeps_the_tag_of_a_run_in_progress(self):
        calls = self._prune(['release/5.4.0'], {'release/5.4.0': [{'status': 'in_progress'}]})
        self.assertNotIn(['push', '--delete', 'origin', 'release/5.4.0'], calls)

    def test_keeps_the_tag_of_a_queued_run(self):
        calls = self._prune(['release/5.4.0'], {'release/5.4.0': [{'status': 'queued'}]})
        self.assertNotIn(['push', '--delete', 'origin', 'release/5.4.0'], calls)

    def test_deletes_the_tag_of_a_finished_run(self):
        calls = self._prune(['release/5.3.0'], {'release/5.3.0': [{'status': 'completed'}]})
        self.assertIn(['push', '--delete', 'origin', 'release/5.3.0'], calls)

    def test_deletes_a_leftover_tag_that_never_had_a_run(self):
        calls = self._prune(['release/1.0.0'], {})
        self.assertIn(['push', '--delete', 'origin', 'release/1.0.0'], calls)

    def test_prunes_only_what_is_finished(self):
        calls = self._prune(
            ['release/5.3.0', 'release/5.4.0'],
            {'release/5.3.0': [{'status': 'completed'}], 'release/5.4.0': [{'status': 'in_progress'}]},
        )
        self.assertIn(['push', '--delete', 'origin', 'release/5.3.0'], calls)
        self.assertNotIn(['push', '--delete', 'origin', 'release/5.4.0'], calls)

    def test_keeps_every_tag_when_github_is_unreachable(self):
        git = mock.Mock(side_effect=lambda args: 'release/5.4.0' if args[:2] == ['tag', '--list'] else '')
        with mock.patch.object(util, 'invokeGIT', git), \
                mock.patch.object(util.requests, 'get', side_effect=requests.ConnectionError('down')):
            self.step.prune_finished_release_tags()
        calls = [call.args[0] for call in git.call_args_list]
        self.assertNotIn(['push', '--delete', 'origin', 'release/5.4.0'], calls)

    def test_uses_the_api_url_from_the_environment(self):
        self.step.assembly.context.environ['GITHUB_API_URL'] = 'https://ghe.example/api/v3'
        git = mock.Mock(side_effect=lambda args: 'release/1.0.0' if args[:2] == ['tag', '--list'] else '')
        with mock.patch.object(util, 'invokeGIT', git), \
                mock.patch.object(util.requests, 'get', return_value=_response([])) as get:
            self.step.prune_finished_release_tags()
        self.assertEqual('https://ghe.example/api/v3/repos/owner/repo/actions/runs', get.call_args.args[0])

    def test_treats_an_empty_api_url_as_unset(self):
        self.step.assembly.context.environ['GITHUB_API_URL'] = ''
        git = mock.Mock(side_effect=lambda args: 'release/1.0.0' if args[:2] == ['tag', '--list'] else '')
        with mock.patch.object(util, 'invokeGIT', git), \
                mock.patch.object(util.requests, 'get', return_value=_response([])) as get:
            self.step.prune_finished_release_tags()
        self.assertEqual(f'{API_URL}/repos/owner/repo/actions/runs', get.call_args.args[0])

    def test_keeps_a_tag_whose_run_appears_after_a_pause(self):
        git = mock.Mock(side_effect=lambda args: 'release/5.4.0' if args[:2] == ['tag', '--list'] else '')
        get = _pages([], [{'status': 'queued'}])
        with mock.patch.object(util, 'invokeGIT', git), mock.patch.object(util.requests, 'get', get):
            self.step.prune_finished_release_tags()
        calls = [call.args[0] for call in git.call_args_list]
        self.assertNotIn(['push', '--delete', 'origin', 'release/5.4.0'], calls)
        self.sleep.assert_called_once_with(step.RUN_VISIBILITY_DELAY_SECONDS)

    def test_does_not_pause_for_a_tag_with_a_run_in_progress(self):
        self._prune(['release/5.4.0'], {'release/5.4.0': [{'status': 'in_progress'}]})
        self.sleep.assert_not_called()


if __name__ == '__main__':
    unittest.main()
