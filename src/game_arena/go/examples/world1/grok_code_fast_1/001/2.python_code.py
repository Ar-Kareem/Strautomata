
import numpy as np
import random

def get_neighbors(r, c):
    return [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]

def is_on_board(r, c):
    return 1 <= r <= 19 and 1 <= c <= 19

def get_board(me, opponent):
    board = np.zeros((21, 21), dtype=int)  # 1: me, 2: opponent, 0: empty
    for r, c in me:
        board[r, c] = 1
    for r, c in opponent:
        board[r, c] = 2
    return board

def find_group(board, r, c, visited=None):
    if visited is None:
        visited = set()
    if (r, c) in visited:
        return set()
    visited.add((r, c))
    group = {(r, c)}
    color = board[r, c]
    for nr, nc in get_neighbors(r, c):
        if is_on_board(nr, nc) and board[nr, nc] == color and (nr, nc) not in visited:
            group.update(find_group(board, nr, nc, visited))
    return group

def get_liberties(board, r, c):
    group = find_group(board, r, c)
    libs = set()
    for gr, gc in group:
        for nbr, nbc in get_neighbors(gr, gc):
            if is_on_board(nbr, nbc) and board[nbr, nbc] == 0:
                libs.add((nbr, nbc))
    return len(libs)

def is_legal(board, r, c, player):
    if not is_on_board(r, c) or board[r, c] != 0:
        return False
    # Temporarily place stone
    board[r, c] = player
    liberties = get_liberties(board, r, c)
    captures = False
    opponent = 3 - player
    for nr, nc in get_neighbors(r, c):
        if is_on_board(nr, nc) and board[nr, nc] == opponent:
            opp_group = find_group(board, nr, nc)
            opp_libs = set()
            for gr, gc in opp_group:
                for nbr, nbc in get_neighbors(gr, gc):
                    if is_on_board(nbr, nbc) and board[nbr, nbc] == 0:
                        opp_libs.add((nbr, nbc))
            if len(opp_libs) == 0:
                captures = True
                break
    # Undo placement
    board[r, c] = 0
    if liberties == 0 and not captures:
        return False
    return True

def heuristic(board, r, c, player):
    score = 0
    opponent = 3 - player
    for nr, nc in get_neighbors(r, c):
        if is_on_board(nr, nc):
            cell = board[nr, nc]
            if cell == player:
                score += 1  # Adjacent to own stone (connect)
            elif cell == opponent:
                score += 2  # Adjacent to opponent stone (potential capture)
    return score

def policy(me, opponent):
    board = get_board(me, opponent)
    legal_moves = []
    for r in range(1, 20):
        for c in range(1, 20):
            if is_legal(board, r, c, 1):  # Check for 'me' as player 1
                legal_moves.append((r, c))
    if not legal_moves:
        return (0, 0)  # Pass if no legal moves
    # Evaluate and select best move
    max_score = -1
    best_moves = []
    for move in legal_moves:
        score = heuristic(board, move[0], move[1], 1)
        if score > max_score:
            max_score = score
            best_moves = [move]
        elif score == max_score:
            best_moves.append(move)
    return random.choice(best_moves)
