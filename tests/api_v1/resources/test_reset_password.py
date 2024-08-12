from flask import url_for, jsonify
from flask.testing import FlaskClient
from tests.conftest import test_client, create_product, test_app, new_db, session, \
    create_user
from app.models.user import User


def test_reset_password_request(create_user: User, test_client: FlaskClient):
    user = create_user

    data = {
        'email': user.email
    }

    response = test_client.post(
        url_for('resources.reset_password_request'), json=data)

    assert response.status_code == 200

    user_data = response.get_json()

    assert 'token' in user_data


def test_reset_password(create_user: User, test_client: FlaskClient):
    user = create_user

    data = {
        'email': user.email
    }

    response = test_client.post(
        url_for('resources.reset_password_request'), json=data)

    assert response.status_code == 200

    token = response.get_json()['token']

    new_password = 'new_password'
    reset_password_data = {
        'token': token,
        'password': new_password
    }
    response = test_client.post(
        url_for('resources.reset_password'), json=reset_password_data)
    assert response.status_code == 200
    assert response.get_json() == {'message': 'Your password has been reset'}

    user = User.query.get(user.id)
    assert user.check_password_hash(new_password)


