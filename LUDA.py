from app import create_app, db
from app.models.user import User
from app.models.product import Product
from app.models.picture import Picture, PictureFormat

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Product': Product, 'Picture': Picture,
            'PictureFormat': PictureFormat}
