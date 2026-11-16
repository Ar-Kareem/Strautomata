
from __future__ import annotations

from typing import List, Tuple, Set, Dict
import random
import time
from collections import deque

BOARD_N = 11

# Neighbor geometry for hex on 0..10 with rows/cols.
# Using the common "axial-like" offset for pointy-top hex grid rendered as rows/cols:
# Touching neighbors of (r,c) are: (r, c-1), (r, c+1), (r-1, c-1), (r-1, c), (r+1, c), (r+1, c-1)
NEI = [(0, -1), (0, 1), (-1, -1), (-1, 0), (1, 0), (1, -1)]

def inb(r: int, c: int) -> bool:
    return 0 <= r < BOARD_N and 0 <= c < BOARD_N

def all_empty(me: List[Tuple[int,int]], opp: List[Tuple[int,int]]) -> List[Tuple[int,int]]:
    occ = set(me) | set(opp)
    empties = [(r,c) for r in range(BOARD_N) for c in range(BOARD_N) if (r,c) not in occ]
    return empties

def build_graph_adjacency(occupied: Set[Tuple[int,int]], color_set: Set[Tuple[int,int]], n: int = BOARD_N):
    # Returns adjacency list over occupied cells only (virtual edges handled separately).
    adj: Dict[Tuple[int,int], List[Tuple[int,int]]] = {}
    for (r,c) in occupied:
        nbrs = []
        for dr,dc in NEI:
            rr,cc = r+dr, c+dc
            if (rr,cc) in occupied:
                nbrs.append((rr,cc))
        adj[(r,c)] = nbrs
    return adj

def has_winning_path(me: List[Tuple[int,int]], opp: List[Tuple[int,int]], color: str) -> bool:
    # BFS with virtual edges.
    # For black: connect top (row 0) to bottom (row n-1)
    # For white: connect left (col 0) to right (col n-1)
    stones = set(me) if color == 'b' else set(me)
    # color param is irrelevant because "me" is the current player's stones.
    # We'll interpret "me" according to 'color' for win condition.
    targets = set()
    start = deque()
    visited = set()
    if color == 'b':
        for c in range(BOARD_N):
            if (0, c) in stones:
                start.append((0,c))
                visited.add((0,c))
        while start:
            r,c = start.popleft()
            if r == BOARD_N-1:
                return True
            for dr,dc in NEI:
                rr,cc = r+dr, c+dc
                if (rr,cc) in stones and (rr,cc) not in visited:
                    visited.add((rr,cc))
                    start.append((rr,cc))
    else:  # 'w'
        for r in range(BOARD_N):
            if (r, 0) in stones:
                start.append((r,0))
                visited.add((r,0))
        while start:
            r,c = start.popleft()
            if c == BOARD_N-1:
                return True
            for dr,dc in NEI:
                rr,cc = r+dr, c+dc
                if (rr,cc) in stones and (rr,cc) not in visited:
                    visited.add((rr,cc))
                    start.append((rr,cc))
    return False

def would_win_after_move(me: List[Tuple[int,int]], opp: List[Tuple[int,int]], color: str, move: Tuple[int,int]) -> bool:
    new_me = me + [move]
    return has_winning_path(new_me, opp, color)

def opponent_color(color: str) -> str:
    return 'w' if color == 'b' else 'b'

