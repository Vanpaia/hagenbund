from flask import jsonify, render_template, request, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.main import bp
from app.models import Prediction, Category, User

from sqlalchemy import func
from collections import defaultdict


@bp.route('/', methods=['GET'])
@bp.route('/index', methods=['GET'])
@login_required
def index():
    return redirect(url_for('main.prediction_overview'))

@bp.route('/2026-predictions', methods=['GET'])
@login_required
def prediction_overview():
    predictions = Prediction.query.filter_by(user_id=current_user.id).all()
    user_ids = [2, 3, 4, 5, 6, 7]

    results = db.session.query(
        Prediction.user_id, 
        func.count(Prediction.id)
    ).filter(Prediction.user_id.in_(user_ids))\
     .group_by(Prediction.user_id)\
     .all()
    counts_dict = {str(user_id): str(count) for user_id, count in results}

    current_app.logger.info(current_user.id)

    sorted_predictions = defaultdict(list)
    for p in predictions:
        sorted_predictions[p.category.name].append(p)
    current_app.logger.info(sorted_predictions)

    return render_template('make_predictions.html', title='2026 Predictions', predictions=sorted_predictions, progress=counts_dict, name=current_user.user_name)


@bp.route('/api/predictions', methods=['POST'])
def create_prediction():
    """Create a new prediction"""
    data = request.get_json()

    # Validate required fields
    required_fields = ['title', 'description', 'category']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    prediction = Prediction(user_id=current_user.id, title=data.get("title"), description=data.get("description"), category=Category[data.get("category")])
    db.session.add(prediction)
    db.session.commit()

    return jsonify({
        'message': 'Prediction successfully created',
        'id': prediction.id,
        'data': prediction.to_dict()
    }), 200

@bp.route('/api/predictions', methods=['GET'])
@login_required
def fetch_predictions():
    """Fetch predictions"""

    #Pulling the data from the URL for further use
    user = current_user
    category = request.args.get('category', None)

    predictions = Prediction.query.filter_by(user_id=user.id).all()
    data = []
    for x in predictions:
        data.append(x.to_dict())

    return jsonify({
        'message': 'Search successfull',
        'id': None,
        'data': data
    }), 200

@bp.route('/api/predictions/<int:prediction_id>', methods=['PUT', 'PATCH'])
def update_project(prediction_id):
    """Update an existing prediction"""
    prediction = Prediction.query.get_or_404(prediction_id)
    data = request.get_json()
    
    # Update fields if provided
    if 'title' in data:
        prediction.title = data['title']
    if 'subtitle' in data:
        prediction.description = data['description']
    if 'category' in data:
        prediction.category = Category[data['category']]
    
    db.session.commit()
    
    return jsonify({
        'message': 'Prediction successfully updated',
        'id': prediction.id,
        'data': prediction.to_dict()
    }), 200

@bp.route('/api/predictions/<int:prediction_id>', methods=['DELETE'])
def delete_project(prediction_id):
    """Delete a prediction"""
    prediction = Prediction.query.get_or_404(prediction_id)
    db.session.delete(prediction)
    db.session.commit()
    
    return jsonify({
        'message': 'Prediction successfully deleted',
        'id': prediction.id,
        'data': prediction.to_dict()
    }), 200
