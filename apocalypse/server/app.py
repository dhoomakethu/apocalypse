from flask import Flask, request
from flask import render_template
from flask import jsonify
from flask.helpers import send_from_directory
# from flask_triangle.triangle import Triangle

import os
from apocalypse.utils.docker_client import DockerClientException
from apocalypse.utils.logger import init_logger

from apocalypse.app.chaosapp import ChaosApp
from apocalypse.exceptions import NetError

init_logger()
web_app = Flask(__name__, static_url_path="")

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5555))
NETWORK = os.environ.get("NETWORK", "minicloud_default")

chaos_app = ChaosApp(NETWORK)
chaos_app.init_network_emulator()


class AppError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        super(AppError, self).__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv


def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def handle_other_error(error, status_code):
    error = {"error": error.message}
    response = jsonify(error)
    response.status_code = status_code
    return response


def handle_docker_error(error):
    return handle_other_error(error, 500)


@web_app.errorhandler(Exception)
def handle_error(error):
    if isinstance(error, (DockerClientException, NetError)):
        return handle_docker_error(error)
    elif isinstance(error, AppError):
        # return handle_other_error(error)
        return handle_invalid_usage(error)
    else:
        return handle_other_error(error, 500)


@web_app.route("/service_state/<service>", methods=["GET"], )
def service_state(service):
    try:
        args = request.args
        category = args.get("category")
        if category == "network":
            behavior = chaos_app.emulator.network_state(service)
        else:
            behavior = chaos_app.get_service_state(service)
        return jsonify(behavior)
    except (DockerClientException, NetError) as e:
        raise AppError("Error retrieving service state for %s, check if the "
                       "service is running" % service, status_code=500)


@web_app.route("/")
def main():

    context = {
        "services": chaos_app.get_services()
    }

    return render_template("index.html", **context)


@web_app.route("/restore/<service>", methods=["POST"])
def restore(service):
    result = {
        "message": "Success"
    }
    resp = chaos_app.emulator.restore(service)
    if any(resp):
        raise AppError("Error restoring service", status_code=500)
    return jsonify(result)


@web_app.route("/emulate", methods=["POST"])
def emulate():
    req = dict(request.json)
    service = req.get("service")
    event = req.get("event")
    # event_category = req.get("category")
    _emulate = event.pop("name")
    resp = getattr(chaos_app, _emulate)([service], **event)
    if not resp:
        raise AppError(resp, status_code=500)
    req["event"]["name"] = _emulate
    return jsonify(req)


@web_app.route("/refresh", methods=["POST"])
def refresh():
    result = {
        "message": "Success"
    }
    chaos_app.init()
    chaos_app.init_network_emulator()
    context = {
        "services": chaos_app.get_services()
    }
    render_template("index.html", **context)
    return jsonify(result)


@web_app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('templates/css', path)


@web_app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('templates/js', path)


@web_app.route('/images/<path:path>')
def send_images(path):
    return send_from_directory('templates/images', path)


if __name__ == "__main__":
    web_app.run(host=HOST, port=PORT, debug=True)
