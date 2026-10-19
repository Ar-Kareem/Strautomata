
import numpy as np

PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
}

def square_to_coords(sq):
    file = ord(sq[0]) - ord('a')
    rank = int(sq[1]) - 1
    return (rank, file)

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    color_prefix = 'w' if to_play == 'white' else 'b'
    opponent_prefix = 'b' if color_prefix == 'w' else 'w'

    # Helper to get piece value from code like 'wQ' or 'bR'
    def get_piece_value(piece_code):
        if piece_code is None:
            return 0
        return PIECE_VALUES.get(piece_code[1], 0)

    # Simulate a move and see if it gives checkmate (very basic check: opponent has no legal moves after)
    # Since we don't have a move generator, we can only guess from move string notation.
    # Instead, prioritize moves that deliver check and capture high-value pieces.

    # 1. First pass: find captures
    captures = []
    for move in legal_moves:
        if 'x' in move:
            # Parse capture: e.g. Bxe5, exd5, Nf3xd4
            # Simple method: target square is after 'x'
            parts = move.split('x')
            if len(parts) == 2:
                # target square: last part until end or until promotion
                target = parts[1]
                # Remove check/disambig symbols
                for sym in ['+', '#', '=Q', '=R', '=B', '=N']:
                    if target.endswith(sym):
                        target = target[:-len(sym)]
                # Remove any remaining non-alphanumeric (shouldn't happen here)
                if target[-1].isdigit() and target[0].isalpha():
                    target_sq = target[:2]
                else:
                    # fallback: try to find square pattern
                    import re
                    m = re.search(r'([a-h][1-8])', target)
                    if m:
                        target_sq = m.group(1)
                    else:
                        continue
                captured_piece = pieces.get(target_sq)
                if captured_piece is not None and captured_piece[0] == opponent_prefix:
                    captures.append((move, get_piece_value(captured_piece), target_sq))
        # Also, promotions that capture? e.g., exd8=Q+
        if '=' in move and 'x' in move:
            # handle like above
            parts = move.split('x')
            if len(parts) == 2:
                target = parts[1].split('=')[0]
                captured_piece = pieces.get(target)
                if captured_piece is not None and captured_piece[0] == opponent_prefix:
                    captures.append((move, get_piece_value(captured_piece), target))

    # Sort captures by captured value descending
    captures.sort(key=lambda x: x[1], reverse=True)

    # If there are captures, pick the highest-value capture
    # but avoid losing a higher-value piece (very crude: assume moving piece is lowest value possible)
    if captures:
        best_move = captures[0][0]
        # If multiple captures with same value, pick one
        for move, val, _ in captures:
            if val == captures[0][1]:
                best_move = move
                break
        return best_move

    # 2. No captures: look for checks
    checks = []
    for move in legal_moves:
        if move.endswith('+') or move.endswith('#'):
            checks.append(move)
    if checks:
        # Prefer centralizing checks if possible (heuristic: move to central squares)
        central_squares = ['d4', 'e4', 'd5', 'e5']
        for move in checks:
            # extract target square from move (last part before +/#)
            target = move.replace('+', '').replace('#', '')
            if target[-2:] in central_squares:
                return move
        return checks[0]

    # 3. No captures, no checks: prioritize knight/bishop development and king safety
    # Heuristic: prefer moving knights/bishops toward center, avoid moving king unless castling
    castle_moves = [m for m in legal_moves if m.startswith('O-O')]
    if castle_moves:
        return castle_moves[0]  # prefer kingside, but either is fine

    # Prefer moving pieces to center squares
    center = ['d4', 'e4', 'd5', 'e5', 'c3', 'f3', 'c6', 'f6', 'd3', 'e3', 'd6', 'e6']
    for sq in center:
        for move in legal_moves:
            if move.replace('+', '').replace('#', '').endswith(sq):
                return move

    # Default: first legal move (should always be at least one)
    return legal_moves[0]
