
import math
import random
import time

# ----- Board constants -----
N = 11
SIZE = N * N
ME = 1
OPP = 2
EMPTY = 0
# Hex adjacency: all 8 grid neighbors except (i-1,j-1) and (i+1,j+1)
NEI = ((-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0))
CENTER_IDX = 5 * N + 5

# ----- Tuning knobs -----
EXPLORATION = 0.5
RAVE_K = 1000.0
RAVE_DEPTH = 8
MAX_CANDIDATES = 28
TIME_BUDGET = 0.90

# ----- Precomputed geometry -----
NEIGHBORS = [[] for _ in range(SIZE)]
D2 = [[] for _ in range(SIZE)]
for _r in range(N):
    for _c in range(N):
        _idx = _r * N + _c
        for _dr, _dc in NEI:
            _r2, _c2 = _r + _dr, _c + _dc
            if 0 <= _r2 < N and 0 <= _c2 < N:
                NEIGHBORS[_idx].append(_r2 * N + _c2)
        for _dr in (-2, -1, 0, 1, 2):
            for _dc in (-2, -1, 0, 1, 2):
                if _dr == 0 and _dc == 0:
                    continue
                _r2, _c2 = _r + _dr, _c + _dc
                if 0 <= _r2 < N and 0 <= _c2 < N:
                    D2[_idx].append(_r2 * N + _c2)


def _is_connected(board, player, color):
    """BFS check: does `player` connect its two sides?"""
    if color == 'b':
        stack = [c for c in range(N) if board[c] == player]
    else:
        stack = [r * N for r in range(N) if board[r * N] == player]
    if not stack:
        return False
    visited = [False] * SIZE
    for idx in stack:
        visited[idx] = True
    target = N - 1
    check_row = (color == 'b')
    while stack:
        idx = stack.pop()
        r, c = divmod(idx, N)
        if (r if check_row else c) == target:
            return True
        for j in NEIGHBORS[idx]:
            if not visited[j] and board[j] == player:
                visited[j] = True
                stack.append(j)
    return False


def _find_winning_move(board, player, color):
    """Return an empty cell that immediately connects `player`, or None."""
    tried = [False] * SIZE
    for idx in range(SIZE):
        if board[idx] == player:
            for j in NEIGHBORS[idx]:
                if board[j] == EMPTY and not tried[j]:
                    tried[j] = True
                    board[j] = player
                    if _is_connected(board, player, color):
                        board[j] = EMPTY
                        return j
                    board[j] = EMPTY
    return None


def _candidates(board):
    """Ordered list of plausible moves (best first)."""
    stones = 0
    cand = set()
    for idx in range(SIZE):
        if board[idx] != EMPTY:
            stones += 1
            for j in D2[idx]:
                if board[j] == EMPTY:
                    cand.add(j)
    if stones == 0:
        return [CENTER_IDX]
    empty_count = SIZE - stones
    if empty_count <= 40:
        cand = set(idx for idx in range(SIZE) if board[idx] == EMPTY)
    else:
        for r in (4, 5, 6):
            for c in (4, 5, 6):
                idx = r * N + c
                if board[idx] == EMPTY:
                    cand.add(idx)
    if not cand:
        return [idx for idx in range(SIZE) if board[idx] == EMPTY]
    scored = []
    for idx in cand:
        s = 0
        for j in NEIGHBORS[idx]:
            v = board[j]
            if v == ME:
                s += 3
            elif v == OPP:
                s += 2
        r, c = divmod(idx, N)
        scored.append((s, -(abs(r - 5) + abs(c - 5)), idx))
    scored.sort(reverse=True)
    limit = MAX_CANDIDATES if empty_count > 40 else empty_count
    return [idx for _, _, idx in scored[:limit]]


class _Node:
    __slots__ = ('move', 'player', 'children', 'untried', 'visits', 'wins', 'rave')

    def __init__(self, move, player, untried):
        self.move = move
        self.player = player
        self.children = {}
        self.untried = untried
        self.visits = 0
        self.wins = 0
        self.rave = {}


def _select(node):
    logN = math.log(node.visits)
    beta = math.sqrt(RAVE_K / (3.0 * node.visits + RAVE_K))
    best = None
    best_val = -1e18
    for move, child in node.children.items():
        n = child.visits
        q = child.wins / n
        rv = node.rave.get(move)
        if rv is not None and rv[1] > 0:
            qr = rv[0] / rv[1]
            val = (1.0 - beta) * q + beta * qr + EXPLORATION * math.sqrt(logN / n)
        else:
            val = q + EXPLORATION * math.sqrt(logN / n)
        if val > best_val:
            best_val = val
            best = child
    return best


