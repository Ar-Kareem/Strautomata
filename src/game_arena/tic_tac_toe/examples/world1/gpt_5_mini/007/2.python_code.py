
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose the optimal move for player 1 (value 1) on a 3x3 Tic-Tac-Toe board.
    board: 3x3 list of lists with values: 0 empty, 1 (you), -1 (opponent)
    Returns (row, col) with 0 <= row,col <= 2
    """

    def check_winner(b: List[List[int]]) -> int:
        # Return 1 if player 1 wins, -1 if opponent wins, 0 otherwise
        lines = []
        # rows and cols
        for i in range(3):
            lines.append((b[i][0], b[i][1], b[i][2]))
            lines.append((b[0][i], b[1][i], b[2][i]))
        # diagonals
        lines.append((b[0][0], b[1][1], b[2][2]))
        lines.append((b[0][2], b[1][1], b[2][0]))
        for a, c, d in lines:
            s = a + c + d
            if s == 3:
                return 1
            if s == -3:
                return -1
        return 0

    def is_full(b: List[List[int]]) -> bool:
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return False
        return True

    def legal_moves(b: List[List[int]]) -> List[Tuple[int, int]]:
        moves = []
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    moves.append((r, c))
        return moves

    # Minimax with alpha-beta
    def minimax(b: List[List[int]], maximizing: bool, alpha: int, beta: int) -> Tuple[int, Optional[Tuple[int, int]]]:
        winner = check_winner(b)
        if winner != 0:
            return winner, None  # winner is 1 or -1
        if is_full(b):
            return 0, None

        best_move: Optional[Tuple[int, int]] = None
        if maximizing:
            value = -2  # less than minimum possible
            for (r, c) in legal_moves(b):
                b[r][c] = 1
                score, _ = minimax(b, False, alpha, beta)
                b[r][c] = 0
                if score > value:
                    value = score
                    best_move = (r, c)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value, best_move
        else:
            value = 2  # greater than maximum possible
            for (r, c) in legal_moves(b):
                b[r][c] = -1
                score, _ = minimax(b, True, alpha, beta)
                b[r][c] = 0
                if score < value:
                    value = score
                    best_move = (r, c)
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value, best_move

    # If no moves (shouldn't be the case), return a default valid coordinate
    moves = legal_moves(board)
    if not moves:
        return (0, 0)

    # Minor heuristic ordering: prefer center, then corners, then sides to help deterministic tie-breaking
    preferred_order = [(1,1), (0,0), (0,2), (2,0), (2,2), (0,1), (1,0), (1,2), (2,1)]
    moves_set = set(moves)
    ordered_moves = [m for m in preferred_order if m in moves_set] + [m for m in moves if m not in set(preferred_order)]

    # To use ordering, we temporarily try moves in that order within minimax by patching legal_moves:
    # Simpler: copy board and run minimax but with initial move iteration in ordered_moves
    best_score = -2
    best_move: Optional[Tuple[int, int]] = None
    for (r, c) in ordered_moves:
        board[r][c] = 1
        score, _ = minimax(board, False, -2, 2)
        board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
        # If winning move found, we can break early
        if best_score == 1:
            break

    if best_move is None:
        # fallback to first empty
        return moves[0]
    return best_move


# Example quick test: (This section will not execute in the arena; it's here for local sanity)
if __name__ == "__main__":
    # empty board: should pick center
    b = [[0,0,0],[0,0,0],[0,0,0]]
    print(policy(b))  # expect (1,1)
