import unittest
from Testing.ZopeTestCase import FunctionalDocFileSuite as Suite
from plone.app.redirector.tests.base import RedirectorTestCase

from zope.component import getMultiAdapter

class TestRedirectorView(RedirectorTestCase):
    """Ensure that the redirector view behaves as expected.
    """
    
    def _view(self, context, url):
        pass

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestRedirectorView))
    return suite
