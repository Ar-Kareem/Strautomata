
import time

# Precompute all 36 5-in-a-row lines on a 6x6 board
LINES = []
for r in range(6):
    for c in range(2):
        LINES.append([(r, c+i) for i in range(5)])
for c in range(6):
    for r in range(2):
        LINES.append([(r+i, c) for i in range(5)])
for r in range(2):
    for c in range(2):
        LINES.append([(r+i, c+i) for i in range(5)])
for r in range(2):
    for c in range(4, 6):
        LINES.append([(r+i, c-i) for i in range(5)])

SCORES = [0, 1, 10, 100, 10000]  # score for 0,1,2,3,4 marbles in a row

class GameState:
    def __init__(self, board, turn):
        self.board = board
        self.turn = turn

    def copy(self):
        return GameState([row[:] for row in self.board], self.turn)

    def legal_moves(self):
        moves = []
        for r in range(6):
            for c in range(6):
                if self.board[r][c] == 0:
                    for q in range(4):
                        moves.append((r, c, q, 'L'))
                        moves.append((r, c, q, 'R'))
        return moves

    def apply_move(self, r, c, q, d):
        new_board = [row[:] for row in self.board]
        new_board[r][c] = self.turn
        qr = (q // 2) * 3
        qc = (q % 2) * 3
        block = [new_board[qr+i][qc:qc+3] for i in range(3)]
        if d == 'L':
            new_block = [[block[j][2-i] for j in range(3)] for i in range(3)]
        else:
            new_block = [[block[2-j][i] for j in range(3)] for i in range(3)]
        for i in range(3):
            new_board[qr+i][qc:qc+3] = new_block[i]
        next_turn = 3 - self.turn
        return GameState(new_board, next_turn)

    def is_terminal(self):
        p1 = False
        p2 = False
        for line in LINES:
            p1_count = 0
            p2_count = 0
            for r, c in line:
                v = self.board[r][c]
                if v == 1:
                    p1_count += 1
                elif v == 2:
                    p2_count += 1
            if p1_count >= 5:
                p1 = True
            if p2_count >= 5:
                p2 = True
        if p1 and p2:
            return 0  # draw
        if p1:
            return 1  # player 1 wins
        if p2:
            return 2  # player 2 wins
        for row in self.board:
            if 0 in row:
                return -1  # not terminal
        return 0  # draw (board full)

def evaluate(state):
    score = 0
    for line in LINES:
        p1 = 0
        p2 = 0
        for r, c in line:
            v = state.board[r][c]
            if v == 1:
                p1 += 1
            elif v == 2:
                p2 += 1
        if p1 > 0 and p2 > 0:
            continue
        score += SCORES[p1] - SCORES[p2]
    return score

def minimax(state, depth, alpha, beta, start_time=None):
    if start_time and time.time() - start_time > 0.9:
        return evaluate(state)
    result = state.is_terminal()
    if result != -1:
        if result == 1:
            return 1000000
        elif result == 2:
            return -1000000
        else:
            return 0
    if depth == 0:
        return evaluate(state)

    moves = state.legal_moves()
    if state.turn == 1:  # maximizing player
        if depth > 1:
            move_evals = []
            for move in moves:
                child = state.apply_move(*move)
                move_evals.append((evaluate(child), move))
            move_evals.sort(key=lambda x: x[0], reverse=True)
            moves = [m for _, m in move_evals]
        max_eval = -float('inf')
        for move in moves:
            child = state.apply_move(*move)
            val = minimax(child, depth-1, alpha, beta, start_time)
            max_eval = max(max_eval, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_eval
    else:  # minimizing player (opponent)
        if depth > 1:
            move_evals = []
            for move in moves:
                child = state.apply_move(*move)
                move_evals.append((evaluate(child), move))
            move_evals.sort(key=lambda x: x[0])
            moves = [m for _, m in move_evals]
        min_eval = float('inf')
        for move in moves:
            child = state.apply_move(*move)
            val = minimax(child, depth-1, alpha, beta, start_time)
            min_eval = min(min_eval, val)
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_eval

def policy(you, opponent):
    board = [[0]*6 for _ in range(6)]
    for r in range(6):
        for c in range(6):
            if you[r][c]:
                board[r][c] = 1
            elif opponent[r][c]:
                board[r][c] = 2
    state = GameState(board, 1)

    # Immediate win
    for move in state.legal_moves():
        child = state.apply_move(*move)
        if child.is_terminal() == 1:
            r, c, q, d = move
            return f"{r+1},{c+1},{q},{d}"

    start_time = time.time()
    best_move = None
    depth = 1
    while True:
        moves = state.legal_moves()
        if depth > 1:
            move_evals = []
            for move in moves:
                child = state.apply_move(*move)
                move_evals.append((evaluate(child), move))
            move_evals.sort(key=lambda x: x[0], reverse=True)
            moves = [m for _, m in move_evals]

        current_best = None
        best_val = -float('inf')
        for move in moves:
            child = state.apply_move(*move)
            val = minimax(child, depth-1, -float('inf'), float('inf'), start_time)
            if val > best_val:
                best_val = val
                current_best = move
            if time.time() - start_time > 0.9:
                break

        if current_best is not None:
            best_move = current_best

        if time.time() - start_time > 0.9 or depth >= 10:
            break
        depth += 1

    if best_move is None:
        best_move = state.legal_moves()[0]
    r, c, q, d = best_move
    return f"{r+1},{c+1},{q},{d}"
