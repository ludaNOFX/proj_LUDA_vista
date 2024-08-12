from app.api_v1.resources import bp
import os
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, Response, request, url_for, current_app, make_response
from app.models.product import Product
from app.models.user import User
from app.models.picture import Picture, PictureFormat
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.main.errors import bad_request, error_response


@bp.route('/products/<int:id>/', methods=['GET'])
@jwt_required()
def get_product(id: int) -> Response:
    return jsonify(Product.query.get_or_404(id).to_dict())


@bp.route('/products/', methods=['GET'])
@jwt_required()
def get_products() -> Response:
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Product.to_collection_dict(
        Product.query, page, per_page, 'resources.get_products')
    return jsonify(data)


@bp.route('/products/user/<int:id>/', methods=['GET'])
@jwt_required()
def get_users_products(id: int) -> Response:
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Product.to_collection_dict(
        Product.query.filter(
            Product.user_id == id).order_by(
            Product.timestamp.desc()), page, per_page,
        'resources.get_users_products', id=id)
    return jsonify(data)


@bp.route('/products/', methods=['POST'])
@jwt_required()
def create_product() -> Response:
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    if 'name' not in data or 'price' not in data:
        return bad_request('must include name and price fields')
    if Product.query.filter_by(name=data['name']).first():
        return bad_request('please use a different name')
    product = Product(author=user)
    product.from_dict(data)
    db.session.add(product)
    db.session.commit()
    response_dict = product.to_dict()
    response = jsonify(response_dict)
    response.status_code = 201
    response.headers['Location'] = url_for('resources.get_product', id=product.id)
    return response


@bp.route('/products/<int:id>/', methods=['DELETE'])
@jwt_required()
def delete_product(id: int) -> Response:
    product = Product.query.get_or_404(id)
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    if product.user_id != user.id:
        return error_response(
            403, 'You can only delete products that you have created.')
    try:
        last_picture = Picture.query.filter_by(product_id=product.id).order_by(Picture.id.desc()).first()
        if last_picture:
            last_formats = PictureFormat.query.filter_by(picture_id=last_picture.id).all()
            files_to_remove = [os.path.join(current_app.root_path, 'static/product_pics', pic_format.filename) for
                               pic_format in last_formats]
            for file_path in files_to_remove:
                os.remove(file_path)
            for pic_format in last_formats:
                db.session.delete(pic_format)
            db.session.delete(last_picture)
        db.session.delete(product)
        db.session.commit()
        response = jsonify({'message': 'Product and associated picture have been deleted.'})
        response.status_code = 200
        return response
    except SQLAlchemyError as e:
        return error_response(400,
                              f'A database error occurred while deleting product or picture:'
                              f' {str(e)}')
    except OSError as e:
        return error_response(
            400, f'An error occurred while deleting picture files: {str(e)}')


@bp.route('/products/update/<int:id>/', methods=['PUT'])
@jwt_required()
def update_product(id: int) -> Response:
    product = Product.query.get_or_404(id)
    user_id = get_jwt_identity()
    if product.user_id != user_id:
        return error_response(
            403, 'You can only update products that you have created.')
    data = request.get_json() or {}
    if 'name' in data and data['name'] != product.name and \
            Product.query.filter_by(name=data['name']).first():
        return bad_request('please use a different username')
    product.from_dict(data)
    db.session.commit()
    return jsonify(product.to_dict())


@bp.route('/products/add_to_cart/<int:id>/', methods=['POST'])
@jwt_required()
def add_to_cart(id: int) -> Response:
    try:
        product = Product.query.get_or_404(id)
        user_id = get_jwt_identity()
        if product.user_id == user_id:
            return error_response(
                403, 'You cannot add your own product.')
        user = User.query.get_or_404(user_id)
        product.add_to_cart(user)
        db.session.commit()
        response = make_response(jsonify({'message': f'You added product {product.name}.'}), 200)
        return response
    except Exception as e:
        return error_response(
            400, f'An error occurred: {str(e)}')


@bp.route('/products/remove_from_cart/<int:id>/', methods=['POST'])
@jwt_required()
def remove_from_cart(id: int) -> Response:
    try:
        product = Product.query.get_or_404(id)
        user_id = get_jwt_identity()
        if product.user_id == user_id:
            return error_response(
                403, 'You cannot remove your own product from the cart.')
        user = User.query.get_or_404(user_id)
        product.remove_from_cart(user)
        db.session.commit()
        response = jsonify({'message': f'You removed product {product.name}.'})
        return response
    except Exception as e:
        return error_response(
            400, f'An error occurred: {str(e)}')


@bp.route('/products/in_cart/', methods=['GET'])
@jwt_required()
def products_in_cart() -> Response:
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    data = Product.to_collection_dict(
        user.added_products.order_by(
            Product.timestamp.desc()), page, per_page, 'resources.products_in_cart')
    return jsonify(data)


@bp.route('products/liked_users/<int:id>/', methods=['GET'])
@jwt_required()
def liked_users(id: int) -> Response:
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    product = Product.query.get_or_404(id)
    data = User.to_collection_dict(
        product.users_liked(), page, per_page, 'resources.liked_users', id=id)
    return jsonify(data)


@bp.route('/products/purchase/<int:id>/', methods=['POST'])
@jwt_required()
def purchase(id: int) -> Response:
    product = Product.query.get_or_404(id)
    user_id = get_jwt_identity()
    if product.user_id == user_id:
        return error_response(
            403, 'You cannot buy your own product.')
    buy = product.purchase()
    if buy:
        db.session.commit()
        return jsonify(product.to_dict())
    else:
        return error_response(
            400, 'product purchased.')




