# -*- coding: utf-8 -*-
from plone.app.redirector.storage import RedirectionStorage

import unittest


class TestStorage(unittest.TestCase):
    """Test the RedirectionStorage class.

    This used to be in a doctest inside storage.py itself.
    """

    def test_storage_one_redirect(self):
        # Add one redirect
        p = RedirectionStorage()
        self.assertFalse(p.has_path('/foo'))
        p.add('/foo', '/bar')
        self.assertTrue(p.has_path('/foo'))
        self.assertEqual(p.get('/foo'), '/bar')
        self.assertFalse(p.has_path('/bar'))
        self.assertListEqual(p.redirects('/bar'), ['/foo'])

    def test_storage_no_slash(self):
        # Standard Plone will created redirects with key
        # /plone-site-id/some/path.
        # But a slash at the beginning is not mandatory.
        p = RedirectionStorage()
        self.assertFalse(p.has_path('foo'))
        p.add('foo', 'bar')
        self.assertTrue(p.has_path('foo'))
        self.assertEqual(p.get('foo'), 'bar')
        self.assertFalse(p.has_path('bar'))
        self.assertListEqual(p.redirects('bar'), ['foo'])

    def test_storage_nested(self):
        # Since Plone will created redirects with key
        # /plone-site-id/some/path, testing with multiple slashes seems wise.
        p = RedirectionStorage()
        self.assertFalse(p.has_path('/plone/some/path'))
        p.add('/plone/some/path', '/plone/a/different/path')
        self.assertTrue(p.has_path('/plone/some/path'))
        self.assertEqual(p.get('/plone/some/path'), '/plone/a/different/path')
        self.assertFalse(p.has_path('/plone/a/different/path'))
        self.assertListEqual(p.redirects('/plone/a/different/path'), ['/plone/some/path'])

    def test_storage_trailing_slash(self):
        # trailing slashes are ignored
        p = RedirectionStorage()
        self.assertFalse(p.has_path('/foo/'))
        p.add('/foo', '/bar')
        self.assertTrue(p.has_path('/foo/'))
        self.assertEqual(p.get('/foo/'), '/bar')
        self.assertListEqual(p.redirects('/bar/'), ['/foo'])

        # This goes the other way around too
        self.assertFalse(p.has_path('/quux'))
        p.add('/quux/', '/baaz/')
        self.assertTrue(p.has_path('/quux'))
        self.assertEqual(p.get('/quux'), '/baaz')
        self.assertListEqual(p.redirects('/baaz'), ['/quux'])

    def test_storage_two_redirects(self):
        # Add multiple redirects.
        p = RedirectionStorage()
        p.add('/foo', '/bar')
        p.add('/baz', '/bar')
        self.assertTrue(p.has_path('/baz'))
        self.assertEqual(p.get('/baz'), '/bar')
        self.assertListEqual(sorted(p.redirects('/bar')), ['/baz', '/foo'])

    def test_storage_update_redirect(self):
        # Update a redirect
        p = RedirectionStorage()
        p.add('/foo', '/bar')
        p.add('/baz', '/bar')
        p.add('/foo', '/quux')
        self.assertTrue(p.has_path('/foo'))
        self.assertEqual(p.get('/foo'), '/quux')
        self.assertListEqual(p.redirects('/bar'), ['/baz'])
        self.assertListEqual(p.redirects('/quux'), ['/foo'])

    def test_storage_remove_redirect(self):
        # Remove a redirect
        p = RedirectionStorage()
        p.add('/foo', '/bar')
        p.remove('/foo')
        self.assertFalse(p.has_path('/foo'))
        self.assertEqual(p.get('/foo', default='_notfound_'), '_notfound_')
        self.assertListEqual(p.redirects('/bar'), [])

    def test_storage_chain(self):
        # Update a redirect in a chain
        p = RedirectionStorage()
        p.add('/fred', '/foo')
        self.assertEqual(p.get('/fred'), '/foo')
        self.assertListEqual(sorted(p.redirects('/foo')), ['/fred'])

        p.add('/fred', '/barney')
        self.assertEqual(p.get('/fred'), '/barney')
        self.assertListEqual(sorted(p.redirects('/foo')), [])
        self.assertListEqual(sorted(p.redirects('/barney')), ['/fred'])

        p.add('/barney', '/wilma')
        self.assertEqual(p.get('/fred'), '/wilma')
        self.assertEqual(p.get('/barney'), '/wilma')
        self.assertListEqual(
            sorted(p.redirects('/wilma')), ['/barney', '/fred']
        )
        self.assertListEqual(sorted(p.redirects('/barney')), [])

    def test_storage_destroy_target(self):
        # Destroy the target of a redirect
        p = RedirectionStorage()
        p.add('/fred', '/barney')
        p.add('/barney', '/wilma')
        p.destroy('/wilma')
        self.assertFalse(p.has_path('/barney'))
        self.assertFalse(p.has_path('/fred'))
        self.assertListEqual(p.redirects('/wilma'), [])

    def test_storage_iterator(self):
        # We can get an iterator over all existing paths
        p = RedirectionStorage()
        self.assertListEqual(sorted(iter(p)), [])

        # Add one
        p.add('/baz', '/bar')
        self.assertListEqual(sorted(iter(p)), ['/baz'])

        # Now add some more
        p.add('/foo', '/bar')
        p.add('/barney', '/wilma')
        self.assertListEqual(sorted(p), ['/barney', '/baz', '/foo'])

    def test_storage_no_circular(self):
        # Circular references are ignored
        p = RedirectionStorage()
        p.add('/circle', '/circle')
        self.assertFalse(p.has_path('/circle'))
        self.assertEqual(p.get('/circle', '_marker_'), '_marker_')
        self.assertListEqual(p.redirects('/circle'), [])

    def test_storage_three_step_circular_rename(self):
        # What about three step circular rename ?
        p = RedirectionStorage()

        # Add first redirect.
        p.add('first', 'second')

        # There is only one redirect.

        self.assertEqual(p.get('first'), 'second')
        self.assertIsNone(p.get('second'))
        self.assertIsNone(p.get('third'))

        # There is one back reference.

        self.assertListEqual(p.redirects('first'), [])
        self.assertListEqual(p.redirects('second'), ['first'])
        self.assertListEqual(p.redirects('third'), [])

        # Add second redirect.
        p.add('second', 'third')

        # There are now two.

        self.assertEqual(p.get('first'), 'third')
        self.assertEqual(p.get('second'), 'third')
        self.assertIsNone(p.get('third'))

        # There are two back references as well.
        self.assertListEqual(p.redirects('first'), [])
        self.assertListEqual(p.redirects('second'), [])
        self.assertListEqual(p.redirects('third'), ['first', 'second'])

        # Add third redirect, CIRCULAR.
        p.add('third', 'first')

        # There are still only two redirects.
        self.assertIsNone(p.get('first'))
        self.assertEqual(p.get('second'), 'first')
        self.assertEqual(p.get('third'), 'first')

        # And same for the back references.
        self.assertListEqual(p.redirects('first'), ['second', 'third'])
        self.assertListEqual(p.redirects('second'), [])
        self.assertListEqual(p.redirects('third'), [])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStorage))
    return suite
