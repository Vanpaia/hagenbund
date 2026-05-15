from flask import jsonify, request
from flask_login import login_required, current_user
from app import db
from config import Config
from ... import socketio
from app.main import bp
from app.models import Prediction, Category, PredictionConclusion, PredictionConclusionVote, PredictionStatus, User, ConclusionOutcome, ConclusionStatus
from app.utils.signal import send_signal_message
from app.achievements import set_achievement


def create_prediction(data: dict, user_id: int) -> tuple:
    """Create a new prediction"""

    category_raw = data.get("category", None)
    category = Category[category_raw] if category_raw else None
    prediction = Prediction(user_id=user_id, title=data.get("title"), description=data.get("description"), category=category)
    db.session.add(prediction)
    db.session.commit()


    set_achievement(8, current_user.user_name, socketio)

    return jsonify({
        'message': 'Prediction successfully created',
        'id': prediction.id,
        'data': prediction.to_dict()
    }), 200

def fetch_predictions(user_id: int) -> tuple:
    """Fetch all user predictions"""

    predictions = Prediction.query.filter_by(user_id=user_id).all()
    data = []
    for x in predictions:
        data.append(x.to_dict())

    return jsonify({
        'message': 'Search successfull',
        'id': None,
        'data': data
    }), 200

def update_prediction(prediction_id:int, data:dict) -> tuple:
    """Update an existing prediction"""
    prediction = Prediction.query.get_or_404(prediction_id)
    
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

def delete_prediction(prediction_id) -> tuple:
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

def create_conclusion(data: dict) -> tuple:
    """Create a new prediction conclusion"""

    # Validate required fields
    required_fields = ['prediction_id', 'description', 'outcome']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400


    existing = PredictionConclusion.query.filter_by(
        prediction_id=data["prediction_id"], status=ConclusionStatus.ACTIVE
    ).first()
    if existing:
        return jsonify({'error': 'An active conclusion already exists'}), 409

    try:
        outcome_raw = data.get("outcome", None)
        if not outcome_raw:
            return jsonify({'error': 'Outcome value required'}), 400
        outcome = ConclusionOutcome[outcome_raw]
    except KeyError:
        return jsonify({'error': 'Invalid outcome value'}), 400

    conclusion = PredictionConclusion(prediction_id=data.get("prediction_id"), user_id=data.get("user_id", current_user.id), description=data.get("description"), url=data.get("url"), outcome=outcome)
    db.session.add(conclusion)
    db.session.flush()

    vote = PredictionConclusionVote(prediction_conclusion_id=conclusion.id, user_id=data.get("user_id", current_user.id), vote=True)
    db.session.add(vote)

    conclusion.prediction.status = PredictionStatus.VOTING

    db.session.commit()

    if (conclusion.prediction.author.id != conclusion.user_id) and (conclusion.outcome == ConclusionOutcome.FAILED):
        brutus = User.query.get(conclusion.user_id)
        set_achievement(16, brutus.user_name, socketio)

    message = f'Opened Prediction Conclusion!\n\n{current_user.user_name} has claimed the {conclusion.outcome.sentence()} conclusion of the following prediction by {conclusion.prediction.author.user_name}: {conclusion.prediction.title}.\n\nThey support this claim saying: {conclusion.description}. Go cast your vote at https://bund.hagen.social'
    send_signal_message(Config.PHONE_NUMBER, Config.SIGNAL_GROUP, message)

    return jsonify({
        'message': 'Prediction conclusion successfully created',
        'id': conclusion.id,
        'data': conclusion.to_dict()
    }), 201

def fetch_all_conclusions() -> tuple:
    """Fetch all conclusions"""

    conclusions = PredictionConclusion.query.filter_by(status=ConclusionStatus.ACTIVE).all()

    data = []
    for x in conclusions:
        data.append(x.to_dict())

    return jsonify({
        'message': 'Search successfull',
        'id': None,
        'data': data
    }), 200


def fetch_conclusion(id: int) -> tuple:
    """Fetch one conclusion"""

    conclusion = PredictionConclusion.query.filter_by(id=id, status=ConclusionStatus.ACTIVE).first_or_404()

    return jsonify({
        'message': 'Search successfull',
        'id': None,
        'data': conclusion.to_dict()})


def update_conclusion(conclusion_id: int, user_id: int, data: dict) -> tuple:
    
    conclusion = PredictionConclusion.query.get_or_404(conclusion_id)
    if 'status' in data:
        try:
            new_status = ConclusionStatus[data['status']]
        except KeyError:
            return jsonify({'error': 'Invalid status value'}), 400
        
        # only the submitter can cancel
        if new_status == ConclusionStatus.CANCELLED:
            if conclusion.user_id != user_id:
                return jsonify({'error': 'Unauthorized'}), 403
            if conclusion.status != ConclusionStatus.ACTIVE:
                return jsonify({'error': 'Can only cancel an active conclusion'}), 409

            conclusion.status = new_status

    db.session.commit()
    return jsonify({'message': 'Conclusion updated', 'id': conclusion.id}), 200

