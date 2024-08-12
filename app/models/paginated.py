from flask import url_for
from flask_sqlalchemy import BaseQuery
from typing import Any, Dict


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query: BaseQuery, page: int,
                           per_page: int, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        resources = query.paginate(page=page, per_page=per_page, error_out=False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data


