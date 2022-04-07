from plone.app.redirector.interfaces import IRedirectionStorage
from plone.app.redirector.testing import PLONE_APP_REDIRECTOR_INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces import ISearchSchema
from zope.component import getMultiAdapter
from zope.component import getUtility

import unittest


class TestRedirectorView(unittest.TestCase):
    """Ensure that the redirector view behaves as expected."""

    layer = PLONE_APP_REDIRECTOR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.portal.invokeFactory("Folder", "folder")
        self.folder = self.portal.folder
        self.storage = getUtility(IRedirectionStorage)

    def view(self, context, actual_url, query_string=""):
        self.request["ACTUAL_URL"] = actual_url
        self.request["QUERY_STRING"] = query_string
        return getMultiAdapter((context, self.request), name="plone_redirector_view")

    def test_attempt_redirect_with_known_url(self):
        fp = "/".join(self.folder.getPhysicalPath())
        fu = self.folder.absolute_url()
        self.storage.add(fp + "/foo", fp + "/bar")
        view = self.view(self.portal, fu + "/foo")
        self.assertEqual(True, view.attempt_redirect())
        self.assertEqual(302, self.request.response.getStatus())
        self.assertEqual(fu + "/bar", self.request.response.getHeader("location"))

    def test_attempt_redirect_with_known_url_and_template(self):
        fp = "/".join(self.folder.getPhysicalPath())
        fu = self.folder.absolute_url()
        self.storage.add(fp + "/foo", fp + "/bar")
        view = self.view(self.portal, fu + "/foo/view")
        self.assertEqual(True, view.attempt_redirect())
        self.assertEqual(302, self.request.response.getStatus())
        self.assertEqual(fu + "/bar/view", self.request.response.getHeader("location"))

    def test_attempt_redirect_with_known_url_and_view_with_part(self):
        fp = "/".join(self.folder.getPhysicalPath())
        fu = self.folder.absolute_url()
        self.storage.add(fp + "/foo", fp + "/bar")
        view = self.view(self.portal, fu + "/foo/@@view/part")
        self.assertEqual(True, view.attempt_redirect())
        self.assertEqual(302, self.request.response.getStatus())
        self.assertEqual(
            fu + "/bar/@@view/part", self.request.response.getHeader("location")
        )

    def test_attempt_redirect_with_unknown_url(self):
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + "/foo")
        self.assertEqual(False, view.attempt_redirect())
        self.assertNotEqual(302, self.request.response.getStatus())

    def test_attempt_redirect_with_unknown_url_with_illegal_characters(self):
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + "+LÃ¤nder")
        self.assertEqual(False, view.attempt_redirect())
        self.assertNotEqual(302, self.request.response.getStatus())

    def test_attempt_redirect_with_quoted_url(self):
        fp = "/".join(self.folder.getPhysicalPath())
        fu = self.folder.absolute_url()
        self.storage.add(fp + "/foo", fp + "/bar")
        view = self.view(self.portal, fu + "/foo/baz%20quux")
        self.assertEqual(True, view.attempt_redirect())
        self.assertEqual(302, self.request.response.getStatus())
        self.assertEqual(
            fu + "/bar/baz%20quux", self.request.response.getHeader("location")
        )

    def test_attempt_redirect_with_query_string(self):
        fp = "/".join(self.folder.getPhysicalPath())
        fu = self.folder.absolute_url()
        self.storage.add(fp + "/foo?blah=blah", fp + "/bar")
        view = self.view(self.portal, fu + "/foo", "blah=blah")
        self.assertEqual(True, view.attempt_redirect())
        self.assertEqual(302, self.request.response.getStatus())
        self.assertEqual(fu + "/bar", self.request.response.getHeader("location"))

    def test_attempt_redirect_appending_query_string(self):
        fp = "/".join(self.folder.getPhysicalPath())
        fu = self.folder.absolute_url()
        self.storage.add(fp + "/foo", fp + "/bar")
        view = self.view(self.portal, fu + "/foo", "blah=blah")
        self.assertEqual(True, view.attempt_redirect())
        self.assertEqual(302, self.request.response.getStatus())
        self.assertEqual(
            fu + "/bar?blah=blah", self.request.response.getHeader("location")
        )

    def test_attempt_redirect_with_external_url(self):
        fp = "/".join(self.folder.getPhysicalPath())
        fu = self.folder.absolute_url()
        self.storage.add(fp + "/foo", "http://otherhost" + fp + "/bar%20qux corge")
        view = self.view(self.portal, fu + "/foo")
        self.assertEqual(True, view.attempt_redirect())
        self.assertEqual(302, self.request.response.getStatus())
        self.assertEqual(
            "http://otherhost" + fp + "/bar%20qux%20corge",
            self.request.response.getHeader("location"),
        )

    def test_find_first_parent_found_leaf(self):
        self.folder.invokeFactory("Folder", "f1")
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + "/f1/p1")
        obj = view.find_first_parent()
        self.assertEqual(fu + "/f1", obj.absolute_url())

    def test_find_first_parent_found_node(self):
        self.folder.invokeFactory("Folder", "f1")
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + "/f1/p1/p2")
        obj = view.find_first_parent()
        self.assertEqual(fu + "/f1", obj.absolute_url())

    def test_find_first_parent_not_found(self):
        view = self.view(self.portal, "/foo/f1/p1/p2")
        self.assertEqual(None, view.find_first_parent())

    def test_find_first_parent_not_viewable(self):
        view = self.view(
            self.portal,
            self.portal.absolute_url() + "/portal_css/Plone Default/gone.css",
        )
        self.assertEqual(None, view.find_first_parent())

    def test_search_leaf(self):
        self.folder.invokeFactory("Folder", "f1")
        self.folder.invokeFactory("Folder", "f2")
        self.folder.f1.invokeFactory("Document", "p1")
        self.folder.f1.invokeFactory("Document", "p2")
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + "/f2/p1")
        urls = sorted(b.getURL() for b in view.search_for_similar())
        self.assertEqual(1, len(urls))
        self.assertEqual(fu + "/f1/p1", urls[0])

    def test_search_ignore_ids(self):
        self.folder.invokeFactory("Folder", "f1")
        self.folder.invokeFactory("Folder", "f2")
        self.folder.f1.invokeFactory("Document", "p1")
        self.folder.f1.invokeFactory("Document", "p2")
        self.folder.f1.invokeFactory("Document", "p3", title="view")
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + "/f2/p1/view")
        urls = sorted(b.getURL() for b in view.search_for_similar())
        self.assertEqual(1, len(urls))
        self.assertEqual(fu + "/f1/p1", urls[0])

    def test_search_node(self):
        self.folder.invokeFactory("Folder", "f1")
        self.folder.invokeFactory("Folder", "f2")
        self.folder.f1.invokeFactory("Document", "p1")
        self.folder.f1.invokeFactory("Document", "p2")
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + "/f2/p1/f3")
        urls = sorted(b.getURL() for b in view.search_for_similar())
        self.assertEqual(1, len(urls))
        self.assertEqual(fu + "/f1/p1", urls[0])

    def test_search_parens(self):
        self.folder.invokeFactory("Folder", "f1")
        self.folder.invokeFactory("Folder", "f2")
        self.folder.f1.invokeFactory("Document", "p1")
        self.folder.f1.invokeFactory("Document", "p2")
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + "/f2/p1/f3(")
        urls = sorted(b.getURL() for b in view.search_for_similar())
        self.assertEqual(1, len(urls))
        self.assertEqual(fu + "/f1/p1", urls[0])

    def test_search_query_parser_error(self):
        view = self.view(self.portal, self.portal.absolute_url() + "/&")
        try:
            urls = view.search_for_similar()
        except:
            self.fail("Query parsing error was not handled.")

    def test_search_blacklisted(self):
        self.folder.invokeFactory("Folder", "f1")
        self.folder.invokeFactory("Folder", "f2")
        self.folder.f1.invokeFactory("Document", "p1")
        self.folder.f1.invokeFactory("Document", "p2")
        fu = self.folder.absolute_url()
        registry = getUtility(IRegistry)
        settings = registry.forInterface(ISearchSchema, prefix="plone")
        settings.types_not_searched = ("Document",)
        view = self.view(self.portal, fu + "/f2/p1")
        urls = sorted(b.getURL() for b in view.search_for_similar())
        self.assertEqual(1, len(urls))
        self.assertEqual(fu + "/f2", urls[0])
