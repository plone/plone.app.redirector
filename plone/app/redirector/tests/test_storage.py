# -*- coding: utf-8 -*-
import unittest
import doctest

from plone.app.redirector import storage

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(storage, optionflags=optionflags))
    return suite
