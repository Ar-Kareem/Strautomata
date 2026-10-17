
import time
import math
import random

def policy(board) -> str:
    """
    Monte Carlo Tree Search (MCTS) based policy for Lines of Action.
    Uses heuristic evaluation for rollouts to save time and increase depth.
    """
    # Configuration
    time_limit = 0.95  # Seconds
    max_iterations = 5000
    
    # State Representation
    # board is 8x8 list of ints
    # 0: empty, 1: player (us), -1: opponent

    # --- Helper Functions ---

    def get_legal_moves(b, player):
        moves = []
        rows = range(8)
        cols = range(8)
        
        # Directions: (dr, dc)
        directions = [
            (0, 1), (0, -1), (1, 0), (-1, 0),  # Orthogonal
            (1, 1), (1, -1), (-1, 1), (-1, -1) # Diagonal
        ]
        
        for r in rows:
            for c in cols:
                if b[r][c] == player:
                    # Count pieces in lines
                    row_count = sum(1 for x in b[r] if x != 0)
                    col_count = sum(1 for x in [b[i][c] for i in rows] if x != 0)
                    
                    # Diagonals
                    # Main diag (r-c constant)
                    diag1_count = 0
                    for i in range(8):
                        if 0 <= r + i < 8 and 0 <= c + i < 8 and b[r+i][c+i] != 0:
                            diag1_count += 1
                        if 0 <= r - i < 8 and 0 <= c - i < 8 and b[r-i][c-i] != 0:
                            diag1_count += 1
                    diag1_count //= 2 # counted center twice if valid
                    
                    # Anti-diag (r+c constant)
                    diag2_count = 0
                    for i in range(8):
                        if 0 <= r + i < 8 and 0 <= c - i < 8 and b[r+i][c-i] != 0:
                            diag2_count += 1
                        if 0 <= r - i < 8 and 0 <= c + i < 8 and b[r-i][c+i] != 0:
                            diag2_count += 1
                    diag2_count //= 2

                    # Unique counts per direction
                    counts = { (0,1): row_count, (0,-1): row_count, 
                               (1,0): col_count, (-1,0): col_count,
                               (1,1): diag1_count, (-1,-1): diag1_count,
                               (1,-1): diag2_count, (-1,1): diag2_count }

                    for dr, dc in directions:
                        dist = counts[(dr, dc)]
                        if dist == 0: continue
                        
                        nr, nc = r + dr * dist, c + dc * dist
                        
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            # Check path for enemies
                            blocked = False
                            steps = 1
                            while steps < dist:
                                tr, tc = r + dr * steps, c + dc * steps
                                if b[tr][tc] == -player: # Enemy piece
                                    blocked = True
                                    break
                                steps += 1
                            
                            if not blocked:
                                # Valid move if empty or enemy (capture)
                                # Note: Self capture is impossible with valid rules, 
                                # but if dist=0 it wouldn't be here.
                                if b[nr][nc] != player:
                                    moves.append(((r, c), (nr, nc)))
        return moves

    def apply_move(b, move, player):
        new_b = [row[:] for row in b]
        (r1, c1), (r2, c2) = move
        new_b[r1][c1] = 0
        new_b[r2][c2] = player
        return new_b

    def is_win(b, player):
        # Check if all player pieces are connected (8-directional)
        visited = set()
        pieces = []
        for r in range(8):
            for c in range(8):
                if b[r][c] == player:
                    pieces.append((r, c))
        
        if not pieces:
            return False # No pieces means not connected (usually)
        
        # BFS/DFS to find connected components
        count = 0
        for start in pieces:
            if start in visited:
                continue
            count += 1
            if count > 1:
                # Optimization: If we already found 2 components, we know we didn't win
                # But wait, we need to check the opponent too? 
                # No, this is just for win check.
                pass
            
            stack = [start]
            visited.add(start)
            while stack:
                curr_r, curr_c = stack.pop()
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0: continue
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            if b[nr][nc] == player and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                stack.append((nr, nc))
        
        return count == 1

    def get_components_count(b, player):
        visited = set()
        pieces = []
        for r in range(8):
            for c in range(8):
                if b[r][c] == player:
                    pieces.append((r, c))
        
        if not pieces: return 0
        
        components = 0
        for start in pieces:
            if start in visited: continue
            components += 1
            stack = [start]
            visited.add(start)
            while stack:
                curr_r, curr_c = stack.pop()
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0: continue
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            if b[nr][nc] == player and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                stack.append((nr, nc))
        return components

    def count_pieces(b, player):
        c = 0
        for r in range(8):
            for c_col in range(8):
                if b[r][c_col] == player:
                    c += 1
        return c

    def heuristic(b, player):
        # Returns a score from the perspective of 'player'
        # Win/Loss
        if is_win(b, player): return 10000
        if is_win(b, -player): return -10000
        
        # Connectivity: Minimize number of components (maximize connectedness)
        # 1 component is best (score +1), many is bad.
        # We want to maximize our connectivity (negative components) 
        # and minimize opponent connectivity (positive components relative to us)
        
        my_comp = get_components_count(b, player)
        opp_comp = get_components_count(b, -player)
        
        # Piece difference
        my_pieces = count_pieces(b, player)
        opp_pieces = count_pieces(b, -player)
        
        # Heuristic value:
        # We want Low My Components (-my_comp)
        # We want High Opp Components (+opp_comp)
        # We want More Pieces (+my_pieces)
        
        score = (-my_comp * 5) + (opp_comp * 5) + (my_pieces - opp_pieces)
        
        return score

    # --- MCTS Node Class ---
    class Node:
        def __init__(self, state, parent=None, move=None):
            self.state = state
            self.parent = parent
            self.move = move
            self.children = []
            self.wins = 0
            self.visits = 0
            self.untried_moves = get_legal_moves(state, 1) # Assuming we are '1' in simulation
            self.player = 1 # The player who makes the move to reach this state

    def mcts_search(root_state):
        root = Node(root_state)
        start_time = time.time()
        
        iterations = 0
        while (time.time() - start_time < time_limit) and (iterations < max_iterations):
            # 1. Selection
            node = root
            while node.untried_moves == [] and node.children != []:
                # UCB1
                best_score = -float('inf')
                best_child = None
                
                for child in node.children:
                    # Standard UCB1: w/n + c * sqrt(ln(N) / n)
                    # c usually sqrt(2)
                    if child.visits == 0:
                        ucb = float('inf')
                    else:
                        exploit = child.wins / child.visits
                        # Exploration term
                        explore = math.sqrt(2 * math.log(node.visits) / child.visits)
                        ucb = exploit + explore
                    
                    if ucb > best_score:
                        best_score = ucb
                        best_child = child
                node = best_child
            
            # 2. Expansion
            if node.untried_moves != []:
                move = random.choice(node.untried_moves)
                node.untried_moves.remove(move)
                new_state = apply_move(node.state, move, 1) # 1 is player in simulation
                child = Node(new_state, parent=node, move=move)
                node.children.append(child)
                node = child
            
            # 3. Simulation (Rollout / Evaluation)
            # Instead of random rollout, we use the heuristic evaluation on the current state
            # This is effectively "depth 1" search with a strong evaluation function
            # It's much faster than full random rollouts
            state = node.state
            
            # Check if terminal
            if is_win(state, 1):
                result = 1 # Win
            elif is_win(state, -1):
                result = -1 # Loss
            else:
                # Heuristic score mapping
                # Normalize heuristic to roughly [-1, 1] range if possible, or just raw
                h = heuristic(state, 1)
                # Map h to [-1, 1] roughly. 
                # If h > 0, player is winning. If h < 0, losing.
                # Let's use sigmoid-like scaling or just sign.
                # Given the heuristic returns up to 10000, using tanh is good.
                result = math.tanh(h / 20.0)
            
            # 4. Backpropagation
            curr = node
            while curr is not None:
                curr.visits += 1
                curr.wins += result
                curr = curr.parent
                result = -result # Switch perspective for parent
            
            iterations += 1
            
        # Best move selection: Highest visits (robust) or Highest avg score
        # Highest visits is usually safer for stability
        if not root.children:
            # Should not happen unless no moves, but handle gracefully
            moves = get_legal_moves(board, 1)
            if moves:
                m = random.choice(moves)
                return f"{m[0][0]},{m[0][1]}:{m[1][0]},{m[1][1]}"
            else:
                # No moves? Game over?
                return "0,0:0,0" 

        best_child = max(root.children, key=lambda c: c.visits)
        return best_child.move

    # --- Main Execution ---
    # Determine our player color (1 or -1)
    # The board is passed, we need to identify if we are 1 or -1.
    # The problem says "You are always the player to move", and board has 1 as current player.
    # So we are always 1.
    move = mcts_search(board)
    
    (r1, c1), (r2, c2) = move
    return f"{r1},{c1}:{r2},{c2}"
