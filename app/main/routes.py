from flask import jsonify, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.main import bp
from app.models import Prediction, Category, User

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

    sorted_predictions = defaultdict(list)
    for p in predictions:
        sorted_predictions[p.category.name].append(p)
    print(sorted_predictions)

    return render_template('make_predictions.html', title='2026 Predictions', predictions=sorted_predictions, name=current_user.user_name)


@bp.route('/api/predictions', methods=['POST'])
def create_prediction():
    """Create a new prediction"""
    data = request.get_json()

    # Validate required fields
    required_fields = ['title', 'description', 'category']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    user = User.query.filter_by(user_name="Test").first_or_404()

    prediction = Prediction(user_id=user.id, title=data.get("title"), description=data.get("description"), category=Category[data.get("category")])
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

    # Validate required fields
    if not user:
        return jsonify({'error': 'Missing required field: user'}), 400
    print(user)
    
    user = User.query.filter_by(user_name="Test").first_or_404()

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
