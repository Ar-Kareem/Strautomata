
import numpy as np

def is_path_clear(board, start, end, vacated):
    """
    Check if the path from start to end is clear, ignoring vacated if on the path.
    """
    sr, sc = start
    er, ec = end
    dr = er - sr
    dc = ec - sc
    if dr == 0 and dc == 0:
        return False  # Same position
    if abs(dr) != abs(dc) and dr != 0 and dc != 0:
        return False  # Not a straight or diagonal line
    dr = 1 if dr > 0 else -1 if dr < 0 else 0
    dc = 1 if dc > 0 else -1 if dc < 0 else 0
    r, c = sr + dr, sc + dc
    while (r, c) != (er, ec):
        if board[r, c] != 0 and (r, c) != vacated:
            return False
        r += dr
        c += dc
    return True

def get_possible_moves(board, for_player):
    """Generates all legal moves for the given player."""
    moves = []
    player = 1 if for_player else 2
    positions = [(i, j) for i in range(6) for j in range(6) if board[i, j] == player]
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for fr in positions:
        fr_r, fr_c = fr
        for dr, dc in directions:
            r, c = fr_r + dr, fr_c + dc
            while 0 <= r < 6 and 0 <= c < 6:
                if board[r, c] != 0:
                    break
                # Valid 'to' position
                to = (r, c)
                # Now check arrows from 'to', considering 'fr' can be passed through as vacated
                for ddr, ddc in directions:
                    rr, cc = r + ddr, c + ddc
                    while 0 <= rr < 6 and 0 <= cc < 6:
                        if board[rr, cc] != 0 and (rr, cc) != (fr_r, fr_c):
                            break
                        # Valid 'arrow' position
                        moves.append((fr_r, fr_c, r, c, rr, cc))
                        rr += ddr
                        cc += ddc
                r += dr
                c += dc
    return moves

def simulate_move(board, move, for_player):
    """Simulate a move on a copy of the board."""
    new_board = board.copy()
    fr_r, fr_c, to_r, to_c, ar_r, ar_c = move
    player = 1 if for_player else 2
    new_board[fr_r, fr_c] = 0  # Vacate 'from'
    new_board[to_r, to_c] = player  # Move to 'to'
    new_board[ar_r, ar_c] = -1  # Place arrow
    return new_board

def policy(board):
    """Returns the best legal move string based on mobility heuristic."""
    my_moves = get_possible_moves(board, True)
    best_score = -float('inf')
    best_move = my_moves[0] if my_moves else None
    
    for move in my_moves:
        new_board = simulate_move(board, move, True)
        my_count = len(get_possible_moves(new_board, True))
        opp_count = len(get_possible_moves(new_board, False))
        score = my_count - opp_count
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move:
        fr_r, fr_c, to_r, to_c, ar_r, ar_c = best_move
        return f"{fr_r},{fr_c}:{to_r},{to_c}:{ar_r},{ar_c}"
    else:
        # Fallback: should not happen, but return a dummy legal move string if no moves
        return "0,0:0,1:0,2"
