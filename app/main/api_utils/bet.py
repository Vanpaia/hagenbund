

@login_required
@bp.route('/api/beer', methods=['POST'])
def create_beer_transaction():
    """Create a new beer transaction"""
    data = request.get_json()

    required_fields = ['creditor_id', 'amount']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    bet_id = data.get("bet_id")
    bet_id = None if bet_id == None else int(bet_id)

    reason = entry.get('reason', '').strip() or None

    ledger_entry = BeerLedger(debtor_id=data.get("debitor_id", current_user.id), creditor_id=data.get("creditor_id"), amount=float(data.get("amount")), bet_id=bet_id, reason=reason)
    db.session.add(ledger_entry)
    db.session.commit()

    return jsonify({
        'message': 'Ledger entry successfully created',
        'id': ledger_entry.id,
        'data': ledger_entry.to_dict()
    }), 200

@login_required
@bp.route('/api/beer/bulk', methods=['POST'])
def create_bulk_beer_transaction():
    """Create bulk beer transactions"""
    data = request.get_json()
    try:
        ids = []
        ledger_data = []

        for i, entry in enumerate(data["data"]):
            required_fields = ['creditor_id', 'amount']
            for field in required_fields:
                if field not in entry:
                    return jsonify({'error': f'Missing required field: {field} in {i}'}), 400


            bet_id = entry.get("bet_id")
            bet_id = None if bet_id == None else int(bet_id)

            reason = entry.get('reason', '').strip() or None

            ledger_entry = BeerLedger(debtor_id=entry.get("debitor_id", current_user.id), creditor_id=entry.get("creditor_id"), amount=float(entry.get("amount")), bet_id=bet_id, reason=reason)
            db.session.add(ledger_entry)
            db.session.flush()
            ids.append(ledger_entry.id)
            ledger_data.append(ledger_entry.to_dict())

        db.session.commit()

        return jsonify({
            'message': 'Ledger entries successfully created',
            'id': ids,
            'data': ledger_data
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({'error': f'{e}'}), 400



@login_required
@bp.route('/api/beer', methods=['GET'])
def fetch_beer_transaction():
    """Fetch a beer transaction"""

    #Pulling the data from the URL for further use
    user = current_user

    beers_debit = BeerLedger.query.filter_by(debitor_id=user.id).all()
    beers_credit = BeerLedger.query.filter_by(creditor_id=user.id).all()
    data = {"total": {"debit": 0, "credit":0}, "debit":[], "credit":[]}
    for x in beers_debit:
        data.debit.append(x.to_dict())
        data.total.debit += x.amount

    for x in beers_credit:
        data.credit.append(x.to_dict())
        data.total.credit += x.amount

    return jsonify({
        'message': 'Search successfull',
        'id': None,
        'data': data
    }), 200

@bp.route('/api/bets', methods=['POST'])
def create_bet():
    """Create a new bet"""
    data = request.get_json()
    print(data)

    # Validate required fields
    required_fields = ['title']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    open_bets = Bet.query.filter(
        Bet.user_id == (data.get("user_id") or current_user.id),
        Bet.status.in_([PredictionStatus.PENDING, PredictionStatus.VOTING])
    ).first()

    if open_bets:
        return jsonify({"error": "You already have an active bet!"}), 400

    now = datetime.now(timezone.utc)
    d = int(data.get("days") or 0)
    h = int(data.get("hours") or 0)
    m = int(data.get("minutes") or 0)

    if d == 0 and h == 0 and m == 0:
        h = 1

    # 3. Create the timedelta
    open_timedelta = timedelta(days=d, hours=h, minutes=m)   
    vote_until = now + open_timedelta
    print(vote_until)

    bet = Bet(user_id=data.get("user_id", current_user.id), title=data.get("title"), description=data.get("description"), vote_until=vote_until)
    db.session.add(bet)
    db.session.commit()

    return jsonify({
        'message': 'Prediction successfully created',
        'id': bet.id,
        'data': bet.to_dict()
    }), 200

@bp.route('/api/bets', methods=['GET'])
@login_required
def fetch_bets():
    """Fetch bets"""

    #Pulling the data from the URL for further use
    user = current_user

    bets = Bet.query.filter_by(user_id=user.id).all()
    data = []
    for x in bets:
        data.append(x.to_dict())

    return jsonify({
        'message': 'Search successfull',
        'id': None,
        'data': data
    }), 200

@bp.route('/api/bets/<int:bet_id>', methods=['PUT', 'PATCH'])
def update_bet(bet_id):
    """Update an existing bet"""
    bet = Bet.query.get_or_404(bet_id)
    data = request.get_json()
    
    # Update fields if provided
    if 'title' in data:
        prediction.title = data['title']
    if 'subtitle' in data:
        prediction.description = data['description']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Bet successfully updated',
        'id': bet.id,
        'data': bet.to_dict()
    }), 200

