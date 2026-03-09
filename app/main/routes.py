from flask import jsonify, render_template, request, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
import app
from .. import socketio
from app.main import bp
from app.models import Prediction, Category, User, StockPick, StockUpdate, PredictionVote, UserAchievement
from app.utils.stocks import search_stock_ticker, get_stock_info
from app.achievements import set_achievement

from sqlalchemy import func
from collections import defaultdict


@bp.route('/', methods=['GET'])
@bp.route('/index', methods=['GET'])
@login_required
def index():
    users = User.query.all()
    investments= sorted(users, key=lambda g: g.total_investment, reverse=True)
    predictions= sorted(users, key=lambda g: g.total_prediction_points, reverse=True)

    return render_template('index.html', title='Gentleboys Clubhouse', user=current_user, investments=investments, predictions=predictions)

@bp.route('/chat', methods=['GET'])
@login_required
def chatroom():
    return render_template('chatroom.html', title='Gentleboys Chatroom', user=current_user)

@bp.route('/profile/<name>', methods=['GET'])
@login_required
def profile(name):
    user = User.query.filter_by(user_name=name).first_or_404()
    stockpicks = StockPick.query.filter_by(user_id=user.id).all()
    achievements = UserAchievement.query.filter_by(user_id=user.id).all()
    sorted_predictions = {}
    total_points = 0 
    total_likelihood = 0 
    count = 0

    for category in Category:
        sorted_predictions[category.name] = Prediction.query.filter_by(
            user_id=user.id, 
            category=category.name
        ).order_by(Prediction.uuid_key).all()
        for x in sorted_predictions[category.name]:
            if x.points:
                total_points += x.points
            if x.likelihood:
                total_likelihood += x.likelihood
                count += 1
    print(sorted_predictions)
    if count > 0:
        total_likelihood = float(total_likelihood/count)

    return render_template('profile.html', user=user, predictions=sorted_predictions, stockpicks=stockpicks, achievements=achievements, total_points=total_points, total_likelihood=total_likelihood)

@bp.route('/api/stocks/search', methods=['POST'])
def search_stocks():
    """Search for a specific stock ticker using an external API"""
    data = request.get_json()

    # Validate required fields
    required_fields = ['keywords']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    result = search_stock_ticker(data.get("keywords"))

    return jsonify({
        'message': 'Stock search sucessful',
        'data': result
    }), 200

@bp.route('/api/predictions', methods=['POST'])
def create_prediction():
    """Create a new prediction"""
    data = request.get_json()

    # Validate required fields
    required_fields = ['title', 'description', 'category']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    prediction = Prediction(user_id=data.get("user_id", current_user.id), title=data.get("title"), description=data.get("description"), category=Category[data.get("category")])
    db.session.add(prediction)
    db.session.commit()


    set_achievement(8, current_user.user_name, socketio)

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
    
    # 1. Capture the data while the object is still "alive" and attached
    prediction_data = prediction.to_dict()
    prediction_id_val = prediction.id
    
    # 2. Perform the deletion
    db.session.delete(prediction)
    db.session.commit()
    
    # 3. Return the captured data
    return jsonify({
        'message': 'Prediction successfully deleted',
        'id': prediction_id_val,
        'data': prediction_data
    }), 200

@bp.route('/api/stockpicks', methods=['POST'])
def create_stockpick():
    """Create a new stockpick"""
    data = request.get_json()

    # Validate required fields
    required_fields = ['symbol']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    stock_info = get_stock_info(data["symbol"])

    user_id = data.get("user_id", current_user.id)
    user = User.query.filter_by(id = user_id).first_or_404()
    
    if not stock_info:
        return jsonify({'error': f'Error fetching info for: {data["symbol"]}'}), 400
    pick = StockPick(
        user_id=user.id,
        symbol=data["symbol"],
        name=stock_info[0]["companyName"],
        currency=stock_info[0]["currency"],
        country=stock_info[0]["country"],
        ceo=stock_info[0]["ceo"],
        exchange_full_name=stock_info[0]["exchangeFullName"],
        exchange=stock_info[0]["exchange"],
        sector=stock_info[0]["sector"],
        industry=stock_info[0]["industry"],
        employees=stock_info[0]["fullTimeEmployees"],
        description=stock_info[0]["description"],
        website=stock_info[0]["website"],
        image=stock_info[0]["image"],
        initial_price=stock_info[0]["price"],
        current_price=stock_info[0]["price"]
    )
    db.session.add(pick)
    db.session.flush()
    update = StockUpdate(
        stock_id=pick.id,
        price=stock_info[0]["price"],
        change=stock_info[0]["change"],
        change_percentage=stock_info[0]["changePercentage"],
        beta=stock_info[0]["beta"],
        market_cap=stock_info[0]["marketCap"],
        volume=stock_info[0]["volume"],
        average_volume=stock_info[0]["averageVolume"]
    )
    db.session.add(update)
    db.session.commit()

    # Set achievements if necessary
    mag_7 = ['Alphabet Inc.', 'Microsoft Corporation', 'Apple Inc.', 'Amazon.com, Inc.', 'Meta Platforms, Inc.', 'NVIDIA Corporation', 'Tesla, Inc.']
    if pick.industry == "Aerospace & Defense":
        set_achievement(5, user.user_name, socketio)
    elif pick.name == 'FiscalNote Holdings, Inc.':
        set_achievement(7, user.user_name, socketio)
    elif pick.name in mag_7:
        set_achievement(6, user.user_name, socketio)

    return jsonify({
        'message': 'Stock successfully added',
        'id': pick.id,
        'data': pick.to_dict()
    }), 200

@bp.route('/api/stockpicks', methods=['GET'])
@login_required
def fetch_stockpicks():
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

@bp.route('/api/stockpicks/<int:stock_id>', methods=['PUT', 'PATCH'])
def update_stockpicks(stock_id):
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

@bp.route('/api/stockpicks/<int:stock_id>', methods=['DELETE'])
def delete_stockpick(stock_id):
    """Delete a prediction"""
    pick = StockPick.query.get_or_404(stock_id)
    db.session.delete(pick)
    db.session.commit()
    
    return jsonify({
        'message': 'Stock successfully deleted',
        'id': pick.id,
        'data': pick.to_dict()
    }), 200

@bp.route('/toggle_flag', methods=['GET'])
@login_required
def toggle_flag():
    """toggle feature flag"""
    app.feature_flag = not app.feature_flag

    return jsonify({
        'message': 'Feature flag succesfully toggled',
        'id': None,
        'data': app.feature_flag,
    }), 200
