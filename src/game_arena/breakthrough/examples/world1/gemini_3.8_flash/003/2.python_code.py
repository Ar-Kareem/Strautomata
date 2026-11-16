
import time
import math

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    time_limit = 0.88  # Safety margin within 1.0s

    is_white = (color == 'w')
    my_dir = 1 if is_white else -1
    goal_row = 7 if is_white else 0
    opp_goal_row = 0 if is_white else 7

    # Fast bitboard / set representations
    my_set = set(me)
    opp_set = set(opp)

    # 1. Immediate Win Check
    for r, c in me:
        nr = r + my_dir
        if nr == goal_row:
            for nc in (c - 1, c, c + 1):
                if 0 <= nc < 8:
                    if nc == c:
                        if (nr, nc) not in my_set and (nr, nc) not in opp_set:
                            return ((r, c), (nr, nc))
                    else:
                        if (nr, nc) not in my_set:
                            return ((r, c), (nr, nc))

    # Helper: Move generator for a state
    def get_moves(player_pieces, enemy_pieces, p_dir, p_goal):
        moves = []
        p_set = set(player_pieces)
        e_set = set(enemy_pieces)

        for r, c in player_pieces:
            nr = r + p_dir
            # Straight move (must be empty)
            if (nr, c) not in p_set and (nr, c) not in e_set:
                moves.append(((r, c), (nr, c)))
            # Diagonals (empty or capture enemy)
            for nc in (c - 1, c + 1):
                if 0 <= nc < 8:
                    if (nr, nc) not in p_set:
                        moves.append(((r, c), (nr, nc)))
        return moves

    # Check immediate opponent winning threats
    opp_threats = []
    for r, c in opp:
        if r + (-my_dir) == opp_goal_row:
            opp_threats.append((r, c))

    # Static Evaluation function from 'me' perspective
    # Positive is good for 'me', negative is good for 'opp'
    def evaluate(p_me, p_opp):
        if not p_opp:
            return 50000
        if not p_me:
            return -50000

        score = 0
        p_me_set = set(p_me)
        p_opp_set = set(p_opp)

        # Distance bonuses and runner detection
        # For white, distance to row 7 is (7 - r). For black, distance to row 0 is r.
        min_dist_me = 8
        min_dist_opp = 8

        for r, c in p_me:
            dist = (7 - r) if is_white else r
            if dist < min_dist_me:
                min_dist_me = dist
            # Exponential advancement weight
            adv = 7 - dist
            score += adv * adv * 14 + adv * 10

            # Diagonal defense bonus (pawn chain)
            support_r = r - my_dir
            if (support_r, c - 1) in p_me_set or (support_r, c + 1) in p_me_set:
                score += 18

        for r, c in p_opp:
            dist = r if is_white else (7 - r)
            if dist < min_dist_opp:
                min_dist_opp = dist
            adv = 7 - dist
            score -= (adv * adv * 14 + adv * 10)

            # Opponent diagonal defense
            support_r = r + my_dir
            if (support_r, c - 1) in p_opp_set or (support_r, c + 1) in p_opp_set:
                score -= 18

        # Race advantage bonus
        score += (min_dist_opp - min_dist_me) * 65

        # Material advantage
        score += (len(p_me) - len(p_opp)) * 120

        return score

    # Move sorting helper
    def order_moves(moves, p_opp_set, p_goal, p_dir):
        def move_priority(m):
            (fr, fc), (tr, tc) = m
            prio = 0
            if tr == p_goal:
                prio += 100000
            if (tr, tc) in p_opp_set:
                prio += 5000 + (7 - abs(tr - p_goal)) * 20
            # Moving forward towards goal
            prio += (7 - abs(tr - p_goal)) * 10
            # Center control
            prio += (3.5 - abs(tc - 3.5)) * 2
            return prio

        moves.sort(key=move_priority, reverse=True)
        return moves

    # Negamax search
    tt = {}

    def search(p_me, p_opp, depth, alpha, beta, is_my_turn):
        if time.time() - start_time > time_limit:
            raise TimeoutError()

        p_dir = my_dir if is_my_turn else -my_dir
        p_goal = goal_row if is_my_turn else opp_goal_row

        current_player_pieces = p_me if is_my_turn else p_opp
        current_enemy_pieces = p_opp if is_my_turn else p_me
        enemy_set = set(current_enemy_pieces)

        # Terminal state check
        for r, c in current_enemy_pieces:
            if r == (opp_goal_row if is_my_turn else goal_row):
                return -40000 - depth

        if not current_player_pieces:
            return -40000 - depth

        if depth == 0:
            val = evaluate(p_me, p_opp)
            return val if is_my_turn else -val

        # State hash for transposition table
        state_key = (frozenset(p_me), frozenset(p_opp), is_my_turn)
        tt_entry = tt.get(state_key)
        if tt_entry and tt_entry[0] >= depth:
            entry_depth, entry_val, entry_flag = tt_entry
            if entry_flag == 'EXACT':
                return entry_val
            elif entry_flag == 'LOWER' and entry_val > alpha:
                alpha = entry_val
            elif entry_flag == 'UPPER' and entry_val < beta:
                beta = entry_val
            if alpha >= beta:
                return entry_val

        moves = get_moves(current_player_pieces, current_enemy_pieces, p_dir, p_goal)
        if not moves:
            return -40000 - depth

        moves = order_moves(moves, enemy_set, p_goal, p_dir)

        best_val = -math.inf
        orig_alpha = alpha

        for (fr, fc), (tr, tc) in moves:
            # Check immediate win
            if tr == p_goal:
                val = 40000 + depth
            else:
                # Apply move
                if is_my_turn:
                    new_me = [p for p in p_me if p != (fr, fc)]
                    new_me.append((tr, tc))
                    new_opp = [p for p in p_opp if p != (tr, tc)]
                    val = -search(new_me, new_opp, depth - 1, -beta, -alpha, False)
                else:
                    new_opp = [p for p in p_opp if p != (fr, fc)]
                    new_opp.append((tr, tc))
                    new_me = [p for p in p_me if p != (tr, tc)]
                    val = -search(new_me, new_opp, depth - 1, -beta, -alpha, True)

            if val > best_val:
                best_val = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        # Store in TT
        flag = 'EXACT'
        if best_val <= orig_alpha:
            flag = 'UPPER'
        elif best_val >= beta:
            flag = 'LOWER'
        tt[state_key] = (depth, best_val, flag)

        return best_val

    # Generate initial root moves
    root_moves = get_moves(me, opp, my_dir, goal_row)
    if not root_moves:
        return ((me[0][0], me[0][1]), (me[0][0], me[0][1]))

    root_moves = order_moves(root_moves, opp_set, goal_row, my_dir)
    best_move = root_moves[0]

    # Iterative Deepening
    try:
        for depth in range(1, 10):
            current_best_move = None
            current_best_val = -math.inf
            alpha = -math.inf
            beta = math.inf

            for (fr, fc), (tr, tc) in root_moves:
                if tr == goal_row:
                    return ((fr, fc), (tr, tc))

                new_me = [p for p in me if p != (fr, fc)]
                new_me.append((tr, tc))
                new_opp = [p for p in opp if p != (tr, tc)]

                val = -search(new_me, new_opp, depth - 1, -beta, -alpha, False)
                if val > current_best_val:
                    current_best_val = val
                    current_best_move = ((fr, fc), (tr, tc))
                if val > alpha:
                    alpha = val

            if current_best_move:
                best_move = current_best_move
            # If a guaranteed win is found, no need to search deeper
            if current_best_val >= 35000:
                break
    except TimeoutError:
        pass

    return best_move
