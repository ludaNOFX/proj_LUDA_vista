from decimal import Decimal

from flask.testing import FlaskClient
from sqlalchemy.orm import Session
from app.models.product import Product
from tests.conftest import test_client, create_product, test_app, new_db, session
from tests.api_v1.resources.conftest import get_token_and_user, create_products
from flask import url_for


def test_get_product(create_product: Product, get_token_and_user: tuple, test_client: FlaskClient):
    product = create_product
    headers = {
        'Authorization': f'Bearer {get_token_and_user[0]}'
    }
    response = test_client.get(
        url_for('resources.get_product', id=product.id), headers=headers)

    assert response.status_code == 200
    assert response.get_json()['name'] == create_product.name
    assert response.get_json()['price'] == str(create_product.price)


def test_get_products(test_client: FlaskClient, create_products: list, get_token_and_user: tuple):
    token = get_token_and_user[0]

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = test_client.get(url_for('resources.get_products'), headers=headers)

    assert response.status_code == 200
    assert response.get_json()['_meta']['total_items'] == len(create_products)
    assert len(response.get_json()['items']) == min(len(create_products), 10)

    if len(create_products) > 10:
        response = test_client.get(
            url_for('resources.get_products', page=2), headers=headers)
        assert len(response.get_json()['items']) == len(create_products) - 10


def test_create_product(test_client: FlaskClient, get_token_and_user: tuple):
    token, user = get_token_and_user

    headers = {
        'Authorization': f'Bearer {token}'
    }

    data = {
        'name': 'test_product',
        'price': 1,
    }

    response = test_client.post(
        url_for('resources.create_product'), json=data, headers=headers)

    assert response.status_code == 201

    product_data = response.get_json()

    assert product_data['name'] == data['name']
    assert Decimal(product_data['price']) == Decimal(str(data['price'])).quantize(Decimal('0.00'))


def test_update_product(
        test_client: FlaskClient, get_token_and_user: tuple, session: Session):
    token, user = get_token_and_user

    headers = {
        'Authorization': f'Bearer {token}'
    }

    data = {
        'name': 'test_product',
        'price': 1,
    }

    response = test_client.post(
        url_for('resources.create_product'), json=data, headers=headers)

    assert response.status_code == 201

    resp_data = response.get_json()
    product = Product.query.get(resp_data['id'])

    new_data = {
        'name': 'updated_name',
        'price': 10
    }

    response = test_client.put(
        url_for('resources.update_product', id=product.id), json=new_data, headers=headers)
    assert response.status_code == 200

    updated_product = response.get_json()

    assert updated_product["name"] == new_data["name"]
    assert Decimal(updated_product["price"]) == Decimal(str(new_data['price'])).quantize(Decimal('0.00'))


def test_add_to_cart(
        create_product: Product,
        get_token_and_user: tuple, test_client: FlaskClient, session: Session):
    token, user = get_token_and_user
    product = create_product

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = test_client.post(
        url_for('resources.add_to_cart', id=product.id), headers=headers)

    assert response.status_code == 200
    assert f'You added product {product.name}.' in response.get_json()['message']

    data = {
        'name': 'test_product',
        'price': 1,
    }

    response = test_client.post(
        url_for('resources.create_product'), json=data, headers=headers)

    assert response.status_code == 201

    resp_data = response.get_json()
    product = Product.query.get(resp_data['id'])

    response = test_client.post(url_for('resources.add_to_cart', id=product.id))

    assert response.status_code == 401


def test_remove_from_cart(
        create_product: Product, get_token_and_user: tuple,
        test_client: FlaskClient, session: Session):
    token, user = get_token_and_user
    product = create_product

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = test_client.post(
        url_for('resources.add_to_cart', id=product.id), headers=headers)

    assert response.status_code == 200

    response = test_client.post(
        url_for('resources.remove_from_cart', id=product.id), headers=headers)

    assert response.status_code == 200
    assert f'You removed product {product.name}.' in response.get_json()['message']


def test_products_in_cart(
        create_product: Product, get_token_and_user: tuple,
        test_client: FlaskClient, session: Session):
    token, user = get_token_and_user
    product = create_product

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = test_client.post(
        url_for('resources.add_to_cart', id=product.id), headers=headers)

    assert response.status_code == 200

    response = test_client.get(
        url_for('resources.products_in_cart'), headers=headers)

    assert response.status_code == 200
    assert response.get_json()['_meta']['total_items'] == 1
    assert len(response.get_json()['items']) == min(1, 10)


def test_liked_users(
        create_product: Product, get_token_and_user: tuple,
        test_client: FlaskClient, session: Session):
    token, user = get_token_and_user
    product = create_product

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = test_client.post(
        url_for('resources.add_to_cart', id=product.id), headers=headers)

    assert response.status_code == 200

    response = test_client.get(
        url_for('resources.liked_users', id=product.id), headers=headers)

    assert response.status_code == 200
    assert response.get_json()['_meta']['total_items'] == 1
    assert len(response.get_json()['items']) == min(1, 10)


def test_purchase(
        create_product: Product, get_token_and_user: tuple,
        test_client: FlaskClient, session: Session):
    token, user = get_token_and_user
    product = create_product

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = test_client.post(
        url_for('resources.purchase', id=product.id), headers=headers)

    assert response.status_code == 200

    data = response.get_json()

    assert data['is_purchased'] == True

    data = {
        'name': 'test_product',
        'price': 1,
    }

    response = test_client.post(
        url_for('resources.create_product'), json=data, headers=headers)

    assert response.status_code == 201

    resp_data = response.get_json()
    product = Product.query.get(resp_data['id'])

    response = test_client.post(
        url_for('resources.purchase', id=product.id), headers=headers)

    assert response.status_code == 403

    assert f'You cannot buy your own product.' in response.get_json()['message']
















