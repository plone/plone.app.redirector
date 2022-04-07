from Acquisition import aq_base
from plone.app.redirector.interfaces import IRedirectionStorage
from zope.component import queryUtility


def objectMoved(obj, event):
    """Tell the redirection storage that an object moved"""

    # Unfortunately, IObjectMoved is a rather generic event...
    if (
        event.oldParent is not None
        and event.newParent is not None
        and event.oldName is not None
    ):
        storage = queryUtility(IRedirectionStorage)
        if storage is None:
            return

        old_path = "{}/{}".format(
            "/".join(event.oldParent.getPhysicalPath()),
            event.oldName,
        )
        new_path = "/".join(obj.getPhysicalPath())

        # This event gets redispatched to children, and we should keep track of them as well
        # In this case, event.object is not the same as obj, and the old_path should actually
        # include obj.id

        if aq_base(event.object) is not aq_base(obj):
            new_path_of_moved = "/".join(event.object.getPhysicalPath())
            old_path = old_path + new_path[len(new_path_of_moved) :]

        storage.add(old_path, new_path)


def objectRemoved(obj, event):
    """Tell the redirection storage that the object was removed"""
    storage = queryUtility(IRedirectionStorage)
    if storage is not None:
        path = "/".join(obj.getPhysicalPath())
        storage.destroy(path)
