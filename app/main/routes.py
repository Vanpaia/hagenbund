from flask import jsonify, render_template, request, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.main import bp
from app.models import Prediction, Category, User, StockPick, StockUpdate
from app.utils.stocks import search_stock_ticker, get_stock_info

from sqlalchemy import func
from collections import defaultdict


@bp.route('/', methods=['GET'])
@bp.route('/index', methods=['GET'])
@login_required
def index():
    return redirect(url_for('main.prediction_overview'))

@bp.route('/chat', methods=['GET'])
@login_required
def chatroom():
    return render_template('chatroom.html', title='Gentleboys Chatroom', user=current_user)

@bp.route('/live', methods=['GET'])
@login_required
def live_game():
    return render_template('live.html', title='Gentleboys Live Game', user=current_user)

@bp.route('/2026-predictions', methods=['GET'])
@login_required
def prediction_overview():
    predictions = Prediction.query.filter_by(user_id=current_user.id).all()
    stockpicks = StockPick.query.filter_by(user_id=current_user.id).all()
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

    return render_template('make_predictions.html', title='2026 Predictions', predictions=sorted_predictions, stockpicks=stockpicks, progress=counts_dict, name=current_user.user_name)


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
    
    if not stock_info:
        return jsonify({'error': f'Error fetching info for: {data["symbol"]}'}), 400
    pick = StockPick(
        user_id=data.get("user_id", current_user.id),
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
