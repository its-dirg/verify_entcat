import logging

from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from saml2.httputil import SeeOther, Response

from entity_category_compare.ec_compare import EntityCategoryComparison

logger = logging.getLogger(__name__)


class ServiceProviderRequestHandler:
    pass


class ServiceProviderRequestHandlerError(Exception):
    pass


class SSO(ServiceProviderRequestHandler):
    def __init__(self, idp_entity_id=None, discovery_service_url=None, bindings=None):
        if (idp_entity_id is None and discovery_service_url is None) or (
                        idp_entity_id is not None and discovery_service_url is not None):
            raise ValueError(
                "Specify either a single IdP's entity id or the url to a discovery service.")

        self.idp_entity_id = idp_entity_id
        self.discovery_service_url = discovery_service_url
        if bindings:
            self.bindings = bindings
        else:
            self.bindings = [BINDING_HTTP_POST, BINDING_HTTP_REDIRECT]

    def do_authn(self, sp):
        if self.idp_entity_id:
            return self.make_authn_request(sp, self.idp_entity_id)
        elif self.discovery_service_url:
            return self.redirect_to_discovery_service(sp, self.discovery_service_url)

    def make_authn_request(self, sp, idp_entity_id):
        request_binding, destination = sp.pick_binding("single_sign_on_service", self.bindings,
                                                       entity_id=idp_entity_id)
        logger.debug("binding: %s, destination: %s", request_binding, destination)

        id, req = sp.create_authn_request(destination)

        ht_args = dict(
            sp.apply_binding(request_binding, str(req), destination))

        if request_binding == BINDING_HTTP_REDIRECT:
            headers = dict(ht_args["headers"])
            return SeeOther(headers["Location"])
        else:  # request_binding == BINDING_HTTP_POST:
            return Response(ht_args["data"], headers=ht_args["headers"])

    def redirect_to_discovery_service(self, sp, discover_service_url):
        return_to = sp.config.getattr("endpoints", "sp")["discovery_response"][0][0]
        redirect_url = sp.create_discovery_service_request(self.discovery_service_url,
                                                           sp.config.entityid,
                                                           **{"return": return_to})
        logger.debug("Redirect to Discovery Service function: %s", redirect_url)
        return SeeOther(redirect_url)


class ACS(ServiceProviderRequestHandler):
    def __init__(self, attribute_release_policy):
        self.entity_category_comparison = EntityCategoryComparison(attribute_release_policy)

    def parse_authn_response(self, sp, auth_response, test_id):
        # parse response
        try:
            saml_response = sp.parse_authn_request_response(auth_response, BINDING_HTTP_POST)
            if not saml_response:
                message = "Could not parse authn response from IdP: {}".format(auth_response)
                logger.error(message)
                raise ServiceProviderRequestHandlerError(message)
        except Exception as e:
            message = "{}: {}".format(type(e).__name__, str(e))
            logger.error("%s: %s", type(e).__name__, str(e))
            raise ServiceProviderRequestHandlerError(message)

        logger.debug("SAML Response: %s", saml_response)
        logger.debug("AVA: %s" % saml_response.ava)

        attribute_diff = self.entity_category_comparison(sp.config.entity_category,
                                                         saml_response.ava)

        # TODO simplify fetching of entity id
        _resp = saml_response.response
        logger.info(">%s>%s> %s", _resp.issuer.text, sp.config.entityid, attribute_diff)

        # TODO store/update result in database
        # TODO render test list with test marked as run with status

        return attribute_diff
