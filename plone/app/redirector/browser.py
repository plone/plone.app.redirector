#python
import csv
import logging
from urllib import unquote
from cStringIO import StringIO

#zope3
from zope import interface
from zope import component
from zope.i18nmessageid import MessageFactory
from zope.formlib.form import setUpWidgets, FormFields

#zope2
from Acquisition import aq_inner
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.ZCTextIndex.ParseTree import QueryError, ParseError
from Products.statusmessages.interfaces import IStatusMessage

#plone
from plone.memoize.instance import memoize

from plone.app.redirector.interfaces import IFourOhFourView
from plone.app.redirector.interfaces import IRedirectionStorage
from plone.app.redirector.interfaces import IRedirectionPolicy

logger = logging.getLogger('plone.app.redirector')
_ = MessageFactory('plone')


class FourOhFourView(BrowserView):
    interface.implements(IFourOhFourView)

    def attempt_redirect(self):
        url = self._url()
        if not url:
            return False

        try:
            old_path_elements = self.request.physicalPathFromURL(url)
        except ValueError:
            return False

        storage = component.queryUtility(IRedirectionStorage)
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
        portal_state = self.portal_state
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
        portal_state = self.portal_state
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

        portal_state = self.portal_state
        portal_path = '/'.join(portal_state.portal().getPhysicalPath())
        if not path.startswith(portal_path):
            return None

        return path.split('/')

    @property
    def portal_state(self):
        return component.getMultiAdapter((aq_inner(self.context),
                                                 self.request),
                                                 name='plone_portal_state')


def absolutize_path(path, context=None, is_alias=True):
    """Check whether `path` is a well-formed path from the portal root, and
       make it Zope-root-relative. If `is_alias` (as opposed to "is_target"),
       also make sure the user has the requisite ModifyAliases permissions to
       make an alias from that path. Return a 2-tuple: (absolute redirection path,
       an error message iff something goes wrong and otherwise '').

    Assume relative paths are relative to `context`; reject relative paths if
    `context` is None.

    """
    portal = component.getUtility(ISiteRoot)
    err = None
    if path is None or path == '':
        err = is_alias and _(u"You have to enter an alias.") \
                        or _(u"You have to enter a target.")
    elif '://' in path:
        err = is_alias and _(u"An alias is a path from the portal root and doesn't include http:// or alike.") \
                        or _(u"Target path must be relative to the portal root and not include http:// or the like.")
    else:
        if path.startswith('/'):
            context_path = "/".join(portal.getPhysicalPath())
            path = "%s%s" % (context_path, path)
        else:
            if context is None:
                err = is_alias and _(u"Alias path must start with a slash.") \
                                or _(u"Target path must start with a slash.")
            else:
                context_path = "/".join(context.getPhysicalPath()[:-1])
                path = "%s/%s" % (context_path, path)
        if not err and is_alias:  # XXX should we require Modify Alias permission on the target as well?
            source = path.split('/')
            while len(source):
                obj = portal.unrestrictedTraverse(source, None)
                if obj is None:
                    source = source[:-1]
                else:
#                    if not getSecurityManager().checkPermission(ModifyAliases, obj):
#                        obj = None
                    break
            if obj is None:
                err = _(u"You don't have the permission to set an alias from the location you provided.")
            else:
                pass
                # XXX check if there is an existing alias
                # XXX check whether there is an object
    return path, err

class ControlPanel(BrowserView):
    """Control panel controller for plone.app.redirector package
    """
    template = ViewPageTemplateFile('controlpanel.pt')

    def __init__(self, context, request):
        super(ControlPanel, self).__init__(context, request)
        self.errors = []  # list of tuples: (line_number, absolute_redirection_path, err_msg, target)

    def redirects(self):
        storage = component.getUtility(IRedirectionStorage)
        portal = component.getUtility(ISiteRoot)
        context_path = "/".join(self.context.getPhysicalPath())
        portal_path = "/".join(portal.getPhysicalPath())
        portal_path_len = len(portal_path)
        for redirect in storage:
            if redirect.startswith(portal_path):
                path = redirect[portal_path_len:]
            else:
                path = redirect
            redirectto = storage.get(redirect)
            if redirectto.startswith(portal_path):
                redirectto = redirectto[portal_path_len:]
            yield {
                'redirect': redirect,
                'path': path,
                'redirect-to': redirectto,
            }

    def __call__(self):
        storage = component.getUtility(IRedirectionStorage)
        portal = component.getUtility(ISiteRoot)
        request = self.request
        form = request.form
        status = IStatusMessage(self.request)

        if 'form.button.Remove' in form:
            redirects = form.get('redirects', ())
            for redirect in redirects:
                storage.remove(redirect)
            if len(redirects) == 0:
                status.addStatusMessage(_(u"No aliases selected for removal."), type='info')
            elif len(redirects) > 1:
                status.addStatusMessage(_(u"Aliases removed."), type='info')
            else:
                status.addStatusMessage(_(u"Alias removed."), type='info')
        elif 'form.button.Save' in form:
            dst = IAliasesSchema(self.context)
            dst.managed_types = self.request.form['form.managed_types']
        elif 'form.button.Upload' in form:
            self.upload(form['file'], portal, storage, status)
        
        elif 'form.button.Export' in form:
            return self.export()
        
        return self.template()

    def upload(self, file, portal, storage, status):
        """Add the redirections from the CSV file `file`. If anything goes wrong, do nothing."""
        # Turn all kinds of newlines into LF ones. The csv module doesn't do
        # its own newline sniffing and requires either \n or \r.
        file = StringIO('\n'.join(file.read().splitlines()))

        # Use first two lines as a representative sample for guessing format,
        # in case one is a bunch of headers.
        dialect = csv.Sniffer().sniff(file.readline() + file.readline())
        file.seek(0)

        portal_path = "/".join(portal.getPhysicalPath())
        successes = []  # list of tuples: (abs_redirection, target)
        had_errors = False
        for i, fields in enumerate(csv.reader(file, dialect)):
            if len(fields) == 2:
                redirection, target = fields
                abs_redirection, err = absolutize_path(redirection, is_alias=True)
                abs_target, target_err = absolutize_path(target, is_alias=False)
                if err and target_err:
                    err = "%s %s" % (err, target_err)  # sloppy w.r.t. i18n
                elif target_err:
                    err = target_err
                else:
                    if abs_redirection == abs_target:
                        err = _(u"Aliases that point to themselves will cause \
                            an endless cycle of redirects.") # TODO: detect indirect recursion
            else:
                err = _(u"Each line must have 2 columns.")

            if not err:
                if not had_errors:  # else don't bother
                    successes.append((abs_redirection, abs_target))
            else:
                had_errors = True
                self.errors.append(dict(line_number=i+1, line=dialect.delimiter.join(fields), message=err))

        if not had_errors:
            for abs_redirection, abs_target in successes:
                storage.add(abs_redirection, abs_target)
            status.addStatusMessage(_(u"%i aliases added.") % len(successes), type='info')

    @memoize
    def view_url(self):
        return self.context.absolute_url() + '/@@redirection-controlpanel'

    def export(self):
        out = StringIO()
        writer = csv.writer(out)
        writer.writerow(('old path','new path'))
        writer.writerows((r['path'], r['redirect-to']) for r in self.redirects())
        filename = "Redirects for %s.csv" % self.context.title
        self.request.response.setHeader('Content-Type', 'text/csv')
        self.request.response.setHeader('Content-Disposition', 'attachment; filename="%s"' % filename)
        return out.getvalue()
