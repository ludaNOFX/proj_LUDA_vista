import pytest

from app.models.user import User
from tests.conftest import create_user, test_app, test_client, new_db, session
from tests.api_v1.resources.conftest import get_token_and_user, create_users
from flask import url_for
from flask.testing import FlaskClient
from sqlalchemy.orm import Session


def test_get_user(test_client: FlaskClient, create_user: User, get_token_and_user: tuple):
    user_id = create_user.id

    headers = {
        'Authorization': f'Bearer {get_token_and_user[0]}'
    }
    response = test_client.get(
        url_for('resources.get_user', id=user_id), headers=headers)

    assert response.status_code == 200
    assert response.get_json()['username'] == create_user.username
    assert response.get_json()['email'] == create_user.email


def test_get_users(test_client: FlaskClient, create_users: list, get_token_and_user: tuple):
    token = get_token_and_user[0]

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = test_client.get(url_for('resources.get_users'), headers=headers)

    assert response.status_code == 200
    assert response.get_json()['_meta']['total_items'] == len(create_users) + 1
    assert len(response.get_json()['items']) == min(len(create_users) + 1, 10)

    if len(create_users) + 1 > 10:
        response = test_client.get(
            url_for('resources.get_users', page=2), headers=headers)
        assert len(response.get_json()['items']) == len(create_users) + 1 - 10


def test_get_followers(
        test_client: FlaskClient, get_token_and_user: tuple, create_users: list, session: Session):
    token, user = get_token_and_user
    headers = {
        'Authorization': f'Bearer {token}'
    }
    for u in create_users:
        u.follow(user)
        session.commit()

    response = test_client.get(
        url_for('resources.get_followers', id=user.id), headers=headers)

    assert response.status_code == 200
    assert response.get_json()['_meta']['total_items'] == len(create_users)
    assert len(response.get_json()['items']) == min(len(create_users), 10)

    if len(create_users) > 10:
        response = test_client.get(
            url_for('resources.get_followers', page=2, id=user.id), headers=headers)
        assert len(response.get_json()['items']) == len(create_users) - 10


def test_get_followed(
        test_client: FlaskClient, get_token_and_user: tuple, create_users: list, session: Session):
    token, user = get_token_and_user
    headers = {
        'Authorization': f'Bearer {token}'
    }
    for u in create_users:
        user.follow(u)
        session.commit()

    response = test_client.get(
        url_for('resources.get_followed', id=user.id), headers=headers)

    assert response.status_code == 200
    assert response.get_json()['_meta']['total_items'] == len(create_users)
    assert len(response.get_json()['items']) == min(len(create_users), 10)


def test_follow(test_client: FlaskClient, get_token_and_user: tuple, session: Session):
    token, user = get_token_and_user
    headers = {
        'Authorization': f'Bearer {token}'
    }
    user2 = User(email='test@mail.ru', username='testuser')
    session.add(user2)
    session.commit()

    response = test_client.post(
        url_for('resources.follow', id=user2.id), headers=headers)

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["username"] == user2.username
    assert json_data["email"] == user2.email


def test_unfollow(test_client: FlaskClient, get_token_and_user: tuple, session: Session):
    token, user = get_token_and_user
    headers = {
        'Authorization': f'Bearer {token}'
    }
    user2 = User(email='test@mail.ru', username='testuser')
    session.add(user2)
    session.commit()

    user.follow(user2)
    session.add(user)
    session.commit()

    assert user.is_following(user2)

    response = test_client.post(
        url_for('resources.unfollow', id=user2.id), headers=headers)

    assert response.status_code == 200

    session.refresh(user)
    assert not user.is_following(user2)


def test_create_user(test_client: FlaskClient, session: Session):
    session.query(User).delete()

    data = {
        'username': 'test_user',
        'email': 'test@example.com',
        'password': 'test_password',
    }
    response = test_client.post(url_for('resources.create_user'), json=data)

    assert response.status_code == 201

    user_data = response.get_json()

    assert user_data['username'] == data['username']
    assert user_data['email'] == data['email']

    assert 'access_token' in user_data


def test_login(test_client: FlaskClient, session: Session):
    session.query(User).delete()
    password = 'test_password'
    data = {
        'username': 'test_user',
        'email': 'test@example.com',
        'password': password,
    }
    response = test_client.post(url_for('resources.create_user'), json=data)

    assert response.status_code == 201

    user_data = response.get_json()

    response = test_client.post(
        url_for('resources.login_user'),
        json={'email': user_data['email'], 'password': password}
    )

    assert response.status_code == 200

    json_data = response.get_json()
    assert 'access_token' in json_data

    headers = {
        'Authorization': f'Bearer {json_data["access_token"]}',
    }

    new_data = {
        'username': 'updated_username',
        'email': 'updated_email@example.com'
    }
    response = test_client.put(
        url_for('resources.update_user'), json=new_data, headers=headers)

    assert response.status_code == 200


def test_update_user(test_client: FlaskClient, get_token_and_user: tuple, session: Session):
    token, user = get_token_and_user
    headers = {
        'Authorization': f'Bearer {token}'
    }
    new_data = {
        'username': 'updated_username',
        'email': 'updated_email@example.com'
    }
    response = test_client.put(
        url_for('resources.update_user'), json=new_data, headers=headers)

    assert response.status_code == 200
    updated_user = response.get_json()

    assert updated_user["username"] == new_data["username"]
    assert updated_user["email"] == new_data["email"]

    db_user = User.query.get(user.id)
    assert db_user.to_dict() == updated_user


def test_edit_password(test_client: FlaskClient, get_token_and_user: tuple, session: Session):
    token, user = get_token_and_user
    headers = {
        'Authorization': f'Bearer {token}'
    }

    user.set_password('current_password')
    session.commit()

    current_password = 'current_password'
    new_password = 'new_password'
    password_data = {
        'current_password': current_password,
        'password': new_password,
    }

    response = test_client.put(
        url_for('resources.edit_password'), json=password_data, headers=headers)

    assert response.status_code == 200

    updated_user = response.get_json()

    response = test_client.post(
        url_for('resources.login_user'),
        json={'email': updated_user['email'], 'password': new_password}
    )

    assert response.status_code == 200

    json_data = response.get_json()
    assert 'access_token' in json_data

    headers = {
        'Authorization': f'Bearer {json_data["access_token"]}',
    }

    new_data = {
        'username': 'updated_username',
        'email': 'updated_email@example.com'
    }
    response = test_client.put(
        url_for('resources.update_user'), json=new_data, headers=headers)

    assert response.status_code == 200