def create_conclusion_vote(user_id: int, data:dict) -> tuple:
    """Create a new prediction conclusion vote"""
    data = request.get_json()
    user_id=data.get("user_id", current_user.id)

    # Validate required fields
    required_fields = ['prediction_conclusion_id', 'vote']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400


    conclusion = PredictionConclusion.query.filter_by(
        id=data["prediction_conclusion_id"]
    ).first()
 
    if not conclusion:
        return jsonify({'error': 'No active conclusion for this vote exists'}), 400   

    existing = PredictionConclusionVote.query.filter_by(
        prediction_conclusion_id=data["prediction_conclusion_id"], user_id=user_id
    ).first()

    if existing:
        return jsonify({'error': 'A vote for this conclusion already exists'}), 409

    vote = PredictionConclusionVote(prediction_conclusion_id=conclusion.id, user_id=user_id, vote=data.get("vote"))
    db.session.add(vote)
    db.session.flush()
    
    if conclusion.total_in_favour >= Config.VOTE_LIMIT:
        if conclusion.outcome == ConclusionOutcome.SUCCESS:
            if conclusion.prediction.likelihood < 25.0:
                set_achievement(14, conclusion.prediction.author.user_name, socketio)
            achievement_test = Prediction.query.filter_by(status=PredictionStatus.SUCCESS).first()
            if not achievement_test:
                set_achievement(12, conclusion.prediction.author.user_name, socketio)

        if conclusion.outcome == ConclusionOutcome.FAILED:
            set_achievement(13, conclusion.prediction.author.user_name, socketio)

        conclusion.prediction.status = PredictionStatus(conclusion.outcome.value)
        conclusion.status = ConclusionStatus.ACCEPTED

        message = f'Prediction conclusion: {conclusion.outcome.value.upper()}!\n\n{conclusion.prediction.author.user_name} made a prediction worth {conclusion.prediction.points * conclusion.prediction.multiplier } points { conclusion.prediction.status.sentence() }. The group gave a {conclusion.prediction.likelihood}% chance of succeeding to the prediction that: {conclusion.prediction.title}.'
        send_signal_message(Config.PHONE_NUMBER, Config.SIGNAL_GROUP, message)

    elif conclusion.total_against >= Config.VOTE_LIMIT:
        if conclusion.outcome == ConclusionOutcome.FAILED and (conclusion.prediction.author.id != conclusion.user_id):
            omar = User.query.get(conclusion.user_id)
            set_achievement(17, omar.user_name, socketio)
        conclusion.status = ConclusionStatus.REJECTED
        conclusion.prediction.status = PredictionStatus.PENDING

    db.session.commit()

    # Test for Bingo!
    if (conclusion.total_in_favour >= Config.VOTE_LIMIT) and (conclusion.outcome == ConclusionOutcome.SUCCESS):
        horizontal = Prediction.query.filter_by(
            user_id=conclusion.prediction.author.id,
            category=conclusion.prediction.category,
            status=PredictionStatus.SUCCESS
        ).all()
        
        vertical = Prediction.query.filter_by(
            user_id=conclusion.prediction.author.id,
            position=conclusion.prediction.position,
            status=PredictionStatus.SUCCESS
        ).all()

        categories = list(Category)

        diagonal_left = Prediction.query.filter(
            Prediction.user_id == conclusion.prediction.author.id,
            Prediction.status == PredictionStatus.SUCCESS,
            db.or_(
                *[
                    db.and_(
                        Prediction.category == cat,
                        Prediction.position == i + 1
                    )
                    for i, cat in enumerate(categories)
                ]
            )
        ).all()

        diagonal_right = Prediction.query.filter(
            Prediction.user_id == conclusion.prediction.author.id,
            Prediction.status == PredictionStatus.SUCCESS,
            db.or_(
                *[
                    db.and_(
                        Prediction.category == cat,
                        Prediction.position == len(categories) - i
                    )
                    for i, cat in enumerate(categories)
                ]
            )
        ).all()

        if len(horizontal) >= 5:
            set_achievement(18, conclusion.prediction.author.user_name, socketio)
            print("That's a bingo!")
            for prediction in horizontal:
                prediction.multiplier *= 2
            db.session.commit()
        if len(vertical) >= 5:
            set_achievement(18, conclusion.prediction.author.user_name, socketio)
            print("That's a bingo!")
            for prediction in vertical:
                prediction.multiplier *= 2
            db.session.commit()
        if len(diagonal_left) >= 5:
            set_achievement(18, conclusion.prediction.author.user_name, socketio)
            print("That's a bingo!")
            for prediction in diagonal_left:
                prediction.multiplier *= 2
            db.session.commit()
        if len(diagonal_right) >= 5:
            set_achievement(18, conclusion.prediction.author.user_name, socketio)
            print("That's a bingo!")
            for prediction in diagonal_right:
                prediction.multiplier *= 2
            db.session.commit()

    return jsonify({
        'message': 'Prediction conclusion vote successfully created',
        'id': vote.id,
        'data': {'vote': vote.vote, 'status': vote.conclusion.status.value}
    }), 201

