from plone.app.redirector.interfaces import IRedirectionStorage
from plone.app.redirector.testing import PLONE_APP_REDIRECTOR_INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getUtility

import transaction
import unittest


class TestRedirectorEvents(unittest.TestCase):
    """Ensure that the redirector event subscribers behave as expected."""

    layer = PLONE_APP_REDIRECTOR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.portal.invokeFactory("Folder", "folder")
        self.folder = self.portal.folder

    @property
    def storage(self):
        return getUtility(IRedirectionStorage)

    def test_rename_updates_storage(self):
        self.folder.invokeFactory("Document", "p1")
        transaction.savepoint(1)
        self.folder.manage_renameObject("p1", "p2")

        fp = "/".join(self.folder.getPhysicalPath())
        self.assertEqual(self.storage.get(fp + "/p1"), fp + "/p2")

    def test_cut_paste_updates_storage(self):
        self.folder.invokeFactory("Folder", "f1")
        self.folder.invokeFactory("Document", "p1")
        self.folder.invokeFactory("Document", "p2")
        transaction.savepoint(1)
        cp = self.folder.manage_cutObjects(ids=("p1", "p2"))
        self.folder.f1.manage_pasteObjects(cp)

        fp = "/".join(self.folder.getPhysicalPath())
        self.assertEqual(self.storage.get(fp + "/p1"), fp + "/f1/p1")
        self.assertEqual(self.storage.get(fp + "/p2"), fp + "/f1/p2")

    def test_cut_paste_rename_updates_storage(self):
        self.folder.invokeFactory("Folder", "f1")
        self.folder.invokeFactory("Document", "p1")
        self.folder.invokeFactory("Document", "p2")
        transaction.savepoint(1)
        cp = self.folder.manage_cutObjects(ids=("p1", "p2"))
        self.folder.f1.manage_pasteObjects(cp)
        transaction.savepoint(1)
        self.folder.f1.manage_renameObject("p2", "p3")

        fp = "/".join(self.folder.getPhysicalPath())
        self.assertEqual(self.storage.get(fp + "/p1"), fp + "/f1/p1")
        self.assertEqual(self.storage.get(fp + "/p2"), fp + "/f1/p3")
        self.assertEqual(self.storage.get(fp + "/f1/p2"), fp + "/f1/p3")

    def test_delete_destroys_reference(self):
        self.folder.invokeFactory("Document", "p1")
        transaction.savepoint(1)
        self.folder.manage_renameObject("p1", "p2")
        transaction.savepoint(1)

        fp = "/".join(self.folder.getPhysicalPath())
        self.assertEqual(self.storage.get(fp + "/p1"), fp + "/p2")

        self.folder._delObject("p2")

        self.assertEqual(self.storage.get(fp + "/p1"), None)

    def test_delete_destroys_child_reference(self):
        self.folder.invokeFactory("Folder", "f1")
        self.folder.f1.invokeFactory("Document", "p1")
        transaction.savepoint(1)
        self.folder.f1.manage_renameObject("p1", "p2")
        transaction.savepoint(1)

        fp = "/".join(self.folder.getPhysicalPath())
        self.assertEqual(self.storage.get(fp + "/f1/p1"), fp + "/f1/p2")

        self.folder._delObject("f1")

        self.assertEqual(self.storage.get(fp + "/f1/p1"), None)

    def test_rename_updates_parent_and_children(self):
        self.folder.invokeFactory("Folder", "f1")
        self.folder.f1.invokeFactory("Document", "p1")
        self.folder.f1.invokeFactory("Document", "p2")
        transaction.savepoint(1)
        self.folder.manage_renameObject("f1", "f2")

        fp = "/".join(self.folder.getPhysicalPath())
        self.assertEqual(self.storage.get(fp + "/f1"), fp + "/f2")
        self.assertEqual(self.storage.get(fp + "/f1/p1"), fp + "/f2/p1")
        self.assertEqual(self.storage.get(fp + "/f1/p2"), fp + "/f2/p2")

    def test_cut_paste_updates_parent_and_children(self):
        self.folder.invokeFactory("Folder", "f1")
        self.folder.invokeFactory("Folder", "f2")
        self.folder.f1.invokeFactory("Document", "p1")
        self.folder.f1.invokeFactory("Document", "p2")
        transaction.savepoint(1)
        cp = self.folder.manage_cutObjects(ids=("f1",))
        self.folder.f2.manage_pasteObjects(cp)

        fp = "/".join(self.folder.getPhysicalPath())
        self.assertEqual(self.storage.get(fp + "/f1"), fp + "/f2/f1")
        self.assertEqual(self.storage.get(fp + "/f1/p1"), fp + "/f2/f1/p1")
        self.assertEqual(self.storage.get(fp + "/f1/p2"), fp + "/f2/f1/p2")

    def test_rename_updates_parent_and_children_deep(self):
        self.folder.invokeFactory("Folder", "f1")
        self.folder.f1.invokeFactory("Folder", "f11")
        self.folder.f1.f11.invokeFactory("Document", "p1")
        self.folder.f1.f11.invokeFactory("Document", "p2")
        transaction.savepoint(1)
        self.folder.manage_renameObject("f1", "f2a")

        fp = "/".join(self.folder.getPhysicalPath())
        self.assertEqual(self.storage.get(fp + "/f1"), fp + "/f2a")
        self.assertEqual(self.storage.get(fp + "/f1/f11"), fp + "/f2a/f11")
        self.assertEqual(self.storage.get(fp + "/f1/f11/p1"), fp + "/f2a/f11/p1")
        self.assertEqual(self.storage.get(fp + "/f1/f11/p2"), fp + "/f2a/f11/p2")

    def test_cut_paste_updates_parent_and_children_deep(self):
        self.folder.invokeFactory("Folder", "f1")
        self.folder.invokeFactory("Folder", "f2a")
        self.folder.f1.invokeFactory("Folder", "f11")
        self.folder.f1.f11.invokeFactory("Document", "p1")
        self.folder.f1.f11.invokeFactory("Document", "p2")
        transaction.savepoint(1)
        cp = self.folder.manage_cutObjects(ids=("f1",))
        self.folder.f2a.manage_pasteObjects(cp)

        fp = "/".join(self.folder.getPhysicalPath())
        self.assertEqual(self.storage.get(fp + "/f1"), fp + "/f2a/f1")
        self.assertEqual(self.storage.get(fp + "/f1/f11"), fp + "/f2a/f1/f11")
        self.assertEqual(self.storage.get(fp + "/f1/f11/p1"), fp + "/f2a/f1/f11/p1")
        self.assertEqual(self.storage.get(fp + "/f1/f11/p2"), fp + "/f2a/f1/f11/p2")

    def test_add_doesnt_create_storage_entry(self):
        """refers https://dev.plone.org/plone/ticket/8260"""
        orig_len = len(list(self.storage))
        self.folder.invokeFactory("Document", "p1")
        transaction.savepoint(1)
        self.assertEqual(0, len(list(self.storage)) - orig_len)
