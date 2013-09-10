__author__ = 'rolandh'

from conf import CONFIG
from conf import BASE
from saml2.entity_category.swamid import NREN

CONFIG["entityid"] = "%s/%s/sp.xml" % (BASE, "nren")
CONFIG["entity_category"] = [NREN]

from saml2 import BINDING_HTTP_REDIRECT
from saml2 import BINDING_HTTP_POST
CONFIG["service"]["sp"]["endpoints"]["assertion_consumer_service"] = [
    ("%s/acs/nren/redirect" % BASE, BINDING_HTTP_REDIRECT),
    ("%s/acs/nren/post" % BASE, BINDING_HTTP_POST)
]
