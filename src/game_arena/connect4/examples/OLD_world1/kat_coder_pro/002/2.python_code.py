
import numpy as np
import random
import math

# Constants
ROWS = 6
COLS = 7
PLAYER = 1
OPPONENT = -1

class Node:
    def __init__(self, board, col, parent=None):
        self.board = board
        self.col = col
        self.parent = parent
        self.children = []
        self.visits = 0
        self.score = 0.0
        self.untried_cols = self.get_valid_moves(board)

    def get_valid_moves(self, board):
        valid_cols = []
        for col in range(COLS):
            if board[0][col] == 0:
                valid_cols.append(col)
        return valid_cols

    def is_fully_expanded(self):
        return len(self.untried_cols) == 0

    def best_child(self, c_param=1.41):
        choices_weights = []
        for child in self.children:
            if child.visits > 0:
                exploitation = child.score / child.visits
                exploration = math.sqrt((2 * math.log(self.visits)) / child.visits)
                weight = exploitation + c_param * exploration
            else:
                weight = float('inf')
            choices_weights.append(weight)
        return self.children[np.argmax(choices_weights)]

def is_valid_position(row, col):
    return 0 <= row < ROWS and 0 <= col < COLS

def check_win(board, player):
    # Horizontal check
    for r in range(ROWS):
        for c in range(COLS - 3):
            if board[r][c] == player and board[r][c+1] == player and \
               board[r][c+2] == player and board[r][c+3] == player:
                return True

    # Vertical check
    for r in range(ROWS - 3):
        for c in range(COLS):
            if board[r][c] == player and board[r+1][c] == player and \
               board[r+2][c] == player and board[r+3][c] == player:
                return True

    # Diagonal (positive slope) check
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if board[r][c] == player and board[r+1][c+1] == player and \
               board[r+2][c+2] == player and board[r+3][c+3] == player:
                return True

    # Diagonal (negative slope) check
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if board[r][c] == player and board[r-1][c+1] == player and \
               board[r-2][c+2] == player and board[r-3][c+3] == player:
                return True

    return False

def is_board_full(board):
    return all(board[0][c] != 0 for c in range(COLS))

def make_move(board, col, player):
    new_board = [row[:] for row in board]
    for r in range(ROWS - 1, -1, -1):
        if new_board[r][col] == 0:
            new_board[r][col] = player
            return new_board, r, col
    return None, -1, -1

def get_opponent(player):
    return -player

def evaluate_window(window, player):
    score = 0
    opponent = get_opponent(player)

    if window.count(player) == 4:
        score += 100
    elif window.count(player) == 3 and window.count(0) == 1:
        score += 5
    elif window.count(player) == 2 and window.count(0) == 2:
        score += 2

    if window.count(opponent) == 4:
        score -= 100
    elif window.count(opponent) == 3 and window.count(0) == 1:
        score -= 4

    return score

def score_position(board, player):
    score = 0

    # Center column preference
    center_col = [board[r][COLS // 2] for r in range(ROWS)]
    center_count = center_col.count(player)
    score += center_count * 3

    # Horizontal scoring
    for r in range(ROWS):
        row_array = [board[r][c] for c in range(COLS)]
        for c in range(COLS - 3):
            window = row_array[c:c+4]
            score += evaluate_window(window, player)

    # Vertical scoring
    for c in range(COLS):
        col_array = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS - 3):
            window = col_array[r:r+4]
            score += evaluate_window(window, player)

    # Diagonal (positive slope) scoring
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, player)

    # Diagonal (negative slope) scoring
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r-i][c+i] for i in range(4)]
            score += evaluate_window(window, player)

    return score

def mcts_policy(board):
    root = Node(board, None)

    if not root.untried_cols:
        return random.choice([c for c in range(COLS) if board[0][c] == 0])

    simulations = 1000

    for _ in range(simulations):
        node = root
        current_board = [row[:] for row in board]
        current_player = PLAYER

        # Selection
        while not node.is_fully_expanded() and node.children:
            node = node.best_child()
            current_board, _, _ = make_move(current_board, node.col, current_player)
            current_player = get_opponent(current_player)

        # Expansion
        if node.untried_cols:
            col = random.choice(node.untried_cols)
            node.untried_cols.remove(col)
            new_board, r, c = make_move(current_board, col, current_player)
            if new_board:
                child_node = Node(new_board, col, parent=node)
                node.children.append(child_node)
                node = child_node
                current_board = new_board

        # Simulation
        temp_board = [row[:] for row in current_board]
        temp_player = current_player
        while True:
            valid_moves = [c for c in range(COLS) if temp_board[0][c] == 0]
            if not valid_moves or check_win(temp_board, PLAYER) or check_win(temp_board, OPPONENT) or is_board_full(temp_board):
                break

            col = random.choice(valid_moves)
            temp_board, _, _ = make_move(temp_board, col, temp_player)
            temp_player = get_opponent(temp_player)

        # Backpropagation
        score = 0
        if check_win(temp_board, PLAYER):
            score = 1
        elif check_win(temp_board, OPPONENT):
            score = -1

        while node:
            node.visits += 1
            node.score += score
            node = node.parent

    best_move = root.best_child()
    return best_move.col

def policy(board: list[list[int]]) -> int:
    board = [row[:] for row in board]
    valid_moves = [c for c in range(COLS) if board[0][c] == 0]

    if not valid_moves:
        return 0

    # Check for immediate win
    for col in valid_moves:
        new_board, r, c = make_move(board, col, PLAYER)
        if new_board and check_win(new_board, PLAYER):
            return col

    # Block opponent's immediate win
    for col in valid_moves:
        new_board, r, c = make_move(board, col, OPPONENT)
        if new_board and check_win(new_board, OPPONENT):
            return col

    # Use MCTS
    return mcts_policy(board)
