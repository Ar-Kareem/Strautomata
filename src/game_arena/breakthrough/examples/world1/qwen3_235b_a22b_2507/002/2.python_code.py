
import random
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Define forward direction based on color
    forward = -1 if color == 'b' else 1  # black moves up (decreasing row), white moves down (increasing row)
    my_home, opp_home = (7, 0) if color == 'b' else (0, 7)

    # Convert opp list to set for fast lookup
    opp_set = set(opp)
    me_set = set(me)

    def is_in_bounds(r: int, c: int) -> bool:
        return 0 <= r < 8 and 0 <= c < 8

    def will_win_after_move(piece: Tuple[int, int], to_pos: Tuple[int, int], opp_pieces: List[Tuple[int, int]]) -> bool:
        to_r, to_c = to_pos
        # Win by reaching opponent's home row
        if to_r == opp_home:
            return True
        # Simulate capture
        new_opp = [p for p in opp_pieces if p != (to_r, to_c)]
        # Win by capturing all opponent pieces
        if len(new_opp) == 0:
            return True
        return False

    def get_legal_moves() -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        moves = []
        for piece in me:
            r, c = piece
            # Straight forward
            straight = (r + forward, c)
            if is_in_bounds(straight[0], straight[1]) and straight not in me_set and straight not in opp_set:
                moves.append((piece, straight))
            # Diagonal left (capture or move)
            diag_left = (r + forward, c - 1)
            if is_in_bounds(diag_left[0], diag_left[1]):
                if diag_left in opp_set or diag_left not in me_set:  # can capture or move if empty
                    if diag_left not in me_set:  # not occupied by own piece
                        moves.append((piece, diag_left))
            # Diagonal right
            diag_right = (r + forward, c + 1)
            if is_in_bounds(diag_right[0], diag_right[1]):
                if diag_right in opp_set or diag_right not in me_set:
                    if diag_right not in me_set:
                        moves.append((piece, diag_right))
        return moves

    def evaluate_move(move: Tuple[Tuple[int, int], Tuple[int, int]]) -> float:
        (fr, fc), (to_r, to_c) = move
        score = 0.0

        # Immediate win check
        if will_win_after_move((fr, fc), (to_r, to_c), opp):
            return float('inf')  # Best possible move

        # Reward advancement towards opponent's home
        progress = abs(to_r - my_home) - abs(fr - my_home)  # more progress is better
        score += progress * 10

        # Bonus for capturing
        if (to_r, to_c) in opp_set:
            score += 50

        # Small penalty for moving to edge (less mobility)
        if to_c == 0 or to_c == 7:
            score -= 5

        # Encourage central control
        score += (3 - abs(to_c - 3.5))  # center columns (3,4) preferred

        return score

    # Generate all legal moves
    legal_moves = get_legal_moves()

    # If no legal moves? (should not happen in Breakthrough) fallback
    if not legal_moves:
        # Try to return any possible move, even if blocked
        for piece in me:
            r, c = piece
            for dc in [-1, 0, 1]:
                nr, nc = r + forward, c + dc
                if is_in_bounds(nr, nc):
                    return (r, c), (nr, nc)
        return (0, 0), (0, 0)  # fallback

    # Score all moves
    scored_moves = [(move, evaluate_move(move)) for move in legal_moves]

    # Find the best move
    best_move = max(scored_moves, key=lambda x: x[1])[0]

    return best_move
