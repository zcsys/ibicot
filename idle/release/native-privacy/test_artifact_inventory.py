"""Collector counterexamples only; these never establish native runtime behavior."""
import io
import json
import plistlib
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from inspect_artifacts import android_summary, inspect, safe_relative, selected_members


class InventoryTests(unittest.TestCase):
    def archive(self, rows):
        data = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(data, 'w') as z:
                for name, value in rows:
                    z.writestr(name, value)
        data.seek(0)
        return zipfile.ZipFile(data)

    def test_read_actual_binary_plist_and_properties(self):
        with self.archive([
            ('Runner.app/PrivacyInfo.xcprivacy', plistlib.dumps(
                {'NSPrivacyTracking': False}, fmt=plistlib.FMT_BINARY)),
            ('base/root/billing.properties', b'version=8.0.0\n'),
            ('Runner.app/executable', b'ignored executable bytes'),
        ]) as z:
            rows = selected_members(z)
        self.assertEqual(len(rows), 2)
        self.assertIs(rows[0][0]['plist']['NSPrivacyTracking'], False)
        self.assertEqual(rows[1][0]['text'], 'version=8.0.0\n')

    def test_duplicate_member_rejected(self):
        with self.archive([('a.properties', b'1'), ('a.properties', b'2')]) as z:
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                selected_members(z)

    def test_unsafe_member_rejected_even_when_not_selected(self):
        for name in ['../outside', '/outside', 'nested/../../outside', 'a\\b']:
            with self.subTest(name=name), self.archive([(name, b'0')]) as z:
                with self.assertRaisesRegex(ValueError, 'unsafe'):
                    selected_members(z)

    def test_safe_paths(self):
        self.assertEqual(str(safe_relative('a/b.apk')), 'a/b.apk')

    def test_large_member_rejected(self):
        with self.archive([('a.properties', b'x' * (1024 * 1024 + 1))]) as z:
            with self.assertRaisesRegex(ValueError, 'oversized'):
                selected_members(z)

    def test_non_dictionary_plist_rejected(self):
        with self.archive([('App/Info.plist', plistlib.dumps(['wrong']))]) as z:
            with self.assertRaisesRegex(ValueError, 'dictionary'):
                selected_members(z)

    def test_corrupt_plist_rejected(self):
        with self.archive([('App/Info.plist', b'not a plist')]) as z:
            with self.assertRaises(plistlib.InvalidFileException):
                selected_members(z)

    def test_actual_manifest_field_names(self):
        xml = b'''<manifest xmlns:android="http://schemas.android.com/apk/res/android"
            package="example.test" android:versionCode="7"><uses-sdk android:minSdkVersion="29"/>
            <uses-permission android:name="android.permission.INTERNET"/>
            <application android:usesCleartextTraffic="false">
            <provider android:name="Example"><meta-data android:name="a" android:value="b"/></provider>
            </application></manifest>'''
        value = android_summary(xml)
        self.assertEqual(value['package'], 'example.test')
        self.assertEqual(value['version_code'], '7')
        self.assertEqual(len(value['permissions']), 1)
        self.assertEqual(value['components'][0]['kind'], 'provider')
        self.assertEqual(len(value['components'][0]['metadata']), 1)

    def test_wrong_manifest_root_rejected(self):
        with self.assertRaisesRegex(ValueError, 'not an Android'):
            android_summary('<not-manifest/>')

    def test_missing_application_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing Android'):
            android_summary('<manifest/>')

    def test_source_drift_rejected_before_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'source').mkdir()
            (root / 'source/a').write_text('changed')
            (root / 'manifest.json').write_text(json.dumps({
                'source_fingerprint': '0' * 64, 'source_sha256': {'a': '0' * 64}}))
            with self.assertRaisesRegex(ValueError, 'source drift'):
                inspect(root, root, [], root / 'out', 'java', root, root)
            self.assertFalse((root / 'out').exists())


if __name__ == '__main__':
    unittest.main()
