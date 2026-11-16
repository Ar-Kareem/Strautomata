
import collections

def policy(board) -> str:
    # Directions for movement and connectivity
    DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]

    def get_pieces(b, player):
        return [(r, c) for r in range(8) for c in range(8) if b[r][c] == player]

    def is_connected(pieces):
        if not pieces: return True
        visited = set()
        queue = collections.deque([pieces[0]])
        visited.add(pieces[0])
        while queue:
            curr = queue.popleft()
            for dr, dc in DIRECTIONS:
                neighbor = (curr[0] + dr, curr[1] + dc)
                if neighbor in pieces and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return len(visited) == len(pieces)

    def get_legal_moves(b, player):
        pieces = get_pieces(b, player)
        moves = []
        for r, c in pieces:
            # Check all 4 lines (horiz, vert, diag\, diag/)
            lines = [
                (0, 1), (1, 0), (1, 1), (1, -1)
            ]
            for dr, dc in lines:
                # Count pieces in this line
                count = 0
                for i in range(-7, 8):
                    nr, nc = r + i*dr, c + i*dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and b[nr][nc] != 0:
                        count += 1
                
                # Try moving in both directions along the line
                for direction in [1, -1]:
                    tr, tc = r + direction * dr * count, c + direction * dc * count
                    if 0 <= tr < 8 and 0 <= tc < 8:
                        # Rule: cannot land on own piece
                        if b[tr][tc] != player:
                            # Rule: cannot jump over enemy piece
                            blocked = False
                            for step in range(1, count):
                                mr, mc = r + direction * dr * step, c + direction * dc * step
                                if b[mr][mc] == -player:
                                    blocked = True
                                    break
                            if not blocked:
                                moves.append(((r, c), (tr, tc)))
        return moves

    def apply_move(b, move, player):
        (fr, fc), (tr, tc) = move
        new_board = [row[:] for row in b]
        new_board[tr][tc] = player
        new_board[fr][fc] = 0
        return new_board

    def evaluate(b):
        my_pieces = get_pieces(b, 1)
        opp_pieces = get_pieces(b, -1)
        
        if not my_pieces: return -10000
        if is_connected(my_pieces): return 10000
        if is_connected(opp_pieces): return -10000
        
        # Center of mass distance
        my_r_avg = sum(p[0] for p in my_pieces) / len(my_pieces)
        my_c_avg = sum(p[1] for p in my_pieces) / len(my_pieces)
        dist_sum = sum(abs(p[0]-my_r_avg) + abs(p[1]-my_c_avg) for p in my_pieces)
        
        # Centrality (prefer middle of board)
        centrality = sum((3.5 - abs(p[0]-3.5) + 3.5 - abs(p[1]-3.5)) for p in my_pieces)
        
        return -2 * dist_sum + centrality - 2 * len(opp_pieces)

    def minimax(b, depth, alpha, beta, maximizing_player):
        if depth == 0:
            return evaluate(b)
        
        if maximizing_player:
            max_eval = -float('inf')
            moves = get_legal_moves(b, 1)
            if not moves: return evaluate(b)
            for move in moves:
                eval = minimax(apply_move(b, move, 1), depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            moves = get_legal_moves(b, -1)
            if not moves: return evaluate(b)
            for move in moves:
                eval = minimax(apply_move(b, move, -1), depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    best_val = -float('inf')
    best_move = None
    legal_moves = get_legal_moves(board, 1)
    
    if not legal_moves:
        return "" # Should not happen in LoA

    # Simple move ordering: move that leads to win immediately
    for move in legal_moves:
        nb = apply_move(board, move, 1)
        if is_connected(get_pieces(nb, 1)):
            return f"{move[0][0]},{move[0][1]}:{move[1][0]},{move[1][1]}"

    for move in legal_moves:
        val = minimax(apply_move(board, move, 1), 1, -float('inf'), float('inf'), False)
        if val > best_val:
            best_val = val
            best_move = move
            
    if best_move:
        return f"{best_move[0][0]},{best_move[0][1]}:{best_move[1][0]},{best_move[1][1]}"
    
    # Fallback
    m = legal_moves[0]
    return f"{m[0][0]},{m[0][1]}:{m[1][0]},{m[1][1]}"
