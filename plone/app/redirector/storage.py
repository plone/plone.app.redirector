from zope.interface import implementer

from persistent import Persistent
from BTrees.OOBTree import OOBTree, OOSet

from plone.app.redirector.interfaces import IRedirectionStorage


@implementer(IRedirectionStorage)
class RedirectionStorage(Persistent):
    """Stores old paths to new paths.

    Note - instead of storing "new paths" it could store object ids or
    similar. In general, there is a many-to-one relationship between
    "old paths" and "new paths". An "old path" points to exactly one
    "new path" (where the object is now to be found), but a "new path"
    can be pointed to by multiple different "old paths" (several objects
    that used to be distinct are now consolidated into one).

    The following tests (see test_storage.py) demonstrate its usage.

        >>> p = RedirectionStorage()

    Add one redirect

        >>> p.has_path('/foo')
        False
        >>> p.add('/foo', '/bar')
        >>> p.has_path('/foo')
        True
        >>> p.get('/foo')
        '/bar'
        >>> p.has_path('/bar')
        False
        >>> p.redirects('/bar')
        ['/foo']

    Note that trailing slashes are ignored:

        >>> p.has_path('/foo/')
        True
        >>> p.get('/foo/')
        '/bar'
        >>> p.redirects('/bar/')
        ['/foo']

    Circular references are ignored

        >>> p.add('/circle', '/circle')
        >>> p.has_path('/circle')
        False
        >>> p.get('/circle', '_marker_')
        '_marker_'
        >>> p.redirects('/circle')
        []

    Add another redirect

        >>> p.has_path('/baz')
        False
        >>> p.add('/baz', '/bar')
        >>> p.has_path('/baz')
        True
        >>> p.get('/baz')
        '/bar'
        >>> sorted(p.redirects('/bar'))
        ['/baz', '/foo']

    Update a redirect

        >>> p.add('/foo', '/quux')
        >>> p.has_path('/foo')
        True
        >>> p.get('/foo')
        '/quux'
        >>> p.redirects('/bar')
        ['/baz']
        >>> p.redirects('/quux')
        ['/foo']

    Remove a redirect

        >>> p.remove('/foo')
        >>> p.has_path('/foo')
        False
        >>> p.get('/foo', default='_notfound_')
        '_notfound_'
        >>> p.redirects('/quux')
        []

    Update a redirect in a chain

        >>> p.add('/fred', '/foo')
        >>> p.get('/fred')
        '/foo'
        >>> sorted(p.redirects('/foo'))
        ['/fred']

        >>> p.add('/fred', '/barney')
        >>> p.get('/fred')
        '/barney'
        >>> sorted(p.redirects('/foo'))
        []
        >>> sorted(p.redirects('/barney'))
        ['/fred']

        >>> p.add('/barney', '/wilma')
        >>> p.get('/fred')
        '/wilma'
        >>> p.get('/barney')
        '/wilma'
        >>> sorted(p.redirects('/wilma'))
        ['/barney', '/fred']
        >>> sorted(p.redirects('/barney'))
        []

    Destroy the target of a redirect

        >>> p.destroy('/wilma')
        >>> p.has_path('/barney')
        False
        >>> p.has_path('/fred')
        False
        >>> p.redirects('/wilma')
        []

    What about three step circular rename ?

    Add first redirect.

        >>> p.add('first', 'second')

    There is only one redirect.

        >>> p.get('first')
        'second'
        >>> p.get('second')
        >>> p.get('third')

    There is one back reference.

        >>> p.redirects('first')
        []
        >>> p.redirects('second')
        ['first']
        >>> p.redirects('third')
        []

    Add second redirect.

        >>> p.add('second', 'third')

    There are now two.

        >>> p.get('first')
        'third'
        >>> p.get('second')
        'third'
        >>> p.get('third')

    There are two back references as well.

        >>> p.redirects('first')
        []
        >>> p.redirects('second')
        []
        >>> p.redirects('third')
        ['first', 'second']

    Add third redirect, CIRCULAR.

        >>> p.add('third', 'first')

    There are still only two redirects.

        >>> p.get('first')
        >>> p.get('second')
        'first'
        >>> p.get('third')
        'first'

    And same for the back references.

        >>> p.redirects('first')
        ['second', 'third']
        >>> p.redirects('second')
        []
        >>> p.redirects('third')
        []

    Cleanup after circular

        >>> p.remove('second')
        >>> p.remove('third')

    We can get an iterator over all existing paths

        >>> iter(p)
        <OO-iterator object at ...>
        >>> sorted(p)
        ['/baz']

    Now add some more

        >>> p.add('/foo', '/bar')
        >>> p.add('/barney', '/wilma')
        >>> sorted(p)
        ['/barney', '/baz', '/foo']
    """

    def __init__(self):
        self._paths = OOBTree()
        self._rpaths = OOBTree()

    def add(self, old_path, new_path):
        old_path = self._canonical(old_path)
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
                del self._paths[new_path]

        # Remove reverse paths for old_path
        if old_path in self._rpaths:
            del self._rpaths[old_path]

        self._paths[old_path] = new_path
        self._rpaths.setdefault(new_path, OOSet()).insert(old_path)

    def remove(self, old_path):
        old_path = self._canonical(old_path)
        new_path = self._paths.get(old_path, None)
        if new_path is not None and new_path in self._rpaths:
            if len(self._rpaths[new_path]) == 1:
                del self._rpaths[new_path]
            else:
                self._rpaths[new_path].remove(old_path)
        del self._paths[old_path]

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

    def get(self, old_path, default=None):
        old_path = self._canonical(old_path)
        return self._paths.get(old_path, default)

    def redirects(self, new_path):
        new_path = self._canonical(new_path)
        return [a for a in self._rpaths.get(new_path, [])]

    def _canonical(self, path):
        if path.endswith('/'):
            path = path[:-1]
        return path

    def __iter__(self):
        return iter(self._paths)
