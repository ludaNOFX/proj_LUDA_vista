from typing import List, Tuple
from app import db
from flask import current_app
from app.models.user import User
from app.models.product import Product
from app.models.searchable import SearchableMixin


def add_to_index(index: str, model: SearchableMixin) -> None:
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id, body=payload)


def remove_from_index(index: str, model: SearchableMixin) -> None:
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, id=model.id)


def query_index(
    index: List[str], query: str, page: int, per_page: int
) -> Tuple[List[int], int] | Tuple[List, int]:
    if not current_app.elasticsearch:
        return [], 0
    multiple_index = ",".join(index)
    search = current_app.elasticsearch.search(
        index=multiple_index,
        body={'query': {'multi_match': {'query': query, 'fields': ['*']}},
              'from': (page - 1) * per_page, 'size': per_page})
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']


def search_multiple_models(query: str, page: int, per_page: int) -> Tuple[dict, int]:
    index_names = [User.__tablename__, Product.__tablename__]
    ids, total = query_index(index_names, query, page, per_page)

    results = {}
    if total > 0:
        for index_name in index_names:
            model_class = globals()[index_name.capitalize()]
            when = {}
            for i in range(len(ids)):
                when[ids[i]] = i
            results[index_name] = model_class.query.filter(model_class.id.in_(ids)).order_by(
                db.case(when, value=model_class.id))
    return results, total
