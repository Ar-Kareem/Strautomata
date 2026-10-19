
from typing import List, Tuple

# ---------- board utilities ----------

def neighbor_coords(r: int, c: int):
    """Return the six neighbours of (r,c) in the 15x15 Havannah offset grid."""
    ns = [(r - 1, c), (r + 1, c)]
    if r % 2 == 0:
        ns += [(r - 1, c - 1), (r, c - 1), (r - 1, c + 1), (r, c + 1)]
    else:
        ns += [(r, c - 1), (r + 1, c - 1), (r, c + 1), (r + 1, c + 1)]
    return ns


def bits_of(mask: int):
    res = []
    while mask:
        lb = mask & -mask
        res.append(lb)
        mask ^= lb
    return res


def bit_index(lb: int) -> int:
    return lb.bit_length() - 1


class BoardInfo:
    def __init__(self, valid_mask):
        self.size = len(valid_mask)
        self.n_cells = self.size * self.size
        self.valid_cells = []
        self.cell_index = [[-1] * self.size for _ in range(self.size)]

        for r in range(self.size):
            for c in range(self.size):
                if valid_mask[r][c]:
                    idx = len(self.valid_cells)
                    self.valid_cells.append((r, c))
                    self.cell_index[r][c] = idx

        self.num_valid = len(self.valid_cells)
        self.valid_mask = 0
        for i in range(self.num_valid):
            self.valid_mask |= 1 << i

        self.neighbor_masks = [0] * self.num_valid
        self.degree = [0] * self.num_valid
        for i, (r, c) in enumerate(self.valid_cells):
            mask = 0
            for nr, nc in neighbor_coords(r, c):
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    j = self.cell_index[nr][nc]
                    if j != -1:
                        mask |= 1 << j
            self.neighbor_masks[i] = mask
            self.degree[i] = mask.bit_count()

        self.boundary_mask = 0
        boundary_cells = []
        for i, d in enumerate(self.degree):
            if d < 6:
                self.boundary_mask |= 1 << i
                boundary_cells.append(i)

        # Corners are the six boundary cells with degree 3.
        corners = [i for i, d in enumerate(self.degree) if d == 3]
        if len(corners) != 6:
            # robust fallback if the exact board shape differs
            min_deg = min(self.degree)
            corners = [i for i, d in enumerate(self.degree) if d == min_deg]
            if len(corners) > 6:
                corners = corners[:6]

        self.corner_mask = 0
        for i in corners:
            self.corner_mask |= 1 << i

        neighbor_list = [bits_of(m) for m in self.neighbor_masks]
        self.edge_masks = trace_sides(corners, boundary_cells, neighbor_list)

        # small static centre bias
        avg_r = sum(r for r, _ in self.valid_cells) / self.num_valid
        avg_c = sum(c for _, c in self.valid_cells) / self.num_valid
        self.center_score = [0] * self.num_valid
        for i, (r, c) in enumerate(self.valid_cells):
            d = abs(r - avg_r) + abs(c - avg_c)
            self.center_score[i] = max(0, 14 - d)

        self.idx_to_cell = self.valid_cells


def trace_sides(corners, boundary_cells, neighbor_list):
    boundary_set = set(boundary_cells)
    corner_set = set(corners)
    edge_masks = [0] * 6

    if len(corners) != 6:
        return edge_masks

    start = corners[0]
    bns = [n for n in neighbor_list[start] if n in boundary_set]
    if len(bns) < 2:
        return edge_masks

    prev = start
    curr = bns[0]
    side = 0
    seen = set()

    for _ in range(1000):
        while curr not in corner_set:
            if curr in seen:
                break
            seen.add(curr)
            edge_masks[side] |= 1 << curr

            nxt = [n for n in neighbor_list[curr] if n in boundary_set and n != prev]
            if len(nxt) != 1:
                if not nxt:
                    break
                choices = [n for n in nxt if n not in seen]
                nxt = [choices[0] if choices else nxt[0]]
            prev, curr = curr, nxt[0]

        if curr == start:
            break

        bns = [n for n in neighbor_list[curr] if n in boundary_set and n != prev]
        if len(bns) != 1:
            if not bns:
                break
            choices = [n for n in bns if n not in seen]
            bns = [choices[0] if choices else bns[0]]
        prev, curr = curr, bns[0]
        side += 1
        if side >= 6:
            break

    return edge_masks


# ---------- bitmask graph helpers ----------

