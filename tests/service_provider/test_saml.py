import base64
import os
from unittest.mock import Mock
from urllib.parse import urlparse, parse_qsl, quote_plus, parse_qs

import pytest
import responses
from saml2 import server, BINDING_HTTP_POST, BINDING_HTTP_REDIRECT
from saml2.authn_context import PASSWORD
from saml2.client import Saml2Client
from saml2.config import SPConfig, IdPConfig
from saml2.entity_category.refeds import RESEARCH_AND_SCHOLARSHIP
from saml2.extension.idpdisc import BINDING_DISCO
from saml2.mdstore import MetaDataMDX, SAML_METADATA_CONTENT_TYPE
from saml2.metadata import entity_descriptor
from saml2.saml import NameID, NAMEID_FORMAT_TRANSIENT

from service_provider.saml import SSO, ACS, RequestCache, DS
from service_provider.saml import ServiceProviderRequestHandlerError

SP_BASE = "https://verify_entcat.example.com"


def full_path(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)


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


@pytest.fixture
def idp_instance(sp_metadata):
    return server.Server(config=IdPConfig().load({

        "metadata": {"inline": [sp_metadata]}
    }))


class TestSSO:
    @pytest.fixture(autouse=True)
    def setup(self, sp_instance):
        self.sp = sp_instance

    def verify_redirect_binding_request(self, metadata, auth_request):
        redirect_endpoint = urlparse(
            metadata.single_sign_on_service("https://idp.example.com", BINDING_HTTP_REDIRECT)[0][
                "location"])
        redirect_request = urlparse(auth_request.message)

        assert redirect_request.netloc == redirect_endpoint.netloc
        assert redirect_request.path == redirect_endpoint.path

        request_parameters = parse_qs(redirect_request.query)
        assert "SAMLRequest" in request_parameters

    def test_make_authn_req(self):
        sso_handler = SSO(RequestCache())
        auth_req = sso_handler.make_authn_request(self.sp, "https://idp.example.com",
                                                  "https://myservice.example.com")
        self.verify_redirect_binding_request(self.sp.metadata, auth_req)

    def test_rejects_idp_without_redirect_binding_sso_location(self):
        sso_handler = SSO(RequestCache())

        sp = Saml2Client(SPConfig())
        metadata_mock = Mock()
        metadata_mock.service.return_value = []
        sp.metadata = metadata_mock

        with pytest.raises(ServiceProviderRequestHandlerError):
            sso_handler.get_sso_location_for_redirect_binding(sp, "https://idp.example.com")

    def test_stores_outgoing_message_id(self, idp_instance):
        request_cache = RequestCache()
        request_origin = "https://someservice.example.com"

        sso_handler = SSO(request_cache)
        auth_req = sso_handler.make_authn_request(self.sp, "https://idp.example.com",
                                                  request_origin)

        redirect_req = urlparse(auth_req.message)
        request_parameters = parse_qs(redirect_req.query)
        saml_req = request_parameters["SAMLRequest"][0]
        parsed_req = idp_instance.parse_authn_request(saml_req)
        assert request_cache[parsed_req.message.id] == request_origin


class TestACS:
    @pytest.fixture(autouse=True)
    def setup(self, sp_instance):
        self.sp = sp_instance
        self.acs = ACS(RequestCache())

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

    def test_raises_exception_for_broken_response_xml_from_idp(self, idp_instance):
        authn_response = idp_instance.create_authn_response({"eduPersonPrincipalName": None,
                                                             "eduPersonScopedAffiliation": None,
                                                             "mail": None,
                                                             "givenName": None, "sn": None,
                                                             "displayName": None},
                                                            in_response_to=None, destination=None,
                                                            sp_entity_id=self.sp.config.entityid,
                                                            issuer="https://idp.example.com",
                                                            name_id=NameID(
                                                                format=NAMEID_FORMAT_TRANSIENT,
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

    def test_removes_answered_message_id(self, idp_instance):
        message_id = "abcdef"
        request_cache = RequestCache()
        request_cache[message_id] = None  # insert fake message in request cache shared with ACS

        authn_response = idp_instance.create_authn_response({},
                                                            in_response_to=message_id,
                                                            destination=None,
                                                            sp_entity_id=self.sp.config.entityid,
                                                            issuer="https://idp.example.com",
                                                            name_id=NameID(
                                                                format=NAMEID_FORMAT_TRANSIENT,
                                                                sp_name_qualifier=None,
                                                                name_qualifier=None,
                                                                text="Tester"),
                                                            authn={"class_ref": PASSWORD})
        saml_response = base64.b64encode(str(authn_response).encode("utf-8"))
        self.sp.allow_unsolicited = True

        acs = ACS(request_cache)
        acs.parse_authn_response(self.sp, saml_response, "r_s")

        assert message_id not in request_cache


class TestDS:
    @pytest.fixture(autouse=True)
    def setup(self, sp_instance):
        self.sp = sp_instance

    def verify_discovery_service_request(self, sp_config, discovery_service_url, disco_request):
        entity_id = sp_config.entityid
        discovery_response_endpoint = sp_config._sp_endpoints["discovery_response"][0][0]
        discovery_url = urlparse(discovery_service_url)

        redirect_request = urlparse(disco_request.message)
        assert (redirect_request.scheme, redirect_request.netloc, redirect_request.path) == (
            discovery_url.scheme, discovery_url.netloc, discovery_url.path)

        request_parameters = dict(parse_qsl(redirect_request.query))
        assert request_parameters["entityID"] == entity_id
        assert request_parameters["return"].startswith(discovery_response_endpoint)

    def test_redirect_to_discovery_service(self):
        ds_handler = DS(RequestCache())
        disco_req = ds_handler.redirect_to_discovery_service(self.sp, "https://disco.example.com",
                                                             "https://myservice.example.com")
        self.verify_discovery_service_request(self.sp.config, "https://disco.example.com",
                                              disco_req)

    def test_stores_requesting_origin(self):
        request_cache = RequestCache()
        ds_handler = DS(request_cache)
        ds_handler.redirect_to_discovery_service(self.sp, "https://disco.example.com",
                                                 "https://myservice.example.com")

        assert len(request_cache) == 1
        assert list(request_cache.values())[0] == "https://myservice.example.com"

    def test_removes_session_id_when_answered(self):
        session_id = "abcdef"
        request_cache = RequestCache()
        request_cache[session_id] = "https://myservice.example.com"
        ds_handler = DS(request_cache)

        response_params = {"entityID": "https://idp.example.com", "sid": session_id}
        idp_entity_id, requesting_origin = ds_handler.parse_discovery_response(response_params)

        assert idp_entity_id == "https://idp.example.com"
        assert requesting_origin == "https://myservice.example.com"
        assert session_id not in request_cache
