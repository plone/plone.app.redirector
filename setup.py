from setuptools import setup, find_packages

version = '1.3.2'

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
          "Framework :: Zope2",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
      ],
      keywords='links redirect',
      author='Plone Foundation',
      author_email='plone-developers@lists.sourceforge.net',
      url='https://pypi.python.org/pypi/plone.app.redirector',
      license='GPL version 2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone', 'plone.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'plone.memoize',
      ],
      extras_require={
          'test': [
              'plone.app.testing',
              'plone.app.contenttypes'
          ]
      },
      )
