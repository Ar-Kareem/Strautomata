
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    def generate_legal_moves(me_list, opp_list, color):
        me_set = set(me_list)
        opp_set = set(opp_list)
        direction = 1 if color == 'w' else -1
        legal_moves = []
        for (r, c) in me_list:
            new_r = r + direction
            # Straight move
            if 0 <= new_r <= 7:
                if (new_r, c) not in me_set and (new_r, c) not in opp_set:
                    legal_moves.append(((r, c), (new_r, c)))
            # Diagonal left
            new_c = c - 1
            if 0 <= new_r <= 7 and 0 <= new_c <= 7:
                target = (new_r, new_c)
                if target not in me_set:
                    legal_moves.append(((r, c), target))
            # Diagonal right
            new_c = c + 1
            if 0 <= new_r <= 7 and 0 <= new_c <= 7:
                target = (new_r, new_c)
                if target not in me_set:
                    legal_moves.append(((r, c), target))
        return legal_moves

    def evaluate_move(move, color, direction, me_set, opp_set):
        (fr, fc), (tr, tc) = move
        is_capture = (tr, tc) in opp_set
        simulated_opp = opp_set - {(tr, tc)} if is_capture else opp_set
        home_row = 7 if color == 'w' else 0
        if tr == home_row:  # Winning move
            return 10000
        # Advancement
        if color == 'w':
            advancement = (tr - fr) * 10
        else:
            advancement = (fr - tr) * 10
        # Capture bonus
        capture_bonus = 0
        if is_capture:
            if color == 'w':
                opp_progress = tr
            else:
                opp_progress = 7 - tr
            capture_bonus = 50 + opp_progress * 2
        # Center bonus
        center_bonus = [0, 1, 2, 3, 3, 2, 1, 0][tc]
        # Vulnerability penalty
        opp_dir = -direction
        threat1 = (tr + opp_dir, tc - 1)
        threat2 = (tr + opp_dir, tc + 1)
        vulnerability = 0
        if threat1 in simulated_opp or threat2 in simulated_opp:
            count = sum([threat1 in simulated_opp, threat2 in simulated_opp])
            vulnerability = 30 * count
        return advancement + capture_bonus + center_bonus - vulnerability

    me_list, opp_list = me.copy(), opp.copy()
    me_set, opp_set = set(me), set(opp)
    direction = 1 if color == 'w' else -1
    legal_moves = generate_legal_moves(me_list, opp_list, color)
    if not legal_moves:
        assert False, "No legal moves available"

    moves_scores = []
    for move in legal_moves:
        score = evaluate_move(move, color, direction, me_set, opp_set)
        moves_scores.append((move, score))
    max_score = max(score for move, score in moves_scores)
    best_moves = [move for move, score in moves_scores if score == max_score]

    # Tie-breakers: centrality then advancement
    def tiebreaker(move):
        (_, _), (tr, tc) = move
        centrality = -abs(tc - 3.5)
        advancement = tr if color == 'w' else 7 - tr
        return (centrality, advancement)
    best_moves.sort(key=tiebreaker, reverse=True)
    return best_moves[0]
