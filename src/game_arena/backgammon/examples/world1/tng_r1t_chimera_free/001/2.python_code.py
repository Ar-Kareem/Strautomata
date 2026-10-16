
import numpy as np

def policy(state: dict) -> str:
    def get_die_orders(dice):
        if len(dice) < 2:
            return [dice]
        d1, d2 = dice
        if d1 == d2:
            return [dice]
        elif d1 > d2:
            return [[d1, d2], [d2, d1]]
        else:
            return [[d2, d1], [d1, d2]]

    def evaluate_move(state, from_point, die, is_bar=False):
        score = 0
        if is_bar:
            entry_point = 24 - die
            if state['opp_pts'][entry_point] == 1:
                score += 100
            score += (24 - entry_point)
            return score
        else:
            dest = from_point - die
            if dest < 0:
                if all(c == 0 for c in state['my_pts'][6:]):
                    return 200 + die  # Higher bonus for exact bear-off
                else:
                    return -np.inf  # Invalid if not all checkers in home
            if state['opp_pts'][dest] >= 2:
                return -np.inf
            if state['opp_pts'][dest] == 1:
                score += 100
            if state['my_pts'][from_point] == 1:
                score -= 30
            if (state['my_pts'][dest] + 1) >= 2:
                score += 50
            score += (24 - dest) * 2
            return score

    # Main logic
    if state['my_bar'] > 0:
        best_score = -np.inf
        best_order = 'H'
        best_moves = ['P', 'P']
        dice = state['dice']
        for die_order in get_die_orders(dice):
            temp_bar = state['my_bar']
            used_moves = []
            total_score = 0
            valid = True
            for die in die_order:
                if temp_bar == 0:
                    break
                ep = 24 - die
                if ep < 0 or ep >= 24 or state['opp_pts'][ep] >= 2:
                    continue
                score = evaluate_move(state, None, die, is_bar=True)
                total_score += score
                used_moves.append('B')
                temp_bar -= 1
            if not used_moves:
                continue
            while len(used_moves) < 2:
                used_moves.append('P')
            order_char = 'H' if (len(die_order) > 1 and die_order[0] > die_order[1]) else 'L'
            if total_score > best_score or (total_score == best_score and order_char == 'H'):
                best_score = total_score
                best_order = order_char
                best_moves = used_moves[:2]
        if best_score != -np.inf:
            return f"{best_order}:{','.join(best_moves)}"
        else:
            return 'H:P,P'
    else:
        def generate_non_bar_move(die_order, state):
            temp_pts = state['my_pts'].copy()
            moves = []
            score = 0
            for die in die_order:
                best_move_score = -np.inf
                best_from = None
                for from_point in range(24):
                    if temp_pts[from_point] == 0:
                        continue
                    move_score = evaluate_move(state, from_point, die)
                    if move_score > best_move_score:
                        best_move_score = move_score
                        best_from = from_point
                if best_from is not None and best_move_score != -np.inf:
                    dest = best_from - die
                    if dest >= 0:
                        if state['opp_pts'][dest] >= 2:
                            continue
                    moves.append(f"A{best_from}")
                    score += best_move_score
                    temp_pts[best_from] -= 1
                    if dest >= 0:
                        temp_pts[dest] += 1
                else:
                    moves.append('P')
            while len(moves) < 2:
                moves.append('P')
            return score, moves

        dice = state['dice']
        best_score = -np.inf
        best_order = 'H'
        best_moves = ['P', 'P']
        home_board = all(c == 0 for c in state['my_pts'][6:])
        for die_order in get_die_orders(dice):
            current_score, current_moves = generate_non_bar_move(die_order, state)
            current_order = 'H' if len(die_order) < 2 or die_order[0] >= die_order[1] else 'L'
            if current_score > best_score or (current_score == best_score and current_order == 'H'):
                best_score = current_score
                best_order = current_order
                best_moves = current_moves
        return f"{best_order}:{','.join(best_moves)}"
