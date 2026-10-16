"""Approved check evidence, changing inputs, safe persistence and historical reads."""
from __future__ import annotations
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from euromind_safeops import run_receipts as receipts
from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError, json_bytes, sha256, tree_digest
from euromind_safeops.execution import approve, run
from euromind_safeops.planning import create_plan

class RunReceiptTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = (Path(self.temp.name) / 'private' / 'project').resolve()
        (self.root / 'src').mkdir(parents=True)
        (self.root / 'tests').mkdir()
        (self.root / 'src/demo.py').write_bytes(b'value = 1\n')
        (self.root / 'tests/test_demo.py').write_bytes(b'import unittest\nclass T(unittest.TestCase):\n def test_it(self): pass\n')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['--root', str(self.root), 'init']), 0)
        self.state = self.root / '.safeops'
        self.config = self.state / 'config.json'
        self.write_config({'schema': 1, 'checks': ['compile']})
        self.plan_id = self.approved()

    def write_config(self, value):
        self.config.write_bytes(json_bytes(value))

    def approved(self):
        plan = create_plan(self.root, 'Review public documentation', [], 'private advisory fixture', 'offline')
        approve(self.root, plan['id'], 'private human reason fixture', plan['id'])
        return plan['id']

    def execute(self, effect=None):
        with patch('euromind_safeops.execution.run_check', side_effect=effect, return_value=subprocess.CompletedProcess([], 0, 'private stdout fixture', 'private stderr fixture')):
            return run(self.root, self.plan_id)

    def owned(self, run_id):
        return self.state / 'runs' / run_id

    def records(self, result):
        directory = self.owned(result['run_id'])
        return (json.loads((directory / 'intent.json').read_bytes()), json.loads((directory / 'receipt.json').read_bytes()))

    def call(self, run_id):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(['--json', '--root', str(self.root), 'inspect-run', run_id])
        return (code, json.loads(out.getvalue()))

    def assert_rejected(self, run_id):
        code, payload = self.call(run_id)
        self.assertEqual(code, 2)
        self.assertIsNone(payload['data'])
        self.assertEqual(payload['error']['message'], receipts._ERROR)

    def rewrite(self, path, value):
        value.pop('fingerprint', None)
        value['fingerprint'] = sha256(value)
        path.write_bytes(json_bytes(value) + b'\n')

    def test_real_checks_and_historical_inspection_preserve_inputs_and_privacy(self):
        self.write_config({'schema': 1, 'checks': ['compile', 'unit-tests']})
        self.plan_id = self.approved()
        (self.root / '.git').mkdir()
        (self.root / '.git/HEAD').write_bytes(b'ref: refs/heads/main\n')
        before = {p: p.read_bytes() for group in ('plans', 'approvals') for p in (self.state / group).iterdir()}
        digest = tree_digest(self.root)
        result = run(self.root, self.plan_id)
        self.assertEqual(result['status'], 'passed')
        intent, receipt = self.records(result)
        self.assertEqual(receipt['end_context'], intent['bindings'])
        self.assertEqual(receipt['fingerprint'], result['receipt_fingerprint'])
        self.assertEqual(len(receipt['checks']), 2)
        self.assertEqual({p: p.read_bytes() for p in before}, before)
        self.assertEqual(tree_digest(self.root), digest)
        self.assertEqual((self.root / '.git/HEAD').read_bytes(), b'ref: refs/heads/main\n')
        raw = json.dumps([intent, receipt])
        for value in ('private advisory fixture', 'private human reason fixture', 'value = 1', str(self.root)):
            self.assertNotIn(value, raw)
        before = {p: p.read_bytes() for p in self.state.rglob('*') if p.is_file()}
        with patch('subprocess.run') as child, patch('euromind_safeops.cli.remote_advice') as provider:
            code, payload = self.call(result['run_id'])
            child.assert_not_called()
            provider.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(payload['data']['source_context'], 'historical-binding-only')
        self.assertEqual({p: p.read_bytes() for p in before}, before)

    def test_schema_two_real_checks_do_not_generate_selected_import_bytecode(self):
        self.write_config({'schema': 2, 'checks': ['compile', 'unit-tests'], 'targets': {'compile': ['src'], 'unit-tests': ['tests']}})
        self.plan_id = self.approved()
        result = run(self.root, self.plan_id)
        self.assertEqual(result['status'], 'passed')
        self.assertFalse((self.root / 'tests/__pycache__').exists())
        self.assertIsNotNone(self.records(result)[0]['bindings']['targets_digest'])

    def test_captured_output_is_returned_but_never_persisted(self):
        result = self.execute()
        self.assertEqual(result['checks'][0]['stdout'], 'private stdout fixture')
        raw = b''.join((p.read_bytes() for p in self.owned(result['run_id']).iterdir()))
        for text in (b'private stdout fixture', b'private stderr fixture', b'private advisory fixture', b'private human reason fixture'):
            self.assertNotIn(text, raw)

    def test_failed_check_stops_sequence_and_receipt_inspects_as_exit_one(self):
        self.write_config({'schema': 1, 'checks': ['compile', 'unit-tests']})
        self.plan_id = self.approved()
        result = self.execute(lambda *a, **k: subprocess.CompletedProcess([], 17, '', 'private failure'))
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(len(self.records(result)[1]['checks']), 1)
        self.assertEqual(self.call(result['run_id'])[0], 1)

    def test_timeout_has_fixed_outcome_and_no_exception_text(self):
        result = self.execute(subprocess.TimeoutExpired(['private command'], 1, output='private timeout output'))
        self.assertEqual(result['status'], 'timed-out')
        receipt = self.records(result)[1]
        self.assertEqual(receipt['checks'], [{'check': 'compile', 'exit_code': -1, 'status': 'timed-out'}])
        self.assertNotIn('private', json.dumps(receipt))
        self.assertEqual(self.call(result['run_id'])[0], 1)

    def test_source_changed_by_check_is_recorded_and_stops_remaining_checks(self):
        self.write_config({'schema': 1, 'checks': ['compile', 'unit-tests']})
        self.plan_id = self.approved()

        def change(*args, **kwargs):
            (self.root / 'src/demo.py').write_bytes(b'changed private input\n')
            return subprocess.CompletedProcess([], 0, '', '')
        result = self.execute(change)
        self.assertEqual(result['status'], 'changed-inputs')
        self.assertEqual(result['reasons'], ['source-changed'])
        self.assertEqual(len(result['checks']), 1)
        self.assertNotEqual(*[v['workspace_digest'] for v in (self.records(result)[0]['bindings'], self.records(result)[1]['end_context'])])

    def test_approval_change_is_detected_without_renewal(self):
        path = self.state / 'approvals' / (self.plan_id + '.json')

        def change(*args, **kwargs):
            value = json.loads(path.read_bytes())
            value['reason'] = 'changed local reason'
            path.write_bytes(json_bytes(value))
            return subprocess.CompletedProcess([], 0, '', '')
        result = self.execute(change)
        self.assertEqual(result['reasons'], ['approval-changed'])
        self.assertEqual(json.loads(path.read_bytes())['reason'], 'changed local reason')

    def test_configuration_change_is_detected(self):

        def change(*args, **kwargs):
            self.write_config({'schema': 1, 'checks': ['unit-tests']})
            return subprocess.CompletedProcess([], 0, '', '')
        self.assertEqual(self.execute(change)['reasons'], ['configuration-changed'])

    def test_generated_selected_data_change_is_detected(self):
        cache = self.root / 'src/build'
        cache.mkdir()
        data = cache / 'data.bin'
        data.write_bytes(b'before')
        self.write_config({'schema': 2, 'checks': ['compile'], 'targets': {'compile': ['src']}})
        self.plan_id = self.approved()

        def change(*args, **kwargs):
            data.write_bytes(b'after')
            return subprocess.CompletedProcess([], 0, '', '')
        self.assertEqual(self.execute(change)['reasons'], ['selected-targets-changed'])

    def test_postcheck_unreadable_context_is_incomplete_without_false_pass(self):
        original = receipts.stable_context
        calls = 0

        def fail_after_start(*args):
            nonlocal calls
            calls += 1
            if calls > 1:
                raise SafeOpsError('private OS text')
            return original(*args)
        with patch.object(receipts, 'stable_context', side_effect=fail_after_start):
            result = self.execute()
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['reasons'], ['postcheck-context-unavailable'])
        self.assertIsNone(self.records(result)[1]['end_context'])
        self.assertEqual(self.call(result['run_id'])[0], 1)

    def test_failure_to_start_child_leaves_intent_and_sanitizes_details(self):
        with self.assertRaises(SafeOpsError) as error:
            self.execute(PermissionError('private OS file text'))
        self.assertNotIn('private OS', str(error.exception))
        owned, = (self.state / 'runs').iterdir()
        self.assertIn(owned.name, str(error.exception))
        self.assertFalse((owned / 'receipt.json').exists())
        self.assertEqual(self.call(owned.name)[1]['data']['status'], 'incomplete')

    def test_audit_failure_leaves_no_terminal_receipt_or_success(self):
        with patch('euromind_safeops.execution.audit', side_effect=OSError('private audit path')):
            with self.assertRaisesRegex(SafeOpsError, 'cannot append'):
                self.execute()
        owned, = (self.state / 'runs').iterdir()
        self.assertFalse((owned / 'receipt.json').exists())
        self.assertEqual(self.call(owned.name)[0], 1)

    def test_marker_cleanup_failure_leaves_no_terminal_receipt(self):

        def change(*args, **kwargs):
            (self.state / 'run.lock').write_bytes(b'changed owner')
            return subprocess.CompletedProcess([], 0, '', '')
        with self.assertRaisesRegex(SafeOpsError, 'cleanup refused'):
            self.execute(change)
        owned, = (self.state / 'runs').iterdir()
        self.assertFalse((owned / 'receipt.json').exists())
        self.assertEqual(self.call(owned.name)[0], 1)
        self.assertEqual((self.state / 'run.lock').read_bytes(), b'changed owner')

    def test_terminal_write_failure_keeps_intent_for_inspection(self):
        original = receipts._write_new

        def fail(root, path, value):
            if path.name == 'receipt.json':
                raise OSError('private write failure')
            return original(root, path, value)
        with patch.object(receipts, '_write_new', side_effect=fail):
            with self.assertRaisesRegex(SafeOpsError, 'Cannot complete'):
                self.execute()
        owned, = (self.state / 'runs').iterdir()
        self.assertEqual(self.call(owned.name)[1]['data']['reasons'], ['completion-receipt-absent'])

    def test_missing_approval_and_changing_initial_context_do_not_allocate_run(self):
        original = receipts.capture_context
        count = 0

        def change(*args):
            nonlocal count
            value = original(*args)
            count += 1
            if count == 2:
                value[0]['workspace_digest'] = '0' * 64
            return value
        with patch.object(receipts, 'capture_context', side_effect=change), self.assertRaises(SafeOpsError):
            self.execute()
        self.assertFalse((self.state / 'runs').exists())
        (self.state / 'approvals' / (self.plan_id + '.json')).unlink()
        with self.assertRaises(SafeOpsError):
            self.execute()
        self.assertFalse((self.state / 'runs').exists())

    def test_history_is_independent_of_current_version_and_project(self):
        result = self.execute()
        self.config.unlink()
        (self.state / 'plans' / (self.plan_id + '.json')).unlink()
        (self.state / 'approvals' / (self.plan_id + '.json')).unlink()
        (self.root / 'src/demo.py').write_bytes(b'later changes')
        with patch.object(receipts, '__version__', '99.0.0'):
            code, payload = self.call(result['run_id'])
        self.assertEqual(code, 0)
        self.assertFalse(payload['data']['version_matches'])
        self.assertEqual(payload['data']['status'], 'passed')

    def test_existing_run_id_is_not_overwritten_or_retried(self):
        first = self.execute()
        before = {p: p.read_bytes() for p in self.owned(first['run_id']).iterdir()}
        with patch.object(receipts.secrets, 'token_hex', return_value=first['run_id']), self.assertRaises(SafeOpsError):
            self.execute()
        self.assertEqual({p: p.read_bytes() for p in before}, before)

    def test_run_ids_are_unique_and_histories_preserved(self):
        first, second = (self.execute(), self.execute())
        self.assertNotEqual(first['run_id'], second['run_id'])
        self.assertEqual(self.call(first['run_id'])[0], 0)
        self.assertEqual(self.call(second['run_id'])[0], 0)

    def test_strict_json_and_receipt_read_budget(self):
        result = self.execute()
        path = self.owned(result['run_id']) / 'receipt.json'
        for raw in (b'{"schema":1,"schema":1}', b'{"schema":NaN}', b'\xff', b'[]', b'private invalid json', b' ' * 16001):
            path.write_bytes(raw)
            self.assert_rejected(result['run_id'])

    def test_intent_schema_fields_timestamps_bindings_and_checks_are_strict(self):
        result = self.execute()
        intent, _ = self.records(result)
        path = self.owned(result['run_id']) / 'intent.json'
        for key, value in (('schema', True), ('schema', 2), ('run_id', '0' * 12), ('plan_id', '../escape'), ('started_at', '2026-02-30T00:00:00+00:00'), ('started_at', 42), ('safeops_version', 'private'), ('timeout', True), ('timeout', 301), ('checks', []), ('checks', ['compile', 'compile']), ('checks', [{}]), ('bindings', {}), ('extra', 1)):
            with self.subTest(field=key, value=value):
                changed = copy.deepcopy(intent)
                changed[key] = value
                self.rewrite(path, changed)
                self.assert_rejected(result['run_id'])

    def test_receipt_linkage_and_impossible_results_are_rejected(self):
        result = self.execute()
        _, receipt = self.records(result)
        path = self.owned(result['run_id']) / 'receipt.json'
        changes = [('schema', True), ('run_id', '0' * 12), ('intent_fingerprint', '0' * 64), ('finished_at', 'bad'), ('checks', []), ('checks', {}), ('checks', [{}]), ('checks', [{'check': 'shell', 'exit_code': 0, 'status': 'passed'}]), ('checks', [{'check': 'compile', 'exit_code': False, 'status': 'passed'}]), ('checks', [{'check': 'compile', 'exit_code': 1, 'status': 'passed'}]), ('checks', [{'check': 'compile', 'exit_code': 2 ** 32, 'status': 'failed'}]), ('checks', [{'check': 'compile', 'exit_code': 2, 'status': 'timed-out'}]), ('status', 'failed'), ('status', 'changed-inputs'), ('reasons', ['private reason']), ('end_context', {}), ('extra', 1)]
        for key, value in changes:
            with self.subTest(field=key, value=value):
                changed = copy.deepcopy(receipt)
                changed[key] = value
                self.rewrite(path, changed)
                self.assert_rejected(result['run_id'])

    def test_unrehashed_tampering_is_rejected(self):
        result = self.execute()
        path = self.owned(result['run_id']) / 'receipt.json'
        value = json.loads(path.read_bytes())
        value['status'] = 'failed'
        path.write_bytes(json_bytes(value))
        self.assert_rejected(result['run_id'])

    def test_intent_or_receipt_changes_during_inspection_fail(self):
        result = self.execute()
        original = receipts._read
        for target in ('intent.json', 'receipt.json'):
            calls = 0

            def change(root, path, limit):
                nonlocal calls
                raw = original(root, path, limit)
                if path.name == target:
                    calls += 1
                    if calls > 1:
                        return raw + b' '
                return raw
            with patch.object(receipts, '_read', side_effect=change):
                self.assert_rejected(result['run_id'])

    def test_receipt_appearing_during_inspection_fails(self):
        result = self.execute()
        owned = self.owned(result['run_id'])
        raw = (owned / 'receipt.json').read_bytes()
        (owned / 'receipt.json').unlink()
        original = receipts._read
        calls = 0

        def appear(root, path, limit):
            nonlocal calls
            value = original(root, path, limit)
            if path.name == 'intent.json':
                calls += 1
                if calls == 2:
                    (owned / 'receipt.json').write_bytes(raw)
            return value
        with patch.object(receipts, '_read', side_effect=appear):
            self.assert_rejected(result['run_id'])

    def test_storage_owner_change_prevents_terminal_write(self):
        original = receipts.begin_run

        def change(*args):
            owner = original(*args)
            owner['identities'][-1] = (0, 0)
            return owner
        with patch.object(receipts, 'begin_run', side_effect=change), self.assertRaises(SafeOpsError):
            self.execute()
        owned, = (self.state / 'runs').iterdir()
        self.assertFalse((owned / 'receipt.json').exists())

    def test_exclusive_write_budget_and_changed_readback_fail(self):
        with patch.object(receipts, 'MAX_RECEIPT_BYTES', 1), self.assertRaises(SafeOpsError):
            self.execute()
        original = receipts._read

        def change(root, path, limit):
            value = original(root, path, limit)
            return value + b' ' if path.name == 'intent.json' else value
        with patch.object(receipts, '_read', side_effect=change), self.assertRaises(SafeOpsError):
            self.execute()

    def test_initial_observation_rejects_control_changes(self):
        original = receipts._source_snapshot

        def change(*args):
            value = original(*args)
            self.config.write_bytes(json_bytes({'schema': 1, 'checks': ['unit-tests']}))
            return value
        with patch.object(receipts, '_source_snapshot', side_effect=change), self.assertRaises(SafeOpsError):
            self.execute()
        self.assertFalse((self.state / 'runs').exists())

    def test_changed_plan_has_fixed_reason_and_bad_ids_fail(self):

        def change(*args, **kwargs):
            path = self.state / 'plans' / (self.plan_id + '.json')
            value = json.loads(path.read_bytes())
            value['advice'] = 'changed private advice'
            self.rewrite(path, value)
            return subprocess.CompletedProcess([], 0, '', '')
        self.assertEqual(self.execute(change)['reasons'], ['plan-changed'])
        with self.assertRaises(SafeOpsError):
            receipts.read_plan(self.root, '../escape')

    def test_unfinished_sequence_cannot_claim_failed_or_passed_with_unchanged_inputs(self):
        self.write_config({'schema': 1, 'checks': ['compile', 'unit-tests']})
        self.plan_id = self.approved()
        result = self.execute(lambda *a, **k: subprocess.CompletedProcess([], 1, '', ''))
        _, value = self.records(result)
        value['checks'][0] = {'check': 'compile', 'status': 'passed', 'exit_code': 0}
        self.rewrite(self.owned(result['run_id']) / 'receipt.json', value)
        self.assert_rejected(result['run_id'])

    def test_nonpassing_check_cannot_be_followed_by_another_recorded_check(self):
        self.write_config({'schema': 1, 'checks': ['compile', 'unit-tests']})
        self.plan_id = self.approved()
        result = self.execute()
        _, value = self.records(result)
        value['checks'][0] = {'check': 'compile', 'status': 'failed', 'exit_code': 1}
        self.rewrite(self.owned(result['run_id']) / 'receipt.json', value)
        self.assert_rejected(result['run_id'])

    def test_receipt_context_hash_shapes_and_missing_fields_fail(self):
        result = self.execute()
        _, value = self.records(result)
        path = self.owned(result['run_id']) / 'receipt.json'
        for key in ('workspace_digest', 'targets_digest'):
            changed = copy.deepcopy(value)
            changed['end_context'][key] = 'bad'
            self.rewrite(path, changed)
            self.assert_rejected(result['run_id'])
        changed = copy.deepcopy(value)
        changed.pop('checks')
        self.rewrite(path, changed)
        self.assert_rejected(result['run_id'])

    def test_directory_identity_change_during_inspection_fails(self):
        result = self.execute()
        original = receipts._directory
        count = 0

        def change(path):
            nonlocal count
            identity = original(path)
            if path == self.state:
                count += 1
                if count > 1:
                    return (0, 0)
            return identity
        with patch.object(receipts, '_directory', side_effect=change):
            self.assert_rejected(result['run_id'])

    def test_run_cli_operational_error_never_returns_success(self):
        output = io.StringIO()
        with patch('euromind_safeops.execution.run_check', side_effect=OSError('private process error')), contextlib.redirect_stdout(output):
            code = main(['--json', '--root', str(self.root), 'run', self.plan_id])
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 2)
        self.assertIsNone(payload['data'])
        self.assertNotIn('private process error', payload['error']['message'])

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX FIFO')
    def test_audit_fifo_created_by_check_does_not_block_or_complete(self):
        path = self.state / 'audit.jsonl'

        def change(*args, **kwargs):
            path.unlink()
            os.mkfifo(path)
            return subprocess.CompletedProcess([], 0, '', '')
        with self.assertRaisesRegex(SafeOpsError, 'cannot append'):
            self.execute(change)
        owned, = (self.state / 'runs').iterdir()
        self.assertFalse((owned / 'receipt.json').exists())

    def test_invalid_ids_and_missing_or_partial_evidence_are_rejected(self):
        for value in ('../private', 'not-an-id', '0' * 12):
            self.assert_rejected(value)
        result = self.execute()
        (self.owned(result['run_id']) / 'intent.json').write_bytes(b'partial')
        self.assert_rejected(result['run_id'])

    def test_plan_and_policy_preflight_read_limits_fail_without_child(self):
        plan = self.state / 'plans' / (self.plan_id + '.json')
        for path in (plan, self.config):
            before = path.read_bytes()
            path.write_bytes(b' ' * 256001)
            with patch('euromind_safeops.execution.run_check') as child, self.assertRaises(SafeOpsError):
                run(self.root, self.plan_id)
            child.assert_not_called()
            path.write_bytes(before)

    def test_receipt_and_control_hardlinks_fail(self):
        result = self.execute()
        for target in (self.owned(result['run_id']) / 'receipt.json', self.config):
            alias = Path(self.temp.name) / 'alias'
            try:
                os.link(target, alias)
            except OSError:
                self.skipTest('Hardlinks unavailable')
            try:
                if target == self.config:
                    with self.assertRaises(SafeOpsError):
                        self.execute()
                else:
                    self.assert_rejected(result['run_id'])
            finally:
                alias.unlink()

    def test_history_directory_symlink_is_rejected_before_execution(self):
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        try:
            (self.state / 'runs').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Symlinks unavailable')
        with patch('euromind_safeops.execution.run_check') as child, self.assertRaises(SafeOpsError):
            run(self.root, self.plan_id)
        child.assert_not_called()
        self.assertEqual(list(outside.iterdir()), [])

    def test_receipt_symlink_is_rejected(self):
        result = self.execute()
        path = self.owned(result['run_id']) / 'receipt.json'
        path.unlink()
        outside = Path(self.temp.name) / 'outside'
        outside.write_bytes(b'private external data')
        try:
            path.symlink_to(outside)
        except OSError:
            self.skipTest('Symlinks unavailable')
        self.assert_rejected(result['run_id'])

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX FIFO')
    def test_plan_and_receipt_fifos_do_not_block(self):
        result = self.execute()
        for target in (self.state / 'plans' / (self.plan_id + '.json'), self.owned(result['run_id']) / 'receipt.json'):
            before = target.read_bytes()
            target.unlink()
            os.mkfifo(target)
            try:
                if target.name == 'receipt.json':
                    self.assert_rejected(result['run_id'])
                else:
                    with self.assertRaises(SafeOpsError):
                        self.execute()
            finally:
                target.unlink()
                target.write_bytes(before)
if __name__ == '__main__':
    unittest.main()
