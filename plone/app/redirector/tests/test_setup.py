import unittest
from plone.app.redirector.tests.base import RedirectorTestCase

from zope.component import queryUtility

from plone.app.redirector.interfaces import IRedirectionStorage

class TestRedirectorSetup(RedirectorTestCase):
    """Ensure that the basic redirector setup is successful.
    """

    def test_utility(self):
        utility = queryUtility(IRedirectionStorage)
        self.assertNotEquals(None, utility)

    def test_view(self):
        view = self.portal.restrictedTraverse('@@plone_redirector_view')
        self.assertNotEquals(None, view)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestRedirectorSetup))
    return suite
