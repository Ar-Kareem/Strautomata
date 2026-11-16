
import random
import numpy as np

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Convert to sets for fast lookup
    me_set = set(me)
    opponent_set = set(opponent)
    
    # Create board representation to help with calculations
    board = np.zeros((19, 19), dtype=int)
    for r, c in me_set:
        board[r-1, c-1] = 1  # My stones
    for r, c in opponent_set:
        board[r-1, c-1] = 2  # Opponent stones
    
    def get_liberties(stones):
        """Get liberties of a group of stones"""
        liberties = set()
        for r, c in stones:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                    liberties.add((nr, nc))
        return liberties
    
    def get_group(r, c):
        """Get all stones in the group connected to (r,c)"""
        if board[r, c] == 0:
            return set()
        color = board[r, c]
        group = set()
        stack = [(r, c)]
        while stack:
            r, c = stack.pop()
            if (r, c) in group:
                continue
            group.add((r, c))
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < 19 and 0 <= nc < 19 and 
                    board[nr, nc] == color and (nr, nc) not in group):
                    stack.append((nr, nc))
        return group
    
    def is_legal(r, c):
        """Check if a move is legal"""
        if board[r, c] != 0:
            return False
        
        # Make temporary move
        board[r, c] = 1  # My color
        
        # Check if this move captures any opponent stones
        captured = set()
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 2:
                group = get_group(nr, nc)
                liberties = get_liberties(group)
                if len(liberties) == 0:
                    captured.update(group)
        
        # Check if our own group has liberties
        if captured:  # If captured opponent stones, our group will have liberties
            board[r, c] = 0
            return True
        
        # Temporarily place the stone and check liberties
        group = get_group(r, c)
        liberties = get_liberties(group)
        board[r, c] = 0  # Restore board
        
        if len(liberties) > 0:
            return True
        # Check the capture case again
        board[r, c] = 1
        liberties = get_liberties(group)
        board[r, c] = 0
        return len(liberties) > 0
    
    # Check if we can capture opponent stones
    for r in range(19):
        for c in range(19):
            if board[r, c] == 0:  # Empty spot
                # Simulate placing a stone and see if we can capture
                board[r, c] = 1
                captured = False
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 2:
                        group = get_group(nr, nc)
                        liberties = get_liberties(group)
                        if len(liberties) == 0:
                            board[r, c] = 0
                            return (r+1, c+1)  # Return move that captures
                board[r, c] = 0
    
    # If can't capture immediately, check for defensive moves
    # Check if opponent can win with immediate capture
    for r in range(19):
        for c in range(19):
            if board[r, c] == 0:  # Empty spot
                # Check if this spot is where opponent can capture me
                board[r, c] = 2  # Opponent's stone temporarily
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 1:
                        group = get_group(nr, nc)
                        liberties = get_liberties(group)
                        if len(liberties) == 0:
                            board[r, c] = 0
                            return (r+1, c+1)  # Block the capture
                board[r, c] = 0
    
    # Otherwise, try to prioritize moves in corners and sides
    corners = [(1,1), (1,19), (19,1), (19,19)]
    sides = [(1,10), (10,1), (10,19), (19,10)]
    
    # Try valid corner moves
    for r, c in corners:
        if is_legal(r-1, c-1):
            return (r, c)
    
    # Try valid side moves
    for r, c in sides:
        if is_legal(r-1, c-1):
            return (r, c)
    
    # If not in opening, play more central moves
    for r in range(7, 12):
        for c in range(7, 12):
            if is_legal(r-1, c-1):
                return (r, c)
    
    # Play somewhere that looks good for territorial expansion
    for r in range(19):
        for c in range(19):
            if is_legal(r, c):
                return (r+1, c+1)
    
    # If no valid moves, pass
    return (0, 0)
