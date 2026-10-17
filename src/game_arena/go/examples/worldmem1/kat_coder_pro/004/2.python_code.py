
import numpy as np
from collections import defaultdict

# Constants
BOARD_SIZE = 19
PASS = (0, 0)
EMPTY = 0
ME = 1
OPPONENT = 2

def is_on_board(row, col):
    """Check if a position is on the board."""
    return 1 <= row <= BOARD_SIZE and 1 <= col <= BOARD_SIZE

def get_neighbors(row, col):
    """Get the four orthogonal neighbors of a point."""
    neighbors = []
    if row > 1:
        neighbors.append((row - 1, col))
    if row < BOARD_SIZE:
        neighbors.append((row + 1, col))
    if col > 1:
        neighbors.append((row, col - 1))
    if col < BOARD_SIZE:
        neighbors.append((row, col + 1))
    return neighbors

def find_connected_group(board, row, col, color):
    """Find the connected group of stones of the same color."""
    group = set()
    stack = [(row, col)]
    while stack:
        r, c = stack.pop()
        if (r, c) in group:
            continue
        group.add((r, c))
        for nr, nc in get_neighbors(r, c):
            if board[nr, nc] == color and (nr, nc) not in group:
                stack.append((nr, nc))
    return group

def has_liberties(board, group):
    """Check if a group has any liberties."""
    for r, c in group:
        for nr, nc in get_neighbors(r, c):
            if board[nr, nc] == EMPTY:
                return True
    return False

def remove_stones(board, group):
    """Remove a group of stones from the board."""
    for r, c in group:
        board[r, c] = EMPTY

def is_legal_move(board, row, col, color):
    """Check if a move is legal."""
    if not is_on_board(row, col):
        return False
    if board[row, col] != EMPTY:
        return False

    # Temporarily place the stone
    board[row, col] = color

    # Check if the move captures any opponent stones
    opponent_color = OPPONENT if color == ME else ME
    captured_any = False
    for nr, nc in get_neighbors(row, col):
        if board[nr, nc] == opponent_color:
            group = find_connected_group(board, nr, nc, opponent_color)
            if not has_liberties(board, group):
                captured_any = True
                break

    # Check suicidal rule
    my_group = find_connected_group(board, row, col, color)
    is_suicidal = not has_liberties(board, my_group) and not captured_any

    # Restore the board
    board[row, col] = EMPTY

    return not is_suicidal

def simulate_game(board, me_color):
    """Simulate a random game from the current position."""
    current_board = board.copy()
    current_player = me_color

    while True:
        # Get all legal moves
        legal_moves = []
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                if is_legal_move(current_board, r, c, current_player):
                    legal_moves.append((r, c))

        # If no legal moves, pass
        if not legal_moves:
            current_player = ME if current_player == OPPONENT else OPPONENT
            continue

        # Randomly choose a move
        move = legal_moves[np.random.randint(len(legal_moves))]
        r, c = move
        current_board[r, c] = current_player

        # Remove captured opponent stones
        opponent_color = ME if current_player == OPPONENT else OPPONENT
        for nr, nc in get_neighbors(r, c):
            if current_board[nr, nc] == opponent_color:
                group = find_connected_group(current_board, nr, nc, opponent_color)
                if not has_liberties(current_board, group):
                    remove_stones(current_board, group)

        # Check if game is over (both players pass)
        if current_player == me_color:
            # Check if opponent has any legal moves
            opponent_legal_moves = []
            for r in range(1, BOARD_SIZE + 1):
                for c in range(1, BOARD_SIZE + 1):
                    if is_legal_move(current_board, r, c, OPPONENT):
                        opponent_legal_moves.append((r, c))
            if not opponent_legal_moves:
                break
        else:
            # Check if we have any legal moves
            me_legal_moves = []
            for r in range(1, BOARD_SIZE + 1):
                for c in range(1, BOARD_SIZE + 1):
                    if is_legal_move(current_board, r, c, ME):
                        me_legal_moves.append((r, c))
            if not me_legal_moves:
                break

        current_player = ME if current_player == OPPONENT else OPPONENT

    # Count score (simplified: just count stones)
    me_score = np.sum(current_board == ME)
    opponent_score = np.sum(current_board == OPPONENT)

    return me_score - opponent_score

def policy(me, opponent, memory):
    # Initialize memory if empty
    if not memory:
        memory['board'] = np.zeros((BOARD_SIZE + 1, BOARD_SIZE + 1), dtype=int)
        memory['last_move'] = None
        memory['move_count'] = 0

    board = memory['board']

    # Update board from input
    board.fill(EMPTY)
    for r, c in me:
        board[r, c] = ME
    for r, c in opponent:
        board[r, c] = OPPONENT

    me_color = ME  # We are always ME

    # Get all legal moves
    legal_moves = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if is_legal_move(board, r, c, me_color):
                legal_moves.append((r, c))

    # If no legal moves, pass
    if not legal_moves:
        return PASS, memory

    # Monte Carlo Tree Search
    # We'll do a simplified version: random playouts for each legal move
    move_scores = defaultdict(int)

    # Number of simulations per move (adjustable based on time constraints)
    simulations_per_move = 5

    for move in legal_moves:
        r, c = move
        total_score = 0

        for _ in range(simulations_per_move):
            # Create a copy of the board
            sim_board = board.copy()

            # Make the move
            sim_board[r, c] = me_color

            # Remove captured opponent stones
            for nr, nc in get_neighbors(r, c):
                if sim_board[nr, nc] == OPPONENT:
                    group = find_connected_group(sim_board, nr, nc, OPPONENT)
                    if not has_liberties(sim_board, group):
                        remove_stones(sim_board, group)

            # Simulate the rest of the game
            score = simulate_game(sim_board, OPPONENT)  # Opponent plays next
            total_score += score

        move_scores[move] = total_score

    # Choose the move with the highest score
    best_move = max(move_scores, key=move_scores.get)

    # Update memory
    memory['last_move'] = best_move
    memory['move_count'] += 1

    return best_move, memory
