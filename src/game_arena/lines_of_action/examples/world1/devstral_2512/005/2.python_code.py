
import random
import numpy as np
from collections import deque

def policy(board) -> str:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)

    # Find all my pieces and opponent pieces
    my_pieces = np.argwhere(board == 1)
    opp_pieces = np.argwhere(board == -1)

    # If no pieces left (shouldn't happen), return random move
    if len(my_pieces) == 0:
        return "0,0:0,1"

    # Generate all possible legal moves
    legal_moves = []
    for piece in my_pieces:
        row, col = piece
        # Check all 8 directions
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                # Calculate number of pieces in this line
                count = 0
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    if board[r][c] != 0:
                        count += 1
                    r += dr
                    c += dc
                # Possible move distance
                distance = count
                if distance == 0:
                    continue
                # Check possible landing positions
                for d in [distance, -distance]:
                    r, c = row + dr*d, col + dc*d
                    if 0 <= r < 8 and 0 <= c < 8:
                        # Check if path is clear (no opponent pieces in between)
                        path_clear = True
                        step = 1 if d > 0 else -1
                        for i in range(1, abs(d)):
                            rr, cc = row + dr*i*step, col + dc*i*step
                            if board[rr][cc] == -1:
                                path_clear = False
                                break
                        if path_clear:
                            legal_moves.append((row, col, r, c))

    # If no legal moves (shouldn't happen), return random move
    if not legal_moves:
        return "0,0:0,1"

    # Score each legal move
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        from_row, from_col, to_row, to_col = move
        # Create a copy of the board to simulate the move
        temp_board = board.copy()
        # Move the piece
        temp_board[to_row][to_col] = 1
        temp_board[from_row][from_col] = 0
        # If capturing opponent piece
        if board[to_row][to_col] == -1:
            temp_board[to_row][to_col] = 1

        # Calculate score for this move
        score = evaluate_move(temp_board, from_row, from_col, to_row, to_col)

        if score > best_score:
            best_score = score
            best_move = move

    # If all moves have same score, pick randomly
    if best_move is None:
        best_move = random.choice(legal_moves)

    # Format the move string
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"

def evaluate_move(board, from_row, from_col, to_row, to_col):
    score = 0

    # 1. Connectivity score (most important)
    my_pieces = np.argwhere(board == 1)
    if len(my_pieces) == 0:
        return -1000  # Shouldn't happen

    # Calculate connectivity using BFS
    visited = set()
    groups = 0
    for piece in my_pieces:
        if tuple(piece) not in visited:
            groups += 1
            queue = deque([tuple(piece)])
            visited.add(tuple(piece))
            while queue:
                r, c = queue.popleft()
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < 8 and 0 <= cc < 8 and board[rr][cc] == 1 and (rr, cc) not in visited:
                            visited.add((rr, cc))
                            queue.append((rr, cc))

    # Fewer groups is better (we want 1 group)
    score += (1 - groups) * 100

    # 2. Material advantage
    my_count = len(my_pieces)
    opp_count = len(np.argwhere(board == -1))
    score += (my_count - opp_count) * 10

    # 3. Central control (distance from center)
    center = 3.5
    dist_from_center = abs(to_row - center) + abs(to_col - center)
    score += (7 - dist_from_center) * 5  # Max distance is 7 (corner)

    # 4. Mobility - count possible moves for remaining pieces
    mobility = 0
    for piece in my_pieces:
        row, col = piece
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                count = 0
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    if board[r][c] != 0:
                        count += 1
                    r += dr
                    c += dc
                distance = count
                if distance == 0:
                    continue
                for d in [distance, -distance]:
                    r, c = row + dr*d, col + dc*d
                    if 0 <= r < 8 and 0 <= c < 8:
                        path_clear = True
                        step = 1 if d > 0 else -1
                        for i in range(1, abs(d)):
                            rr, cc = row + dr*i*step, col + dc*i*step
                            if board[rr][cc] == -1:
                                path_clear = False
                                break
                        if path_clear:
                            mobility += 1
    score += mobility * 2

    # 5. Bonus for capturing opponent piece
    if board[to_row][to_col] == -1:
        score += 20

    return score
