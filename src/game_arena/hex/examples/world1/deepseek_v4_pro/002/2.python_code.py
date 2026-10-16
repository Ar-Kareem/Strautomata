
import random
import math
import time

SIZE = 11
N_CELLS = SIZE * SIZE
TOP = N_CELLS
BOTTOM = N_CELLS + 1
LEFT = N_CELLS
RIGHT = N_CELLS + 1

DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

def get_neighbors():
    neigh = [[] for _ in range(N_CELLS)]
    for r in range(SIZE):
        for c in range(SIZE):
            idx = r * SIZE + c
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE:
                    neigh[idx].append(nr * SIZE + nc)
    return neigh

NEIGHBORS = get_neighbors()

class HexState:
    __slots__ = ('board', 'empty', 'empty_pos', 'current_player',
                 'parent_black', 'rank_black', 'parent_white', 'rank_white')
    def __init__(self):
        self.board = [0] * N_CELLS
        self.empty = list(range(N_CELLS))
        self.empty_pos = list(range(N_CELLS))
        self.current_player = 1
        self.parent_black = list(range(N_CELLS + 2))
        self.rank_black = [0] * (N_CELLS + 2)
        self.parent_white = list(range(N_CELLS + 2))
        self.rank_white = [0] * (N_CELLS + 2)

    def clone(self):
        new_state = HexState()
        new_state.board = self.board[:]
        new_state.empty = self.empty[:]
        new_state.empty_pos = self.empty_pos[:]
        new_state.current_player = self.current_player
        new_state.parent_black = self.parent_black[:]
        new_state.rank_black = self.rank_black[:]
        new_state.parent_white = self.parent_white[:]
        new_state.rank_white = self.rank_white[:]
        return new_state

    def find(self, parent_arr, x):
        while parent_arr[x] != x:
            parent_arr[x] = parent_arr[parent_arr[x]]
            x = parent_arr[x]
        return x

    def union(self, parent_arr, rank_arr, x, y):
        xr = self.find(parent_arr, x)
        yr = self.find(parent_arr, y)
        if xr == yr:
            return
        if rank_arr[xr] < rank_arr[yr]:
            parent_arr[xr] = yr
        elif rank_arr[xr] > rank_arr[yr]:
            parent_arr[yr] = xr
        else:
            parent_arr[yr] = xr
            rank_arr[xr] += 1

    def move(self, idx):
        player = self.current_player
        self.board[idx] = player
        pos = self.empty_pos[idx]
        last = self.empty[-1]
        self.empty[pos] = last
        self.empty_pos[last] = pos
        self.empty.pop()

        if player == 1:
            parent_arr = self.parent_black
            rank_arr = self.rank_black
            r = idx // SIZE
            c = idx % SIZE
            if r == 0:
                self.union(parent_arr, rank_arr, idx, TOP)
            if r == SIZE - 1:
                self.union(parent_arr, rank_arr, idx, BOTTOM)
            for nb in NEIGHBORS[idx]:
                if self.board[nb] == 1:
                    self.union(parent_arr, rank_arr, idx, nb)
            if self.find(parent_arr, TOP) == self.find(parent_arr, BOTTOM):
                self.current_player = 3 - player
                return player
        else:
            parent_arr = self.parent_white
            rank_arr = self.rank_white
            r = idx // SIZE
            c = idx % SIZE
            if c == 0:
                self.union(parent_arr, rank_arr, idx, LEFT)
            if c == SIZE - 1:
                self.union(parent_arr, rank_arr, idx, RIGHT)
            for nb in NEIGHBORS[idx]:
                if self.board[nb] == 2:
                    self.union(parent_arr, rank_arr, idx, nb)
            if self.find(parent_arr, LEFT) == self.find(parent_arr, RIGHT):
                self.current_player = 3 - player
                return player
        self.current_player = 3 - player
        return 0

    def rebuild_dsu(self):
        self.parent_black = list(range(N_CELLS + 2))
        self.rank_black = [0] * (N_CELLS + 2)
        self.parent_white = list(range(N_CELLS + 2))
        self.rank_white = [0] * (N_CELLS + 2)
        for r in range(SIZE):
            for c in range(SIZE):
                idx = r * SIZE + c
                if self.board[idx] == 1:
                    if r == 0:
                        self.union(self.parent_black, self.rank_black, idx, TOP)
                    if r == SIZE - 1:
                        self.union(self.parent_black, self.rank_black, idx, BOTTOM)
                    for nb in NEIGHBORS[idx]:
                        if self.board[nb] == 1:
                            self.union(self.parent_black, self.rank_black, idx, nb)
                elif self.board[idx] == 2:
                    if c == 0:
                        self.union(self.parent_white, self.rank_white, idx, LEFT)
                    if c == SIZE - 1:
                        self.union(self.parent_white, self.rank_white, idx, RIGHT)
                    for nb in NEIGHBORS[idx]:
                        if self.board[nb] == 2:
                            self.union(self.parent_white, self.rank_white, idx, nb)

