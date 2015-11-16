import os

import flask
import yaml
from flask import Flask
from flask.templating import render_template
from saml2.httputil import geturl

from verify_entcat.configure import build_test_list, create_service_providers
from verify_entcat.saml import SSO, ACS, DS, RequestCache, ATTRIBUTE_RELEASE_POLICY


def read_config():
    config_file = os.environ.get('VERIFY_ENTCAT_CONFIG', 'config.yml')
    with open(config_file) as f:
        config = yaml.safe_load(f.read())

    return config


config = read_config()

app = Flask(__name__)
app.config.update(dict(
    TESTS=build_test_list(config["available_tests"], config["test_text_descriptions"],
                          ATTRIBUTE_RELEASE_POLICY),
    SP=create_service_providers(config["available_tests"], config["verify_entcat_conf"]),
    DISCOVERY_SERVICE=config["verify_entcat_conf"]["discovery_service"],
    SECRET_KEY=config["verify_entcat_conf"]["secret_key"]
))


@app.route("/")
def index():
    test_results = flask.session.get("test_results", {})
    return render_template("test_list.html", tests=app.config['TESTS'], test_results=test_results)


@app.route("/tests/<test_id>")
def run_test(test_id):
    if "request_cache" not in flask.session:
        flask.session["request_cache"] = RequestCache()

    request_origin = geturl(flask.request.environ)
    redirect = DS(flask.session["request_cache"]).redirect_to_discovery_service(
        app.config['SP'][test_id], app.config['DISCOVERY_SERVICE'], request_origin)

    return redirect


@app.route("/<test_id>/disco")
def disco(test_id):
    # TODO store selected IdP in session and don't redirect to discovery service every time?

    idp_entity_id, request_origin = DS(flask.session["request_cache"]).parse_discovery_response(
        flask.request.args)

    authn_req = SSO(flask.session["request_cache"]).make_authn_request(
        app.config['SP'][test_id], idp_entity_id, request_origin)
    return authn_req


@app.route("/<test_id>/acs/post", methods=["POST"])
def acs(test_id):
    authn_response = flask.request.form["SAMLResponse"]

    test_result = ACS(flask.session["request_cache"]).parse_authn_response(
        app.config['SP'][test_id], authn_response)

    if "test_results" not in flask.session:
        flask.session["test_results"] = {}
    flask.session["test_results"][test_id] = test_result.to_dict()

    # TODO store/update result in database

    return render_template("test_list.html", tests=app.config["TESTS"],
                           test_results=flask.session["test_results"])
