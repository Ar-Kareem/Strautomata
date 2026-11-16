
import numpy as np

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Create board representation
    board = np.zeros((19, 19), dtype=int)
    for (r, c) in me:
        board[r-1, c-1] = 1
    for (r, c) in opponent:
        board[r-1, c-1] = 2
    
    # Generate legal moves
    legal_moves = []
    for r in range(19):
        for c in range(19):
            if board[r, c] != 0:
                continue
            if is_legal_move(board, r, c, 1):
                legal_moves.append((r, c))
    legal_moves.append((0, 0))  # Pass
    
    # If no moves, pass
    if not legal_moves:
        return (0, 0)
    
    # Evaluate moves using Monte Carlo simulation
    best_move = None
    best_score = -float('inf')
    simulations = 100
    
    for move in legal_moves:
        wins = 0
        for _ in range(simulations):
            if simulate_game(board.copy(), move, 1):
                wins += 1
        win_rate = wins / simulations
        if win_rate > best_score:
            best_score = win_rate
            best_move = move
    
    return best_move

def is_legal_move(board, row, col, player):
    # Check if move is on board
    if row < 0 or row >= 19 or col < 0 or col >= 19:
        return False
    
    # Check if cell is empty
    if board[row, col] != 0:
        return False
    
    # Check for captures
    captures = check_captures(board, row, col, player)
    if captures:
        return True
    
    # Check for liberties
    liberties = check_liberties(board, row, col, player)
    return liberties > 0

def check_captures(board, row, col, player):
    # Check opponent stones to capture
    captures = 0
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    for dr, dc in directions:
        r, c = row + dr, col + dc
        if 0 <= r < 19 and 0 <= c < 19 and board[r, c] == 3 - player:
            # Check if opponent group has no liberties
            if check_liberties(board, r, c, 3 - player) == 0:
                captures += 1
    return captures

def check_liberties(board, row, col, player):
    # Count liberties of a stone
    liberties = 0
    visited = set()
    stack = [(row, col)]
    while stack:
        r, c = stack.pop()
        if (r, c) in visited:
            continue
        visited.add((r, c))
        if board[r, c] != player:
            continue
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board[nr, nc] == 0:
                    liberties += 1
                elif board[nr, nc] == player:
                    stack.append((nr, nc))
    return liberties

def simulate_game(board, move, player):
    # Simulate a game from current position
    current_board = board.copy()
    current_player = player
    
    # Make initial move
    if move != (0, 0):
        r, c = move
        current_board[r, c] = current_player
        # Check for captures
        captures = check_captures(current_board, r, c, current_player)
        if captures:
            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                for _ in range(captures):
                    r2, c2 = r + dr, c + dc
                    if 0 <= r2 < 19 and 0 <= c2 < 19 and current_board[r2, c2] == 3 - current_player:
                        current_board[r2, c2] = 0
    
    # Alternate turns until game ends
    while True:
        # Generate legal moves
        legal_moves = []
        for r in range(19):
            for c in range(19):
                if current_board[r, c] != 0:
                    continue
                if is_legal_move(current_board, r, c, current_player):
                    legal_moves.append((r, c))
        legal_moves.append((0, 0))
        
        # Check if current player has any legal moves
        if not legal_moves:
            # Pass to opponent
            current_player = 3 - current_player
            continue
        
        # Choose random legal move
        next_move = legal_moves[np.random.randint(len(legal_moves))]
        r, c = next_move
        
        # Make move
        current_board[r, c] = current_player
        captures = check_captures(current_board, r, c, current_player)
        if captures:
            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                for _ in range(captures):
                    r2, c2 = r + dr, c + dc
                    if 0 <= r2 < 19 and 0 <= c2 < 19 and current_board[r2, c2] == 3 - current_player:
                        current_board[r2, c2] = 0
        
        # Check if game should end
        if current_player == 1:
            # Check if opponent has moves
            opponent_moves = []
            for r in range(19):
                for c in range(19):
                    if current_board[r, c] != 0:
                        continue
                    if is_legal_move(current_board, r, c, 2):
                        opponent_moves.append((r, c))
            if not opponent_moves:
                # Game ends
                return True
        else:
            # Check if current player has moves
            current_moves = []
            for r in range(19):
                for c in range(19):
                    if current_board[r, c] != 0:
                        continue
                    if is_legal_move(current_board, r, c, 3 - current_player):
                        current_moves.append((r, c))
            if not current_moves:
                # Game ends
                return False
        
        # Switch player
        current_player = 3 - current_player
