
import time

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Kalah policy function.
    Returns the index (0-5) of the house to sow.
    """
    state = you + opponent
    solver = KalahSolver(state)
    return solver.get_best_move()

class KalahSolver:
    def __init__(self, board):
        # Board layout:
        # 0-5: Player houses
        # 6: Player store
        # 7-12: Opponent houses (from Player's perspective)
        # 13: Opponent store
        self.board = board
        self.start_time = 0
        # Time limit set to 0.9s to allow safe return within 1s
        self.time_limit = 0.90 
        self.nodes_visited = 0

    def get_best_move(self):
        self.start_time = time.time()
        
        # Identify legal moves
        legal_moves = [i for i in range(6) if self.board[i] > 0]
        if not legal_moves:
            return 0
        
        best_move = legal_moves[0]
        
        # Iterative Deepening
        # Start at depth 1 and increase until time runs out
        for depth in range(1, 25):
            try:
                move, value = self.search_root(self.board, depth)
                best_move = move
                
                # Optimization: If we found a winning path (score > 48 means huge win), stop
                if value > 40:
                    break
                    
                if time.time() - self.start_time > self.time_limit:
                    break
            except Exception:
                # Timeout occurred, return best move from previous completed depth
                break
                
        return best_move

    def check_time(self):
        self.nodes_visited += 1
        # Check time every 1024 nodes to reduce overhead
        if self.nodes_visited & 1023 == 0:
            if time.time() - self.start_time > self.time_limit:
                raise Exception("Timeout")

    def search_root(self, board, depth):
        legal = [i for i in range(6) if board[i] > 0]
        
        # Ordering: Try extra turn moves first
        ordered_moves = self.order_moves(board, legal)
        
        best_val = -float('inf')
        best_move = ordered_moves[0]
        alpha = -float('inf')
        beta = float('inf')
        
        for m in ordered_moves:
            self.check_time()
            new_board, extra, ended = self.simulate(board, m)
            
            if extra and not ended:
                # Extra turn: continue with same depth (or treated as update)
                val = self.alphabeta(new_board, depth, alpha, beta, True)
            else:
                if ended:
                    val = self.evaluate(new_board)
                else:
                    # Pass turn: flip board view
                    val = -self.alphabeta(self.flip(new_board), depth - 1, -beta, -alpha, True)
            
            if val > best_val:
                best_val = val
                best_move = m
            
            alpha = max(alpha, best_val)
            # Root node: no beta cut needed
            
        return best_move, best_val

    def alphabeta(self, board, depth, alpha, beta, maximizing):
        self.check_time()
        
        if depth <= 0:
            return self.evaluate(board)
            
        # Check if current side has no moves (game over check)
        # (Though simulate() handles cleanup, we might reach here recursively)
        if sum(board[0:6]) == 0:
             return self.evaluate(board)
             
        legal = [i for i in range(6) if board[i] > 0]
        if not legal:
            return self.evaluate(board)
            
        ordered = self.order_moves(board, legal)
        
        value = -float('inf')
        
        for m in ordered:
            new_board, extra, ended = self.simulate(board, m)
            
            if extra and not ended:
                v = self.alphabeta(new_board, depth, alpha, beta, True)
            else:
                if ended:
                    v = self.evaluate(new_board)
                else:
                    v = -self.alphabeta(self.flip(new_board), depth - 1, -beta, -alpha, True)
                    
            value = max(value, v)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
                
        return value

    def simulate(self, board_in, move):
        # Simulate a move and return (new_board, extra_turn, game_ended)
        board = board_in[:]
        seeds = board[move]
        board[move] = 0
        
        # Sowing logic
        # We skip index 13 (opp store). Modulo 13 arithmetic maps 0..12 to 0..12.
        
        laps = seeds // 13
        rem = seeds % 13
        
        # Distribute laps (full cycles)
        if laps > 0:
            for i in range(13):
                board[i] += laps
                
        # Distribute remainder
        curr = (move + 1) % 13
        for _ in range(rem):
            board[curr] += 1
            # Manual increment with wrap at 12 -> 0 (skip 13 effectively)
            curr = 0 if curr == 12 else curr + 1
            
        # Determine index of last seed
        if rem == 0:
            last_idx = move
        else:
            last_idx = 12 if curr == 0 else curr - 1
            
        extra_turn = (last_idx == 6)
        
        # Capture Rule:
        # Last seed in own empty house (0-5) AND opposite house has seeds.
        # Note: 'board[last_idx] == 1' implies it was empty before this specific drop
        # (accounting for laps addition).
        if 0 <= last_idx <= 5 and board[last_idx] == 1:
            opp_idx = 12 - last_idx
            if board[opp_idx] > 0:
                capture_amt = board[opp_idx] + 1
                board[6] += capture_amt
                board[last_idx] = 0
                board[opp_idx] = 0
                
        # Game End Check
        side_me = sum(board[0:6])
        side_op = sum(board[7:13])
        ended = (side_me == 0 or side_op == 0)
        
        if ended:
            board[6] += side_me
            board[13] += side_op
            for i in range(6): board[i] = 0
            for i in range(7, 13): board[i] = 0
            extra_turn = False
            
        return board, extra_turn, ended

    def flip(self, board):
        # Rotate board 180 degrees for opponent view
        # Swap My Side (0-6) with Op Side (7-13)
        return board[7:14] + board[0:7]

    def evaluate(self, board):
        # Score difference from current player's perspective
        return board[6] - board[13]

    def order_moves(self, board, legal):
        # Prioritize moves landing in store
        extras = []
        others = []
        for m in legal:
            seeds = board[m]
            dist = 6 - m
            # Check if lands in store: (seeds - dist) % 13 == 0 ???
            # Simpler: seeds % 13 == dist
            if seeds % 13 == dist:
                extras.append(m)
            else:
                others.append(m)
        
        # Sort others by number of seeds (heuristic)
        others.sort(key=lambda x: board[x], reverse=True)
        return extras + others
