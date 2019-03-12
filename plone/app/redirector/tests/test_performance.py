# -*- coding: utf-8 -*-
from contextlib import contextmanager
from plone.app.redirector.storage import RedirectionStorage
from time import time

import os
import unittest


env_name = 'PLONE_APP_REDIRECTOR_PERFORMANCE_NUMBER'
if env_name in os.environ:
    # This could fail with a ValueError, but that seems a fine error message.
    NUMBER = max(int(os.getenv(env_name)), 1)
    VERBOSE = True
else:
    # No environment variable set.
    # Pick a relatively low number so the run is fast.
    # And don't be verbose, don't print anything:
    # only give an assertion error when it is really slow.
    NUMBER = 10000
    VERBOSE = False


def pretty_number(num):
    if num < 1000:
        return num
    num = int(num / 1000)
    if num < 1000:
        return '{0} thousand'.format(num)
    num = int(num / 1000)
    return '{0} million'.format(num)


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
        elif VERBOSE:
            print(
                '{0}: {1:.2f} seconds (max {2})'.format(message, total, limit)
            )

    def test_storage_performance(self):
        """Test the performance of some of the code.

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
        if VERBOSE:
            print('\nRunning plone.app.redirector storage performance tests.')

        # Can take long.  But 10.000 per second should be no problem.
        # Take one tenth of the items at first.
        num = max(int(NUMBER / 10), 1)
        with self.timeit(
            'Inserting {0} individual items'.format(pretty_number(num)),
            num / 10000.0,
        ):
            for i in range(num):
                st['/old/{0}'.format(i)] = '/new/{0}'.format(i)

        # I expected this to be almost instantaneous because we replace
        # the data with new OOBTrees, but it still takes time:
        # for ten million items it take 0.3 seconds.
        with self.timeit('Clearing storage', num / 1000000.0):
            st.clear()

        # Should be fairly quick.
        with self.timeit(
            'Preparing {0} items for bulk import'.format(
                pretty_number(NUMBER)
            ),
            NUMBER / 100000.0,
        ):
            info = {
                '/old/{0}'.format(i): '/new/{0}'.format(i)
                for i in range(NUMBER)
            }

        # Can take long.  But 10.000 per second should be no problem.
        with self.timeit(
            'Inserting {0} prepared items in bulk'.format(
                pretty_number(NUMBER)
            ),
            NUMBER / 10000.0,
        ):
            # Prepare input:
            info = {}
            for i in range(NUMBER):
                info['/old/{0}'.format(i)] = '/new/{0}'.format(i)
            st.update(info)

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

        # Can take long.  But 10.000 per second should be no problem.
        with self.timeit(
            'Rebuilding the structure for migration', NUMBER / 100000.0
        ):
            st._rebuild()
