from Acquisition import aq_base
from Acquisition import aq_inner
from plone.app.redirector.interfaces import IFourOhFourView
from plone.app.redirector.interfaces import IRedirectionPolicy
from plone.app.redirector.interfaces import IRedirectionStorage
from plone.memoize.instance import memoize
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.ZCTextIndex.ParseTree import ParseError
from Products.ZCTextIndex.ParseTree import QueryError
from urllib.parse import quote
from urllib.parse import SplitResult
from urllib.parse import unquote
from urllib.parse import urlsplit
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.interface import implementer

import logging


logger = logging.getLogger("plone.app.redirector")


@implementer(IFourOhFourView)
class FourOhFourView(BrowserView):
    def attempt_redirect(self):
        url = self._url()
        if not url:
            return False

        try:
            old_path_elements = self.request.physicalPathFromURL(url)
        except ValueError:
            return False

        storage = queryUtility(IRedirectionStorage)
        if storage is None:
            return False

        old_path = "/".join(old_path_elements)

        # First lets try with query string in cases or content migration

        new_path = None

        query_string = self.request.QUERY_STRING
        if query_string:
            new_path = storage.get(f"{old_path}?{query_string}")
            # if we matched on the query_string we don't want to include it
            # in redirect
            if new_path:
                query_string = ""

        if not new_path:
            new_path = storage.get(old_path)

        if not new_path:
            new_path = self.find_redirect_if_view(old_path_elements, storage)

        if not new_path:
            new_path = self.find_redirect_if_template(url, old_path_elements, storage)

        if not new_path:
            return False

        url = urlsplit(new_path)
        if url.netloc:
            # External URL
            # avoid double quoting
            url_path = unquote(url.path)
            url_path = quote(url_path)
            url = SplitResult(*(url[:2] + (url_path,) + url[3:])).geturl()
        else:
            url = self.request.physicalPathToURL(new_path)

        # some analytics programs might use this info to track
        if query_string:
            url += "?" + query_string

        # Answer GET requests with 302 (Found). Every other method will be answered
        # with 307 (Temporary Redirect), which instructs the client to NOT
        # switch the method (if the original request was a POST, it should
        # re-POST to the new URL from the Location header).
        if self.request.method.upper() == "GET":
            status = 302
        else:
            status = 307

        self.request.response.redirect(url, status=status, lock=1)
        return True

    def find_redirect_if_view(self, old_path_elements, storage):
        """find redirect for urls like http://example.com/object/@@view/part."""
        if len(old_path_elements) <= 1:
            return None

        object_id_hiearchy = []
        view_parts = []
        for element in old_path_elements:
            if element.startswith("@@") or view_parts:
                view_parts.append(element)
            else:
                object_id_hiearchy.append(element)
        if not view_parts:
            return None

        old_path_parent = "/".join(object_id_hiearchy)
        new_path_parent = storage.get(old_path_parent)
        if not new_path_parent or (new_path_parent == old_path_parent):
            return None

        return new_path_parent + "/" + "/".join(view_parts)

    def find_redirect_if_template(self, url, old_path_elements, storage):
        if len(old_path_elements) <= 1:
            return None
        # If the last part of the URL was a template name, say, look for
        # the parent
        old_path_parent = "/".join(old_path_elements[:-1])
        template_id = unquote(url.split("/")[-1])
        new_path_parent = storage.get(old_path_parent)

        if new_path_parent == old_path_parent:
            logger.warning("source and target are equal : [%s]" % new_path_parent)
            logger.warning(
                "for more info, see " "http://dev.plone.org/plone/ticket/8840"
            )
        if not new_path_parent or (new_path_parent == old_path_parent):
            return None

        return new_path_parent + "/" + template_id

    def find_first_parent(self):
        path_elements = self._path_elements()
        if not path_elements:
            return None
        portal_state = getMultiAdapter(
            (aq_inner(self.context), self.request), name="plone_portal_state"
        )
        portal = portal_state.portal()
        for i in range(len(path_elements) - 1, 0, -1):
            obj = portal.restrictedTraverse("/".join(path_elements[:i]), None)
            if obj is not None:
                # Skin objects acquire portal_type from the Plone site
                if (
                    getattr(aq_base(obj), "portal_type", None)
                    in portal_state.friendly_types()
                ):
                    return obj
        return None

    def search_for_similar(self):
        path_elements = self._path_elements()
        if not path_elements:
            return None
        path_elements.reverse()
        policy = IRedirectionPolicy(self.context)
        ignore_ids = policy.ignore_ids
        portal_catalog = getToolByName(self.context, "portal_catalog")
        portal_state = getMultiAdapter(
            (aq_inner(self.context), self.request), name="plone_portal_state"
        )
        navroot = portal_state.navigation_root_path()
        for element in path_elements:
            # Prevent parens being interpreted
            element = element.replace("(", '"("')
            element = element.replace(")", '")"')
            if element not in ignore_ids:
                try:
                    result_set = portal_catalog(
                        SearchableText=element,
                        path=navroot,
                        portal_type=portal_state.friendly_types(),
                        sort_limit=10,
                    )
                    if result_set:
                        return result_set[:10]
                except (QueryError, ParseError):
                    # ignore if the element can't be parsed as a text query
                    pass
        return []

    @memoize
    def _url(self):
        """Get the current, canonical URL"""
        return self.request.get(
            "ACTUAL_URL", self.request.get("VIRTUAL_URL", self.request.get("URL", None))
        )

    @memoize
    def _path_elements(self):
        """Get the path to the object implied by the current URL, as a list
        of elements. Get None if it can't be calculated or it is not under
        the current portal path.
        """
        url = self._url()
        if not url:
            return None

        try:
            path = "/".join(self.request.physicalPathFromURL(url))
        except ValueError:
            return None

        portal_state = getMultiAdapter(
            (aq_inner(self.context), self.request), name="plone_portal_state"
        )
        portal_path = "/".join(portal_state.portal().getPhysicalPath())
        if not path.startswith(portal_path):
            return None

        return path.split("/")
