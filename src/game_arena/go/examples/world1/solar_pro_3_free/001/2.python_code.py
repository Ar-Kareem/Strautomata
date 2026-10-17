
import random
from typing import List, Tuple, Dict, Set
import numpy as np

SIZE = 19
NEIGHBORS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def neighbor_coords(r: int, c: int) -> List[Tuple[int, int]]:
    """Return the four orthogonal neighbour coordinates (including out‑of‑bounds)."""
    return [(r + dr, c + dc) for dr, dc in NEIGHBORS]

def compute_groups(
    board: Dict[Tuple[int, int], str],
    stones: List[Tuple[int, int]],
    owner: str,
) -> Tuple[Dict[Tuple[int, int], int], List[Dict]]:
    """
    Group stones by BFS. Returns:
    * stone_to_group: mapping of each stone point → group id
    * groups: list of group dicts with keys
        - owner: 'B' or 'W'
        - stones: set of points in the group
        - liberties: set of empty neighbour points (including out‑of‑bounds)
        - liberties_count: integer size of liberties set
    """
    stone_to_group = {}
    groups = []
    gid = 1

    for s in stones:
        if s in stone_to_group:
            continue
        g = {
            "owner": owner,
            "stones": {s},
            "liberties": set(),
            "liberties_count": 0,
        }
        visited = set()
        stack = [s]

        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            stone_to_group[cur] = gid

            # collect liberties
            for nb in neighbor_coords(cur[0], cur[1]):
                # out‑of‑bounds counts as a liberty
                if not (1 <= nb[0] <= SIZE and 1 <= nb[1] <= SIZE):
                    g["liberties"].add(nb)
                else:
                    if board.get(nb, ".") == ".":
                        g["liberties"].add(nb)

            # connect to same‑coloured neighbours
            if nb in board and board[nb] == owner and nb not in stone_to_group:
                stack.append(nb)

        g["liberties_count"] = len(g["liberties"])
        groups.append(g)
        gid += 1

    return stone_to_group, groups

def simulate_move(board: Dict, p: Tuple[int, int], player: str) -> Tuple[int, List[Dict]]:
    """
    Copy the board, place a stone for `player` at `p`, and recompute groups.
    Returns (player's group mapping, list of player groups) for the new board.
    """
    new_board = board.copy()
    new_board[p] = player

    # recompute groups for the player whose turn it is
    stone_to_group, groups = compute_groups(new_board, [], player)
    return stone_to_group, groups

