# -*- coding: utf-8 -*-
from plone.app.redirector.storage import RedirectionStorage

import unittest


class TestStorage(unittest.TestCase):
    """Test the RedirectionStorage class.

    This used to be in a doctest inside storage.py itself.
    """

    def test_storage_one_redirect(self):
        # Add one redirect
        st = RedirectionStorage()
        self.assertFalse(st.has_path('/foo'))
        st.add('/foo', '/bar')
        self.assertTrue(st.has_path('/foo'))
        self.assertEqual(st.get('/foo'), '/bar')
        self.assertFalse(st.has_path('/bar'))
        self.assertListEqual(st.redirects('/bar'), ['/foo'])
        self.assertIn('/foo', st)
        self.assertNotIn('/bar', st)
        self.assertEqual(st['/foo'], '/bar')
        with self.assertRaises(KeyError):
            st['/bar']

    def test_storage_no_slash(self):
        # Standard Plone will created redirects with key
        # /plone-site-id/some/path.
        # But a slash at the beginning is not mandatory.
        st = RedirectionStorage()
        self.assertFalse(st.has_path('foo'))
        st.add('foo', 'bar')
        self.assertTrue(st.has_path('foo'))
        self.assertEqual(st.get('foo'), 'bar')
        self.assertFalse(st.has_path('bar'))
        self.assertListEqual(st.redirects('bar'), ['foo'])
        self.assertIn('foo', st)
        self.assertNotIn('bar', st)
        self.assertEqual(st['foo'], 'bar')
        with self.assertRaises(KeyError):
            st['bar']

    def test_storage_nested(self):
        # Since Plone will created redirects with key
        # /plone-site-id/some/path, testing with multiple slashes seems wise.
        st = RedirectionStorage()
        self.assertFalse(st.has_path('/plone/some/path'))
        st.add('/plone/some/path', '/plone/a/different/path')
        self.assertTrue(st.has_path('/plone/some/path'))
        self.assertEqual(st.get('/plone/some/path'), '/plone/a/different/path')
        self.assertFalse(st.has_path('/plone/a/different/path'))
        self.assertListEqual(st.redirects('/plone/a/different/path'), ['/plone/some/path'])
        self.assertIn('/plone/some/path', st)
        self.assertNotIn('/plone/a/different/path', st)
        self.assertEqual(st['/plone/some/path'], '/plone/a/different/path')
        with self.assertRaises(KeyError):
            st['/plone/a/different/path']

    def test_storage_trailing_slash(self):
        # trailing slashes are ignored
        st = RedirectionStorage()
        self.assertFalse(st.has_path('/foo/'))
        st.add('/foo', '/bar')
        self.assertTrue(st.has_path('/foo/'))
        self.assertEqual(st.get('/foo/'), '/bar')
        self.assertListEqual(st.redirects('/bar/'), ['/foo'])
        self.assertIn('/foo/', st)
        self.assertNotIn('/bar/', st)
        self.assertEqual(st['/foo/'], '/bar')
        with self.assertRaises(KeyError):
            st['/bar/']

        # This goes the other way around too
        self.assertFalse(st.has_path('/quux'))
        st.add('/quux/', '/baaz/')
        self.assertTrue(st.has_path('/quux'))
        self.assertEqual(st.get('/quux'), '/baaz')
        self.assertListEqual(st.redirects('/baaz'), ['/quux'])
        self.assertIn('/quux', st)
        self.assertNotIn('/baaz', st)
        self.assertEqual(st['/quux'], '/baaz')
        with self.assertRaises(KeyError):
            st['/baaz']

    def test_storage_two_redirects_plain(self):
        # Add multiple redirects.
        st = RedirectionStorage()
        st.add('/foo', '/bar')
        st.add('/baz', '/bar')
        self.assertTrue(st.has_path('/baz'))
        self.assertEqual(st.get('/baz'), '/bar')
        self.assertListEqual(sorted(st.redirects('/bar')), ['/baz', '/foo'])
        self.assertIn('/foo', st)
        self.assertIn('/baz', st)
        self.assertNotIn('/bar', st)

    def test_storage_two_redirects_pythonic(self):
        # Add multiple redirects.
        st = RedirectionStorage()
        st['/foo'] = '/bar'
        st['/baz'] = '/bar'
        self.assertTrue(st.has_path('/baz'))
        self.assertEqual(st.get('/baz'), '/bar')
        self.assertListEqual(sorted(st.redirects('/bar')), ['/baz', '/foo'])
        self.assertIn('/foo', st)
        self.assertIn('/baz', st)
        self.assertNotIn('/bar', st)

    def test_storage_clear(self):
        # Clear all information.
        st = RedirectionStorage()
        st['/foo'] = '/bar'
        st['/baz'] = '/bar'
        st.clear()
        self.assertNotIn('/foo', st)
        self.assertNotIn('/baz', st)
        self.assertEqual(len(st.redirects('/bar')), 0)
        # Test the internal structures directly
        self.assertEqual(len(st._paths), 0)
        self.assertEqual(len(st._rpaths), 0)

    def test_storage_update_redirect(self):
        # Update a redirect
        st = RedirectionStorage()
        st.add('/foo', '/bar')
        st.add('/baz', '/bar')
        st.add('/foo', '/quux')
        self.assertTrue(st.has_path('/foo'))
        self.assertEqual(st.get('/foo'), '/quux')
        self.assertListEqual(st.redirects('/bar'), ['/baz'])
        self.assertListEqual(st.redirects('/quux'), ['/foo'])
        self.assertIn('/foo', st)

    def test_storage_remove_redirect_plain(self):
        # Remove a redirect
        st = RedirectionStorage()
        st.add('/foo', '/bar')
        st.remove('/foo')
        self.assertFalse(st.has_path('/foo'))
        self.assertEqual(st.get('/foo', default='_notfound_'), '_notfound_')
        self.assertListEqual(st.redirects('/bar'), [])
        self.assertNotIn('/foo', st)
        with self.assertRaises(KeyError):
            st.remove('/foo')

    def test_storage_remove_redirect_pythonic(self):
        # Remove a redirect
        st = RedirectionStorage()
        st['/foo'] = '/bar'
        self.assertIn('/foo', st)
        del st['/foo']
        self.assertNotIn('/foo', st)
        with self.assertRaises(KeyError):
            st['/foo']
        self.assertListEqual(st.redirects('/bar'), [])

        # test with extra slash
        st['/foo'] = '/bar'
        self.assertIn('/foo', st)
        del st['/foo/']
        self.assertNotIn('/foo', st)
        with self.assertRaises(KeyError):
            st['/foo/']
        self.assertListEqual(st.redirects('/bar'), [])

    def test_storage_chain(self):
        # Update a redirect in a chain
        st = RedirectionStorage()
        st.add('/fred', '/foo')
        self.assertEqual(st.get('/fred'), '/foo')
        self.assertListEqual(sorted(st.redirects('/foo')), ['/fred'])

        st.add('/fred', '/barney')
        self.assertEqual(st.get('/fred'), '/barney')
        self.assertListEqual(sorted(st.redirects('/foo')), [])
        self.assertListEqual(sorted(st.redirects('/barney')), ['/fred'])

        st.add('/barney', '/wilma')
        self.assertEqual(st.get('/fred'), '/wilma')
        self.assertEqual(st.get('/barney'), '/wilma')
        self.assertListEqual(
            sorted(st.redirects('/wilma')), ['/barney', '/fred']
        )
        self.assertListEqual(sorted(st.redirects('/barney')), [])
        self.assertIn('/fred', st)
        self.assertIn('/barney', st)

    def test_storage_destroy_target(self):
        # Destroy the target of a redirect
        st = RedirectionStorage()
        st.add('/fred', '/barney')
        st.add('/barney', '/wilma')
        st.destroy('/wilma')
        self.assertFalse(st.has_path('/barney'))
        self.assertFalse(st.has_path('/fred'))
        self.assertListEqual(st.redirects('/wilma'), [])
        self.assertNotIn('/fred', st)
        self.assertNotIn('/barney', st)

    def test_storage_iterator(self):
        # We can get an iterator over all existing paths
        st = RedirectionStorage()
        self.assertListEqual(sorted(iter(st)), [])

        # Add one
        st.add('/baz', '/bar')
        self.assertListEqual(sorted(iter(st)), ['/baz'])

        # Now add some more
        st.add('/foo', '/bar')
        st.add('/barney', '/wilma')
        self.assertListEqual(sorted(st), ['/barney', '/baz', '/foo'])

    def test_storage_len(self):
        # We can get the length of the storage (number of old paths).
        st = RedirectionStorage()
        self.assertEqual(len(st), 0)

        # Add one
        st['/baz'] = '/bar'
        self.assertEqual(len(st), 1)

        # Now add some more
        st['/foo'] = '/bar'
        st['/barney'] = '/wilma'
        self.assertEqual(len(st), 3)

    def test_storage_no_circular(self):
        # Circular references are ignored
        st = RedirectionStorage()
        st.add('/circle', '/circle')
        self.assertFalse(st.has_path('/circle'))
        self.assertEqual(st.get('/circle', '_marker_'), '_marker_')
        self.assertListEqual(st.redirects('/circle'), [])
        self.assertNotIn('/circle', st)

    def test_storage_three_step_circular_rename(self):
        # What about three step circular rename ?
        st = RedirectionStorage()

        # Add first redirect.
        st.add('first', 'second')

        # There is only one redirect.

        self.assertEqual(st.get('first'), 'second')
        self.assertIsNone(st.get('second'))
        self.assertIsNone(st.get('third'))

        # There is one back reference.

        self.assertListEqual(st.redirects('first'), [])
        self.assertListEqual(st.redirects('second'), ['first'])
        self.assertListEqual(st.redirects('third'), [])

        # Add second redirect.
        st.add('second', 'third')

        # There are now two.

        self.assertEqual(st.get('first'), 'third')
        self.assertEqual(st.get('second'), 'third')
        self.assertIsNone(st.get('third'))

        # There are two back references as well.
        self.assertListEqual(st.redirects('first'), [])
        self.assertListEqual(st.redirects('second'), [])
        self.assertListEqual(st.redirects('third'), ['first', 'second'])

        # Add third redirect, CIRCULAR.
        st.add('third', 'first')

        # There are still only two redirects.
        self.assertIsNone(st.get('first'))
        self.assertEqual(st.get('second'), 'first')
        self.assertEqual(st.get('third'), 'first')
        self.assertNotIn('first', st)
        self.assertIn('second', st)
        self.assertIn('third', st)

        # And same for the back references.
        self.assertListEqual(st.redirects('first'), ['second', 'third'])
        self.assertListEqual(st.redirects('second'), [])
        self.assertListEqual(st.redirects('third'), [])

    def test_storage_non_string_path_fails(self):
        st = RedirectionStorage()
        with self.assertRaises(AttributeError):
            st[0] = '/bar'
        with self.assertRaises(AttributeError):
            st['/foo'] = 0
