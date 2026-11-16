
import random

BOARD_SIZE = 19
NUM_POS = BOARD_SIZE * BOARD_SIZE
ALL_MASK = (1 << NUM_POS) - 1

# ----- precomputed masks for shift operations -----
MASK_COL_1 = 0
MASK_COL_19 = 0
for i in range(BOARD_SIZE):
    MASK_COL_1 |= 1 << (i * BOARD_SIZE)
    MASK_COL_19 |= 1 << (i * BOARD_SIZE + BOARD_SIZE - 1)

# ----- neighbour list for each point (index 0..360) -----
NEIGHBORS = []
for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        idx = r * BOARD_SIZE + c
        nb = []
        if r > 0: nb.append(idx - BOARD_SIZE)
        if r < BOARD_SIZE - 1: nb.append(idx + BOARD_SIZE)
        if c > 0: nb.append(idx - 1)
        if c < BOARD_SIZE - 1: nb.append(idx + 1)
        NEIGHBORS.append(nb)

# ----- influence potential (Manhattan radius 5) -----
POTENTIAL = [0] * NUM_POS
for r1 in range(BOARD_SIZE):
    for c1 in range(BOARD_SIZE):
        idx1 = r1 * BOARD_SIZE + c1
        total = 0
        for r2 in range(BOARD_SIZE):
            for c2 in range(BOARD_SIZE):
                d = abs(r1 - r2) + abs(c1 - c2)
                if d < 6:
                    total += 6 - d
        POTENTIAL[idx1] = total

# ----- star point bonus (encourages opening moves) -----
STAR_COORDS = [(4,4), (4,10), (4,16), (10,4), (10,16), (16,4), (16,10), (16,16)]
STAR_WEIGHT = 50
STAR_BONUS = [0] * NUM_POS
for idx in range(NUM_POS):
    r = idx // BOARD_SIZE + 1   # row number 1..19
    c = idx % BOARD_SIZE + 1    # col number 1..19
    max_bonus = 0
    for (sr, sc) in STAR_COORDS:
        d = abs(r - sr) + abs(c - sc)
        if d <= 4:
            bonus = (4 - d) * STAR_WEIGHT
            if bonus > max_bonus:
                max_bonus = bonus
    STAR_BONUS[idx] = max_bonus

# ----- bitboard expansion (orthogonal neighbours) -----
def expand(bits):
    east  = ((bits << 1) & ALL_MASK) & ~MASK_COL_1
    west  = ((bits >> 1) & ALL_MASK) & ~MASK_COL_19
    north = (bits >> BOARD_SIZE) & ALL_MASK
    south = (bits << BOARD_SIZE) & ALL_MASK
    return east | west | north | south

# ----- helpers -----
def list_to_mask(stone_list):
    mask = 0
    for (r, c) in stone_list:
        idx = (r-1) * BOARD_SIZE + (c-1)
        mask |= 1 << idx
    return mask

def idx_to_coord(idx):
    r = idx // BOARD_SIZE + 1
    c = idx % BOARD_SIZE + 1
    return (r, c)

def compute_groups(color_mask, empty_mask):
    """return (list of groups, array mapping stone index -> group id)"""
    groups = []
    remaining = color_mask
    group_id = [-1] * NUM_POS
    gid = 0
    while remaining:
        low = remaining & -remaining
        remaining ^= low
        group_mask = low
        while True:
            neighbours = expand(group_mask) & color_mask
            new_mask = group_mask | neighbours
            if new_mask == group_mask:
                break
            group_mask = new_mask
        # remove whole component from remaining
        remaining &= ~group_mask
        # liberties
        libs = expand(group_mask) & empty_mask
        # assign group id and compute total potential of the group
        pot_sum = 0
        mask_tmp = group_mask
        while mask_tmp:
            lowbit = mask_tmp & -mask_tmp
            idx = lowbit.bit_length() - 1
            group_id[idx] = gid
            pot_sum += POTENTIAL[idx]
            mask_tmp ^= lowbit
        groups.append({
            'mask': group_mask,
            'libs': libs,
            'size': group_mask.bit_count(),
            'pot_sum': pot_sum
        })
        gid += 1
    return groups, group_id

