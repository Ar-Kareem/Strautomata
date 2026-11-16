
from collections import deque

# Standard arena embedding for the 15x15 Havannah board:
# neighbors are: (-1,-1), (-1,0), (0,-1), (0,1), (1,0), (1,1)
DIRS = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, 0), (1, 1)]
# Clockwise order for local ring-shape features
RING_DIRS = [(-1, -1), (-1, 0), (0, 1), (1, 1), (1, 0), (0, -1)]

_BOARD_CACHE = {}
INF = 10**9


def _mask_key(valid_mask):
    try:
        return (tuple(valid_mask.shape), valid_mask.tobytes())
    except Exception:
        return tuple(tuple(bool(x) for x in row) for row in valid_mask)


def _first_legal(valid_mask, occupied):
    n = len(valid_mask)
    for r in range(n):
        for c in range(n):
            try:
                ok = bool(valid_mask[r][c])
            except Exception:
                ok = False
            if ok and (r, c) not in occupied:
                return (r, c)
    # Impossible in a normal game, but keep a last-resort fallback.
    for r in range(n):
        for c in range(n):
            try:
                if bool(valid_mask[r][c]):
                    return (r, c)
            except Exception:
                pass
    return (0, 0)


class BoardInfo:
    def __init__(self, valid_mask):
        self.n = len(valid_mask)

        self.cells = []
        self.row_cols = []
        for r in range(self.n):
            cols = []
            for c in range(self.n):
                if bool(valid_mask[r][c]):
                    cols.append(c)
                    self.cells.append((r, c))
            self.row_cols.append(cols)

        self.num_cells = len(self.cells)
        self.cell_set = set(self.cells)

        # Hex graph
        self.neigh = {}
        for r, c in self.cells:
            ns = []
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.n and 0 <= nc < self.n and bool(valid_mask[nr][nc]):
                    ns.append((nr, nc))
            self.neigh[(r, c)] = ns

        # Boundary cells for ring detection
        self.boundary = {cell for cell in self.cells if len(self.neigh[cell]) < 6}

        # Corners / edges from the row intervals (standard Havannah mask)
        starts = [cols[0] for cols in self.row_cols]
        ends = [cols[-1] for cols in self.row_cols]
        self.mid = max(range(self.n), key=lambda r: len(self.row_cols[r]))

        self.corners = [
            (0, starts[0]),
            (0, ends[0]),
            (self.mid, ends[self.mid]),
            (self.n - 1, ends[self.n - 1]),
            (self.n - 1, starts[self.n - 1]),
            (self.mid, starts[self.mid]),
        ]
        self.corner_index = {cell: i for i, cell in enumerate(self.corners)}

        self.edge_cells = [[] for _ in range(6)]
        # top
        for c in range(starts[0] + 1, ends[0]):
            self.edge_cells[0].append((0, c))
        # upper-right
        for r in range(1, self.mid):
            self.edge_cells[1].append((r, ends[r]))
        # lower-right
        for r in range(self.mid + 1, self.n - 1):
            self.edge_cells[2].append((r, ends[r]))
        # bottom
        for c in range(starts[self.n - 1] + 1, ends[self.n - 1]):
            self.edge_cells[3].append((self.n - 1, c))
        # lower-left
        for r in range(self.mid + 1, self.n - 1):
            self.edge_cells[4].append((r, starts[r]))
        # upper-left
        for r in range(1, self.mid):
            self.edge_cells[5].append((r, starts[r]))

        self.edge_of = {}
        for i, cells in enumerate(self.edge_cells):
            for cell in cells:
                self.edge_of[cell] = i

        # Geometric center
        mid_row = self.row_cols[self.mid]
        self.center = (self.mid, mid_row[len(mid_row) // 2])

        self.dist_to_center = self._bfs_dist(self.center)
        self.max_center_dist = max(self.dist_to_center.values()) if self.dist_to_center else 1

    def _bfs_dist(self, start):
        dist = {start: 0}
        dq = deque([start])
        while dq:
            u = dq.popleft()
            du = dist[u]
            for v in self.neigh[u]:
                if v not in dist:
                    dist[v] = du + 1
                    dq.append(v)
        return dist


class CompInfo:
    __slots__ = ("label", "members", "sizes", "corners", "edges")

    def __init__(self):
        self.label = {}
        self.members = []
        self.sizes = []
        self.corners = []
        self.edges = []


def _get_board(valid_mask):
    key = _mask_key(valid_mask)
    board = _BOARD_CACHE.get(key)
    if board is None:
        board = BoardInfo(valid_mask)
        _BOARD_CACHE[key] = board
    return board


def build_comp_info(stones, board):
    stones = set(stones)
    info = CompInfo()
    seen = set()

    for s in stones:
        if s in seen:
            continue
        cid = len(info.members)
        comp = []
        corners = set()
        edges = set()
        dq = deque([s])
        seen.add(s)
        info.label[s] = cid

        while dq:
            u = dq.popleft()
            comp.append(u)

            if u in board.corner_index:
                corners.add(board.corner_index[u])
            eid = board.edge_of.get(u)
            if eid is not None:
                edges.add(eid)

            for v in board.neigh[u]:
                if v in stones and v not in seen:
                    seen.add(v)
                    info.label[v] = cid
                    dq.append(v)

        info.members.append(comp)
        info.sizes.append(len(comp))
        info.corners.append(corners)
        info.edges.append(edges)

    return info


def has_ring(player_stones, board):
    # A ring needs at least 6 stones.
    if len(player_stones) < 6:
        return False

    player_stones = set(player_stones)
    seen = set()
    dq = deque()

    # Flood-fill all non-player cells reachable from the boundary.
    for cell in board.boundary:
        if cell not in player_stones:
            seen.add(cell)
            dq.append(cell)

    while dq:
        u = dq.popleft()
        for v in board.neigh[u]:
            if v not in player_stones and v not in seen:
                seen.add(v)
                dq.append(v)

    # Any non-player cell not reached from the boundary is enclosed.
    for cell in board.cells:
        if cell not in player_stones and cell not in seen:
            return True
    return False


def is_winning_move(player_stones, move, board, comp_info):
    # Bridge / fork can be checked from the merged component metadata.
    adj_comp_ids = set()
    adj_count = 0
    corners = set()
    edges = set()

    for n in board.neigh[move]:
        cid = comp_info.label.get(n)
        if cid is not None:
            adj_count += 1
            adj_comp_ids.add(cid)

    if move in board.corner_index:
        corners.add(board.corner_index[move])
    eid = board.edge_of.get(move)
    if eid is not None:
        edges.add(eid)

    for cid in adj_comp_ids:
        corners |= comp_info.corners[cid]
        edges |= comp_info.edges[cid]

    if len(corners) >= 2:
        return True
    if len(edges) >= 3:
        return True

    # Ring: only worth checking if the move joins at least two friendly neighbors.
    if len(player_stones) + 1 >= 6 and adj_count >= 2:
        new_stones = set(player_stones)
        new_stones.add(move)
        if has_ring(new_stones, board):
            return True

    return False


def count_winning_moves_after(player_stones_after, legal, skip_move, board, comp_info_after, stop_after=2):
    cnt = 0
    for m in legal:
        if m == skip_move:
            continue
        if is_winning_move(player_stones_after, m, board, comp_info_after):
            cnt += 1
            if cnt >= stop_after:
                return cnt
    return cnt


def setup_threat_count(player_stones, move, legal, board):
    new_stones = set(player_stones)
    new_stones.add(move)
    new_info = build_comp_info(new_stones, board)
    return count_winning_moves_after(new_stones, legal, move, board, new_info, stop_after=2)


def zero_one_connection_dist(sources, my_stones_after, opp_stones, board):
    dist = {}
    dq = deque()

    for s in sources:
        if s not in dist:
            dist[s] = 0
            dq.appendleft(s)

    while dq:
        u = dq.popleft()
        du = dist[u]
        for v in board.neigh[u]:
            if v in opp_stones:
                continue
            w = 0 if v in my_stones_after else 1
            nd = du + w
            old = dist.get(v)
            if old is None or nd < old:
                dist[v] = nd
                if w == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)
    return dist


def ring_local_potential(move, my_stones, board):
    r, c = move
    pres = []
    for dr, dc in RING_DIRS:
        pres.append((r + dr, c + dc) in my_stones)

    count = sum(pres)
    adjacent_pairs = sum(1 for i in range(6) if pres[i] and pres[(i + 1) % 6])
    skip_pairs = sum(1 for i in range(6) if pres[i] and pres[(i + 2) % 6])

    return 0.4 * count + adjacent_pairs + 0.5 * skip_pairs


def move_score(me_stones, opp_stones, move, board, my_info, opp_info, total_occupied):
    phase = total_occupied / max(1, board.num_cells)

    adj_my = 0
    adj_opp = 0
    adj_my_ids = set()
    adj_opp_ids = set()

    sources = [move]
    merged_size = 1
    corners = set()
    edges = set()

    for n in board.neigh[move]:
        cid = my_info.label.get(n)
        if cid is not None:
            adj_my += 1
            adj_my_ids.add(cid)
        oid = opp_info.label.get(n)
        if oid is not None:
            adj_opp += 1
            adj_opp_ids.add(oid)

    for cid in adj_my_ids:
        merged_size += my_info.sizes[cid]
        sources.extend(my_info.members[cid])
        corners |= my_info.corners[cid]
        edges |= my_info.edges[cid]

    if move in board.corner_index:
        corners.add(board.corner_index[move])
    eid = board.edge_of.get(move)
    if eid is not None:
        edges.add(eid)

    empty_neighbors = 0
    for n in board.neigh[move]:
        if n not in me_stones and n not in opp_stones:
            empty_neighbors += 1

    score = 0.0

    # Local structure / contact
    score += 12.0 * adj_my
    k = len(adj_my_ids)
    if k >= 2:
        score += 18.0 * k * (k - 1)
    score += 2.0 * merged_size

    score += 5.0 * adj_opp
    score += 4.0 * len(adj_opp_ids)
    score += 1.2 * empty_neighbors

    # Center early
    center_term = (board.max_center_dist - board.dist_to_center.get(move, board.max_center_dist)) / max(1, board.max_center_dist)
    score += (12.0 * (1.0 - phase) + 2.0) * center_term

    # Touching strategic borders matters more later
    score += (4.0 + 8.0 * phase) * len(edges)
    score += (6.0 + 12.0 * phase) * len(corners)

    # Avoid aimless early edge/corner drifting
    if adj_my == 0 and adj_opp == 0 and phase < 0.18:
        if move in board.corner_index:
            score -= 28.0
        elif move in board.edge_of:
            score -= 14.0
        else:
            score -= 4.0

    # Estimate future bridge/fork potential from the new component
    my_after = set(me_stones)
    my_after.add(move)
    dist = zero_one_connection_dist(sources, my_after, opp_stones, board)

    corner_ds = sorted(dist.get(c, INF) for c in board.corners)

    edge_ds = []
    for i in range(6):
        best = INF
        for cell in board.edge_cells[i]:
            d = dist.get(cell)
            if d is not None and d < best:
                best = d
        edge_ds.append(best)
    edge_ds.sort()

    obj = 0.0
    obj += 80.0 / (2.0 + corner_ds[0] + corner_ds[1])
    obj += 65.0 / (3.0 + edge_ds[0] + edge_ds[1] + edge_ds[2])
    obj += 20.0 / (1.0 + corner_ds[0]) + 12.0 / (1.0 + corner_ds[1])
    obj += 14.0 / (1.0 + edge_ds[0]) + 10.0 / (1.0 + edge_ds[1]) + 6.0 / (1.0 + edge_ds[2])
    score += (0.45 + 1.10 * phase) * obj

    # Local ring flavor
    score += 3.5 * ring_local_potential(move, me_stones, board)

    # Tiny deterministic tie-break
    score += 0.001 * ((move[0] * 31 + move[1] * 17 + total_occupied * 13) % 1000)

    return score


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    occupied = set(me) | set(opp)
    fallback = _first_legal(valid_mask, occupied)

    try:
        board = _get_board(valid_mask)
        me_stones = set(me)
        opp_stones = set(opp)

        legal = [cell for cell in board.cells if cell not in occupied]
        if not legal:
            return fallback

        total_occupied = len(me_stones) + len(opp_stones)

        # Fast opening
        if total_occupied == 0 and board.center in legal:
            return board.center

        my_info = build_comp_info(me_stones, board)
        opp_info = build_comp_info(opp_stones, board)

        # Immediate wins
        my_wins = []
        for m in legal:
            if is_winning_move(me_stones, m, board, my_info):
                my_wins.append(m)

        if len(my_wins) == 1:
            return my_wins[0]

        base_cache = {}

        def base(m):
            if m not in base_cache:
                base_cache[m] = move_score(me_stones, opp_stones, m, board, my_info, opp_info, total_occupied)
            return base_cache[m]

        if my_wins:
            move = max(my_wins, key=base)
            return move if move in legal else fallback

        # Immediate opponent wins: block if possible.
        opp_wins = []
        for m in legal:
            if is_winning_move(opp_stones, m, board, opp_info):
                opp_wins.append(m)

        if len(opp_wins) == 1:
            return opp_wins[0]
        elif opp_wins:
            # Probably losing, but occupy the best of their winning cells.
            move = max(opp_wins, key=base)
            return move if move in legal else fallback

        # Full positional scores
        for m in legal:
            base(m)

        # Our setup threats after one move
        my_setup_counts = {}
        my_double = []
        has_my_threat = False
        for m in legal:
            cnt = setup_threat_count(me_stones, m, legal, board)
            my_setup_counts[m] = cnt
            if cnt >= 1:
                has_my_threat = True
            if cnt >= 2:
                my_double.append(m)

        if my_double:
            move = max(my_double, key=base)
            return move if move in legal else fallback

        # Opponent setup threats after one move
        opp_setup_counts = {}
        opp_double = []
        for m in legal:
            cnt = setup_threat_count(opp_stones, m, legal, board)
            opp_setup_counts[m] = cnt
            if cnt >= 2:
                opp_double.append(m)

        # If they have a double-threat setup and we cannot make even a single threat,
        # blocking one of their dangerous setup cells is urgent.
        if opp_double and not has_my_threat:
            move = max(opp_double, key=base)
            return move if move in legal else fallback

        # Final combined score
        best_move = None
        best_score = -10**18
        for m in legal:
            score = base_cache[m]
            score += 140.0 * my_setup_counts[m]
            score += 100.0 * opp_setup_counts[m]
            if opp_setup_counts[m] >= 2:
                score += 80.0
            if score > best_score:
                best_score = score
                best_move = m

        if best_move is not None and best_move in legal:
            return best_move

        return fallback

    except Exception:
        return fallback
