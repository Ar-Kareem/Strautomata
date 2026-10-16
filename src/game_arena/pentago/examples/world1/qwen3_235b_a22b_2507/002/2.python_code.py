
import numpy as np

def policy(you, opponent) -> str:
    # Convert inputs to numpy arrays for easier manipulation
    you_board = np.array(you, dtype=int)
    opp_board = np.array(opponent, dtype=int)
    board = you_board - opp_board  # Combined: 1 = me, -1 = opponent, 0 = empty
    empty = (you_board + opp_board == 0)

    # Helper: rotate quadrant in board
    def rotate_quad(board, quad, direction):
        # Extract 3x3 quadrant
        if quad == 0:
            sub = board[0:3, 0:3].copy()
        elif quad == 1:
            sub = board[0:3, 3:6].copy()
        elif quad == 2:
            sub = board[3:6, 0:3].copy()
        else:  # quad 3
            sub = board[3:6, 3:6].copy()
        
        # Rotate
        if direction == 'R':
            sub = np.rot90(sub, k=3)  # 90 deg clockwise
        else:  # 'L'
            sub = np.rot90(sub, k=1)  # 90 deg anticlockwise
        
        # Write back
        new_board = board.copy()
        if quad == 0:
            new_board[0:3, 0:3] = sub
        elif quad == 1:
            new_board[0:3, 3:6] = sub
        elif quad == 2:
            new_board[3:6, 0:3] = sub
        else:
            new_board[3:6, 3:6] = sub
        return new_board

    # Helper: check if player has 5 in a row (either player)
    def has_won(board):
        # Check rows
        for r in range(6):
            for c in range(2):
                line = board[r, c:c+5]
                if np.all(line == 1) or np.all(line == -1):
                    return board[r, c]
        # Check cols
        for c in range(6):
            for r in range(2):
                line = board[r:r+5, c]
                if np.all(line == 1) or np.all(line == -1):
                    return board[r, c]
        # Check diagonals: top-left to bottom-right
        for r in range(2):
            for c in range(2):
                line = [board[r+i, c+i] for i in range(5)]
                if all(x == 1 for x in line) or all(x == -1 for x in line):
                    return board[r, c]
        # Check anti-diagonals: top-right to bottom-left
        for r in range(2):
            for c in range(4, 6):
                line = [board[r+i, c-i] for i in range(5)]
                if all(x == 1 for x in line) or all(x == -1 for x in line):
                    return board[r, c]
        return 0

    # Heuristic evaluation: score the position
    def evaluate(board):
        score = 0
        # Check all possible 5-length lines
        lines = []

        # Rows
        for r in range(6):
            for c in range(2):
                lines.append(board[r, c:c+5])
        # Cols
        for c in range(6):
            for r in range(2):
                lines.append(board[r:r+5, c])
        # Diagonals
        for r in range(2):
            for c in range(2):
                lines.append([board[r+i, c+i] for i in range(5)])
        for r in range(2):
            for c in range(4, 6):
                lines.append([board[r+i, c-i] for i in range(5)])

        for line in lines:
            line = np.array(line)
            my_count = np.sum(line == 1)
            opp_count = np.sum(line == -1)
            if opp_count == 0:
                if my_count == 5:
                    score += 10000
                elif my_count == 4:
                    score += 100
                elif my_count == 3:
                    score += 10
            elif my_count == 0:
                if opp_count == 5:
                    score -= 10000
                elif opp_count == 4:
                    score -= 100
                elif opp_count == 3:
                    score -= 10
        return score

    # Get list of empty positions
    empty_positions = [(r, c) for r in range(6) for c in range(6) if empty[r, c]]

    # Try each legal move: (r, c, quad, dir)
    moves = []
    for r, c in empty_positions:
        for quad in range(4):
            for direction in ['L', 'R']:
                # Simulate move
                new_board = board.copy()
                new_board[r, c] = 1  # place our marble
                new_board = rotate_quad(new_board, quad, direction)

                # Check if this move makes us win (even if opponent also wins, it's a draw — but we win only if we have 5 in row and not canceled)
                result = has_won(new_board)
                if result == 1:
                    return f"{r+1},{c+1},{quad},{direction}"  # immediate win

                # Also check if this blocks an opponent win or creates a strong position
                # But don't return yet — we must check all wins first
                score = evaluate(new_board)
                moves.append((score, (r, c, quad, direction)))

    # If no winning move, check: is opponent about to win? Can we block?
    # Simulate: what if we don't move — could opponent win on their next move?
    # But simpler: among our moves, prioritize highest heuristic score
    # Sort by score descending
    moves.sort(key=lambda x: x[0], reverse=True)

    # Pick move with highest score
    best_move = moves[0][1]
    r, c, quad, direction = best_move
    return f"{r+1},{c+1},{quad},{direction}"
