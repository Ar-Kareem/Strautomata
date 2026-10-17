
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose the next move for player 1 (represented by 1) on a 3x3 Tic Tac Toe board.
    board: 3x3 list of lists with values {1: us, -1: opponent, 0: empty}
    Returns a tuple (row, col) with 0-based indices.
    """

    WIN_LINES = [
        [(0,0),(0,1),(0,2)],
        [(1,0),(1,1),(1,2)],
        [(2,0),(2,1),(2,2)],
        [(0,0),(1,0),(2,0)],
        [(0,1),(1,1),(2,1)],
        [(0,2),(1,2),(2,2)],
        [(0,0),(1,1),(2,2)],
        [(0,2),(1,1),(2,0)]
    ]

    def check_winner(b: List[List[int]]) -> int:
        # return 1 if player 1 wins, -1 if opponent wins, 0 otherwise
        for line in WIN_LINES:
            s = b[line[0][0]][line[0][1]] + b[line[1][0]][line[1][1]] + b[line[2][0]][line[2][1]]
            if s == 3:
                return 1
            if s == -3:
                return -1
        return 0

    def has_empty(b: List[List[int]]) -> bool:
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return True
        return False

    # Minimax with alpha-beta. Score is from perspective of player 1:
    # 1 -> player 1 wins, -1 -> opponent wins, 0 -> draw.
    def minimax(b: List[List[int]], player_turn: int, alpha: int, beta: int) -> Tuple[int, Optional[Tuple[int,int]]]:
        winner = check_winner(b)
        if winner != 0:
            return winner, None
        if not has_empty(b):
            return 0, None

        best_move: Optional[Tuple[int,int]] = None

        if player_turn == 1:
            best_score = -2  # less than minimum possible
            # iterate row-major to be deterministic
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = 1
                        score, _ = minimax(b, -1, alpha, beta)
                        b[r][c] = 0
                        if score > best_score:
                            best_score = score
                            best_move = (r, c)
                        alpha = max(alpha, best_score)
                        if beta <= alpha:
                            return best_score, best_move
            return best_score, best_move
        else:
            best_score = 2  # greater than maximum possible
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = -1
                        score, _ = minimax(b, 1, alpha, beta)
                        b[r][c] = 0
                        if score < best_score:
                            best_score = score
                            best_move = (r, c)
                        beta = min(beta, best_score)
                        if beta <= alpha:
                            return best_score, best_move
            return best_score, best_move

    # If board is already terminal, just pick the first empty cell (or (0,0) if none).
    if check_winner(board) != 0 or not has_empty(board):
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)

    _, move = minimax(board, 1, -2, 2)
    if move is None:
        # fallback: first empty cell
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)
    return move
