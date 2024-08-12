from time import sleep
import pytest
from flask import current_app
from flask_jwt_extended import decode_token
import jwt
from app.models.user import User
from tests.conftest import session, new_db, test_app, create_user, create_product
from sqlalchemy.orm import Session
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy


def test_set_and_check_password() -> None:
    user = User()
    test_password = 'loh'
    user.set_password(test_password)

    assert user.password_hash, "The password hash was not set"
    assert isinstance(user.password_hash, str), "The password hash is not a string"

    assert user.check_password_hash(test_password), "The password was not correctly set or checked"


def test_check_password_hash() -> None:
    user = User()
    test_password = 'loh'
    wrong_password = 'not_loh'
    user.set_password(test_password)

    assert user.check_password_hash(test_password), "Correct password is not verified"
    assert not user.check_password_hash(wrong_password), "Incorrect password is verified"

    user = User()  # new User with no password set yet

    assert not user.check_password_hash(test_password), "Non-set password should fail verification"


def test_to_dict(
        session: Session, new_db: SQLAlchemy, test_app: FlaskClient, create_user: User) -> None:
    with test_app.app_context():
        user = create_user
        user_dict = user.to_dict()

        assert isinstance(user_dict, dict)
        assert 'id' in user_dict
        assert 'username' in user_dict
        assert 'email' in user_dict
        assert 'last_seen' in user_dict
        assert 'about_me' in user_dict
        assert 'product_count' in user_dict
        assert 'followers_count' in user_dict
        assert 'followed_count' in user_dict
        assert 'product_liked_count' in user_dict
        assert '_links' in user_dict
        assert user_dict['username'] == user.username
        assert user_dict['email'] == user.email


def test_from_dict(
        session: Session, new_db: SQLAlchemy, test_app: FlaskClient, create_user: User) -> None:
    with test_app.app_context():
        user = create_user

        update_data = {
            'username': 'Updated User',
            'email': 'updated@example.com',
            'about_me': 'Just an updated test user',
        }

        user.from_dict(update_data)

        assert user.username == 'Updated User'
        assert user.email == 'updated@example.com'
        assert user.about_me == 'Just an updated test user'


def test_get_token(session: Session, create_user: User) -> None:
    user = create_user

    token = user.get_token()
    assert isinstance(token, str)


def test_get_token(session: Session, test_app: FlaskClient, create_user: User) -> None:
    user = create_user

    with test_app.test_request_context():
        token = user.get_token()
        assert isinstance(token, str)

        decoder = decode_token(token)
        assert 'sub' in decoder
        assert decoder['sub'] == user.id


def test_authenticate(session: Session, create_user: User) -> None:
    password = "password"
    user = create_user
    user.set_password(password)

    authenticated_user = User.authenticate(user.email, password)
    assert authenticated_user is not None
    assert authenticated_user.id == user.id

    non_authenticated_user = User.authenticate(user.email, 'wrong_password')
    assert non_authenticated_user is None

    non_existing_user = User.authenticate('wrong_email@example.com', password)
    assert non_existing_user is None


def test_follow(session: Session, create_user: User) -> None:
    user1 = create_user
    user2 = User(email='test@mail.ru', username='testuser')

    assert not user1.is_following(user2)

    user1.follow(user2)
    session.commit()

    assert user1.is_following(user2)


def test_unfollow(session: Session, create_user: User) -> None:
    user1 = create_user
    user2 = User(email='test@mail.ru', username='testuser')
    user1.follow(user2)
    session.commit()

    assert user1.is_following(user2)

    user1.unfollow(user2)

    assert not user1.is_following(user2)


def test_is_following(session: Session, create_user: User) -> None:
    user1 = create_user
    user2 = User(email='test@mail.ru', username='testuser')

    user1.follow(user2)
    session.commit()

    assert user1.is_following(user2) == True
    assert user2.is_following(user1) == False


def test_get_reset_password_token(session: Session, create_user: User) -> None:
    user = create_user
    token = user.get_reset_password_token()

    assert token is not None

    decoded_token = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])

    assert decoded_token is not None
    assert 'reset_password' in decoded_token

    assert decoded_token['reset_password'] == user.id


def test_token_expiry(session: Session, create_user: User) -> None:
    user = create_user
    short_token = user.get_reset_password_token(expires_in=1)

    assert short_token is not None
    sleep(2)

    with pytest.raises(jwt.exceptions.ExpiredSignatureError):
        jwt.decode(short_token, current_app.config['SECRET_KEY'], algorithms=['HS256'])


def test_verify_reset_password_token(session: Session, create_user: User) -> None:
    user = create_user

    token = user.get_reset_password_token()

    assert User.verify_reset_password_token(token) == user

    assert User.verify_reset_password_token("wrong token") is None

    expired_token = user.get_reset_password_token(expires_in=-1)
    assert User.verify_reset_password_token(expired_token) is None




