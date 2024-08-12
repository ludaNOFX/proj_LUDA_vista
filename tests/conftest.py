from decimal import Decimal
from typing import Iterator
import random
import string
import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.session import Session
from app import create_app, db
from app.models.product import Product
from app.models.user import User
from config import TestConfig


@pytest.fixture(scope='session')
def test_app() -> Flask:
    return create_app(config_class=TestConfig)


@pytest.fixture(scope="function")
def test_client(test_app: Flask) -> Iterator[FlaskClient]:
    with test_app.test_client() as test_client:
        yield test_client


@pytest.fixture(scope="function")
def new_db(test_app: Flask) -> Iterator[SQLAlchemy]:
    with test_app.app_context():
        db.create_all()
        yield db
        db.drop_all()


@pytest.fixture(scope='function')
def session(new_db: SQLAlchemy) -> Iterator[Session]:
    db.session.begin_nested()
    yield db.session
    db.session.rollback()


@pytest.fixture(scope='function')
def create_user(session: Session) -> User:
    username = ''.join(random.choices(string.ascii_letters, k=10))
    email = ''.join(random.choices(string.ascii_letters, k=10)) + "@example.com"

    user = User(username=username, email=email)
    session.add(user)
    session.commit()
    return user


@pytest.fixture(scope='function')
def create_product(session: Session) -> Product:
    user = User(username='AUTHOR', email='author@mail.ru')
    name = ''.join(random.choices(string.ascii_letters, k=10))
    product = Product(name=name, price=1, author=user)
    session.add(product)
    session.commit()
    return product



