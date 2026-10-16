
import time
import numpy as np
from typing import List, Tuple, Optional

# Policy entry point required by the arena.
def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return a move string like "d3" or "pass".
    you and opponent are 8x8 numpy arrays with 0/1 integers.
    """
    # Convert numpy boards to python lists for faster local manipulation
    you_board = [row[:] for row in you.tolist()]
    opp_board = [row[:] for row in opponent.tolist()]

    solver = OthelloSolver(you_board, opp_board, time_limit=0.95)
    move = solver.find_best_move()

    if move is None:
        return "pass"
    r, c = move
    return chr(ord('a') + c) + str(r + 1)


# --- Solver implementation --------------------------------------------------

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),          (0, 1),
              (1, -1),  (1, 0), (1, 1)]

# Positional weights (common heuristic)
POSITION_WEIGHTS = [
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10, -2, -1, -1, -1, -1, -2, 10],
    [5, -2, -1, -1, -1, -1, -2, 5],
    [5, -2, -1, -1, -1, -1, -2, 5],
    [10, -2, -1, -1, -1, -1, -2, 10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100]
]

CORNER_COORDS = [(0,0), (0,7), (7,0), (7,7)]
ADJ_TO_CORNER = [(0,1),(1,0),(1,1),(0,6),(1,7),(1,6),(6,0),(7,1),(6,1),(6,7),(7,6),(6,6)]

INF = 10**9

class OthelloSolver:
    def __init__(self, you: List[List[int]], opp: List[List[int]], time_limit: float = 0.95):
        self.root_you = you
        self.root_opp = opp
        self.start_time = time.time()
        self.time_limit = time_limit
        self.end_time = self.start_time + self.time_limit
        self.tt = {}  # simple transposition table: (you_bb, opp_bb, depth)->score

    def find_best_move(self) -> Optional[Tuple[int,int]]:
        you = self.root_you
        opp = self.root_opp
        legal = self.get_legal_moves(you, opp)
        if not legal:
            return None

        best_move = None
        best_score = -INF

        # Iterative deepening
        max_depth = 6  # base depth
        empties = self.count_empty(you, opp)
        # increase depth toward endgame
        if empties <= 20:
            max_depth = 8
        if empties <= 12:
            max_depth = 12

        # at least search depth 3 for a reasonable play
        min_depth = 3
        try:
            for depth in range(min_depth, max_depth + 1):
                # time check before each depth
                if time.time() > self.end_time:
                    break
                self.tt.clear()
                cur_best_move = None
                cur_best_score = -INF

                # Move ordering: sort moves by heuristic quickly
                ordered_moves = sorted(legal, key=lambda m: -self.quick_move_score(you, opp, m))

                for move in ordered_moves:
                    if time.time() > self.end_time:
                        raise TimeoutError
                    new_you, new_opp = self.apply_move_copy(you, opp, move)
                    # Negamax: swap players
                    score = -self.negamax(new_opp, new_you, depth - 1, -INF, INF)
                    if score > cur_best_score:
                        cur_best_score = score
                        cur_best_move = move

                if cur_best_move is not None:
                    best_move = cur_best_move
                    best_score = cur_best_score

        except TimeoutError:
            # time ran out, return last known best_move
            pass

        # If nothing found (shouldn't happen), choose a legal move
        if best_move is None:
            return legal[0]
        return best_move

    def negamax(self, you: List[List[int]], opp: List[List[int]], depth: int, alpha: int, beta: int) -> int:
        # time check
        if time.time() > self.end_time:
            raise TimeoutError

        you_bb = self.board_to_bitboard(you)
        opp_bb = self.board_to_bitboard(opp)
        tt_key = (you_bb, opp_bb, depth, alpha, beta)
        if tt_key in self.tt:
            return self.tt[tt_key]

        legal = self.get_legal_moves(you, opp)
        if depth == 0 or not legal:
            # If no legal moves: check if opponent has moves
            if not legal:
                opp_legal = self.get_legal_moves(opp, you)
                if not opp_legal:
                    # Game over: final score difference (big)
                    score = self.final_score(you, opp)
                    self.tt[tt_key] = score
                    return score
                # pass: swap players without changing board; reduce depth
                val = -self.negamax(opp, you, depth - 1, -beta, -alpha)
                self.tt[tt_key] = val
                return val
            # depth 0 evaluate using heuristic
            eval_val = self.evaluate(you, opp)
            self.tt[tt_key] = eval_val
            return eval_val

        max_val = -INF
        # Order moves by quick heuristic
        ordered_moves = sorted(legal, key=lambda m: -self.quick_move_score(you, opp, m))
        for move in ordered_moves:
            if time.time() > self.end_time:
                raise TimeoutError
            new_you, new_opp = self.apply_move_copy(you, opp, move)
            val = -self.negamax(new_opp, new_you, depth - 1, -beta, -alpha)
            if val > max_val:
                max_val = val
            if max_val > alpha:
                alpha = max_val
            if alpha >= beta:
                break

        self.tt[tt_key] = max_val
        return max_val

    # --- Helpers ------------------------------------------------------------

    def board_to_bitboard(self, board: List[List[int]]) -> int:
        bb = 0
        idx = 0
        for r in range(8):
            for c in range(8):
                if board[r][c]:
                    bb |= (1 << idx)
                idx += 1
        return bb

    def count_empty(self, you: List[List[int]], opp: List[List[int]]) -> int:
        cnt = 0
        for r in range(8):
            for c in range(8):
                if you[r][c] == 0 and opp[r][c] == 0:
                    cnt += 1
        return cnt

    def final_score(self, you: List[List[int]], opp: List[List[int]]) -> int:
        you_count = sum(sum(row) for row in you)
        opp_count = sum(sum(row) for row in opp)
        # scale strongly
        return (you_count - opp_count) * 1000

    def evaluate(self, you: List[List[int]], opp: List[List[int]]) -> int:
        # positional score
        pos_score = 0
        you_count = 0
        opp_count = 0
        for r in range(8):
            for c in range(8):
                if you[r][c]:
                    pos_score += POSITION_WEIGHTS[r][c]
                    you_count += 1
                elif opp[r][c]:
                    pos_score -= POSITION_WEIGHTS[r][c]
                    opp_count += 1

        # mobility
        my_moves = len(self.get_legal_moves(you, opp))
        opp_moves = len(self.get_legal_moves(opp, you))
        if my_moves + opp_moves != 0:
            mobility = 100 * (my_moves - opp_moves) // (my_moves + opp_moves)
        else:
            mobility = 0

        # corner occupancy bonus
        corner_score = 0
        for (r, c) in CORNER_COORDS:
            if you[r][c]:
                corner_score += 800
            elif opp[r][c]:
                corner_score -= 800

        # near-corner penalty (if corner is empty, being adjacent is bad)
        near_corner_pen = 0
        for (r, c) in ADJ_TO_CORNER:
            if you[r][c]:
                near_corner_pen -= 150
            elif opp[r][c]:
                near_corner_pen += 150

        # disk difference (only moderate weight early; larger weight near endgame)
        disc_diff = you_count - opp_count
        empties = self.count_empty(you, opp)
        if empties <= 12:
            parity = 1000 * disc_diff
        else:
            parity = 10 * disc_diff

        score = pos_score + mobility * 5 + corner_score + near_corner_pen + parity
        return int(score)

    def get_legal_moves(self, you: List[List[int]], opp: List[List[int]]) -> List[Tuple[int,int]]:
        moves = []
        for r in range(8):
            for c in range(8):
                if you[r][c] or opp[r][c]:
                    continue
                if self.is_legal_move(you, opp, r, c):
                    moves.append((r, c))
        return moves

    def is_legal_move(self, you: List[List[int]], opp: List[List[int]], r: int, c: int) -> bool:
        # Empty required
        if you[r][c] or opp[r][c]:
            return False
        for dr, dc in DIRECTIONS:
            rr = r + dr
            cc = c + dc
            found_op = False
            while 0 <= rr < 8 and 0 <= cc < 8:
                if opp[rr][cc]:
                    found_op = True
                elif you[rr][cc]:
                    if found_op:
                        return True
                    else:
                        break
                else:
                    break
                rr += dr
                cc += dc
        return False

    def apply_move_copy(self, you: List[List[int]], opp: List[List[int]], move: Tuple[int,int]) -> Tuple[List[List[int]], List[List[int]]]:
        r0, c0 = move
        new_you = [row[:] for row in you]
        new_opp = [row[:] for row in opp]
        flips = []
        for dr, dc in DIRECTIONS:
            rr = r0 + dr
            cc = c0 + dc
            line = []
            while 0 <= rr < 8 and 0 <= cc < 8:
                if new_opp[rr][cc]:
                    line.append((rr, cc))
                elif new_you[rr][cc]:
                    if line:
                        flips.extend(line)
                    break
                else:
                    break
                rr += dr
                cc += dc
        # Place piece and flip
        new_you[r0][c0] = 1
        for (fr, fc) in flips:
            new_opp[fr][fc] = 0
            new_you[fr][fc] = 1
        return new_you, new_opp

    def quick_move_score(self, you: List[List[int]], opp: List[List[int]], move: Tuple[int,int]) -> int:
        # Quick heuristic to order moves: prefer corners, then positional weight, then number of flips
        r, c = move
        score = 0
        if (r, c) in CORNER_COORDS:
            score += 10000
        score += POSITION_WEIGHTS[r][c] * 10
        # count flips quickly without full copy
        flips = 0
        for dr, dc in DIRECTIONS:
            rr = r + dr
            cc = c + dc
            line = 0
            found_op = False
            while 0 <= rr < 8 and 0 <= cc < 8:
                if opp[rr][cc]:
                    found_op = True
                    line += 1
                elif you[rr][cc]:
                    if found_op:
                        flips += line
                    break
                else:
                    break
                rr += dr
                cc += dc
        score += flips * 20
        return score
