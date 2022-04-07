# -*- coding: utf-8 -*-
from plone.app.redirector.interfaces import IRedirectionPolicy
from zope.component import adapts
from zope.interface import implementer
from zope.interface import Interface


@implementer(IRedirectionPolicy)
class RedirectionPolicy(object):
    adapts(Interface)

    def __init__(self, context):
        self.context = context

    # The following ids are ignored when looking for parts of a URL to
    # consider part of a path - see browser.py.

    ignore_ids = (
        "index_html",
        "FrontPage",
        "folder_listing",
        "folder_contents",
        "view",
        "edit",
        "properties",
        "sharing",
        "+",  # IAdding view
    )
