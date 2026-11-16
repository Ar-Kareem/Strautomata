
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Return the optimal move (row, col) for player 1 on a 3x3 tic-tac-toe board.
    board: 3x3 list of lists with values 0 (empty), 1 (us), -1 (opponent).
    """

    def check_winner(b: List[List[int]]) -> int:
        # returns 1 if us wins, -1 if opponent wins, 0 otherwise
        lines = []
        # rows and cols
        for i in range(3):
            lines.append((b[i][0], b[i][1], b[i][2]))
            lines.append((b[0][i], b[1][i], b[2][i]))
        # diagonals
        lines.append((b[0][0], b[1][1], b[2][2]))
        lines.append((b[0][2], b[1][1], b[2][0]))
        for a, c, d in lines:
            if a == c == d != 0:
                return a
        return 0

    def is_full(b: List[List[int]]) -> bool:
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return False
        return True

    # minimax with alpha-beta; player = 1 (us) or -1 (opponent)
    def minimax(b: List[List[int]], player: int, depth: int, alpha: int, beta: int) -> Tuple[int, Optional[Tuple[int, int]]]:
        winner = check_winner(b)
        if winner != 0:
            # winner is 1 or -1
            return (10 - depth) * winner, None  # For opponent win winner=-1 => negative score
        if is_full(b):
            return 0, None

        best_move: Optional[Tuple[int, int]] = None

        if player == 1:
            max_eval = -9999
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = player
                        eval_score, _ = minimax(b, -player, depth + 1, alpha, beta)
                        b[r][c] = 0
                        if eval_score > max_eval:
                            max_eval = eval_score
                            best_move = (r, c)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            return max_eval, best_move
            return max_eval, best_move
        else:
            min_eval = 9999
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = player
                        eval_score, _ = minimax(b, -player, depth + 1, alpha, beta)
                        b[r][c] = 0
                        if eval_score < min_eval:
                            min_eval = eval_score
                            best_move = (r, c)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            return min_eval, best_move
            return min_eval, best_move

    # If board already terminal or full, return first empty or (0,0) as fallback
    winner_now = check_winner(board)
    if winner_now != 0 or is_full(board):
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)

    _, move = minimax(board, 1, 0, -9999, 9999)
    if move is None:
        # fallback: pick first empty
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)
    return move
