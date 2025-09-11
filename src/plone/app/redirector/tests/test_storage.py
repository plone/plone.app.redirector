from DateTime import DateTime
from plone.app.redirector.storage import RedirectionStorage

import unittest


class TestStorage(unittest.TestCase):
    """Test the RedirectionStorage class.

    This used to be in a doctest inside storage.py itself.
    """

    def test_storage_one_redirect(self):
        # Add one redirect
        st = RedirectionStorage()
        self.assertFalse(st.has_path("/foo"))
        st.add("/foo", "/bar")
        self.assertTrue(st.has_path("/foo"))
        self.assertEqual(st.get("/foo"), "/bar")
        self.assertFalse(st.has_path("/bar"))
        self.assertListEqual(st.redirects("/bar"), ["/foo"])
        self.assertIn("/foo", st)
        self.assertNotIn("/bar", st)
        self.assertEqual(st["/foo"], "/bar")
        with self.assertRaises(KeyError):
            st["/bar"]

    def test_storage_get_full_standard(self):
        # get_full gets the full tuple instead of only the path
        st = RedirectionStorage()
        time1 = DateTime()
        st.add("/foo", "/bar", now=time1, manual=False)
        full = st.get_full("/foo")
        self.assertIsInstance(full, tuple)
        self.assertEqual(full, st._paths["/foo"])
        self.assertEqual(full[0], "/bar")
        self.assertEqual(full[1], time1)
        self.assertFalse(full[2])  # manual

    def test_storage_get_full_fallback(self):
        # get_full gets the full tuple,
        # even if the unmigrated data only has the path
        st = RedirectionStorage()
        st._paths["/foo"] = "/bar"
        self.assertEqual(st._paths["/foo"], "/bar")
        full = st.get_full("/foo")
        self.assertIsInstance(full, tuple)
        self.assertEqual(full[0], "/bar")
        # Instead of a DateTime, we get None in the fallback
        self.assertIsNone(full[1])
        self.assertTrue(full[2])  # manual

    def test_storage_no_slash(self):
        # Standard Plone will created redirects with key
        # /plone-site-id/some/path.
        # But a slash at the beginning is not mandatory.
        st = RedirectionStorage()
        self.assertFalse(st.has_path("foo"))
        st.add("foo", "bar")
        self.assertTrue(st.has_path("foo"))
        self.assertEqual(st.get("foo"), "bar")
        self.assertFalse(st.has_path("bar"))
        self.assertListEqual(st.redirects("bar"), ["foo"])
        self.assertIn("foo", st)
        self.assertNotIn("bar", st)
        self.assertEqual(st["foo"], "bar")
        with self.assertRaises(KeyError):
            st["bar"]

    def test_storage_nested(self):
        # Since Plone will created redirects with key
        # /plone-site-id/some/path, testing with multiple slashes seems wise.
        st = RedirectionStorage()
        self.assertFalse(st.has_path("/plone/some/path"))
        st.add("/plone/some/path", "/plone/a/different/path")
        self.assertTrue(st.has_path("/plone/some/path"))
        self.assertEqual(st.get("/plone/some/path"), "/plone/a/different/path")
        self.assertFalse(st.has_path("/plone/a/different/path"))
        self.assertListEqual(
            st.redirects("/plone/a/different/path"), ["/plone/some/path"]
        )
        self.assertIn("/plone/some/path", st)
        self.assertNotIn("/plone/a/different/path", st)
        self.assertEqual(st["/plone/some/path"], "/plone/a/different/path")
        with self.assertRaises(KeyError):
            st["/plone/a/different/path"]

    def test_storage_trailing_slash(self):
        # trailing slashes are ignored
        st = RedirectionStorage()
        self.assertFalse(st.has_path("/foo/"))
        st.add("/foo", "/bar")
        self.assertTrue(st.has_path("/foo/"))
        self.assertEqual(st.get("/foo/"), "/bar")
        self.assertListEqual(st.redirects("/bar/"), ["/foo"])
        self.assertIn("/foo/", st)
        self.assertNotIn("/bar/", st)
        self.assertEqual(st["/foo/"], "/bar")
        with self.assertRaises(KeyError):
            st["/bar/"]

        # This goes the other way around too
        self.assertFalse(st.has_path("/quux"))
        st.add("/quux/", "/baaz/")
        self.assertTrue(st.has_path("/quux"))
        self.assertEqual(st.get("/quux"), "/baaz")
        self.assertListEqual(st.redirects("/baaz"), ["/quux"])
        self.assertIn("/quux", st)
        self.assertNotIn("/baaz", st)
        self.assertEqual(st["/quux"], "/baaz")
        with self.assertRaises(KeyError):
            st["/baaz"]

    def test_storage_date(self):
        # Add one redirect
        st = RedirectionStorage()
        time1 = DateTime()
        st.add("/foo", "/bar")
        time2 = DateTime()
        # Check the internals: we now store a date (and manual True/False).
        info = st._paths["/foo"]
        self.assertIsInstance(info, tuple)
        self.assertTrue(time1 < info[1] < time2)
        # Use an explicit date.
        now = DateTime(2000, 12, 31)
        st.add("/exp", "/bar", now=now)
        info = st._paths["/exp"]
        self.assertIsInstance(info, tuple)
        self.assertEqual(info[1], now)
        # Update with a different date.
        st.add("/exp", "/bar", now=time1)
        info = st._paths["/exp"]
        self.assertIsInstance(info, tuple)
        self.assertEqual(info[1], time1)
        # Update with an implicit date.
        st.add("/exp", "/bar")
        time3 = DateTime()
        info = st._paths["/exp"]
        self.assertIsInstance(info, tuple)
        self.assertTrue(time2 < info[1] < time3)

    def test_storage_manual(self):
        # Add one redirect
        st = RedirectionStorage()
        st.add("/foo", "/bar")
        # Check the internals: we now store manual True/False (and a date).
        info = st._paths["/foo"]
        self.assertIsInstance(info, tuple)
        self.assertIsInstance(info[2], bool)
        self.assertFalse(info[2])
        # Store a manual one.
        st.add("/exp", "/bar", manual=True)
        info = st._paths["/exp"]
        self.assertIsInstance(info, tuple)
        self.assertIsInstance(info[2], bool)
        self.assertTrue(info[2])
        # Update to non-manual (the default).
        st.add("/exp", "/bar")
        info = st._paths["/exp"]
        self.assertIsInstance(info, tuple)
        self.assertIsInstance(info[2], bool)
        self.assertFalse(info[2])
        # Make the original non-manual one manual.
        st.add("/foo", "/bar", manual=True)
        # Check the internals: we now store manual True/False (and a date).
        info = st._paths["/foo"]
        self.assertIsInstance(info, tuple)
        self.assertIsInstance(info[2], bool)
        self.assertTrue(info[2])

    def test_storage_two_redirects_plain(self):
        # Add multiple redirects.
        st = RedirectionStorage()
        st.add("/foo", "/bar")
        st.add("/baz", "/bar")
        self.assertTrue(st.has_path("/baz"))
        self.assertEqual(st.get("/baz"), "/bar")
        self.assertListEqual(sorted(st.redirects("/bar")), ["/baz", "/foo"])
        self.assertIn("/foo", st)
        self.assertIn("/baz", st)
        self.assertNotIn("/bar", st)

    def test_storage_two_redirects_pythonic(self):
        # Add multiple redirects.
        st = RedirectionStorage()
        st["/foo"] = "/bar"
        st["/baz"] = "/bar"
        self.assertTrue(st.has_path("/baz"))
        self.assertEqual(st.get("/baz"), "/bar")
        self.assertListEqual(sorted(st.redirects("/bar")), ["/baz", "/foo"])
        self.assertIn("/foo", st)
        self.assertIn("/baz", st)
        self.assertNotIn("/bar", st)

    def test_storage_clear(self):
        # Clear all information.
        st = RedirectionStorage()
        st["/foo"] = "/bar"
        st["/baz"] = "/bar"
        st.clear()
        self.assertNotIn("/foo", st)
        self.assertNotIn("/baz", st)
        self.assertEqual(len(st.redirects("/bar")), 0)
        # Test the internal structures directly
        self.assertEqual(len(st._paths), 0)
        self.assertEqual(len(st._rpaths), 0)

    def test_storage_update_redirect(self):
        # Update a redirect
        st = RedirectionStorage()
        st.add("/foo", "/bar")
        st.add("/baz", "/bar")
        st.add("/foo", "/quux")
        self.assertTrue(st.has_path("/foo"))
        self.assertEqual(st.get("/foo"), "/quux")
        self.assertListEqual(st.redirects("/bar"), ["/baz"])
        self.assertListEqual(st.redirects("/quux"), ["/foo"])
        self.assertIn("/foo", st)

    def test_storage_remove_redirect_plain(self):
        # Remove a redirect
        st = RedirectionStorage()
        st.add("/foo", "/bar")
        st.remove("/foo")
        self.assertFalse(st.has_path("/foo"))
        self.assertEqual(st.get("/foo", default="_notfound_"), "_notfound_")
        self.assertListEqual(st.redirects("/bar"), [])
        self.assertNotIn("/foo", st)
        with self.assertRaises(KeyError):
            st.remove("/foo")

    def test_storage_remove_redirect_pythonic(self):
        # Remove a redirect
        st = RedirectionStorage()
        st["/foo"] = "/bar"
        self.assertIn("/foo", st)
        del st["/foo"]
        self.assertNotIn("/foo", st)
        with self.assertRaises(KeyError):
            st["/foo"]
        self.assertListEqual(st.redirects("/bar"), [])

        # test with extra slash
        st["/foo"] = "/bar"
        self.assertIn("/foo", st)
        del st["/foo/"]
        self.assertNotIn("/foo", st)
        with self.assertRaises(KeyError):
            st["/foo/"]
        self.assertListEqual(st.redirects("/bar"), [])

    def test_storage_chain(self):
        # Update a redirect in a chain
        st = RedirectionStorage()
        st.add("/fred", "/foo")
        self.assertEqual(st.get("/fred"), "/foo")
        self.assertListEqual(sorted(st.redirects("/foo")), ["/fred"])

        st.add("/fred", "/barney")
        self.assertEqual(st.get("/fred"), "/barney")
        self.assertListEqual(sorted(st.redirects("/foo")), [])
        self.assertListEqual(sorted(st.redirects("/barney")), ["/fred"])

        st.add("/barney", "/wilma")
        self.assertEqual(st.get("/fred"), "/wilma")
        self.assertEqual(st.get("/barney"), "/wilma")
        self.assertListEqual(sorted(st.redirects("/wilma")), ["/barney", "/fred"])
        self.assertListEqual(sorted(st.redirects("/barney")), [])
        self.assertIn("/fred", st)
        self.assertIn("/barney", st)

    def test_storage_destroy_target(self):
        # Destroy the target of a redirect
        st = RedirectionStorage()
        st.add("/fred", "/barney")
        st.add("/barney", "/wilma")
        st.destroy("/wilma")
        self.assertFalse(st.has_path("/barney"))
        self.assertFalse(st.has_path("/fred"))
        self.assertListEqual(st.redirects("/wilma"), [])
        self.assertNotIn("/fred", st)
        self.assertNotIn("/barney", st)

    def test_storage_iterator(self):
        # We can get an iterator over all existing paths
        st = RedirectionStorage()
        self.assertListEqual(sorted(iter(st)), [])

        # Add one
        st.add("/baz", "/bar")
        self.assertListEqual(sorted(iter(st)), ["/baz"])

        # Now add some more
        st.add("/foo", "/bar")
        st.add("/barney", "/wilma")
        self.assertListEqual(sorted(st), ["/barney", "/baz", "/foo"])

    def test_storage_len(self):
        # We can get the length of the storage (number of old paths).
        st = RedirectionStorage()
        self.assertEqual(len(st), 0)

        # Add one
        st["/baz"] = "/bar"
        self.assertEqual(len(st), 1)

        # Now add some more
        st["/foo"] = "/bar"
        st["/barney"] = "/wilma"
        self.assertEqual(len(st), 3)

    def test_storage_no_circular(self):
        # Circular references are ignored
        st = RedirectionStorage()
        st.add("/circle", "/circle")
        self.assertFalse(st.has_path("/circle"))
        self.assertEqual(st.get("/circle", "_marker_"), "_marker_")
        self.assertListEqual(st.redirects("/circle"), [])
        self.assertNotIn("/circle", st)

    def test_storage_three_step_circular_rename(self):
        # What about three step circular rename ?
        st = RedirectionStorage()

        # Add first redirect.
        st.add("first", "second")

        # There is only one redirect.

        self.assertEqual(st.get("first"), "second")
        self.assertIsNone(st.get("second"))
        self.assertIsNone(st.get("third"))

        # There is one back reference.

        self.assertListEqual(st.redirects("first"), [])
        self.assertListEqual(st.redirects("second"), ["first"])
        self.assertListEqual(st.redirects("third"), [])

        # Add second redirect.
        st.add("second", "third")

        # There are now two.

        self.assertEqual(st.get("first"), "third")
        self.assertEqual(st.get("second"), "third")
        self.assertIsNone(st.get("third"))

        # There are two back references as well.
        self.assertListEqual(st.redirects("first"), [])
        self.assertListEqual(st.redirects("second"), [])
        self.assertListEqual(st.redirects("third"), ["first", "second"])

        # Add third redirect, CIRCULAR.
        st.add("third", "first")

        # There are still only two redirects.
        self.assertIsNone(st.get("first"))
        self.assertEqual(st.get("second"), "first")
        self.assertEqual(st.get("third"), "first")
        self.assertNotIn("first", st)
        self.assertIn("second", st)
        self.assertIn("third", st)

        # And same for the back references.
        self.assertListEqual(st.redirects("first"), ["second", "third"])
        self.assertListEqual(st.redirects("second"), [])
        self.assertListEqual(st.redirects("third"), [])

    def test_storage_non_string_path_fails(self):
        st = RedirectionStorage()
        with self.assertRaises(AttributeError):
            st[0] = "/bar"
        with self.assertRaises(AttributeError):
            st["/foo"] = 0

    def test_storage_update_paths(self):
        st = RedirectionStorage()
        info = {}
        time1 = DateTime()
        for i in range(10):
            info[f"/old/{i}"] = f"/new/{i}"
        st.update(info)
        time2 = DateTime()
        self.assertEqual(len(st), 10)
        self.assertEqual(st.get("/old/0"), "/new/0")
        self.assertEqual(st.get("/old/1"), "/new/1")
        self.assertTrue(time1 < st.get_full("/old/0")[1] < time2)
        self.assertTrue(st.get_full("/old/0")[2])

    def test_storage_update_tuple(self):
        st = RedirectionStorage()
        info = {}
        for i in range(10):
            info[f"/old/{i}"] = (
                f"/new/{i}",
                DateTime(),
                False,
            )
        st.update(info)
        self.assertEqual(st.get("/old/0"), "/new/0")
        self.assertEqual(st.get("/old/1"), "/new/1")
        self.assertEqual(st.get_full("/old/0"), info["/old/0"])

    def test_storage_update_keeps_info(self):
        st = RedirectionStorage()
        info = {}
        time1 = DateTime()
        time2 = DateTime()
        info["/old/1"] = ("/new", time1, False)
        info["/old/2"] = ("/new", time2, True)
        st.update(info)
        self.assertEqual(len(st), 2)
        self.assertEqual(st.get("/old/1"), "/new")
        self.assertEqual(st.get("/old/2"), "/new")
        self.assertListEqual(sorted(st.redirects("/new")), ["/old/1", "/old/2"])
        self.assertEqual(st.get_full("/old/1"), info["/old/1"])
        self.assertEqual(st.get_full("/old/2"), info["/old/2"])
        # New info
        del info["/old/1"]
        time3 = DateTime()
        info["/old/2"] = ("/new/2", time2, False)
        info["/old/3"] = ("/new", time3, True)
        st.update(info)
        self.assertEqual(len(st), 3)
        self.assertEqual(st.get("/old/1"), "/new")
        self.assertEqual(st.get("/old/2"), "/new/2")
        self.assertEqual(st.get("/old/3"), "/new")
        self.assertListEqual(sorted(st.redirects("/new")), ["/old/1", "/old/3"])
        self.assertListEqual(sorted(st.redirects("/new/2")), ["/old/2"])
        self.assertEqual(st.get_full("/old/2"), info["/old/2"])
        self.assertEqual(st.get_full("/old/3"), info["/old/3"])

    def test_storage_update_mixed(self):
        st = RedirectionStorage()
        info = {}
        time1 = DateTime()
        for i in range(10):
            info[f"/old/{i}"] = f"/new/{i}"
        for i in range(10, 20):
            info[f"/old/{i}"] = (
                f"/new/{i}",
                DateTime(),
                False,
            )
        for i in range(20, 30):
            info[f"/old/{i}"] = (f"/new/{i}", None, True)
        st.update(info)
        time2 = DateTime()
        self.assertEqual(len(st), 30)
        self.assertEqual(st.get("/old/0"), "/new/0")
        self.assertEqual(st.get("/old/1"), "/new/1")
        self.assertTrue(time1 < st.get_full("/old/0")[1] < time2)
        self.assertTrue(st.get_full("/old/0")[2])
        self.assertEqual(st.get("/old/10"), "/new/10")
        self.assertEqual(st.get("/old/11"), "/new/11")
        self.assertEqual(st.get_full("/old/10"), info["/old/10"])
        self.assertEqual(st.get("/old/20"), "/new/20")
        self.assertEqual(st.get("/old/21"), "/new/21")
        self.assertTrue(time1 < st.get_full("/old/20")[1] < time2)
        self.assertTrue(st.get_full("/old/20")[2])
        # Update again with the same info.
        # This may set new dates.
        st.update(info)
        time3 = DateTime()
        self.assertEqual(len(st), 30)
        self.assertEqual(st.get("/old/0"), "/new/0")
        self.assertTrue(time2 < st.get_full("/old/0")[1] < time3)
        self.assertTrue(st.get_full("/old/0")[2])
        self.assertEqual(st.get("/old/10"), "/new/10")
        self.assertEqual(st.get_full("/old/10"), info["/old/10"])
        self.assertEqual(st.get("/old/20"), "/new/20")
        self.assertTrue(time2 < st.get_full("/old/20")[1] < time3)
        self.assertTrue(st.get_full("/old/20")[2])

    def test_rebuild(self):
        # Rebuild the internal information.
        # This is mostly meant to be used in migration
        # to initialize the date and manual information.
        st = RedirectionStorage()
        # Should run fine on an empty storage.
        st._rebuild()
        # Set internals directly.
        st._paths["/old"] = "/new"
        st._paths["/older"] = "/new"
        st._paths["/first"] = "/second"
        st._rpaths["/unused"] = "/unknown"
        # Add some bad redirects, which should have been updated to point to /new.
        st._paths["/bad"] = "/old"
        st._paths["/worse"] = "/old"
        st._paths["/worst"] = "/worse"
        self.assertIsInstance(st._paths["/old"], str)
        self.assertEqual(st._paths["/old"], "/new")
        self.assertEqual(len(st._paths), 6)
        self.assertEqual(len(st._rpaths), 1)

        # Rebuild
        time1 = DateTime()
        st._rebuild()
        time2 = DateTime()
        # The _paths should be tuples now.
        self.assertEqual(
            sorted(list(st._paths)),
            ["/bad", "/first", "/old", "/older", "/worse", "/worst"],
        )
        info = st._paths["/old"]
        self.assertIsInstance(info, tuple)
        # The good ones were pointing to /new or /second, which should stay the same,
        # but the bad ones have been updated to point to new as well.
        self.assertSetEqual(
            {path[0] for path in st._paths.values()},
            {"/new", "/second"},
        )
        # Date should be set to the same for all.
        self.assertIsInstance(info[1], DateTime)
        new_time = info[1]
        self.assertTrue(time1 < new_time < time2)
        self.assertSetEqual({path[1] for path in st._paths.values()}, {new_time})
        # manual is set to True when migrating to tuples:
        self.assertEqual(info[2], True)
        # _rpaths should be filled now with only the new one.
        self.assertEqual(len(st._rpaths), 2)
        self.assertNotIn("/unused", st._rpaths)
        self.assertEqual(sorted(list(st._rpaths["/second"])), ["/first"])
        self.assertEqual(
            sorted(list(st._rpaths["/new"])),
            ["/bad", "/old", "/older", "/worse", "/worst"],
        )

        # Rebuild again.  Nothing fundamentally should have changed,
        # except that _rpaths have been recreated.
        old_paths = st._paths
        old_rpaths = st._rpaths
        st._rebuild()
        self.assertIs(old_paths, st._paths)
        self.assertIsNot(old_rpaths, st._rpaths)
        self.assertListEqual(sorted(list(old_rpaths)), sorted(list(st._rpaths)))
        self.assertSetEqual(
            {path[0] for path in st._paths.values()},
            {"/new", "/second"},
        )
        self.assertSetEqual({path[1] for path in st._paths.values()}, {new_time})
        self.assertSetEqual({path[2] for path in st._paths.values()}, {True})
