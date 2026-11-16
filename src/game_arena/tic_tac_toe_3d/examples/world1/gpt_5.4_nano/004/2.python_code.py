
from __future__ import annotations

from typing import List, Tuple, Optional
import math
import time

Board = List[List[List[int]]]

# All winning lines in a 3x3x3 grid: rows, columns, pillars, and all diagonals on planes and space diagonals.
def _generate_lines() -> List[List[Tuple[int,int,int]]]:
    lines = []
    n = 3

    # Helper to add a line
    def add(cells):
        if len(cells) == n:
            lines.append(cells)

    # Straight lines along axes
    for i in range(n):
        for j in range(n):
            add([(i, j, k) for k in range(n)])  # z axis
    for i in range(n):
        for k in range(n):
            add([(i, j, k) for j in range(n)])  # y axis
    for j in range(n):
        for k in range(n):
            add([(i, j, k) for i in range(n)])  # x axis

    # Diagonals in planes (constant x)
    for x in range(n):
        add([(x, t, t) for t in range(n)])
        add([(x, t, n-1-t) for t in range(n)])

    # Diagonals in planes (constant y)
    for y in range(n):
        add([(t, y, t) for t in range(n)])
        add([(t, y, n-1-t) for t in range(n)])

    # Diagonals in planes (constant z)
    for z in range(n):
        add([(t, t, z) for t in range(n)])
        add([(t, n-1-t, z) for t in range(n)])

    # Space diagonals
    add([(t, t, t) for t in range(n)])
    add([(t, t, n-1-t) for t in range(n)])
    add([(t, n-1-t, t) for t in range(n)])
    add([(t, n-1-t, n-1-t) for t in range(n)])

    # Remove duplicates (shouldn't exist, but keep safe)
    uniq = []
    seen = set()
    for line in lines:
        key = tuple(sorted(line))
        if key not in seen:
            seen.add(key)
            uniq.append(line)
    return uniq

LINES = _generate_lines()

def _check_winner(board: Board) -> int:
    # Returns 1 if we win, -1 if opponent wins, 0 otherwise
    for line in LINES:
        s = 0
        for (i, j, k) in line:
            s += board[i][j][k]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def _legal_moves(board: Board) -> List[Tuple[int,int,int]]:
    moves = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    moves.append((i, j, k))
    return moves

def _apply_move(board: Board, move: Tuple[int,int,int], player: int) -> Board:
    i, j, k = move
    newb = [ [row[:] for row in plane] for plane in board ]
    newb[i][j][k] = player
    return newb

def _board_full(board: Board) -> bool:
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return False
    return True

def _heuristic(board: Board) -> int:
    # Simple line-based heuristic:
    # For each line, count our marks and opponent marks.
    # If opponent has any mark, only our potential is 0 (and vice versa).
    # Score is based on "threat strength".
    # Higher is better for us.
    score = 0
    for line in LINES:
        ours = 0
        opp = 0
        for (i, j, k) in line:
            v = board[i][j][k]
            if v == 1:
                ours += 1
            elif v == -1:
                opp += 1
        if ours > 0 and opp > 0:
            continue  # blocked line
        if ours == 0 and opp == 0:
            continue
        # line is open for one side
        if ours > 0:
            # 1->small, 2->bigger, 3->handled by terminal check
            if ours == 1:
                score += 1
            elif ours == 2:
                score += 30
        elif opp > 0:
            if opp == 1:
                score -= 1
            elif opp == 2:
                score -= 30
    return score

def _minimax(board: Board, player: int, alpha: int, beta: int, depth: int, deadline: float) -> Tuple[int, Optional[Tuple[int,int,int]]]:
    # player: whose turn to play (1 for us, -1 for opponent)
    # Returns (best_value, best_move)
    # value is from perspective of our player (maximizing for us).
    if time.time() >= deadline:
        # Out of time: fall back to heuristic
        return _heuristic(board), None

    w = _check_winner(board)
    if w != 0:
        # Our win => large positive, opponent win => large negative
        return (1000000 if w == 1 else -1000000), None
    if _board_full(board) or depth == 0:
        return _heuristic(board), None

    moves = _legal_moves(board)

    # Move ordering: prioritize moves that create immediate threats/wins or block.
    # This significantly improves pruning.
    def move_score(mv: Tuple[int,int,int]) -> int:
        b2 = _apply_move(board, mv, player)
        w2 = _check_winner(b2)
        if w2 == player:
            return 100000  # immediate win
        # count line potentials quickly via heuristic difference
        return _heuristic(b2) * (1 if player == 1 else -1)

    moves.sort(key=move_score, reverse=True)

    best_move = None
    if player == 1:
        value = -math.inf
        for mv in moves:
            b2 = _apply_move(board, mv, 1)
            v2, _ = _minimax(b2, -1, alpha, beta, depth - 1, deadline)
            if v2 > value:
                value = v2
                best_move = mv
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = math.inf
        for mv in moves:
            b2 = _apply_move(board, mv, -1)
            v2, _ = _minimax(b2, 1, alpha, beta, depth - 1, deadline)
            if v2 < value:
                value = v2
                best_move = mv
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move

def policy(board: Board) -> Tuple[int,int,int]:
    # Ensure legal move: board is 3x3x3 with 0/1/-1
    # Strategy:
    # 1) If we have a winning move now, play it.
    # 2) Else if opponent has a winning move next, block it.
    # 3) Else run minimax with alpha-beta to a depth chosen by remaining empty cells and time budget.
    start = time.time()
    deadline = start + 0.85  # keep a bit of margin

    # Try immediate win
    for mv in _legal_moves(board):
        b2 = _apply_move(board, mv, 1)
        if _check_winner(b2) == 1:
            return mv

    # Try to block immediate opponent win
    for mv in _legal_moves(board):
        b2 = _apply_move(board, mv, -1)
        if _check_winner(b2) == -1:
            return mv

    empties = len(_legal_moves(board))

    # Depth selection: as board fills up, search deeper.
    # Starting at 27 empties -> depth 3-4; near end -> depth up to 8-9.
    if empties >= 22:
        depth = 3
    elif empties >= 16:
        depth = 4
    elif empties >= 10:
        depth = 5
    elif empties >= 6:
        depth = 7
    else:
        depth = 9

    # If time is extremely tight, reduce depth.
    if deadline - start < 0.3:
        depth = 3

    _, best = _minimax(board, 1, alpha=-math.inf, beta=math.inf, depth=depth, deadline=deadline)

    # Fallback: choose any legal move (shouldn't be needed, but guarantees legality)
    if best is None:
        moves = _legal_moves(board)
        # Prefer center-ish squares and corners by simple static ordering
        # (centers/corners often appear in strong 3D play)
        def static_pref(mv):
            i, j, k = mv
            # center distance
            d = abs(i-1) + abs(j-1) + abs(k-1)
            # corners get priority, but center also good => use inverse distance with corner bonus
            corner = (i in (0,2) and j in (0,2) and k in (0,2))
            return (corner * 2) - d
        moves.sort(key=static_pref, reverse=True)
        return moves[0]
    return best
