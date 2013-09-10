__author__ = 'rolandh'

from conf import CONFIG
from conf import BASE
from saml2.entity_category.swamid import RESEARCH_AND_EDUCATION
from saml2.entity_category.swamid import HEI
from saml2.entity_category.swamid import SFS_1993_1153

CONFIG["entityid"] = "%s/%s/sp.xml" % (BASE, "re_sfs_hei")
CONFIG["entity_category"] = [RESEARCH_AND_EDUCATION, HEI, SFS_1993_1153]

from saml2 import BINDING_HTTP_REDIRECT
from saml2 import BINDING_HTTP_POST
CONFIG["service"]["sp"]["endpoints"]["assertion_consumer_service"] = [
    ("%s/acs/re_sfs_hei/redirect" % BASE, BINDING_HTTP_REDIRECT),
    ("%s/acs/re_sfs_hei/post" % BASE, BINDING_HTTP_POST)
]