
import random

BOARD_SIZE = 19

OPENING_POINTS = [
    (4, 4), (16, 4), (4, 16), (16, 16),
    (4, 10), (10, 4), (16, 10), (10, 16), (10, 10),
    (3, 4), (4, 3), (16, 3), (17, 4), (3, 16), (4, 17), (16, 17), (17, 16),
    (3, 10), (10, 3), (17, 10), (10, 17),
    (3, 3), (17, 3), (3, 17), (17, 17),
]

def in_bounds(r: int, c: int) -> bool:
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE

def get_adj(r: int, c: int):
    res = []
    if r > 1: res.append((r - 1, c))
    if r < BOARD_SIZE: res.append((r + 1, c))
    if c > 1: res.append((r, c - 1))
    if c < BOARD_SIZE: res.append((r, c + 1))
    return res

class BoardState:
    def __init__(self, my_stones: set, opp_stones: set):
        self.grid = {}
        for p in my_stones:
            self.grid[p] = 1
        for p in opp_stones:
            self.grid[p] = 2

    def get_group_and_liberties(self, start_pos: tuple[int, int]):
        color = self.grid.get(start_pos)
        if not color:
            return set(), set()
        group = set([start_pos])
        liberties = set()
        queue = [start_pos]
        visited = set([start_pos])

        while queue:
            curr = queue.pop()
            for neighbor in get_adj(curr[0], curr[1]):
                if neighbor not in self.grid:
                    liberties.add(neighbor)
                elif self.grid[neighbor] == color and neighbor not in visited:
                    visited.add(neighbor)
                    group.add(neighbor)
                    queue.append(neighbor)
        return group, liberties

    def simulate_move(self, r: int, c: int, color: int):
        """Simulates placing a stone. Returns (is_legal, captured_stones, my_liberties_count)."""
        if (r, c) in self.grid:
            return False, set(), 0

        opp_color = 2 if color == 1 else 1
        adj = get_adj(r, c)

        # Temporarily place stone
        self.grid[(r, c)] = color

        captured = set()
        checked_opp_groups = set()

        # Check adjacent opponent groups for capture
        for nr, nc in adj:
            if self.grid.get((nr, nc)) == opp_color and (nr, nc) not in checked_opp_groups:
                opp_grp, opp_libs = self.get_group_and_liberties((nr, nc))
                checked_opp_groups.update(opp_grp)
                if len(opp_libs) == 0:
                    captured.update(opp_grp)

        # Remove captured stones
        for stone in captured:
            del self.grid[stone]

        # Check friendly liberties
        my_grp, my_libs = self.get_group_and_liberties((r, c))
        my_lib_count = len(my_libs)

        # Revert simulation
        for stone in captured:
            self.grid[stone] = opp_color
        del self.grid[(r, c)]

        if my_lib_count == 0 and len(captured) == 0:
            return False, set(), 0

        return True, captured, my_lib_count


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    my_stones = set(me)
    opp_stones = set(opponent)
    board = BoardState(my_stones, opp_stones)

    history = memory.get('history', set())
    current_board_key = (frozenset(my_stones), frozenset(opp_stones))
    history.add(current_board_key)

    total_stones = len(my_stones) + len(opp_stones)

    # Precompute existing chains and liberties
    opp_groups = []
    seen_opp = set()
    for s in opp_stones:
        if s not in seen_opp:
            grp, libs = board.get_group_and_liberties(s)
            seen_opp.update(grp)
            opp_groups.append((grp, libs))

    my_groups = []
    seen_my = set()
    for s in my_stones:
        if s not in seen_my:
            grp, libs = board.get_group_and_liberties(s)
            seen_my.update(grp)
            my_groups.append((grp, libs))

    # Candidate move generation
    candidates = set()
    if total_stones < 20:
        for pt in OPENING_POINTS:
            if pt not in board.grid:
                candidates.add(pt)

    # Add points in vicinity of all existing stones
    all_stones = list(my_stones | opp_stones)
    if not all_stones:
        candidates.add((4, 4))
    else:
        for r, c in all_stones:
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and (nr, nc) not in board.grid:
                        candidates.add((nr, nc))

    # Evaluate each candidate move
    best_move = None
    best_score = -1e9

    for r, c in candidates:
        is_legal, captured, my_libs = board.simulate_move(r, c, 1)
        if not is_legal:
            continue

        # Check Ko / Superko rule
        next_my = (my_stones - captured) | {(r, c)}
        next_opp = opp_stones - captured
        next_state_key = (frozenset(next_opp), frozenset(next_my)) # viewed next turn
        if (frozenset(next_my), frozenset(next_opp)) in history:
            continue

        score = 0.0

        # 1. Capturing opponent stones
        cap_count = len(captured)
        if cap_count > 0:
            score += 150.0 + cap_count * 50.0

        # 2. Liberty evaluation and avoiding self-atari
        if my_libs == 1:
            if cap_count == 0:
                score -= 300.0  # Self-atari penalty
            else:
                score -= 60.0
        elif my_libs == 2:
            score += 5.0
        elif my_libs >= 3:
            score += 25.0 + min(my_libs, 6) * 3.0

        # 3. Saving friendly groups in atari
        for grp, libs in my_groups:
            if len(libs) == 1 and (r, c) in libs:
                if my_libs >= 2 or cap_count > 0:
                    score += 120.0 + len(grp) * 25.0

        # 4. Attacking opponent groups in atari
        for grp, libs in opp_groups:
            if len(libs) == 1 and (r, c) in libs:
                score += 140.0 + len(grp) * 30.0
            elif len(libs) == 2 and (r, c) in libs:
                score += 35.0 + len(grp) * 10.0

        # 5. Strategic positioning and board control
        line_r = min(r, BOARD_SIZE - r + 1)
        line_c = min(c, BOARD_SIZE - c + 1)
        min_line = min(line_r, line_c)

        if total_stones < 25:
            # Early game: strong preference for 3rd and 4th lines
            if min_line == 4:
                score += 40.0
            elif min_line == 3:
                score += 35.0
            elif min_line == 2:
                score -= 15.0
            elif min_line == 1:
                score -= 80.0
        else:
            if min_line == 1 and cap_count == 0:
                score -= 30.0
            elif min_line in (3, 4):
                score += 10.0

        # 6. Local connectivity and eye formation
        adj = get_adj(r, c)
        friendly_adj = sum(1 for nr, nc in adj if board.grid.get((nr, nc)) == 1)
        empty_adj = sum(1 for nr, nc in adj if (nr, nc) not in board.grid)
        score += friendly_adj * 8.0 + empty_adj * 4.0

        # Small random noise to break ties naturally
        score += random.uniform(0.0, 0.5)

        if score > best_score:
            best_score = score
            best_move = (r, c)

    memory['history'] = history

    if best_move is None or best_score < -200:
        # Fallback: scan for any legal move before passing
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                if (r, c) not in board.grid:
                    is_legal, _, libs = board.simulate_move(r, c, 1)
                    if is_legal and libs >= 2:
                        return (r, c), memory
        return (0, 0), memory

    return best_move, memory
