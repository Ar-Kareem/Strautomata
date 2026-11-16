
import numpy as np

def get_queen_moves(board, r, c, allow_through=None):
    moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 6 and 0 <= nc < 6:
            if (allow_through is None or (nr, nc) != allow_through) and board[nr, nc] != 0:
                break
            if board[nr, nc] == 0:
                moves.append((nr, nc))
            nr += dr
            nc += dc
    return moves

def apply_move(board, move_str):
    parts = move_str.split(':')
    fr, fc = map(int, parts[0].split(','))
    tr, tc = map(int, parts[1].split(','))
    ar, ac = map(int, parts[2].split(','))
    new_board = board.copy()
    new_board[fr, fc] = 0  # Vacate from
    new_board[tr, tc] = 1  # Move to to
    new_board[ar, ac] = -1  # Place arrow
    return new_board

def count_legal_moves(board, player):
    count = 0
    player_positions = [(r, c) for r in range(6) for c in range(6) if board[r, c] == player]
    for pr, pc in player_positions:
        tos = get_queen_moves(board, pr, pc)
        for tr, tc in tos:
            temp_board = board.copy()
            temp_board[pr, pc] = 0
            temp_board[tr, tc] = player  # Temporarily place here for arrow check
            arrows = [pos for pos in get_queen_moves(temp_board, tr, tc) if pos != (pr, pc) and pos != (tr, tc)]
            count += len(arrows)
    return count

def generate_legal_moves(board):
    moves = []
    player_positions = [(r, c) for r in range(6) for c in range(6) if board[r, c] == 1]
    for fr, fc in player_positions:
        tos = get_queen_moves(board, fr, fc)
        for tr, tc in tos:
            temp_board = board.copy()
            temp_board[fr, fc] = 0
            temp_board[tr, tc] = 1
            arrows = [pos for pos in get_queen_moves(temp_board, tr, tc) if pos != (tr, tc)]
            for ar, ac in arrows:
                moves.append(f"{fr},{fc}:{tr},{tc}:{ar},{ac}")
    return moves

def policy(board):
    if not board.flags.c_contiguous:  # Ensure numpy array is C-contiguous
        board = np.ascontiguousarray(board)
    legal_moves = generate_legal_moves(board)
    if not legal_moves:
        # Should not happen, but robustness: return invalid move or something; but per rules, it won't be called.
        return "0,0:0,1:0,2"  # Dummy, but not legal; won't be reached.
    
    best_move = None
    best_score = float('-inf')
    for move in legal_moves:
        new_board = apply_move(board, move)
        my_moves = count_legal_moves(new_board, 1)
        opp_moves = count_legal_moves(new_board, 2)
        score = my_moves - opp_moves
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
