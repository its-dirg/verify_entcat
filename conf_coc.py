
__author__ = 'rolandh'

from conf import CONFIG
from conf import BASE
from saml2.entity_category.edugain import COC

CONFIG["entityid"] = "%s/%s/sp.xml" % (BASE, "coc")
CONFIG["entity_category"] = [COC]

from saml2 import BINDING_HTTP_REDIRECT
from saml2 import BINDING_HTTP_POST
CONFIG["service"]["sp"]["endpoints"]["assertion_consumer_service"] = [
    ("%s/acs/coc/redirect" % BASE, BINDING_HTTP_REDIRECT),
    ("%s/acs/coc/post" % BASE, BINDING_HTTP_POST)
]
