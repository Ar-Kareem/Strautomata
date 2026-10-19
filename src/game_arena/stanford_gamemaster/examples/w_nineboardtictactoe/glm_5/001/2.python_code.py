
def policy(state: list[list[object]], role: str) -> str:
    import random
    
    boards = {}
    current_board = None
    
    for prop in state:
        if prop[0] == "cell":
            M, N, m, n, val = prop[1], prop[2], prop[3], prop[4], prop[5]
            key = (M, N)
            if key not in boards:
                boards[key] = {}
            boards[key][(m, n)] = val
        elif prop[0] == "current":
            current_board = (prop[1], prop[2])
    
    opponent = 'o' if role == 'x' else 'x'
    board = boards.get(current_board, {})
    
    empty_cells = []
    for m in ['1', '2', '3']:
        for n in ['1', '2', '3']:
            if board.get((m, n), 'b') == 'b':
                empty_cells.append((m, n))
    
    lines = [
        [('1','1'), ('1','2'), ('1','3')],
        [('2','1'), ('2','2'), ('2','3')],
        [('3','1'), ('3','2'), ('3','3')],
        [('1','1'), ('2','1'), ('3','1')],
        [('1','2'), ('2','2'), ('3','2')],
        [('1','3'), ('2','3'), ('3','3')],
        [('1','1'), ('2','2'), ('3','3')],
        [('1','3'), ('2','2'), ('3','1')],
    ]
    
    def find_winning_move(board_state, player):
        for line in lines:
            vals = [board_state.get(c, 'b') for c in line]
            if vals.count(player) == 2 and vals.count('b') == 1:
                return line[vals.index('b')]
        return None
    
    def count_threats(board_state, player):
        count = 0
        for line in lines:
            vals = [board_state.get(c, 'b') for c in line]
            if vals.count(player) == 2 and vals.count('b') == 1:
                count += 1
        return count
    
    # Priority 1: Win immediately
    move = find_winning_move(board, role)
    if move:
        return f"mark({current_board[0]},{current_board[1]},{move[0]},{move[1]})"
    
    # Priority 2: Block opponent's win
    move = find_winning_move(board, opponent)
    if move:
        return f"mark({current_board[0]},{current_board[1]},{move[0]},{move[1]})"
    
    # Priority 3: Create a fork
    for cell in empty_cells:
        new_board = dict(board)
        new_board[cell] = role
        if count_threats(new_board, role) >= 2:
            return f"mark({current_board[0]},{current_board[1]},{cell[0]},{cell[1]})"
    
    # Priority 4: Block opponent's fork
    for cell in empty_cells:
        new_board = dict(board)
        new_board[cell] = opponent
        if count_threats(new_board, opponent) >= 2:
            return f"mark({current_board[0]},{current_board[1]},{cell[0]},{cell[1]})"
    
    # Priority 5: Strategic evaluation
    best_moves = []
    best_score = -float('inf')
    
    for cell in empty_cells:
        target_board = boards.get(cell, {})
        score = 0
        
        # Don't send opponent to winning position
        if find_winning_move(target_board, opponent):
            score -= 10000
        elif find_winning_move(target_board, role):
            score += 500
        
        # Creating threats is good
        new_board = dict(board)
        new_board[cell] = role
        score += count_threats(new_board, role) * 50
        
        # Positional preference
        if cell == ('2', '2'):
            score += 25
        elif cell in [('1','1'), ('1','3'), ('3','1'), ('3','3')]:
            score += 15
        
        if score > best_score:
            best_score = score
            best_moves = [cell]
        elif score == best_score:
            best_moves.append(cell)
    
    if best_moves:
        move = random.choice(best_moves)
        return f"mark({current_board[0]},{current_board[1]},{move[0]},{move[1]})"
    
    if empty_cells:
        move = random.choice(empty_cells)
        return f"mark({current_board[0]},{current_board[1]},{move[0]},{move[1]})"
    
    return "mark(1,1,1,1)"
