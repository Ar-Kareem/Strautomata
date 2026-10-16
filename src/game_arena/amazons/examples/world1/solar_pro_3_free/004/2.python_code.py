
import numpy as np
import random
import math

# --- board constants ---
BOARD_SIZE = 6
QUEEN_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
              (-1, -1), (-1, 1), (1, -1), (1, 1)]
C = math.sqrt(2)          # UCT exploration constant
MAX_ITER = 2000            # number of MCTS iterations per call

# --- helper functions ---
def generate_legal_moves(board: np.ndarray, side: int) -> list:
    """
    Return a list of legal moves for a given side (1 = our amazon, 2 = opponent).
    Each move is a tuple (from_r, from_c, to_r, to_c, arrow_r, arrow_c).
    """
    moves = []
    amazon_pos = list(np.argwhere(board == side))
    opponent_side = 2 if side == 1 else 1

    for (from_r, from_c) in amazon_pos:
        for dr, dc in QUEEN_DIRS:
            step = 1
            while True:
                to_r = from_r + step * dr
                to_c = from_c + step * dc
                # queen move must stay inside board and land on an empty square
                if not (0 <= to_r < BOARD_SIZE and 0 <= to_c < BOARD_SIZE):
                    break
                if board[to_r, to_c] != 0:   # cannot jump over anything
                    break

                # Queen landing square is legal; now generate arrow shots
                dest = (to_r, to_c)
                for ar in QUEEN_DIRS:
                    arr = dest[0] + ar[0]
                    acc = dest[1] + ar[1]
                    arrow_target = None
                    last_empty = None
                    while True:
                        if not (0 <= arr < BOARD_SIZE and 0 <= acc < BOARD_SIZE):
                            break
                        piece = board[arr, acc]
                        if piece == opponent_side:          # arrow kills opponent amazon
                            arrow_target = (arr, acc)
                            break
                        if piece != 0:                      # blocked by arrow or own amazon
                            break
                        # empty square → continue scanning
                        last_empty = (arr, acc)
                        arr += ar[0]
                        acc += ar[1]

                    if arrow_target:
                        moves.append((from_r, from_c, to_r, to_c,
                                      arrow_target[0], arrow_target[1]))
                    elif last_empty:
                        # last empty square in that direction is a legal arrow target
                        moves.append((from_r, from_c, to_r, to_c,
                                      last_empty[0], last_empty[1]))
                step += 1
    return moves

def apply_move(board: np.ndarray, move_str: str) -> np.ndarray:
    """
    Apply a move string to a board and return the resulting board.
    """
    frm, to, arr = move_str.split(':')
    frm_r, frm_c = map(int, frm.split(','))
    to_r, to_c   = map(int,   to.split(','))
    arr_r, arr_c = map(int,   arr.split(','))

    new_board = board.copy()
    new_board[frm_r, frm_c] = 0                     # empty start square
    new_board[to_r, to_c]   = 1                     # our amazon lands
    new_board[arr_r, arr_c] = -1                    # arrow (blocked) square
    return new_board

def evaluate(board: np.ndarray) -> int:
    """Simple heuristic: our amazons minus opponent amazons."""
    ours = np.count_nonzero(board == 1)
    theirs = np.count_nonzero(board == 2)
    return ours - theirs

# --- tree node for MCTS ---
class Node:
    __slots__ = ('board', 'move', 'children', 'visits', 'wins', 'turn')

    def __init__(self, board: np.ndarray, move: str | None = None, turn: bool = True):
        self.board = board
        self.move = move
        self.children = []
        self.visits = 0
        self.wins = 0
        self.turn = turn                     # True = our side, False = opponent

    def is_terminal(self) -> bool:
        # Terminal if neither side can move any longer
        our_moves = generate_legal_moves(self.board, 1)
        opp_moves = generate_legal_moves(self.board, 2)
        return not our_moves and not opp_moves

# --- UCT selection helper ---
def select_best_child(parent: Node, exploration_const: float) -> Node:
    if not parent.children:
        return parent                     # just return the leaf node
    total_visits = parent.visits
    ucb_vals = [
        (c.wins / c.visits) +
        exploration_const * math.sqrt(math.log(total_visits) / c.visits)
        for c in parent.children
    ]
    max_idx = max(range(len(ucb_vals)), key=lambda i: ucb_vals[i])
    return parent.children[max_idx]

# --- random playout from a node until terminal ---
def simulate_random(node: Node) -> int:
    """Play a random game from node to terminal and return:
       1 = we win, -1 = we lose, 0 = draw."""
    board = node.board.copy()
    turn = node.turn                      # True = us, False = opponent

    while True:
        # Obtain legal moves for the player whose turn it is
        if turn:
            moves = generate_legal_moves(board, 1)
        else:
            moves = generate_legal_moves(board, 2)

        if not moves:                     # current player has no moves → game ends
            break

        move = random.choice(moves)
        board = apply_move(board, move)
        turn = not turn                    # switch side

        # Check if both sides are stuck
        moves_now = generate_legal_moves(board, 1)
        moves_opp = generate_legal_moves(board, 2)
        if not moves_now and not moves_opp:
            break

    # Evaluate final board
    score = evaluate(board)
    if score > 0:
        return 1
    if score < 0:
        return -1
    return 0

# --- main policy function ---
def policy(board: np.ndarray) -> str:
    """
    Choose the best move for the given board state.
    Returns a legal move string: "from_row,from_col:to_row,to_col:arrow_row,arrow_col".
    """
    # Root node always on our turn
    root = Node(board, turn=True)

    for _ in range(MAX_ITER):
        node = root
        # Selection phase – follow UCT until we reach a leaf node with no children yet
        while node.children:
            child = select_best_child(node, C)
            node = child

        # This leaf is the node we will expand (if possible) and simulate from
        leaf = node
        leaf.visits += 1                     # leaf has been selected this iteration

        # Expansion – if leaf can still move, create a random child
        if not leaf.is_terminal():
            legal_moves = generate_legal_moves(leaf.board, leaf.turn)
            if legal_moves:
                chosen = random.choice(legal_moves)
                child_board = apply_move(leaf.board, chosen)
                child = Node(child_board, move=chosen,
                             turn=not leaf.turn)
                leaf.children.append(child)
            # else: leaf is terminal → skip this iteration

        # Simulation – play random playout from the newly created child (or leaf if terminal)
        sim_node = leaf if not leaf.is_terminal() else leaf
        result = simulate_random(sim_node)

        # Back‑propagation
        if sim_node.turn:                    # player who moved at this leaf is us
            sim_node.wins += result
        else:
            sim_node.wins -= result
        sim_node.visits += 1                 # count the simulated play

    # Choose the child with the best empirical win‑rate
    best_child = max(root.children,
                     key=lambda c: (c.wins / c.visits) if c.visits > 0 else 0)
    return best_child.move  # guaranteed to be a legal move string
