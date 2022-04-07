from zope.interface import Attribute
from zope.interface import Interface


class IRedirectionPolicy(Interface):
    """An adapters that provides some policy about how redirects are performed"""

    ignore_ids = Attribute(
        "A list of ids to ignore when examining a URL " "for a potential redirection"
    )


class IFourOhFourView(Interface):
    """A view that supports a useful 404 page"""

    def attempt_redirect():
        """Attempt to find a single appropriate redirection target by
        investigating the request.

        If a redirection target is found, perform the redirect and return
        True. Else, do nothing and return False.
        """

    def find_first_parent():
        """Look at the URL given, and attempt to translate it into a partial
        path. Find the first "parent" of the attempted path that is an actual
        object and return it.

        Returns None if no object could be found.
        """

    def search_for_similar():
        """Look at the URL given, and attempt to translate it into a partial
        path. Take the id of the requested object (as it would be), and look
        for other objects in the catalog with a SearchableText containing
        this. If found, return the top five matches. If not, look at the
        "parent" as per the attempted path, and so on. If the portal root
        is reached, return an empty list.
        """


class IRedirectionStorage(Interface):
    """A storage for items where the old and the new location are known.

    Will be registered as a local utility.
    """

    def add(old_path, new_path):
        """Remember that the object at old_path is now at new_path.

        Any redirects that already pointed at old_path will now point to
        new_path as well.
        """

    def remove(old_path):
        """Forget all redirects from old_path to any new path"""

    def destroy(new_path):
        """Forget all redirects to new_path.

        Normally called if the object at new_path is removed
        """

    def has_path(old_path):
        """Determine if there are any redirects from old_path in effect."""

    def get(old_path, default=None):
        """Get the new path to the object that used to be at old_path.

        Will return the default value (None, unless set otherwise) if old_path
        is not found.
        """

    def redirects(new_path):
        """Get a list of paths that redirect to new_path.

        Will return an empty list if nothing redirects to new_path.
        """

    def __iter__():
        """Iterate over all existing paths."""