def _simulate(board, just_moved, my_color):
    """Locality-biased random playout. Returns (me_won, me_moves, opp_moves)."""
    local = []
    far = []
    for idx in range(SIZE):
        if board[idx] == EMPTY:
            adj = False
            for j in NEIGHBORS[idx]:
                if board[j] != EMPTY:
                    adj = True
                    break
            if adj:
                local.append(idx)
            else:
                far.append(idx)
    random.shuffle(local)
    random.shuffle(far)
    ordered = local + far
    cur = OPP if just_moved == ME else ME
    moves_me = []
    moves_opp = []
    for idx in ordered:
        board[idx] = cur
        if cur == ME:
            moves_me.append(idx)
            cur = OPP
        else:
            moves_opp.append(idx)
            cur = ME
    win = _is_connected(board, ME, my_color)
    for idx in ordered:
        board[idx] = EMPTY
    return win, moves_me, moves_opp


def _mcts(board, candidates, my_color, deadline):
    root = _Node(None, OPP, list(reversed(candidates)))
    iterations = 0
    while True:
        if (iterations & 31) == 0 and time.time() > deadline:
            break
        iterations += 1
        node = root
        path = [root]
        path_moves = []
        # selection
        while node.children and not node.untried:
            node = _select(node)
            board[node.move] = node.player
            path.append(node)
            path_moves.append((node.move, node.player))
        # expansion
        if node.untried:
            move = node.untried.pop()
            p = ME if node.player == OPP else OPP
            board[move] = p
            local = []
            far = []
            for idx in range(SIZE):
                if board[idx] == EMPTY:
                    adj = False
                    for j in NEIGHBORS[idx]:
                        if board[j] != EMPTY:
                            adj = True
                            break
                    if adj:
                        local.append(idx)
                    else:
                        far.append(idx)
            random.shuffle(local)
            random.shuffle(far)
            child = _Node(move, p, far + local)
            node.children[move] = child
            node = child
            path.append(node)
            path_moves.append((move, p))
        # playout
        win, moves_me, moves_opp = _simulate(board, node.player, my_color)
        pm = (moves_me, moves_opp)
        plen = len(path_moves)
        # backpropagation (with RAVE near the top of the tree)
        for i, nd in enumerate(path):
            nd.visits += 1
            if (nd.player == ME) == win:
                nd.wins += 1
            if i < RAVE_DEPTH:
                P = ME if nd.player == OPP else OPP
                winc = 1 if ((P == ME) == win) else 0
                rave = nd.rave
                for m in pm[P - 1]:
                    rv = rave.get(m)
                    if rv is None:
                        rave[m] = [winc, 1]
                    else:
                        rv[0] += winc
                        rv[1] += 1
                for j in range(i, plen):
                    m, pl = path_moves[j]
                    if pl == P:
                        rv = rave.get(m)
                        if rv is None:
                            rave[m] = [winc, 1]
                        else:
                            rv[0] += winc
                            rv[1] += 1
        # undo tree moves
        for m, _ in path_moves:
            board[m] = EMPTY
    # pick the most-visited root child
    best_move = None
    best_visits = -1
    best_wins = -1
    for move, child in root.children.items():
        if child.visits > best_visits or (child.visits == best_visits and child.wins > best_wins):
            best_visits = child.visits
            best_wins = child.wins
            best_move = move
    return best_move


def policy(me, opp, color):
    try:
        start = time.time()
        board = [EMPTY] * SIZE
        for r, c in me:
            board[r * N + c] = ME
        for r, c in opp:
            board[r * N + c] = OPP
        my_color = color
        opp_color = 'w' if color == 'b' else 'b'

        # openings
        if not me and not opp:
            return (5, 5)
        if not me and len(opp) == 1 and board[CENTER_IDX] == EMPTY:
            return (5, 5)

        # immediate win
        m = _find_winning_move(board, ME, my_color)
        if m is not None:
            return divmod(m, N)
        # immediate block
        m = _find_winning_move(board, OPP, opp_color)
        if m is not None:
            return divmod(m, N)

        candidates = _candidates(board)
        if not candidates:
            for idx in range(SIZE):
                if board[idx] == EMPTY:
                    return divmod(idx, N)
            return (0, 0)
        if len(candidates) == 1:
            return divmod(candidates[0], N)
        deadline = start + TIME_BUDGET
        best = _mcts(board, candidates, my_color, deadline)
        if best is None or board[best] != EMPTY:
            best = candidates[0]
        return divmod(best, N)
    except Exception:
        occupied = set(me)
        occupied.update(opp)
        for r in range(N):
            for c in range(N):
                if (r, c) not in occupied:
                    return (r, c)
        return (0, 0)
