import os
import random
import string

import flask
import yaml
from beaker.middleware import SessionMiddleware
from flask import Flask
from flask.globals import g
from flask.sessions import SessionInterface
from flask.templating import render_template
from verify_entcat.configure import build_test_list, create_service_providers
from verify_entcat.result_db import ResultDB
from verify_entcat.saml import SSO, ACS, DS, RequestCache, ATTRIBUTE_RELEASE_POLICY


class BeakerSessionInterface(SessionInterface):
    def open_session(self, app, request):
        session = request.environ['beaker.session']
        return session

    def save_session(self, app, session, response):
        session.save()

def random_string(n=16):
    return ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(n))


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
    SECRET_KEY=config["verify_entcat_conf"].get("secret_key", random_string()),
    RESULT_DB=config["verify_entcat_conf"]["result_db"]
))

session_opts = {
    # TODO can't be server-side due to pyff redirecting to disco endpoint twice
    "session.type": "cookie",
    "session.validate_key": app.config["SECRET_KEY"]
}

app.wsgi_app = SessionMiddleware(app.wsgi_app, session_opts)
app.session_interface = BeakerSessionInterface()


def get_db():
    if not hasattr(g, 'result_db'):
        g.result_db = ResultDB(app.config["RESULT_DB"])
    return g.result_db


@app.route("/")
def index():
    test_results = flask.session.get("test_results", {})
    return render_template("test_list.html", tests=app.config['TESTS'], test_results=test_results)


@app.route("/tests/<test_id>")
def run_test(test_id):
    if "request_cache" not in flask.session:
        flask.session["request_cache"] = RequestCache()

    request_origin = flask.request.url
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

    idp_entity_id, test_result = ACS(flask.session["request_cache"]).parse_authn_response(
        app.config['SP'][test_id], authn_response)

    if "test_results" not in flask.session:
        flask.session["test_results"] = {}
    flask.session["test_results"][test_id] = test_result

    db = get_db()
    test_result.test_id = test_id
    db[idp_entity_id] = test_result

    return render_template("test_list.html", tests=app.config["TESTS"],
                           test_results=flask.session["test_results"])


@app.route("/results_overview")
def results_overview():
    db = get_db()

    results_overview = {}

    for idp_entity_id in db:
        if idp_entity_id not in results_overview:
            results_overview[idp_entity_id] = {}

        for result_entry in db[idp_entity_id]:
            results_overview[idp_entity_id][result_entry.test_id] = result_entry

    return render_template("results_overview.html", tests=app.config["TESTS"],
                           results_overview=results_overview)