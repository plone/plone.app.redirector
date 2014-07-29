Introduction
============

by Martin Aspeli <optilude@gmx.net> based on work by Helge Tesdal
(RedirectionTool) and Whit Morriss (topp.rose).

Bring dead links back to life! plone.app.redirector knows where your content
used to be and can bring you to its new location when content moves.

This component expects you to register storage.RedirectionStorage as a local
utility providing IRedirectionStorage (CMFPlone does this). Once that's done,
the subscribers in subscribers.py will listen for object moved and object
deleted events.

When an object is moved (renamed or cut/pasted into a different location),
the redirection storage will remember the old path. It is smart enough to
deal with transitive references (if we have a -> b and then add b -> c,
it is replaced by a reference a -> c) and circular references (attempting to
add a -> a does nothing).

When an object is deleted, all references to it are deleted as well.

The view in browser.py contains methods (used in Plone's
default_error_message.pt when it gets a NotFound error) that do the following:

- attempt to redirect from the assumed intended path to the new path of an
  object, if the redirection storage holds a reference from the old path.

- if not, look for the first valid parent of the assumed intended path, and
  present it as an option to the user

- further, use the last id of the assumed intended path and attempt to search
  for objects in the catalog that contain this, presenting the options to the
  user

