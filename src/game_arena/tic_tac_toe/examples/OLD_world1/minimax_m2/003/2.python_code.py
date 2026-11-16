
memo = {}

def state_value(state):
    if state in memo:
        return memo[state]
    
    for i in range(3):
        row_sum = state[3*i] + state[3*i+1] + state[3*i+2]
        if row_sum == 3:
            memo[state] = 1
            return 1
        if row_sum == -3:
            memo[state] = -1
            return -1
            
    for j in range(3):
        col_sum = state[j] + state[j+3] + state[j+6]
        if col_sum == 3:
            memo[state] = 1
            return 1
        if col_sum == -3:
            memo[state] = -1
            return -1
            
    diag1_sum = state[0] + state[4] + state[8]
    if diag1_sum == 3:
        memo[state] = 1
        return 1
    if diag1_sum == -3:
        memo[state] = -1
        return -1
        
    diag2_sum = state[2] + state[4] + state[6]
    if diag2_sum == 3:
        memo[state] = 1
        return 1
    if diag2_sum == -3:
        memo[state] = -1
        return -1
        
    if 0 not in state:
        memo[state] = 0
        return 0
        
    count1 = state.count(1)
    count_minus1 = state.count(-1)
    
    if count1 == count_minus1:
        current_player = 1
    else:
        current_player = -1
        
    next_states = []
    for i in range(9):
        if state[i] == 0:
            next_state = list(state)
            next_state[i] = current_player
            next_state = tuple(next_state)
            next_states.append(next_state)
            
    values = []
    for ns in next_states:
        values.append(state_value(ns))
        
    if current_player == 1:
        best = max(values)
    else:
        best = min(values)
        
    memo[state] = best
    return best

def policy(board: list[list[int]]) -> tuple[int, int]:
    flat_board = (board[0][0], board[0][1], board[0][2],
                  board[1][0], board[1][1], board[1][2],
                  board[2][0], board[2][1], board[2][2])
                  
    count1 = flat_board.count(1)
    count_minus1 = flat_board.count(-1)
    
    if count1 != count_minus1:
        for i in range(9):
            if flat_board[i] == 0:
                return (i // 3, i % 3)
        return (0, 0)
        
    terminal = False
    for i in range(3):
        row_sum = flat_board[3*i] + flat_board[3*i+1] + flat_board[3*i+2]
        if row_sum == 3 or row_sum == -3:
            terminal = True
            break
            
    if not terminal:
        for j in range(3):
            col_sum = flat_board[j] + flat_board[j+3] + flat_board[j+6]
            if col_sum == 3 or col_sum == -3:
                terminal = True
                break
                
    if not terminal:
        diag1_sum = flat_board[0] + flat_board[4] + flat_board[8]
        diag2_sum = flat_board[2] + flat_board[4] + flat_board[6]
        if diag1_sum == 3 or diag1_sum == -3 or diag2_sum == 3 or diag2_sum == -3:
            terminal = True
            
    if not terminal:
        if 0 not in flat_board:
            terminal = True
            
    if terminal:
        for i in range(9):
            if flat_board[i] == 0:
                return (i // 3, i % 3)
        return (0, 0)
        
    best_move = None
    best_value = -2
    
    for i in range(9):
        if flat_board[i] == 0:
            next_state = list(flat_board)
            next_state[i] = 1
            next_state = tuple(next_state)
            value_next = state_value(next_state)
            if value_next > best_value:
                best_value = value_next
                best_move = (i // 3, i % 3)
                
    return best_move if best_move is not None else (0, 0)
