
import numpy as np
from collections import defaultdict

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    # Helper functions
    def is_legal_move(from_pt, die):
        if from_pt == 'B':
            if my_bar == 0:
                return False
            to_pt = 24 - die  # Bar entry point
            return opp_pts[to_pt] < 2
        else:
            from_pt = int(from_pt[1:])
            if my_pts[from_pt] == 0:
                return False
            to_pt = from_pt + die
            if to_pt >= 24:
                return True  # Bearing off
            return opp_pts[to_pt] < 2

    def get_legal_moves():
        moves = []
        if my_bar > 0:
            # Must move from bar first
            for die in sorted(dice, reverse=True):
                to_pt = 24 - die
                if opp_pts[to_pt] < 2:
                    moves.append(('B', die))
        else:
            # Check all possible moves
            for from_pt in range(24):
                if my_pts[from_pt] > 0:
                    for die in sorted(dice, reverse=True):
                        to_pt = from_pt + die
                        if to_pt >= 24:
                            # Bearing off
                            if my_off + my_bar + sum(my_pts[0:6]) == len(my_pts) - sum(my_pts[18:24]):
                                moves.append((f'A{from_pt}', die))
                        else:
                            if opp_pts[to_pt] < 2:
                                moves.append((f'A{from_pt}', die))
        return moves

    def evaluate_move(move):
        from_pt, die = move
        if from_pt == 'B':
            to_pt = 24 - die
            # Prefer moving to points with fewer opponent checkers
            score = -opp_pts[to_pt]
            # Prefer moving to home board (points 0-5)
            if to_pt < 6:
                score += 2
            return score
        else:
            from_pt = int(from_pt[1:])
            to_pt = from_pt + die
            if to_pt >= 24:
                # Bearing off - prefer higher value checkers
                return -from_pt  # Higher points are better to bear off
            else:
                # Prefer moves that don't leave blots
                score = 0
                # Avoid creating blots
                if opp_pts[to_pt] == 0 and my_pts[to_pt] == 1:
                    score -= 3
                # Prefer moving to points with fewer opponent checkers
                score -= opp_pts[to_pt]
                # Prefer moving to home board
                if to_pt < 6:
                    score += 2
                # Prefer moving checkers forward
                score += from_pt
                return score

    def get_best_move():
        legal_moves = get_legal_moves()
        if not legal_moves:
            return 'H:P,P'

        # Sort by die value (higher first)
        legal_moves.sort(key=lambda x: -x[1])

        # If only one die can be played, must use higher die
        if len(dice) == 1 or (len(dice) == 2 and not any(m[1] == dice[0] for m in legal_moves)):
            best_move = max(legal_moves, key=evaluate_move)
            return f'H:{best_move[0]},{best_move[0]}' if len(dice) == 1 else f'H:{best_move[0]},P'

        # Try to find a pair of moves
        best_score = -float('inf')
        best_pair = None

        # Generate all possible pairs
        for i in range(len(legal_moves)):
            for j in range(i, len(legal_moves)):
                from1, die1 = legal_moves[i]
                from2, die2 = legal_moves[j]

                # Check if we can use both dice
                if (from1 == from2 and die1 == die2) or (from1 != from2 and die1 != die2):
                    # Calculate combined score
                    score = evaluate_move((from1, die1)) + evaluate_move((from2, die2))

                    # Prefer using both dice
                    if score > best_score:
                        best_score = score
                        best_pair = (from1, from2)

        if best_pair:
            # Determine order (higher die first)
            move1, move2 = best_pair
            die1 = dice[1] if dice[1] > dice[0] else dice[0]
            die2 = dice[0] if dice[1] > dice[0] else dice[1]

            # Check which move uses which die
            if is_legal_move(move1, die1) and is_legal_move(move2, die2):
                return f'H:{move1},{move2}'
            else:
                # Fallback to single move
                best_single = max(legal_moves, key=evaluate_move)
                return f'H:{best_single[0]},P'

        # Fallback to single best move
        best_single = max(legal_moves, key=evaluate_move)
        return f'H:{best_single[0]},P'

    return get_best_move()
