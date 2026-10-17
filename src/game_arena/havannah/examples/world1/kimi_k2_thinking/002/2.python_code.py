
import random

BOARD_SIZE = 15
# six corner cells of a 15‑cell‑side Havannah board (side length = 8)
CORNERS = {(0, 0), (0, 7), (7, 0), (7, 14), (14, 0), (14, 7)}


def neighbours(r, c, valid):
    """
    Yield all valid neighbours of (r,c) according to the odd‑q offset
    coordinate system.  The six neighbour offsets depend on column parity.
    """
    if c % 2 == 0:          # even column
        offs = [(-1, 0), (1, 0), (0, -1), (0, 1), (1, -1), (1, 1)]
    else:                    # odd column
        offs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1)]

    for dr, dc in offs:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and valid[nr][nc]:
            yield (nr, nc)


def side_labels(r, c, valid):
    """
    Return the set of neighbour‑direction indices that are missing
    because they lie outside the board or are masked out.
    Corner cells are not considered edges, so they return an empty set.
    """
    if (r, c) in CORNERS:
        return set()
    if c % 2 == 0:
        offs = [(-1, 0), (1, 0), (0, -1), (0, 1), (1, -1), (1, 1)]
    else:
        offs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1)]

    labels = set()
    for i, (dr, dc) in enumerate(offs):
        nr, nc = r + dr, c + dc
        if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE) or not valid[nr][nc]:
            labels.add(i)
    return labels


def is_bridge(stones, valid):
    """
    A bridge exists if the set *stones* contains a path that connects two
    different corners of the board.
    """
    # list of corners owned by the player
    corners = [p for p in CORNERS if p in stones]
    if len(corners) < 2:
        return False

    # simple DFS/BFS from the first corner
    stack = [corners[0]]
    visited = set()
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)

        # reached another corner -> bridge completed
        if node != corners[0] and node in CORNERS:
            return True

        for nb in neighbours(node[0], node[1], valid):
            if nb in stones and nb not in visited:
                stack.append(nb)

    return False


def is_fork(stones, valid):
    """
    A fork exists when a connected component of *stones* touches three
    different board edges (edges are identified by missing neighbour
    directions).  Corner cells are ignored for edge detection.
    """
    visited = set()
    for stone in stones:
        if stone in visited:
            continue

        # collect the whole component
        comp = set()
        stack = [stone]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            comp.add(node)

            for nb in neighbours(node[0], node[1], valid):
                if nb in stones and nb not in visited:
                    stack.append(nb)

        # union of side labels of the component
        edge_set = set()
        for s in comp:
            edge_set.update(side_labels(s[0], s[1], valid))

        if len(edge_set) >= 3:
            return True

    return False


def evaluate(move, me_set, opp_set, valid):
    """
    Heuristic score for a candidate move.  Higher is better.
    """
    r, c = move
    own_adj = 0
    opp_adj = 0
    for nb in neighbours(r, c, valid):
        if nb in me_set:
            own_adj += 1
        elif nb in opp_set:
            opp_adj += 1

    score = 5 * own_adj - 2 * opp_adj

    # reward being on an edge (more missing neighbour directions)
    lbl = side_labels(r, c, valid)
    score += 3 * len(lbl)

    # bonus for being next to a corner (helps building a bridge)
    for nb in neighbours(r, c, valid):
        if nb in CORNERS:
            score += 20

    # tiny random noise to break ties
    score += random.random() * 0.1
    return score


def policy(me, opp, valid_mask):
    """
    Return a legal move for the current player:
      1) win immediately if possible,
      2) block an opponent's immediate win,
      3) otherwise pick the move with the highest heuristic score.
    """
    me_set = set(me)
    opp_set = set(opp)

    # enumerate all legal (empty) cells
    legal = [(r, c) for r in range(BOARD_SIZE)
             for c in range(BOARD_SIZE)
             if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set]

    if not legal:                     # safety, should never happen
        return (0, 0)

    best_move = None
    best_score = -float('inf')
    block_moves = []

    for mv in legal:
        # ----- can we win with this move? -----
        new_me = me_set | {mv}
        if is_bridge(new_me, valid_mask) or is_fork(new_me, valid_mask):
            return mv

        # ----- would opponent win with this move? (i.e. do we have to block?) -----
        new_opp = opp_set | {mv}
        if is_bridge(new_opp, valid_mask) or is_fork(new_opp, valid_mask):
            block_moves.append(mv)
            # keep looking – a win for us is more important than a block
            continue

        # ----- ordinary heuristic evaluation -----
        scr = evaluate(mv, me_set, opp_set, valid_mask)
        if scr > best_score:
            best_score = scr
            best_move = mv

    # If we found any move that blocks an opponent win, play the best among them.
    if block_moves:
        best_block = None
        best_block_score = -float('inf')
        for m in block_moves:
            s = evaluate(m, me_set, opp_set, valid_mask)
            if s > best_block_score:
                best_block_score = s
                best_block = m
        return best_block

    return best_move
