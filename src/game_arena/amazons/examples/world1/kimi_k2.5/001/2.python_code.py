
import numpy as np
import time

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def get_legal_moves(board, player):
    """Generate all legal moves for the given player."""
    moves = []
    positions = np.argwhere(board == player)
    if len(positions) == 0:
        return moves
    
    for fr, fc in positions:
        for dr, dc in DIRECTIONS:
            tr, tc = fr + dr, fc + dc
            while 0 <= tr < 6 and 0 <= tc < 6 and board[tr, tc] == 0:
                # From (tr, tc), shoot arrow
                for ar, ac in DIRECTIONS:
                    arr, arc = tr + ar, tc + ac
                    while 0 <= arr < 6 and 0 <= arc < 6:
                        # Arrow can pass through/land on original square (fr, fc) which is now empty
                        if (arr == fr and arc == fc) or board[arr, arc] == 0:
                            moves.append((fr, fc, tr, tc, arr, arc))
                            arr += ar
                            arc += ac
                        else:
                            break
                tr += dr
                tc += dc
    return moves

def apply_move(board, move, player):
    """Return a new board after applying the move."""
    fr, fc, tr, tc, ar, ac = move
    new_board = board.copy()
    new_board[fr, fc] = 0
    new_board[tr, tc] = player
    new_board[ar, ac] = -1
    return new_board

def count_mobility(board, player):
    """Count queen-mobility (reachable squares) for the player."""
    count = 0
    positions = np.argwhere(board == player)
    for r, c in positions:
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                count += 1
                nr += dr
                nc += dc
    return count

def evaluate(board, player):
    """Evaluate board from player's perspective."""
    my_mob = count_mobility(board, player)
    opp_mob = count_mobility(board, 3 - player)
    return my_mob - 2 * opp_mob

def search(board, depth, alpha, beta, current_player, original_player, start_time, time_limit):
    """Alpha-beta search. Returns evaluation score."""
    if time.time() - start_time > time_limit:
        raise TimeoutError()
    
    if depth == 0:
        return evaluate(board, original_player)
    
    moves = get_legal_moves(board, current_player)
    if not moves:
        # Current player cannot move: if it's us, we lose; if opponent, we win
        return -10000 if current_player == original_player else 10000
    
    next_player = 3 - current_player
    
    if current_player == original_player:  # Maximizing
        value = -float('inf')
        for move in moves:
            new_board = apply_move(board, move, current_player)
            value = max(value, search(new_board, depth - 1, alpha, beta, next_player, 
                                     original_player, start_time, time_limit))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:  # Minimizing
        value = float('inf')
        for move in moves:
            new_board = apply_move(board, move, current_player)
            value = min(value, search(new_board, depth - 1, alpha, beta, next_player, 
                                     original_player, start_time, time_limit))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

def policy(board):
    """Select the best move using iterative deepening alpha-beta search."""
    start_time = time.time()
    time_limit = 0.9  # seconds
    
    moves = get_legal_moves(board, 1)
    if not moves:
        return "0,0:0,0:0,0"  # Should not happen per problem statement
    
    if len(moves) == 1:
        m = moves[0]
        return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"
    
    best_move = moves[0]
    depth = 1
    
    try:
        while True:
            best_value = -float('inf')
            alpha = -float('inf')
            beta = float('inf')
            current_best = moves[0]
            
            for move in moves:
                new_board = apply_move(board, move, 1)
                value = search(new_board, depth - 1, alpha, beta, 2, 1, start_time, time_limit)
                if value > best_value:
                    best_value = value
                    current_best = move
                alpha = max(alpha, best_value)
            
            # If we completed this depth within time, accept it
            best_move = current_best
            depth += 1
            
    except TimeoutError:
        pass
    
    m = best_move
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"
