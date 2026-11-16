
from __future__ import annotations

from collections import deque
from typing import Dict, List, Set, Tuple, Iterable, Optional

BOARD_SIZE = 19
PASS_MOVE = (0, 0)

Point = Tuple[int, int]


def policy(me: List[Point], opponent: List[Point], memory: Dict) -> Tuple[Point, Dict]:
    """
    Returns (action, memory). action is (row, col) in 1..19 or (0,0) to pass.
    Implements basic Go legality: occupied check, captures, suicide prevention, simple ko.
    """
    me_set: Set[Point] = set(me)
    op_set: Set[Point] = set(opponent)

    # Quick sanity: if lists contain overlaps (shouldn't), treat as occupied.
    occupied = me_set | op_set

    prev_pos = memory.get("prev_pos")  # simple ko: disallow recreating our previous post-move position

    move_number = len(me_set) + len(op_set)

    # Opening preferences if board is sparse.
    opening_points = [
        (4, 4), (4, 16), (16, 4), (16, 16),  # 4-4 points
        (10, 10),  # center
        (4, 10), (10, 4), (10, 16), (16, 10),
    ]

    # --- Helper functions ---
    def on_board(p: Point) -> bool:
        r, c = p
        return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE

    def neighbors(p: Point) -> List[Point]:
        r, c = p
        res = []
        if r > 1:
            res.append((r - 1, c))
        if r < BOARD_SIZE:
            res.append((r + 1, c))
        if c > 1:
            res.append((r, c - 1))
        if c < BOARD_SIZE:
            res.append((r, c + 1))
        return res

    def pos_signature(mset: Set[Point], oset: Set[Point]) -> Tuple[Tuple[Point, ...], Tuple[Point, ...]]:
        # Deterministic signature for ko checking
        return (tuple(sorted(mset)), tuple(sorted(oset)))

    def group_and_liberties(start: Point, my_stones: Set[Point], their_stones: Set[Point]) -> Tuple[Set[Point], Set[Point]]:
        """
        Return (group, liberties) for the connected component of start within my_stones.
        """
        q = deque([start])
        visited = {start}
        group: Set[Point] = {start}
        libs: Set[Point] = set()
        occupied_local = my_stones | their_stones

        while q:
            p = q.popleft()
            for nb in neighbors(p):
                if nb in my_stones and nb not in visited:
                    visited.add(nb)
                    group.add(nb)
                    q.append(nb)
                elif nb not in occupied_local:
                    libs.add(nb)
        return group, libs

    def apply_move(move: Point, mset: Set[Point], oset: Set[Point]) -> Tuple[bool, Set[Point], Set[Point], int, int, int]:
        """
        Simulate placing move for current player (mset) against opponent (oset).
        Returns:
          (legal, new_mset, new_oset, captured, my_libs_after, opp_groups_put_in_atari)
        """
        if move == PASS_MOVE:
            # Passing is always legal; no board change.
            return True, set(mset), set(oset), 0, 0, 0

        if not on_board(move):
            return False, set(mset), set(oset), 0, 0, 0
        if move in mset or move in oset:
            return False, set(mset), set(oset), 0, 0, 0

        new_m = set(mset)
        new_o = set(oset)
        new_m.add(move)

        # Capture any adjacent opponent groups that lose their last liberty.
        captured_total = 0
        checked_opp: Set[Point] = set()
        for nb in neighbors(move):
            if nb in new_o and nb not in checked_opp:
                grp, libs = group_and_liberties(nb, new_o, new_m)
                checked_opp |= grp
                if len(libs) == 0:
                    # Capture
                    new_o -= grp
                    captured_total += len(grp)

        # Suicide check: our group at move must have at least one liberty after captures.
        grp_me, libs_me = group_and_liberties(move, new_m, new_o)
        if len(libs_me) == 0:
            return False, set(mset), set(oset), 0, 0, 0

        # Simple ko: disallow recreating the position after our previous move.
        if prev_pos is not None:
            sig = pos_signature(new_m, new_o)
            if sig == prev_pos:
                return False, set(mset), set(oset), 0, 0, 0

        # Count how many adjacent opponent groups are put into atari by this move (after captures).
        opp_atari = 0
        seen_opp2: Set[Point] = set()
        for nb in neighbors(move):
            if nb in new_o and nb not in seen_opp2:
                grp, libs = group_and_liberties(nb, new_o, new_m)
                seen_opp2 |= grp
                if len(libs) == 1:
                    opp_atari += 1

        return True, new_m, new_o, captured_total, len(libs_me), opp_atari

    def liberties_count_for_group_containing(p: Point, mset: Set[Point], oset: Set[Point]) -> int:
        if p not in mset:
            return 0
        _, libs = group_and_liberties(p, mset, oset)
        return len(libs)

    # --- Candidate generation ---
    empties: Set[Point] = set((r, c) for r in range(1, BOARD_SIZE + 1) for c in range(1, BOARD_SIZE + 1)) - occupied

    if not empties:
        # Board full
        return PASS_MOVE, memory

    # Build a focused candidate set: within distance 2 of any stone, plus opening points.
    candidates: Set[Point] = set()
    all_stones = list(occupied)

    if all_stones:
        # Distance-1 and distance-2 neighborhood around stones
        for s in all_stones:
            for nb in neighbors(s):
                if nb in empties:
                    candidates.add(nb)
                # distance 2
                for nb2 in neighbors(nb):
                    if nb2 in empties:
                        candidates.add(nb2)
    else:
        # Completely empty board: take a strong opening point.
        for p in opening_points:
            if p in empties:
                legal, new_m, new_o, captured, my_libs, opp_atari = apply_move(p, me_set, op_set)
                if legal:
                    new_memory = dict(memory)
                    new_memory["prev_pos"] = pos_signature(new_m, new_o)
                    return p, new_memory
        # Fallback
        first = min(empties)
        new_memory = dict(memory)
        # Passing has no signature update; but keep memory stable.
        return first, new_memory

    # Always include opening points early if empty
    if move_number <= 20:
        for p in opening_points:
            if p in empties:
                candidates.add(p)

    # Ensure we always have something to try
    if not candidates:
        candidates = set(list(empties)[:50])

    # --- Tactical priorities: captures and saves ---
    def find_atari_liberties(target_set: Set[Point], other_set: Set[Point]) -> List[Point]:
        """
        Find liberties of groups in atari for target_set (stones), given other_set.
        Returns list of liberty points (may include duplicates; caller can dedupe).
        """
        seen: Set[Point] = set()
        libs_out: List[Point] = []
        for stone in target_set:
            if stone in seen:
                continue
            grp, libs = group_and_liberties(stone, target_set, other_set)
            seen |= grp
            if len(libs) == 1:
                libs_out.append(next(iter(libs)))
        return libs_out

    # 1) Capture opponent atari if possible
    opp_atari_libs = list(dict.fromkeys(find_atari_liberties(op_set, me_set)))  # dedupe preserving order
    for mv in opp_atari_libs:
        legal, new_m, new_o, captured, my_libs, opp_atari = apply_move(mv, me_set, op_set)
        if legal and captured > 0:
            new_memory = dict(memory)
            new_memory["prev_pos"] = pos_signature(new_m, new_o)
            return mv, new_memory

    # 2) Save our atari if possible
    my_atari_libs = list(dict.fromkeys(find_atari_liberties(me_set, op_set)))
    for mv in my_atari_libs:
        legal, new_m, new_o, captured, my_libs, opp_atari = apply_move(mv, me_set, op_set)
        if legal:
            # Prefer moves that increase liberties or capture
            if captured > 0 or my_libs >= 2:
                new_memory = dict(memory)
                new_memory["prev_pos"] = pos_signature(new_m, new_o)
                return mv, new_memory

    # Add tactical liberty points into candidates
    for mv in opp_atari_libs + my_atari_libs:
        if mv in empties:
            candidates.add(mv)

    # --- Heuristic scoring over candidates ---
    def local_features(move: Point, new_m: Set[Point], new_o: Set[Point], captured: int, my_libs: int, opp_atari: int) -> float:
        # adjacency counts in resulting position (local, cheap)
        adj_my = 0
        adj_opp = 0
        for nb in neighbors(move):
            if nb in new_m:
                adj_my += 1
            elif nb in new_o:
                adj_opp += 1

        # Penalize self-atari (but not illegal); reward healthy liberties
        self_atari_penalty = 0.0
        if my_libs == 1:
            self_atari_penalty = 120.0

        # Mild opening preference: corners / star-points early
        opening_bonus = 0.0
        if move_number <= 16:
            if move in {(4, 4), (4, 16), (16, 4), (16, 16)}:
                opening_bonus += 20.0
            # prefer away from first line unless tactical
            r, c = move
            if (r in (1, 19) or c in (1, 19)) and captured == 0 and opp_atari == 0:
                opening_bonus -= 8.0

        # Prefer central-ish if nothing else (very mild)
        r, c = move
        dist_center = abs(r - 10) + abs(c - 10)
        center_bonus = max(0.0, 6.0 - 0.3 * dist_center)

        score = 0.0
        score += 1000.0 * captured
        score += 90.0 * opp_atari
        score += 10.0 * adj_opp
        score += 3.0 * adj_my
        score += 2.5 * my_libs
        score += opening_bonus + center_bonus
        score -= self_atari_penalty

        return score

    best_move: Optional[Point] = None
    best_score = float("-inf")
    best_result = None  # (new_m, new_o)

    # Evaluate candidates; also keep a fallback legal move if found.
    fallback_move: Optional[Point] = None
    fallback_result = None

    for mv in candidates:
        legal, new_m, new_o, captured, my_libs, opp_atari = apply_move(mv, me_set, op_set)
        if not legal:
            continue
        if fallback_move is None:
            fallback_move = mv
            fallback_result = (new_m, new_o)

        score = local_features(mv, new_m, new_o, captured, my_libs, opp_atari)
        if score > best_score:
            best_score = score
            best_move = mv
            best_result = (new_m, new_o)

    if best_move is not None and best_result is not None:
        new_memory = dict(memory)
        new_memory["prev_pos"] = pos_signature(best_result[0], best_result[1])
        return best_move, new_memory

    # If no candidate was legal, expand search to any legal move (guarantee legality or pass).
    for mv in empties:
        legal, new_m, new_o, captured, my_libs, opp_atari = apply_move(mv, me_set, op_set)
        if legal:
            new_memory = dict(memory)
            new_memory["prev_pos"] = pos_signature(new_m, new_o)
            return mv, new_memory

    # If somehow no legal move exists (rare), pass.
    return PASS_MOVE, memory
