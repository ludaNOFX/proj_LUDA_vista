from flask import Flask
import os
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from typing import Type
from flask_jwt_extended import JWTManager
from elasticsearch import Elasticsearch

from config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_class: Type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None

    from app.models import bp as models_bp
    app.register_blueprint(models_bp, url_prefix='/api_v1/models')

    from app.utils import bp as utils_bp
    app.register_blueprint(utils_bp, url_prefix='/api_v1/utils')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp, url_prefix='/api/v1/main')

    from app.api_v1.resources import bp as resources_bp
    app.register_blueprint(resources_bp, url_prefix='/api_v1')

    if not app.debug:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='LUDA_API Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/luda_api.log', maxBytes=10240,
                                           backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('LUDA_API startup')
    return app