class MCTSNode:
    __slots__ = ('state', 'parent', 'move', 'player', 'visits', 'value',
                 'children', 'untried_moves', 'terminal', 'winner')
    def __init__(self, state, parent=None, move=None, player=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.player = player
        self.visits = 0
        self.value = 0.0
        self.children = {}
        self.untried_moves = state.empty.copy()
        self.terminal = False
        self.winner = 0

def ucb(node, parent_visits, C=1.4):
    if node.visits == 0:
        return float('inf')
    return node.value / node.visits + C * math.sqrt(math.log(parent_visits) / node.visits)

def simulate(state):
    while True:
        if not state.empty:
            return 0
        idx = random.choice(state.empty)
        winner = state.move(idx)
        if winner:
            return winner

def mcts(root_state, time_limit):
    root = MCTSNode(root_state)
    if not root_state.empty:
        return None
    end_time = time.time() + time_limit
    while time.time() < end_time:
        node = root
        # Selection
        while not node.untried_moves and node.children:
            best_child = None
            best_ucb = -float('inf')
            for child in node.children.values():
                u = ucb(child, node.visits)
                if u > best_ucb:
                    best_ucb = u
                    best_child = child
            node = best_child

        if node.terminal:
            winner = node.winner
        else:
            # Expansion
            if node.untried_moves:
                i = random.randrange(len(node.untried_moves))
                move_idx = node.untried_moves[i]
                node.untried_moves[i] = node.untried_moves[-1]
                node.untried_moves.pop()
                new_state = node.state.clone()
                player = new_state.current_player
                winner = new_state.move(move_idx)
                child = MCTSNode(new_state, parent=node, move=move_idx, player=player)
                if winner:
                    child.terminal = True
                    child.winner = winner
                node.children[move_idx] = child
                node = child
                if not winner:
                    sim_state = new_state.clone()
                    winner = simulate(sim_state)
            else:
                winner = 0

        # Backpropagation
        while node is not None:
            node.visits += 1
            if node.player is not None and winner != 0:
                if node.player == winner:
                    node.value += 1
            node = node.parent

    if not root.children:
        if root.untried_moves:
            best_idx = random.choice(root.untried_moves)
        else:
            best_idx = random.choice(root.state.empty)
        return (best_idx // SIZE, best_idx % SIZE)

    best_child = max(root.children.values(), key=lambda c: c.visits)
    return (best_child.move // SIZE, best_child.move % SIZE)

def policy(me, opp, color):
    state = HexState()
    player = 1 if color == 'b' else 2
    opp_player = 3 - player
    state.current_player = player

    # Add opponent stones
    for r, c in opp:
        idx = r * SIZE + c
        state.board[idx] = opp_player
        pos = state.empty_pos[idx]
        last = state.empty[-1]
        state.empty[pos] = last
        state.empty_pos[last] = pos
        state.empty.pop()
    # Add own stones
    for r, c in me:
        idx = r * SIZE + c
        state.board[idx] = player
        pos = state.empty_pos[idx]
        last = state.empty[-1]
        state.empty[pos] = last
        state.empty_pos[last] = pos
        state.empty.pop()

    state.rebuild_dsu()

    # Opening book
    if len(state.empty) == SIZE * SIZE:
        return (5, 5)
    if len(state.empty) == SIZE * SIZE - 1:
        opp_idx = next(i for i in range(N_CELLS) if state.board[i] == opp_player)
        if opp_idx == 5 * SIZE + 5:
            if state.board[5 * SIZE + 4] == 0:
                return (5, 4)
            else:
                return (4, 5)
        else:
            center = 5 * SIZE + 5
            if state.board[center] == 0:
                return (center // SIZE, center % SIZE)

    # Immediate win
    for idx in state.empty:
        test = state.clone()
        test.current_player = player
        if test.move(idx) == player:
            return (idx // SIZE, idx % SIZE)

    # Block opponent win
    for idx in state.empty:
        test = state.clone()
        test.current_player = opp_player
        if test.move(idx) == opp_player:
            return (idx // SIZE, idx % SIZE)

    # MCTS
    time_limit = 0.85
    best_move = mcts(state, time_limit)
    if best_move is not None:
        return best_move

    # Fallback
    idx = random.choice(state.empty)
    return (idx // SIZE, idx % SIZE)
