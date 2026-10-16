
import random
from typing import List, Tuple, Dict

BOARD_SIZE = 19

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    # Initialize memory
    if memory is None:
        memory = {}
    else:
        memory = dict(memory)

    # Build board: 0 empty, 1 me, -1 opponent
    board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for r, c in me:
        board[r-1][c-1] = 1
    for r, c in opponent:
        board[r-1][c-1] = -1

    last_board = memory.get("last_board")

    def neighbors(r, c):
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                yield nr, nc

    def get_group(bd, start):
        sr, sc = start
        color = bd[sr][sc]
        stack = [start]
        visited = set([start])
        stones = []
        liberties = set()
        while stack:
            r, c = stack.pop()
            stones.append((r, c))
            for nr, nc in neighbors(r, c):
                if bd[nr][nc] == color and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    stack.append((nr, nc))
                elif bd[nr][nc] == 0:
                    liberties.add((nr, nc))
        return stones, liberties

    def board_to_tuple(bd):
        return tuple(tuple(row) for row in bd)

    def simulate_move(move):
        if move == (0,0):
            return board
        r, c = move
        if board[r][c] != 0:
            return None
        # Copy board
        b = [row[:] for row in board]
        b[r][c] = 1

        # Capture opponent groups with no liberties
        for nr, nc in neighbors(r, c):
            if b[nr][nc] == -1:
                stones, libs = get_group(b, (nr, nc))
                if len(libs) == 0:
                    for sr, sc in stones:
                        b[sr][sc] = 0

        # Check for suicide
        stones, libs = get_group(b, (r, c))
        if len(libs) == 0:
            return None

        # Simple ko check
        bt = board_to_tuple(b)
        if last_board is not None and bt == last_board:
            return None

        return b

    def get_all_groups(bd, color):
        visited = set()
        groups = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if bd[r][c] == color and (r, c) not in visited:
                    stones, libs = get_group(bd, (r, c))
                    for s in stones:
                        visited.add(s)
                    groups.append((stones, libs))
        return groups

    total_stones = len(me) + len(opponent)

    # 1) Capture moves
    best_move = None
    best_board = None
    best_score = -10**9

    opp_groups = get_all_groups(board, -1)
    capture_moves = {}
    for stones, libs in opp_groups:
        if len(libs) == 1:
            lib = next(iter(libs))
            capture_moves[lib] = capture_moves.get(lib, 0) + len(stones)

    for move, cap in capture_moves.items():
        b = simulate_move(move)
        if b is not None:
            score = 1000 + cap * 10
            if score > best_score:
                best_score = score
                best_move = move
                best_board = b

    # 2) دفاعی حرکات (saving our groups in atari)
    if best_move is None:
        my_groups = get_all_groups(board, 1)
        defense_moves = set()
        for stones, libs in my_groups:
            if len(libs) == 1:
                defense_moves.add(next(iter(libs)))
        for move in defense_moves:
            b = simulate_move(move)
            if b is not None:
                score = 500
                if score > best_score:
                    best_score = score
                    best_move = move
                    best_board = b

    # 3) Heuristic positional play
    if best_move is None:
        candidates = set()
        if total_stones == 0:
            candidates.add((9, 9))  # center
        else:
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if board[r][c] != 0:
                        for nr, nc in neighbors(r, c):
                            if board[nr][nc] == 0:
                                candidates.add((nr, nc))
        if not candidates:
            # fallback to all empty points
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if board[r][c] == 0:
                        candidates.add((r, c))

        for move in candidates:
            b = simulate_move(move)
            if b is None:
                continue
            r, c = move
            dist = abs(r-9) + abs(c-9)
            score = 20 - dist
            adj_own = adj_opp = empty_nb = 0
            for nr, nc in neighbors(r, c):
                if board[nr][nc] == 1:
                    adj_own += 1
                elif board[nr][nc] == -1:
                    adj_opp += 1
                else:
                    empty_nb += 1
            score += adj_own * 3 - adj_opp * 1 + empty_nb * 0.5
            # liberties after move
            stones, libs = get_group(b, (r, c))
            score += len(libs) * 0.5

            if score > best_score:
                best_score = score
                best_move = move
                best_board = b

    # If no legal move, pass
    if best_move is None:
        memory["last_board"] = board_to_tuple(board)
        return (0, 0), memory

    memory["last_board"] = board_to_tuple(best_board)
    return (best_move[0]+1, best_move[1]+1), memory
