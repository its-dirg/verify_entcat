#!/usr/bin/env python
import json

from subprocess import Popen, PIPE
from saml2.sigver import get_xmlsec_binary

#
MAKE_METADATA = "make_metadata.py"
# or if you have problem with your paths be more specific
#MAKE_METADATA = "/usr/bin/make_metadata.py"
#MAKE_METADATA = "/Library/Frameworks/Python.framework/Versions/2.7/bin/make_metadata.py"

XMLSEC = get_xmlsec_binary(["/opt/local/bin", "/usr/local/bin"])

MDNS = '"urn:oasis:names:tc:SAML:2.0:metadata"'
NFORMAT = "xenosmilus.umdc.umu.se-8086%ssp.xml"

CNFS = [""]
COMBOS = json.loads(open("build.json").read())
CNFS.extend(COMBOS.keys())

for cnf in CNFS:

    if cnf:
        name = "conf_%s.py" % cnf
        fname = "-%s-" % cnf
    else:
        name = "conf.py"
        fname = "-"

    print 10*"=" + name + 10*"="

    com_list = [MAKE_METADATA, "-x", XMLSEC, name]
    pof = Popen(com_list, stderr=PIPE, stdout=PIPE)

    txt = pof.stdout.read()
    txt = txt.replace(MDNS,
                      MDNS+" xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"")
    f = open(NFORMAT % fname, "w")
    f.write(txt)
    f.close()
    #print etxt
