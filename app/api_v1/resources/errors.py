from app import db
from flask import Response, request
from werkzeug.exceptions import HTTPException
from app.api_v1.resources import bp
from app.main.errors import error_response


def wants_json_response():
    return request.accept_mimetypes['application/json']


@bp.app_errorhandler(404)
def not_found_error(error: HTTPException) -> Response:
    if wants_json_response():
        return error_response(404)


@bp.app_errorhandler(500)
def internal_error(error: HTTPException) -> Response:
    db.session.rollback()
    if wants_json_response():
        return error_response(500)
