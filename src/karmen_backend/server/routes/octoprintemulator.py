import re

from flask import jsonify, request, abort
from flask_cors import cross_origin

from server import app, __version__
from server.database import gcodes
from server.services import files
from server.tasks.analyze_gcode import analyze_gcode
from flask_jwt_extended import decode_token


@app.route("/octoprint-emulator/api/version", methods=["GET", "OPTIONS"])
@cross_origin()
def version():
    token = request.headers.get("x-api-key", None)
    if not token:
        return abort(403)
    try:
        decode_token(token)
    except Exception as e:
        abort(403)
    return jsonify(
        {"api": "karmen", "text": "OctoPrint emulator by Karmen", "server": __version__}
    )


@app.route("/octoprint-emulator/api/files/local", methods=["POST", "OPTIONS"])
@cross_origin()
def upload():
    token = request.headers.get("x-api-key", None)
    if not token:
        return abort(403)
    user_uuid = None
    try:
        decoded = decode_token(token)
        user_uuid = decoded["identity"]
    except Exception as e:
        abort(403)
    if "file" not in request.files:
        return abort(400)
    incoming = request.files["file"]
    if incoming.filename == "":
        return abort(400)

    if not re.search(r"\.gco(de)?$", incoming.filename):
        return abort(415)
    # TODO set user_uuid to gcode as well
    try:
        saved = files.save(incoming, request.form.get("path", "/"))
        gcode_id = gcodes.add_gcode(
            path=saved["path"],
            filename=saved["filename"],
            display=saved["display"],
            absolute_path=saved["absolute_path"],
            size=saved["size"],
            user_uuid=user_uuid,
        )
        analyze_gcode.delay(gcode_id)
    except (IOError, OSError) as e:
        return abort(e, 500)
    return (
        jsonify(
            {
                "files": {
                    "local": {
                        "name": saved["filename"],
                        "display": saved["display"],
                        "path": saved["absolute_path"],
                        "origin": "local",
                    }
                }
            }
        ),
        201,
    )
