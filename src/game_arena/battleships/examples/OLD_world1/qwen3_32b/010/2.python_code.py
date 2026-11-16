
def policy(board: list[list[int]]) -> tuple[int, int]:
    # First, check for adjacent candidates to existing hits
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                # Check up, down, right, left in that order
                for dx, dy in [(-1, 0), (1, 0), (0, 1), (0, -1)]:
                    ni = i + dx
                    nj = j + dy
                    if 0 <= ni < 10 and 0 <= nj < 10:
                        if board[ni][nj] == 0:
                            return (ni, nj)
    
    # If no adjacent candidates, compute best cell based on probability matrix
    prob = [[0 for _ in range(10)] for _ in range(10)]
    ship_lengths = [5, 4, 3, 3, 2]
    
    for length in ship_lengths:
        # Check horizontal positions
        for i in range(10):
            max_j = 10 - length
            for j in range(0, max_j + 1):
                valid = True
                for k in range(length):
                    x, y = i, j + k
                    if board[x][y] == -1:
                        valid = False
                        break
                if valid:
                    for k in range(length):
                        x, y = i, j + k
                        prob[x][y] += 1
        
        # Check vertical positions
        for j in range(10):
            max_i = 10 - length
            for i in range(0, max_i + 1):
                valid = True
                for k in range(length):
                    x, y = i + k, j
                    if board[x][y] == -1:
                        valid = False
                        break
                if valid:
                    for k in range(length):
                        x, y = i + k, j
                        prob[x][y] += 1
    
    # Find cell with max probability that is not yet fired upon
    max_prob = -1
    best_i, best_j = 0, 0
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                if prob[i][j] > max_prob:
                    max_prob = prob[i][j]
                    best_i, best_j = i, j
    
    return (best_i, best_j)