@bp.route('/api/bets/<int:bet_id>', methods=['DELETE'])
def delete_bet(bet_id):
    """Delete a bet"""
    bet = Bet.query.get_or_404(bet_id)
    
    # 1. Capture the data while the object is still "alive" and attached
    bet_data = bet.to_dict()
    bet_id_val = bet.id
    
    # 2. Perform the deletion
    db.session.delete(bet)
    db.session.commit()
    
    # 3. Return the captured data
    return jsonify({
        'message': 'Bet successfully deleted',
        'id': bet_id_val,
        'data': bet_data
    }), 200

@bp.route('/api/bet/vote', methods=['POST'])
@login_required
def create_bet_vote():
    """Create a new bet vote"""
    data = request.get_json()
    user_id=data.get("user_id", current_user.id)

    # Validate required fields
    required_fields = ['bet_id', 'vote']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    bet = Bet.query.filter_by(
        id=data["bet_id"]
    ).first()

    if not bet:
        return jsonify({'error': 'No active bet for this vote exists'}), 400   

    now_aware = datetime.now(timezone.utc)
    now_naive = now_aware.replace(tzinfo=None)
    if now_naive > bet.vote_until:
        return jsonify({'error': 'Forbidden: the time for voting has passed'}), 403

    existing = BetVote.query.filter_by(
        bet_id=data["bet_id"], user_id=user_id
    ).first()

    if existing:
        return jsonify({'error': 'A vote for this bet already exists'}), 409

    vote = BetVote(bet_id=bet.id, user_id=user_id, vote=data.get("vote"))
    db.session.add(vote)
    db.session.commit()

    return jsonify({
        'message': 'Bet vote successfully created',
        'id': vote.id,
        'data': {'vote': vote.vote, 'status': vote.bet.status.value}
    }), 201

@bp.route('/api/bet/vote/<int:vote_id>', methods=['PUT', 'PATCH'])
@login_required
def update_bet_vote(vote_id):
    """Update an existing bet vote"""
    vote = BetVote.query.get_or_404(vote_id)
    data = request.get_json()

    if vote.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
 
    now_aware = datetime.now(timezone.utc)
    now_naive = now_aware.replace(tzinfo=None)
    if now_naive > vote.bet.vote_until:
        return jsonify({'error': 'Forbidden: the time for voting has passed'}), 403

    # Update fields if provided
    if 'vote' in data:
        vote.vote= data['vote']

    db.session.commit()

    return jsonify({
        'message': 'Bet vote successfully updated',
        'id': vote.id,
        'data': {'vote': vote.vote, 'status': vote.bet.status.value}
    }), 200

@bp.route('/api/bet-conclusion', methods=['POST'])
@login_required
def create_bet_conclusion():
    """Create a new bet conclusion"""
    data = request.get_json()

    # Validate required fields
    required_fields = ['bet_id', 'description', 'outcome']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400


    existing = BetConclusion.query.filter_by(
        bet_id=data["bet_id"], status=ConclusionStatus.ACTIVE
    ).first()
    if existing:
        return jsonify({'error': 'An active conclusion already exists'}), 409

    try:
        outcome = ConclusionOutcome[data.get("outcome")]
    except KeyError:
        return jsonify({'error': 'Invalid outcome value'}), 400
    
    conclusion = BetConclusion(bet_id=data.get("bet_id"), user_id=data.get("user_id", current_user.id), description=data.get("description"), url=data.get("url"), outcome=outcome)
    db.session.add(conclusion)
    db.session.flush()

    vote = BetConclusionVote(bet_conclusion_id=conclusion.id, user_id=data.get("user_id", current_user.id), vote=True)
    db.session.add(vote)

    conclusion.bet.status = PredictionStatus.VOTING

    db.session.commit()

    return jsonify({
        'message': 'Bet conclusion successfully created',
        'id': conclusion.id,
        'data': {'conclusion': conclusion.to_dict(), 'vote': vote.vote}
    }), 201

