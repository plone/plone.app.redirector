from plone.app.redirector.interfaces import IRedirectionStorage
from plone.app.redirector.testing import PLONE_APP_REDIRECTOR_INTEGRATION_TESTING
from zope.component import queryUtility

import unittest


class TestRedirectorSetup(unittest.TestCase):
    """Ensure that the basic redirector setup is successful."""

    layer = PLONE_APP_REDIRECTOR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]

    def test_utility(self):
        utility = queryUtility(IRedirectionStorage)
        self.assertNotEqual(None, utility)

    def test_view(self):
        view = self.portal.restrictedTraverse("@@plone_redirector_view")
        self.assertNotEqual(None, view)
