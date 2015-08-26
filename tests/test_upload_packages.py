from mock import (
    Mock,
    patch,
)
import os
from unittest import TestCase

from upload_packages import (
    get_changes,
    upload_package,
)
from utils import temp_dir


CHANGES_DATA = """\
-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA1

Format: 1.8
Date: Mon, 10 Aug 2015 20:16:09 +0000
Source: juju-core
Binary: juju-core juju juju-local juju-local-kvm
Architecture: source
Version: 1.24.5-0ubuntu1~14.04.1~juju1
Distribution: trusty
"""


class UploadPackageTestCase(TestCase):

    def test_get_changes(self):
        with temp_dir() as package_dir:
            changes_path = os.path.join(package_dir, 'foo_source.changes')
            with open(changes_path, 'w') as changes_file:
                changes_file.write(CHANGES_DATA)
            with open(os.path.join(package_dir, 'foo.dsc'), 'w') as other_file:
                other_file.write('other_file')
            source_name, version, file_name = get_changes(package_dir)
        self.assertEqual('juju-core', source_name)
        self.assertEqual('1.24.5-0ubuntu1~14.04.1~juju1', version)
        self.assertEqual('foo_source.changes', file_name)

    @patch('subprocess.check_call', autospec=True)
    @patch('upload_packages.get_changes', autospec=True)
    def test_upload_package_uploaded(self, gc_mock, cc_mock):
        gc_mock.return_value = (
            'juju-core', '1.24.5-0ubuntu1~14.04.1~juju1', 'foo_source.changes')
        archive = Mock(getPublishedSources=Mock())
        archive.getPublishedSources.return_value = [
            Mock(source_package_version='1.24.5-0ubuntu1~14.04.1~juju1',
                 source_package_name='juju-core')]
        with temp_dir() as package_dir:
            result = upload_package(
                'ppa:bar/baz', archive, package_dir, dry_run=False)
        self.assertFalse(result)
        self.assertEqual(0, cc_mock.call_count)
        gc_mock.assert_called_with(package_dir)
        archive.getPublishedSources.assert_called_with(
            source_name='juju-core', version='1.24.5-0ubuntu1~14.04.1~juju1')

    @patch('subprocess.check_call', autospec=True)
    @patch('upload_packages.get_changes', autospec=True)
    def test_upload_package_uploading(self, gc_mock, cc_mock):
        gc_mock.return_value = (
            'juju-core', '1.24.5-0ubuntu1~14.04.1~juju1', 'foo_source.changes')
        archive = Mock(getPublishedSources=Mock())
        archive.getPublishedSources.return_value = []
        with temp_dir() as package_dir:
            result = upload_package(
                'ppa:bar/baz', archive, package_dir, dry_run=False)
        self.assertTrue(result)
        gc_mock.assert_called_with(package_dir)
        cc_mock.assert_called_with(
            ['dput', 'ppa:bar/baz', 'foo_source.changes'], cwd=package_dir)
        archive.getPublishedSources.assert_called_with(
            source_name='juju-core', version='1.24.5-0ubuntu1~14.04.1~juju1')
