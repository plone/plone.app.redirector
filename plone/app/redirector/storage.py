# -*- coding: utf-8 -*-
from zope.interface import implementer

from persistent import Persistent
from BTrees.OOBTree import OOBTree, OOSet
from DateTime import DateTime
from plone.app.redirector.interfaces import IRedirectionStorage
from six import string_types


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
        self._dates = OOBTree()
        self._manual = OOSet()

    def add(self, old_path, new_path, now=None):
        old_path = self._canonical(old_path)
        manual = False
        if not isinstance(new_path, string_types):
            manual = new_path[1]
            new_path = new_path[0]
        new_path = self._canonical(new_path)

        if old_path == new_path:
            return

        # Forget any existing reverse paths to old_path
        existing_target = self._paths.get(old_path, None)
        if (existing_target is not None) and (
            existing_target in self._rpaths):
            if len(self._rpaths[existing_target]) == 1:
                del self._rpaths[existing_target]
            else:
                self._rpaths[existing_target].remove(old_path)

        # Update any references that pointed to old_path
        for p in self.redirects(old_path):
            if p != new_path:
                self._paths[p] = new_path
                self._rpaths.setdefault(new_path, OOSet()).insert(p)
            else:
                # There is an existing redirect from new_path to old_path.
                # We now want to update new_path to point to new_path.
                # This is not useful, so we delete it.
                del self._paths[new_path]
                self._dates.pop(new_path, None)
                try:
                    self._manual.remove(new_path)
                except KeyError:
                    # First testing 'new_path in self._manual' looks nicer
                    # but is probably slower.
                    pass

        # Remove reverse paths for old_path
        if old_path in self._rpaths:
            del self._rpaths[old_path]

        self._paths[old_path] = new_path
        self._rpaths.setdefault(new_path, OOSet()).insert(old_path)
        if now is None:
            now = DateTime()
        self._dates[old_path] = now
        if manual:
            # The added redirect is a manual one.
            self._manual.add(old_path)

    __setitem__ = add

    def update(self, info):
        now = DateTime()
        for key, value in info.items():
            self.add(key, value, now=now)

    def remove(self, old_path):
        old_path = self._canonical(old_path)
        new_path = self._paths.get(old_path, None)
        if new_path is not None and new_path in self._rpaths:
            if len(self._rpaths[new_path]) == 1:
                del self._rpaths[new_path]
            else:
                self._rpaths[new_path].remove(old_path)
        del self._paths[old_path]
        # _dates are a new addition, so be forgiving when nothing is found.
        # We can create a method for setting a date for all in migration.
        self._dates.pop(old_path, None)
        try:
            self._manual.remove(old_path)
        except KeyError:
            pass

    __delitem__ = remove

    def _rebuild_dates(self):
        # Rebuild the _dates information.
        # Can be used in migration to initialize the _dates.
        now = DateTime()
        self._dates.clear()
        for path in self._paths:
            self._dates[path] = now

    def destroy(self, new_path):
        new_path = self._canonical(new_path)
        for p in self._rpaths.get(new_path, []):
            if p in self._paths:
                del self._paths[p]
                self._dates.pop(p, None)
                try:
                    self._manual.remove(p)
                except KeyError:
                    pass
        if new_path in self._rpaths:
            if new_path in self._rpaths:
                del self._rpaths[new_path]

    def has_path(self, old_path):
        old_path = self._canonical(old_path)
        return old_path in self._paths

    __contains__ = has_path

    def get(self, old_path, default=None):
        old_path = self._canonical(old_path)
        return self._paths.get(old_path, default)

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
