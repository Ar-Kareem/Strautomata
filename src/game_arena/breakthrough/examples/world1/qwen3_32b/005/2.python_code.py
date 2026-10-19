
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    def generate_moves(current_me, current_opp, current_color):
        me_set = set(current_me)
        opp_set = set(current_opp)
        moves = []
        for (row, col) in current_me:
            if current_color == 'w':
                step = 1
                home_row = 7
            else:
                step = -1
                home_row = 0
            new_row = row + step
            straight_pos = (new_row, col)
            if 0 <= new_row <= 7:
                if straight_pos not in me_set and straight_pos not in opp_set:
                    moves.append(((row, col), straight_pos))
            for delta_col in (-1, 1):
                new_col = col + delta_col
                capture_pos = (new_row, new_col)
                if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                    if capture_pos in opp_set:
                        moves.append(((row, col), capture_pos))
        return moves

    def is_winning_move(pos, current_color):
        row, _ = pos
        if current_color == 'w' and row == 7:
            return True
        if current_color == 'b' and row == 0:
            return True
        return False

    def evaluate(current_me, current_opp, current_color):
        for pos in current_me:
            if is_winning_move(pos, current_color):
                return float('inf')
        if len(current_opp) == 0:
            return float('inf')
        if len(current_me) == 0:
            return float('-inf')
        current_moves = generate_moves(current_me, current_opp, current_color)
        if not current_moves:
            return float('-inf')
        me_count = len(current_me)
        opp_count = len(current_opp)
        def positional_score(pieces):
            score = 0
            for r, _ in pieces:
                if current_color == 'w':
                    score += r
                else:
                    score += (7 - r)
            return score
        my_pos = positional_score(current_me)
        opp_pos = positional_score(current_opp)
        my_mob = len(current_moves)
        opp_mob = len(generate_moves(current_opp, current_me, 'b' if current_color == 'w' else 'w'))
        piece_weight = 100
        positional_weight = 1
        mobility_weight = 0.1
        score = (me_count - opp_count) * piece_weight + (my_pos - opp_pos) * positional_weight + (my_mob - opp_mob) * mobility_weight
        return score

    possible_moves = generate_moves(me, opp, color)
    for move in possible_moves:
        to_pos = move[1]
        if is_winning_move(to_pos, color):
            return move

    max_depth = 2
    best_move = possible_moves[0]
    best_score = -float('inf')

    def alphabeta(current_me, current_opp, current_color, depth, alpha, beta, is_maximizing):
        if depth == 0:
            return evaluate(current_me, current_opp, current_color)
        current_eval = evaluate(current_me, current_opp, current_color)
        if current_eval in (float('inf'), float('-inf')):
            return current_eval
        if is_maximizing:
            max_val = -float('inf')
            for move in generate_moves(current_me, current_opp, current_color):
                from_pos, to_pos = move
                new_me = [p for p in current_me if p != from_pos] + [to_pos]
                new_opp = current_opp.copy()
                if to_pos in new_opp:
                    new_opp.remove(to_pos)
                val = alphabeta(new_me, new_opp, 'b' if current_color == 'w' else 'w', depth - 1, alpha, beta, False)
                max_val = max(max_val, val)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return max_val
        else:
            min_val = float('inf')
            opponent_color = 'b' if current_color == 'w' else 'w'
            for move in generate_moves(current_opp, current_me, opponent_color):
                from_pos, to_pos = move
                new_opp = [p for p in current_opp if p != from_pos] + [to_pos]
                new_me = current_me.copy()
                if to_pos in new_me:
                    new_me.remove(to_pos)
                val = alphabeta(new_me, new_opp, current_color, depth - 1, alpha, beta, True)
                min_val = min(min_val, val)
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return min_val

    for move in possible_moves:
        from_pos, to_pos = move
        new_me = [p for p in me if p != from_pos] + [to_pos]
        new_opp = opp.copy()
        if to_pos in new_opp:
            new_opp.remove(to_pos)
        score = alphabeta(new_me, new_opp, 'b' if color == 'w' else 'w', max_depth - 1, -float('inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
