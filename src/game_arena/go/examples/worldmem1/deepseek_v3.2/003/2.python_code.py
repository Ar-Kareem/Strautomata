
import numpy as np
from collections import deque

def policy(me, opponent, memory):
    BOARD_SIZE = 19
    EMPTY = 0
    MY_STONE = 1
    OP_STONE = 2

    # Initialize memory fields
    if "move_count" not in memory:
        memory["move_count"] = 0
        memory["last_moves"] = []
        memory["board_hash"] = None
        memory["ko_point"] = None
    memory["move_count"] += 1
    move_count = memory["move_count"]

    # Build board array
    board = np.zeros((BOARD_SIZE + 2, BOARD_SIZE + 2), dtype=int)  # 1-indexed with border
    for r, c in me:
        board[r, c] = MY_STONE
    for r, c in opponent:
        board[r, c] = OP_STONE

    # Helper: find groups and liberties
    def find_group_and_liberties(start_r, start_c, stone_type):
        visited = set()
        q = deque([(start_r, start_c)])
        stones = []
        liberties = set()
        while q:
            r, c = q.popleft()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            stones.append((r, c))
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                    if board[nr, nc] == stone_type:
                        q.append((nr, nc))
                    elif board[nr, nc] == EMPTY:
                        liberties.add((nr, nc))
        return stones, liberties

    # Get all groups
    all_my_groups = []
    all_op_groups = []
    processed = set()
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r, c] == MY_STONE and (r, c) not in processed:
                stones, libs = find_group_and_liberties(r, c, MY_STONE)
                all_my_groups.append((stones, libs))
                processed.update(stones)
    processed.clear()
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r, c] == OP_STONE and (r, c) not in processed:
                stones, libs = find_group_and_liberties(r, c, OP_STONE)
                all_op_groups.append((stones, libs))
                processed.update(stones)

    # Urgent moves: defend groups with 1 liberty, attack groups with 1 liberty
    defend_moves = []
    for stones, libs in all_my_groups:
        if len(libs) == 1:
            defend_moves.extend(libs)
    attack_moves = []
    for stones, libs in all_op_groups:
        if len(libs) == 1:
            attack_moves.extend(libs)

    # If can capture, do it (unless ko)
    if attack_moves:
        for move in attack_moves:
            if move != memory.get("ko_point"):
                return move, memory

    # If must defend, do it
    if defend_moves:
        for move in defend_moves:
            if board[move[0], move[1]] == EMPTY:
                return move, memory

    # Influence map
    influence = np.zeros((BOARD_SIZE + 2, BOARD_SIZE + 2), dtype=float)
    decay = 0.7
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r, c] == MY_STONE:
                for rr in range(1, BOARD_SIZE + 1):
                    for cc in range(1, BOARD_SIZE + 1):
                        dist = max(abs(rr - r), abs(cc - c))
                        influence[rr, cc] += decay ** dist
            elif board[r, c] == OP_STONE:
                for rr in range(1, BOARD_SIZE + 1):
                    for cc in range(1, BOARD_SIZE + 1):
                        dist = max(abs(rr - r), abs(cc - c))
                        influence[rr, cc] -= decay ** dist

    # Opening book: star points and corners
    opening_moves = [
        (4, 4), (4, 16), (16, 4), (16, 16),  # corners
        (4, 10), (10, 4), (10, 16), (16, 10),  # side stars
        (10, 10)  # center star
    ]
    if move_count <= 20:
        for move in opening_moves:
            if board[move[0], move[1]] == EMPTY:
                # Prefer reducing opponent's strong influence area
                if influence[move[0], move[1]] < -0.5:
                    return move, memory
        # If none with high opponent influence, pick first empty opening move
        for move in opening_moves:
            if board[move[0], move[1]] == EMPTY:
                return move, memory

    # Evaluate all empty points
    best_score = -float('inf')
    best_move = (0, 0)  # pass as fallback
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r, c] != EMPTY:
                continue
            # Avoid immediate repetition
            if (r, c) in memory.get("last_moves", []):
                continue
            # Ko avoidance
            if (r, c) == memory.get("ko_point"):
                continue

            score = 0.0
            # Influence gain
            score += 2.0 * (influence[r, c] + 1.0)  # bias toward positive influence

            # Centrality bonus (slight preference for center)
            center_dist = max(abs(r - 10), abs(c - 10))
            score += 0.1 * (9 - center_dist)

            # Liberty bonus: if touching own group with few liberties, good
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                    if board[nr, nc] == MY_STONE:
                        # find group
                        for stones, libs in all_my_groups:
                            if (nr, nc) in stones:
                                score += 0.5 * (4 - len(libs))
                                break
                    elif board[nr, nc] == OP_STONE:
                        for stones, libs in all_op_groups:
                            if (nr, nc) in stones:
                                score += 0.8 * (4 - len(libs))
                                break

            # Distance to nearest stone (encourage not too close in opening)
            if move_count < 40:
                min_dist = 10
                for rr in range(1, BOARD_SIZE + 1):
                    for cc in range(1, BOARD_SIZE + 1):
                        if board[rr, cc] != EMPTY:
                            d = max(abs(rr - r), abs(cc - c))
                            if d < min_dist:
                                min_dist = d
                if min_dist < 2:
                    score -= 1.0

            if score > best_score:
                best_score = score
                best_move = (r, c)

    # Update memory
    memory["last_moves"] = (memory.get("last_moves", []) + [best_move])[-6:]  # keep last 6
    # Simple ko detection: if move captures exactly one stone, set ko point
    if best_move != (0, 0):
        capture_count = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = best_move[0] + dr, best_move[1] + dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE and board[nr, nc] == OP_STONE:
                # check if that group has exactly 1 liberty before move
                for stones, libs in all_op_groups:
                    if (nr, nc) in stones:
                        if len(libs) == 1 and list(libs)[0] == best_move:
                            capture_count += len(stones)
                        break
        if capture_count == 1:
            memory["ko_point"] = (best_move[0], best_move[1])
        else:
            memory["ko_point"] = None

    return best_move, memory