def score_cell(me: List[Tuple[int,int]], opp: List[Tuple[int,int]], color: str, move: Tuple[int,int]) -> float:
    # Connectivity heuristics:
    # - distance-to-target and local adjacency
    # - bridge patterns to create "virtual" connections
    r, c = move
    myset = set(me)
    opset = set(opp)

    # If illegal, score extremely bad
    if (r,c) in myset or (r,c) in opset:
        return -1e9

    # Edge distances
    if color == 'b':
        my_progress = (BOARD_N - 1) - r  # bigger when closer to bottom
        my_front = r  # smaller when closer to top
        # For white opponent: connect left-right
        opp_progress = BOARD_N - 1 - c
        opp_front = c
    else:  # white
        my_progress = (BOARD_N - 1) - c
        my_front = c
        opp_progress = BOARD_N - 1 - r
        opp_front = r

    # Immediate adjacency counts (direct connections are best)
    my_adj = 0
    opp_adj = 0
    for dr,dc in NEI:
        rr,cc = r+dr, c+dc
        if (rr,cc) in myset:
            my_adj += 1
        if (rr,cc) in opset:
            opp_adj += 1

    # Bridge heuristic: for hex, a bridge exists when two stones are "knight-like" connected
    # and the empty cell in the middle completes a safer connection.
    # We'll use a generic bridge pattern checker on our grid coordinates.
    bridge_bonus = 0.0
    # For each empty move, check if it can connect two of our stones that are two steps apart in a bridge configuration.
    # These patterns are known for hex coordinates; we approximate by checking two-step diagonals.
    # We'll explicitly define plausible bridge pairs for (r,c) based on the neighbor geometry.
    # For our coordinate system (row, col), common bridge directions:
    # - horizontal bridge: stones at (r, c-1) and (r-1, c) can be bridged by (r-1, c-1) or vice versa.
    # We'll just cover a set of patterns by relative coordinates.
    # Each pattern gives bonus if both endpoint stones are ours.
    patterns = [
        # endpoints pair 1
        ((0, -1), (-1, 0), (-1, -1)),
        ((0, 1), (1, 0), (1, 1)),
        ((-1, -1), (-1, 0), (-1, -1)),  # degenerate, harmless
        # Another bridge set
        ((-1, 0), (0, 1), (-1, 1)),
        ((1, 0), (0, -1), (1, -1)),
        # Symmetric
        ((0, -1), (1, 0), (1, -1)),
        ((0, 1), (-1, 0), (-1, 1)),
    ]
    # Instead of the above imperfect list, we'll do a more robust check:
    # Look for two our stones that are at "bridge" distance around the candidate.
    # Candidate acts as bridge if there exist two our stones that are adjacent to candidate
    # via different directions forming a non-adjacent pair across a gap.
    # We'll count pairs of our stones among the 6 neighbors that are not directly adjacent to each other.
    neighbors = []
    for dr,dc in NEI:
        rr,cc = r+dr, c+dc
        if (rr,cc) in myset:
            neighbors.append((rr,cc))
    # If there are at least two neighbors, and some of those pairs are "bridgy", bonus.
    # Two neighbors that are exactly one move apart (touching) implies direct connection already counted by my_adj.
    # Bridge aims to connect two components with one move when those neighbors are not touching each other.
    # We'll give bonus for neighbor pairs that are at L1-like separation around.
    def touching(a,b):
        ar,ac=a; br,bc=b
        return any(ar+dr==br and ac+dc==bc for dr,dc in NEI)
    for i in range(len(neighbors)):
        for j in range(i+1,len(neighbors)):
            a = neighbors[i]; b = neighbors[j]
            if not touching(a,b):
                bridge_bonus += 0.35

    # Block bonus: if opponent has stones adjacent, this move can disrupt their local connectivity.
    # Also give extra if move is near opponent frontier.
    block_bonus = opp_adj * 0.9

    # Center bias / smoothness
    center = (BOARD_N-1)/2
    center_dist = abs(r-center) + abs(c-center)
    center_bias = -0.02 * center_dist

    # Combine:
    # emphasize direct adjacency heavily; then progress; then bridge.
    my_progress_term = my_progress * 0.25 + (BOARD_N-1 - my_front) * 0.05
    opp_progress_term = opp_progress * 0.10 + (BOARD_N-1 - opp_front) * 0.02

    # Since higher score should favor our growth and reduce opponent:
    score = 0.0
    score += my_adj * 2.4
    score += bridge_bonus
    score += my_progress_term
    score -= opp_progress_term * 0.35  # prevent stepping into opponent strong areas
    score += block_bonus * 0.6
    score += center_bias
    return score

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    myset = set(me)
    opset = set(opp)

    # Generate empties
    empties = all_empty(me, opp)
    if not empties:
        # Shouldn't happen in legal play; return something legal if forced.
        return (0,0)

    # 1) Immediate win
    for mv in empties:
        if would_win_after_move(me, opp, color, mv):
            return mv

    # 2) Immediate block (opponent win next)
    opp_color = opponent_color(color)
    for mv in empties:
        # Would opponent win if they play mv?
        if would_win_after_move(opp, me, opp_color, mv):
            return mv

    # 3) Strong move scoring
    # Tie-break ordering: prefer moves closer to center early, but still strategic.
    # Also do a small random shuffle to avoid deterministic predictability.
    # Yet keep deterministic-ish: use fixed seed based on board state hash.
    seed = (len(me)*1315423911 + len(opp)*2654435761 + (hash(tuple(sorted(me))) % 1000003)) & 0xffffffff
    rng = random.Random(seed)
    rng.shuffle(empties)

    best_mv = None
    best_sc = -1e18

    # Optional: narrow candidates near frontier for speed, but full board is fine (121 cells).
    for mv in empties:
        sc = score_cell(me, opp, color, mv)

        # Extra: if move increases our connection near both sides, boost.
        r,c = mv
        if color == 'b':
            # closeness to bottom
            sc += (r == BOARD_N-1) * 5.0 + (r <= 2) * 0.3
        else:
            sc += (c == BOARD_N-1) * 5.0 + (c <= 2) * 0.3

        if sc > best_sc:
            best_sc = sc
            best_mv = mv

    # Ensure legal
    if best_mv is None:
        best_mv = empties[0]
    return best_mv
