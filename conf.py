from saml2 import BINDING_HTTP_REDIRECT
from saml2 import BINDING_HTTP_POST
from saml2.extension.idpdisc import BINDING_DISCO
from saml2.saml import NAME_FORMAT_URI

try:
    from saml2.sigver import get_xmlsec_binary
except ImportError:
    get_xmlsec_binary = None


if get_xmlsec_binary:
    xmlsec_path = get_xmlsec_binary(["/opt/local/bin","/usr/local/bin"])
else:
    xmlsec_path = '/usr/bin/xmlsec1'

BASE = "https://samltest.swamid.se"

CONFIG = {
    "entityid": "%s/%ssp.xml" % (BASE, ""),
    "description": "Verify Entity Categories SP",
    "service": {
        "sp": {
            "name": "Verify Entity Categories",
            "endpoints": {
                "assertion_consumer_service": [
                    ("%s/acs/redirect" % BASE, BINDING_HTTP_REDIRECT),
                    ("%s/acs/post" % BASE, BINDING_HTTP_POST)
                ],
                "discovery_response": [
                    ("%s/disco" % BASE, BINDING_DISCO)
                ]
            }
        },
    },
    "key_file": "pki/sp.key",
    "cert_file": "pki/sp.crt",
    #"attribute_map_dir": "../pysaml2/src/saml2/attributemaps",
    "xmlsec_binary": xmlsec_path,
    "metadata": {"mdfile": ["./swamid2.md"]},
    "name_form": NAME_FORMAT_URI,
    #"entity_category": ["http://www.swamid.se/category/research-and-education"]
}