def flood_fill(start_mask: int, allowed_mask: int, info: BoardInfo) -> int:
    visited = 0
    frontier = start_mask & allowed_mask
    while frontier:
        visited |= frontier
        nxt = 0
        f = frontier
        while f:
            lb = f & -f
            idx = bit_index(lb)
            nxt |= info.neighbor_masks[idx]
            f ^= lb
        frontier = nxt & ~visited & allowed_mask
    return visited


def expand(mask: int, info: BoardInfo) -> int:
    nxt = 0
    f = mask
    while f:
        lb = f & -f
        idx = bit_index(lb)
        nxt |= info.neighbor_masks[idx]
        f ^= lb
    return nxt


# ---------- win detection ----------

def has_ring(stone_mask: int, info: BoardInfo) -> bool:
    nonblocked = info.valid_mask & ~stone_mask
    start = info.boundary_mask & nonblocked
    visited = flood_fill(start, nonblocked, info)

    # A non-stone region not touching the boundary is enclosed by stones.
    if nonblocked & ~visited:
        return True

    # If no empty/opponent region is enclosed, a ring can still enclose a
    # friendly stone that has no non-stone neighbour.
    interior = stone_mask & ~info.boundary_mask
    rem = interior
    while rem:
        lb = rem & -rem
        idx = bit_index(lb)
        if info.neighbor_masks[idx] & nonblocked == 0:
            return True
        rem ^= lb

    return False


def check_win(stone_mask: int, info: BoardInfo) -> bool:
    rem = stone_mask
    while rem:
        lb = rem & -rem
        comp = flood_fill(lb, stone_mask, info)
        rem &= ~comp

        # bridge: two corners
        if (comp & info.corner_mask).bit_count() >= 2:
            return True

        # fork: three non-corner edge sides
        sides = 0
        for sm in info.edge_masks:
            if comp & sm:
                sides += 1
                if sides >= 3:
                    return True

    return has_ring(stone_mask, info)


def find_wins(player_mask: int, legal_mask: int, info: BoardInfo,
              stop_after_first: bool = False):
    wins = []
    rem = legal_mask
    while rem:
        lb = rem & -rem
        rem ^= lb
        if check_win(player_mask | lb, info):
            if stop_after_first:
                return [lb]
            wins.append(lb)
    return wins


# ---------- heuristic helpers ----------

def get_comp_data(player_mask: int, empty_mask: int, info: BoardInfo):
    comps = []
    rem = player_mask
    while rem:
        lb = rem & -rem
        comp = flood_fill(lb, player_mask, info)
        rem &= ~comp
        size = comp.bit_count()
        corners = (comp & info.corner_mask).bit_count()
        edges = 0
        for sm in info.edge_masks:
            if comp & sm:
                edges += 1
        adj_count = (expand(comp) & empty_mask).bit_count()
        comps.append({
            'mask': comp,
            'size': size,
            'corners': corners,
            'edges': edges,
            'adj_count': adj_count,
        })
    return comps


def comp_id_map(comps, n_cells: int):
    arr = [-1] * n_cells
    for ci, comp in enumerate(comps):
        rem = comp['mask']
        while rem:
            lb = rem & -rem
            i = bit_index(lb)
            arr[i] = ci
            rem ^= lb
    return arr


def quick_score(bit: int, info: BoardInfo, me_mask: int, opp_mask: int,
                empty_mask: int, my_comps, opp_comps,
                my_comp_id, opp_comp_id) -> float:
    i = bit_index(bit)
    score = 0

    if bit & info.corner_mask:
        score += 150
    for sm in info.edge_masks:
        if bit & sm:
            score += 30
            break
    score += info.center_score[i]

    # My adjacent components
    my_adj = set()
    rem = info.neighbor_masks[i] & me_mask
    while rem:
        lb = rem & -rem
        ci = my_comp_id[bit_index(lb)]
        if ci != -1:
            my_adj.add(ci)
        rem ^= lb

    for ci in my_adj:
        d = my_comps[ci]
        score += 10 + d['size'] * 3 + d['corners'] * 40 + d['edges'] * 20 + d['adj_count'] * 3
        if d['corners'] == 1:
            score += 40
        if d['edges'] == 2:
            score += 50

    if len(my_adj) >= 2:
        score += 60 * (len(my_adj) - 1)

    # Opponent adjacent components (defensive value)
    opp_adj = set()
    rem = info.neighbor_masks[i] & opp_mask
    while rem:
        lb = rem & -rem
        ci = opp_comp_id[bit_index(lb)]
        if ci != -1:
            opp_adj.add(ci)
        rem ^= lb

    for ci in opp_adj:
        d = opp_comps[ci]
        score += 15 + d['corners'] * 50 + d['edges'] * 25
        if d['corners'] == 1:
            score += 30
        if d['edges'] == 2:
            score += 40

    return score


