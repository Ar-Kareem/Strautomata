
import random
import math
import time


def get_board_info(valid_mask):
    rows = len(valid_mask)
    cols = len(valid_mask[0])
    cell_to_idx = {}
    idx_to_cell = []
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if valid_mask[r][c]:
                cell_to_idx[(r, c)] = idx
                idx_to_cell.append((r, c))
                idx += 1
    N = idx

    neighbors = [[] for _ in range(N)]
    for r, c in idx_to_cell:
        u = cell_to_idx[(r, c)]
        # same column
        if r > 0 and valid_mask[r-1][c]:
            neighbors[u].append(cell_to_idx[(r-1, c)])
        if r < rows-1 and valid_mask[r+1][c]:
            neighbors[u].append(cell_to_idx[(r+1, c)])
        if r % 2 == 0:
            # left
            if r > 0 and c > 0 and valid_mask[r-1][c-1]:
                neighbors[u].append(cell_to_idx[(r-1, c-1)])
            if c > 0 and valid_mask[r][c-1]:
                neighbors[u].append(cell_to_idx[(r, c-1)])
            # right
            if r > 0 and c < cols-1 and valid_mask[r-1][c+1]:
                neighbors[u].append(cell_to_idx[(r-1, c+1)])
            if c < cols-1 and valid_mask[r][c+1]:
                neighbors[u].append(cell_to_idx[(r, c+1)])
        else:
            # left
            if c > 0 and valid_mask[r][c-1]:
                neighbors[u].append(cell_to_idx[(r, c-1)])
            if r < rows-1 and c > 0 and valid_mask[r+1][c-1]:
                neighbors[u].append(cell_to_idx[(r+1, c-1)])
            # right
            if c < cols-1 and valid_mask[r][c+1]:
                neighbors[u].append(cell_to_idx[(r, c+1)])
            if r < rows-1 and c < cols-1 and valid_mask[r+1][c+1]:
                neighbors[u].append(cell_to_idx[(r+1, c+1)])

    corners = [False] * N
    boundary = [False] * N
    for i in range(N):
        deg = len(neighbors[i])
        if deg == 3:
            corners[i] = True
            boundary[i] = True
        elif deg == 4:
            boundary[i] = True

    edge_groups = []
    visited = [False] * N
    for i in range(N):
        if len(neighbors[i]) == 4 and not visited[i]:
            group = set()
            q = [i]
            visited[i] = True
            while q:
                u = q.pop()
                group.add(u)
                for v in neighbors[u]:
                    if len(neighbors[v]) == 4 and not visited[v]:
                        visited[v] = True
                        q.append(v)
            edge_groups.append(group)

    cell_to_edge_group = [-1] * N
    for eg_idx, group in enumerate(edge_groups):
        for u in group:
            cell_to_edge_group[u] = eg_idx

    return {
        'N': N,
        'neighbors': neighbors,
        'corners': corners,
        'boundary': boundary,
        'cell_to_edge_group': cell_to_edge_group,
        'cell_to_idx': cell_to_idx,
        'idx_to_cell': idx_to_cell,
    }


class State:
    __slots__ = ('me', 'opp', 'empty', 'turn', 'info', 'N', 'neighbors', 'corners', 'boundary', 'cell_to_edge_group', '_moves', '_terminal', '_winner')

    def __init__(self, me, opp, empty, turn, info):
        self.me = me
        self.opp = opp
        self.empty = empty
        self.turn = turn
        self.info = info
        self.N = info['N']
        self.neighbors = info['neighbors']
        self.corners = info['corners']
        self.boundary = info['boundary']
        self.cell_to_edge_group = info['cell_to_edge_group']
        self._moves = None
        self._terminal = None
        self._winner = None

    def get_moves(self):
        if self._moves is None:
            moves = []
            e = self.empty
            while e:
                lsb = e & -e
                moves.append(lsb.bit_length() - 1)
                e ^= lsb
            self._moves = moves
        return self._moves

    def apply_move(self, move):
        move_bit = 1 << move
        if self.turn == 0:
            new_me = self.me | move_bit
            new_opp = self.opp
        else:
            new_me = self.me
            new_opp = self.opp | move_bit
        new_empty = self.empty ^ move_bit
        new_turn = 1 - self.turn
        return State(new_me, new_opp, new_empty, new_turn, self.info)

    def is_terminal(self):
        if self._terminal is not None:
            return self._terminal, self._winner
        mover = 1 - self.turn
        if mover == 0:
            if self._player_wins(self.me, self.opp):
                self._terminal = True
                self._winner = 0
                return True, 0
        else:
            if self._player_wins(self.opp, self.me):
                self._terminal = True
                self._winner = 1
                return True, 1
        if self.empty == 0:
            self._terminal = True
            self._winner = -1
            return True, -1
        self._terminal = False
        self._winner = None
        return False, None

    def _player_wins(self, stones, other_stones):
        if self._has_bridge_or_fork(stones):
            return True
        nonS = self.empty | other_stones
        if self._has_ring(nonS):
            return True
        return False

    def _has_bridge_or_fork(self, stones):
        visited = bytearray(self.N)
        st = stones
        while st:
            lsb = st & -st
            u = lsb.bit_length() - 1
            st ^= lsb
            if not visited[u]:
                corners_hit, edges_hit = self._bfs_bf(u, stones, visited)
                if corners_hit >= 2:
                    return True
                if edges_hit >= 3:
                    return True
        return False

    def _bfs_bf(self, start, stones, visited):
        q = [start]
        visited[start] = 1
        corners_hit = 0
        edge_groups = set()
        while q:
            u = q.pop()
            if self.corners[u]:
                corners_hit += 1
            eg = self.cell_to_edge_group[u]
            if eg != -1:
                edge_groups.add(eg)
            for v in self.neighbors[u]:
                if (stones >> v) & 1 and not visited[v]:
                    visited[v] = 1
                    q.append(v)
        return corners_hit, len(edge_groups)

    def _has_ring(self, nonS):
        visited = bytearray(self.N)
        ns = nonS
        while ns:
            lsb = ns & -ns
            u = lsb.bit_length() - 1
            ns ^= lsb
            if not visited[u]:
                q = [u]
                visited[u] = 1
                has_boundary = False
                while q:
                    v = q.pop()
                    if self.boundary[v]:
                        has_boundary = True
                    for w in self.neighbors[v]:
                        if (nonS >> w) & 1 and not visited[w]:
                            visited[w] = 1
                            q.append(w)
                if not has_boundary:
                    return True
        return False


