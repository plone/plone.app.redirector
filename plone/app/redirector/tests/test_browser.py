from plone.app.redirector.interfaces import IRedirectionStorage
from plone.app.redirector.testing import PLONE_APP_REDIRECTOR_FUNCTIONAL_TESTING
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.testing.z2 import Browser
from zope.component import getUtility

import unittest


class TestBrowser(unittest.TestCase):
    """Test no redirection entries when instantiating object.

    This test checks https://dev.plone.org/plone/ticket/8260,
    i.e. it makes sure no redirection entries are created when
    a content object gets instantiated:

    This used to be in browser.txt.
    """

    layer = PLONE_APP_REDIRECTOR_FUNCTIONAL_TESTING

    def setUp(self):
        app = self.layer["app"]
        self.browser = Browser(app)
        self.browser.handleErrors = False
        self.browser.addHeader(
            "Authorization",
            f"Basic {SITE_OWNER_NAME}:{SITE_OWNER_PASSWORD}",
        )
        portal = self.layer["portal"]
        self.portal_url = portal.absolute_url()

    def test_no_redirect_on_creation(self):
        storage = getUtility(IRedirectionStorage)
        # Initially the redirection storage should be empty:
        self.assertListEqual(list(storage), [])

        # Let's create an object and check again:
        self.browser.open(self.portal_url)
        self.browser.getLink(url="++add++Document").click()
        self.browser.getControl(name="form.widgets.IDublinCore.title").value = "Foo"
        self.browser.getControl("Save").click()
        self.assertIn("Item created", self.browser.contents)
        self.assertListEqual(list(storage), [])

        # However, if this object is renamed in a normal manner,
        # an entry should be created, of course:
        self.browser.getLink("Rename").click()
        self.browser.getControl("New Short Name").value = "bar"
        self.browser.getControl("New Title").value = "Bar"
        self.browser.getControl("Rename").click()
        self.assertListEqual(list(storage), ["/plone/foo"])
        self.assertEqual(storage.get("/plone/foo"), "/plone/bar")
