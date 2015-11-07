import logging

from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from saml2.httputil import SeeOther, ServiceError, Response
from saml2.s_utils import rndstr

logger = logging.getLogger(__name__)


class ServiceProviderRequestHandler:
    def do(self, sp):
        raise NotImplementedError()


class SSO(ServiceProviderRequestHandler):
    def __init__(self, idp_entity_id=None, discovery_service_url=None, bindings=None):
        if (idp_entity_id is None and discovery_service_url is None) or (
                        idp_entity_id is not None and discovery_service_url is not None):
            raise ValueError(
                "Specify either a single IdP's entity id or the url to a discovery service.")

        self.entity_id = idp_entity_id
        self.discovery_service_url = discovery_service_url
        if bindings:
            self.bindings = bindings
        else:
            self.bindings = [BINDING_HTTP_REDIRECT, BINDING_HTTP_POST]

    def do(self, sp):
        if self.entity_id:
            return self._make_auth_request(sp, self.entity_id, {})
        elif self.discovery_service_url:
            return self._redirect_to_discovery_service(sp, self.discovery_service_url)

    def _make_auth_request(self, sp, idp_entity_id, session):
        request_binding, destination = sp.pick_binding("single_sign_on_service", self.bindings,
                                                       entity_id=idp_entity_id)
        logger.debug("binding: %s, destination: %s", request_binding, destination)

        id, req = sp.create_authn_request(destination)

        relay_state = rndstr()
        session["relay_state"] = relay_state
        ht_args = dict(
            sp.apply_binding(request_binding, str(req), destination, relay_state=relay_state))

        if request_binding == BINDING_HTTP_REDIRECT:
            headers = dict(ht_args["headers"])
            try:
                return SeeOther(headers["Location"])
            except KeyError:
                return ServiceError("Could not determine IdP HTTP-Redirect SSO Location.")
        elif request_binding == BINDING_HTTP_POST:
            return Response(ht_args["data"], headers=ht_args["headers"])

        return ServiceError("Could not construct authentication request to IdP.")

    def _redirect_to_discovery_service(self, sp, discover_service_url):
        return_to = sp.config.getattr("endpoints", "sp")["discovery_response"][0][0]
        redirect_url = sp.create_discovery_service_request(self.discovery_service_url,
                                                           sp.config.entityid,
                                                           **{"return": return_to})
        logger.debug("Redirect to Discovery Service function: %s", redirect_url)
        return SeeOther(redirect_url)
