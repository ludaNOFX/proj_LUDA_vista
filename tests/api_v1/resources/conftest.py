import random
import string
from typing import Tuple
import pytest
from flask_sqlalchemy.session import Session
from flask import Flask, jsonify, url_for, Response

from app.models.product import Product
from app.models.user import User
from tests.conftest import test_client, session, create_user


@pytest.fixture(scope='function')
def get_token_and_user(session: Session, test_client: Flask, create_user) -> Tuple[str, User]:
    user = create_user
    return user.get_token(), user


@pytest.fixture(scope='function')
def create_users(session: Session, amount: int = 5) -> list:
    users = []
    for _ in range(amount):
        username = ''.join(random.choices(string.ascii_letters, k=10))
        email = ''.join(random.choices(string.ascii_letters, k=10)) + "@example.com"
        user = User(username=username, email=email)
        session.add(user)
        users.append(user)
    session.commit()
    return users


@pytest.fixture(scope='function')
def create_products(session: Session, amount: int = 5) -> list:
    products = []
    for _ in range(amount):
        username = ''.join(random.choices(string.ascii_letters, k=10))
        email = ''.join(random.choices(string.ascii_letters, k=10)) + "@example.com"
        user = User(username=username, email=email)
        session.add(user)
        name = ''.join(random.choices(string.ascii_letters, k=10))
        price = 100
        product = Product(name=name, price=price, author=user)
        session.add(product)
        products.append(product)
    session.commit()
    return products


