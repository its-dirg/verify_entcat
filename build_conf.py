#!/usr/bin/env python
import json

import pprint

__author__ = 'rolandh'

from conf import CONFIG
from conf import BASE

SETUP = """
try:
    from saml2.sigver import get_xmlsec_binary
except ImportError:
    get_xmlsec_binary = None


if get_xmlsec_binary:
    xmlsec_path = get_xmlsec_binary(["/opt/local/bin", "/usr/local/bin"])
else:
    xmlsec_path = '/usr/local/bin/xmlsec1'

"""

#from saml2.entity_category.swamid import RESEARCH_AND_EDUCATION
#CONFIG["entityid"] = "%s/%s/sp.xml" % (BASE, "re_eu")
#CONFIG["entity_category"] = [RESEARCH_AND_EDUCATION, EU]

COMBOS = json.loads(open("build.json").read())

pp = pprint.PrettyPrinter(indent=2)

for key, spec in COMBOS.items():
    text = []
    ecs = []
    for mod, ec in spec:
        text.append("from %s import %s" % (mod, ec))
        ecs.append(ec)
    text.extend([SETUP, "BASE = \"%s\"" % BASE, ""])

    CONFIG["entityid"] = "%%s/%%s/sp.xml %% (BASE, \"%s\")" % key
    CONFIG["entity_category"] = ecs
    _acs = []
    for v in CONFIG["service"]["sp"]["endpoints"]["assertion_consumer_service"]:
        url = v[0]
        if url.endswith("/redirect"):
            url = url[:-8]
            url += "%s/redirect" % key
        elif url.endswith("/post"):
            url = url[:-4]
            url += "%s/post" % key
        _acs.append((url, v[1]))
    CONFIG["service"]["sp"]["endpoints"]["assertion_consumer_service"] = _acs
    _str = "CONFIG = %s" % pp.pformat(CONFIG)
    _str = _str.replace("u'", "'")
    for mod, ec in spec:
        _str = _str.replace("'%s'" % ec, ec)
    text.append(_str)
    fil = open("conf_%s.py" % key, "w")
    fil.write("\n".join(text))
    fil.close()