class Node:
    __slots__ = ('state', 'parent', 'move', 'visits', 'value', 'children', 'untried_moves')

    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.visits = 0
        self.value = 0.0
        self.children = {}
        moves = state.get_moves()
        random.shuffle(moves)
        self.untried_moves = moves


def select(node):
    while not node.state.is_terminal()[0] and not node.untried_moves:
        best = None
        best_score = -float('inf')
        log_parent = math.log(node.visits + 1)
        for child in node.children.values():
            if child.visits == 0:
                score = float('inf')
            else:
                exploit = child.value / child.visits
                explore = math.sqrt(2 * log_parent / child.visits)
                score = exploit + explore
            if score > best_score:
                best_score = score
                best = child
        node = best
    return node


def expand(node):
    if node.untried_moves:
        move = node.untried_moves.pop()
        new_state = node.state.apply_move(move)
        child = Node(new_state, parent=node, move=move)
        node.children[move] = child
        return child
    return node


def rollout(state):
    while True:
        term, winner = state.is_terminal()
        if term:
            return winner
        moves = state.get_moves()
        move = random.choice(moves)
        state = state.apply_move(move)


def backprop(node, terminal_winner):
    root_reward = 1 if terminal_winner == 0 else (-1 if terminal_winner == 1 else 0)
    while node:
        node.visits += 1
        if node.state.turn == 0:
            node.value += root_reward
        else:
            node.value -= root_reward
        node = node.parent


def policy(me, opp, valid_mask):
    info = get_board_info(valid_mask)
    N = info['N']
    cell_to_idx = info['cell_to_idx']
    idx_to_cell = info['idx_to_cell']

    me_mask = 0
    for r, c in me:
        me_mask |= (1 << cell_to_idx[(r, c)])
    opp_mask = 0
    for r, c in opp:
        opp_mask |= (1 << cell_to_idx[(r, c)])
    empty_mask = ((1 << N) - 1) ^ (me_mask | opp_mask)

    root_state = State(me_mask, opp_mask, empty_mask, 0, info)
    moves = root_state.get_moves()

    if not moves:
        return 0, 0
    if len(moves) == 1:
        return idx_to_cell[moves[0]]

    # Instant win
    for move in moves:
        child = root_state.apply_move(move)
        term, winner = child.is_terminal()
        if term and winner == 0:
            return idx_to_cell[move]

    # Block opponent's instant win
    for move in moves:
        sim_opp_opp = opp_mask | (1 << move)
        sim_opp_empty = empty_mask & ~(1 << move)
        # Simulate state after opponent's move (turn=1 means we would be next)
        sim_state = State(me_mask, sim_opp_opp, sim_opp_empty, 1, info)
        if sim_state._player_wins(sim_opp_opp, me_mask):
            return idx_to_cell[move]

    root_node = Node(root_state)
    start_time = time.time()
    while time.time() - start_time < 0.95:
        leaf = select(root_node)
        term, winner = leaf.state.is_terminal()
        if not term:
            leaf = expand(leaf)
            term, winner = leaf.state.is_terminal()
        if term:
            backprop(leaf, winner)
        else:
            rollout_winner = rollout(leaf.state)
            backprop(leaf, rollout_winner)

    best_move = None
    best_visits = -1
    best_value = -float('inf')
    for move, child in root_node.children.items():
        if child.visits > best_visits or (child.visits == best_visits and child.value / child.visits > best_value):
            best_visits = child.visits
            best_value = child.value / child.visits
            best_move = move

    if best_move is None:
        if root_node.untried_moves:
            best_move = root_node.untried_moves[0]
        else:
            best_move = moves[0]

    return idx_to_cell[best_move]