def update_conclusion_vote(vote_id):
    """Update an existing prediction conclusion vote"""
    vote = PredictionConclusionVote.query.get_or_404(vote_id)
    data = request.get_json()


    if vote.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
 
    conclusion = PredictionConclusion.query.filter_by(id=vote.prediction_conclusion_id).first()

    # Update fields if provided
    if 'vote' in data:
        vote.vote= data['vote']

    db.session.flush()

    
    if conclusion.total_in_favour >= Config.VOTE_LIMIT:
        if conclusion.outcome == ConclusionOutcome.SUCCESS:
            if conclusion.prediction.likelihood < 25.0:
                set_achievement(14, conclusion.prediction.author.user_name, socketio)
            achievement_test = Prediction.query.filter_by(status=PredictionStatus.SUCCESS).first()
            if not achievement_test:
                set_achievement(12, conclusion.prediction.author.user_name, socketio)
        if conclusion.outcome == ConclusionOutcome.FAILED:
            set_achievement(13, conclusion.prediction.author.user_name, socketio)

        conclusion.prediction.status = PredictionStatus(conclusion.outcome.value)
        conclusion.status = ConclusionStatus.ACCEPTED

        message = f'Prediction conclusion: {conclusion.outcome.value.upper()}!\n\n{conclusion.prediction.author.user_name} made a prediction worth {conclusion.prediction.points * conclusion.prediction.multiplier } points { conclusion.prediction.status.sentence() }. The group gave a {conclusion.prediction.likelihood}% chance of succeeding to the prediction that: {conclusion.prediction.title}.'
        send_signal_message(Config.PHONE_NUMBER, Config.SIGNAL_GROUP, message)


    elif conclusion.total_against >= Config.VOTE_LIMIT:
        if conclusion.outcome == ConclusionOutcome.FAILED and (conclusion.prediction.author.id != conclusion.user_id):
            omar = User.query.get(conclusion.user_id)
            set_achievement(17, omar.user_name, socketio)
        conclusion.status = ConclusionStatus.REJECTED
        conclusion.prediction.status = PredictionStatus.PENDING

    db.session.commit()

    # Test for Bingo!
    if (conclusion.total_in_favour >= Config.VOTE_LIMIT) and (conclusion.outcome == ConclusionOutcome.SUCCESS):
        horizontal = Prediction.query.filter_by(
            user_id=conclusion.prediction.author.id,
            category=conclusion.prediction.category,
            status=PredictionStatus.SUCCESS
        ).all()
        
        vertical = Prediction.query.filter_by(
            user_id=conclusion.prediction.author.id,
            position=conclusion.prediction.position,
            status=PredictionStatus.SUCCESS
        ).all()

        categories = list(Category)

        diagonal_left = Prediction.query.filter(
            Prediction.user_id == conclusion.prediction.author.id,
            Prediction.status == PredictionStatus.SUCCESS,
            db.or_(
                *[
                    db.and_(
                        Prediction.category == cat,
                        Prediction.position == i + 1
                    )
                    for i, cat in enumerate(categories)
                ]
            )
        ).all()

        diagonal_right = Prediction.query.filter(
            Prediction.user_id == conclusion.prediction.author.id,
            Prediction.status == PredictionStatus.SUCCESS,
            db.or_(
                *[
                    db.and_(
                        Prediction.category == cat,
                        Prediction.position == len(categories) - i
                    )
                    for i, cat in enumerate(categories)
                ]
            )
        ).all()

        if len(horizontal) >= 5:
            set_achievement(18, conclusion.prediction.author.user_name, socketio)
            print("That's a bingo!")
            for prediction in horizontal:
                prediction.multiplier *= 2
            db.session.commit()
        if len(vertical) >= 5:
            set_achievement(18, conclusion.prediction.author.user_name, socketio)
            print("That's a bingo!")
            for prediction in vertical:
                prediction.multiplier *= 2
            db.session.commit()
        if len(diagonal_left) >= 5:
            set_achievement(18, conclusion.prediction.author.user_name, socketio)
            print("That's a bingo!")
            for prediction in diagonal_left:
                prediction.multiplier *= 2
            db.session.commit()
        if len(diagonal_right) >= 5:
            set_achievement(18, conclusion.prediction.author.user_name, socketio)
            print("That's a bingo!")
            for prediction in diagonal_right:
                prediction.multiplier *= 2
            db.session.commit()


    return jsonify({
        'message': 'Prediction conclusion vote successfully updated',
        'id': vote.id,
        'data': {'vote': vote.vote, 'status': vote.conclusion.status.value}
    }), 200
