#!/usr/bin/env python3

import os
from argparse import ArgumentParser

import requests
import yaml
from saml2 import BINDING_HTTP_POST
from saml2.client import Saml2Client
from saml2.config import SPConfig
from saml2.extension.idpdisc import BINDING_DISCO
from saml2.md import EntitiesDescriptor
from saml2.mdstore import MetaDataMDX
from saml2.metadata import entity_descriptor, metadata_tostring_fix

from verify_entcat.ec_compare import get_expected_attributes


def build_test_list(configured_tests, text_descriptions, attribute_release_policy):
    tests = {}

    for test_id, test_config in configured_tests.items():
        tests[test_id] = {
            "short_name": test_config["short_name"],
            "descriptions": [text_descriptions[ec] for ec in test_config["entity_category"]],
            "expected_attributes": get_expected_attributes(attribute_release_policy,
                                                           test_config["entity_category"])
        }

    return tests


class HTTPRequester:
    def send(self, url, **kwargs):
        return requests.get(url, **kwargs)


METADATA_FILENAME_TEMPLATE = "{test_id}.xml"


def create_service_providers(configured_tests, verify_entcat_config):
    BASE_SP_CONFIG = {
        "service": {
            "sp": {
                "endpoints": None  # dynamically filled per SP test instance
            },
        },
        "encryption_keypairs": [verify_entcat_config["sp_encryption_keys"]]
    }

    mdx_interface = MetaDataMDX(verify_entcat_config["mdx"])

    SP = {}
    for test_id, test_config in configured_tests.items():
        name = METADATA_FILENAME_TEMPLATE.format(test_id=test_id)
        sp_config_dict = {
            "entityid": "{base}/sp/{name}".format(base=verify_entcat_config["base"], name=name)
        }

        # add common config
        sp_config_dict.update(BASE_SP_CONFIG)
        sp_config_dict["service"]["sp"]["endpoints"] = {
            "assertion_consumer_service": [
                ("{base}/{test_id}/acs/post".format(base=verify_entcat_config["base"],
                                                    test_id=test_id),
                 BINDING_HTTP_POST)],

            "discovery_response": [
                ("{base}/{test_id}/disco".format(base=verify_entcat_config["base"],
                                                 test_id=test_id),
                 BINDING_DISCO)
            ]
        }

        # merge test specific config
        sp_config_dict["entity_category"] = test_config["entity_category"]
        sp_config_dict["service"]["sp"]["required_attributes"] = test_config.get(
            "required_attributes", [])

        # create SP instance
        sp_config = SPConfig().load(sp_config_dict)
        sp_config.metadata = mdx_interface
        SP[test_id] = Saml2Client(sp_config)

    return SP


def create_metadata_from_conf(SP, output_dir):
    def _write_saml_metadata(saml_element, filename):
        """
        :param saml_element: either EntityDescriptor or EntitiesDescriptor
        :param filename: output file
        """
        os.makedirs(output_dir, exist_ok=True)

        xml_namespace = {"xs": "http://www.w3.org/2001/XMLSchema"}
        with open(os.path.join(output_dir, filename), "wb") as f:
            f.write(metadata_tostring_fix(saml_element, xml_namespace))

    entities_descr = EntitiesDescriptor()
    for test_id, sp_instance in SP.items():
        entity_descr = entity_descriptor(sp_instance.config)
        entities_descr.entity_descriptor.append(entity_descr)
        _write_saml_metadata(entity_descr, METADATA_FILENAME_TEMPLATE.format(test_id=test_id))

    _write_saml_metadata(entities_descr, "verify_entcat-providers.xml")


def main():
    parser = ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("-o", dest="output_dir", default=".")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f.read())

    SP = create_service_providers(config["available_tests"], config["verify_entcat_conf"])
    create_metadata_from_conf(SP, args.output_dir)
    print("Metadata created in {}.".format(os.path.abspath(args.output_dir)))


if __name__ == "__main__":
    main()