@bp.route('/api/bet-conclusion', methods=['GET'])
@login_required
def fetch_bet_conclusions():
    """Fetch bet conclusions"""

    #Pulling the data from the URL for further use
    id = request.args.get('id', None)

    if id:
        conclusions = [BetConclusion.query.filter_by(id=id, status=ConclusionStatus.ACTIVE).first_or_404()]
    else:
        conclusions = BetConclusion.query.filter_by(status=ConclusionStatus.ACTIVE).all()

    data = []
    for x in conclusions:
        data.append(x.to_dict())

    return jsonify({
        'message': 'Search successfull',
        'id': None,
        'data': data
    }), 200

@bp.route('/api/bet-conclusion/<int:bet_conclusion_id>', methods=['PATCH'])
@login_required
def update_bet_conclusion(bet_conclusion_id):
    conclusion = BetConclusion.query.get_or_404(bet_conclusion_id)
    data = request.get_json()

    if 'status' in data:
        try:
            new_status = ConclusionStatus[data['status']]
        except KeyError:
            return jsonify({'error': 'Invalid status value'}), 400
        
        # only the submitter can cancel
        if new_status == ConclusionStatus.CANCELLED:
            if conclusion.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized'}), 403
            if conclusion.status != ConclusionStatus.ACTIVE:
                return jsonify({'error': 'Can only cancel an active conclusion'}), 409

            conclusion.status = new_status

    db.session.commit()
    return jsonify({'message': 'Bet conclusion updated', 'id': conclusion.id}), 200

@bp.route('/api/bet-conclusion/vote', methods=['POST'])
@login_required
def create_bet_conclusion_vote():
    """Create a new bet conclusion vote"""
    data = request.get_json()
    user_id=data.get("user_id", current_user.id)

    # Validate required fields
    required_fields = ['bet_conclusion_id', 'vote']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400


    conclusion = BetConclusion.query.filter_by(
        id=data["bet_conclusion_id"]
    ).first()

    if not conclusion:
        return jsonify({'error': 'No active conclusion for this vote exists'}), 400   

    existing = BetConclusionVote.query.filter_by(
        bet_conclusion_id=data["bet_conclusion_id"], user_id=user_id
    ).first()

    if existing:
        return jsonify({'error': 'A vote for this bet conclusion already exists'}), 409

    vote = BetConclusionVote(bet_conclusion_id=conclusion.id, user_id=user_id, vote=data.get("vote"))
    db.session.add(vote)
    db.session.flush()
    
    if conclusion.total_in_favour >= Config.VOTE_LIMIT:

        conclusion.bet.status = PredictionStatus(conclusion.outcome.value)
        conclusion.status = ConclusionStatus.ACCEPTED
        winnings = 0.0
        if conclusion.outcome == ConclusionOutcome.SUCCESS:
            winnings += conclusion.bet.odds_against
        elif conclusion.outcome == ConclusionOutcome.FAILED:
            winnings += conclusion.bet.odds_in_favour

        losers = []
        winners = []

        for participant in conclusion.bet.votes:
            if (conclusion.outcome == ConclusionOutcome.SUCCESS) and (participant.vote is True):
                winners.append(participant.id)
            elif (conclusion.outcome == ConclusionOutcome.FAILED) and (participant.vote is False):
                winners.append(participant.id)
            else:
                losers.append(participant.id)
            
            for loser in losers:
                for winner in winners:
                    ledger_entry = BeerLedger(debtor_id=loser, creditor_id=winner, amount=float(winnings), bet_id=conclusion.bet.id, reason=f"Bet {conclusion.bet.id} - {conclusion.outcome} - {winnings} beer")
                    db.session.add(ledger_entry)

    elif conclusion.total_against >= Config.VOTE_LIMIT:
        conclusion.status = ConclusionStatus.REJECTED
        conclusion.bet.status = PredictionStatus.PENDING

    db.session.commit()

    return jsonify({
        'message': 'Bet conclusion vote successfully created',
        'id': vote.id,
        'data': {'vote': vote.vote, 'status': vote.conclusion.status.value}
    }), 201

