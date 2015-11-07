import functools
import os
from unittest.mock import Mock
from urllib.parse import urlparse, parse_qs, parse_qsl

import pytest
from lxml import html
from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from saml2.client import Saml2Client
from saml2.config import SPConfig
from saml2.extension.idpdisc import BINDING_DISCO

from service_provider.saml import SSO

SP_BASE = "https://verify_entcat.example.com"


def full_path(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)


def get_endpoint_by_binding(binding, endpoints):
    for endpoint in endpoints:
        if endpoint["binding"] == binding:
            return endpoint


def verify_redirect_binding_request(idp_sso_endpoints, auth_request):
    redirect_endpoint = urlparse(
        get_endpoint_by_binding(BINDING_HTTP_REDIRECT, idp_sso_endpoints)["location"])
    redirect_request = urlparse(auth_request.message)

    assert redirect_request.netloc == redirect_endpoint.netloc
    assert redirect_request.path == redirect_endpoint.path

    request_parameters = parse_qs(redirect_request.query)
    assert "SAMLRequest" in request_parameters
    assert "RelayState" in request_parameters


def verify_post_binding_request(idp_sso_endpoints, auth_request):
    post_endpoint = urlparse(
        get_endpoint_by_binding(BINDING_HTTP_POST, idp_sso_endpoints)["location"])

    html_page = "".join(auth_request.message)
    form_post = html.document_fromstring(html_page)
    form = form_post.forms[0]

    assert form.action == "{}://{}{}".format(post_endpoint.scheme, post_endpoint.netloc,
                                             post_endpoint.path)
    assert "SAMLRequest" in form.fields
    assert "RelayState" in form.fields


def verify_discovery_service_request(sp_config, discovery_service_url, disco_request):
    entity_id = sp_config.entityid
    discovery_response_endpoint = sp_config._sp_endpoints["discovery_response"][0][0]
    discovery_url = urlparse(discovery_service_url)

    redirect_request = urlparse(disco_request.message)
    assert (redirect_request.scheme, redirect_request.netloc, redirect_request.path) == (
    discovery_url.scheme, discovery_url.netloc, discovery_url.path)

    request_parameters = dict(parse_qsl(redirect_request.query))
    assert request_parameters["entityID"] == entity_id
    assert request_parameters["return"] == discovery_response_endpoint


def single_sign_on_service_mock(sso_element, expected_binding, idp_entity_id, binding,
                                descriptor_type):
    return [sso_element] if binding == sso_element["binding"] else None


@pytest.fixture(scope="session")
def sp_config():
    with open(full_path("test_idp.xml")) as f:
        idp_xml = f.read()

    config = {
        "entityid": "{}/sp.xml".format(SP_BASE),
        "description": "Verify Entity Categories Test SP",
        "service": {
            "sp": {
                "name": "Verify Entity Categories",
                "endpoints": {
                    "assertion_consumer_service": [
                        ("{}/acs/post".format(SP_BASE), BINDING_HTTP_POST)
                    ],
                    "discovery_response": [
                        ("{}/disco".format(SP_BASE), BINDING_DISCO)
                    ]
                }
            },
        },
        "metadata": {
            "inline": [idp_xml],
        },
    }

    return SPConfig().load(config)


class TestSSO:
    @pytest.fixture(autouse=True)
    def create_sp(self, sp_config):
        self.sp = Saml2Client(config=sp_config)
        self.idp_sso_endpoints = \
            self.sp.metadata.metadata[1].entity['https://idp.example.com']['idpsso_descriptor'][0][
                'single_sign_on_service']

    def test_automatically_select_idp_by_entity_id(self):
        sso_handler = SSO(idp_entity_id="https://idp.example.com")
        auth_req = sso_handler.do(self.sp)

        verify_redirect_binding_request(self.idp_sso_endpoints, auth_req)

        redirect_request = urlparse(auth_req.message)
        assert redirect_request.netloc == "idp.example.com"
        assert redirect_request.path == "/SSO/redirect"

        request_parameters = parse_qs(redirect_request.query)
        assert "SAMLRequest" in request_parameters
        assert "RelayState" in request_parameters

    @pytest.mark.parametrize("binding, custom_assert", [
        (BINDING_HTTP_POST, verify_post_binding_request),
        (BINDING_HTTP_REDIRECT, verify_redirect_binding_request)
    ])
    def test_request_binding(self, binding, custom_assert):
        metadata_mock = Mock()
        endpoint = get_endpoint_by_binding(binding, self.idp_sso_endpoints)
        metadata_mock.single_sign_on_service.side_effect = functools.partial(
            single_sign_on_service_mock, endpoint, binding)

        self.sp.metadata = metadata_mock

        sso_handler = SSO(idp_entity_id="https://idp.example.com")
        auth_req = sso_handler.do(self.sp)

        custom_assert(self.idp_sso_endpoints, auth_req)

    def test_redirect_to_discovery_service(self):
        sso_handler = SSO(discovery_service_url="https://disco.example.com")
        disco_req = sso_handler.do(self.sp)
        verify_discovery_service_request(self.sp.config, "https://disco.example.com", disco_req)

    def test_rejects_both_entityid_and_disco_url(self):
        with pytest.raises(ValueError):
            SSO(idp_entity_id="foo", discovery_service_url="bar")

    def test_rejects_no_entityid_or_disco_url(self):
        with pytest.raises(ValueError):
            SSO()
