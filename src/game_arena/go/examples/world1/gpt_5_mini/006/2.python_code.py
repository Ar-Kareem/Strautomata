
#!/usr/bin/env python3
"""
Go play policy for 19x19.

Implements:
    def policy(me: list[tuple[int,int]], opponent: list[tuple[int,int]]) -> tuple[int,int]

Returns a 1-based (row, col) tuple for the chosen move, or (0,0) to pass.
"""

from collections import deque
from typing import List, Tuple

SIZE = 19

def policy(me: List[Tuple[int,int]], opponent: List[Tuple[int,int]]) -> Tuple[int,int]:
    # Build board: 0 empty, 1 me, 2 opponent. Use 0-based indices internally.
    board = [[0]*SIZE for _ in range(SIZE)]
    for (r, c) in me:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[r-1][c-1] = 1
    for (r, c) in opponent:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[r-1][c-1] = 2

    # Precompute center index for influence
    center = (SIZE - 1) / 2.0

    # Helpers
    def in_board(r, c):
        return 0 <= r < SIZE and 0 <= c < SIZE

    def neighbors(r, c):
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r+dr, c+dc
            if in_board(nr, nc):
                yield nr, nc

    # BFS to get group stones and liberties. board is read-only here.
    def get_group_and_liberties(r, c, color, b):
        visited = set()
        q = deque()
        q.append((r,c))
        visited.add((r,c))
        liberties = set()
        stones = []
        while q:
            cr, cc = q.popleft()
            stones.append((cr, cc))
            for nr, nc in neighbors(cr, cc):
                if b[nr][nc] == 0:
                    liberties.add((nr, nc))
                elif b[nr][nc] == color and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
        return stones, liberties

    best_score = None
    best_move = None

    # Iterate over all empty points
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] != 0:
                continue  # occupied

            # simulate placing our stone at (r,c)
            # copy board
            b = [row[:] for row in board]
            b[r][c] = 1  # place

            # Check adjacent opponent groups for captures
            captured = 0
            removed_positions = set()
            for nr, nc in neighbors(r, c):
                if b[nr][nc] == 2:
                    stones, libs = get_group_and_liberties(nr, nc, 2, b)
                    if len(libs) == 0:
                        # capture: remove stones
                        for sr, sc in stones:
                            b[sr][sc] = 0
                            removed_positions.add((sr, sc))
                        captured += len(stones)

            # After captures, check if our placed stone/group has liberties
            stones_ours, libs_ours = get_group_and_liberties(r, c, 1, b)
            if len(libs_ours) == 0:
                # illegal suicide (no liberties and didn't capture)
                continue

            # Heuristic scoring
            score = 0
            # Big bonus for captures
            score += captured * 10000

            # Adjacency bonuses: prefer connecting to own stones and pressing adjacent opponent stones
            adj_own = 0
            adj_opp = 0
            for nr, nc in neighbors(r, c):
                if board[nr][nc] == 1:
                    adj_own += 1
                elif board[nr][nc] == 2:
                    adj_opp += 1
            score += adj_own * 80
            score += adj_opp * 40

            # Prefer moves that increase liberties for our group (size of liberties)
            score += len(libs_ours) * 10

            # Prefer moves near existing own stones (connectivity). Count distance to nearest own stone.
            min_dist_to_own = 1000
            if me:
                for (orow, ocol) in me:
                    # convert to 0-based
                    d = abs((orow-1) - r) + abs((ocol-1) - c)
                    if d < min_dist_to_own:
                        min_dist_to_own = d
                # smaller distance better
                score += max(0, 50 - min_dist_to_own)

            # Center influence: prefer central moves moderately
            dist_center = abs(r - center) + abs(c - center)
            score += max(0, 20 - dist_center)

            # Slight penalty for moves on very edge to encourage influence
            if r == 0 or r == SIZE-1:
                score -= 5
            if c == 0 or c == SIZE-1:
                score -= 5

            # Tiebreakers deterministic: prefer move with smaller (row, col) but include score as primary
            if best_score is None or score > best_score or (score == best_score and (r+1, c+1) < best_move):
                best_score = score
                best_move = (r+1, c+1)  # convert back to 1-based

    if best_move is None:
        # No legal moves: pass
        return (0, 0)
    return best_move

# For module testing (not executed in arena), allow direct calls
if __name__ == "__main__":
    # simple self test: empty board -> should pick a central-ish move (e.g., 10,10)
    print(policy([], []))
