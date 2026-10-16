
import random
from collections import deque
from typing import List, Tuple, Dict

def policy(me: List[Tuple[int, int]],
           opponent: List[Tuple[int, int]],
           memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    """
    Return the next move (row, col) for the current player on a 19x19 board.
    `me` and `opponent` are lists of (row, col) stone positions (1‑based).
    The function always returns a legal move; (0,0) is used to pass.
    """

    SIZE = 19

    # ----------------------------------------------------------------------
    # Helper functions
    # ----------------------------------------------------------------------
    def empty_board():
        """Create a 20x20 board (index 1..19) filled with 0."""
        return [[0] * (SIZE + 1) for _ in range(SIZE + 1)]

    def build_board() -> List[List[int]]:
        """Place current stones on a fresh board."""
        b = empty_board()
        for r, c in me:
            b[r][c] = 1          # our stones
        for r, c in opponent:
            b[r][c] = 2          # opponent stones
        return b

    NEIGHBORS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def in_bounds(r: int, c: int) -> bool:
        return 1 <= r <= SIZE and 1 <= c <= SIZE

    def bfs_group(board, start_r, start_c, owner):
        """Return all coordinates of the connected group belonging to `owner`
        and the set of its liberties."""
        group = []
        liberties = set()
        q = deque()
        q.append((start_r, start_c))
        visited = set()
        visited.add((start_r, start_c))

        while q:
            r, c = q.popleft()
            group.append((r, c))
            for dr, dc in NEIGHBORS:
                nr, nc = r + dr, c + dc
                if not in_bounds(nr, nc):
                    continue
                if board[nr][nc] == 0:
                    liberties.add((nr, nc))
                elif board[nr][nc] == owner and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
        return group, liberties

    def simulate_move(board, move_r, move_c):
        """Place our stone on (move_r, move_c) and return:
        - new board (list of lists)
        - number of opponent stones captured
        - whether the move is legal (no suicide)
        """
        new_board = [row[:] for row in board]   # deep copy of rows
        new_board[move_r][move_c] = 1           # our stone

        captured = 0

        # 1) Check adjacent opponent groups for capture
        processed = set()
        for dr, dc in NEIGHBORS:
            nr, nc = move_r + dr, move_c + dc
            if not in_bounds(nr, nc):
                continue
            if new_board[nr][nc] != 2:
                continue
            if (nr, nc) in processed:
                continue
            group, libs = bfs_group(new_board, nr, nc, 2)
            processed.update(group)
            if (move_r, move_c) in libs:
                libs.discard((move_r, move_c))
            if len(libs) == 0:
                # capture the whole group
                captured += len(group)
                for gr, gc in group:
                    new_board[gr][gc] = 0

        # 2) Verify our new group has at least one liberty
        our_group, our_libs = bfs_group(new_board, move_r, move_c, 1)
        if len(our_libs) == 0:
            # illegal (suicide)
            return board, 0, False

        return new_board, captured, True

    # ----------------------------------------------------------------------
    # Main policy logic
    # ----------------------------------------------------------------------
    board = build_board()

    best_move = (0, 0)          # pass by default
    best_score = -1

    for r in range(1, SIZE + 1):
        for c in range(1, SIZE + 1):
            if board[r][c] != 0:
                continue  # not empty

            new_board, captured, legal = simulate_move(board, r, c)
            if not legal:
                continue

            # liberties of the new stone (group after potential merges)
            _, libs = bfs_group(new_board, r, c, 1)
            liberties = len(libs)

            # Simple tactical score: captures weighted heavily
            score = captured * 10 + liberties

            if score > best_score:
                best_score = score
                best_move = (r, c)

    # If we never found a legal move, best_move stays (0,0) – pass.
    return best_move, memory
