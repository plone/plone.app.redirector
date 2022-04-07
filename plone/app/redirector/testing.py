from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from zope.configuration import xmlconfig


class PloneAppRedirector(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import plone.app.redirector

        xmlconfig.file(
            "configure.zcml", plone.app.redirector, context=configurationContext
        )


PLONE_APP_REDIRECTOR_FIXTURE = PloneAppRedirector()
PLONE_APP_REDIRECTOR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONE_APP_REDIRECTOR_FIXTURE,), name="PloneAppRedirector:Integration"
)
PLONE_APP_REDIRECTOR_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONE_APP_REDIRECTOR_FIXTURE,), name="PloneAppRedirector:Functional"
)
