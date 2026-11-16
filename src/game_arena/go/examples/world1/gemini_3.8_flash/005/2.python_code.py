
import random

def get_neighbors(r: int, c: int) -> list[tuple[int, int]]:
    res = []
    if r > 1: res.append((r - 1, c))
    if r < 19: res.append((r + 1, c))
    if c > 1: res.append((r, c - 1))
    if c < 19: res.append((r, c + 1))
    return res

def get_diagonals(r: int, c: int) -> list[tuple[int, int]]:
    res = []
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = r + dr, c + dc
        if 1 <= nr <= 19 and 1 <= nc <= 19:
            res.append((nr, nc))
    return res

def find_chains(stones: set[tuple[int, int]], board: dict[tuple[int, int], int]):
    visited = set()
    chains = []
    for stone in stones:
        if stone in visited:
            continue
        chain = []
        liberties = set()
        queue = [stone]
        visited.add(stone)
        while queue:
            curr = queue.pop()
            chain.append(curr)
            for nbr in get_neighbors(curr[0], curr[1]):
                nbr_val = board.get(nbr, 0)
                if nbr_val == 0:
                    liberties.add(nbr)
                elif nbr_val == board[stone] and nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
        chains.append((chain, liberties))
    return chains

def is_true_eye(r: int, c: int, color: int, board: dict[tuple[int, int], int]) -> bool:
    nbrs = get_neighbors(r, c)
    for nbr in nbrs:
        if board.get(nbr, 0) != color:
            return False
    diags = get_diagonals(r, c)
    opp_diags = sum(1 for d in diags if board.get(d, 0) not in (0, color))
    if len(nbrs) == 4:
        return opp_diags <= 1
    return opp_diags == 0

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    my_stones = set(me)
    opp_stones = set(opponent)
    
    board = {}
    for pos in my_stones:
        board[pos] = 1
    for pos in opp_stones:
        board[pos] = 2

    total_stones = len(my_stones) + len(opp_stones)

    my_chains = find_chains(my_stones, board)
    opp_chains = find_chains(opp_stones, board)

    opp_chain_map = {}
    for idx, (chain, libs) in enumerate(opp_chains):
        for s in chain:
            opp_chain_map[s] = idx

    my_chain_map = {}
    for idx, (chain, libs) in enumerate(my_chains):
        for s in chain:
            my_chain_map[s] = idx

    candidates = {}

    for r in range(1, 20):
        for c in range(1, 20):
            pt = (r, c)
            if pt in board:
                continue

            nbrs = get_neighbors(r, c)
            captures = 0
            captured_stones_count = 0
            for nbr in nbrs:
                if board.get(nbr, 0) == 2:
                    chain_idx = opp_chain_map[nbr]
                    c_stones, c_libs = opp_chains[chain_idx]
                    if len(c_libs) == 1 and pt in c_libs:
                        captures += 1
                        captured_stones_count += len(c_stones)

            has_liberty = any(board.get(nbr, 0) == 0 for nbr in nbrs)
            connects_to_safe = False
            for nbr in nbrs:
                if board.get(nbr, 0) == 1:
                    chain_idx = my_chain_map[nbr]
                    c_stones, c_libs = my_chains[chain_idx]
                    if len(c_libs) > 1:
                        connects_to_safe = True
                        break

            # Suicide check
            if not has_liberty and not connects_to_safe and captures == 0:
                continue

            if is_true_eye(r, c, 1, board) and captures == 0:
                continue

            # Base score by board line
            line_r = min(r, 20 - r)
            line_c = min(c, 20 - c)
            line = min(line_r, line_c)
            
            score = 0.0
            if line == 3:
                score += 18.0
            elif line == 4:
                score += 20.0
            elif line == 2:
                score += 4.0
            elif line == 5:
                score += 12.0
            elif line == 1:
                score -= 25.0

            # Opening boost for star points and corners
            if total_stones < 20:
                if pt in [(4, 4), (4, 16), (16, 4), (16, 16)]:
                    score += 65.0
                elif pt in [(4, 10), (10, 4), (10, 16), (16, 10), (10, 10)]:
                    score += 40.0
                elif pt in [(3, 4), (4, 3), (3, 16), (16, 3), (4, 17), (17, 4), (16, 17), (17, 16)]:
                    score += 55.0

            # Huge reward for immediate captures
            if captures > 0:
                score += 300.0 + 80.0 * captured_stones_count

            # Defense: Saving our chains in atari
            for nbr in nbrs:
                if board.get(nbr, 0) == 1:
                    chain_idx = my_chain_map[nbr]
                    c_stones, c_libs = my_chains[chain_idx]
                    if len(c_libs) == 1 and pt in c_libs:
                        score += 250.0 + 60.0 * len(c_stones)
                    elif len(c_libs) == 2:
                        score += 40.0

            # Offense: Putting opponent chains into atari
            for nbr in nbrs:
                if board.get(nbr, 0) == 2:
                    chain_idx = opp_chain_map[nbr]
                    c_stones, c_libs = opp_chains[chain_idx]
                    if len(c_libs) == 2 and pt in c_libs:
                        score += 50.0 + 15.0 * len(c_stones)

            # Shape: Connecting separate friendly groups
            friendly_groups = set()
            for nbr in nbrs:
                if board.get(nbr, 0) == 1:
                    friendly_groups.add(my_chain_map[nbr])
            if len(friendly_groups) >= 2:
                score += 35.0 * len(friendly_groups)

            # Shape: Cutting opponent groups
            opp_groups = set()
            for nbr in nbrs:
                if board.get(nbr, 0) == 2:
                    opp_groups.add(opp_chain_map[nbr])
            if len(opp_groups) >= 2:
                score += 30.0 * len(opp_groups)

            # Proximity to action
            has_adjacent = any(board.get(nbr, 0) != 0 for nbr in nbrs)
            if has_adjacent:
                score += 15.0

            # Penalize self-atari unless capturing
            if captures == 0:
                empty_nbrs = sum(1 for nbr in nbrs if board.get(nbr, 0) == 0)
                if empty_nbrs == 0:
                    max_lib_connected = 0
                    for nbr in nbrs:
                        if board.get(nbr, 0) == 1:
                            chain_idx = my_chain_map[nbr]
                            max_lib_connected = max(max_lib_connected, len(my_chains[chain_idx][1]))
                    if max_lib_connected <= 2:
                        score -= 150.0

            # Slight randomness to break ties
            score += random.uniform(0.0, 1.0)
            candidates[pt] = score

    if not candidates:
        return (0, 0)

    best_move = max(candidates.keys(), key=lambda move: candidates[move])
    if candidates[best_move] < -100.0 and total_stones > 100:
        return (0, 0)

    return best_move
