
import sys
import time
import random
import math
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict, Set

# Increase recursion limit just in case, though we use iterative approaches
sys.setrecursionlimit(20000)

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    """
    MCTS-based Hex AI with parallel rollouts.
    """
    start_time = time.time()
    BOARD_SIZE = 11
    
    # --- 1. Board Initialization & Helpers ---
    
    # Flattened board representation: 0=empty, 1=me, 2=opp
    # Index = row * 11 + col
    board = [0] * (BOARD_SIZE * BOARD_SIZE)
    
    # Convert inputs to board state
    my_id = 1 if color == 'b' else 2
    opp_id = 2 if color == 'b' else 1
    
    for r, c in me:
        board[r * BOARD_SIZE + c] = my_id
    for r, c in opp:
        board[r * BOARD_SIZE + c] = opp_id
        
    # Neighbor offsets for a "pointy top" hex grid where:
    # (i, j) touches (i, j-1), (i, j+1), (i-1, j), (i-1, j+1), (i+1, j-1), (i+1, j)
    # The prompt describes: excluding (i-1, j-1) and (i+1, j+1)
    # Let's verify: 
    # Top: (i-1, j) and (i-1, j+1)
    # Bottom: (i+1, j-1) and (i+1, j)
    # Side: (i, j-1) and (i, j+1)
    NEIGHBORS = [
        (0, -1), (0, 1),   # Left, Right
        (-1, 0), (-1, 1),  # Top-Left, Top-Right
        (1, -1), (1, 0)    # Bottom-Left, Bottom-Right
    ]

    def get_idx(r, c):
        return r * BOARD_SIZE + c

    def get_neighbors(idx):
        r, c = divmod(idx, BOARD_SIZE)
        for dr, dc in NEIGHBORS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                yield nr * BOARD_SIZE + nc

    # --- 2. Game Logic (Win Check) ---
    
    # For Black (Top-Bottom): Check if connected Top (Row 0) to Bottom (Row 10)
    # For White (Left-Right): Check if connected Left (Col 0) to Right (Col 10)
    
    def check_win_fast(board_state, player_id, color_str):
        # BFS or DSU is better than DFS for graph connectivity to avoid recursion depth
        # Using a simple visited set and queue for BFS
        
        if color_str == 'b':
            # Check Top (0,*) to Bottom (10,*)
            # Add all Top row stones of player to queue
            queue = [c for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if r == 0 and board_state[r*BOARD_SIZE+c] == player_id]
            target_rows = {10 * BOARD_SIZE + c for c in range(BOARD_SIZE)}
            visited = set(queue)
        else:
            # Check Left (*,0) to Right (*,10)
            # Add all Left col stones of player to queue
            queue = [r * BOARD_SIZE for r in range(BOARD_SIZE) if board_state[r * BOARD_SIZE] == player_id]
            target_cols = {r * BOARD_SIZE + 10 for r in range(BOARD_SIZE)}
            visited = set(queue)
            
        while queue:
            curr = queue.pop(0)
            
            if color_str == 'b':
                if curr in target_rows:
                    return True
            else:
                if curr in target_cols:
                    return True
            
            for n in get_neighbors(curr):
                if board_state[n] == player_id and n not in visited:
                    visited.add(n)
                    queue.append(n)
        return False

    # --- 3. Move Ordering (Heuristic) ---
    
    def get_valid_moves():
        # Prioritize moves:
        # 1. Center (if empty)
        # 2. Adjacent to existing stones (My stones + Opp stones)
        # 3. Edges (strategic for connection)
        
        moves = []
        occupied = set()
        for r, c in me: occupied.add(r * BOARD_SIZE + c)
        for r, c in opp: occupied.add(r * BOARD_SIZE + c)
        
        # Calculate influence map (adjacent to any stone)
        influence = set()
        for idx in occupied:
            for n in get_neighbors(idx):
                if n not in occupied:
                    influence.add(n)
        
        # Generate candidates
        candidates = list(influence)
        
        # If very early game, ensure we explore center
        if not me and not opp:
            center = 5 * BOARD_SIZE + 5
            if center not in occupied:
                candidates.append(center)
                
        # Fill remaining empty spots if candidates < full board
        if len(candidates) < (BOARD_SIZE*BOARD_SIZE - len(occupied)):
            for i in range(BOARD_SIZE * BOARD_SIZE):
                if i not in occupied and i not in candidates:
                    candidates.append(i)
        
        return candidates

    candidates = get_valid_moves()
    if not candidates:
        return (0, 0) # Should not happen in valid game

    # If board is empty, play center immediately
    if len(me) == 0 and len(opp) == 0:
        return (5, 5)

    # --- 4. MCTS Implementation ---

    # Node structure: {idx: {'wins': float, 'visits': int, 'children': list}}
    # We use a flat dictionary for the tree to avoid class overhead
    tree_wins = {} # idx -> wins (from perspective of the player making the move at this node)
    tree_visits = {} # idx -> visits
    tree_children = {} # idx -> list of child indices
    
    # Lock for thread safety during tree updates
    tree_lock = threading.Lock()

    def uct_select(node_idx, total_visits, current_board_state):
        # Find best child using UCT
        # UCT = w_i / n_i + c * sqrt(ln(N) / n_i)
        # If node not visited, return it
        
        # Check if node has children generated
        if node_idx in tree_children:
            children = tree_children[node_idx]
            if not children:
                return None # No moves left (terminal state)
            
            best_score = -float('inf')
            best_child = -1
            
            for child_idx in children:
                # Check if child is valid on current board
                r, c = divmod(child_idx, BOARD_SIZE)
                if current_board_state[child_idx] != 0:
                    continue
                
                w = tree_wins.get(child_idx, 0)
                n = tree_visits.get(child_idx, 0)
                
                if n == 0:
                    # Unexplored node - high priority
                    return child_idx
                
                # Constant C (exploration factor). 1.41 is standard.
                # We adjust based on game phase or slightly favor exploitation
                c_val = 1.41
                
                # Score is for the player who played the move to reach this node.
                # In Hex, we alternate. We need to know whose turn it is at node_idx.
                # The tree tracks moves. The parent node is the state before the move.
                # So 'w' is the win rate for the player who made 'node_idx'.
                
                uct = (w / n) + c_val * math.sqrt(math.log(total_visits) / n)
                
                if uct > best_score:
                    best_score = uct
                    best_child = child_idx
            
            return best_child
            
        else:
            # Node has no children yet (or needs expansion)
            return None

    def expand(node_idx, current_board_state):
        # Generate legal moves for this node
        moves = []
        for i in range(BOARD_SIZE * BOARD_SIZE):
            if current_board_state[i] == 0:
                moves.append(i)
        
        if moves:
            with tree_lock:
                tree_children[node_idx] = moves
            return moves[0] # Return first move for immediate simulation if needed
        return None

    def simulate(initial_board_state, player_to_move_id):
        """
        Perform a random simulation from the current state.
        Returns 1 if player_to_move_id wins, 0 otherwise.
        """
        sim_board = list(initial_board_state)
        empty_cells = [i for i, x in enumerate(sim_board) if x == 0]
        
        # Heuristic: Shuffle but bias towards existing clusters?
        # Pure random is faster and valid for MCTS average.
        random.shuffle(empty_cells)
        
        current_player = player_to_move_id
        opp_player = 2 if player_to_move_id == 1 else 1
        
        # Determine which color is being simulated for win check
        # If player_to_move_id is 1 (Black), check 'b' win.
        # If player_to_move_id is 2 (White), check 'w' win.
        # Color mapping: 1 -> 'b', 2 -> 'w'
        check_color = 'b' if player_to_move_id == 1 else 'w'
        
        for idx in empty_cells:
            sim_board[idx] = current_player
            
            # Check win
            if check_win_fast(sim_board, current_player, check_color):
                return 1.0 # Current player wins
            
            # Switch player
            current_player = opp_player
            check_color = 'w' if check_color == 'b' else 'b'
            
        # Draw (should be rare in Hex, usually someone wins before board fills)
        return 0.5

    def mcts_worker(root_idx, root_board_state, my_pid):
        """
        One Monte Carlo iteration: Selection -> Expansion -> Simulation -> Backprop
        """
        path = [] # List of (node_idx, move_idx)
        curr_board = list(root_board_state)
        curr_node = root_idx
        current_player = my_pid
        
        # 1. Selection
        while True:
            # Check if node is terminal (no moves left)
            # We check if board is full implicitly by checking valid moves
            # For speed, we assume we only traverse valid paths
            
            # Check if we have expanded this node
            if curr_node in tree_children:
                # Select child
                next_node_idx = uct_select(curr_node, tree_visits.get(root_idx, 1), curr_board)
                
                if next_node_idx is not None:
                    # Move to child
                    # Update board state
                    # Check if move is actually valid on board (should be if tree is consistent)
                    r, c = divmod(next_node_idx, BOARD_SIZE)
                    if curr_board[next_node_idx] != 0:
                        # Collision (state desync?), break
                        return 0.5
                        
                    curr_board[next_node_idx] = current_player
                    
                    # Check immediate win
                    check_c = 'b' if current_player == 1 else 'w'
                    if check_win_fast(curr_board, current_player, check_c):
                        # We found a winning move path!
                        # Backpropagate win
                        with tree_lock:
                            # Update all nodes in path
                            for p_idx, _ in path:
                                tree_visits[p_idx] = tree_visits.get(p_idx, 0) + 1
                                # The player who played p_idx wins if the subsequent moves lead to win?
                                # Wait. In MCTS backprop:
                                # If we are at state S (after move A), and we simulate and win:
                                # Node A (representing the move) gets a win.
                                # Node S (parent of A) gets a win if S's player is the winner? 
                                # No. In standard MCTS, we backpropagate the result from the perspective of the root.
                                # Root is my turn. 
                                # Path: Root -> Move 1 (Me) -> Move 2 (Opp) ...
                                # If simulation wins for Me (at the end):
                                # Nodes played by Me get +1 win. Nodes played by Opp get +0 win.
                                
                            # Actually simpler:
                            # We just update the node corresponding to the winning move.
                            # The parent node sees that this child leads to a win.
                            
                            # Let's refine backprop logic below.
                            pass
                        
                        # We will handle the win update in the backprop section,
                        # but we need to know we won.
                        result = 1.0 # Perspective of root player (Me)
                        
                        # Backprop
                        with tree_lock:
                            # Update the leaf node (the winning move)
                            leaf_idx = next_node_idx
                            tree_visits[leaf_idx] = tree_visits.get(leaf_idx, 0) + 1
                            tree_wins[leaf_idx] = tree_wins.get(leaf_idx, 0) + result
                            
                            # Update parents
                            for p_idx, p_player in reversed(path):
                                tree_visits[p_idx] = tree_visits.get(p_idx, 0) + 1
                                # If p_player == my_pid, we add result. Else 1-result? 
                                # No, we always track win rate for the player who moved at p_idx.
                                # Wait, standard MCTS tracks value for the player to move at that node.
                                # If node is "Opponent's turn", we want to minimize our win probability.
                                # Or we can track "Win for Root Player".
                                # Let's track "Win for Root Player".
                                # But that requires knowing who is root.
                                # Let's track "Win for Current Node Player".
                                # If simulation result is from perspective of Root Player (Me).
                                
                                # If path step was Me (player_to_move was Me), add result.
                                # If path step was Opp, add (1 - result) because Opp winning means Me losing?
                                # No, result is 1 if Me won.
                                # If Opp moved at node X, and eventually Me won, then move X was bad for Opp (good for Me).
                                # So for node X (Opp's turn), we increment wins? 
                                # We usually flip the score for min-max trees or negate UCT.
                                # In UCT (bandits), usually W/N is kept as "Reward".
                                # If we play against ourselves (simulation), we treat it as a single player trying to win against the opponent.
                                # So if "Me" wins, all "Me" nodes get +1. All "Opp" nodes get +0.
                                
                                if p_player == my_pid:
                                    tree_wins[p_idx] = tree_wins.get(p_idx, 0) + result
                                # else: Opp node, we don't add to wins (or add 1-result if we track losses)
                                # Actually, to calculate UCT, we need win rate. 
                                # If Opp node has high win rate (for Opp), it's bad for Me.
                                # So for Opp node, we track "Win for Opp".
                                # UCT calculation uses w/n. If w is "Win for Player at node", then:
                                # For Me: w = wins.
                                # For Opp: w = wins.
                                # UCT formula doesn't care who plays, just maximizes reward.
                                # To make it work for 2 players:
                                # We backpropagate the raw simulation result (1 if Me won, 0 if Opp won).
                                # For Me nodes: Add result.
                                # For Opp nodes: Add (1 - result).
                                # This makes "w" the "Win rate for the player who moved at this node".
                                
                                if p_player == my_pid:
                                    tree_wins[p_idx] = tree_wins.get(p_idx, 0) + result
                                else:
                                    tree_wins[p_idx] = tree_wins.get(p_idx, 0) + (1 - result)

                        return

                    # Add to path
                    path.append((curr_node, next_node_idx))
                    curr_node = next_node_idx
                    current_player = 2 if current_player == 1 else 1
                    continue
                else:
                    # No child selected (terminal or all visited but no children generated yet?)
                    # If children exist but uct returned None, it means no valid moves?
                    # Or we need to expand.
                    break
            else:
                # Expand
                expand(curr_node, curr_board)
                # Pick the first child to simulate
                if curr_node in tree_children and tree_children[curr_node]:
                    next_node = tree_children[curr_node][0]
                    # Verify it's empty
                    if curr_board[next_node] == 0:
                        curr_board[next_node] = current_player
                        path.append((curr_node, next_node))
                        curr_node = next_node
                        current_player = 2 if current_player == 1 else 1
                        # Fall through to simulation
                    else:
                        return 0.5 # Invalid expansion
                else:
                    return 0.5 # No moves

        # 2. Simulation (from current state)
        # Determine whose turn it is at curr_board
        # current_player is the one to move now.
        sim_result = simulate(curr_board, current_player)
        
        # 3. Backpropagation
        with tree_lock:
            # Update leaf
            tree_visits[curr_node] = tree_visits.get(curr_node, 0) + 1
            # Leaf node: whose turn was it?
            # We switched current_player at the end of the loop.
            # So the move at curr_node was made by (2 if current_player==1 else 1)
            leaf_player = 2 if current_player == 1 else 1
            
            if leaf_player == my_pid:
                tree_wins[curr_node] = tree_wins.get(curr_node, 0) + sim_result
            else:
                tree_wins[curr_node] = tree_wins.get(curr_node, 0) + (1 - sim_result)

            # Update parents in path
            for p_idx, p_player in reversed(path):
                tree_visits[p_idx] = tree_visits.get(p_idx, 0) + 1
                if p_player == my_pid:
                    tree_wins[p_idx] = tree_wins.get(p_idx, 0) + sim_result
                else:
                    tree_wins[p_idx] = tree_wins.get(p_idx, 0) + (1 - sim_result)

    # --- 5. Execution ---

    # Root node ID is -1 (virtual)
    root_idx = -1
    tree_wins[root_idx] = 0
    tree_visits[root_idx] = 0
    
    # Generate initial children for root
    expand(root_idx, board)
    root_children = tree_children.get(root_idx, [])
    
    # Filter root children based on candidates (move ordering)
    # We only want to explore promising candidates at root to save time
    # candidates is a list of indices
    promising_children = [c for c in root_children if c in candidates]
    if promising_children:
        tree_children[root_idx] = promising_children
    
    # Time control
    # We have 1 second. Allocate 0.8s for MCTS, 0.2s overhead.
    time_limit = 0.8
    
    # Parallel Rollouts
    num_workers = 4 # Adjust based on CPU cores available in environment
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        while time.time() - start_time < time_limit:
            # Submit tasks
            if not futures:
                # Initial batch
                for _ in range(num_workers * 2):
                    futures.append(executor.submit(mcts_worker, root_idx, board, my_id))
            else:
                # Keep pool filled
                done, _ = as_completed(futures).__next__(), futures
                # Submit new one
                futures.append(executor.submit(mcts_worker, root_idx, board, my_id))
                
            # Check if we need to break early
            if time.time() - start_time > time_limit * 0.9:
                break

    # --- 6. Selection ---
    
    # Choose the child with the highest number of visits
    best_move = -1
    max_visits = -1
    
    children = tree_children.get(root_idx, [])
    for child in children:
        visits = tree_visits.get(child, 0)
        if visits > max_visits:
            max_visits = visits
            best_move = child
            
    # Fallback: if no visits (shouldn't happen), pick random valid
    if best_move == -1:
        best_move = random.choice(candidates)

    r, c = divmod(best_move, BOARD_SIZE)
    return (r, c)
