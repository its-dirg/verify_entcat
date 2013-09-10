__author__ = 'rolandh'

from conf import CONFIG
from conf import BASE
from saml2.entity_category.swamid import RESEARCH_AND_EDUCATION
from saml2.entity_category.swamid import NREN

CONFIG["entityid"] = "%s/%s/sp.xml" % (BASE, "re_nren")
CONFIG["entity_category"] = [RESEARCH_AND_EDUCATION, NREN]

from saml2 import BINDING_HTTP_REDIRECT
from saml2 import BINDING_HTTP_POST
CONFIG["service"]["sp"]["endpoints"]["assertion_consumer_service"] = [
    ("%s/acs/re_nren/redirect" % BASE, BINDING_HTTP_REDIRECT),
    ("%s/acs/re_nren/post" % BASE, BINDING_HTTP_POST)
]