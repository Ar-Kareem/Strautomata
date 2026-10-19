
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Define all possible winning lines (rows, columns, diagonals)
    lines = [
        [(0,0), (0,1), (0,2), (0,3)],
        [(1,0), (1,1), (1,2), (1,3)],
        [(2,0), (2,1), (2,2), (2,3)],
        [(3,0), (3,1), (3,2), (3,3)],
        [(0,0), (1,0), (2,0), (3,0)],
        [(0,1), (1,1), (2,1), (3,1)],
        [(0,2), (1,2), (2,2), (3,2)],
        [(0,3), (1,3), (2,3), (3,3)],
        [(0,0), (1,1), (2,2), (3,3)],
        [(0,3), (1,2), (2,1), (3,0)]
    ]
    
    # Check for winning moves
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:  # Empty cell
                # Check if placing 1 here wins the game
                for line in lines:
                    if (i, j) in line:
                        count = [0, 0, 0]  # [empty, my_mark, opponent_mark]
                        for coord in line:
                            count[board[coord[0]][coord[1]]] += 1
                        if count[1] == 3 and count[0] == 1:
                            return (i, j)
    
    # Check for blocking moves
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:  # Empty cell
                for line in lines:
                    if (i, j) in line:
                        count = [0, 0, 0]  # [empty, my_mark, opponent_mark]
                        for coord in line:
                            count[board[coord[0]][coord[1]]] += 1
                        if count[2] == 3 and count[0] == 1:
                            return (i, j)
    
    # Evaluate board positions using heuristic scoring
    best_score = -float('inf')
    best_move = None
    
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:  # Empty cell
                score = 0
                # Check all lines containing (i, j)
                for line in lines:
                    if (i, j) in line:
                        count = [0, 0, 0]  # [empty, my_mark, opponent_mark]
                        for coord in line:
                            count[board[coord[0]][coord[1]]] += 1
                        # Add points for potential threats
                        if count[1] == 2 and count[0] == 1:
                            score += 10
                        if count[2] == 2 and count[0] == 1:
                            score -= 10
                # Prioritize center and corners
                if (i == 1 or i == 2) and (j == 1 or j == 2):
                    score += 5
                elif i == 0 or i == 3 or j == 0 or j == 3:
                    score += 3
                # Choose highest-scoring move
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move
