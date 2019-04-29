# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

version = '2.1.0'

setup(name='plone.app.redirector',
      version=version,
      description="redirection tool",
      long_description=(open("README.rst").read() + "\n" +
                        open("CHANGES.rst").read()),
      classifiers=[
          "Environment :: Web Environment",
          "Framework :: Plone",
          "Framework :: Plone :: 5.0",
          "Framework :: Plone :: 5.1",
          "Framework :: Plone :: 5.2",
          "Framework :: Zope2",
          "Framework :: Zope :: 4",
          "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
      ],
      keywords='links redirect',
      author='Plone Foundation',
      author_email='plone-developers@lists.sourceforge.net',
      url='https://pypi.org/project/plone.app.redirector',
      license='GPL version 2',
      packages=find_packages(),
      namespace_packages=['plone', 'plone.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'plone.memoize',
          'six',
      ],
      extras_require={
          'test': [
              'plone.app.testing',
              'plone.app.contenttypes'
          ]
      },
      )
