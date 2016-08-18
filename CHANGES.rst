Changelog
=========

1.3.2 (2016-08-18)
------------------

Fixes:

- Use zope.interface decorator.
  [gforcada]


1.3.1 (2015-09-09)
------------------

- Fixed tests to use registry for value lookup.
  [esteele]


1.3 (2015-08-14)
----------------

- Rerelease of 1.2.1 as 1.3 for clarity.  This is for Plone 5 only.
  [maurits]


1.2.2 (2015-08-14)
------------------

- Rerelease of same code as 1.2.  The changes from 1.2.1 are for Plone 5.
  [maurits]


1.2.1 (2014-02-26)
------------------

- Rename without using folder_contents.
  [davisagli]

- Use p.a.contenttypes test fixture and adapt/fix failing tests due to the
  ATContentTypes removal from PLONE_FIXTURE in Plone 5.
  [timo]


1.2 (2013-05-26)
----------------

- Support redirecting to external URLs.
  [rpatterson]


1.2a1 (2012-07-02)
------------------

- Import object events from zope.lifecycleevent.
  [davisagli]

- Move tests from PloneTestCase to plone.app.testing.
  [timo]


1.1.3 (2012-05-07)
------------------

- Support parts of views e.g. mypage/@@myview/somepart
  [anthonygerrard]

- #12354 will redirect based on the query string as well as path if query_string
  stored. [djay]

- #9967 will append the same query string after redirecting to be more tracker
  friendly. [djay]

- #12858 first suggestion on not found page can be unsuitable
  [anthonygerrard]


1.1.2 - 2011-07-05
------------------

- Don't break in the objectMoved handler if the request has no ACTUAL_URL, to
  facilitate testing.
  [davisagli]

- Add MANIFEST.in.
  [WouterVH]


1.1.1 - 2011-03-02
------------------

- Gracefully handle errors parsing the SearchableText query on the 404 view.
  [davisagli]


1.1 - 2010-07-18
----------------

- Update license to GPL version 2 only.
  [hannosch]


1.0.13 - 2010-01-25
-------------------

- Added optional support for the getRedirectionAllowedForTypes method of
  Products.RedirectionTool.
  [hannosch]


1.0.12 - 2009-06-17
-------------------

- Fix bad calling convention in IFourOhFourView definition.
  [wichert]

- Move event subscribers to a separate zcml file so they can easily be
  excluded.
  [wichert]

- Update browser view to handle environments where the storage utility is not
  availbale.
  [wichert]


1.0.11 - 2009-04-05
-------------------

- Fixed multiple steps circular references #8840
  [gotcha]

- Fixed a bug which caused URLs with %-escaped sequences to grow extra %25s upon
  redirect.
  [erikrose]


1.0.10 - 2009-03-07
-------------------

- Fixed tests to be independent of any default content.
  [hannosch]

- Fixed a test to be less dependent on the page rendering.
  [hannosch]

- Added quotation marks around open and close parens. This fixes
  http://dev.plone.org/plone/ticket/8588.
  [MatthewWilkes]


1.0.9 - 2008-07-07
------------------

- Fix for the fix regarding unnecessary creation of redirection entries for
  newly created objects.
  [witsch]


1.0.8 - 2008-07-07
------------------

- Fix release confusion by ensuring we have a "late" version number.
  Somewhere, someone created a 1.0.7. :-)
  [optilude]


1.0.6 - 2008-07-07
------------------

- Fix unnecessary creation of redirection entries for newly created objects.
  [witsch]


1.0.5 - 2008-01-03
------------------

- Start searches for missing items in the navigation root instead of the site
  root.
  [wichert]


1.0.2 - 2007-10-08
------------------

- also ignore ids from views.
  [ldr]

- Added __iter__ function to storage which iterates over all paths.
  [fschulze]


1.0 - 2007-08-17
----------------

- Initial release.
  [optilude]
