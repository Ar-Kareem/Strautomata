
import numpy as np
import random
import time
import math

# -------------------- Move Generation --------------------
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),           (0, 1),
              (1, -1),  (1, 0),  (1, 1)]

def generate_moves(board, player):
    """Return a list of legal move strings for the given player."""
    moves = []
    b = board
    # Find all positions occupied by the player's amazons
    rows, cols = np.where(b == player)
    for r, c in zip(rows, cols):
        # --- Amazon movement ---
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and b[nr, nc] == 0:
                # Create a temporary board with the amazon moved
                b2 = b.copy()
                b2[r, c] = 0
                b2[nr, nc] = player
                # --- Arrow shot from (nr, nc) ---
                for adr, adc in DIRECTIONS:
                    anr, anc = nr + adr, nc + adc
                    while 0 <= anr < 6 and 0 <= anc < 6 and b2[anr, anc] == 0:
                        # b2 has (r,c) set to 0, so vacated square is free
                        moves.append(f"{r},{c}:{nr},{nc}:{anr},{anc}")
                        anr += adr
                        anc += adc
                nr += dr
                nc += dc
    return moves

def apply_move(board, move_str, player):
    """Apply a move string to a board copy and return the new board state."""
    fr_fc, to, arrow = move_str.split(':')
    fr, fc = map(int, fr_fc.split(','))
    tr, tc = map(int, to.split(','))
    ar, ac = map(int, arrow.split(','))

    new_board = board.copy()
    new_board[fr, fc] = 0   # vacate
    new_board[tr, tc] = player  # move amazon
    new_board[ar, ac] = -1      # shoot arrow
    return new_board

# -------------------- MCTS Node --------------------
class Node:
    __slots__ = ('board', 'player', 'parent', 'move', 'children',
                 'visits', 'value', 'untried_moves')
    def __init__(self, board, player, parent=None, move=None):
        self.board = board
        self.player = player      # 1 or 2
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.value = 0.0          # sum of rewards from this node's player perspective
        self.untried_moves = None  # lazy generation

    def is_terminal(self):
        moves = self.get_legal_moves()
        return not moves

    def get_legal_moves(self):
        if self.untried_moves is None:
            self.untried_moves = generate_moves(self.board, self.player)
        return self.untried_moves

# -------------------- MCTS Core --------------------
def ucb1(child, parent_visits, c=1.4):
    if child.visits == 0:
        return float('inf')
    # child.value is from child's player perspective.
    # Parent wants to maximize the negative of that (zero-sum).
    avg = child.value / child.visits   # [-1, 1]
    parent_avg = -avg
    exploration = c * math.sqrt(math.log(parent_visits) / child.visits)
    return parent_avg + exploration

def simulate(board, player):
    """Random rollout from the current state. Returns the winner (1 or 2)."""
    current = player
    b = board.copy()
    while True:
        moves = generate_moves(b, current)
        if not moves:
            # current player has no moves -> loses, opponent wins
            return 3 - current
        move = random.choice(moves)
        b = apply_move(b, move, current)
        current = 3 - current

def backpropagate(node, winner):
    """Backpropagate the result up the tree."""
    while node is not None:
        node.visits += 1
        if node.player == winner:
            node.value += 1
        else:
            node.value -= 1
        node = node.parent

def mcts(board, time_limit=0.95):
    root = Node(board, player=1)
    start = time.time()
    while time.time() - start < time_limit:
        # Selection
        node = root
        while True:
            if node.is_terminal():
                break
            # Lazy generation of legal moves
            if node.untried_moves is None:
                node.get_legal_moves()
            if len(node.untried_moves) == 0 and node.children:
                # Fully expanded, pick best UCB child
                node = max(node.children, key=lambda c: ucb1(c, node.visits))
            else:
                break

        # Expansion
        if not node.is_terminal():
            move = random.choice(node.untried_moves)
            node.untried_moves.remove(move)
            new_board = apply_move(node.board, move, node.player)
            child = Node(new_board, player=3 - node.player,
                         parent=node, move=move)
            node.children.append(child)
            node = child

        # Simulation
        winner = simulate(node.board, node.player)
        # Backpropagation
        backpropagate(node, winner)

    # Choose best child by visit count
    if not root.children:
        # fallback in case something went wrong
        moves = generate_moves(board, 1)
        return moves[0] if moves else "0,0:0,0:0,0"

    best = max(root.children, key=lambda c: c.visits)
    return best.move

# -------------------- Required API --------------------
def policy(board) -> str:
    """
    Given a 6x6 board (numpy array), return the best move string.
    board values: 0=empty, 1=our amazon, 2=opponent amazon, -1=arrow.
    """
    return mcts(board, time_limit=0.95)
