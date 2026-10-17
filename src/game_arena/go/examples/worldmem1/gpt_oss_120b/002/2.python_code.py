
import math
import random
from collections import deque
from typing import List, Tuple, Dict

Board = List[List[int]]  # 0 = empty, 1 = me, 2 = opponent
Point = Tuple[int, int]  # (row, col) 1‑based


def neighbors(r: int, c: int) -> List[Tuple[int, int]]:
    """Return orthogonal neighbours (1‑based)."""
    return [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]


def inside(r: int, c: int) -> bool:
    return 1 <= r <= 19 and 1 <= c <= 19


def get_group(board: Board, sr: int, sc: int, colour: int) -> List[Tuple[int, int]]:
    """BFS to collect all stones of the same colour connected to (sr,sc)."""
    visited = set()
    q = deque()
    q.append((sr, sc))
    visited.add((sr, sc))
    group = [(sr, sc)]
    while q:
        r, c = q.popleft()
        for nr, nc in neighbors(r, c):
            if inside(nr, nc) and (nr, nc) not in visited:
                if board[nr - 1][nc - 1] == colour:
                    visited.add((nr, nc))
                    q.append((nr, nc))
                    group.append((nr, nc))
    return group


def liberties(board: Board, group: List[Tuple[int, int]]) -> int:
    """Count distinct empty points adjacent to the group."""
    lib = set()
    for r, c in group:
        for nr, nc in neighbors(r, c):
            if inside(nr, nc) and board[nr - 1][nc - 1] == 0:
                lib.add((nr, nc))
    return len(lib)


def simulate_move(board: Board, move: Point) -> Tuple[bool, int]:
    """
    Simulate placing my stone at `move`.
    Returns (is_legal, captured_opponent_stones).
    """
    r, c = move
    if board[r - 1][c - 1] != 0:
        return False, 0  # occupied

    # copy board
    new_board = [row[:] for row in board]
    new_board[r - 1][c - 1] = 1  # place my stone

    captured = 0
    # check four neighbours for possible captures
    for nr, nc in neighbors(r, c):
        if not inside(nr, nc):
            continue
        if new_board[nr - 1][nc - 1] == 2:
            opp_group = get_group(new_board, nr, nc, 2)
            if liberties(new_board, opp_group) == 0:
                captured += len(opp_group)
                for gr, gc in opp_group:
                    new_board[gr - 1][gc - 1] = 0

    # after captures, check my own group for suicide
    my_group = get_group(new_board, r, c, 1)
    if liberties(new_board, my_group) == 0:
        return False, 0  # suicide

    return True, captured


def evaluate_move(board: Board, move: Point, captured: int) -> float:
    """Simple heuristic score for a legal move."""
    r, c = move
    # distance to centre (10,10) – centre bias
    dist = math.hypot(r - 10, c - 10)
    score = -dist

    # capture bonus
    score += 0.3 * captured

    # adjacency to opponent stones (before capture)
    adj_opponent = 0
    for nr, nc in neighbors(r, c):
        if inside(nr, nc) and board[nr - 1][nc - 1] == 2:
            adj_opponent += 1
    score += 0.1 * adj_opponent

    # tiny random tie‑breaker
    score += random.random() * 1e-4
    return score


def policy(me: List[Point], opponent: List[Point], memory: Dict) -> Tuple[Point, Dict]:
    """
    Return the next move for the player.
    `memory` can be used to store anything between calls.
    """
    # Initialise board
    board: Board = [[0] * 19 for _ in range(19)]
    for r, c in me:
        board[r - 1][c - 1] = 1
    for r, c in opponent:
        board[r - 1][c - 1] = 2

    # List all empty points
    empties = [(r, c) for r in range(1, 20) for c in range(1, 20) if board[r - 1][c - 1] == 0]

    best_move: Point | None = None
    best_score = -float('inf')
    best_capture = 0

    for mv in empties:
        legal, captured = simulate_move(board, mv)
        if not legal:
            continue
        sc = evaluate_move(board, mv, captured)
        if sc > best_score:
            best_score = sc
            best_move = mv
            best_capture = captured

    # If no legal move found (extremely unlikely) pass.
    if best_move is None:
        action = (0, 0)
    else:
        action = best_move

    # Example of storing something in memory – last move played.
    memory = dict(memory)  # make a shallow copy to avoid mutating caller dict
    memory['last_move'] = action

    return action, memory
