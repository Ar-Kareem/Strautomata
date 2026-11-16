
from itertools import combinations
from typing import List, Any, Dict, Tuple, Set, FrozenSet

def policy(state: List[List[Any]], role: str) -> str:
    """
    Return a legal move for the given role in the Trifecta game.
    The policy performs a full minimax search with alpha‑beta pruning,
    using pre‑computed winning triples based on card attributes.
    """
    # ------------------------------------------------------------------
    # 1. Parse the raw proposition list
    # ------------------------------------------------------------------
    cells: Dict[Tuple[int, int], str] = {}               # (r,c) -> owner
    attrs: Dict[Tuple[int, int], Dict[str, Any]] = {}    # (r,c) -> {attr:val}
    control = None

    for prop in state:
        if not isinstance(prop, (list, tuple)) or len(prop) == 0:
            continue
        tag = prop[0]
        if tag == "cell" and len(prop) == 4:
            r, c, owner = int(prop[1]), int(prop[2]), prop[3]
            cells[(r, c)] = owner
        elif tag == "control" and len(prop) == 2:
            control = prop[1]
        elif len(prop) == 4:
            # Any other 4‑ary proposition is treated as a static attribute
            try:
                r, c, val = int(prop[1]), int(prop[2]), prop[3]
                if (r, c) not in attrs:
                    attrs[(r, c)] = {}
                attrs[(r, c)][tag] = val
            except (ValueError, IndexError):
                pass

    # Ensure every cell is represented (some may be missing from the list)
    for pos in attrs:
        if pos not in cells:
            cells[pos] = "b"
    if len(cells) < 9:          # fill the standard 3×3 grid if still incomplete
        for r in (1, 2, 3):
            for c in (1, 2, 3):
                if (r, c) not in cells:
                    cells[(r, c)] = "b"

    positions = sorted(cells.keys())          # fixed order for encoding
    opponent = "o" if role == "x" else "x"

    # ------------------------------------------------------------------
    # Fallback: if we have no attribute data, use a simple heuristic
    # ------------------------------------------------------------------
    if not attrs:
        pref = [(2, 2), (1, 1), (1, 3), (3, 1), (3, 3),
                (1, 2), (2, 1), (2, 3), (3, 2)]
        for p in pref:
            if cells.get(p) == "b":
                return f"mark({p[0]},{p[1]})"
        for p in positions:
            if cells[p] == "b":
                return f"mark({p[0]},{p[1]})"
        return "mark(1,1)"

    # ------------------------------------------------------------------
    # 2. Pre‑compute all winning triples (three cells sharing any attribute)
    # ------------------------------------------------------------------
    winning_triples: Set[FrozenSet[Tuple[int, int]]] = set()
    attr_types: Set[str] = set()
    for d in attrs.values():
        attr_types.update(d.keys())

    for atype in attr_types:
        groups: Dict[Any, List[Tuple[int, int]]] = {}
        for pos in positions:
            if pos in attrs and atype in attrs[pos]:
                val = attrs[pos][atype]
                groups.setdefault(val, []).append(pos)
        for grp in groups.values():
            if len(grp) >= 3:
                for triple in combinations(grp, 3):
                    winning_triples.add(frozenset(triple))

    # ------------------------------------------------------------------
    # Helper: test if a player has already formed a winning set
    # ------------------------------------------------------------------
    def has_won(pl: str) -> bool:
        owned = {p for p in positions if cells[p] == pl}
        if len(owned) < 3:
            return False
        for triple in winning_triples:
            if triple.issubset(owned):
                return True
        return False

    # ------------------------------------------------------------------
    # 3. Immediate win check
    # ------------------------------------------------------------------
    free = [p for p in positions if cells[p] == "b"]
    for pos in free:
        cells[pos] = role
        if has_won(role):
            return f"mark({pos[0]},{pos[1]})"
        cells[pos] = "b"

    # ------------------------------------------------------------------
    # 4. Minimax search with alpha‑beta and memoisation
    # ------------------------------------------------------------------
    def encode() -> str:
        """String encoding of the current board (b/x/o for each position)."""
        return "".join(cells[p] for p in positions)

    memo: Dict[Tuple[str, str], int] = {}
    INF = 10

    def search(cur_player: str, alpha: int, beta: int) -> int:
        """Return game value from this state: +1 win for role, -1 loss, 0 draw."""
        # Terminal draw (no free cells)
        free_local = [p for p in positions if cells[p] == "b"]
        if not free_local:
            return 0

        key = (encode(), cur_player)
        if key in memo:
            return memo[key]

        if cur_player == role:
            # Maximizing
            best = -INF
            for p in free_local:
                cells[p] = cur_player
                if has_won(cur_player):
                    val = 1
                else:
                    nxt = "o" if cur_player == "x" else "x"
                    val = search(nxt, alpha, beta)
                cells[p] = "b"

                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            memo[key] = best
            return best
        else:
            # Minimizing
            best = INF
            for p in free_local:
                cells[p] = cur_player
                if has_won(cur_player):
                    val = -1
                else:
                    nxt = "o" if cur_player == "x" else "x"
                    val = search(nxt, alpha, beta)
                cells[p] = "b"

                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if beta <= alpha:
                    break
            memo[key] = best
            return best

    # ------------------------------------------------------------------
    # 5. Choose the best move
    # ------------------------------------------------------------------
    best_move = None
    best_score = -INF
    for pos in free:
        cells[pos] = role
        if has_won(role):
            score = 1
        else:
            score = search(opponent, -INF, INF)
        cells[pos] = "b"

        if score > best_score:
            best_score = score
            best_move = pos
            if best_score == 1:          # found a forced win
                break

    if best_move is None:
        best_move = free[0]

    return f"mark({best_move[0]},{best_move[1]})"
