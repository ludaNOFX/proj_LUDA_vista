from __future__ import annotations
from flask import current_app
from flask_sqlalchemy.session import Session
from app import db


class SearchableMixin(object):
    @classmethod
    def before_commit(cls, session: Session) -> None:
        try:
            if not current_app.elasticsearch.ping():  # Проверка доступности Elasticsearch
                print("Cannot connect to Elasticsearch server")
                return
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session: Session) -> None:
        try:
            if not current_app.elasticsearch.ping():  # Проверка доступности Elasticsearch
                print("Cannot connect to Elasticsearch server")
                return
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return
        from app.utils.search import add_to_index, remove_from_index
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                try:
                    add_to_index(obj.__tablename__, obj)
                except ConnectionError:
                    print("There was an error adding an object to the Elasticsearch index")
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                try:
                    add_to_index(obj.__tablename__, obj)
                except ConnectionError:
                    print("There was an error adding an object to the Elasticsearch index")
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                try:
                    remove_from_index(obj.__tablename__, obj)
                except ConnectionError:
                    print("There was an error removing an object from the Elasticsearch index")
        session._changes = None

    @classmethod
    def reindex(cls) -> None:
        from app.utils.search import add_to_index
        for obj in cls.query.all():
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)
