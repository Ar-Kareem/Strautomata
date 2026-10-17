
import random
import math
import time

ROWS = 5
COLS = 6
DIRS = {'U': (-1, 0), 'R': (0, 1), 'D': (1, 0), 'L': (0, -1)}

ALL_MOVES = []
for r in range(ROWS):
    for c in range(COLS):
        sq = r * COLS + c
        for d, (dr, dc) in DIRS.items():
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                ALL_MOVES.append((sq, nr * COLS + nc, d))

def get_legal_moves(you_bb, opp_bb):
    moves = []
    for from_sq, to_sq, d in ALL_MOVES:
        if (you_bb >> from_sq) & 1 and (opp_bb >> to_sq) & 1:
            moves.append((from_sq, to_sq, d))
    return moves

def apply_move(you_bb, opp_bb, from_sq, to_sq):
    you_bb &= ~(1 << from_sq)
    you_bb |= (1 << to_sq)
    opp_bb &= ~(1 << to_sq)
    return you_bb, opp_bb

def playout(you_bb, opp_bb, player):
    current_player = player
    while True:
        if current_player == 0:
            moves = get_legal_moves(you_bb, opp_bb)
        else:
            moves = get_legal_moves(opp_bb, you_bb)
        if not moves:
            return 1 if current_player != player else 0
        from_sq, to_sq, _ = random.choice(moves)
        if current_player == 0:
            you_bb, opp_bb = apply_move(you_bb, opp_bb, from_sq, to_sq)
        else:
            opp_bb, you_bb = apply_move(opp_bb, you_bb, from_sq, to_sq)
        current_player = 1 - current_player

class Node:
    __slots__ = ('state', 'player', 'move', 'parent', 'children', 'untried_moves', 'visits', 'wins')
    def __init__(self, state, player, move=None, parent=None):
        self.state = state
        self.player = player
        self.move = move
        self.parent = parent
        self.children = []
        self.visits = 0
        self.wins = 0
        you_bb, opp_bb = state
        if player == 0:
            self.untried_moves = get_legal_moves(you_bb, opp_bb)
        else:
            self.untried_moves = get_legal_moves(opp_bb, you_bb)

    def is_fully_expanded(self):
        return len(self.untried_moves) == 0

    def best_child(self, C=1.414):
        log_visits = math.log(self.visits)
        def ucb(c):
            if c.visits == 0:
                return float('inf')
            child_value = c.wins / c.visits
            parent_value = 1 - child_value
            return parent_value + C * math.sqrt(log_visits / c.visits)
        return max(self.children, key=ucb)

def policy(you, opponent):
    you_bb = 0
    opp_bb = 0
    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            if you[r][c]:
                you_bb |= (1 << idx)
            if opponent[r][c]:
                opp_bb |= (1 << idx)

    legal_moves = get_legal_moves(you_bb, opp_bb)
    if not legal_moves:
        return "0,0,U"
    if len(legal_moves) == 1:
        from_sq, to_sq, d = legal_moves[0]
        r, c = divmod(from_sq, COLS)
        return f"{r},{c},{d}"

    root = Node(state=(you_bb, opp_bb), player=0)

    time_limit = 0.9
    start_time = time.time()

    while time.time() - start_time < time_limit:
        node = root
        while node.is_fully_expanded() and node.children:
            node = node.best_child()
        
        if node.untried_moves:
            move = random.choice(node.untried_moves)
            node.untried_moves.remove(move)
            from_sq, to_sq, d = move
            p0_bb, p1_bb = node.state
            if node.player == 0:
                new_p0, new_p1 = apply_move(p0_bb, p1_bb, from_sq, to_sq)
            else:
                new_p1, new_p0 = apply_move(p1_bb, p0_bb, from_sq, to_sq)
            child = Node(state=(new_p0, new_p1), player=1 - node.player, move=move, parent=node)
            node.children.append(child)
            node = child
        
        p0_bb, p1_bb = node.state
        result = playout(p0_bb, p1_bb, node.player)
        
        while node is not None:
            node.visits += 1
            node.wins += result
            result = 1 - result
            node = node.parent

    best_move = max(root.children, key=lambda c: c.visits).move
    from_sq, to_sq, d = best_move
    r, c = divmod(from_sq, COLS)
    return f"{r},{c},{d}"
