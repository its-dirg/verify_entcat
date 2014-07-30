#!/usr/bin/env python
import json
import logging
import os
import pickle
import re
import argparse
import server_conf

from Cookie import SimpleCookie
from mako.lookup import TemplateLookup
from urlparse import parse_qs
from sqlite3 import dbapi2 as sqlite
import sys

from saml2 import BINDING_HTTP_REDIRECT
from saml2 import BINDING_SOAP
from saml2 import time_util
from saml2 import ecp
from saml2 import BINDING_HTTP_ARTIFACT
from saml2 import BINDING_HTTP_POST
from saml2.client import Saml2Client
from saml2.ecp_client import PAOS_HEADER_INFO
from saml2.httputil import geturl, make_cookie, parse_cookie
from saml2.httputil import get_post
from saml2.httputil import Response
from saml2.httputil import BadRequest
from saml2.httputil import ServiceError
from saml2.httputil import SeeOther
from saml2.httputil import Unauthorized
from saml2.httputil import NotFound
from saml2.httputil import Redirect
from saml2.httputil import NotImplemented
from saml2.response import StatusError
from saml2.response import VerificationError
from saml2.s_utils import UnknownPrincipal
from saml2.s_utils import UnsupportedBinding
from saml2.s_utils import sid
from saml2.s_utils import rndstr

logger = logging.getLogger("")
hdlr = logging.FileHandler('spx.log')
base_formatter = logging.Formatter(
    "%(asctime)s %(name)s:%(levelname)s %(message)s")

