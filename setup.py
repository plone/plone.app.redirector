from setuptools import setup, find_packages

version = '1.0.11'

setup(name='plone.app.redirector',
      version=version,
      description="redirection tool",
      long_description=open("README.txt").read(),
      classifiers=[
          "Framework :: Plone",
          "Framework :: Zope2",
          "Programming Language :: Python",
          ], 
      keywords='',
      author='Martin Aspeli, based on work by Helge Tesdal and Whit Morriss',
      author_email='plone-developers@lists.sourceforge.net',
      url='http://pypi.python.org/pypi/plone.app.redirector',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages = ['plone', 'plone.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
        'plone.memoize',
      ],
      )
