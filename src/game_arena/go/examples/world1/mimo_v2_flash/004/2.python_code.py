
import time
import random
import math
import numpy as np

# Constants for board size and encoding
BOARD_SIZE = 19
TOTAL_POINTS = BOARD_SIZE * BOARD_SIZE
EMPTY = 0
ME = 1
OPP = 2
PASS = (0, 0)

# Bitmasks for board encoding (approximate for optimization)
# 19x19 fits easily into standard integers if we use bitboards, 
# but for simplicity and standard library compatibility, we use a flattened array or bit-integers.
# Here we use a flattened numpy array for speed in Python.

class FastBoard:
    __slots__ = ('board', 'me_stones', 'opp_stones', 'hash_val')
    
    def __init__(self, board=None, me_list=None, opp_list=None):
        if board is not None:
            self.board = board.copy()
            self.me_stones = set(me_list) if me_list else set()
            self.opp_stones = set(opp_list) if opp_list else set()
            self.hash_val = 0 # Placeholder for hash
        else:
            self.board = np.zeros(TOTAL_POINTS, dtype=np.int8)
            self.me_stones = set()
            self.opp_stones = set()
            self.hash_val = 0

    def copy(self):
        return FastBoard(self.board, self.me_stones, self.opp_stones)

    def idx(self, r, c):
        return (r - 1) * BOARD_SIZE + (c - 1)

    def rc(self, idx):
        return (idx // BOARD_SIZE + 1, idx % BOARD_SIZE + 1)

    def place_stone(self, r, c, player):
        idx = self.idx(r, c)
        if player == ME:
            self.board[idx] = ME
            self.me_stones.add(idx)
        else:
            self.board[idx] = OPP
            self.opp_stones.add(idx)

    def get_neighbors(self, r, c):
        n = []
        if r > 1: n.append((r - 1, c))
        if r < BOARD_SIZE: n.append((r + 1, c))
        if c > 1: n.append((r, c - 1))
        if c < BOARD_SIZE: n.append((r, c + 1))
        return n

    def get_group(self, r, c, player):
        stack = [(r, c)]
        visited = set()
        group = set()
        liberties = set()
        
        target = ME if player == ME else OPP
        
        while stack:
            cr, cc = stack.pop()
            c_idx = self.idx(cr, cc)
            if c_idx in visited:
                continue
            visited.add(c_idx)
            
            if self.board[c_idx] == target:
                group.add(c_idx)
                for nr, nc in self.get_neighbors(cr, cc):
                    n_idx = self.idx(nr, nc)
                    if self.board[n_idx] == EMPTY:
                        liberties.add(n_idx)
                    else:
                        if n_idx not in visited:
                            stack.append((nr, nc))
        
        return group, liberties

    def is_valid_move(self, r, c, player):
        idx = self.idx(r, c)
        if idx in self.me_stones or idx in self.opp_stones:
            return False
        
        # Check suicide
        temp_board = self.copy()
        temp_board.place_stone(r, c, player)
        
        # Check if capture occurs (saving from suicide)
        opp = OPP if player == ME else ME
        opp_stones = temp_board.opp_stones if player == ME else temp_board.me_stones
        
        # Check neighbors for capture
        captured = False
        for nr, nc in self.get_neighbors(r, c):
            n_idx = temp_board.idx(nr, nc)
            if temp_board.board[n_idx] == opp:
                g, l = temp_board.get_group(nr, nc, opp)
                if len(l) == 0:
                    captured = True
                    break
        
        if captured:
            return True
            
        # If no capture, check own liberties
        g, l = temp_board.get_group(r, c, player)
        if len(l) == 0:
            return False # Suicide
            
        return True

    def get_legal_moves(self, player):
        moves = []
        occupied = self.me_stones.union(self.opp_stones)
        
        # Optimization: Check random spots first if board is dense, else check all
        # But for MCTS, we usually generate all legal moves or a heuristic subset
        
        # Simple scanning
        for idx in range(TOTAL_POINTS):
            if idx in occupied:
                continue
            r, c = self.rc(idx)
            if self.is_valid_move(r, c, player):
                moves.append((r, c))
        return moves

    def evaluate_score(self):
        # Heuristic evaluation for end of simulation
        # Counts territory + stones
        me_score = len(self.me_stones)
        opp_score = len(self.opp_stones)
        
        # Add simple territory estimation (flood fill)
        # This is expensive, so we approximate by checking empty spots adjacent to stones
        visited_empty = set()
        for idx in range(TOTAL_POINTS):
            if self.board[idx] == EMPTY and idx not in visited_empty:
                # Start flood fill
                region = set()
                queue = [idx]
                border = {ME, OPP}
                
                is_me = False
                is_opp = False
                
                while queue:
                    curr = queue.pop()
                    if curr in visited_empty:
                        continue
                    visited_empty.add(curr)
                    region.add(curr)
                    
                    cr, cc = self.rc(curr)
                    for nr, nc in self.get_neighbors(cr, cc):
                        n_idx = self.idx(nr, nc)
                        val = self.board[n_idx]
                        if val == EMPTY:
                            if n_idx not in visited_empty:
                                queue.append(n_idx)
                        elif val == ME:
                            is_me = True
                        elif val == OPP:
                            is_opp = True
                
                if is_me and not is_opp:
                    me_score += len(region)
                elif is_opp and not is_me:
                    opp_score += len(region)
                    
        return me_score - opp_score

# MCTS Node
class Node:
    __slots__ = ('wins', 'visits', 'children', 'parent', 'move', 'untried_moves', 'player_moved')
    
    def __init__(self, parent=None, move=None, player=None):
        self.wins = 0
        self.visits = 0
        self.children = []
        self.parent = parent
        self.move = move # The move that led to this node
        self.untried_moves = None
        self.player_moved = player # Who moved to get here? (The opponent of the node's perspective usually, but here simple)

def ucb1(node, explore=1.414):
    if node.visits == 0:
        return float('inf')
    return (node.wins / node.visits) + explore * math.sqrt(math.log(node.parent.visits) / node.visits)

def get_policy_move(board, player):
    # Heuristic move prioritization for the root
    moves = board.get_legal_moves(player)
    if not moves:
        return PASS
    
    # Sort moves by simple heuristic to reduce MCTS branching
    scored_moves = []
    
    for r, c in moves:
        score = 0
        idx = board.idx(r, c)
        
        # 1. Capture potential
        opp = OPP if player == ME else ME
        for nr, nc in board.get_neighbors(r, c):
            n_idx = board.idx(nr, nc)
            if board.board[n_idx] == opp:
                # Check liberties of opponent group
                g, l = board.get_group(nr, nc, opp)
                if len(l) == 1: # About to capture
                    score += 100
                elif len(l) == 2:
                    score += 20
        
        # 2. Self liberties
        temp_board = board.copy()
        temp_board.place_stone(r, c, player)
        g, l = temp_board.get_group(r, c, player)
        if len(l) >= 3:
            score += 5
        elif len(l) == 1:
            score -= 10 # Risky
            
        # 3. Connection
        for nr, nc in board.get_neighbors(r, c):
            n_idx = board.idx(nr, nc)
            if board.board[n_idx] == player:
                score += 5
                
        scored_moves.append((score, (r, c)))
    
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    # Return top moves (limit branching factor to ~10-15 for speed)
    return [m for s, m in scored_moves[:15]]

def simulate_rollout(board, player):
    # Fast simulation with pattern heuristic
    current_player = player
    passes = 0
    steps = 0
    
    # Ko prevention (simple hash set)
    seen_hashes = set()
    
    while steps < 200: # Limit rollout length for speed
        moves = board.get_legal_moves(current_player)
        if not moves:
            passes += 1
            if passes >= 2:
                break
            current_player = OPP if current_player == ME else ME
            continue
        passes = 0
        
        # Greedy selection for rollout
        best_move = None
        best_score = -1
        
        # Check for direct captures first (strong heuristic)
        for r, c in moves:
            idx = board.idx(r, c)
            opp = OPP if current_player == ME else ME
            
            # Check capture
            for nr, nc in board.get_neighbors(r, c):
                n_idx = board.idx(nr, nc)
                if board.board[n_idx] == opp:
                    g, l = board.get_group(nr, nc, opp)
                    if len(l) == 1: # Capture!
                        best_move = (r, c)
                        break
            if best_move:
                break
                
        if not best_move:
            # If no capture, pick random move from top heuristics
            scored = []
            for r, c in moves:
                s = 0
                # Liberty count
                temp = board.copy()
                temp.place_stone(r, c, current_player)
                _, libs = temp.get_group(r, c, current_player)
                s += len(libs)
                # Random component to diversify
                s += random.random() 
                scored.append((s, (r, c)))
            scored.sort(key=lambda x: x[0], reverse=True)
            best_move = scored[0][1]
            
        board.place_stone(best_move[0], best_move[1], current_player)
        current_player = OPP if current_player == ME else ME
        steps += 1
        
    return board.evaluate_score()

def mcts_policy(me, opponent):
    board = FastBoard()
    for r, c in me:
        board.place_stone(r, c, ME)
    for r, c in opponent:
        board.place_stone(r, c, OPP)
        
    # Get heuristic moves for root
    root_moves = get_policy_move(board, ME)
    
    if not root_moves:
        return PASS
    
    # If only one move, play it
    if len(root_moves) == 1:
        return root_moves[0]
        
    # MCTS Initialization
    root = Node(player=OPP) # Parent of root is Opponent
    root.untried_moves = root_moves
    
    time_limit = 0.85 # Seconds (leave buffer for overhead)
    start_time = time.time()
    
    iterations = 0
    while time.time() - start_time < time_limit:
        node = root
        temp_board = board.copy()
        
        # 1. Selection
        while node.untried_moves is None and node.children:
            node = max(node.children, key=lambda n: ucb1(n))
            temp_board.place_stone(node.move[0], node.move[1], ME if node.player_moved == ME else OPP)
            
        # 2. Expansion
        if node.untried_moves:
            move = random.choice(node.untried_moves)
            node.untried_moves.remove(move)
            
            # Determine who is moving
            # Root is just before ME moves. 
            # Actually, input `me` is stones I already have. I am moving NOW.
            # So the first move in the tree is ME.
            # But MCTS logic usually assumes node stores who moved to get there.
            
            # Let's determine turn at this node.
            # We need to calculate turn based on depth or stored value.
            # Easier: Pass turn down.
            current_turn = ME
            if node == root:
                current_turn = ME
            else:
                # Traverse back to find turn logic? Or just track it.
                # Let's track it in the loop.
                pass
            
            # Correct Logic:
            # We are at `node`. The board state reflects moves up to `node`.
            # Who moves next?
            # If node.player_moved == ME, next is OPP. If OPP, next is ME.
            next_player = OPP if node.player_moved == ME else ME
            if node == root: next_player = ME
            
            new_node = Node(parent=node, move=move, player=next_player)
            
            # Handle turn tracking properly
            # The board currently has stones. We are adding `move`.
            # If we are at root, ME moves.
            # If we selected a child, that child's `move` was played by `child.player_moved`.
            # So for the new child, we need to know who plays now.
            
            # Let's reset the turn logic for clarity.
            # State S at node. 
            # If node == root: ME to play.
            # If node != root: (Opponent of node.player_moved) to play.
            
            player_to_move = ME if node == root else (OPP if node.player_moved == ME else ME)
            new_node.player_moved = player_to_move
            
            node.children.append(new_node)
            node = new_node
            temp_board.place_stone(move[0], move[1], player_to_move)
            
        # 3. Simulation
        # The turn is now for the opponent of the node just selected/expanded
        # If we expanded, `node` is the new node. `node.player_moved` is the one who just moved.
        # So next player is opponent.
        sim_player = OPP if node.player_moved == ME else ME
        
        # If we didn't expand (fully expanded tree), `node` is the one we selected.
        # The turn is for the opponent of who moved to get there.
        if not node.children and not node.untried_moves:
             sim_player = OPP if node.player_moved == ME else ME
        
        # Perform rollout
        # Note: We need a copy of the board for the rollout
        roll_board = temp_board.copy()
        score = simulate_rollout(roll_board, sim_player)
        
        # 4. Backpropagation
        # Score > 0 means ME wins.
        # We backpropagate the result from the perspective of the player who moved at each node.
        current = node
        while current is not None:
            current.visits += 1
            if current.player_moved == ME:
                # If ME moved here, and result is positive for ME, it's good.
                current.wins += score
            else:
                # If OPP moved here, and result is positive for ME, it's bad for OPP.
                current.wins += -score
            current = current.parent
            
        iterations += 1
        
    # Select best move
    best_child = None
    max_visits = -1
    
    for child in root.children:
        if child.visits > max_visits:
            max_visits = child.visits
            best_child = child
            
    if best_child:
        return best_child.move
        
    # Fallback
    return root_moves[0]

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    try:
        return mcts_policy(me, opponent)
    except Exception:
        # Fallback for safety
        return (0, 0)
