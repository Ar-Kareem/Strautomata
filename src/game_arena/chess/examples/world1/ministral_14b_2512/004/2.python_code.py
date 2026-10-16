
import re
from typing import Dict, List

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str]) -> str:
    # Precompute piece values and colors
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    opponent_color = 'b' if to_play == 'white' else 'w'
    our_color = 'w' if to_play == 'white' else 'b'

    # Parse the board to find our and opponent pieces
    our_pieces = {sq: pc for sq, pc in pieces.items() if pc[0] == our_color}
    opponent_pieces = {sq: pc for sq, pc in pieces.items() if pc[0] == opponent_color}

    # Helper functions
    def square_to_rank_file(sq: str) -> tuple[int, int]:
        file = ord(sq[0]) - ord('a')
        rank = int(sq[1]) - 1
        return rank, file

    def rank_file_to_square(rank: int, file: int) -> str:
        return f"{chr(ord('a') + file)}{rank + 1}"

    def is_checkmate(move: str) -> bool:
        # Simulate the move and check if the opponent has no legal moves
        # For simplicity, we assume the move leads to checkmate if it's a check and the opponent has no escapes
        # This is a heuristic; a full implementation would require move generation
        return move.endswith('#')

    def evaluate_move(move: str) -> float:
        score = 0.0

        # Check for checkmate
        if is_checkmate(move):
            return float('inf')

        # Parse the move to extract capture info
        capture_match = re.match(r'([a-h][1-8])x([a-h][1-8])', move)
        if capture_match:
            target_sq = capture_match.group(2)
            if target_sq in opponent_pieces:
                captured_piece = opponent_pieces[target_sq]
                score += piece_values[captured_piece[1]] * 1.5  # Bonus for captures

        # Check for promotions (prefer Queen unless tactical)
        if '=' in move:
            score += 9.0  # Queen promotion is strong

        # Check for castling (safe king move)
        if move in ['O-O', 'O-O-O']:
            score += 0.5  # Small bonus for castling

        # Check for checks (aggressive play)
        if move.endswith('+'):
            score += 1.0

        # Check for pawn moves (central control)
        if move[0].islower() and move[1].isdigit():  # Pawn move (e.g., 'e4')
            rank, file = square_to_rank_file(move[:2])
            if 3 <= file <= 4 and 3 <= rank <= 4:  # Center squares
                score += 0.3

        # Check for knight forks or bishop pins (tactical)
        if re.match(r'N[a-h][1-8]', move) or re.match(r'B[a-h][1-8]', move):
            score += 0.2

        # King safety: avoid moving king into danger
        if move.startswith('K'):
            king_sq = move[:2]
            king_rank, king_file = square_to_rank_file(king_sq)
            # Check if king is exposed to opponent attacks (simplified)
            for sq in opponent_pieces:
                opp_rank, opp_file = square_to_rank_file(sq)
                if abs(king_rank - opp_rank) <= 1 and abs(king_file - opp_file) <= 1:
                    score -= 2.0  # Penalize dangerous king moves

        return score

    # Evaluate all legal moves and pick the best
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        score = evaluate_move(move)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move
