from BTrees.OOBTree import OOBTree
from BTrees.OOBTree import OOSet
from DateTime import DateTime
from persistent import Persistent
from plone.app.redirector.interfaces import IRedirectionStorage
from zope.interface import implementer


_marker = object()


@implementer(IRedirectionStorage)
class RedirectionStorage(Persistent):
    """Stores old paths to new paths.

    Note - instead of storing "new paths" it could store object ids or
    similar. In general, there is a many-to-one relationship between
    "old paths" and "new paths". An "old path" points to exactly one
    "new path" (where the object is now to be found), but a "new path"
    can be pointed to by multiple different "old paths" (several objects
    that used to be distinct are now consolidated into one).

    See test_storage.py for demonstrations of its usage.
    """

    def __init__(self):
        self.clear()

    def clear(self):
        # If the data already exists, we could call 'clear' on all BTrees,
        # but making them fresh seems cleaner and faster.
        self._paths = OOBTree()
        self._rpaths = OOBTree()

    def add(self, old_path, new_path, now=None, manual=False):
        old_path = self._canonical(old_path)
        new_path = self._canonical(new_path)

        if old_path == new_path:
            return

        # Forget any existing reverse paths to old_path
        existing_target = self.get(old_path)
        if (existing_target is not None) and (existing_target in self._rpaths):
            # old_path was pointing to existing_target, but now we want it to
            # point to new_path.  So remove the existing reverse path.
            if len(self._rpaths[existing_target]) == 1:
                del self._rpaths[existing_target]
            else:
                self._rpaths[existing_target].remove(old_path)

        if now is None:
            now = DateTime()
        full_value = (new_path, now, manual)

        # Update any references that pointed to old_path
        for p in self.redirects(old_path):
            # p points to old_path, but old_path will point to new_path,
            # so we update p to point to new_path directly.
            if p != new_path:
                old_full_value = self._paths[p]
                if isinstance(old_full_value, tuple):
                    # keep date and manual
                    new_full_value = (
                        new_path,
                        old_full_value[1],
                        old_full_value[2],
                    )
                else:
                    new_full_value = full_value
                self._paths[p] = new_full_value
                self._rpaths.setdefault(new_path, OOSet()).insert(p)
            else:
                # There is an existing redirect from new_path to old_path.
                # We now want to update new_path to point to new_path.
                # This is not useful, so we delete it.
                del self._paths[new_path]

        # Remove reverse paths for old_path.  If old_path was being
        # redirected to, the above code will have updated those redirects,
        # so this reverse redirect info is no longer needed.
        if old_path in self._rpaths:
            del self._rpaths[old_path]

        self._paths[old_path] = full_value
        self._rpaths.setdefault(new_path, OOSet()).insert(old_path)

    __setitem__ = add

    def update(self, info, manual=True):
        # Bulk update information.
        # Calling update will usually be done for manual additions (csv upload).
        now = DateTime()
        for key, value in info.items():
            if isinstance(value, tuple):
                # This is (new path, datetime, manual),
                # where datetime may be None.
                self.add(key, value[0], now=value[1] or now, manual=value[2])
            else:
                self.add(key, value, now=now, manual=manual)

    def remove(self, old_path):
        old_path = self._canonical(old_path)
        new_path = self.get(old_path)
        if new_path is not None and new_path in self._rpaths:
            if len(self._rpaths[new_path]) == 1:
                del self._rpaths[new_path]
            else:
                self._rpaths[new_path].remove(old_path)
        del self._paths[old_path]

    __delitem__ = remove

    def _rebuild(self):
        """Rebuild the information.

        Can be used in migration to initialize the date and manual information.

        For good measure, this also rebuild the _rpaths structure:
        the _paths structure is leading.  For one million paths,
        the _paths rebuilding takes 1 second,
        and the _rpaths an extra 3 seconds.  Seems fine, as this should
        rarely be used.
        """
        now = DateTime()
        self._rpaths = OOBTree()
        for old_path in self._paths:
            new_info = self._paths[old_path]
            if isinstance(new_info, tuple):
                new_path = new_info[0]
            else:
                # Store as tuple: (new_path, date, manual).
                # We cannot know if this was a manual redirect or not.
                # For safety we register this as a manual one.
                new_path = new_info
                new_info = (new_path, now, True)
                self._paths[old_path] = new_info
            self._rpaths.setdefault(new_path, OOSet()).insert(old_path)

        # Look for inconsistenties and fix them:
        # paths that are both in paths and in rpaths.
        bads = [new_path for new_path in self._rpaths if new_path in self._paths]
        for new_path in bads:
            newer_path = self._paths[new_path][0]
            for old_path in self._rpaths[new_path]:
                # old_path points to new_path,
                # but new_path points to newer_path.
                # So update old_path to point to newer_path.
                info = self._paths[old_path]
                info = (newer_path, info[1], info[2])
                self._paths[old_path] = info
                self._rpaths[newer_path].insert(old_path)
            # self._rpaths[new_path] is empty now
            del self._rpaths[new_path]

    def destroy(self, new_path):
        new_path = self._canonical(new_path)
        for p in self._rpaths.get(new_path, []):
            if p in self._paths:
                del self._paths[p]
        if new_path in self._rpaths:
            if new_path in self._rpaths:
                del self._rpaths[new_path]

    def has_path(self, old_path):
        old_path = self._canonical(old_path)
        return old_path in self._paths

    __contains__ = has_path

    def get(self, old_path, default=None):
        old_path = self._canonical(old_path)
        new_path = self._paths.get(old_path, default)
        if isinstance(new_path, tuple):
            # (new_path, date, manual)
            return new_path[0]
        return new_path

    def get_full(self, old_path, default=None):
        old_path = self._canonical(old_path)
        new_path = self._paths.get(old_path, default)
        if isinstance(new_path, tuple):
            # (new_path, date, manual)
            return new_path
        return (new_path, None, True)

    def __getitem__(self, old_path):
        result = self.get(old_path, default=_marker)
        if result is _marker:
            raise KeyError(old_path)
        return result

    def redirects(self, new_path):
        new_path = self._canonical(new_path)
        return [a for a in self._rpaths.get(new_path, [])]

    def _canonical(self, path):
        if path.endswith("/"):
            path = path[:-1]
        return path

    def __iter__(self):
        return iter(self._paths)

    def __len__(self):
        return len(self._paths)
