
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    def is_terminal(current_board):
        # Check rows
        for row in current_board:
            if all(cell == row[0] and cell != 0 for cell in row):
                return True, 1 if row[0] == 1 else -1

        # Check columns
        for col in range(4):
            column = [current_board[row][col] for row in range(4)]
            if all(cell == column[0] and cell != 0 for cell in column):
                return True, 1 if column[0] == 1 else -1

        # Check main diagonals
        diag1 = [current_board[i][i] for i in range(4)]
        diag2 = [current_board[i][3-i] for i in range(4)]
        for diag in [diag1, diag2]:
            if all(cell == diag[0] and cell != 0 for cell in diag):
                return True, 1 if diag[0] == 1 else -1

        # Check if board is full (draw)
        if all(cell != 0 for row in current_board for cell in row):
            return True, 0

        return False, 0

    def get_possible_moves(current_board):
        return [(i, j) for i in range(4) for j in range(4) if current_board[i][j] == 0]

    def apply_move(current_board, move, player):
        new_board = [row[:] for row in current_board]
        row, col = move
        new_board[row][col] = player
        return new_board

    def evaluate_board(current_board):
        lines = []
        # All rows
        for row in current_board:
            lines.append(row)
        # All columns
        for col in range(4):
            column = [current_board[row][col] for row in range(4)]
            lines.append(column)
        # Main diagonals
        diag1 = [current_board[i][i] for i in range(4)]
        diag2 = [current_board[i][3-i] for i in range(4)]
        lines.extend([diag1, diag2])

        score = 0
        for line in lines:
            p1 = line.count(1)
            p2 = line.count(-1)
            empties = line.count(0)

            # Player 1's lines
            if p1 > 0 and p2 == 0:
                score += p1 * (p1**2)  # Bias for more complete lines
            # Player -1's lines
            if p2 > 0 and p1 == 0:
                score -= p2 * (p2**2)

        return score

    MAX_DEPTH = 6  # Adjust based on performance requirements

    def minimax(current_board, depth, alpha, beta, maximizing_player):
        term, sc = is_terminal(current_board)
        if term:
            return sc, None

        if depth >= MAX_DEPTH:
            return evaluate_board(current_board), None

        moves = get_possible_moves(current_board)

        if maximizing_player:  # AI's turn (player == 1)
            max_score = -float('inf')
            best_m = None
            for m in moves:
                new_b = apply_move(current_board, m, 1)
                val, _ = minimax(new_b, depth + 1, alpha, beta, False)
                if val > max_score:
                    max_score, best_m = val, m
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return max_score, best_m
        else:  # Opponent's turn (player == -1)
            min_score = float('inf')
            best_m = None
            for m in moves:
                new_b = apply_move(current_board, m, -1)
                val, _ = minimax(new_b, depth + 1, alpha, beta, True)
                if val < min_score:
                    min_score, best_m = val, m
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return min_score, best_m

    # Entry point for decision
    _, best_move = minimax(board, 0, -float('inf'), float('inf'), True)
    return best_move
