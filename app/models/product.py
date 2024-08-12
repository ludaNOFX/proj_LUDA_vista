from datetime import datetime
from typing import Dict, Any
from flask import url_for
from sqlalchemy import func
from app.models.searchable import SearchableMixin
from app import db
from app.models.paginated import PaginatedAPIMixin
from app.models.user import User


cart = db.Table(
    'cart',
    db.Column('user_cart_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'))
)


class Product(PaginatedAPIMixin, SearchableMixin, db.Model):
    __searchable__ = ['name']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String(140), nullable=True)
    price = db.Column(db.DECIMAL(precision=10, scale=2), index=True, nullable=False)
    pictures = db.relationship('Picture', backref='product', lazy='dynamic')
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_purchased = db.Column(db.Boolean, default=False)
    liked = db.relationship(
        'User', secondary=cart,
        primaryjoin=(cart.c.product_id == id),
        secondaryjoin=(cart.c.user_cart_id == User.id),
        backref=db.backref('added_products', lazy='dynamic'), lazy='dynamic')

    def __repr__(self) -> str:
        return f"<Product {self.name}>"

    def is_added(self, user: User) -> bool:
        return self.liked.filter(
            cart.c.user_cart_id == user.id).count() > 0

    def add_to_cart(self, user: User) -> None:
        if not self.is_added(user):
            self.liked.append(user)

    def remove_from_cart(self, user: User) -> None:
        if self.is_added(user):
            self.liked.remove(user)

    def purchase(self) -> bool:
        if not self.is_purchased:
            self.is_purchased = True
            db.session.add(self)
            db.session.commit()
            return True
        return False

    def users_liked(self):
        from app.models.user import User
        return User.query.join(
            cart, (cart.c.user_cart_id == User.id)).filter(
            cart.c.product_id == self.id)

    def to_dict(self) -> Dict[str, Any]:
        picture = self.pictures.first()
        if picture:
            mini_pic_format = picture.formats.filter_by(format='300x300').first()
            pic_format = picture.formats.filter_by(format='500x500').first()
            mini_pic_url = mini_pic_format.filename if mini_pic_format else \
                url_for('static', filename='product_pics/default_pic_product_300x300.png')
            product_pic_url = pic_format.filename if pic_format else \
                url_for('static', filename='product_pics/default_pic_product_500x500.png')
        else:
            mini_pic_url = url_for(
                'static', filename='product_pics/default_pic_product_300x300.png')
            product_pic_url = url_for(
                'static', filename='product_pics/default_pic_product_500x500.png')
        data = {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'timestamp': self.timestamp,
            'description': self.description,
            'is_purchased': self.is_purchased,
            'liked_count': db.session.query(func.count(
                cart.c.user_cart_id)).filter(cart.c.product_id == self.id).scalar(),
            '_links': {
                'self': url_for('resources.get_product', id=self.id),
                'liked_users': url_for('resources.liked_users', id=self.id),
                'avatar_300x300': mini_pic_url,
                'avatar_500x500': product_pic_url,
                'author': url_for('resources.get_user', id=self.user_id)
            }
        }
        return data

    def from_dict(self, data: dict) -> None:
        for field in ['name', 'description', 'price']:
            if field in data:
                setattr(self, field, data[field])