@bp.route('/api/bet-conclusion/vote/<int:vote_id>', methods=['PUT', 'PATCH'])
@login_required
def update_bet_conclusion_vote(vote_id):
    """Update an existing bet conclusion vote"""
    vote = BetConclusionVote.query.get_or_404(vote_id)
    data = request.get_json()

    if vote.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
 
    conclusion = BetConclusion.query.filter_by(id=vote.bet_conclusion_id).first()

    # Update fields if provided
    if 'vote' in data:
        vote.vote= data['vote']

    db.session.flush()

    
    if conclusion.total_in_favour >= Config.VOTE_LIMIT:
        conclusion.bet.status = PredictionStatus(conclusion.outcome.value)
        conclusion.status = ConclusionStatus.ACCEPTED
        winnings = 0.0
        if conclusion.outcome == ConclusionOutcome.SUCCESS:
            winnings += conclusion.bet.odds_against
        elif conclusion.outcome == ConclusionOutcome.FAILED:
            winnings += conclusion.bet.odds_favour

        losers = []
        winners = []

        for participant in conclusion.bet.votes:
            if (conclusion.outcome == ConclusionOutcome.SUCCESS) and (participant.vote is True):
                winners.append(participant.id)
            elif (conclusion.outcome == ConclusionOutcome.FAILED) and (participant.vote is False):
                winners.append(participant.id)
            else:
                losers.append(participant.id)
            
            for loser in losers:
                for winner in winners:
                    ledger_entry = BeerLedger(debtor_id=loser, creditor_id=winner, amount=float(winnings), bet_id=conclusion.bet.id, reason=f"Bet {conclusion.bet.id} - {conclusion.outcome} - {winnings} beer")
                    db.session.add(ledger_entry)

    elif conclusion.total_against >= Config.VOTE_LIMIT:
        conclusion.status = ConclusionStatus.REJECTED
        conclusion.bet.status = PredictionStatus.PENDING

    db.session.commit()

    return jsonify({
        'message': 'Bet conclusion vote successfully updated',
        'id': vote.id,
        'data': {'vote': vote.vote, 'status': vote.conclusion.status.value}
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
def update_prediction(prediction_id):
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
def delete_prediction(prediction_id):
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

@bp.route('/api/conclusion', methods=['POST'])
@login_required
def create_conclusion():
    """Create a new prediction conclusion"""
    data = request.get_json()

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
        outcome = ConclusionOutcome[data.get("outcome")]
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

@bp.route('/api/conclusion', methods=['GET'])
@login_required
def fetch_conclusions():
    """Fetch conclusions"""

    #Pulling the data from the URL for further use
    id = request.args.get('id', None)

    if id:
        conclusions = [PredictionConclusion.query.filter_by(id=id, status=ConclusionStatus.ACTIVE).first_or_404()]
    else:
        conclusions = PredictionConclusion.query.filter_by(status=ConclusionStatus.ACTIVE).all()

    data = []
    for x in conclusions:
        data.append(x.to_dict())

    return jsonify({
        'message': 'Search successfull',
        'id': None,
        'data': data
    }), 200

@bp.route('/api/conclusion/<int:conclusion_id>', methods=['PATCH'])
@login_required
def update_conclusion(conclusion_id):
    conclusion = PredictionConclusion.query.get_or_404(conclusion_id)
    data = request.get_json()

    if 'status' in data:
        try:
            new_status = ConclusionStatus[data['status']]
        except KeyError:
            return jsonify({'error': 'Invalid status value'}), 400
        
        # only the submitter can cancel
        if new_status == ConclusionStatus.CANCELLED:
            if conclusion.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized'}), 403
            if conclusion.status != ConclusionStatus.ACTIVE:
                return jsonify({'error': 'Can only cancel an active conclusion'}), 409

            conclusion.status = new_status

    db.session.commit()
    return jsonify({'message': 'Conclusion updated', 'id': conclusion.id}), 200

@bp.route('/api/conclusion/vote', methods=['POST'])
@login_required
def create_conclusion_vote():
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

@bp.route('/api/conclusion/vote/<int:vote_id>', methods=['PUT', 'PATCH'])
@login_required
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


@bp.route('/api/signal/info', methods=['GET'])
def signal_get_info():
    """Get standing info through signal"""

    users = User.query.all()
    investments= sorted(users, key=lambda g: g.total_investment, reverse=True)
    predictions= sorted(users, key=lambda g: g.total_outstanding_points, reverse=True)
    predictions= sorted(predictions, key=lambda g: g.total_achieved_points, reverse=True)
    best_stock = StockPick.highest_return()
    worst_stock = StockPick.lowest_return()

    data = {
            "investments": [{"name": x.user_name, "rank": i, "total": x.total_investment} for i,x in enumerate(investments, 1)],
            "best_stock": {"name": best_stock.name, "total": best_stock.total_return},
            "worst_stock": {"name": worst_stock.name, "total": worst_stock.total_return},
            "predictions": [{"name": x.user_name,"rank": i, "total": {"achieved": x.total_achieved_points, "failed": x.total_failed_points, "outstanding":x.total_outstanding_points}} for i, x in enumerate(predictions, 1)],
    }


    return jsonify({
        'message': '',
        'data': data,
    }), 200


@bp.route('/api/signal/bets', methods=['POST'])
def signal_create_bet():
    """Create a new bet through signal"""
    data = request.get_json()
    print(data)

    # Validate required fields
    required_fields = ['title']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    open_bets = Bet.query.filter(
        Bet.user_id == (data.get("user_id") or current_user.id),
        Bet.status.in_([PredictionStatus.PENDING, PredictionStatus.VOTING])
    ).first()

    if open_bets:
        return jsonify({"error": "You already have an active bet!"}), 400

    now = datetime.now(timezone.utc)
    d = int(data.get("days") or 0)
    h = int(data.get("hours") or 0)
    m = int(data.get("minutes") or 0)

    if d == 0 and h == 0 and m == 0:
        h = 1

    # 3. Create the timedelta
    open_timedelta = timedelta(days=d, hours=h, minutes=m)   
    vote_until = now + open_timedelta
    print(vote_until)

    bet = Bet(user_id=data.get("user_id", current_user.id), title=data.get("title"), description=data.get("description"), vote_until=vote_until)
    db.session.add(bet)
    db.session.commit()

    return jsonify({
        'message': 'Prediction successfully created',
        'id': bet.id,
        'data': bet.to_dict()
    }), 200


@bp.route('/api/signal/beer', methods=['POST'])
def signal_create_bulk_beer_transaction():
    """Create bulk beer transactions through signal"""
    data = request.get_json()
    try:
        ids = []
        ledger_data = []

        for i, entry in enumerate(data["data"]):
            required_fields = ['creditor_id', 'amount']
            for field in required_fields:
                if field not in entry:
                    return jsonify({'error': f'Missing required field: {field} in {i}'}), 400


            bet_id = entry.get("bet_id")
            bet_id = None if bet_id == None else int(bet_id)

            reason = entry.get('reason', '').strip() or None

            ledger_entry = BeerLedger(debtor_id=entry.get("debitor_id", current_user.id), creditor_id=entry.get("creditor_id"), amount=float(entry.get("amount")), bet_id=bet_id, reason=reason)
            db.session.add(ledger_entry)
            db.session.flush()
            ids.append(ledger_entry.id)
            ledger_data.append(ledger_entry.to_dict())

        db.session.commit()

        return jsonify({
            'message': 'Ledger entries successfully created',
            'id': ids,
            'data': ledger_data
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({'error': f'{e}'}), 400

