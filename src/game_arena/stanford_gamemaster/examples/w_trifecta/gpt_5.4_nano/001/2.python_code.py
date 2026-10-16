
import re
from typing import List, Tuple, Dict, Any

def policy(state: list[list[object]], role: str) -> str:
    # Extract cell occupancy: cell row col occupant
    # Observed from examples: ["cell", "1", "2", "b"] for empty, ["cell","1","2","x"] when taken by x, similarly o.
    occ: Dict[Tuple[int,int], str] = {}
    control = None
    for fact in state:
        if not fact:
            continue
        if fact[0] == "control" and len(fact) >= 2:
            control = str(fact[1])
        if fact[0] == "cell" and len(fact) >= 4:
            r = int(fact[1])
            c = int(fact[2])
            occ[(r,c)] = str(fact[3])
    # Determine empty cells
    empty = [(r,c) for r in [1,2,3] for c in [1,2,3] if occ.get((r,c), 'b') == 'b']
    if not empty:
        # fallback (should not happen in legal play)
        return "mark(1,1)"

    opp = "o" if role == "x" else "x"

    # Candidate lines under coordinate-based interpretation
    lines = []
    # rows
    for r in [1,2,3]:
        lines.append([(r,1),(r,2),(r,3)])
    # cols
    for c in [1,2,3]:
        lines.append([(1,c),(2,c),(3,c)])
    # diagonals
    lines.append([(1,1),(2,2),(3,3)])
    lines.append([(1,3),(2,2),(3,1)])

    def score_for_move(player: str, move: Tuple[int,int]) -> int:
        """Heuristic: immediate win if player can have any 3-in-set by the move,
        else count how many lines get closer."""
        r,c = move
        # make hypothetical occupancy
        taken = {k for k,v in occ.items() if v == player}
        taken.add((r,c))

        # immediate win by any line (coordinate-based proxy)
        # (In the true game, 'any of following characteristics' wins; we approximate
        # using coordinate lines, which are always well-defined.)
        for line in lines:
            if all(p in taken for p in line):
                return 10_000

        # otherwise, line progress
        best = 0
        for line in lines:
            in_line = sum(1 for p in line if p in taken)
            if in_line > 0:
                # prefer lines with many own marks and no opponent marks
                if any(p in {k for k,v in occ.items() if v == opp} for p in line):
                    continue
                best = max(best, in_line)
        return best * 100

    def find_immediate_win(player: str) -> Tuple[int,int] | None:
        for mv in empty:
            if score_for_move(player, mv) >= 10_000:
                return mv
        return None

    # Block opponent immediate wins
    win_opp = find_immediate_win(opp)
    if win_opp is not None:
        return f"mark({win_opp[0]},{win_opp[1]})"

    # Take immediate win if available
    win_me = find_immediate_win(role)
    if win_me is not None:
        return f"mark({win_me[0]},{win_me[1]})"

    # Otherwise choose move maximizing (my potential - opponent potential)
    opp_pot = []
    best_mv = None
    best_val = -10**18
    for mv in empty:
        myv = score_for_move(role, mv)
        oppv = score_for_move(opp, mv)
        # opponent potential reduces our value
        val = myv - oppv//2
        if val > best_val:
            best_val = val
            best_mv = mv

    return f"mark({best_mv[0]},{best_mv[1]})"
