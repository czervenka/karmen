import functools
from flask import jsonify, request, abort, make_response
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_claims, get_current_user
from server import app, jwt, __version__
from server.database import users as db_users, local_users as db_local_users, api_tokens


def jwt_requires_role(required_role):
    def jwt_token_decorator(func):
        @functools.wraps(func)
        @jwt_required
        def wrap(*args, **kwargs):
            if request.method == "OPTIONS":
                return func(*args, **kwargs)
            claims = get_jwt_claims()
            role = claims.get("role", None)
            if not role or role != required_role or role != "admin":
                return abort(
                    make_response(
                        jsonify(
                            message="Token does not match the required role of %s"
                            % required_role
                        ),
                        401,
                    )
                )
            # check current situation, the token might be from a role-change or user delete period
            user = get_current_user()
            if not user:
                return abort(make_response("", 401))
            if user["role"] != required_role or role != "admin":
                return abort(
                    make_response(
                        jsonify(
                            message="User does not have the required role of %s or admin"
                            % required_role
                        ),
                        401,
                    )
                )
            return func(*args, **kwargs)

        return wrap

    return jwt_token_decorator


def jwt_force_password_change(func):
    @functools.wraps(func)
    @jwt_required
    def wrap(*args, **kwargs):
        if request.method == "OPTIONS":
            return func(*args, **kwargs)
        claims = get_jwt_claims()
        force_pwd_change = claims.get("force_pwd_change", None)
        user = get_current_user()
        if not user:
            return abort(make_response("", 401))
        if "local" in user["providers"] and force_pwd_change:
            luser = db_local_users.get_local_user(user["uuid"])
            if luser["force_pwd_change"]:
                return abort(
                    make_response(
                        jsonify(message="Password change is enforced on this account!"),
                        401,
                    )
                )
        return func(*args, **kwargs)

    return wrap


@jwt.user_claims_loader
def add_claims_to_access_token(user):
    return {
        "role": user.get("role", "user"),
        "username": user.get("username"),
        "force_pwd_change": user.get("force_pwd_change", False),
    }


@jwt.token_in_blacklist_loader
def check_if_token_revoked(decrypted_token):
    # check only tokens without expiration, this can be extended in
    # the future in exchange for a decreased performance
    if "exp" not in decrypted_token:
        token = api_tokens.get_token(decrypted_token["jti"])
        if token and token["revoked"]:
            return True
    return False


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user["uuid"]


@jwt.user_loader_callback_loader
def user_loader_callback(identity):
    user = db_users.get_by_uuid(identity)
    if user["suspended"]:
        return abort(
            make_response(jsonify(message="This account has been suspended"), 401)
        )
    return user


@app.route("/", methods=["GET"])
@cross_origin()
def index():
    return jsonify(
        {
            "app": "karmen_backend",
            "docs": "https://karmen.readthedocs.io",
            "version": __version__,
        }
    )


import server.routes.gcodes
import server.routes.octoprintemulator
import server.routes.printers
import server.routes.printjobs
import server.routes.settings
import server.routes.tasks

# me has to come before users
import server.routes.users_me
import server.routes.users
