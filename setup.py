from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='plone.app.redirector',
      version=version,
      description="redirection tool",
      long_description="""\
bring dead links back to life!""",
      classifiers=[], # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Martin Aspeli, based on work by Helge Tesdal and Whit Morriss',
      author_email='plone-developers@lists.sourceforge.net',
      url='https://svn.plone.org/svn/plone/plone.app.redirector',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