# ----- main policy -----
def policy(me, opponent, memory):
    # convert inputs to bitmasks
    my_mask = list_to_mask(me)
    opp_mask = list_to_mask(opponent)
    empty_mask = ALL_MASK ^ (my_mask | opp_mask)

    # ---- recover current ko restriction from opponent's last move ----
    if memory:
        prev_my = memory['prev_my']
        prev_opp = memory['prev_opp']
        opp_move_bits = opp_mask & ~prev_opp          # stone opponent placed
        captured_my_bits = prev_my & ~my_mask        # stones of ours that disappeared
        captured_count = captured_my_bits.bit_count()
        if captured_count == 1:
            ko_point = captured_my_bits.bit_length() - 1   # index of the single captured stone
        else:
            ko_point = None
    else:
        ko_point = None   # first move, no ko

    # ---- compute groups for current board ----
    my_groups, my_group_id = compute_groups(my_mask, empty_mask)
    opp_groups, opp_group_id = compute_groups(opp_mask, empty_mask)

    # ---- constants for scoring ----
    CAPTURE_WEIGHT = 10000
    PRESSURE_WEIGHT = 30
    INFLUENCE_WEIGHT = 2
    SELF_ATARI_PENALTY = 5000
    EXTEND_BONUS = 5

    best_score = -float('inf')
    best_idx = None

    empty = empty_mask
    while empty:
        low = empty & -empty
        idx = low.bit_length() - 1
        empty ^= low

        p_bit = 1 << idx

        # collect adjacent groups and empty neighbours
        own_adj_gids = set()
        opp_adj_gids = set()
        empty_neighbors_mask = 0
        for nb in NEIGHBORS[idx]:
            nb_bit = 1 << nb
            if my_mask & nb_bit:
                gid = my_group_id[nb]
                if gid != -1:
                    own_adj_gids.add(gid)
            elif opp_mask & nb_bit:
                gid = opp_group_id[nb]
                if gid != -1:
                    opp_adj_gids.add(gid)
            else:
                empty_neighbors_mask |= nb_bit

        # ---- capture ----
        capture_size = 0
        capture_contrib = 0
        for gid in opp_adj_gids:
            g = opp_groups[gid]
            if g['libs'] == p_bit:          # only liberty removed -> captured
                capture_size += g['size']
                capture_contrib += g['pot_sum']

        # ---- ko illegal move ----
        if ko_point is not None and idx == ko_point and capture_size == 1:
            continue

        # ---- legality check (suicide) ----
        if capture_size > 0:
            legal = True
        else:
            if empty_neighbors_mask != 0:
                legal = True
            else:
                libs_after = empty_neighbors_mask
                for gid in own_adj_gids:
                    libs_after |= my_groups[gid]['libs']
                libs_after &= ~p_bit
                legal = (libs_after != 0)
        if not legal:
            continue

        # ---- score components ----
        capture_score = CAPTURE_WEIGHT * capture_size

        pressure_score = 0
        for gid in opp_adj_gids:
            g = opp_groups[gid]
            if (p_bit & g['libs']) != 0 and g['libs'].bit_count() > 1:
                pressure_score += PRESSURE_WEIGHT * g['size'] / g['libs'].bit_count()

        influence_score = INFLUENCE_WEIGHT * (POTENTIAL[idx] + capture_contrib)

        star_bonus = STAR_BONUS[idx]

        # self‑atari penalty
        self_atari_penalty = 0
        if capture_size == 0:
            libs_after = empty_neighbors_mask
            for gid in own_adj_gids:
                libs_after |= my_groups[gid]['libs']
            libs_after &= ~p_bit
            if libs_after.bit_count() == 1:
                new_group_size = 1 + sum(my_groups[gid]['size'] for gid in own_adj_gids)
                self_atari_penalty = SELF_ATARI_PENALTY * new_group_size

        extension_bonus = EXTEND_BONUS * len(own_adj_gids)

        total_score = (capture_score + pressure_score + influence_score +
                       star_bonus - self_atari_penalty + extension_bonus +
                       random.random())   # tie‑breaker

        if total_score > best_score:
            best_score = total_score
            best_idx = idx

    # ---- if no legal move (should not happen), pass ----
    if best_idx is None:
        action = (0, 0)
        memory_out = {
            'prev_my': my_mask,
            'prev_opp': opp_mask,
            'ko': None
        }
        return action, memory_out

    # ---- apply chosen move to produce next state ----
    p_bit = 1 << best_idx
    captured_mask = 0
    captured_size = 0
    for g in opp_groups:
        if g['libs'] == p_bit:
            captured_mask |= g['mask']
            captured_size += g['size']
    new_my_mask = my_mask | p_bit
    new_opp_mask = opp_mask & ~captured_mask
    if captured_size == 1:
        ko_idx = captured_mask.bit_length() - 1
    else:
        ko_idx = None

    memory_out = {
        'prev_my': new_my_mask,
        'prev_opp': new_opp_mask,
        'ko': ko_idx
    }
    return idx_to_coord(best_idx), memory_out
