from typing import Tuple
from app import db
from app.api_v1.resources import bp
from flask import request, Response, jsonify
from app.main.errors import error_response
from app.models.user import User


@bp.route('/reset_password_request/', methods=['POST'])
def reset_password_request() -> Tuple[Response, int] | Response:
    data = request.get_json() or {}
    user = User.query.filter_by(email=data['email']).first()
    if user:
        token = user.get_reset_password_token()
        return jsonify({'token': token}), 200
    else:
        return error_response(404)


@bp.route('/reset_password/', methods=['POST'])
def reset_password() -> Tuple[Response, int] | Response:
    data = request.get_json() or {}
    token = data.get('token')
    new_password = data.get('password')
    if not token or not new_password:
        return error_response(400, "Token and new password required")

    user = User.verify_reset_password_token(token)
    if not user:
        return error_response(400, "Invalid or expired token")

    user.set_password(new_password)
    db.session.commit()
    return jsonify({'message': 'Your password has been reset'}), 200

