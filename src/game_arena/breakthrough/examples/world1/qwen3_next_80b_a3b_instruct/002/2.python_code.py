
import copy
import heapq
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Determine direction, home row, and opponent home row
    if color == 'b':
        # Black moves downward: row decreases
        direction = -1
        my_home_row = 7  # Top
        opp_home_row = 0 # Bottom
    else:  # color == 'w'
        # White moves upward: row increases
        direction = 1
        my_home_row = 0  # Bottom
        opp_home_row = 7 # Top

    # Convert to set for O(1) lookup
    opp_set = set(opp)
    me_set = set(me)

    # Generate all legal moves
    legal_moves = []
    for r, c in me:
        # Straight forward
        new_r = r + direction
        new_c = c
        if 0 <= new_r <= 7:
            if (new_r, new_c) not in me_set and (new_r, new_c) not in opp_set:
                # Empty square - can move
                legal_moves.append(((r, c), (new_r, new_c)))
            elif (new_r, new_c) in opp_set:
                # Cannot move straight into opponent (capture only diagonal)
                pass
        
        # Diagonal forward left
        new_r = r + direction
        new_c = c - 1
        if 0 <= new_r <= 7 and 0 <= new_c <= 7:
            if (new_r, new_c) not in me_set:
                if (new_r, new_c) in opp_set:
                    # Capture
                    legal_moves.append(((r, c), (new_r, new_c)))
                else:
                    # Empty square - can move
                    legal_moves.append(((r, c), (new_r, new_c)))
        
        # Diagonal forward right
        new_r = r + direction
        new_c = c + 1
        if 0 <= new_r <= 7 and 0 <= new_c <= 7:
            if (new_r, new_c) not in me_set:
                if (new_r, new_c) in opp_set:
                    # Capture
                    legal_moves.append(((r, c), (new_r, new_c)))
                else:
                    # Empty square - can move
                    legal_moves.append(((r, c), (new_r, new_c)))

    # Check for immediate winning moves
    winning_moves = []
    for move in legal_moves:
        from_pos, to_pos = move
        if to_pos[0] == opp_home_row:
            return move  # Immediate win

    # If no winning move, use heuristic search (limited depth)
    # Prioritize moves: captures first, then center moves, then other advances
    def evaluate_move(move):
        from_pos, to_pos = move
        r, c = to_pos
        
        # Base score: higher for advancement toward goal
        advancement_score = abs(r - my_home_row)
        # Bonus for center positions
        center_bonus = 0
        if 3 <= c <= 4:
            center_bonus = 2
        # Capture bonus
        capture_bonus = 10 if to_pos in opp_set else 0
        # Mobile potential: number of forward moves from new position
        mobility_bonus = 0
        # Check future mobility from new position
        future_moves = 0
        for dr, dc in [(direction, 0), (direction, -1), (direction, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr <= 7 and 0 <= nc <= 7:
                if (nr, nc) not in me_set and (nr, nc) not in opp_set:
                    future_moves += 1
                elif (nr, nc) in opp_set:
                    future_moves += 1  # Capture also counts as mobility
        mobility_bonus = future_moves * 1.5
        # Penalize edge moves slightly
        edge_penalty = 0
        if c == 0 or c == 7:
            edge_penalty = -1
        
        return advancement_score + center_bonus + capture_bonus + mobility_bonus + edge_penalty

    # Sort moves by evaluation score (descending)
    ranked_moves = sorted(legal_moves, key=evaluate_move, reverse=True)

    # If no legal moves (shouldn't happen in a real game), return first possible
    if not ranked_moves:
        # Fallback: this should never happen unless board is full, but be safe
        return legal_moves[0] if legal_moves else ((0, 0), (0, 0))

    # For performance, use greedy with one-step lookahead
    # Try: if a move leads to opponent having no good reply, pick it
    # We'll do a shallow 1-ply lookahead: for each of our moves, check opponent's best reply
    best_move = ranked_moves[0]
    best_score = float('-inf')

    # Look at top 10 moves for efficiency
    for move in ranked_moves[:min(10, len(ranked_moves))]:
        # Simulate our move
        from_pos, to_pos = move
        new_me = [p for p in me if p != from_pos]
        new_me.append(to_pos)
        new_opp = [p for p in opp if p != to_pos]  # remove if captured

        # If we captured and it's a win condition, we already checked for win
        # Now simulate opponent's best response
        opp_legal_moves = []
        for r, c in new_opp:
            # Reverse direction for opponent
            opp_dir = -direction
            # Straight
            nr, nc = r + opp_dir, c
            if 0 <= nr <= 7:
                if (nr, nc) not in new_me and (nr, nc) not in set(new_opp):
                    opp_legal_moves.append(((r, c), (nr, nc)))
                # Diagonal left
            nr, nc = r + opp_dir, c - 1
            if 0 <= nr <= 7 and 0 <= nc <= 7:
                if (nr, nc) not in new_me:
                    if (nr, nc) in set(new_opp):
                        opp_legal_moves.append(((r, c), (nr, nc)))
                    else:
                        opp_legal_moves.append(((r, c), (nr, nc)))
            # Diagonal right
            nr, nc = r + opp_dir, c + 1
            if 0 <= nr <= 7 and 0 <= nc <= 7:
                if (nr, nc) not in new_me:
                    if (nr, nc) in set(new_opp):
                        opp_legal_moves.append(((r, c), (nr, nc)))
                    else:
                        opp_legal_moves.append(((r, c), (nr, nc)))

        # Evaluate opponent's best move
        opp_winning_moves = []
        for op_move in opp_legal_moves:
            if op_move[1][0] == my_home_row:
                opp_winning_moves.append(op_move)

        if opp_winning_moves:
            # Opponent wins immediately -> avoid this move
            continue

        # Otherwise, evaluate opponent's best move by heuristic
        def opp_evaluate_move(op_move):
            _, to_pos = op_move
            r, c = to_pos
            # Goal for opponent: reach our home row
            advancement = abs(r - opp_home_row)
            center_bonus = 2 if 3 <= c <= 4 else 0
            capture_bonus = 10 if to_pos in new_me else 0
            # Stability: avoid being too exposed
            exposure_penalty = 0
            for dr, dc in [(-opp_dir, 0), (-opp_dir, -1), (-opp_dir, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr <= 7 and 0 <= nc <= 7:
                    if (nr, nc) in new_me:
                        exposure_penalty -= 3  # vulnerable to capture
            return advancement + center_bonus + capture_bonus + exposure_penalty

        if opp_legal_moves:
            best_opp_move = max(opp_legal_moves, key=opp_evaluate_move)
            # We want to minimize the opponent's gain -> lower score is better for us
            opp_score = opp_evaluate_move(best_opp_move)
            # Our move's "goodness": higher advancement + lower opp_score = better
            # Use a simple difference: our advancement minus opponent's potential
            our_advancement = abs(to_pos[0] - my_home_row)
            score = our_advancement - opp_score * 0.5  # opponent's advancement is half weighted
        else:
            # Opponent has no moves? Unlikely but we win!
            score = float('inf')

        if score > best_score:
            best_score = score
            best_move = move

    return best_move