hdlr.setFormatter(base_formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

reslog = logging.getLogger("reslog")
r_hdlr = logging.FileHandler('res.log')
r_base_formatter = logging.Formatter("%(asctime)s %(message)s")
r_hdlr.setFormatter(r_base_formatter)
reslog.addHandler(r_hdlr)
reslog.setLevel(logging.INFO)

COMBOS = json.loads(open("build.json").read())
EC_SEQUENCE = [""]
EC_SEQUENCE.extend(COMBOS.keys())

NREN_DESC = (
    "<b>National research and education network</b>(NREN)<br>"
    "The application is provided by the Swedish NREN (SUNET) which is "
    "ultimately responsible for its operation."
    "This category is only relevant for attribute-release between SWAMID "
    "registered IdPs and SUNET services.<br /><br />This category "
    "should return the attribute: <ul><li>eduPersonTargetedID</li></ul>")

RE_DESC = (
    "<b>Research & Education</b>(RE)<br />"
    "The Research & Education category applies to low-risk services that "
    "support research and education as an essential component. For instance, a "
    "service that provides tools for both multi-institutional research "
    "collaboration and instruction is eligible as a candidate for this "
    "category. This category is very similar to InCommons Research & "
    "Scolarship Category. The recommended IdP behavior is to release name, "
    "eppn, eptid, mail and eduPersonScopedAffiliation which also aligns with "
    "the InCommon recommendation only if the services is also in at least one "
    "of the safe data processing categories. It is also a recommendation that "
    "static organisational information is released."
    "<br /><br />This category should return the attributes:"
    "<ul><li>eduPersonTargetedID</li><li>givenName</li><li>initials</li>"
    "<li>displayName</li><li>c</li><li>o</li><li>ou</li>"
    "<li>eduPersonPrincipalName</li><li>sn</li>"
    "<li>eduPersonScopedAffiliation</li><li>email</li></ul>")

SFS_DESC = (
    "<b>Svensk f&ouml;rfattningssamling 1993:1153</b>(SFS)<br />"
    "The SFS 1993:1153 category applies to services that fulfill "
    "<a href='http://www.riksdagen.se/sv/Dokument-Lagar/Lagar/"
    "Svenskforfattningssamling/Forordning-19931153-om-redo_sfs-1993-1153' "
    "target='_blank'>SFS 1993:1153</a>. SFS 1993:1153 limits membership in "
    "this category to services provided by Swedish HEI-institutions, VHS.se or "
    "SCB.se. Example services include common government-operated student- and "
    "admissions administration services such as LADOK and NyA aswell as "
    "enrollment and course registration services. Inclusion in this category "
    "is strictly reserved for applications that are governed by SFS 1993:1153 "
    "which implies that the application may make use of norEduPersonNIN. The "
    "recommended IdP behavior is to release norEduPersonNIN."
    "<br /><br />This category should return the attributes:"
    "<ul><li>eduPersonTargetedID</li><li>norEduPersonNIN</li></ul>")

EU_DESC = (
    "<b>EU Adequate Protection</b>(EU)<br />"
    "The application is compliant with any of the EU adequate protection for "
    "3rd countries according to EU Commission decisions on the adequacy of the "
    "protection of personal data in third countries. This category includes "
    "for instance applications that declares compliance with US safe-harbor."
    "<br /><br />This category should return the attributes:"
    "<ul><li>eduPersonTargetedID</li></ul>")

HEI_DESC = (
    "<b>HEI Service</b>(HEI)<br />"
    "The application is provided by a Swedish HEI which is ultimately "
    "responsible for its operation."
    "<br /><br />This category should return the attributes:"
    "<ul><li>eduPersonTargetedID</li></ul>")

RS_DESC = (
    "<b>Research & Scholarship</b>(RS)<br />"
    "Candidates for the Research and Scholarship (R&S) "
    "Category are Service Providers that support research "
    "and scholarship interaction, collaboration or management "
    "as an essential component."
    "<br /><br />This category should return the attributes:"
    "<ul><li>eduPersonTargetedID</li><li>givenName</li>"
    "<li>displayName</li><li>eduPersonPrincipalName</li>"
    "<li>sn</li><li>eduPersonScopedAffiliation</li><li>mail</li></ul>")

COC_DESC = (
    "<b>Code of Conduct</b>(CoC)<br />The GEANT Data protection Code of "
    "Conduct (CoC) defines an approach on European level to "
    "meet the requirements of the EU data protection directive for releasing "
    "mostly harmless personal attributes to a Service Provider (SP) from an "
    "Identity Provider (IdP). "
    "For more information please see GEANT Data Protection Code of Conduct. "
    "<br /><br />This category should return the attributes:"
    "<ul><li>eduPersonTargetedID</li><li>eduPersonPrincipalName</li>"
    "<li>eduPersonScopedAffiliation</li><li>email</li><li>givenName</li>"
    "<li>sn</li><li>displayName</li><li>schachomeorganization</li></ul>")

# Descriptions exists here:
# https://portal.nordu.net/display/SWAMID/Entity+Categories#EntityCategories
# -SFS1993%3A1153

EC_INFORMATION = {
    "": {"Name": "Base category",
         "Description": (
             "<b>Base category</b><br />A basic category that only should "
             "return the attribute:"
             "<ul><li>eduPersonTargetedID</li></ul>")},
    "coc": {"Name": "CoC", "Description": COC_DESC},
    "nren": {"Name": "NREN", "Description": NREN_DESC},
    "re": {"Name": "RE", "Description": RE_DESC},
    "sfs": {"Name": "SFS", "Description": SFS_DESC},
    "r_and_s": {"Name": "RS", "Description": RS_DESC},
    "re_eu": {"Name": "RE & EU",
              "Description": RE_DESC + "<br /><br />" + EU_DESC},
    "re_hei": {"Name": "RE & HEI",
               "Description": RE_DESC + "<br /><br />" + HEI_DESC},
    "re_nren": {"Name": "RE & NREN",
                "Description": RE_DESC + "<br /><br />" + NREN_DESC},
    "re_nren_sfs": {
        "Name": "RE & NREN & SFS",
        "Description": RE_DESC + "<br /><br />" + NREN_DESC +
                       "<br /><br />" + SFS_DESC},
    "re_sfs_hei": {
        "Name": "RE & SFS & HEI",
        "Description": RE_DESC + "<br /><br />" + SFS_DESC + "<br /><br />" +
                       HEI_DESC},
}

SP = {}
SEED = ""
POLICY = None

LOOKUP = TemplateLookup(directories=['templates', 'htdocs'],
                        module_directory='modules',
                        input_encoding='utf-8',
                        output_encoding='utf-8')


def handleStatic(environ, start_response, path):
    """
    Creates a response for a static file. There might be a longer path
    then just /static/... if so strip the path leading up to static.

    :param environ: wsgi enviroment
    :param start_response: wsgi start response
    :param path: the static file and path to the file.
    :return: wsgi response for the static file.
    """
    try:
        text = open(path).read()
        if path.endswith(".ico"):
            resp = Response(text, headers=[('Content-Type', "image/x-icon")])
        elif path.endswith(".html"):
            resp = Response(text, headers=[('Content-Type', 'text/html')])
        elif path.endswith(".txt"):
            resp = Response(text, headers=[('Content-Type', 'text/plain')])
        elif path.endswith(".css"):
            resp = Response(text, headers=[('Content-Type', 'text/css')])
        elif path.endswith(".js"):
            resp = Response(text, headers=[('Content-Type', 'text/javascript')])
        elif path.endswith(".png"):
            resp = Response(text, headers=[('Content-Type', 'image/png')])
        else:
            resp = Response(text)
    except IOError:
        resp = NotFound()
    return resp(environ, start_response)


class ECP_response(object):
    code = 200
    title = 'OK'

    def __init__(self, content):
        self.content = content

    # noinspection PyUnusedLocal
    def __call__(self, environ, start_response):
        start_response('%s %s' % (self.code, self.title),
                       [('Content-Type', "text/xml")])
        return [self.content]


def _expiration(timeout, tformat=None):
    # Wed, 06-Jun-2012 01:34:34 GMT
    if not tformat:
        tformat = '%a, %d-%b-%Y %T GMT'

    if timeout == "now":
        return time_util.instant(tformat)
    else:
        # validity time should match lifetime of assertions
        return time_util.in_a_while(minutes=timeout, format=tformat)


class Cache(object):
    def __init__(self):
        self.uid2user = {}
        self.cookie_name = "spauthn"
        self.outstanding_queries = {}
        self.relay_state = {}
        self.user = {}
        self.result = {}

    def kaka2user(self, kaka):
        logger.debug("KAKA: %s" % kaka)
        if kaka:
            cookie_obj = SimpleCookie(kaka)
            morsel = cookie_obj.get(self.cookie_name, None)
            if morsel:
                try:
                    return self.uid2user[morsel.value]
                except KeyError:
                    return None
            else:
                logger.debug("No spauthn cookie")
        return None

    def delete_cookie(self, environ=None, kaka=None):
        if not kaka:
            kaka = environ.get("HTTP_COOKIE", '')
        logger.debug("delete KAKA: %s" % kaka)
        if kaka:
            _name = self.cookie_name
            cookie_obj = SimpleCookie(kaka)
            morsel = cookie_obj.get(_name, None)
            cookie = SimpleCookie()
            cookie[_name] = ""
            cookie[_name]['path'] = "/"
            logger.debug("Expire: %s" % morsel)
            cookie[_name]["expires"] = _expiration("dawn")
            return tuple(cookie.output().split(": ", 1))
        return None

    def user2kaka(self, user):
        uid = rndstr(32)
        self.uid2user[uid] = user
        cookie = SimpleCookie()
        cookie[self.cookie_name] = uid
        cookie[self.cookie_name]['path'] = "/"
        cookie[self.cookie_name]["expires"] = _expiration(480)
        logger.debug("Cookie expires: %s" % cookie[self.cookie_name]["expires"])
        return tuple(cookie.output().split(": ", 1))


# -----------------------------------------------------------------------------
# RECEIVERS
# -----------------------------------------------------------------------------


class Service(object):
    def __init__(self, environ, start_response, user=None):
        self.environ = environ
        logger.debug("ENVIRON: %s" % environ)
        self.start_response = start_response
        self.user = user
        self.sp = None

    def unpack_redirect(self):
        if "QUERY_STRING" in self.environ:
            _qs = self.environ["QUERY_STRING"]
            return dict([(k, v[0]) for k, v in parse_qs(_qs).items()])
        else:
            return None

    def unpack_post(self):
        _dict = parse_qs(get_post(self.environ))
        logger.debug("unpack_post:: %s" % _dict)
        try:
            return dict([(k, v[0]) for k, v in _dict.items()])
        except Exception:
            return None

    def unpack_soap(self):
        try:
            query = get_post(self.environ)
            return {"SAMLResponse": query, "RelayState": ""}
        except Exception:
            return None

    def unpack_either(self):
        if self.environ["REQUEST_METHOD"] == "GET":
            _dict = self.unpack_redirect()
        elif self.environ["REQUEST_METHOD"] == "POST":
            _dict = self.unpack_post()
        else:
            _dict = None
        logger.debug("_dict: %s" % _dict)
        return _dict

    def operation(self, _dict, binding):
        logger.debug("_operation: %s" % _dict)
        if not _dict:
            resp = BadRequest('Error parsing request or no request')
            return resp(self.environ, self.start_response)
        else:
            try:
                _relay_state = _dict["RelayState"]
            except KeyError:
                _relay_state = ""
            if "SAMLResponse" in _dict:
                return self.do(_dict["SAMLResponse"], binding,
                               _relay_state, mtype="response")
            elif "SAMLRequest" in _dict:
                return self.do(_dict["SAMLRequest"], binding,
                               _relay_state, mtype="request")

    def artifact_operation(self, _dict):
        if not _dict:
            resp = BadRequest("Missing query")
            return resp(self.environ, self.start_response)
        else:
            # exchange artifact for response
            request = self.sp.artifact2message(_dict["SAMLart"], "spsso")
            return self.do(request, BINDING_HTTP_ARTIFACT, _dict["RelayState"])

    def response(self, binding, http_args):
        if binding == BINDING_HTTP_ARTIFACT:
            resp = Redirect()
        else:
            resp = Response(http_args["data"], headers=http_args["headers"])
        return resp(self.environ, self.start_response)

    def do(self, query, binding, relay_state="", mtype="response"):
        pass

    def redirect(self):
        """ Expects a HTTP-redirect response """

        _dict = self.unpack_redirect()
        return self.operation(_dict, BINDING_HTTP_REDIRECT)

    def post(self):
        """ Expects a HTTP-POST response """

        _dict = self.unpack_post()
        return self.operation(_dict, BINDING_HTTP_POST)

    def artifact(self):
        # Can be either by HTTP_Redirect or HTTP_POST
        _dict = self.unpack_either()
        return self.artifact_operation(_dict)

    def soap(self):
        """
        Single log out using HTTP_SOAP binding
        """
        logger.debug("- SOAP -")
        _dict = self.unpack_soap()
        logger.debug("_dict: %s" % _dict)
        return self.operation(_dict, BINDING_SOAP)

    def uri(self):
        _dict = self.unpack_either()
        return self.operation(_dict, BINDING_SOAP)

    def not_authn(self):
        resp = Unauthorized('Unknown user')
        return resp(self.environ, self.start_response)


# -----------------------------------------------------------------------------
# Attribute Consuming service
# -----------------------------------------------------------------------------


class ACS(Service):
    def __init__(self, sp, ec_test, environ, start_response, cache=None, **kwargs):
        Service.__init__(self, environ, start_response)
        self.sp = sp
        self.outstanding_queries = cache.outstanding_queries
        self.cache = cache
        self.response = None
        self.kwargs = kwargs
        self.ec_test = ec_test

    def do(self, response, binding, relay_state="", mtype="response"):
        """
        :param response: The SAML response, transport encoded
        :param binding: Which binding the query came in over
        """
        # tmp_outstanding_queries = dict(self.outstanding_queries)
        if not response:
            logger.info("Missing Response")
            resp = Unauthorized('Unknown user')
            return resp(self.environ, self.start_response)

        try:
            self.response = self.sp.parse_authn_request_response(
                response, binding, self.outstanding_queries)
        except UnknownPrincipal, excp:
            logger.error("UnknownPrincipal: %s" % (excp,))
            resp = ServiceError("UnknownPrincipal: %s" % (excp,))
            return resp(self.environ, self.start_response)
        except UnsupportedBinding, excp:
            logger.error("UnsupportedBinding: %s" % (excp,))
            resp = ServiceError("UnsupportedBinding: %s" % (excp,))
            return resp(self.environ, self.start_response)
        except VerificationError, err:
            resp = ServiceError("Verification error: %s" % (err,))
            return resp(self.environ, self.start_response)
        except StatusError, err:
            resp = ServiceError("IdP Status error: %s" % (err,))
            return resp(self.environ, self.start_response)
        except Exception, err:
            resp = ServiceError("Other error: %s" % (err,))
            return resp(self.environ, self.start_response)

        # logger.info("parsed OK")
        _resp = self.response.response

        logger.info("AVA: %s" % self.response.ava)

        _cmp = self.verify_attributes(self.response.ava)
        # Log result to DB
        DB_HANDLER.update_test_result(_resp.issuer.text, self.ec_test, _cmp)

        logger.info(">%s>%s> %s" % (_resp.issuer.text, self.sp.config.entityid,
                                    _cmp))
        reslog.info("#%s#%s#%s" % (_resp.issuer.text, self.sp.config.entityid,
                                   _cmp))
        # _ec = ""
        # for _ec, _sp in SP.items():
        # if _sp == self.sp:
        # break
        # if (re.match('.*/login',
        # tmp_outstanding_queries[_resp.in_response_to])):

        resp = Response(mako_template="check_result.mako",
                        template_lookup=LOOKUP,
                        headers=[])
        argv = {
            "cmp": json.dumps({"data": _cmp})
        }
        return resp(self.environ, self.start_response, **argv)

    def verify_attributes(self, ava):
        logger.info("SP: %s" % self.sp.config.entityid)
        rest = POLICY.get_entity_categories(
            self.sp.config.entityid, self.sp.metadata)
        logger.info("policy: %s" % rest)

        akeys = [k.lower() for k in ava.keys()]

        res = {"less": [], "more": []}
        for key, attr in rest.items():
            if key not in ava:
                if key not in akeys:
                    res["less"].append(key)

        for key, attr in ava.items():
            _key = key.lower()
            if _key not in rest:
                res["more"].append(key)

        return res


# -----------------------------------------------------------------------------
# REQUESTERS
# -----------------------------------------------------------------------------


class SSO(object):
    def __init__(self, sp, environ, start_response, cache=None,
                 wayf=None, discosrv=None, bindings=None):
        self.sp = sp
        self.environ = environ
        self.start_response = start_response
        self.cache = cache
        self.idp_query_param = "IdpQuery"
        self.wayf = wayf
        self.discosrv = discosrv
        if bindings:
            self.bindings = bindings
        else:
            self.bindings = [BINDING_HTTP_REDIRECT, BINDING_HTTP_POST,
                             BINDING_HTTP_ARTIFACT]
        logger.debug("--- SSO ---")

    def response(self, binding, http_args, do_not_start_response=False):
        if binding == BINDING_HTTP_ARTIFACT:
            resp = Redirect()
        elif binding == BINDING_HTTP_REDIRECT:
            for param, value in http_args["headers"]:
                if param == "Location":
                    resp = SeeOther(str(value))
                    break
            else:
                resp = ServiceError("Parameter error")
        else:
            resp = Response(http_args["data"], headers=http_args["headers"])

        if do_not_start_response:
            return resp
        else:
            return resp(self.environ, self.start_response)

    def _wayf_redirect(self, came_from):
        sid_ = sid()
        self.cache.outstanding_queries[sid_] = came_from
        logger.debug("Redirect to WAYF function: %s" % self.wayf)
        return -1, SeeOther(headers=[('Location', "%s?%s" % (self.wayf, sid_))])

    def _pick_idp(self, came_from):
        """
        If more than one idp and if none is selected, I have to do wayf or
        disco
        """

        _cli = self.sp

        logger.debug("[_pick_idp] %s" % self.environ)
        if "HTTP_PAOS" in self.environ:
            if self.environ["HTTP_PAOS"] == PAOS_HEADER_INFO:
                if 'application/vnd.paos+xml' in self.environ["HTTP_ACCEPT"]:
                    # Where should I redirect the user to
                    # entityid -> the IdP to use
                    # relay_state -> when back from authentication

                    logger.debug("- ECP client detected -")

                    _rstate = rndstr()
                    self.cache.relay_state[_rstate] = geturl(self.environ)
                    _entityid = _cli.config.ecp_endpoint(
                        self.environ["REMOTE_ADDR"])

                    if not _entityid:
                        return -1, ServiceError("No IdP to talk to")
                    logger.debug("IdP to talk to: %s" % _entityid)
                    return ecp.ecp_auth_request(_cli, _entityid, _rstate)
                else:
                    return -1, ServiceError('Faulty Accept header')
            else:
                return -1, ServiceError('unknown ECP version')

        # Find all IdPs
        idps = self.sp.metadata.with_descriptor("idpsso")

        idp_entity_id = None

        kaka = self.environ.get("HTTP_COOKIE", '')
        if kaka:
            try:
                (idp_entity_id, _) = parse_cookie("ve_disco", "SEED_SAW", kaka)
            except ValueError:
                pass
            except TypeError:
                pass

        # Any specific IdP specified in a query part
        query = self.environ.get("QUERY_STRING")
        if not idp_entity_id and query:
            try:
                _idp_entity_id = dict(parse_qs(query))[
                    self.idp_query_param][0]
                if _idp_entity_id in idps:
                    idp_entity_id = _idp_entity_id
            except KeyError:
                logger.debug("No IdP entity ID in query: %s" % query)
                pass

        if not idp_entity_id:

            if self.wayf:
                if query:
                    try:
                        wayf_selected = dict(parse_qs(query))[
                            "wayf_selected"][0]
                    except KeyError:
                        return self._wayf_redirect(came_from)
                    idp_entity_id = wayf_selected
                else:
                    return self._wayf_redirect(came_from)
            elif self.discosrv:
                if query:
                    idp_entity_id = _cli.parse_discovery_service_response(
                        query=self.environ.get("QUERY_STRING"))
                if not idp_entity_id:
                    sid_ = sid()
                    self.cache.outstanding_queries[sid_] = came_from
                    logger.debug("Redirect to Discovery Service function")
                    eid = _cli.config.entityid
                    ret = _cli.config.getattr("endpoints",
                                              "sp")["discovery_response"][0][0]
                    ret += "?sid=%s" % sid_
                    loc = _cli.create_discovery_service_request(
                        self.discosrv, eid, **{"return": ret})
                    return -1, SeeOther(loc)
            elif len(idps) == 1:
                # idps is a dictionary
                idp_entity_id = idps.keys()[0]
            elif not len(idps):
                return -1, ServiceError('Misconfiguration')
            else:
                return -1, NotImplemented("No WAYF or DS present!")

        logger.info("Chosen IdP: '%s'" % idp_entity_id)
        return 0, idp_entity_id

    def _redirect_to_auth(self, _cli, entity_id, came_from, vorg_name=""):
        try:
            _binding, destination = _cli.pick_binding(
                "single_sign_on_service", self.bindings, "idpsso",
                entity_id=entity_id)
            logger.debug("binding: %s, destination: %s" % (_binding,
                                                           destination))
            id, req = _cli.create_authn_request(destination, vorg=vorg_name)
            _rstate = rndstr()
            self.cache.relay_state[_rstate] = came_from
            ht_args = _cli.apply_binding(_binding, "%s" % (req,), destination,
                                         relay_state=_rstate)
            _sid = req.id
            logger.debug("ht_args: %s" % ht_args)
        except Exception, exc:
            logger.exception(exc)
            resp = ServiceError(
                "Failed to construct the AuthnRequest: %s" % exc)
            return resp(self.environ, self.start_response)

        # remember the request
        self.cache.outstanding_queries[_sid] = came_from
        return self.response(_binding, ht_args, do_not_start_response=True)

    def do(self):
        _cli = self.sp

        # Which page was accessed to get here
        came_from = geturl(self.environ)
        logger.debug("[sp.challenge] RelayState >> '%s'" % came_from)

        # Am I part of a virtual organization or more than one ?
        try:
            vorg_name = _cli.vorg._name
        except AttributeError:
            vorg_name = ""

        logger.debug("[sp.challenge] VO: %s" % vorg_name)

        # If more than one idp and if none is selected, I have to do wayf
        (done, response) = self._pick_idp(came_from)
        # Three cases: -1 something went wrong or Discovery service used
        # 0 I've got an IdP to send a request to
        # >0 ECP in progress
        logger.debug("_idp_pick returned: %s" % done)
        if done == -1:
            return response(self.environ, self.start_response)
        elif done > 0:
            self.cache.outstanding_queries[done] = came_from
            return ECP_response(response)
        else:
            entity_id = response
            # Do the AuthnRequest
            resp = self._redirect_to_auth(_cli, entity_id, came_from, vorg_name)
            return resp(self.environ, self.start_response)


# ----------------------------------------------------------------------------


# noinspection PyUnusedLocal
def not_found(environ, start_response):
    """Called if no URL matches."""
    resp = NotFound('Not Found')
    return resp(environ, start_response)


# ----------------------------------------------------------------------------


# noinspection PyUnusedLocal
def ecat(environ, start_response, _sp):
    _sso = SSO(_sp, environ, start_response, cache=CACHE, **ARGS)
    return _sso.do()


# noinspection PyUnusedLocal
def verifyLogincookie(environ, start_response, _sp):
    _sso = SSO(_sp, environ, start_response, cache=CACHE, **ARGS)
    return _sso.do()


def disco(environ, start_response, _sp):
    query = parse_qs(environ["QUERY_STRING"])
    entity_id = query["entityID"][0]
    sid = query["sid"][0]
    came_from = CACHE.outstanding_queries[sid]
    _sso = SSO(_sp, environ, start_response, cache=CACHE, **ARGS)
    resp = _sso._redirect_to_auth(_sso.sp, entity_id, came_from)

    # Add cookie
    kaka = make_cookie("ve_disco", entity_id, "SEED_SAW")
    resp.headers.append(kaka)
    return resp(environ, start_response)

# ----------------------------------------------------------------------------

# map urls to functions
urls = [
    # Hmm, place holder, NOT used
    ('place', ("holder", None)),
    (r'^ecat', ecat),
    (r'^login', verifyLogincookie),
    (r'^disco', disco)
]


def add_urls():
    for ec in EC_SEQUENCE:
        if ec == "":
            base = "acs"
        else:
            base = "acs/%s" % ec

        urls.append(("%s/post$" % base, (ACS, "post", SP[ec], ec)))
        urls.append(("%s/post/(.*)$" % base, (ACS, "post", SP[ec], ec)))
        urls.append(("%s/redirect$" % base, (ACS, "redirect", SP[ec], ec)))
        urls.append(("%s/redirect/(.*)$" % base, (ACS, "redirect", SP[ec], ec)))


# ----------------------------------------------------------------------------

class ResultsDBHandler(object):
    """Manager of the database containing all the latest test results for all IdP's.

    The database contains one table with three columns: IdP, TestId and Result.
    When recording a new test result for a specific test and IdP, any previous result is overwritten.
    """

    def __init__(self, db_path, table_name="data"):
        """
        Creates a new manager of the database at the specified path.

        :param db_path location of the database (will be created if it doesn't exist)
        :param table_name optional name of the table containing all results
        """
        self.db_path = db_path
        self.table_name = table_name
        self.idP_column = "IdP"
        self.test_id_column = "TestId"
        self.result_column = "Result"

        con = sqlite.connect(self.db_path)
        cur = con.cursor()
        sql = "CREATE TABLE IF NOT EXISTS {table_name} ({idP}, {test_id}, {result});".format(table_name=self.table_name,
                                                                                             idP=self.idP_column,
                                                                                             test_id=self.test_id_column,
                                                                                             result=self.result_column)
        cur.execute(sql)
        sql = "CREATE UNIQUE INDEX IF NOT EXISTS idx_idp_test ON {table_name} ({idP}, {test_id});".format(
            table_name=self.table_name, idP=self.idP_column, test_id=self.test_id_column)
        cur.execute(sql);
        con.commit()
        con.close()

    def update_test_result(self, idp, test, result):
        """
        Updates the result of an IdP on a test.

        :param idp IdP identifier
        :param test test identifier
        :param result the raw result (as dictionary).
        """
        con = sqlite.connect(self.db_path)
        sql = "REPLACE INTO {table_name} ({idP}, {test_id}, {result}) VALUES (?, ?, ?);".format(
            table_name=self.table_name,
            idP=self.idP_column,
            test_id=self.test_id_column,
            result=self.result_column)

        # Serialize the result
        result = pickle.dumps(result)

        con.cursor().execute(sql, (idp, test, result))
        con.commit()
        con.close()

    def get_overview_data(self):
        """
        Fetch all the latest test results.

        :return: Dictionary containing all results for IdP idp on test t in dict[idp][t]
        """
        con = sqlite.connect(self.db_path)
        sql = "SELECT {idP}, {test_id}, {result} FROM {table_name};".format(table_name=self.table_name,
                                                                            idP=self.idP_column,
                                                                            test_id=self.test_id_column,
                                                                            result=self.result_column)
        result_set = con.cursor().execute(sql).fetchall()
        con.close()

        overview = {}
        for e in result_set:
            idp, test, result = e
            if idp not in overview:
                overview[idp] = {}
            overview[idp][test] = pickle.loads(result)  # Deserialize the result
        return overview


# ----------------------------------------------------------------------------


def application(environ, start_response):
    """
    The main WSGI application. Dispatch the current request to
    the functions from above.

    If nothing matches call the `not_found` function.
    
    :param environ: The HTTP application environment
    :param start_response: The application to run when the handling of the 
        request is done
    :return: The response as a list of lines
    """
    path = environ.get('PATH_INFO', '').lstrip('/')
    logger.info("<application> PATH: '%s'" % path)

    logger.debug("Finding callback to run")
    try:
        for regex, spec in urls:
            match = re.search(regex, path)
            if match is not None:
                if isinstance(spec, tuple):
                    callback, func_name, _sp, ec_test = spec
                    cls = callback(_sp, ec_test, environ, start_response, cache=CACHE)
                    func = getattr(cls, func_name)
                    return func()
                else:
                    query = parse_qs(environ["QUERY_STRING"])
                    if "c" in query:
                        ecs = query["c"][0]
                        if ecs in SP:
                            return spec(environ, start_response, SP[ecs])
                    return spec(environ, start_response, SP[''])
        if re.match(".*static/.*", path):
            return handleStatic(environ, start_response, path)
        if re.match(".*test", path) or path == "/" or path == "":
            resp = Response(mako_template="test.mako",
                            template_lookup=LOOKUP,
                            headers=[])

            str_ec_seq = []
            for ec in EC_SEQUENCE:
                str_ec_seq.append(str(ec))

            argv = {
                # "ec_seq_json": json.dumps(EC_SEQUENCE),
                "ec_seq": str_ec_seq,
                "ec_info": EC_INFORMATION
            }
            return resp(environ, start_response, **argv)
        if re.match(".*overview", path):
            resp = Response(mako_template="test_overview.mako",
                            template_lookup=LOOKUP,
                            headers=[])
            str_ec_seq = []
            for ec in EC_SEQUENCE:
                str_ec_seq.append(str(ec))
            argv = {
                # "ec_seq_json": json.dumps(EC_SEQUENCE),
                "ec_seq": json.dumps(str_ec_seq),
                "ec_info": json.dumps(EC_INFORMATION),
                "test_results": json.dumps(DB_HANDLER.get_overview_data())
            }
            return resp(environ, start_response, **argv)
        return not_found(environ, start_response)
    except StatusError, err:
        logging.error("StatusError: %s" % err)
        resp = BadRequest("%s" % err)
        return resp(environ, start_response)
    except Exception, err:
        # _err = exception_trace("RUN", err)
        # logging.error(exception_trace("RUN", _err))
        print >> sys.stderr, err
        resp = ServiceError("%s" % err)
        return resp(environ, start_response)

# ----------------------------------------------------------------------------

PORT = server_conf.PORT
# ------- HTTPS -------
# These should point to relevant files
SERVER_CERT = server_conf.SERVER_CERT
SERVER_KEY = server_conf.SERVER_KEY
# This is of course the certificate chain for the CA that signed
# you cert and all the way up to the top
CERT_CHAIN = server_conf.CERT_CHAIN

DB_HANDLER = ResultsDBHandler(server_conf.DB_PATH)

if __name__ == '__main__':
    from cherrypy import wsgiserver
    from cherrypy.wsgiserver import ssl_pyopenssl

    _parser = argparse.ArgumentParser()
    _parser.add_argument('-d', dest='debug', action='store_true',
                         help="Print debug information")
    _parser.add_argument('-D', dest='discosrv',
                         help="Which disco server to use")
    _parser.add_argument('-s', dest='seed',
                         help="Cookie seed")
    _parser.add_argument('-W', dest='wayf', action='store_true',
                         help="Which WAYF url to use")
    _parser.add_argument("config", help="SAML client config")

    ARGS = {}
    _args = _parser.parse_args()
    if _args.discosrv:
        ARGS["discosrv"] = _args.discosrv
    if _args.wayf:
        ARGS["wayf"] = _args.wayf

    CACHE = Cache()
    CNFBASE = _args.config
    if _args.seed:
        SEED = _args.seed
    else:
        SEED = "SnabbtInspel"

    SP[""] = Saml2Client(config_file="%s" % CNFBASE)
    for variant in EC_SEQUENCE[1:]:
        SP[variant] = Saml2Client(config_file="%s_%s" % (CNFBASE, variant))

    POLICY = server_conf.POLICY

    add_urls()

    SRV = wsgiserver.CherryPyWSGIServer(('0.0.0.0', PORT), application)

    if server_conf.HTTPS:
        SRV.ssl_adapter = ssl_pyopenssl.pyOpenSSLAdapter(SERVER_CERT,
                                                         SERVER_KEY, CERT_CHAIN)
    logger.info("Server starting")
    print "SP listening on port: %s" % PORT
    try:
        SRV.start()
    except KeyboardInterrupt:
        SRV.stop()
