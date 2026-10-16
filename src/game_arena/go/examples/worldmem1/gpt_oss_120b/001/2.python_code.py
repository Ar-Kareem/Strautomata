
import random
from collections import deque
from typing import List, Tuple, Dict

BoardPos = Tuple[int, int]  # (row, col) where 1 <= row,col <= 19
Memory = Dict  # any dict the caller gives us


def _neighbors(pos: BoardPos) -> List[BoardPos]:
    r, c = pos
    neigh = []
    if r > 1:
        neigh.append((r - 1, c))
    if r < 19:
        neigh.append((r + 1, c))
    if c > 1:
        neigh.append((r, c - 1))
    if c < 19:
        neigh.append((r, c + 1))
    return neigh


def _group_and_liberties(start: BoardPos,
                         board: Dict[BoardPos, str]) -> Tuple[set, set]:
    """
    Returns (group_stones, liberties) for the group that contains `start`.
    `board` maps positions to either 'me' or 'opp'.
    """
    colour = board[start]
    group = set()
    liberties = set()
    q = deque([start])
    while q:
        p = q.popleft()
        if p in group:
            continue
        group.add(p)
        for nb in _neighbors(p):
            if nb not in board:
                liberties.add(nb)
            elif board[nb] == colour and nb not in group:
                q.append(nb)
    return group, liberties


def _find_atari_moves(opponent: List[BoardPos],
                      board: Dict[BoardPos, str]) -> List[BoardPos]:
    """
    Returns a list of opponent liberties that would capture a group
    (i.e., groups with exactly one liberty).
    """
    visited = set()
    capture_moves = set()
    for stone in opponent:
        if stone in visited:
            continue
        group, libs = _group_and_liberties(stone, board)
        visited.update(group)
        if len(libs) == 1:
            capture_moves.update(libs)
    return list(capture_moves)


def _is_suicide(move: BoardPos,
                board: Dict[BoardPos, str],
                me_colour: str,
                opponent_colour: str) -> bool:
    """
    Determines if playing `move` results in a suicide.
    We already know `move` is empty.
    """
    # temporarily place the stone
    tmp_board = board.copy()
    tmp_board[move] = me_colour

    # check the new group of the placed stone
    group, libs = _group_and_liberties(move, tmp_board)
    if libs:
        return False  # has liberties → not suicide

    # if no liberties, check whether we captured any opponent group
    for nb in _neighbors(move):
        if nb in board and board[nb] == opponent_colour:
            opp_group, opp_libs = _group_and_liberties(nb, tmp_board)
            if not opp_libs:
                return False  # capture happened → not suicide
    return True


def policy(me: List[BoardPos],
           opponent: List[BoardPos],
           memory: Memory) -> Tuple[BoardPos, Memory]:
    """
    Returns the chosen move and (unchanged) memory.
    """
    # ------------------------------------------------------------------
    # Build board map
    board = {}
    for p in me:
        board[p] = 'me'
    for p in opponent:
        board[p] = 'opp'

    occupied = set(board.keys())

    # ------------------------------------------------------------------
    # 1. Capture if possible
    capture_moves = _find_atari_moves(opponent, board)
    random.shuffle(capture_moves)  # nondeterministic tie‑break
    for mv in capture_moves:
        if not _is_suicide(mv, board, 'me', 'opp'):
            return mv, memory  # capture!

    # ------------------------------------------------------------------
    # 2. Influence based move selection
    # Pre‑compute distances for speed (Manhattan distance is cheap)
    w_me = 1.0
    w_opp = 1.2
    w_center = 0.3
    centre = (10, 10)  # roughly the centre of a 19x19 board

    best_score = -float('inf')
    best_move = None

    # list of all board points
    all_points = [(r, c) for r in range(1, 20) for c in range(1, 20)]

    for pt in all_points:
        if pt in occupied:
            continue

        # quick suicide check – if the point has no adjacent empty neighbour
        # and does not capture, it is certainly suicide; we can skip early.
        adj_empty = any(nb not in occupied for nb in _neighbors(pt))
        if not adj_empty:
            # possible suicide, we will verify later
            pass

        # Influence score
        score = 0.0
        for s in me:
            d = abs(pt[0] - s[0]) + abs(pt[1] - s[1])
            score += w_me / (d + 1)
        for s in opponent:
            d = abs(pt[0] - s[0]) + abs(pt[1] - s[1])
            score -= w_opp / (d + 1)

        d_center = abs(pt[0] - centre[0]) + abs(pt[1] - centre[1])
        score += w_center / (d_center + 1)

        # Remember best legal move only
        if score > best_score:
            # verify legality (no suicide)
            if not _is_suicide(pt, board, 'me', 'opp'):
                best_score = score
                best_move = pt

    if best_move is not None:
        return best_move, memory

    # ------------------------------------------------------------------
    # 3. No legal moves → pass
    return (0, 0), memory
