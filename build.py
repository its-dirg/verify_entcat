#!/usr/bin/env python

from subprocess import Popen, PIPE
MAKE_METADATA = "/usr/bin/make_metadata.py"
XMLSEC = "/usr/bin/xmlsec1"

MDNS = '"urn:oasis:names:tc:SAML:2.0:metadata"'

NFORMAT = "xenosmilus.umdc.umu.se-8086%ssp.xml"

for cnf in ["", "coc", "nren", "re", "re_eu", "re_hei", "re_nren", "re_sfs_hei",
            "sfs"]:

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
