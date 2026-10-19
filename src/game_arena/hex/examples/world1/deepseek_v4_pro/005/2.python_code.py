
import numpy as np
import math
import random
import time
from collections import deque

# Constants
N = 11
NEIGHBORS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
# Precomputed neighbor indices for speed
NEIGHBOR_LIST = [[] for _ in range(N * N)]
for r in range(N):
    for c in range(N):
        idx = r * N + c
        for dr, dc in NEIGHBORS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                NEIGHBOR_LIST[idx].append((nr, nc))

C_PUCT = 1.5
INF_DIST = 100  # large enough for 11x11

def opponent(player):
    return 'w' if player == 'b' else 'b'

def player_int(player):
    return 1 if player == 'b' else 2

class Node:
    __slots__ = ('player', 'visits', 'wins', 'children', 'unexpanded_moves', 'priors')
    def __init__(self, player):
        self.player = player
        self.visits = 0
        self.wins = 0.0
        self.children = {}
        self.unexpanded_moves = None
        self.priors = None

def is_connected(board, player_int_val):
    visited = np.zeros(N * N, dtype=bool)
    q = deque()
    if player_int_val == 1:  # black: top to bottom
        for c in range(N):
            if board[0, c] == 1:
                q.append((0, c))
                visited[c] = True
        while q:
            r, c = q.popleft()
            if r == 10:
                return True
            for nr, nc in NEIGHBOR_LIST[r * N + c]:
                if board[nr, nc] == 1 and not visited[nr * N + nc]:
                    visited[nr * N + nc] = True
                    q.append((nr, nc))
        return False
    else:  # white: left to right
        for r in range(N):
            if board[r, 0] == 2:
                q.append((r, 0))
                visited[r * N] = True
        while q:
            r, c = q.popleft()
            if c == 10:
                return True
            for nr, nc in NEIGHBOR_LIST[r * N + c]:
                if board[nr, nc] == 2 and not visited[nr * N + nc]:
                    visited[nr * N + nc] = True
                    q.append((nr, nc))
        return False

def check_winner(board):
    if is_connected(board, 1):
        return 'b'
    if is_connected(board, 2):
        return 'w'
    return None

def bfs_distance(board, player):
    """Minimum additional stones needed to connect for the given player."""
    player_int_val = player_int(player)
    opp_int_val = 2 if player_int_val == 1 else 1
    dist = np.full(N * N, INF_DIST, dtype=np.int16)
    dq = deque()
    
    if player == 'b':
        for c in range(N):
            val = board[0, c]
            if val != opp_int_val:
                idx = c
                if val == player_int_val:
                    dist[idx] = 0
                    dq.appendleft((0, c))
                else:
                    dist[idx] = 1
                    dq.append((0, c))
        target_check = lambda r, c: r == 10
    else:
        for r in range(N):
            val = board[r, 0]
            if val != opp_int_val:
                idx = r * N
                if val == player_int_val:
                    dist[idx] = 0
                    dq.appendleft((r, 0))
                else:
                    dist[idx] = 1
                    dq.append((r, 0))
        target_check = lambda r, c: c == 10
    
    while dq:
        r, c = dq.popleft()
        idx = r * N + c
        d = dist[idx]
        if target_check(r, c):
            return min(d, INF_DIST)
        for nr, nc in NEIGHBOR_LIST[idx]:
            val = board[nr, nc]
            if val == opp_int_val:
                continue
            cost = 0 if val == player_int_val else 1
            nd = d + cost
            nidx = nr * N + nc
            if nd < dist[nidx]:
                dist[nidx] = nd
                if cost == 0:
                    dq.appendleft((nr, nc))
                else:
                    dq.append((nr, nc))
    return INF_DIST

