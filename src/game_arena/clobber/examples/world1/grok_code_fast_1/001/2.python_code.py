
import numpy as np

def policy(you: list[list[int]], opponent: list[list[int]]) -> str:
    board_y = np.array(you, dtype=int)  # 5x6 array
    board_o = np.array(opponent, dtype=int)  # 5x6 array
    directions = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
    
    def is_valid(r: int, c: int) -> bool:
        return 0 <= r < 5 and 0 <= c < 6
    
    def generate_moves(me: np.ndarray, opp: np.ndarray) -> list[tuple[int, int, str]]:
        moves = []
        for r in range(5):
            for c in range(6):
                if me[r, c] == 1:
                    for d, (dr, dc) in directions.items():
                        nr, nc = r + dr, c + dc
                        if is_valid(nr, nc) and opp[nr, nc] == 1:
                            moves.append((r, c, d))
        return moves
    
    def make_move(me: np.ndarray, opp: np.ndarray, move: tuple[int, int, str]) -> tuple[np.ndarray, np.ndarray]:
        r, c, d = move
        dr, dc = directions[d]
        nr, nc = r + dr, c + dc
        new_me = me.copy()
        new_me[r, c] = 0
        new_me[nr, nc] = 1
        new_opp = opp.copy()
        new_opp[nr, nc] = 0
        return new_me, new_opp
    
    def evaluate(y: np.ndarray, o: np.ndarray) -> int:
        # Favor higher piece count for the maximizing player (me in our case)
        return np.sum(y) - np.sum(o)
    
    def minimax(y: np.ndarray, o: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> int:
        if depth == 0:
            return evaluate(y, o)
        if maximizing:
            max_val = -float('inf')
            for move in generate_moves(y, o):
                ny, no = make_move(y, o, move)
                val = minimax(ny, no, depth - 1, alpha, beta, False)
                max_val = max(max_val, val)
                alpha = max(alpha, max_val)
                if alpha >= beta:
                    break
            return max_val
        else:
            min_val = float('inf')
            for move in generate_moves(o, y):  # Note: opponent is "me" here
                ny, no = make_move(o, y, move)  # Need to swap for opponent turn
                val = minimax(ny, no, depth - 1, alpha, beta, True)
                min_val = min(min_val, val)
                beta = min(beta, min_val)
                if beta <= alpha:
                    break
            return min_val
    
    moves = generate_moves(board_y, board_o)
    best_move = None
    best_val = -float('inf')
    for move in moves:
        ny, no = make_move(board_y, board_o, move)
        val = minimax(ny, no, 3, -float('inf'), float('inf'), False)  # Opponent to move after our move
        if val > best_val:
            best_val = val
            best_move = move
    
    if best_move:
        r, c, d = best_move
        return f'{r},{c},{d}'
    else:
        # No moves possible, but problem states there always is one, so this shouldn't happen
        pass
