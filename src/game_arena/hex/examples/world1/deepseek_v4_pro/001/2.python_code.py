
import time
import random
import numpy as np

SIZE = 11
BLACK = 1
WHITE = 2

def get_neighbors(r, c):
    candidates = [(r-1,c), (r-1,c+1), (r,c-1), (r,c+1), (r+1,c-1), (r+1,c)]
    return [(nr,nc) for nr,nc in candidates if 0 <= nr < SIZE and 0 <= nc < SIZE]

NEIGHBORS = [[get_neighbors(r,c) for c in range(SIZE)] for r in range(SIZE)]

class Node:
    __slots__ = ('board', 'player', 'visits', 'wins', 'children', 'untried_actions', 'terminal')
    def __init__(self, board, player):
        self.board = board
        self.player = player
        self.visits = 0
        self.wins = 0
        self.children = {}
        self.untried_actions = None
        self.terminal = None

def get_untried_actions(node):
    if node.untried_actions is None:
        empty = np.argwhere(node.board == 0)
        actions = [tuple(e) for e in empty]
        random.shuffle(actions)
        node.untried_actions = actions
    return node.untried_actions

def check_win(board, player):
    visited = np.zeros((SIZE, SIZE), dtype=bool)
    if player == BLACK:
        queue = []
        for c in range(SIZE):
            if board[0, c] == BLACK:
                queue.append((0, c))
                visited[0, c] = True
        while queue:
            r, c = queue.pop()
            if r == SIZE-1:
                return True
            for nr, nc in NEIGHBORS[r][c]:
                if board[nr, nc] == BLACK and not visited[nr, nc]:
                    visited[nr, nc] = True
                    queue.append((nr, nc))
        return False
    else:
        queue = []
        for r in range(SIZE):
            if board[r, 0] == WHITE:
                queue.append((r, 0))
                visited[r, 0] = True
        while queue:
            r, c = queue.pop()
            if c == SIZE-1:
                return True
            for nr, nc in NEIGHBORS[r][c]:
                if board[nr, nc] == WHITE and not visited[nr, nc]:
                    visited[nr, nc] = True
                    queue.append((nr, nc))
        return False

def is_terminal(node):
    if node.terminal is None:
        board = node.board
        node.terminal = check_win(board, BLACK) or check_win(board, WHITE) or np.all(board != 0)
    return node.terminal

def simulate(board, player):
    b = board.copy()
    empty = np.argwhere(b == 0)
    np.random.shuffle(empty)
    for i, (r, c) in enumerate(empty):
        if i % 2 == 0:
            b[r, c] = player
        else:
            b[r, c] = 3 - player
    if check_win(b, BLACK):
        return BLACK
    return WHITE

def uct_select(node, c=1.4):
    best_val = -float('inf')
    best_action = None
    log_n = np.log(node.visits) if node.visits > 0 else 0
    for action, child in node.children.items():
        if child.visits == 0:
            return action
        q = child.wins / child.visits
        u = c * np.sqrt(log_n / child.visits)
        val = q + u
        if val > best_val:
            best_val = val
            best_action = action
    return best_action

def mcts(root_board, my_color):
    root = Node(root_board.copy(), my_color)
    if is_terminal(root):
        return get_untried_actions(root)[0]
    
    end_time = time.time() + 0.95
    while time.time() < end_time:
        node = root
        path = []
        while True:
            if is_terminal(node):
                break
            untried = get_untried_actions(node)
            if untried:
                action = untried.pop()
                new_board = node.board.copy()
                new_board[action] = node.player
                child = Node(new_board, 3 - node.player)
                node.children[action] = child
                path.append((node, action))
                node = child
                break
            else:
                if not node.children:
                    break
                action = uct_select(node)
                if action is None:
                    break
                path.append((node, action))
                node = node.children[action]
        if is_terminal(node):
            if check_win(node.board, BLACK):
                winner = BLACK
            else:
                winner = WHITE
        else:
            winner = simulate(node.board, node.player)
        for parent, action in path:
            child = parent.children[action]
            child.visits += 1
            if winner == parent.player:
                child.wins += 1
            parent.visits += 1
    
    if not root.children:
        return random.choice(get_untried_actions(root))
    best_move = max(root.children.items(), key=lambda x: x[1].visits)[0]
    return best_move

def policy(me, opp, color):
    board = np.zeros((SIZE, SIZE), dtype=np.int8)
    my_color = BLACK if color == 'b' else WHITE
    op_color = WHITE if my_color == BLACK else BLACK
    for r, c in me:
        board[r, c] = my_color
    for r, c in opp:
        board[r, c] = op_color
    move = mcts(board, my_color)
    return move
