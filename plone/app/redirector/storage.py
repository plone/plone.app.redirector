# -*- coding: utf-8 -*-
from zope.interface import implementer

from persistent import Persistent
from BTrees.OOBTree import OOBTree, OOSet
from DateTime import DateTime
from plone.app.redirector.interfaces import IRedirectionStorage


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
        if (existing_target is not None) and (
            existing_target in self._rpaths):
            if len(self._rpaths[existing_target]) == 1:
                del self._rpaths[existing_target]
            else:
                self._rpaths[existing_target].remove(old_path)

        if now is None:
            now = DateTime()
        full_value = (new_path, now, manual)

        # Update any references that pointed to old_path
        for p in self.redirects(old_path):
            if p != new_path:
                old_full_value = self._paths[p]
                if isinstance(old_full_value, tuple):
                    # keep date and manual
                    new_full_value = (
                        new_path, old_full_value[1], old_full_value[2])
                else:
                    new_full_value = full_value
                self._paths[p] = new_full_value
                self._rpaths.setdefault(new_path, OOSet()).insert(p)
            else:
                # There is an existing redirect from new_path to old_path.
                # We now want to update new_path to point to new_path.
                # This is not useful, so we delete it.
                del self._paths[new_path]

        # Remove reverse paths for old_path
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
        # Rebuild the information.
        # Can be used in migration to initialize the dates.
        now = DateTime()
        for path in self._paths:
            new_path = self._paths[path]
            if isinstance(new_path, tuple):
                continue
            # Store as tuple: (new_path, date, manual).
            # We cannot know if this was a manual redirect or not.
            # For safety we register this as a manual one.
            self._paths[path] = (new_path, now, True)

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
            # (new_path, date)
            return new_path[0]
        return new_path

    def __getitem__(self, old_path):
        result = self.get(old_path, default=_marker)
        if result is _marker:
            raise KeyError(old_path)
        return result

    def redirects(self, new_path):
        new_path = self._canonical(new_path)
        return [a for a in self._rpaths.get(new_path, [])]

    def _canonical(self, path):
        if path.endswith('/'):
            path = path[:-1]
        return path

    def __iter__(self):
        return iter(self._paths)

    def __len__(self):
        return len(self._paths)
