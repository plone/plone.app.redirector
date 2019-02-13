# -*- coding: utf-8 -*-
from plone.app.redirector.storage import RedirectionStorage
from time import time

import os
import unittest


env_name = 'PLONE_APP_REDIRECTOR_PERFORMANCE_NUMBER'
NUMBER = int(os.getenv(env_name, 0))


class TestStoragePerformance(unittest.TestCase):
    """Test the performance of the RedirectionStorage class.
    """

    @unittest.skipIf(NUMBER <= 0, '{0} env variable not set'.format(env_name))
    def test_storage_performance(self):
        """Test the performance of some of the code.

        This is skipped by default, unless you set an environment variable.
        If you don't set this, or set this to zero or less, you will see
        a skip reason when you run the tests with enough verbosity:

            $ bin/test -s plone.app.redirector -m test_performance -vvv

        Sample run with one hundred thousand inserts:

            $ PLONE_APP_REDIRECTOR_PERFORMANCE_NUMBER=100000 \
                bin/test -s plone.app.redirector -m test_performance
            ...
            Running plone.app.redirector storage performance tests.
            Inserting 100000 paths...
            Inserting: 0.74 seconds
            Getting length: 0.00 seconds
            Getting iterator: 0.00 seconds
            Listing all: 0.01 seconds
            Listing and getting each single one: 0.16 seconds

        """
        st = RedirectionStorage()

        start_time = time()
        print('\nRunning plone.app.redirector storage performance tests.')
        print('Inserting {0} paths...'.format(NUMBER))
        for i in range(NUMBER):
            st['/old/{0}'.format(i)] = '/new/{0}'.format(i)
        insert_time = time()
        insert_seconds = insert_time - start_time
        print('Inserting: {0:.2f} seconds'.format(insert_seconds))

        # len
        self.assertEqual(len(st), NUMBER)
        length_time = time()
        length_seconds = length_time - insert_time
        print('Getting length: {0:.2f} seconds'.format(length_seconds))

        # iter
        iter(st)
        iter_time = time()
        iter_seconds = iter_time - length_time
        print('Getting iterator: {0:.2f} seconds'.format(iter_seconds))

        # list
        list(st)
        list_time = time()
        list_seconds = list_time - iter_time
        print('Listing all: {0:.2f} seconds'.format(list_seconds))

        # list + get
        for key in st:
            st[key]
        getall_time = time()
        getall_seconds = getall_time - list_time
        print(
            'Listing and getting each single one: {0:.2f} seconds'.format(
                getall_seconds
            )
        )


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStoragePerformance))
    return suite
