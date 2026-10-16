
import itertools
from collections import deque
from typing import List, Tuple, Set, Dict

BOARD_SIZE = 19
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

def add(p, d):
    return (p[0] + d[0], p[1] + d[1])

def on_board(p):
    return 1 <= p[0] <= BOARD_SIZE and 1 <= p[1] <= BOARD_SIZE

def get_group(board: Dict[Tuple[int, int], int],
              start: Tuple[int, int],
              color: int) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
    """Return (stones, liberties) of the connected group containing start."""
    stones = set()
    liberties = set()
    q = deque([start])
    stones.add(start)
    while q:
        cur = q.popleft()
        for d in DIRS:
            nb = add(cur, d)
            if not on_board(nb):
                continue
            if nb not in board:
                liberties.add(nb)
            elif board[nb] == color and nb not in stones:
                stones.add(nb)
                q.append(nb)
    return stones, liberties

def find_capture_move(board: Dict[Tuple[int, int], int]) -> Tuple[int, int]:
    """Return a move that captures an opponent group with one liberty, or (0,0)."""
    visited = set()
    for pos, col in board.items():
        if col != -1 or pos in visited:   # opponent stones are -1
            continue
        stones, libs = get_group(board, pos, -1)
        visited.update(stones)
        if len(libs) == 1:
            lib = next(iter(libs))
            return lib
    return (0, 0)

def is_move_suicidal(board: Dict[Tuple[int, int], int],
                     move: Tuple[int, int]) -> bool:
    """Check whether placing a stone at move would be suicide (no liberties)."""
    temp_board = board.copy()
    temp_board[move] = 1  # our stone
    # Merge with any adjacent own groups
    stones, libs = get_group(temp_board, move, 1)
    if libs:
        return False
    # If the move captures any opponent group, it's legal even with 0 libs
    for d in DIRS:
        nb = add(move, d)
        if nb in temp_board and temp_board[nb] == -1:
            opp_stones, opp_libs = get_group(temp_board, nb, -1)
            if len(opp_libs) == 0:
                return False
    return True

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Build board dictionary
    board: Dict[Tuple[int, int], int] = {}
    for r, c in me:
        board[(r, c)] = 1
    for r, c in opponent:
        board[(r, c)] = -1

    # 1) Try to capture
    cap_move = find_capture_move(board)
    if cap_move != (0, 0):
        return cap_move

    # 2) Find best aggressive move
    best_move = (0, 0)
    best_score = -1
    occupied = set(board.keys())
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            pt = (r, c)
            if pt in occupied:
                continue
            # score = number of adjacent opponent stones
            score = sum(1 for d in DIRS if add(pt, d) in board and board[add(pt, d)] == -1)
            if score < best_score:
                continue
            if is_move_suicidal(board, pt):
                continue
            if score > best_score:
                best_score = score
                best_move = pt

    if best_move != (0, 0):
        return best_move

    # 3) No good move found -> pass
    return (0, 0)
