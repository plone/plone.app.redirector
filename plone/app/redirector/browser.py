from urllib import unquote

from zope.interface import implements
from zope.component import queryUtility, getMultiAdapter

from Acquisition import aq_inner
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName
from Products.ZCTextIndex.ParseTree import QueryError, ParseError

from plone.app.redirector.interfaces import IFourOhFourView
from plone.app.redirector.interfaces import IRedirectionStorage
from plone.app.redirector.interfaces import IRedirectionPolicy

from plone.memoize.instance import memoize

import logging

logger = logging.getLogger('plone.app.redirector')


class FourOhFourView(BrowserView):
    implements(IFourOhFourView)

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

        old_path = '/'.join(old_path_elements)
        new_path = storage.get(old_path)

        if not new_path:

            # If the last part of the URL was a template name, say, look for
            # the parent

            if len(old_path_elements) > 1:
                old_path_parent = '/'.join(old_path_elements[:-1])
                template_id = unquote(url.split('/')[-1])
                new_path_parent = storage.get(old_path_parent)
                if new_path_parent == old_path_parent:
                    logger.warning("source and target are equal : [%s]"
                         % new_path_parent)
                    logger.warning("for more info, see "
                        "https://dev.plone.org/plone/ticket/8840")
                if new_path_parent and new_path_parent <> old_path_parent:
                    new_path = new_path_parent + '/' + template_id

        if not new_path:
            return False

        url = self.request.physicalPathToURL(new_path)
        self.request.response.redirect(url, status=301, lock=1)
        return True

    def find_first_parent(self):
        path_elements = self._path_elements()
        if not path_elements:
            return None
        portal_state = getMultiAdapter((aq_inner(self.context), self.request),
             name='plone_portal_state')
        portal = portal_state.portal()
        for i in range(len(path_elements)-1, 0, -1):
            obj = portal.restrictedTraverse('/'.join(path_elements[:i]), None)
            if obj is not None:
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
        portal_state = getMultiAdapter((aq_inner(self.context), self.request),
             name='plone_portal_state')
        navroot = portal_state.navigation_root_path()
        for element in path_elements:
            # Prevent parens being interpreted
            element=element.replace('(', '"("')
            element=element.replace(')', '")"')
            if element not in ignore_ids:
                try:
                    result_set = portal_catalog(SearchableText=element,
                        path = navroot,
                        portal_type=portal_state.friendly_types(),
                        sort_limit=10)
                    if result_set:
                        return result_set[:10]
                except (QueryError, ParseError):
                    # ignore if the element can't be parsed as a text query
                    pass
        return []

    @memoize
    def _url(self):
        """Get the current, canonical URL
        """
        return self.request.get('ACTUAL_URL',
                 self.request.get('VIRTUAL_URL',
                   self.request.get('URL',
                     None)))

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
            path = '/'.join(self.request.physicalPathFromURL(url))
        except ValueError:
            return None

        portal_state = getMultiAdapter((aq_inner(self.context), self.request),
            name='plone_portal_state')
        portal_path = '/'.join(portal_state.portal().getPhysicalPath())
        if not path.startswith(portal_path):
            return None

        return path.split('/')