def is_legal_capture(board: Dict, move: Tuple[int, int], player: str) -> bool:
    """
    Checks whether placing a stone for `player` at `move` captures opponent stones
    and does not create a suicide (our groups must still have at least one liberty).
    """
    opp = "W" if player == "B" else "B"

    # simulate the move
    _, groups = simulate_move(board, move, player)

    # 1) opponent groups must be removed (dead)
    opp_groups = {g: idx for idx, g in enumerate(board.values()) if g == opp}
    # we need the group data from opponent side before the move
    # recompute opponent groups on the *original* board for classification
    _, opp_groups_orig = compute_groups(board, [s for s, col in board.items() if col == opp], opp)
    for opp_group in opp_groups_orig:
        opp_group_key = opp_group["stones"].pop()  # any stone, we'll find group id later
        # find the group id from stone_to_group on the simulated board
        # simpler: just check after move if any opponent stone group still has liberties
        # after move we need to recompute opponent groups again
        _, opponent_groups = compute_groups(board, [s for s, col in board.items() if col == opp], opp)
        opp_owner_to_groups = {s: idx for idx, s in enumerate([s for s, col in board.items() if col == opp])}
        # we have groups list for opponent on original board; find groups that survive
        alive = False
        for og in opp_groups_orig:
            # check if any stone of this group is still on board after move
            if any(p in board for p in og["stones"]):
                # recompute liberties for this group after move
                # just check if liberties count became 0
                # we need to recompute liberties for this group on new board
                # but we can recompute for opponent groups using simulate_move
                # For simplicity, we will recompute opponent groups on new board as well
                # and then see if any have liberties_count > 0
                # create a new temporary board that contains both players
                temp_board = board.copy()
                temp_board[move] = player
                _, opp_temp_groups = compute_groups(temp_board, [], opp)
                for tg in opp_temp_groups:
                    # locate the group by one of its stones that survived
                    if any(s in tg["stones"] and s in board for s in tg["stones"]):
                        if tg["liberties_count"] > 0:
                            alive = True
                            break
        if alive:
            return False

    # 2) our groups must retain at least one liberty
    _, our_groups = compute_groups(board, [s for s, col in board.items() if col == player], player)
    for grp in our_groups:
        if grp["liberties_count"] == 0:
            return False
    return True

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    # ------------------------------------------------------------
    # 1. Build current board
    # ------------------------------------------------------------
    board: Dict[Tuple[int, int], str] = {}
    for p in me:
        board[p] = "B"
    for p in opponent:
        board[p] = "W"

    # ------------------------------------------------------------
    # 2. Compute groups and liberties for both colours
    # ------------------------------------------------------------
    stone_to_group_me, groups_me = compute_groups(board, me, "B")
    stone_to_group_opp, groups_opp = compute_groups(board, opponent, "W")

    # ------------------------------------------------------------
    # 3. Immediate capture moves
    # ------------------------------------------------------------
    for g_opp in groups_opp:
        if g_opp["liberties_count"] == 1:
            # try each liberty of this group
            for liberty in g_opp["liberties"]:
                if liberty in board and board[liberty] == ".":
                    # simulate the capture
                    if is_legal_capture(board, liberty, "B"):
                        return liberty

    # ------------------------------------------------------------
    # 4. Score every empty point
    # ------------------------------------------------------------
    empties: Set[Tuple[int, int]] = {
        (r, c)
        for r in range(1, SIZE + 1)
        for c in range(1, SIZE + 1)
        if (r, c) not in board
    }

    if not empties:
        return (0, 0)  # board full → pass

    # Helper constants
    REWARD = 5          # each opponent liberty removed
    PUNISH = -10        # each of our own liberties removed
    CAPTURE_BONUS = 20  # extra reward when the move actually captures a group
    CORNER_BONUS = 5    # reward for moves very close to corners
    STAR_BONUS = 3      # reward for playing on star points
    PASSED = (0, 0)

    # Predefined corner and star coordinates
    CORNER_COORDS = {(1, 1), (1, 19), (19, 1), (19, 19)}
    STAR_COORDS = {
        (1, 4), (1, 16), (4, 1), (4, 19),
        (16, 1), (16, 19), (4, 4), (4, 16), (16, 4), (16, 16),
    }

    def corner_bonus(p: Tuple[int, int]) -> int:
        """Manhatten distance to nearest corner (Manhattan distance <= 3) → bonus."""
        r, c = p
        min_dist = min(
            abs(r - 1) + abs(c - 1),
            abs(r - 1) + abs(c - 19),
            abs(r - 19) + abs(c - 1),
            abs(r - 19) + abs(c - 19),
        )
        return 5 if min_dist <= 3 else 0

    def star_bonus(p: Tuple[int, int]) -> int:
        return 3 if p in STAR_COORDS else 0

    scores: Dict[Tuple[int, int], int] = {}
    captured_liberties = []

    for p in empties:
        # count opponent liberties that would disappear
        opp_liberties_removed = 0
        # count our own liberties that would disappear
        our_liberties_removed = 0

        for nb in neighbor_coords(p[0], p[1]):
            # opponent stone adjacent?
            if nb in board and board[nb] == "W":
                # find the opponent group to which nb belongs
                gid = stone_to_group_opp[nb]
                opp_group = groups_opp[gid]
                if p in opp_group["liberties"]:
                    opp_liberties_removed += REWARD
                # note: if opponent group had only one liberty, this move would capture it
                # – we will treat capture later

            # our own stone adjacent?
            if nb in board and board[nb] == "B":
                gid = stone_to_group_me[nb]
                our_group = groups_me[gid]
                if p in our_group["liberties"]:
                    our_liberties_removed += PUNISH

        # capture bonus if the move kills an opponent group
        capture_bonus = 0
        # check opponent groups that have only one liberty and whose liberty is p
        for opp_group in groups_opp:
            if opp_group["liberties_count"] == 1 and p in opp_group["liberties"]:
                capture_bonus = CAPTURE_BONUS

        total_score = opp_liberties_removed + our_liberties_removed + capture_bonus + corner_bonus(p) + star_bonus(p)

        scores[p] = total_score
        captured_liberties.append((capture_bonus > 0, total_score, p))

    # ------------------------------------------------------------
    # 5. Pick the best move
    # ------------------------------------------------------------
    # Choose among moves that capture at least one opponent group first
    capture_candidates = [p for p, s in scores.items() if s == capture_bonus and capture_bonus > 0]

    if capture_candidates:
        # pick the one with the highest overall score (ties random)
        best = max(capture_candidates, key=lambda x: scores[x])
        # deterministic: just return max score
        return best

    # If no capture, take the highest‑score move.
    best_move = max(scores.items(), key=lambda kv: kv[1])[0]

    return best_move
