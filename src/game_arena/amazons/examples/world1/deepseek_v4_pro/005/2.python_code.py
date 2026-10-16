
import time
import math
import random
import numpy as np

DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def get_moves(board, player):
    """Return all legal moves for `player` on `board` (tuple of tuples)."""
    moves = []
    for r in range(6):
        row = board[r]
        for c in range(6):
            if row[c] == player:
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == 0:
                        # Arrow shot from (nr, nc)
                        for ar_dr, ar_dc in DIRS:
                            ar_r, ar_c = nr + ar_dr, nc + ar_dc
                            while 0 <= ar_r < 6 and 0 <= ar_c < 6:
                                cell = board[ar_r][ar_c]
                                if cell == 0 or (ar_r == r and ar_c == c):
                                    moves.append((r, c, nr, nc, ar_r, ar_c))
                                    ar_r += ar_dr
                                    ar_c += ar_dc
                                else:
                                    break
                        nr += dr
                        nc += dc
    return moves


def apply_move(board, move, player):
    """Return a new board (tuple of tuples) after applying `move`."""
    fr, fc, tr, tc, ar, ac = move
    new_board = [list(row) for row in board]
    new_board[fr][fc] = 0
    new_board[tr][tc] = player
    new_board[ar][ac] = -1
    return tuple(tuple(row) for row in new_board)


def apply_move_list(board_list, move, player):
    """Return a new board (list of lists) after applying `move`."""
    fr, fc, tr, tc, ar, ac = move
    new_board = [row[:] for row in board_list]
    new_board[fr][fc] = 0
    new_board[tr][tc] = player
    new_board[ar][ac] = -1
    return new_board


def has_moves(board, player):
    """Return True if `player` has at least one legal move."""
    for r in range(6):
        row = board[r]
        for c in range(6):
            if row[c] == player:
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == 0:
                        for ar_dr, ar_dc in DIRS:
                            ar_r, ar_c = nr + ar_dr, nc + ar_dc
                            while 0 <= ar_r < 6 and 0 <= ar_c < 6:
                                cell = board[ar_r][ar_c]
                                if cell == 0 or (ar_r == r and ar_c == c):
                                    return True
                                else:
                                    break
                        nr += dr
                        nc += dc
    return False


def simulate(board, player):
    """Run a random playout from `board` with `player` to move. Return winner (1 or 2)."""
    board_list = [list(row) for row in board]
    current_player = player
    while True:
        moves = get_moves(board_list, current_player)
        if not moves:
            return 3 - current_player
        move = random.choice(moves)
        board_list = apply_move_list(board_list, move, current_player)
        current_player = 3 - current_player


def mcts(board_tuple, player, time_limit=0.9):
    """Monte Carlo Tree Search with UCB1. Returns the best move tuple."""
    # Check immediate winning move
    moves = get_moves(board_tuple, player)
    if not moves:
        return None
    for move in moves:
        new_board = apply_move(board_tuple, move, player)
        if not has_moves(new_board, 3 - player):
            return move
    if len(moves) == 1:
        return moves[0]

    root_state = (board_tuple, player)
    nodes = {root_state: {'visits': 0, 'total_value': 0.0, 'children': {}, 'unexpanded': None}}
    start_time = time.time()
    C = math.sqrt(2)

    while time.time() - start_time < time_limit:
        state = root_state
        path = []

        # Selection
        while True:
            node = nodes[state]
            if node['unexpanded'] is None:
                node['unexpanded'] = get_moves(state[0], state[1])
            if len(node['unexpanded']) > 0:
                break
            if not node['children']:
                break
            best_ucb = -float('inf')
            best_child = None
            for move, child_state in node['children'].items():
                child_node = nodes[child_state]
                if child_node['visits'] == 0:
                    ucb = float('inf')
                else:
                    ucb = (child_node['total_value'] / child_node['visits'] +
                           C * math.sqrt(math.log(node['visits']) / child_node['visits']))
                if ucb > best_ucb:
                    best_ucb = ucb
                    best_child = child_state
            if best_child is None:
                break
            path.append(state)
            state = best_child

        node = nodes[state]
        # Expansion
        if node['unexpanded'] and len(node['unexpanded']) > 0:
            move = node['unexpanded'].pop()
            new_board = apply_move(state[0], move, state[1])
            next_player = 3 - state[1]
            child_state = (new_board, next_player)
            node['children'][move] = child_state
            if child_state not in nodes:
                nodes[child_state] = {'visits': 0, 'total_value': 0.0, 'children': {}, 'unexpanded': None}
            path.append(state)
            state = child_state
            winner = simulate(state[0], state[1])
        else:
            # Terminal state
            winner = 3 - state[1]

        path.append(state)
        # Backpropagation
        for s in path:
            node = nodes[s]
            node['visits'] += 1
            if s[1] == winner:
                node['total_value'] += 1.0

    root_node = nodes[root_state]
    best_move = None
    best_visits = -1
    for move, child_state in root_node['children'].items():
        visits = nodes[child_state]['visits']
        if visits > best_visits:
            best_visits = visits
            best_move = move
    if best_move is None:
        best_move = random.choice(moves)
    return best_move


def policy(board):
    """Main policy function. `board` is a 6x6 numpy array."""
    # Convert to immutable tuple of tuples
    board_tuple = tuple(tuple(int(cell) for cell in row) for row in board)
    move = mcts(board_tuple, 1, time_limit=0.95)
    if move is None:
        moves = get_moves(board_tuple, 1)
        if moves:
            move = random.choice(moves)
        else:
            # Should never be reached if the game is still ongoing
            return "0,0:0,1:0,2"
    return f"{move[0]},{move[1]}:{move[2]},{move[3]}:{move[4]},{move[5]}"
