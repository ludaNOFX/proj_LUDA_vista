import os
from typing import Tuple
from app import db
from werkzeug.datastructures import FileStorage
from PIL import Image
from flask import current_app, abort
import secrets
from app.models.user import User
from app.models.product import Product
from app.models.picture import Picture, PictureFormat


def save_picture(file_picture: FileStorage, record: User | Product, category: str = 'product',
                 sizes: Tuple[Tuple[int, int], ...] = ((300, 300), (500, 500))) -> Picture:

    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(file_picture.filename)

    picture = Picture(user=record if isinstance(record, User) else None,
                      product=record if isinstance(record, Product) else None)
    try:
        db.session.add(picture)
        db.session.commit()
    except:
        raise Exception("Error saving picture record to database")

    for size in sizes:
        picture_filename = f"{random_hex}_{size[0]}x{size[1]}{file_extension}"
        picture_path = os.path.join(current_app.root_path, 'static', category + '_pics', picture_filename)

        try:
            i = Image.open(file_picture.stream)
            i.thumbnail(size)
            i.save(picture_path)
        except:
            raise Exception("Error processing and saving the image file")

        picture_format = PictureFormat(filename=picture_filename, format=f"{size[0]}x{size[1]}",
                                       picture_id=picture.id)
        try:
            db.session.add(picture_format)
            db.session.commit()
        except:
            raise Exception("Error adding new picture format to the database")

    return picture


def check_file_size(file: FileStorage) -> FileStorage:
    max_size = current_app.config['MAX_SIZE_FILE'] * 1024 * 1024

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0, os.SEEK_SET)

    if file_size > max_size:
        abort(413)
    return file



