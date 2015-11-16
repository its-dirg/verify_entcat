import logging

from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from saml2.assertion import Policy
from saml2.httputil import SeeOther

from entity_category_compare.ec_compare import EntityCategoryComparison

logger = logging.getLogger(__name__)


class ServiceProviderRequestHandler:
    pass


class ServiceProviderRequestHandlerError(Exception):
    pass


class SSO(ServiceProviderRequestHandler):
    def __init__(self, outstanding_messages):
        self.outstanding_messages = outstanding_messages

    def make_authn_request(self, sp, idp_entity_id, request_origin):
        destination = self.get_sso_location_for_redirect_binding(sp, idp_entity_id)
        logger.debug("'%s' SSO location: %s", idp_entity_id, destination)

        id, req = sp.create_authn_request(destination)
        self.outstanding_messages[id] = request_origin

        ht_args = sp.apply_binding(BINDING_HTTP_REDIRECT, str(req), destination)
        headers = dict(ht_args["headers"])
        return SeeOther(headers["Location"])

    def redirect_to_discovery_service(self, sp, discovery_service_url):
        return_to = sp.config.getattr("endpoints", "sp")["discovery_response"][0][0]
        redirect_url = sp.create_discovery_service_request(discovery_service_url,
                                                           sp.config.entityid,
                                                           **{"return": return_to})
        logger.debug("Redirect to Discovery Service function: %s", redirect_url)
        return SeeOther(redirect_url)

    def get_sso_location_for_redirect_binding(self, sp, idp_entity_id):
        # only use HTTP-Redirect binding per SAML2int
        sso_locations = sp.metadata.service(idp_entity_id, "idpsso_descriptor",
                                            "single_sign_on_service", BINDING_HTTP_REDIRECT)

        if sso_locations:
            return sso_locations[0]["location"]
        else:
            logger.error("'{}' does not support HTTP-Redirect binding for SSO location.".format(
                idp_entity_id))
            raise ServiceProviderRequestHandlerError(
                "IdP must support HTTP-Redirect binding for SSO location.")


class ACS(ServiceProviderRequestHandler):
    def __init__(self, outstanding_messages):
        self.outstanding_messages = outstanding_messages
        self.entity_category_comparison = EntityCategoryComparison(
            Policy({"default": {"entity_categories": ["refeds", "edugain"]}})
        )

    def parse_authn_response(self, sp, auth_response, test_id):
        # parse response
        try:
            saml_response = sp.parse_authn_request_response(auth_response, BINDING_HTTP_POST)
        except Exception as e:
            message = "{}: {}".format(type(e).__name__, str(e))
            logger.error("%s: %s", type(e).__name__, str(e))
            raise ServiceProviderRequestHandlerError(message)

        if not saml_response:
            message = "Could not parse authn response from IdP: {}".format(auth_response)
            logger.error(message)
            raise ServiceProviderRequestHandlerError(message)

        # Message has been answered
        try:
            del self.outstanding_messages[saml_response.in_response_to]
        except KeyError:
            if not sp.allow_unsolicited:
                raise ServiceProviderRequestHandlerError(
                    "Got unsolicited response with id: '{}'".format(saml_response.in_response_to))

        logger.debug("SAML Response: %s", saml_response)
        logger.debug("AVA: %s" % saml_response.ava)

        attribute_diff = self.entity_category_comparison(sp.config.entity_category,
                                                         saml_response.ava)

        logger.info(">%s>%s> %s", saml_response.response.issuer.text, sp.config.entityid,
                    attribute_diff)

        return attribute_diff


class RequestCache(dict):
    pass
