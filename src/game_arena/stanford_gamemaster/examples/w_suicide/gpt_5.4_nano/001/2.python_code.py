
from typing import List, Optional, Tuple

def policy(state: list[list[object]], role: str) -> str:
    # --- Parse board and control ---
    # Board cells are encoded as: ["cell", "r", "c", sym] where sym in {"b","x","o"}
    board = [[None]*4 for _ in range(4)]  # 1..3 used
    for fact in state:
        if isinstance(fact, list) and len(fact) >= 4 and fact[0] == "cell":
            r = int(fact[1])
            c = int(fact[2])
            s = str(fact[3])
            board[r][c] = s  # "b","x","o"
    me = role.strip()
    opp = "o" if me == "x" else "x"

    # Collect legal moves (empty cells)
    moves = [(r,c) for r in (1,2,3) for c in (1,2,3) if board[r][c] == "b"]

    def lines():
        return [
            [(1,1),(1,2),(1,3)],
            [(2,1),(2,2),(2,3)],
            [(3,1),(3,2),(3,3)],
            [(1,1),(2,1),(3,1)],
            [(1,2),(2,2),(3,2)],
            [(1,3),(2,3),(3,3)],
            [(1,1),(2,2),(3,3)],
            [(1,3),(2,2),(3,1)],
        ]

    def is_line_complete(bd, sym, line):
        return all(bd[r][c] == sym for (r,c) in line)

    def my_losing(bd, sym=me):
        # In Suicide: the first player to make 3-in-row of their own marks loses.
        for ln in lines():
            if is_line_complete(bd, sym, ln):
                return True
        return False

    def generate_next_moves(bd):
        return [(r,c) for r in (1,2,3) for c in (1,2,3) if bd[r][c] == "b"]

    # Check if opponent's move would cause opponent to lose (i.e., opponent completes their own line)
    def opp_can_lose_immediately(bd_after_my_move):
        # true if there exists at least one opponent move that makes opponent lose immediately
        for (r,c) in generate_next_moves(bd_after_my_move):
            bd2 = [row[:] for row in bd_after_my_move]
            bd2[r][c] = opp
            if my_losing(bd2, sym=opp):
                return True
        return False

    def opponent_forced_to_lose(bd_after_my_move):
        # If for all opponent legal moves, opponent completes a line immediately,
        # then opponent is forced to lose on their move.
        opp_moves = generate_next_moves(bd_after_my_move)
        if not opp_moves:
            return False
        for (r,c) in opp_moves:
            bd2 = [row[:] for row in bd_after_my_move]
            bd2[r][c] = opp
            if not my_losing(bd2, sym=opp):
                return False
        return True

    def count_my_near_lines(bd):
        # number of lines where I have 2 and one empty (dangerous)
        cnt = 0
        for ln in lines():
            cells = [bd[r][c] for (r,c) in ln]
            if cells.count(me) == 2 and cells.count("b") == 1:
                cnt += 1
        return cnt

    def count_opp_near_lines(bd):
        cnt = 0
        for ln in lines():
            cells = [bd[r][c] for (r,c) in ln]
            if cells.count(opp) == 2 and cells.count("b") == 1:
                cnt += 1
        return cnt

    best_move = moves[0]
    best_score = -10**18

    for (r,c) in moves:
        bd = [row[:] for row in board]
        bd[r][c] = me

        # Immediate loss for me?
        if my_losing(bd, sym=me):
            score = -10**12  # huge penalty
        else:
            score = 0
            # If this move forces opponent to lose immediately, great.
            if opponent_forced_to_lose(bd):
                score += 10**9

            # If opponent can lose immediately on their next move, that's good for us
            # because in Suicide the player who completes their own line loses.
            # So "opponent has a move that causes their own loss" means they may avoid it,
            # but generally it gives us tactical advantage; weight modestly.
            if opp_can_lose_immediately(bd):
                score += 5000

            # Reduce immediate self-danger (avoid creating many "two-in-a-row with empty" lines)
            score -= 200 * count_my_near_lines(bd)

            # Increase pressure: if we create many near-lines for opponent,
            # we might force them into positions where they must complete.
            score += 80 * count_opp_near_lines(bd)

            # Small preference for center/edge to break ties (pure heuristic)
            if (r,c) == (2,2):
                score += 5
            elif r in (1,3) and c in (1,3):
                score += 2

        if score > best_score:
            best_score = score
            best_move = (r,c)

    return f"mark({best_move[0]},{best_move[1]})"
