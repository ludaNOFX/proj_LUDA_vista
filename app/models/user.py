from __future__ import annotations
from datetime import datetime, timedelta
from time import time
import jwt
from flask import url_for, current_app
from typing import Dict, Any, Union
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.searchable import SearchableMixin
from app.models.paginated import PaginatedAPIMixin
from sqlalchemy import func
from app import db


followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(SearchableMixin, PaginatedAPIMixin, db.Model):
    __searchable__ = ['username']
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    pictures = db.relationship('Picture', backref='user', lazy='dynamic')
    password_hash = db.Column(db.String(128))
    products = db.relationship('Product', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140), nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def set_password(self, password: str) -> None | str:
        self.password_hash = generate_password_hash(password)
        return self.password_hash

    def check_password_hash(self, password: str) -> bool:
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_email: bool = False) -> Dict[str, Any]:
        from app.models.product import Product, cart
        picture = self.pictures.first()
        if picture:
            mini_pic_format = picture.formats.filter_by(format='50x50').first()
            avatar_pic_format = picture.formats.filter_by(format='450x450').first()
            mini_avatar_url = mini_pic_format.filename if mini_pic_format else \
                url_for('static', filename='profile_pics/default_pic_user_50x50.png')
            avatar_url = avatar_pic_format.filename if avatar_pic_format else \
                url_for('static', filename='profile_pics/default_pic_user_450x450.png')
        else:
            mini_avatar_url = url_for(
                'static', filename='profile_pics/default_pic_user_50x50.png')
            avatar_url = url_for(
                'static', filename='profile_pics/default_pic_user_450x450.png')
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'last_seen': self.last_seen.isoformat() + 'Z',
            'about_me': self.about_me,
            'product_count': db.session.query(
                func.count(Product.id)).filter(Product.user_id == self.id).scalar(),
            'followers_count': db.session.query(func.count(
                followers.c.follower_id)).filter(followers.c.followed_id == self.id).scalar(),
            'followed_count': db.session.query(func.count(
                followers.c.followed_id)).filter(followers.c.follower_id == self.id).scalar(),
            'product_liked_count': db.session.query(func.count(
                cart.c.product_id)).filter(cart.c.user_cart_id == self.id).scalar(),
            '_links': {
                'self': url_for('resources.get_user', id=self.id),
                'followers': url_for('resources.get_followers', id=self.id),
                'followed': url_for('resources.get_followed', id=self.id),
                'products': url_for('resources.get_users_products', id=self.id),
                'avatar_50x50': mini_avatar_url,
                'avatar_450x450': avatar_url
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data: dict, new_user: bool = False) -> None:
        for field in ['username', 'email', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def get_token(self, expires_in: Union[int, float] = 168) -> str:
        expire_delta = timedelta(hours=expires_in)
        token = create_access_token(identity=self.id, expires_delta=expire_delta)
        return token

    @classmethod
    def authenticate(cls, email: str, password: str) -> User:
        user = cls.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            return user

    def follow(self, user: User) -> None:
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user: User) -> None:
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user: User) -> bool:
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def get_reset_password_token(self, expires_in: int = 600) -> str:
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token: str) -> User | None:
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except(jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return
        return User.query.get(id)





    




