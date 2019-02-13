# -*- coding: utf-8 -*-
from contextlib import contextmanager
from plone.app.redirector.storage import RedirectionStorage
from time import time

import os
import unittest


env_name = 'PLONE_APP_REDIRECTOR_PERFORMANCE_NUMBER'
NUMBER = int(os.getenv(env_name, 0))


class TestStoragePerformance(unittest.TestCase):
    """Test the performance of the RedirectionStorage class.
    """

    @contextmanager
    def timeit(self, message, limit=0):
        start = time()
        yield
        end = time()
        total = end - start
        # Allow taking at least 0.1 seconds.  Otherwise a really low NUMBER
        # like 0 may give errors like this:
        # AssertionError: Listing all takes too long: 0.00 seconds (max 1e-06)
        limit = max(limit, 0.1)
        if total > limit:
            self.fail(
                '{0} takes too long: {1:.2f} seconds (max {2})'.format(
                    message, total, limit
                )
            )
        else:
            print(
                '{0}: {1:.2f} seconds (max {2})'.format(message, total, limit)
            )

    @unittest.skipIf(NUMBER <= 0, '{0} env variable not set'.format(env_name))
    def test_storage_performance(self):
        """Test the performance of some of the code.

        This is skipped by default, unless you set an environment variable.
        If you don't set this, or set this to zero or less, you will see
        a skip reason when you run the tests with enough verbosity:

            $ bin/test -s plone.app.redirector -m test_performance -vvv

        Sample run with one million inserts:

            $ PLONE_APP_REDIRECTOR_PERFORMANCE_NUMBER=1000000 \
                bin/test -s plone.app.redirector -m test_performance
            ...
            Running plone.app.redirector storage performance tests.
            Inserting 1000000 paths...
            Inserting: 9.39 seconds (max 1000.0)
            Getting length: 0.01 seconds (max 0.1)
            Getting iterator: 0.00 seconds (max 0.1)
            Listing all: 0.05 seconds (max 1.0)
            Listing and getting each single one: 1.82 seconds (max 10.0)

        """
        st = RedirectionStorage()

        print('\nRunning plone.app.redirector storage performance tests.')
        print('Inserting {0} paths...'.format(NUMBER))
        # Can take long.  But 10.000 per second should be no problem.
        with self.timeit('Inserting', NUMBER / 10000.0):
            for i in range(NUMBER):
                st['/old/{0}'.format(i)] = '/new/{0}'.format(i)

        # Should be almost instantaneous.
        with self.timeit('Getting length'):
            self.assertEqual(len(st), NUMBER)

        # Should be almost instantaneous.
        with self.timeit('Getting iterator'):
            iter(st)

        # Should be fairly quick.
        with self.timeit('Listing all', NUMBER / 1000000.0):
            list(st)

        # Should be reasonably quick, but the time is noticeable.
        with self.timeit(
            'Listing and getting each single one', NUMBER / 100000.0
        ):
            for key in st:
                st[key]


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStoragePerformance))
    return suite
