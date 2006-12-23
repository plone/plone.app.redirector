from zope.component import queryUtility
from plone.app.redirector.interfaces import IRedirectionStorage

# XXX: If we wanted to, we could try to keep aliases for children as well.
# For example, if /foo is moved to /bar, /foo/one/two/three should redirect
# to /bar/one/two/three... However, building the redirects like that may be
# quite complicated and expensive.

# Note that by accident, /foo/one will work, but /foo/one/two will not work.
# This is because the redirect view will attempt to use the implied parent
# when you try something like /foo/document_view to get /bar/document_view.

def objectMoved(obj, event):
    """Tell the redirection storage that an object moved
    """
    # Unfortunately, IObjectMoved is a rather generic event...
    if event.oldParent is not None and event.newParent is not None:
        storage = queryUtility(IRedirectionStorage)
        if storage is not None:
            old_path = "%s/%s" % ('/'.join(event.oldParent.getPhysicalPath()), event.oldName,)
            
            # XXX: Special case - don't remember anything happening inside portal_factory
            if '/portal_factory/' in old_path:
                return
            
            new_path = '/'.join(obj.getPhysicalPath())
            storage.add(old_path, new_path)
        
def objectRemoved(obj, event):
    """Tell the redirection storage that the object was removed
    """
    storage = queryUtility(IRedirectionStorage)
    if storage is not None:
        path = '/'.join(obj.getPhysicalPath())
        storage.destroy(path)