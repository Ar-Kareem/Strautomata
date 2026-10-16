
import random

def policy(me, opponent, memory):
    BOARD_SIZE = 19
    NSQUARES = 361
    FULL = (1 << NSQUARES) - 1

    # ------------------------------------------------------------------
    # Initialise precomputed data on first call
    # ------------------------------------------------------------------
    if not memory:
        memory['init'] = True

        # neighbour list for each index
        neighbors = []
        for i in range(NSQUARES):
            r, c = divmod(i, BOARD_SIZE)
            nb = []
            if r > 0:
                nb.append(i - BOARD_SIZE)
            if r < BOARD_SIZE - 1:
                nb.append(i + BOARD_SIZE)
            if c > 0:
                nb.append(i - 1)
            if c < BOARD_SIZE - 1:
                nb.append(i + 1)
            neighbors.append(nb)
        memory['neighbors'] = neighbors

        # bit masks for each index
        bit_masks = [1 << i for i in range(NSQUARES)]
        memory['bit_masks'] = bit_masks

        # star points (4-4, 4-10, 4-16, 10-4, 10-10, 10-16, 16-4, 16-10, 16-16)
        star_coords = [(4, 4), (4, 10), (4, 16), (10, 4), (10, 10),
                       (10, 16), (16, 4), (16, 10), (16, 16)]
        star_indices = [(r - 1) * BOARD_SIZE + (c - 1) for r, c in star_coords]
        memory['star_indices'] = star_indices

        # points within Manhattan distance ≤ 2 (for local responses)
        radius2 = {}
        for i in range(NSQUARES):
            r1, c1 = divmod(i, BOARD_SIZE)
            lst = []
            for j in range(NSQUARES):
                if i == j:
                    continue
                r2, c2 = divmod(j, BOARD_SIZE)
                if abs(r1 - r2) + abs(c1 - c2) <= 2:
                    lst.append(j)
            radius2[i] = lst
        memory['radius2'] = radius2

        # random generator (deterministic seed for reproducibility)
        memory['rng'] = random.Random(42)

        # board after our previous move (for ko)
        memory['last_my_board_my'] = None
        memory['last_my_board_opp'] = None
        memory['move_count'] = 0
    else:
        neighbors = memory['neighbors']
        bit_masks = memory['bit_masks']
        star_indices = memory['star_indices']
        radius2 = memory['radius2']
        rng = memory['rng']

    last_my_board_my = memory.get('last_my_board_my')
    last_my_board_opp = memory.get('last_my_board_opp')
    move_count = memory.get('move_count', 0)

    # ------------------------------------------------------------------
    # Helper functions (using closures over the variables above)
    # ------------------------------------------------------------------
    def list_to_bb(stone_list):
        bb = 0
        for r, c in stone_list:
            idx = (r - 1) * BOARD_SIZE + (c - 1)
            bb |= bit_masks[idx]
        return bb

    def find_group_with_liberties(own_bb, other_bb, start_idx):
        """BFS returning (set of stones in group, set of its liberties)."""
        stack = [start_idx]
        visited = set()
        group = set()
        liberties = set()
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            group.add(cur)
            for nbr in neighbors[cur]:
                if (own_bb >> nbr) & 1:
                    if nbr not in visited:
                        stack.append(nbr)
                elif (other_bb >> nbr) & 1:
                    continue
                else:
                    liberties.add(nbr)
        return group, liberties

    def compute_groups_with_liberties(own_bb, other_bb):
        """List of (group_set, liberty_set) for all groups of own_bb."""
        visited_mask = 0
        groups = []
        for i in range(NSQUARES):
            if ((own_bb >> i) & 1) and not ((visited_mask >> i) & 1):
                group, libs = find_group_with_liberties(own_bb, other_bb, i)
                for idx in group:
                    visited_mask |= bit_masks[idx]
                groups.append((group, libs))
        return groups

    def do_move(own_bb, other_bb, move_idx, forbid_own=None, forbid_other=None):
        """Simulate a move for the player with stones in own_bb.
        Returns (legal, new_own_bb, new_other_bb)."""
        # occupied?
        if ((own_bb | other_bb) >> move_idx) & 1:
            return False, None, None

        new_own = own_bb | bit_masks[move_idx]
        new_other = other_bb

        # find opponent groups to capture
        opp_stone_neighbors = [nbr for nbr in neighbors[move_idx]
                               if (new_other >> nbr) & 1]
        processed = set()
        captured_groups = []
        for nbr in opp_stone_neighbors:
            if nbr in processed:
                continue
            group, libs = find_group_with_liberties(new_other, new_own, nbr)
            if not libs:          # no liberties -> capture
                captured_groups.append(group)
            processed.update(group)

        # remove captured groups
        for group in captured_groups:
            mask = 0
            for idx in group:
                mask |= bit_masks[idx]
            new_other &= ~mask

        # suicide check
        own_group, own_libs = find_group_with_liberties(new_own, new_other,
                                                        move_idx)
        if not own_libs:
            return False, None, None

        # ko check
        if forbid_own is not None and forbid_other is not None:
            if new_own == forbid_own and new_other == forbid_other:
                return False, None, None

        return True, new_own, new_other

    def evaluate_board(my_bb, opp_bb):
        """Return a float score (positive is good for me)."""
        stone_diff = my_bb.bit_count() - opp_bb.bit_count()
        total = my_bb.bit_count() + opp_bb.bit_count()
        EARLY_THRESH = 30
        area = stone_diff

        if total < EARLY_THRESH:          # early game – Voronoi
            my_coords = [(i // BOARD_SIZE, i % BOARD_SIZE)
                         for i in range(NSQUARES) if (my_bb >> i) & 1]
            opp_coords = [(i // BOARD_SIZE, i % BOARD_SIZE)
                          for i in range(NSQUARES) if (opp_bb >> i) & 1]
            for i in range(NSQUARES):
                if (my_bb >> i) & 1 or (opp_bb >> i) & 1:
                    continue
                r, c = divmod(i, BOARD_SIZE)
                if my_coords:
                    d_me = min(abs(r - mr) + abs(c - mc)
                               for mr, mc in my_coords)
                else:
                    d_me = 1000
                if opp_coords:
                    d_opp = min(abs(r - or_) + abs(c - oc)
                                for or_, oc in opp_coords)
                else:
                    d_opp = 1000
                if d_me < d_opp:
                    area += 1
                elif d_opp < d_me:
                    area -= 1
        else:                             # mid/late game – region territory
            visited = [False] * NSQUARES
            for i in range(NSQUARES):
                if (my_bb >> i) & 1 or (opp_bb >> i) & 1 or visited[i]:
                    continue
                stack = [i]
                region = []
                border_me = False
                border_opp = False
                while stack:
                    cur = stack.pop()
                    if visited[cur]:
                        continue
                    visited[cur] = True
                    region.append(cur)
                    for nbr in neighbors[cur]:
                        if (my_bb >> nbr) & 1:
                            border_me = True
                        elif (opp_bb >> nbr) & 1:
                            border_opp = True
                        else:
                            if not visited[nbr]:
                                stack.append(nbr)
                if border_me and not border_opp:
                    area += len(region)
                elif border_opp and not border_me:
                    area -= len(region)

        # atari bonus/penalty
        ATARI_WEIGHT = 2.0
        bonus = 0.0
        my_groups = compute_groups_with_liberties(my_bb, opp_bb)
       