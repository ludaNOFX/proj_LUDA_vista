from flask_jwt_extended import jwt_required
from app.models.user import User
from app.utils.search import search_multiple_models
from flask import request, jsonify, Response, url_for
from app.api_v1.resources import bp


@bp.route('/search/', methods=['GET'])
@jwt_required()
def search() -> Response:
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    search_results, total = search_multiple_models(query, page, per_page)

    data = {
        'items': [item.to_dict() for item in search_results],
        '_meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': total // per_page,
            'total_items': total
        },
        '_links': {
            'self': url_for('resources.search', page=page, per_page=per_page, q=query),
            'next': url_for('resources.search', page=page + 1,
                            per_page=per_page, q=query) if total > page * per_page else None,
            'prev': url_for('resources.search', page=page - 1, per_page=per_page,
                            q=query) if page > 1 else None
        }
    }

    return jsonify(data)
