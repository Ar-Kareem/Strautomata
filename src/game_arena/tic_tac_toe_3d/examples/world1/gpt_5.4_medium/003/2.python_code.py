
import time
import random

WIN_SCORE = 1_000_000
INF = 10**18


def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k


def _generate_lines():
    lines = []

    for j in range(3):
        for k in range(3):
            lines.append((_idx(0, j, k), _idx(1, j, k), _idx(2, j, k)))
    for i in range(3):
        for k in range(3):
            lines.append((_idx(i, 0, k), _idx(i, 1, k), _idx(i, 2, k)))
    for i in range(3):
        for j in range(3):
            lines.append((_idx(i, j, 0), _idx(i, j, 1), _idx(i, j, 2)))

    for k in range(3):
        lines.append((_idx(0, 0, k), _idx(1, 1, k), _idx(2, 2, k)))
        lines.append((_idx(0, 2, k), _idx(1, 1, k), _idx(2, 0, k)))

    for j in range(3):
        lines.append((_idx(0, j, 0), _idx(1, j, 1), _idx(2, j, 2)))
        lines.append((_idx(0, j, 2), _idx(1, j, 1), _idx(2, j, 0)))

    for i in range(3):
        lines.append((_idx(i, 0, 0), _idx(i, 1, 1), _idx(i, 2, 2)))
        lines.append((_idx(i, 0, 2), _idx(i, 1, 1), _idx(i, 2, 0)))

    lines.append((_idx(0, 0, 0), _idx(1, 1, 1), _idx(2, 2, 2)))
    lines.append((_idx(0, 0, 2), _idx(1, 1, 1), _idx(2, 2, 0)))
    lines.append((_idx(0, 2, 0), _idx(1, 1, 1), _idx(2, 0, 2)))
    lines.append((_idx(0, 2, 2), _idx(1, 1, 1), _idx(2, 0, 0)))

    return lines


LINES = _generate_lines()
CELL_TO_LINES = [[] for _ in range(27)]
OTHERS_BY_CELL = [[] for _ in range(27)]

for lid, line in enumerate(LINES):
    a, b, c = line
    CELL_TO_LINES[a].append(lid)
    CELL_TO_LINES[b].append(lid)
    CELL_TO_LINES[c].append(lid)
    OTHERS_BY_CELL[a].append((b, c))
    OTHERS_BY_CELL[b].append((a, c))
    OTHERS_BY_CELL[c].append((a, b))

CELL_DEGREE = [len(CELL_TO_LINES[i]) for i in range(27)]
IDX_TO_COORD = [(i, j, k) for i in range(3) for j in range(3) for k in range(3)]
CENTER_IDX = _idx(1, 1, 1)
CORNERS = [_idx(i, j, k) for i in (0, 2) for j in (0, 2) for k in (0, 2)]
CORNER_SET = set(CORNERS)

POSITION_SCORES = []
for idx in range(27):
    score = CELL_DEGREE[idx] * 12
    if idx == CENTER_IDX:
        score += 30
    elif idx in CORNER_SET:
        score += 8
    POSITION_SCORES.append(score)

BUILD_SCORE = [0, 18, 2200]
BLOCK_SCORE = [0, 22, 2000]

_rng = random.Random(0)
ZOBRIST = [(_rng.getrandbits(64), _rng.getrandbits(64)) for _ in range(27)]


def _is_win(flat, idx: int, player: int) -> bool:
    for lid in CELL_TO_LINES[idx]:
        a, b, c = LINES[lid]
        if flat[a] == player and flat[b] == player and flat[c] == player:
            return True
    return False


