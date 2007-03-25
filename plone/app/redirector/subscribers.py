from zope.component import queryUtility
from plone.app.redirector.interfaces import IRedirectionStorage

from Acquisition import aq_base

def objectMoved(obj, event):
    """Tell the redirection storage that an object moved
    """
    # Unfortunately, IObjectMoved is a rather generic event...
    if event.oldParent is not None and event.newParent is not None and event.oldName is not None:
        storage = queryUtility(IRedirectionStorage)
        if storage is not None:
            old_path = "%s/%s" % ('/'.join(event.oldParent.getPhysicalPath()), event.oldName,)
            
            # This event gets redispatched to children, and we should keep track of them as well
            # In this case, event.object is not the same as obj, and the old_path should actually
            # include obj.id
            
            if aq_base(event.object) is not aq_base(obj):
                old_path = "%s/%s" % (old_path, obj.getId(),)
            
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