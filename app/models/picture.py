from app import db


class Picture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)

    formats = db.relationship('PictureFormat', backref='picture', lazy='dynamic')  # загрузка форматов по запросу

    def __repr__(self) -> str:
        return f'<Picture {self.id}>'


class PictureFormat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    format = db.Column(db.String(20), nullable=False)  # '50x50', '200x200', '300x300', etc.
    picture_id = db.Column(db.Integer, db.ForeignKey('picture.id'), nullable=False)

    def __repr__(self) -> str:
        return f'<PictureFormat {self.format} for picture {self.picture_id}>'