def player_strength(player_mask: int, empty_mask: int, info: BoardInfo) -> float:
    score = 0.0
    rem = player_mask
    while rem:
        lb = rem & -rem
        comp = flood_fill(lb, player_mask, info)
        rem &= ~comp

        size = comp.bit_count()
        corners = (comp & info.corner_mask).bit_count()
        edges = 0
        for sm in info.edge_masks:
            if comp & sm:
                edges += 1
        adj_count = (expand(comp) & empty_mask).bit_count()

        if corners >= 2 or edges >= 3:
            return 100000.0

        score += size * 3 + adj_count * 2
        if corners == 1:
            score += 100 + adj_count * 3
        if edges == 1:
            score += 20 + adj_count * 2
        elif edges == 2:
            score += 80 + adj_count * 5
        if corners >= 1 and edges >= 1:
            score += 50
        if corners == 0 and edges == 0 and size >= 5:
            score += 10

    return score


# ---------- main policy ----------

TOP_K = 20


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], valid_mask) -> Tuple[int, int]:
    info = BoardInfo(valid_mask)

    me_mask = 0
    for r, c in me:
        idx = info.cell_index[r][c]
        if idx != -1:
            me_mask |= 1 << idx

    opp_mask = 0
    for r, c in opp:
        idx = info.cell_index[r][c]
        if idx != -1:
            opp_mask |= 1 << idx

    occupied = me_mask | opp_mask
    legal_mask = info.valid_mask & ~occupied
    if legal_mask == 0:
        # The game is over; this should not be called in a real game.
        return info.valid_cells[0]

    empty_mask = legal_mask

    # component data for quick move ranking
    my_comps = get_comp_data(me_mask, empty_mask, info)
    opp_comps = get_comp_data(opp_mask, empty_mask, info)
    my_comp_id = comp_id_map(my_comps, info.n_cells)
    opp_comp_id = comp_id_map(opp_comps, info.n_cells)

    def qscore(bit):
        return quick_score(bit, info, me_mask, opp_mask, empty_mask,
                           my_comps, opp_comps, my_comp_id, opp_comp_id)

    # 1. Win immediately if possible.
    my_wins = find_wins(me_mask, legal_mask, info)
    if my_wins:
        return info.idx_to_cell[bit_index(my_wins[0])]

    # 2. Block opponent's immediate winning moves.
    opp_wins = find_wins(opp_mask, legal_mask, info)
    if opp_wins:
        best = max(opp_wins, key=qscore)
        return info.idx_to_cell[bit_index(best)]

    # 3. Rank all legal moves by the fast local heuristic.
    legal_bits = bits_of(legal_mask)
    scored = [(qscore(b), b) for b in legal_bits]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:TOP_K]

    best_bit = top[0][1]
    best_val = float('-inf')

    # 4. Evaluate the top candidates with a shallow lookahead.
    for _, bit in top:
        new_me = me_mask | bit
        if check_win(new_me, info):
            return info.idx_to_cell[bit_index(bit)]

        new_empty = empty_mask & ~bit

        # If opponent can win immediately after this move, penalise it.
        opp_w = find_wins(opp_mask, new_empty, info, stop_after_first=True)
        if opp_w:
            val = -1000000 + qscore(bit)
        else:
            my_score = player_strength(new_me, new_empty, info)
            opp_score = player_strength(opp_mask, new_empty, info)
            val = my_score - opp_score

        if val > best_val:
            best_val = val
            best_bit = bit

    # If all top moves lose immediately, try to find any move that avoids it.
    if best_val <= -1000000:
        for bit in legal_bits:
            new_me = me_mask | bit
            if check_win(new_me, info):
                return info.idx_to_cell[bit_index(bit)]
            new_empty = empty_mask & ~bit
            if not find_wins(opp_mask, new_empty, info, stop_after_first=True):
                my_score = player_strength(new_me, new_empty, info)
                opp_score = player_strength(opp_mask, new_empty, info)
                val = my_score - opp_score
                if val > best_val:
                    best_val = val
                    best_bit = bit

    return info.idx_to_cell[bit_index(best_bit)]