class _Searcher:
    def __init__(self, flat, deadline: float):
        self.flat = flat
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        h = 0
        for idx, v in enumerate(flat):
            if v == 1:
                h ^= ZOBRIST[idx][0]
            elif v == -1:
                h ^= ZOBRIST[idx][1]
        self.hash = h

    def check_time(self):
        self.nodes += 1
        if (self.nodes & 1023) == 0 and time.perf_counter() > self.deadline:
            raise TimeoutError

    def evaluate(self) -> int:
        flat = self.flat
        score = 0

        for a, b, c in LINES:
            va, vb, vc = flat[a], flat[b], flat[c]
            p = (va == 1) + (vb == 1) + (vc == 1)
            o = (va == -1) + (vb == -1) + (vc == -1)
            if p and o:
                continue
            if p == 1:
                score += 5
            elif p == 2:
                score += 130
            elif o == 1:
                score -= 6
            elif o == 2:
                score -= 145

        for idx, v in enumerate(flat):
            if v == 1:
                score += POSITION_SCORES[idx] // 6
            elif v == -1:
                score -= POSITION_SCORES[idx] // 6

        return score

    def ordered_moves(self, player: int, moves=None, tt_move=None, priority_set=None):
        if moves is None:
            moves = [i for i, v in enumerate(self.flat) if v == 0]

        flat = self.flat
        scored = []

        for idx in moves:
            score = POSITION_SCORES[idx]
            if tt_move is not None and idx == tt_move:
                score += 100000
            if priority_set is not None and idx in priority_set:
                score += 3000

            for u, v in OTHERS_BY_CELL[idx]:
                vu = flat[u]
                vv = flat[v]
                p = (vu == player) + (vv == player)
                o = (vu == -player) + (vv == -player)

                if o == 0:
                    score += BUILD_SCORE[p]
                if p == 0:
                    score += BLOCK_SCORE[o]

            scored.append((score, idx))

        scored.sort(reverse=True)
        return [idx for _, idx in scored]

    def negamax(self, depth: int, alpha: int, beta: int, player: int, empties: int) -> int:
        self.check_time()

        if empties == 0:
            return 0
        if depth == 0:
            return player * self.evaluate()

        key = (self.hash, player)
        entry = self.tt.get(key)
        alpha_orig = alpha
        beta_orig = beta
        tt_move = None

        if entry is not None:
            entry_depth, flag, val, best_move = entry
            tt_move = best_move
            if entry_depth >= depth:
                if flag == 0:
                    return val
                elif flag == 1:
                    if val > alpha:
                        alpha = val
                else:
                    if val < beta:
                        beta = val
                if alpha >= beta:
                    return val

        moves = self.ordered_moves(player, tt_move=tt_move)
        best = -INF
        best_move = moves[0]

        for idx in moves:
            self.flat[idx] = player
            self.hash ^= ZOBRIST[idx][0 if player == 1 else 1]

            if _is_win(self.flat, idx, player):
                val = WIN_SCORE + depth
            else:
                val = -self.negamax(depth - 1, -beta, -alpha, -player, empties - 1)

            self.hash ^= ZOBRIST[idx][0 if player == 1 else 1]
            self.flat[idx] = 0

            if val > best:
                best = val
                best_move = idx
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        if best <= alpha_orig:
            flag = 2
        elif best >= beta_orig:
            flag = 1
        else:
            flag = 0
        self.tt[key] = (depth, flag, best, best_move)
        return best

    def choose_move(self, priority_set=None) -> int:
        legal = [i for i, v in enumerate(self.flat) if v == 0]
        if not legal:
            return 0
        if len(legal) == 1:
            return legal[0]

        empties = len(legal)
        if empties <= 8:
            max_depth = empties
        elif empties <= 11:
            max_depth = 8
        elif empties <= 14:
            max_depth = 7
        elif empties <= 18:
            max_depth = 6
        elif empties <= 22:
            max_depth = 5
        else:
            max_depth = 4

        initial_moves = self.ordered_moves(1, legal, priority_set=priority_set)
        best_move = initial_moves[0]

        for depth in range(1, max_depth + 1):
            try:
                alpha = -INF
                beta = INF
                root_entry = self.tt.get((self.hash, 1))
                tt_move = root_entry[3] if root_entry is not None else best_move
                moves = self.ordered_moves(1, legal, tt_move=tt_move, priority_set=priority_set)

                best_val = -INF
                current_best = best_move

                for idx in moves:
                    self.check_time()

                    self.flat[idx] = 1
                    self.hash ^= ZOBRIST[idx][0]

                    if _is_win(self.flat, idx, 1):
                        val = WIN_SCORE + depth
                    else:
                        val = -self.negamax(depth - 1, -beta, -alpha, -1, empties - 1)

                    self.hash ^= ZOBRIST[idx][0]
                    self.flat[idx] = 0

                    if val > best_val:
                        best_val = val
                        current_best = idx
                    if val > alpha:
                        alpha = val

                best_move = current_best
                if best_val >= WIN_SCORE:
                    break

            except TimeoutError:
                break

        return best_move


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    flat = [board[i][j][k] for i in range(3) for j in range(3) for k in range(3)]
    legal = [idx for idx, v in enumerate(flat) if v == 0]

    if not legal:
        return (0, 0, 0)

    for idx in legal:
        flat[idx] = 1
        if _is_win(flat, idx, 1):
            flat[idx] = 0
            return IDX_TO_COORD[idx]
        flat[idx] = 0

    opp_wins = []
    for idx in legal:
        flat[idx] = -1
        if _is_win(flat, idx, -1):
            opp_wins.append(idx)
        flat[idx] = 0

    if len(opp_wins) == 1:
        return IDX_TO_COORD[opp_wins[0]]

    marks_played = 27 - len(legal)

    if marks_played <= 2 and flat[CENTER_IDX] == 0:
        return IDX_TO_COORD[CENTER_IDX]

    if marks_played == 1 and flat[CENTER_IDX] == -1:
        for idx in CORNERS:
            if flat[idx] == 0:
                return IDX_TO_COORD[idx]

    deadline = time.perf_counter() + 0.95
    searcher = _Searcher(flat, deadline)
    priority_set = set(opp_wins) if len(opp_wins) > 1 else None

    best = searcher.choose_move(priority_set=priority_set)

    if 0 <= best < 27 and flat[best] == 0:
        return IDX_TO_COORD[best]

    for idx in legal:
        return IDX_TO_COORD[idx]

    return (0, 0, 0)
