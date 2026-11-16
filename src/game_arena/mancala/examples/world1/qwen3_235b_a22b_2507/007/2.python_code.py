
import math

def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you, opp, move):
        y = you[:]
        o = opp[:]
        seeds = y[move]
        y[move] = 0
        board = y[0:6] + [y[6]] + o[0:6]  # 13 positions: 0-5 your houses, 6 your store, 7-12 opp houses
        current_pit = move + 1
        seeds_to_place = seeds
        while seeds_to_place > 0:
            idx = current_pit % 13
            board[idx] += 1
            seeds_to_place -= 1
            current_pit += 1
        last_land = (current_pit - 1) % 13
        extra = (last_land == 6)
        # Check for capture: lands in own empty house with opponent having seeds
        if last_land < 6 and board[last_land] == 1:  # landed in own house and now has 1 (was empty)
            opp_idx = 5 - last_land
            opp_pit = 7 + opp_idx
            if board[opp_pit] > 0:
                capture_total = 1 + board[opp_pit]
                board[6] += capture_total  # add to your store
                board[last_land] = 0        # clear your house
                board[opp_pit] = 0          # clear opponent's opposite house
        new_you = board[0:6] + [board[6]]
        new_opp = board[7:13] + [o[6]]   # opponent's store unchanged
        return new_you, new_opp, extra

    def game_over(you, opp):
        return sum(you[0:6]) == 0 or sum(opp[0:6]) == 0

    def evaluate(you, opp):
        my_houses = you[0:6]
        opp_houses = opp[0:6]
        my_seeds = sum(my_houses)
        opp_seeds = sum(opp_houses)
        if my_seeds == 0 or opp_seeds == 0:
            # Game over: opponent or you has no seeds, other captures remaining
            my_score = you[6] + my_seeds
            opp_score = opp[6] + opp_seeds
            return my_score - opp_score
        # Heuristic score
        score = (you[6] - opp[6]) * 10  # score difference
        score += (my_seeds - opp_seeds) * 1  # board control
        my_moves = sum(1 for i in range(6) if my_houses[i] > 0)
        opp_moves = sum(1 for i in range(6) if opp_houses[i] > 0)
        score += (my_moves - opp_moves) * 0.5  # mobility
        return score

    def move_order_key(you, opp, move):
        seeds = you[move]
        # Predict final position: (move + seeds) % 13
        pos = (move + seeds) % 13
        if pos == 6:
            return 10  # extra move
        elif pos < 6:
            if you[pos] == 0:  # currently empty
                opp_idx = 5 - pos
                if opp[opp_idx] > 0:
                    capture_amt = 1 + opp[opp_idx]
                    return 8 + capture_amt / 100.0
        return seeds / 100.0  # prefer larger seed moves

    def minimax(you, opp, depth, alpha, beta, maximizing):
        if depth == 0 or game_over(you, opp):
            return evaluate(you, opp), None

        if maximizing:
            best_move = None
            best_value = -math.inf
            moves = [i for i in range(6) if you[i] > 0]
            # Sort moves: better ones first
            moves.sort(key=lambda m: move_order_key(you, opp, m), reverse=True)
            for move in moves:
                new_you, new_opp, extra = simulate_move(you, opp, move)
                if extra:
                    value, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                else:
                    value, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
                if value > best_value:
                    best_value = value
                    best_move = move
                alpha = max(alpha, best_value)
                if beta <= alpha:
                    break
            return best_value, best_move
        else:
            best_value = math.inf
            best_move = None
            moves = [i for i in range(6) if opp[i] > 0]
            # For opponent, we sort to help pruning: moves good for opponent are bad for us
            moves.sort(key=lambda m: move_order_key(opp, you, m), reverse=True)
            for move in moves:
                new_opp, new_you, extra = simulate_move(opp, you, move)
                if extra:
                    value, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
                else:
                    value, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                if value < best_value:
                    best_value = value
                    best_move = move
                beta = min(beta, best_value)
                if beta <= alpha:
                    break
            return best_value, best_move

    # Policy logic
    moves = [i for i in range(6) if you[i] > 0]
    if len(moves) == 1:
        return moves[0]

    # Use minimax to select best move
    depth = 5
    best_score, best_move = minimax(you, opponent, depth, -math.inf, math.inf, True)
    if best_move is None:
        best_move = moves[0]  # fallback
    return best_move
