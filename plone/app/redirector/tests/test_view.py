import unittest
from Testing.ZopeTestCase import FunctionalDocFileSuite as Suite
from plone.app.redirector.tests.base import RedirectorTestCase

from zope.component import getUtility, getMultiAdapter
from plone.app.redirector.interfaces import IRedirectionStorage

class TestRedirectorView(RedirectorTestCase):
    """Ensure that the redirector view behaves as expected.
    """
    
    @property
    def storage(self):
        return getUtility(IRedirectionStorage)
    
    def view(self, context, actual_url):
        request = context.REQUEST
        request['ACTUAL_URL'] = actual_url
        return getMultiAdapter((context, request), name='plone_redirector_view')
        
    def test_attempt_redirect_with_known_url(self):
        pass
        
    def test_attempt_redirect_with_unknown_url(self):
        pass
        
    def test_attempt_redirect_unauthorized(self):
        pass
        
    def test_find_first_parent_found(self):
        pass
        
    def test_find_first_parent_not_found(self):
        pass
        
    def test_search_leaf(self):
        pass
        
    def test_search_node(self):
        pass

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestRedirectorView))
    return suite
