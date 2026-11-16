
import numpy as np
from typing import List, Tuple, Dict, Set

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    # Constants
    N = 19
    EMPTY = 0
    ME = 1
    OPP = 2

    # Build board
    board = np.zeros((N, N), dtype=np.uint8)
    for r, c in me:
        board[r-1, c-1] = ME
    for r, c in opponent:
        board[r-1, c-1] = OPP

    def in_board(r, c):
        return 0 <= r < N and 0 <= c < N

    def get_neighbors(r, c):
        neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
        return [(nr, nc) for nr, nc in neighbors if in_board(nr, nc)]

    def find_group(r, c, player):
        if board[r, c] != player:
            return set()
        visited = set()
        stack = [(r, c)]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            for nr, nc in get_neighbors(*node):
                if board[nr, nc] == player and (nr, nc) not in visited:
                    stack.append((nr, nc))
        return visited

    def get_liberties(group):
        libs = set()
        for r, c in group:
            for nr, nc in get_neighbors(r, c):
                if board[nr, nc] == EMPTY:
                    libs.add((nr, nc))
        return libs

    def would_be_captured_if_played_at(r, c, player):
        board[r, c] = player
        my_group = find_group(r, c, player)
        libs = get_liberties(my_group)
        board[r, c] = EMPTY
        return len(libs) == 0

    def is_suicidal(r, c):
        if would_be_captured_if_played_at(r, c, ME):
            opp_neighbors = [board[nr, nc] == OPP for nr, nc in get_neighbors(r, c)]
            # Only suicidal if no opponent group gets captured
            for nr, nc in get_neighbors(r, c):
                if board[nr, nc] == OPP:
                    opp_group = find_group(nr, nc, OPP)
                    opp_libs_before = get_liberties(opp_group)
                    # Simulate capture
                    captured = True
                    for lr, lc in opp_libs_before:
                        if (lr, lc) != (r, c) or len(opp_libs_before) > 1:
                            captured = False
                            break
                    if captured:
                        # This move kills the group, so not suicidal
                        return False
            return True
        return False

    def get_captured_groups_if_played_at(r, c, player):
        captured = []
        for nr, nc in get_neighbors(r, c):
            if board[nr, nc] == (OPP if player == ME else ME) and not would_be_captured_if_played_at(nr, nc, (OPP if player == ME else ME)):
                continue
            # Temporarily place stone
            board[r, c] = player
            opp_group = find_group(nr, nc, OPP if player == ME else ME)
            libs = get_liberties(opp_group)
            board[r, c] = EMPTY
            if len(libs) == 0 and len(opp_group) > 0:
                captured.extend(list(opp_group))
        return captured

    # Collect all legal moves that are not suicidal
    legal_moves = []
    scores = {}

    best_action = (0, 0)  # default pass
    best_score = -1

    # Check if we need to pass (rare)
    if len(me) + len(opponent) >= N*N:
        return (0, 0), memory

    # Precompute my groups and their states
    my_groups = []
    for r, c in me:
        group = find_group(r, c, ME)
        if all(board[gr, gc] == ME for gr, gc in group) and group not in my_groups:
            my_groups.append((group, get_liberties(group)))

    opp_groups = []
    for r, c in opponent:
        group = find_group(r, c, OPP)
        if all(board[gr, gc] == OPP for gr, gc in group) and group not in opp_groups:
            opp_groups.append((group, get_liberties(group)))

    # Center weights for influence (encourage playing in center)
    center = (9, 9)
    def dist_to_center(r, c):
        return -((r-center[0])**2 + (c-center[1])**2)  # negative squared distance

    # Scan over all empty positions
    for r in range(N):
        for c in range(N):
            if board[r, c] != EMPTY:
                continue

            score = 0.0
            pos = (r, c)

            # 1. Check if it's suicidal
            if is_suicidal(r, c):
                continue

            # 2. Check captures
            captured = get_captured_groups_if_played_at(r, c, ME)
            if captured:
                score += 100 * len(captured)  # big reward for capture

            # 3. Prevent atari on our groups?
            for group, libs in my_groups:
                if pos in libs and len(libs) == 1:
                    # We are saving a group from capture
                    score += 50

            # 4. Put opponent in atari?
            for nr, nc in get_neighbors(r, c):
                if board[nr, nc] == OPP:
                    opp_group = find_group(nr, nc, OPP)
                    opp_libs = get_liberties(opp_group)
                    if len(opp_libs) == 2 and pos in opp_libs:
                        # After we play here, opponent group will have one liberty
                        score += 30

            # 5. Encourage playing near existing stones (but not too much)
            friendly_neighbors = sum(1 for nr, nc in get_neighbors(r, c) if board[nr, nc] == ME)
            opp_neighbors = sum(1 for nr, nc in get_neighbors(r, c) if board[nr, nc] == OPP)
            score += friendly_neighbors * 5
            if opp_neighbors == 0:
                score += dist_to_center(r, c) * 0.01  # prefer center if not near opponents

            # 6. Connection bonus
            if friendly_neighbors >= 2:
                score += 10

            if score > best_score:
                best_score = score
                best_action = (r+1, c+1)  # convert to 1-indexed

    # If no valid move found, pass
    if best_score <= -1:
        best_action = (0, 0)

    return best_action, memory
