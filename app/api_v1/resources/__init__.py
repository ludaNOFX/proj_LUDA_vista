from flask import Blueprint

bp = Blueprint('resources', __name__)

from app.api_v1.resources import users, products, search, upload_files, errors, reset_password

