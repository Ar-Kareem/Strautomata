
import time
import random
from functools import lru_cache

import numpy as np


def policy(horizontal: np.ndarray,
           vertical: np.ndarray,
           capture: np.ndarray) -> str:
    start_time = time.perf_counter()
    search_deadline = start_time + 0.68
    rollout_deadline = start_time + 0.90

    # Edge numbering:
    #   0..19  : horizontal, index = row * 4 + col
    #   20..39 : vertical,   index = 20 + row * 5 + col
    edge_to_move = []
    for r in range(5):
        for c in range(4):
            edge_to_move.append((r, c, "H"))
    for r in range(4):
        for c in range(5):
            edge_to_move.append((r, c, "V"))

    box_masks = []
    box_rc = []
    edge_boxes = [[] for _ in range(40)]

    for r in range(4):
        for c in range(4):
            top = r * 4 + c
            bottom = (r + 1) * 4 + c
            left = 20 + r * 5 + c
            right = 20 + r * 5 + c + 1
            bm = (1 << top) | (1 << bottom) | (1 << left) | (1 << right)
            b = len(box_masks)
            box_masks.append(bm)
            box_rc.append((r, c))
            for e in (top, bottom, left, right):
                edge_boxes[e].append(b)

    # Claimed boxes are no longer relevant to future scoring.
    active_box = []
    for b, (r, c) in enumerate(box_rc):
        active_box.append(capture[r, c] == 0)

    mask = 0
    for e, (r, c, d) in enumerate(edge_to_move):
        occupied = horizontal[r, c] != 0 if d == "H" else vertical[r, c] != 0
        if occupied:
            mask |= 1 << e

    full_edge_mask = (1 << 40) - 1

    def legal_edges(m):
        empty = full_edge_mask ^ (m & full_edge_mask)
        result = []
        while empty:
            bit = empty & -empty
            result.append(bit.bit_length() - 1)
            empty ^= bit
        return result

    root_legal = legal_edges(mask)

    def format_move(e):
        r, c, d = edge_to_move[e]
        return f"{r},{c},{d}"

    # Normally policy is not called after the last physical edge.
    # The padding scan provides a legal-array fallback for unusual harnesses.
    if not root_legal:
        for r in range(5):
            for c in range(5):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
        for r in range(5):
            for c in range(5):
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
        return "0,0,H"

    def incomplete_boxes(m):
        return [
            b for b, bm in enumerate(box_masks)
            if active_box[b] and (m & bm) != bm
        ]

    def incomplete_count(m):
        n = 0
        for b, bm in enumerate(box_masks):
            if active_box[b] and (m & bm) != bm:
                n += 1
        return n

    def missing_count(m, b):
        return (box_masks[b] & ~m).bit_count()

    def capture_count(m, e):
        bit = 1 << e
        if m & bit:
            return -1
        nm = m | bit
        total = 0
        for b in edge_boxes[e]:
            bm = box_masks[b]
            if active_box[b] and (m & bm) != bm and (nm & bm) == bm:
                total += 1
        return total

    def classify_moves(m):
        captures = []
        safe = []
        dangerous = []

        for e in legal_edges(m):
            k = capture_count(m, e)
            if k:
                captures.append(e)
                continue

            is_safe = True
            for b in edge_boxes[e]:
                bm = box_masks[b]
                if not active_box[b] or (m & bm) == bm:
                    continue
                # A box with two missing sides becomes a three-sided box.
                if missing_count(m, b) <= 2:
                    is_safe = False
                    break

            if is_safe:
                safe.append(e)
            else:
                dangerous.append(e)

        return captures, safe, dangerous

    # Internal undrawn edges connecting neighboring boxes.
    neighbor_links = [[] for _ in range(16)]
    for r in range(4):
        for c in range(4):
            b = r * 4 + c
            if c < 3:
                e = 20 + r * 5 + c + 1
                neighbor_links[b].append((b + 1, e))
            if c > 0:
                e = 20 + r * 5 + c
                neighbor_links[b].append((b - 1, e))
            if r < 3:
                e = (r + 1) * 4 + c
                neighbor_links[b].append((b + 4, e))
            if r > 0:
                e = r * 4 + c
                neighbor_links[b].append((b - 4, e))

    def loony_components(m):
        """
        Return components when every incomplete box has exactly two missing
        sides. Each returned item is (size, handout, boxes, opening_edges):
          handout = 2 for a chain and 4 for a loop.
        Return None if this is not a pure unopened chain/loop position.
        """
        nodes = incomplete_boxes(m)
        if not nodes:
            return []

        node_set = set(nodes)
        for b in nodes:
            if missing_count(m, b) != 2:
                return None

        seen = set()
        components = []

        for first in nodes:
            if first in seen:
                continue

            stack = [first]
            seen.add(first)
            comp = []

            while stack:
                b = stack.pop()
                comp.append(b)
                for nb, e in neighbor_links[b]:
                    if nb in node_set and not (m & (1 << e)) and nb not in seen:
                        seen.add(nb)
                        stack.append(nb)

            comp_set = set(comp)
            boundary_openings = []
            all_openings = set()

            for b in comp:
                bm = box_masks[b]
                missing = bm & ~m
                while missing:
                    bit = missing & -missing
                    e = bit.bit_length() - 1
                    all_openings.add(e)
                    adjacent_in_comp = sum(1 for x in edge_boxes[e] if x in comp_set)
                    if adjacent_in_comp == 1 and len(edge_boxes[e]) == 1:
                        boundary_openings.append(e)
                    missing ^= bit

            # A path component has boundary endpoints; a cycle does not.
            if boundary_openings:
                handout = 2
                openings = boundary_openings
            else:
                handout = 4
                openings = list(all_openings)

            components.append((len(comp), handout, tuple(comp), tuple(openings)))

        return components

    @lru_cache(maxsize=None)
    def component_value(component_key):
        """
        Exact future score difference for the player forced to open one of
        these chain/loop components.
        component_key consists of sorted (length, handout) pairs.
        """
        if not component_key:
            return 0

        best = -100
        used = set()

        for i, item in enumerate(component_key):
            if item in used:
                continue
            used.add(item)

            n, handout = item
            rest = component_key[:i] + component_key[i + 1:]
            future = component_value(rest)

            # Controller takes every box, then must open the remaining game.
            take_all = -n - future
            controller_choices = [take_all]

            # Hard-hearted handout: two boxes in a long chain or four in a loop.
            if (handout == 2 and n >= 3) or (handout == 4 and n >= 4):
                hard_handout = 2 * handout - n + future
                controller_choices.append(hard_handout)

            # The opponent/controller chooses the result worst for the opener.
            result = min(controller_choices)
            if result > best:
                best = result

        return best

    def pure_loony_value(m):
        comps = loony_components(m)
        if comps is None:
            return None
        key = tuple(sorted((n, h) for n, h, _, _ in comps))
        return component_value(key)

    def pure_loony_move(m):
        comps = loony_components(m)
        if not comps:
            return None

        best_value = -100
        best_comp = None

        for i, comp in enumerate(comps):
            n, handout, _, openings = comp
            rest = comps[:i] + comps[i + 1:]
            key = tuple(sorted((x[0], x[1]) for x in rest))
            future = component_value(key)

            take_all = -n - future
            outcomes = [take_all]
            if (handout == 2 and n >= 3) or (handout == 4 and n >= 4):
                outcomes.append(2 * handout - n + future)

            value = min(outcomes)
            if value > best_value and openings:
                best_value = value
                best_comp = comp

        if best_comp is None:
            return None
        return best_comp[3][0]

    # Pure unopened chain and loop positions can be solved directly.
    loony_root = pure_loony_move(mask)
    if loony_root is not None:
        return format_move(loony_root)

    class SearchTimeout(Exception):
        pass

    transposition = {}
    node_counter = [0]

    def ordered_moves(m):
        caps, safe, danger = classify_moves(m)

        caps.sort(key=lambda e: capture_count(m, e), reverse=True)

        # Prefer safe moves affecting boxes with many missing sides.
        safe.sort(
            key=lambda e: sum(
                missing_count(m, b)
                for b in edge_boxes[e]
                if active_box[b] and (m & box_masks[b]) != box_masks[b]
            ),
            reverse=True
        )

        # Dangerous moves that expose fewer adjacent boxes are searched first.
        danger.sort(
            key=lambda e: sum(
                1 for b in edge_boxes[e]
                if active_box[b] and (m & box_masks[b]) != box_masks[b]
            )
        )
        return caps + safe + danger

    def solve(m, alpha=-17, beta=17):
        node_counter[0] += 1
        if (node_counter[0] & 511) == 0 and time.perf_counter() >= search_deadline:
            raise SearchTimeout

        if m == full_edge_mask or incomplete_count(m) == 0:
            return 0

        lv = pure_loony_value(m)
        if lv is not None:
            return lv

        original_alpha = alpha
        original_beta = beta

        entry = transposition.get(m)
        if entry is not None:
            value, flag = entry
            if flag == 0:
                return value
            if flag == 1:  # lower bound
                alpha = max(alpha, value)
            else:          # upper bound
                beta = min(beta, value)
            if alpha >= beta:
                return value

        best = -100

        for e in ordered_moves(m):
            k = capture_count(m, e)
            nm = m | (1 << e)

            if k:
                value = k + solve(nm, alpha - k, beta - k)
            else:
                value = -solve(nm, -beta, -alpha)

            if value > best:
                best = value
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        if best <= original_alpha:
            flag = 2  # upper bound
        elif best >= original_beta:
            flag = 1  # lower bound
        else:
            flag = 0  # exact
        transposition[m] = (best, flag)
        return best

    def exact_best_move(m, candidates):
        best_move = candidates[0]
        best_value = -100
        alpha = -17

        for e in ordered_moves(m):
            if e not in candidate_set:
                continue
            if time.perf_counter() >= search_deadline:
                raise SearchTimeout

            k = capture_count(m, e)
            nm = m | (1 << e)

            if k:
                value = k + solve(nm, alpha - k, 17 - k)
            else:
                value = -solve(nm, -17, -alpha)

            if value > best_value:
                best_value = value
                best_move = e
            if value > alpha:
                alpha = value

        return best_move

    captures_now, safe_now, dangerous_now = classify_moves(mask)

    # Search tactical positions, capture sequences, and late games exactly.
    should_search = (
        len(root_legal) <= 19 or
        bool(captures_now) or
        not safe_now
    )

    candidate_set = set(root_legal)
    if should_search:
        try:
            move = exact_best_move(mask, root_legal)
            return format_move(move)
        except SearchTimeout:
            pass

    def vulnerable_component_size(m, seed_boxes):
        """
        Estimate the number of boxes in the chain-like region reached from
        seed_boxes. Boxes with more than two missing sides stop the region.
        """
        stack = []
        seen = set()

        for b in seed_boxes:
            if (active_box[b] and
                    (m & box_masks[b]) != box_masks[b] and
                    missing_count(m, b) <= 2):
                stack.append(b)
                seen.add(b)

        while stack:
            b = stack.pop()
            for nb, e in neighbor_links[b]:
                if m & (1 << e):
                    continue
                if nb in seen or not active_box[nb]:
                    continue
                if (m & box_masks[nb]) == box_masks[nb]:
                    continue
                if missing_count(m, nb) <= 2:
                    seen.add(nb)
                    stack.append(nb)

        return len(seen)

    def dangerous_risk(m, e):
        nm = m | (1 << e)
        seeds = []
        for b in edge_boxes[e]:
            if active_box[b] and (nm & box_masks[b]) != box_masks[b]:
                if missing_count(nm, b) <= 1:
                    seeds.append(b)
        size = vulnerable_component_size(nm, seeds)
        return size if size else 99

    def find_handout(m):
        """
        Look for a double-cross move which does not score immediately but
        offers a two-box capture while preserving another component.
        """
        current_capture_boxes = []
        for b, bm in enumerate(box_masks):
            if active_box[b] and (m & bm) != bm and missing_count(m, b) == 1:
                current_capture_boxes.append(b)

        if not current_capture_boxes:
            return None

        current_region = vulnerable_component_size(m, current_capture_boxes)
        if incomplete_count(m) <= current_region:
            return None

        best = None
        best_offer = 0

        for e in legal_edges(m):
            if capture_count(m, e) != 0:
                continue
            nm = m | (1 << e)

            offered = 0
            for f in legal_edges(nm):
                offered = max(offered, capture_count(nm, f))

            if offered >= 2 and offered > best_offer:
                best_offer = offered
                best = e

        return best

    # Strong tactical fallback after an interrupted search.
    if captures_now:
        handout = find_handout(mask)
        if handout is not None:
            return format_move(handout)
        best_capture = max(captures_now, key=lambda e: capture_count(mask, e))
        return format_move(best_capture)

    # While safe moves exist, playing a dangerous edge is normally dominated.
    root_candidates = safe_now if safe_now else dangerous_now
    if not root_candidates:
        root_candidates = root_legal

    rng_seed = (
        (mask ^ (mask >> 17) ^ (mask >> 31) ^
         sum((b + 1) * int(active_box[b]) for b in range(16)))
        & 0xFFFFFFFF
    )
    rng = random.Random(rng_seed)

    def rollout_choose(m):
        caps, safe, danger = classify_moves(m)

        if caps:
            handout = find_handout(m)
            if handout is not None and rng.random() < 0.82:
                return handout
            max_capture = max(capture_count(m, e) for e in caps)
            options = [e for e in caps if capture_count(m, e) == max_capture]
            return options[rng.randrange(len(options))]

        if safe:
            # Mostly random safe play, biased toward boxes with many open sides.
            if rng.random() < 0.65:
                qualities = []
                best_q = -1
                for e in safe:
                    q = sum(
                        missing_count(m, b)
                        for b in edge_boxes[e]
                        if active_box[b] and
                        (m & box_masks[b]) != box_masks[b]
                    )
                    if q > best_q:
                        best_q = q
                        qualities = [e]
                    elif q == best_q:
                        qualities.append(e)
                return qualities[rng.randrange(len(qualities))]
            return safe[rng.randrange(len(safe))]

        if danger:
            risks = [(dangerous_risk(m, e), e) for e in danger]
            minimum = min(x[0] for x in risks)
            options = [e for risk, e in risks if risk == minimum]
            return options[rng.randrange(len(options))]

        legal = legal_edges(m)
        return legal[rng.randrange(len(legal))] if legal else None

    def rollout(m, current_player, score):
        # current_player is 0 for the root player and 1 for the opponent.
        for _ in range(42):
            if incomplete_count(m) == 0:
                break

            lv = pure_loony_value(m)
            if lv is not None:
                score += lv if current_player == 0 else -lv
                break

            e = rollout_choose(m)
            if e is None:
                break

            k = capture_count(m, e)
            m |= 1 << e

            if k:
                score += k if current_player == 0 else -k
            else:
                current_player ^= 1

        return score

    scores = {e: 0.0 for e in root_candidates}
    counts = {e: 0 for e in root_candidates}

    # Give every candidate several samples before allocating extra rollouts.
    minimum_rounds = 4
    for _ in range(minimum_rounds):
        for e in root_candidates:
            k = capture_count(mask, e)
            nm = mask | (1 << e)
            initial_score = k
            next_player = 0 if k else 1
            value = rollout(nm, next_player, initial_score)
            scores[e] += value
            counts[e] += 1

    index = 0
    while time.perf_counter() < rollout_deadline:
        e = root_candidates[index % len(root_candidates)]
        index += 1

        k = capture_count(mask, e)
        nm = mask | (1 << e)
        initial_score = k
        next_player = 0 if k else 1
        value = rollout(nm, next_player, initial_score)

        scores[e] += value
        counts[e] += 1

    def opening_quality(e):
        q = 0
        for b in edge_boxes[e]:
            if active_box[b] and (mask & box_masks[b]) != box_masks[b]:
                q += missing_count(mask, b)
        # Tiny deterministic tie-break; rollout score remains dominant.
        r, c, d = edge_to_move[e]
        center_bias = -abs(r - 2) - abs(c - 2)
        return q * 0.001 + center_bias * 0.00001 + (1 if d == "H" else 0) * 1e-7

    best_move = max(
        root_candidates,
        key=lambda e: scores[e] / max(1, counts[e]) + opening_quality(e)
    )

    return format_move(best_move)
