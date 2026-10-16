
import collections

def policy(board):
    def get_lines_of_action_count(board, r, c, dr, dc):
        count = 0
        nr, nc = r, c
        while 0 <= nr < 8 and 0 <= nc < 8:
            if board[nr][nc] != 0:
                count += 1
            nr += dr
            nc += dc
        nr, nc = r - dr, c - dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            if board[nr][nc] != 0:
                count += 1
            nr -= dr
            nc -= dc
        return count

    def is_valid_move(board, fr, fc, tr, tc, player):
        if not (0 <= tr < 8 and 0 <= tc < 8):
            return False
        if board[fr][fc] != player:
            return False
        dr, dc = tr - fr, tc - fc
        if dr == 0 and dc == 0:
            return False
        steps = max(abs(dr), abs(dc))
        if steps == 0:
            return False
        if dr != 0 and dc != 0 and abs(dr) != abs(dc):
            return False
        if dr == 0 or dc == 0 or abs(dr) == abs(dc):
            pass
        else:
            return False
            
        line_count = get_lines_of_action_count(board, fr, fc, 
                                              dr//steps if dr != 0 else 0, 
                                              dc//steps if dc != 0 else 0)
        if steps != line_count:
            return False
            
        sr, sc = 1 if dr > 0 else (-1 if dr < 0 else 0), 1 if dc > 0 else (-1 if dc < 0 else 0)
        nr, nc = fr + sr, fc + sc
        for _ in range(steps - 1):
            if not (0 <= nr < 8 and 0 <= nc < 8):
                return False
            if board[nr][nc] == -player:
                return False
            nr += sr
            nc += sc
        if board[tr][tc] == player:
            return False
        return True

    def get_all_legal_moves(board, player):
        moves = []
        for r in range(8):
            for c in range(8):
                if board[r][c] == player:
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            line_count = get_lines_of_action_count(board, r, c, dr, dc)
                            if line_count == 0:
                                continue
                            tr, tc = r + dr * line_count, c + dc * line_count
                            if is_valid_move(board, r, c, tr, tc, player):
                                moves.append((r, c, tr, tc))
        return moves

    def is_connected(board, player):
        visited = [[False]*8 for _ in range(8)]
        pieces = []
        for r in range(8):
            for c in range(8):
                if board[r][c] == player:
                    pieces.append((r, c))
        
        if not pieces:
            return True
            
        stack = [pieces[0]]
        visited[pieces[0][0]][pieces[0][1]] = True
        found = 1
        
        while stack:
            r, c = stack.pop()
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and not visited[nr][nc] and board[nr][nc] == player:
                        visited[nr][nc] = True
                        stack.append((nr, nc))
                        found += 1
                        
        return found == len(pieces)

    def make_move_on_board(b, fr, fc, tr, tc):
        new_board = [row[:] for row in b]
        piece = new_board[fr][fc]
        new_board[fr][fc] = 0
        new_board[tr][tc] = piece
        return new_board

    player = 1
    legal_moves = get_all_legal_moves(board, player)
    
    if not legal_moves:
        return "0,0:0,1"  # Fallback, though should never happen in real play
    
    # 1. Check for winning move
    for fr, fc, tr, tc in legal_moves:
        new_board = make_move_on_board(board, fr, fc, tr, tc)
        if is_connected(new_board, player):
            return f"{fr},{fc}:{tr},{tc}"
    
    # 2. Check for opponent winning threat to block
    opponent_moves = get_all_legal_moves(board, -player)
    for fr, fc, tr, tc in opponent_moves:
        new_board = make_move_on_board(board, fr, fc, tr, tc)
        if is_connected(new_board, -player):
            # Find a move that blocks this
            for m_fr, m_fc, m_tr, m_tc in legal_moves:
                # Try capturing the piece that would win for opponent
                if (m_tr, m_tc) == (fr, fc):
                    return f"{m_fr},{m_fc}:{m_tr},{m_tc}"
                # Try blocking the winning move path
                if (m_tr, m_tc) == (tr, tc) and board[tr][tc] == 0:
                    return f"{m_fr},{m_fc}:{m_tr},{m_tc}"
    
    # 3. Evaluate captures and aggressive moves
    capture_moves = []
    for fr, fc, tr, tc in legal_moves:
        if board[tr][tc] == -player:
            # Simulate capture and check if it improves position
            new_board = make_move_on_board(board, fr, fc, tr, tc)
            if is_connected(new_board, player):
                return f"{fr},{fc}:{tr},{tc}"
            capture_moves.append((fr, fc, tr, tc))
            
    if capture_moves:
        # Prefer captures that reduce opponent pieces significantly
        return f"{capture_moves[0][0]},{capture_moves[0][1]}:{capture_moves[0][2]},{capture_moves[0][3]}"
        
    # 4. Improve connectivity or centralize pieces
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for fr, fc, tr, tc in legal_moves:
        # Score based on moving toward center and improving piece clustering
        score = 0
        dist_to_center = abs(tr - 3.5) + abs(tc - 3.5)
        score -= dist_to_center * 0.1  # Slightly prefer center positions
        
        # Bonus for moves that keep pieces together
        my_pieces_before = [(r,c) for r in range(8) for c in range(8) if board[r][c] == player]
        new_board = make_move_on_board(board, fr, fc, tr, tc)
        my_pieces_after = [(r,c) for r in range(8) for c in range(8) if new_board[r][c] == player]
        
        # Count neighbors after move
        neighbor_count = 0
        for r, c in my_pieces_after:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and new_board[nr][nc] == player:
                        neighbor_count += 1
                        
        score += neighbor_count * 0.2
        
        if score > best_score:
            best_score = score
            best_move = (fr, fc, tr, tc)
            
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
