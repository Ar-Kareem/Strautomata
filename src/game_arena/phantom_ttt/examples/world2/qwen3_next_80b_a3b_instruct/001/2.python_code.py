
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    
    # Get coordinates of all empty/uncertain cells (0) and exclude our own confirmed cells (1)
    possible_moves = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    
    # If no legal moves, return a safe default (shouldn't happen in correct game state)
    if not possible_moves:
        return (0, 0)
    
    # Check for immediate win: if we have two in a line and one empty, play there
    for i in range(3):
        # Check rows
        if np.sum(board[i, :] == 1) == 2:
            for j in range(3):
                if board[i][j] == 0:
                    return (i, j)
        # Check columns
        if np.sum(board[:, i] == 1) == 2:
            for j in range(3):
                if board[j][i] == 0:
                    return (j, i)
    
    # Check main diagonal
    diag1 = [board[i][i] for i in range(3)]
    if np.sum(np.array(diag1) == 1) == 2:
        for i in range(3):
            if diag1[i] == 0:
                return (i, i)
    
    # Check anti-diagonal
    diag2 = [board[i][2-i] for i in range(3)]
    if np.sum(np.array(diag2) == 1) == 2:
        for i in range(3):
            if diag2[i] == 0:
                return (i, 2-i)
    
    # Check for potential opponent wins: if a line has two 0s and zero 1s, opponent might be about to win
    # But since we don't know if 0s are opponent or empty, we infer: if a line has two 0s and one 1, 
    # it's likely that the 1 is ours and the two 0s are potential opponent marks — blocking one is smart.
    # We prioritize blocking threats in lines with one of our marks and two 0s.
    threats = []
    
    for i in range(3):
        # Rows
        row = board[i, :]
        if np.sum(row == 1) == 1 and np.sum(row == 0) == 2:
            for j in range(3):
                if row[j] == 0:
                    threats.append((i, j))
        # Columns
        col = board[:, i]
        if np.sum(col == 1) == 1 and np.sum(col == 0) == 2:
            for j in range(3):
                if col[j] == 0:
                    threats.append((j, i))
    
    # Diagonals
    diag1 = [board[i][i] for i in range(3)]
    if np.sum(np.array(diag1) == 1) == 1 and np.sum(np.array(diag1) == 0) == 2:
        for i in range(3):
            if diag1[i] == 0:
                threats.append((i, i))
    
    diag2 = [board[i][2-i] for i in range(3)]
    if np.sum(np.array(diag2) == 1) == 1 and np.sum(np.array(diag2) == 0) == 2:
        for i in range(3):
            if diag2[i] == 0:
                threats.append((i, 2-i))
    
    # If there are threat moves, pick one from them
    if threats:
        # Pick one threat move (prefer center or corner if possible)
        for move in threats:
            if move == (1, 1):  # center
                return move
        for move in threats:
            if move in [(0,0), (0,2), (2,0), (2,2)]:  # corner
                return move
        return threats[0]  # fallback to first threat
    
    # If no immediate win or threat, prioritize center, then corners, then edges
    priority_moves = [(1,1)]  # center
    priority_moves.extend([(0,0), (0,2), (2,0), (2,2)])  # corners
    priority_moves.extend([(0,1), (1,0), (1,2), (2,1)])  # edges
    
    # Find first priority move that is still available
    for move in priority_moves:
        if move in possible_moves:
            return move
    
    # Fallback: pick any legal move (should never reach here if game state is valid)
    return possible_moves[0]
