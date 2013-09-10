__author__ = 'rolandh'

from conf import CONFIG
from conf import BASE
from saml2.entity_category.swamid import SFS_1993_1153

CONFIG["entityid"] = "%s/%s/sp.xml" % (BASE, "sfs")
CONFIG["entity_category"] = [SFS_1993_1153]

from saml2 import BINDING_HTTP_REDIRECT
from saml2 import BINDING_HTTP_POST
CONFIG["service"]["sp"]["endpoints"]["assertion_consumer_service"] = [
    ("%s/acs/sfs/redirect" % BASE, BINDING_HTTP_REDIRECT),
    ("%s/acs/sfs/post" % BASE, BINDING_HTTP_POST)
]