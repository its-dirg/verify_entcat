#!/usr/bin/env python
import json
import os

from subprocess import Popen, PIPE
from saml2.sigver import get_xmlsec_binary
import subprocess
import server_conf

class RunScript:
    def runScript(self, command, working_directory=None):
        try:
            p = subprocess.Popen(command,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=working_directory)
            while(True):
                retcode = p.poll() #returns None while subprocess is running
                if(retcode is not None):
                    break
            p_out = p.stdout.read()
            p_err = p.stderr.read()
            return (True, p_out, p_err)
        except Exception as ex:
            return (False, None, None)

MAKE_METADATA = "make_metadata.py"
# or if you have problem with your paths be more specific
#MAKE_METADATA = "/usr/bin/make_metadata.py"
#MAKE_METADATA = "/Library/Frameworks/Python.framework/Versions/2.7/bin/make_metadata.py"

XMLSEC = get_xmlsec_binary(["/opt/local/bin", "/usr/local/bin"])

MDNS = '"urn:oasis:names:tc:SAML:2.0:metadata"'
NFORMAT = "{HOST}%ssp.xml".format(HOST=server_conf.HOST)

CNFS = [""]
COMBOS = json.loads(open("build.json").read())
CNFS.extend(COMBOS.keys())

fname_list = []

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
    fname_list.append(NFORMAT % fname)


fp = open("sp_conf", "w")
len = len(fname_list)
count = 1
for file in fname_list:
    fp.write("local " + file)
    if count != len:
        fp.write(os.linesep)
    count += 1
fp.close()

ok, p_out, p_err = RunScript().runScript(["merge_metadata.py", "sp_conf"])

fp = open("all_sp.xml", "w")
fp.write(p_out)
fp.close()