from sqlalchemy.exc import SQLAlchemyError
from app.api_v1.resources import bp
from flask import jsonify, Response, request, url_for, current_app, make_response
import os
from app.models.picture import Picture, PictureFormat
from app.models.product import Product
from app.models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.main.errors import bad_request, error_response


@bp.route('/users/<int:id>/', methods=['GET'])
@jwt_required()
def get_user(id: int) -> Response:
    return jsonify(User.query.get_or_404(id).to_dict())


@bp.route('/users/', methods=['GET'])
@jwt_required()
def get_users() -> Response:
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page, 'resources.get_users')
    return jsonify(data)


@bp.route('/users/<int:id>/followers/', methods=['GET'])
@jwt_required()
def get_followers(id: int) -> Response:
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followers, page, per_page,
                                   'resources.get_followers', id=id)
    return jsonify(data)


@bp.route('/users/<int:id>/followed/', methods=['GET'])
@jwt_required()
def get_followed(id: int) -> Response:
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followed, page, per_page,
                                   'resources.get_followed', id=id)
    return jsonify(data)


@bp.route('/users/follow/<int:id>/', methods=['POST'])
@jwt_required()
def follow(id: int) -> Response:
    user_id = get_jwt_identity()
    if id == user_id:
        return bad_request('You cannot follow yourself!')
    current_user = User.query.get_or_404(user_id)
    user = User.query.get_or_404(id)
    current_user.follow(user)
    db.session.commit()
    return jsonify(user.to_dict())


@bp.route('/users/unfollow/<int:id>/', methods=['POST'])
@jwt_required()
def unfollow(id: int) -> Response:
    user_id = get_jwt_identity()
    if id == user_id:
        return bad_request('You cannot unfollow yourself!')
    current_user = User.query.get_or_404(user_id)
    user = User.query.get_or_404(id)
    current_user.unfollow(user)
    db.session.commit()
    return jsonify(user.to_dict())


@bp.route('/users/', methods=['POST'])
def create_user() -> Response:
    data = request.get_json() or {}
    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('must include username, email and password fields')
    if User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    token = user.get_token()
    response_dict = user.to_dict()
    response_dict['access_token'] = token
    response = jsonify(response_dict)
    response.status_code = 201
    response.headers['Location'] = url_for('resources.get_user', id=user.id)
    return response


@bp.route('/users/login/', methods=['POST'])
def login_user() -> Response:
    data = request.get_json() or {}
    if 'email' not in data or 'password' not in data:
        return bad_request('must include email and password fields')
    user = User.authenticate(email=data['email'], password=data['password'])
    if user:
        token = user.get_token()
        response_dict = user.to_dict()
        response_dict['access_token'] = token
        response = jsonify(response_dict)
        response.headers['Location'] = url_for('resources.get_user', id=user.id)
        return response
    else:
        return error_response(401)


@bp.route('/users/update/', methods=['PUT'])
@jwt_required()
def update_user() -> Response:
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    if 'username' in data and data['username'] != user.username and \
            User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if 'email' in data and data['email'] != user.email and \
            User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user.from_dict(data, new_user=False)
    db.session.commit()
    return jsonify(user.to_dict())


@bp.route('/users/edit_password/', methods=['PUT'])
@jwt_required()
def edit_password() -> Response:
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    if 'current_password' not in data or 'password' not in data:
        return bad_request('must include current_password and password fields')
    if not user.authenticate(email=user.email, password=data['current_password']):
        return bad_request('wrong password')
    user.set_password(data['password'])
    db.session.commit()
    return jsonify(user.to_dict())


@bp.route('/users/delete/', methods=['DELETE'])
@jwt_required()
def delete_user() -> Response:
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    products = Product.query.filter_by(user_id=user_id).all()
    last_picture = Picture.query.filter_by(user_id=user.id).order_by(Picture.id.desc()).first()
    if last_picture:
        last_formats = PictureFormat.query.filter_by(picture_id=last_picture.id).all()
        files_to_remove = [os.path.join(current_app.root_path,
                                        'static/profile_pics', pic_format.filename) for
                           pic_format in last_formats]
        for file_path in files_to_remove:
            os.remove(file_path)
        for pic_format in last_formats:
            db.session.delete(pic_format)
        db.session.delete(last_picture)
    for product in products:
        try:
            last_picture = Picture.query.filter_by(product_id=product.id).order_by(Picture.id.desc()).first()
            if last_picture:
                last_formats = PictureFormat.query.filter_by(picture_id=last_picture.id).all()
                files_to_remove = [os.path.join(current_app.root_path, 'static/product_pics', pic_format.filename) for
                                   pic_format in last_formats]
                for file_path in files_to_remove:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                for pic_format in last_formats:
                    db.session.delete(pic_format)
                db.session.delete(last_picture)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)
        db.session.delete(product)
    try:
        db.session.delete(user)
        db.session.commit()
    except SQLAlchemyError as e:
        return make_response(jsonify({'error': str(e)}), 500)
    return jsonify({'message': 'User has been deleted.'})



