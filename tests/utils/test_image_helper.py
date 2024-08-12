import pytest
from werkzeug.exceptions import RequestEntityTooLarge
from app.models.picture import Picture
from app.utils.image_helper import save_picture, check_file_size
from app.models.user import User
from app.models.product import Product
from tests.conftest import create_product, create_user, session, new_db, test_app
from werkzeug.datastructures import FileStorage
from sqlalchemy.orm import Session
from flask_sqlalchemy import SQLAlchemy
from flask.testing import FlaskClient
from PIL import Image
import io
from pytest_mock import MockerFixture


def test_save_picture(session: Session, mocker: MockerFixture,
                      create_user: User, create_product: Product,
                      new_db: SQLAlchemy,
                      test_app: FlaskClient) -> None:
    mocker.patch('os.path.join', return_value='/path/to/image')
    mocker.patch('PIL.Image.Image.save')
    mocker.patch('sqlalchemy.orm.Session.add')
    mocker.patch('sqlalchemy.orm.Session.commit')

    img = Image.new('RGBA', size=(50, 50), color=(73, 109, 137, 255))

    byte_arr = io.BytesIO()
    img.save(byte_arr, format='PNG')

    mocker.patch('PIL.Image.open', return_value=img)

    user = create_user
    product = create_product

    file_picture = FileStorage(stream=io.BytesIO(b"some image data"), filename='test.jpg')

    category_user = 'user'
    picture = save_picture(file_picture, user, category_user)

    assert isinstance(picture, Picture)
    assert picture.user == user
    assert picture.product is None

    category_product = 'product'
    picture = save_picture(file_picture, product, category_product)

    assert isinstance(picture, Picture)
    assert picture.product == product
    assert picture.user is None


def test_check_file_size_small_file(
        session: Session, mocker: MockerFixture, new_db: SQLAlchemy, test_app: FlaskClient):
    mocked_app = mocker.patch("flask.current_app")
    mocked_app.config = {"MAX_SIZE_FILE": 1}

    file_content = b"1" * 1024 * 500
    file = FileStorage(stream=io.BytesIO(file_content), filename='test')

    assert check_file_size(file) == file


def test_check_file_size_large_file(
        session: Session, mocker: MockerFixture, new_db: SQLAlchemy, test_app: FlaskClient):
    mocked_app = mocker.patch("flask.current_app")
    mocked_app.config = {"MAX_SIZE_FILE": 1}

    file_content = b"1" * 1024 * 1024 * 2
    file = FileStorage(stream=io.BytesIO(file_content), filename='test')

    with pytest.raises(RequestEntityTooLarge):
        check_file_size(file)
