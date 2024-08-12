from app.api_v1.resources import bp
import os
from sqlalchemy.exc import SQLAlchemyError
from flask import request, jsonify, Response, current_app
from app.models.user import User
from app.models.product import Product
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.picture import Picture, PictureFormat
from app import db
from app.main.errors import error_response
from app.utils.image_helper import save_picture, check_file_size


@bp.route('/upload_files/users/', methods=['POST'])
@jwt_required()
def upload_pic_user() -> Response:
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    file = request.files['file']
    file = check_file_size(file)
    try:
        last_picture = Picture.query.filter_by(user_id=user.id).order_by(Picture.id.desc()).first()
        if last_picture:
            last_formats = PictureFormat.query.filter_by(picture_id=last_picture.id).all()
            files_to_remove = [os.path.join(current_app.root_path, 'static/profile_pics', pic_format.filename) for
                               pic_format in last_formats]
            for file_path in files_to_remove:
                os.remove(file_path)
            for pic_format in last_formats:
                db.session.delete(pic_format)
            db.session.delete(last_picture)
        save_picture(file, record=user, category='profile',
                         sizes=((50, 50), (450, 450)))
        response = jsonify({'message': 'Image has been uploaded.'})
        response.status_code = 200
        return response
    except SQLAlchemyError as e:
        return error_response(400,
                              f'A database error occurred while deleting product or picture:'
                              f' {str(e)}')
    except OSError as e:
        return error_response(
            400, f'An error occurred while deleting picture files: {str(e)}')


@bp.route('/upload_files/products/<int:id>/', methods=['POST'])
@jwt_required()
def upload_pic_product(id: int) -> Response:
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    product = Product.query.get_or_404(id)
    if product.user_id != user.id:
        return error_response(
            403, 'You can only delete products that you have created.')
    file = request.files['file']
    file = check_file_size(file)
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
        save_picture(file, record=product, category='product',
                         sizes=((300, 300), (500, 500)))
        response = jsonify({'message': 'Image has been uploaded.'})
        response.status_code = 200
        return response
    except SQLAlchemyError as e:
        return error_response(400,
                              f'A database error occurred while deleting product or picture:'
                              f' {str(e)}')
    except OSError as e:
        return error_response(
            400, f'An error occurred while deleting picture files: {str(e)}')

