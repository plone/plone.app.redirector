import unittest
import transaction

from Testing.ZopeTestCase import FunctionalDocFileSuite as Suite
from plone.app.redirector.tests.base import RedirectorTestCase

from zope.component import getUtility

from plone.app.redirector.interfaces import IRedirectionStorage

class TestRedirectorEvents(RedirectorTestCase):
    """Ensure that the redirector view behaves as expected.
    """
        
    @property
    def storage(self):
        return getUtility(IRedirectionStorage)
        
    def test_rename_updates_storage(self):
        self.folder.invokeFactory('Document', 'p1')
        transaction.savepoint(1)
        self.folder.manage_renameObject('p1', 'p2')
        
        fp = '/'.join(self.folder.getPhysicalPath())
        self.assertEquals(self.storage.get(fp + '/p1'), fp + '/p2')

    def test_copy_paste_updates_storage(self):
        self.folder.invokeFactory('Folder', 'f1')
        self.folder.invokeFactory('Document', 'p1')
        self.folder.invokeFactory('Document', 'p2')
        transaction.savepoint(1)
        cp = self.folder.manage_cutObjects(ids=('p1', 'p2',))
        self.folder.f1.manage_pasteObjects(cp)
        
        fp = '/'.join(self.folder.getPhysicalPath())
        self.assertEquals(self.storage.get(fp + '/p1'), fp + '/f1/p1')
        self.assertEquals(self.storage.get(fp + '/p2'), fp + '/f1/p2')
        
    def test_copy_paste_rename_updates_storage(self):
        self.folder.invokeFactory('Folder', 'f1')
        self.folder.invokeFactory('Document', 'p1')
        self.folder.invokeFactory('Document', 'p2')
        transaction.savepoint(1)
        cp = self.folder.manage_cutObjects(ids=('p1', 'p2',))
        self.folder.f1.manage_pasteObjects(cp)
        transaction.savepoint(1)
        self.folder.f1.manage_renameObject('p2', 'p3')
        
        fp = '/'.join(self.folder.getPhysicalPath())
        self.assertEquals(self.storage.get(fp + '/p1'), fp + '/f1/p1')
        self.assertEquals(self.storage.get(fp + '/p2'), fp + '/f1/p3')
        self.assertEquals(self.storage.get(fp + '/f1/p2'), fp + '/f1/p3')
        
    def test_delete_destroys_reference(self):
        self.folder.invokeFactory('Document', 'p1')
        transaction.savepoint(1)
        self.folder.manage_renameObject('p1', 'p2')
        transaction.savepoint(1)
        
        fp = '/'.join(self.folder.getPhysicalPath())
        self.assertEquals(self.storage.get(fp + '/p1'), fp + '/p2')
        
        self.folder._delObject('p2')
        
        self.assertEquals(self.storage.get(fp + '/p1'), None)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestRedirectorEvents))
    return suite
