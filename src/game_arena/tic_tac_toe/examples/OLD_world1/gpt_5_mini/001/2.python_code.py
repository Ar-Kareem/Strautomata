
from typing import List, Optional, Tuple
import math

def policy(board: List[List[int]]) -> int:
    """
    Choose the best move (1-9) for player 1 on the given Tic Tac Toe board.
    Board is a 3x3 list of lists with values: 0 (empty), 1 (us), -1 (opponent).
    Returns a number 1..9 corresponding to:
      1 2 3
      4 5 6
      7 8 9
    """

    def winner(b: List[List[int]]) -> int:
        # Returns 1 if player 1 wins, -1 if player -1 wins, 0 otherwise
        lines = []
        # rows and cols
        for i in range(3):
            lines.append([b[i][0], b[i][1], b[i][2]])
            lines.append([b[0][i], b[1][i], b[2][i]])
        # diagonals
        lines.append([b[0][0], b[1][1], b[2][2]])
        lines.append([b[0][2], b[1][1], b[2][0]])
        for line in lines:
            s = sum(line)
            if s == 3:
                return 1
            if s == -3:
                return -1
        return 0

    def empty_cells(b: List[List[int]]) -> List[Tuple[int,int,int]]:
        # returns list of (index1to9, r, c)
        cells = []
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    idx = r * 3 + c + 1
                    cells.append((idx, r, c))
        return cells

    def is_terminal(b: List[List[int]]) -> bool:
        if winner(b) != 0:
            return True
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return False
        return True

    # Minimax with alpha-beta. We start with player = 1 (us).
    def minimax(b: List[List[int]], player: int, depth: int, alpha: float, beta: float) -> Tuple[float, Optional[int]]:
        w = winner(b)
        if w != 0:
            # prefer faster wins and slower losses
            if w == 1:
                return (10 - depth, None)
            else:
                return (depth - 10, None)
        empties = empty_cells(b)
        if not empties:
            return (0, None)  # draw

        best_move: Optional[int] = None

        if player == 1:
            # maximize
            max_eval = -math.inf
            for idx, r, c in empties:
                b[r][c] = 1
                eval_score, _ = minimax(b, -1, depth + 1, alpha, beta)
                b[r][c] = 0
                if eval_score > max_eval or (eval_score == max_eval and (best_move is None or idx < best_move)):
                    max_eval = eval_score
                    best_move = idx
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return (max_eval, best_move)
        else:
            # minimize
            min_eval = math.inf
            for idx, r, c in empties:
                b[r][c] = -1
                eval_score, _ = minimax(b, 1, depth + 1, alpha, beta)
                b[r][c] = 0
                if eval_score < min_eval or (eval_score == min_eval and (best_move is None or idx < best_move)):
                    min_eval = eval_score
                    best_move = idx
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return (min_eval, best_move)

    # If board is already terminal or no empties, return first cell (fallback)
    empt = empty_cells(board)
    if not empt or is_terminal(board):
        # fallback to first position 1 if nothing else
        return 1

    # Quick heuristics: win if possible, block immediate opponent win, take center, corner, side
    # This speeds up common cases before full minimax.
    # 1) Win if possible
    for idx, r, c in empt:
        board[r][c] = 1
        if winner(board) == 1:
            board[r][c] = 0
            return idx
        board[r][c] = 0
    # 2) Block opponent immediate win
    for idx, r, c in empt:
        board[r][c] = -1
        if winner(board) == -1:
            board[r][c] = 0
            return idx
        board[r][c] = 0
    # 3) Take center if free
    if board[1][1] == 0:
        return 5
    # 4) Opposite corner if opponent in corner
    corners = [(1,0,0),(3,0,2),(7,2,0),(9,2,2)]
    opposite = {1:9, 3:7, 7:3, 9:1}
    for idx, r, c in corners:
        if board[r][c] == -1:
            opp_idx = opposite[idx]
            orow = (opp_idx - 1) // 3
            ocol = (opp_idx - 1) % 3
            if board[orow][ocol] == 0:
                return opp_idx
    # 5) Take any corner
    for idx, r, c in corners:
        if board[r][c] == 0:
            return idx
    # 6) Take any side
    sides = [2,4,6,8]
    for s in sides:
        r = (s-1)//3
        c = (s-1)%3
        if board[r][c] == 0:
            return s

    # If heuristics didn't pick, use minimax to choose best move
    _, move = minimax(board, 1, 0, -math.inf, math.inf)
    if move is None:
        # fallback to first empty
        return empt[0][0]
    return move
