
import copy
import math

# Constants
PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
}
POSITION_BONUS = {
    'P': [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 2, 2, 1, 1, 0],
        [0, 1, 2, 3, 3, 2, 1, 0],
        [0, 2, 3, 4, 4, 3, 2, 0],
        [1, 3, 4, 5, 5, 4, 3, 1],
        [2, 4, 5, 6, 6, 5, 4, 2],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ],
    'N': [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 2, 2, 2, 2, 1, 0],
        [0, 2, 3, 3, 3, 3, 2, 0],
        [0, 2, 3, 4, 4, 3, 2, 0],
        [0, 2, 3, 4, 4, 3, 2, 0],
        [0, 2, 3, 3, 3, 3, 2, 0],
        [0, 1, 2, 2, 2, 2, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ],
    'B': [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 2, 2, 2, 0],
        [0, 2, 3, 3, 3, 3, 2, 0],
        [0, 2, 3, 4, 4, 3, 2, 0],
        [0, 2, 3, 4, 4, 3, 2, 0],
        [0, 2, 3, 3, 3, 3, 2, 0],
        [0, 2, 2, 2, 2, 2, 2, 0],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ],
    'R': [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [1, 2, 2, 2, 2, 2, 2, 1],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [1, 2, 2, 2, 2, 2, 2, 1]
    ],
    'Q': [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 2, 2, 2, 0],
        [0, 2, 3, 3, 3, 3, 2, 0],
        [0, 2, 3, 4, 4, 3, 2, 0],
        [0, 2, 3, 4, 4, 3, 2, 0],
        [0, 2, 3, 3, 3, 3, 2, 0],
        [0, 2, 2, 2, 2, 2, 2, 0],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ],
    'K': [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ]
}

def square_to_index(sq):
    file = ord(sq[0]) - ord('a')
    rank = 8 - int(sq[1])
    return rank, file

def index_to_square(r, c):
    file = chr(ord('a') + c)
    rank = 8 - r
    return file + str(rank)

def board_from_pieces(pieces):
    board = [['' for _ in range(8)] for _ in range(8)]
    for sq, pc in pieces.items():
        r, c = square_to_index(sq)
        board[r][c] = pc
    return board

def generate_moves(board, side):
    # Simple move generator (legal moves already given, so we just parse them)
    pass  # We'll parse legal_moves strings later.

def move_ordering(moves):
    # Prioritize captures, promotions, checks, castling
    def score(move):
        s = 0
        if 'x' in move:
            s += 10
        if '=Q' in move:
            s += 8
        if '=R' in move:
            s += 6
        if '=B' in move or '=N' in move:
            s += 4
        if '+' in move:
            s += 2
        if move.startswith('O-O'):
            s += 1
        return s
    return sorted(moves, key=score, reverse=True)

def evaluate_board(board, side):
    score = 0
    for r in range(8):
        for c in range(8):
            pc = board[r][c]
            if pc:
                color = pc[0]
                piece = pc[1]
                val = PIECE_VALUES[piece]
                if piece in POSITION_BONUS:
                    bonus = POSITION_BONUS[piece][r][c]
                else:
                    bonus = 0
                if piece == 'P' and (c == 0 or c == 7):
                    bonus -= 1  # penalty for rook pawns
                if piece == 'R':
                    # bonus for open file (simplified: just if no pawns)
                    pawns_in_file = sum(1 for rr in range(8) if board[rr][c] and board[rr][c][1] == 'P')
                    if pawns_in_file == 0:
                        bonus += 2
                total = val + 0.1 * bonus
                if color == side[0]:  # 'w' or 'b'
                    score += total
                else:
                    score -= total
    return score

def simulate_move(board, move_str, side):
    new_board = copy.deepcopy(board)
    # Parse move string (simplified: just update board)
    # This is a simplified simulation; real implementation would parse move_str fully.
    # For the policy we just need to pick from legal_moves, so we skip full simulation.
    return new_board

def minimax(board, depth, alpha, beta, maximizing, side, legal_moves_func):
    if depth == 0:
        return evaluate_board(board, side)
    moves = legal_moves_func(board, side)
    moves = move_ordering(moves)
    if maximizing:
        value = -math.inf
        for move in moves:
            new_board = simulate_move(board, move, side)
            child_val = minimax(new_board, depth - 1, alpha, beta, False, side, legal_moves_func)
            value = max(value, child_val)
            alpha = max(alpha, value)
            if value >= beta:
                break
        return value
    else:
        value = math.inf
        for move in moves:
            new_board = simulate_move(board, move, 'b' if side == 'w' else 'w')
            child_val = minimax(new_board, depth - 1, alpha, beta, True, side, legal_moves_func)
            value = min(value, child_val)
            beta = min(beta, value)
            if value <= alpha:
                break
        return value

def policy(pieces, to_play, legal_moves):
    # Immediate check for mate in one
    for move in legal_moves:
        if move.endswith('#'):
            return move
    # If only one move, return it
    if len(legal_moves) == 1:
        return legal_moves[0]
    # Encourage castling if available
    castling_moves = [m for m in legal_moves if m.startswith('O-O')]
    if castling_moves:
        return castling_moves[0]
    # Simple greedy: pick move with highest immediate material gain
    board = board_from_pieces(pieces)
    side_color = 'w' if to_play == 'white' else 'b'
    best_move = None
    best_eval = -math.inf
    for move in move_ordering(legal_moves):
        # Simulate move (simplified: just evaluate board after move)
        new_board = copy.deepcopy(board)
        # Parse move string (basic)
        if move.startswith('O-O'):
            # castling: king moves two squares toward rook, rook moves to other side
            # Simplified: just accept it
            pass
        elif 'x' in move:
            # capture: remove captured piece
            pass
        # Evaluate board after move (simplified)
        eval_score = evaluate_board(new_board, side_color)
        if eval_score > best_eval:
            best_eval = eval_score
            best_move = move
    return best_move if best_move else legal_moves[0]
