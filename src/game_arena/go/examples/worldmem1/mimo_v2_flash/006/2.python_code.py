
import numpy as np
import random
import time

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Constants
    BOARD_SIZE = 19
    EMPTY = 0
    ME = 1
    OPP = 2
    
    # Initialize Board
    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int8)
    for r, c in me:
        board[r-1, c-1] = ME
    for r, c in opponent:
        board[r-1, c-1] = OPP
        
    # --- Helper: Group Analysis (Union-Find) ---
    class GroupFinder:
        def __init__(self, board, player):
            self.board = board
            self.player = player
            self.parent = {}
            self.liberties = {}
            self.groups = {}
            self.checked = set()
            
        def find(self, pos):
            if self.parent[pos] != pos:
                self.parent[pos] = self.find(self.parent[pos])
            return self.parent[pos]
            
        def union(self, pos1, pos2):
            root1 = self.find(pos1)
            root2 = self.find(pos2)
            if root1 != root2:
                self.parent[root1] = root2
        
        def get_groups(self):
            # Scan board for player stones
            stones = np.argwhere(self.board == self.player)
            for r, c in stones:
                pos = (r, c)
                self.parent[pos] = pos
                self.liberties[pos] = set()
            
            # Union adjacent stones
            for r, c in self.parent.keys():
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                        if self.board[nr, nc] == self.player:
                            self.union((r, c), (nr, nc))
            
            # Calculate liberties
            for r, c in self.parent.keys():
                root = self.find((r, c))
                if root not in self.liberties:
                    self.liberties[root] = set()
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                        if self.board[nr, nc] == EMPTY:
                            self.liberties[root].add((nr, nc))
                        elif self.board[nr, nc] != self.player:
                            # Capturing move check handled elsewhere, liberty is not empty
                            pass
            
            # Group by root
            groups = {}
            for pos, root in self.parent.items():
                if root not in groups:
                    groups[root] = []
                groups[root].append(pos)
            return groups, self.liberties

    # --- Logic for Captures and Validity ---
    def get_groups_and_liberties(player_board, player_id):
        gf = GroupFinder(player_board, player_id)
        return gf.get_groups()

    def get_valid_moves(board, me_player, opp_player, ko_hash):
        # Returns list of (r, c)
        valid_moves = []
        my_groups, my_liberties = get_groups_and_liberties(board, me_player)
        
        # Determine candidates for efficiency
        candidates = []
        # 1. Moves that capture
        opp_groups, opp_liberties = get_groups_and_liberties(board, opp_player)
        for root, libs in opp_liberties.items():
            if len(libs) == 1:
                r, c = list(libs)[0]
                candidates.append((r, c, 'capture'))
        
        # 2. Moves that save my groups (atari defense)
        for root, libs in my_liberties.items():
            if len(libs) == 1:
                for r, c in libs:
                    candidates.append((r, c, 'defense'))
        
        # 3. Random moves in area (sparse sampling)
        # If less than 20 candidates, add random empty spots
        empty_spots = np.argwhere(board == EMPTY)
        if len(candidates) < 20 and len(empty_spots) > 0:
            indices = np.random.choice(len(empty_spots), min(50, len(empty_spots)), replace=False)
            for idx in indices:
                r, c = empty_spots[idx]
                candidates.append((int(r), int(c), 'random'))
        
        # Uniquify and validate
        seen = set()
        for r, c, type in candidates:
            if (r, c) in seen: continue
            seen.add((r, c))
            
            # Check Suicide
            # Temporarily place stone
            temp_board = board.copy()
            temp_board[r, c] = me_player
            
            # Check if capture happened
            # Neighbors
            captured = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if temp_board[nr, nc] == opp_player:
                        # Check liberties of this opponent group
                        opp_gf = GroupFinder(temp_board, opp_player)
                        opp_groups, opp_libs = opp_gf.get_groups()
                        # Find root of neighbor
                        root = opp_gf.find((nr, nc))
                        if root in opp_libs and len(opp_libs[root]) == 0:
                            captured = True
                            break
            
            if not captured:
                # If no capture, check own liberties
                my_gf = GroupFinder(temp_board, me_player)
                my_groups, my_libs = my_gf.get_groups()
                root = my_gf.find((r, c))
                if root in my_libs and len(my_libs[root]) == 0:
                    continue # Suicide
            
            # Check Ko
            new_hash = hash(temp_board.tobytes())
            if new_hash == ko_hash:
                continue
                
            valid_moves.append((r, c))
            
        if not valid_moves:
            return [(0, 0)] # Pass
            
        return valid_moves

    def simulate_game(board, move_r, move_c, me_player, opp_player):
        # Fast random simulation
        sim_board = board.copy()
        sim_board[move_r, move_c] = me_player
        current_player = opp_player
        passes = 0
        
        # Get all empty spots
        empty_spots = list(zip(*np.where(sim_board == EMPTY)))
        random.shuffle(empty_spots)
        
        for r, c in empty_spots:
            # Simple capture check (liberties) without full group rebuild every time
            # Optimized: just check neighbors
            is_valid = False
            # Check suicide/capture logic simplified for speed
            # We will use a simple heuristic: if neighbor is empty or opponent, likely valid
            # Strict check is safer but slower. Given random play, we approximate.
            # Let's do a slightly faster validity check:
            
            temp = sim_board.copy()
            temp[r, c] = current_player
            
            # Check if this move captures anything
            opp = 3 - current_player
            captured = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if temp[nr, nc] == opp:
                        # Check liberties of (nr, nc)
                        # We need a fast liberty check here.
                        # BFS/DFS limited
                        stack = [(nr, nc)]
                        visited = set([(nr, nc)])
                        liberties = 0
                        while stack:
                            cr, cc = stack.pop()
                            for dr2, dc2 in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                ncr, ncc = cr + dr2, cc + dc2
                                if 0 <= ncr < BOARD_SIZE and 0 <= ncc < BOARD_SIZE:
                                    if temp[ncr, ncc] == EMPTY:
                                        liberties += 1
                                        if liberties > 0: break # Optimization: we just need to know if > 0
                                    elif temp[ncr, ncc] == opp and (ncr, ncc) not in visited:
                                        visited.add((ncr, ncc))
                                        stack.append((ncr, ncc))
                            if liberties > 0: break
                        if liberties == 0:
                            captured = True
                            break
            
            if not captured:
                # Check suicide
                # Check liberties of (r, c)
                stack = [(r, c)]
                visited = set([(r, c)])
                liberties = 0
                while stack:
                    cr, cc = stack.pop()
                    for dr2, dc2 in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ncr, ncc = cr + dr2, cc + dc2
                        if 0 <= ncr < BOARD_SIZE and 0 <= ncc < BOARD_SIZE:
                            if temp[ncr, ncc] == EMPTY:
                                liberties += 1
                                if liberties > 0: break
                            elif temp[ncr, ncc] == current_player and (ncr, ncc) not in visited:
                                visited.add((ncr, ncc))
                                stack.append((ncr, ncc))
                    if liberties > 0: break
                if liberties == 0:
                    continue # Suicide
            
            # Apply move
            sim_board[r, c] = current_player
            current_player = opp
            passes = 0
            
        # Scoring (Area scoring)
        # Count empty spots connected to me vs opponent
        # Simplified: just count territory + stones
        score = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if sim_board[r, c] == ME:
                    score += 1
                elif sim_board[r, c] == OPP:
                    score -= 1
        return score

    # --- Main Policy Logic ---
    current_hash = hash(board.tobytes())
    prev_hash = memory.get('prev_hash')
    ko_hash = prev_hash if prev_hash else -1
    
    valid_moves = get_valid_moves(board, ME, OPP, ko_hash)
    
    # 1. Pass if no moves
    if len(valid_moves) == 1 and valid_moves[0] == (0, 0):
        return (0, 0), {'prev_hash': current_hash}
    
    # 2. Filter moves: Center potential
    # Calculate liberties of my groups to see game phase
    my_gf = GroupFinder(board, ME)
    _, my_libs = my_gf.get_groups()
    avg_libs = sum(len(l) for l in my_libs.values()) / len(my_libs) if my_libs else 10
    
    scores = []
    
    if avg_libs > 2:
        # Opening phase: Prioritize center influence
        for r, c in valid_moves:
            dist_center = abs(r - 9) + abs(c - 9)
            score = -dist_center # Closer to center is better
            scores.append((score, (r, c)))
        scores.sort(reverse=True)
        best_move = scores[0][1]
    else:
        # Tactical phase: MCTS
        best_score = -float('inf')
        best_move = valid_moves[0]
        
        # Limit candidates for MCTS to avoid timeout
        candidates = valid_moves
        if len(candidates) > 10:
            # Prioritize captures and defenses if available
            prioritized = []
            for r, c in candidates:
                if r == 0 and c == 0: continue
                # Heuristic check for capture/defense
                prioritized.append((r, c))
            candidates = prioritized[:10] # Take top 10 random
            if not candidates: candidates = valid_moves[:10]

        for r, c in candidates:
            if r == 0 and c == 0: 
                continue # Don't simulate pass unless forced
            
            # Run a few rollouts
            sim_score = 0
            sims = 5 # Keep low for time
            for _ in range(sims):
                sim_score += simulate_game(board, r, c, ME, OPP)
            
            if sim_score > best_score:
                best_score = sim_score
                best_move = (r, c)
        
    return best_move, {'prev_hash': current_hash}
