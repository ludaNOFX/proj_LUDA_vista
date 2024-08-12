from sqlalchemy.orm import Session
from app.models.user import User
from app.models.product import Product
from tests.conftest import session, new_db, test_app, create_user, create_product
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy


def test_is_added(session: Session, create_user: User, create_product: Product) -> None:
    user = create_user
    user2 = User(email='test@mail.ru')
    product = create_product
    product.add_to_cart(user)
    session.commit()
    assert product.is_added(user) == True

    assert product.is_added(user2) == False


def test_add_to_cart(session: Session, create_user: User, create_product: Product) -> None:
    user = create_user
    product = create_product

    assert product.is_added(user) is False

    product.add_to_cart(user)
    session.commit()

    assert product.is_added(user) is True

    product.add_to_cart(user)
    session.commit()

    assert product.liked.count() == 1


def test_remove_from_cart(session: Session, create_user: User, create_product: Product) -> None:
    user = create_user
    product = create_product
    assert product.liked.count() == 0

    assert product.is_added(user) is False

    product.add_to_cart(user)
    session.commit()

    assert product.liked.count() == 1

    assert product.is_added(user) is True

    product.remove_from_cart(user)
    session.commit()

    assert product.is_added(user) is False

    assert product.liked.count() == 0


def test_purchase(session: Session, create_product: Product) -> None:
    product = create_product

    assert product.is_purchased == False

    product.purchase()

    assert product.is_purchased == True


def test_users_liked(session: Session, create_product: Product, create_user: User) -> None:
    product = create_product
    user = create_user

    assert product.users_liked().count() == 0

    product.add_to_cart(user)
    session.commit()

    assert product.users_liked().count() == 1


def test_to_dict(session: Session,
                 new_db: SQLAlchemy, test_app: FlaskClient, create_product: Product) -> None:
    with test_app.app_context():
        product = create_product
        product_dict = product.to_dict()

        assert isinstance(product_dict, dict)
        assert 'id' in product_dict
        assert 'name' in product_dict
        assert 'price' in product_dict
        assert 'timestamp' in product_dict
        assert 'description' in product_dict
        assert 'is_purchased' in product_dict
        assert 'liked_count' in product_dict
        assert '_links' in product_dict
        assert product_dict['name'] == product.name
        assert product_dict['price'] == product.price


def test_from_dict(session: Session,
                   new_db: SQLAlchemy, test_app: FlaskClient, create_product: Product) -> None:
    with test_app.app_context():
        product = create_product

        update_data = {
            'name': 'Updated Product',
            'price': 100,
            'description': 'Just an updated test product',
        }

        product.from_dict(update_data)

        assert product.name == 'Updated Product'
        assert product.price == 100
        assert product.description == 'Just an updated test product'

