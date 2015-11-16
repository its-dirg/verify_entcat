import base64
import os
from unittest.mock import Mock
from urllib.parse import urlparse, parse_qsl, quote_plus, parse_qs

import pytest
import responses
from saml2 import server, BINDING_HTTP_POST, BINDING_HTTP_REDIRECT
from saml2.assertion import Policy
from saml2.authn_context import PASSWORD
from saml2.client import Saml2Client
from saml2.config import SPConfig, IdPConfig
from saml2.entity_category.refeds import RESEARCH_AND_SCHOLARSHIP
from saml2.extension.idpdisc import BINDING_DISCO
from saml2.mdstore import MetaDataMDX, SAML_METADATA_CONTENT_TYPE
from saml2.metadata import entity_descriptor
from saml2.saml import NameID, NAMEID_FORMAT_TRANSIENT

from service_provider.saml import SSO, ACS
from service_provider.saml import ServiceProviderRequestHandlerError

SP_BASE = "https://verify_entcat.example.com"


def full_path(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)


def verify_redirect_binding_request(metadata, auth_request):
    redirect_endpoint = urlparse(
        metadata.single_sign_on_service("https://idp.example.com", BINDING_HTTP_REDIRECT)[0][
            "location"])
    redirect_request = urlparse(auth_request.message)

    assert redirect_request.netloc == redirect_endpoint.netloc
    assert redirect_request.path == redirect_endpoint.path

    request_parameters = parse_qs(redirect_request.query)
    assert "SAMLRequest" in request_parameters


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


@pytest.yield_fixture(scope="session")
def sp_config():
    with open(full_path("test_idp.xml")) as f:
        idp_metadata = f.read()

    config = {
        "entityid": "{}/sp.xml".format(SP_BASE),
        "description": "Verify Entity Categories Test SP",
        "entity_category": [RESEARCH_AND_SCHOLARSHIP],
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
    }

    conf = SPConfig().load(config)
    conf.metadata = MetaDataMDX("http://mdx.example.com")

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        url = "http://mdx.example.com/entities/{}".format(
            quote_plus(MetaDataMDX.sha1_entity_transform("https://idp.example.com")))
        rsps.add(responses.GET, url, body=idp_metadata, status=200,
                 content_type=SAML_METADATA_CONTENT_TYPE)
        yield conf


@pytest.fixture(scope="session")
def sp_metadata(sp_config):
    return entity_descriptor(sp_config).to_string()


@pytest.fixture
def sp_instance(sp_config):
    return Saml2Client(config=sp_config)


class TestSSO:
    @pytest.fixture(autouse=True)
    def setup(self, sp_instance):
        self.sp = sp_instance

    def test_automatically_select_idp_by_entity_id(self):
        sso_handler = SSO(idp_entity_id="https://idp.example.com")
        auth_req = sso_handler.do_authn(self.sp)

        verify_redirect_binding_request(self.sp.metadata, auth_req)

    def test_automatically_redirect_to_discovery_service(self):
        sso_handler = SSO(discovery_service_url="https://disco.example.com")
        disco_req = sso_handler.do_authn(self.sp)
        verify_discovery_service_request(self.sp.config, "https://disco.example.com", disco_req)

    def test_rejects_both_entityid_and_disco_url(self):
        with pytest.raises(ValueError):
            SSO(idp_entity_id="foo", discovery_service_url="bar")

    def test_rejects_no_entityid_or_disco_url(self):
        with pytest.raises(ValueError):
            SSO()

    def test_rejects_idp_without_redirect_binding_sso_location(self):
        sso = SSO(idp_entity_id="https://idp.example.com")

        sp = Saml2Client(SPConfig())
        metadata_mock = Mock()
        metadata_mock.service.return_value = []
        sp.metadata = metadata_mock

        with pytest.raises(ServiceProviderRequestHandlerError):
            sso.get_sso_location_for_redirect_binding(sp, "https://idp.example.com")


class TestACS:
    @pytest.fixture(autouse=True)
    def setup(self, sp_instance):
        self.sp = sp_instance
        self.acs = ACS(Policy({"default": {"entity_categories": ["refeds", "edugain"]}}))

    def test_get_result(self, sp_metadata):
        idp = server.Server(config=IdPConfig().load({"metadata": {"inline": [sp_metadata]}}))

        authn_response = idp.create_authn_response({"eduPersonPrincipalName": None,
                                                    "eduPersonScopedAffiliation": None,
                                                    "mail": None,
                                                    "givenName": None, "sn": None,
                                                    "displayName": None},
                                                   in_response_to=None, destination=None,
                                                   sp_entity_id=self.sp.config.entityid,
                                                   issuer="https://idp.example.com",
                                                   name_id=NameID(format=NAMEID_FORMAT_TRANSIENT,
                                                                  sp_name_qualifier=None,
                                                                  name_qualifier=None,
                                                                  text="Tester"),
                                                   authn={"class_ref": PASSWORD})
        saml_response = base64.b64encode(str(authn_response).encode("utf-8"))
        self.sp.allow_unsolicited = True
        test_result = self.acs.parse_authn_response(self.sp, saml_response, "r_s")
        assert test_result.missing_attributes == set(["edupersontargetedid"])

    def test_raises_exception_for_broken_response_xml_from_idp(self, sp_metadata):
        idp = server.Server(config=IdPConfig().load({"metadata": {"inline": [sp_metadata]}}))

        authn_response = idp.create_authn_response({"eduPersonPrincipalName": None,
                                                    "eduPersonScopedAffiliation": None,
                                                    "mail": None,
                                                    "givenName": None, "sn": None,
                                                    "displayName": None},
                                                   in_response_to=None, destination=None,
                                                   sp_entity_id=self.sp.config.entityid,
                                                   issuer="https://idp.example.com",
                                                   name_id=NameID(format=NAMEID_FORMAT_TRANSIENT,
                                                                  sp_name_qualifier=None,
                                                                  name_qualifier=None,
                                                                  text="Tester"),
                                                   authn={"class_ref": PASSWORD})

        saml_response = base64.b64encode((str(authn_response) + "</broken>").encode("utf-8"))
        with pytest.raises(ServiceProviderRequestHandlerError):
            self.acs.parse_authn_response(self.sp, saml_response, "r_s")

    def test_raises_exception_for_broken_response_from_idp(self):
        saml_response = b"abcdef"
        with pytest.raises(ServiceProviderRequestHandlerError):
            self.acs.parse_authn_response(self.sp, saml_response, "r_s")
