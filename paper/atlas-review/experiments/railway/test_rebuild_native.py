"""Exercise the rebuild verdict with matching, changed and missing class bytes.

The compiler is simulated to isolate comparison and exit behaviour. The real
Java 8 compilation is checked separately by command V09.
"""
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile


spec = importlib.util.spec_from_file_location(
    'rebuild_native', Path(__file__).with_name('rebuild_native.py'))
rebuild = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rebuild)
JARS = (
    'atlas-railway-native-verifier.jar',
    'trainbenchmark-format-emf-model-1.0.0-atlas-native.jar',
    'trainbenchmark-tool-viatra-patterns-1.0.0-atlas-native.jar',
)


class RebuildVerdictTests(unittest.TestCase):
    def exercise(self, mode):
        with tempfile.TemporaryDirectory(prefix='railway-rebuild-test-') as temp:
            root = Path(temp)
            native = root / 'payload/native'
            (native / 'source').mkdir(parents=True)
            (native / 'source/Example.java').write_text('class Example {}', encoding='utf-8')
            (native / 'lib').mkdir()
            for index, name in enumerate(JARS):
                with zipfile.ZipFile(native / 'lib' / name, 'w') as archive:
                    archive.writestr(f'Example{index}.class', b'retained class')
                    archive.writestr('META-INF/NOTICE', b'retained resource')
            out = root / 'build'

            def compiler(command, **kwargs):
                if command[-1] == '-version':
                    return subprocess.CompletedProcess(command, 0, '', 'javac 1.8.0_504')
                for index in range(3):
                    if mode == 'missing' and index == 0:
                        continue
                    content = b'changed class' if mode == 'changed' and index == 0 else b'retained class'
                    (out / 'classes' / f'Example{index}.class').write_bytes(content)
                return subprocess.CompletedProcess(command, 0, '', '')

            args = ['rebuild_native.py', '--payload', str(root / 'payload'),
                    '--out', str(out), '--javac', 'fake-javac']
            with patch.object(sys, 'argv', args), \
                    patch.object(rebuild.shutil, 'which', return_value='fake-javac'), \
                    patch.object(rebuild.subprocess, 'run', side_effect=compiler), \
                    redirect_stdout(io.StringIO()):
                if mode == 'matching':
                    rebuild.main()
                else:
                    with self.assertRaisesRegex(AssertionError, 'non-identical'):
                        rebuild.main()
            result = json.loads((out / 'REBUILD_RESULT.json').read_text(encoding='utf-8'))
            for name in JARS:
                with zipfile.ZipFile(out / name) as archive:
                    self.assertEqual(archive.read('META-INF/NOTICE'), b'retained resource')
            return result

    def test_matching_classes_pass(self):
        result = self.exercise('matching')
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(sum(r['byte_identical_recompiled_classes'] for r in result['jars']), 3)

    def test_changed_class_fails(self):
        result = self.exercise('changed')
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['jars'][0]['different_classes'], ['Example0.class'])
        self.assertEqual(result['jars'][0]['missing_classes'], [])

    def test_missing_class_fails(self):
        result = self.exercise('missing')
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['jars'][0]['missing_classes'], ['Example0.class'])


if __name__ == '__main__':
    unittest.main()