def compute_priors(board, player, legal_moves):
    opp = opponent(player)
    state_score = bfs_distance(board, opp) - bfs_distance(board, player)
    scores = []
    for move in legal_moves:
        r, c = move
        board[r, c] = player_int(player)
        d_player = bfs_distance(board, player)
        d_opp = bfs_distance(board, opp)
        board[r, c] = 0
        new_score = d_opp - d_player
        delta = new_score - state_score
        scores.append(delta)
    max_s = max(scores)
    exps = [math.exp(s - max_s) for s in scores]
    total = sum(exps)
    priors = {m: exps[i] / total for i, m in enumerate(legal_moves)}
    return priors

def rollout(board, player):
    empty = []
    for r in range(N):
        for c in range(N):
            if board[r, c] == 0:
                empty.append((r, c))
    n_empty = len(empty)
    current = player
    for i in range(n_empty):
        idx = random.randrange(n_empty - i)
        r, c = empty[idx]
        board[r, c] = player_int(current)
        empty[idx], empty[n_empty - 1 - i] = empty[n_empty - 1 - i], empty[idx]
        current = opponent(current)
    winner = 'b' if is_connected(board, 1) else 'w'
    return 1 if winner == player else 0

def select_child(node):
    total_visits = node.visits
    sqrt_total = math.sqrt(total_visits)
    best_score = -float('inf')
    best_move = None
    for move, child in node.children.items():
        q = child.wins / child.visits if child.visits > 0 else 0
        p = node.priors[move]
        u = C_PUCT * p * sqrt_total / (1 + child.visits)
        score = q + u
        if score > best_score:
            best_score = score
            best_move = move
    return best_move

def pick_unexpanded(node):
    best_prior = -1
    best_move = None
    for move in node.unexpanded_moves:
        if node.priors[move] > best_prior:
            best_prior = node.priors[move]
            best_move = move
    return best_move

def run_simulation(initial_board, root):
    board = initial_board.copy()
    node = root
    path = [root]
    
    # Selection: traverse until a non-fully-expanded node or terminal
    while node.priors is not None and len(node.unexpanded_moves) == 0 and node.children:
        move = select_child(node)
        child = node.children[move]
        board[move] = player_int(node.player)
        path.append(child)
        node = child
    
    # Terminal check
    winner = check_winner(board)
    if winner is not None:
        R = 0  # player to move has lost
    else:
        legal_moves = list(zip(*np.where(board == 0)))
        if not legal_moves:
            w = check_winner(board)
            R = 1 if w == node.player else 0
        else:
            if node.priors is None:
                if node == root:
                    priors = compute_priors(board, node.player, legal_moves)
                    n_moves = len(legal_moves)
                    noise = np.random.dirichlet([0.03] * n_moves)
                    for i, m in enumerate(legal_moves):
                        priors[m] = 0.75 * priors[m] + 0.25 * noise[i]
                    total = sum(priors.values())
                    for m in priors:
                        priors[m] /= total
                else:
                    p = 1.0 / len(legal_moves)
                    priors = {m: p for m in legal_moves}
                node.priors = priors
                node.unexpanded_moves = list(legal_moves)
            
            move = pick_unexpanded(node)
            node.unexpanded_moves.remove(move)
            child = Node(opponent(node.player))
            node.children[move] = child
            board[move] = player_int(node.player)
            path.append(child)
            node = child
            
            winner = check_winner(board)
            if winner is not None:
                R = 0  # game ended by this move, child's player lost
            else:
                R = rollout(board, node.player)
    
    # Backpropagation
    for n in reversed(path):
        n.visits += 1
        n.wins += R
        R = 1 - R

def policy(me, opp, color):
    board = np.zeros((N, N), dtype=np.int8)
    my_int = 1 if color == 'b' else 2
    opp_int = 2 if color == 'b' else 1
    for r, c in me:
        board[r, c] = my_int
    for r, c in opp:
        board[r, c] = opp_int
    
    root = Node(color)
    start_time = time.perf_counter()
    run_simulation(board.copy(), root)  # ensure at least one simulation
    while time.perf_counter() - start_time < 0.95:
        run_simulation(board.copy(), root)
    
    best_move = max(root.children.items(), key=lambda x: x[1].visits)[0]
    return best_move
