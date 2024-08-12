from app.models.user import User
from sqlalchemy.orm import Session
from app.models.product import Product
from tests.conftest import session, create_user, create_product, new_db, test_app
from flask_sqlalchemy import SQLAlchemy
from flask.testing import FlaskClient


def test_to_collection_dict(session: Session, create_user: User,
                            create_product: Product, new_db: SQLAlchemy,
                            test_app: FlaskClient) -> None:

    user = create_user

    data = (
        User.to_collection_dict(
            User.query.filter(
                User.id == user.id), 1, 10, 'resources.get_user', id=user.id))

    assert data['_meta']['page'] == 1
    assert data['_meta']['per_page'] == 10
    assert data['_meta']['total_pages'] == 1
    assert data['_meta']['total_items'] == 1

    assert data['_links']['self']
    assert data['_links']['next'] is None
    assert data['_links']['prev'] is None

    product = create_product

    data = (Product.to_collection_dict(Product.query.filter(
        Product.id == product.id), 1, 10, 'resources.get_product',
        id=user.id))

    assert data['_meta']['page'] == 1
    assert data['_meta']['per_page'] == 10
    assert data['_meta']['total_pages'] == 1
    assert data['_meta']['total_items'] == 1

    assert data['_links']['self']
    assert data['_links']['next'] is None
    assert data['_links']['prev'] is None

