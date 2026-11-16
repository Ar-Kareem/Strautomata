
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    h, v, cap = horizontal.copy(), vertical.copy(), capture.copy()
    
    legal = get_legal_moves(h, v)
    if not legal:
        return "0,0,H"
    
    capture_moves = [m for m in legal if count_completions(h, v, m) > 0]
    if capture_moves:
        return format_move(find_best_capture(h, v, cap, capture_moves))
    
    safe = [m for m in legal if not creates_three_edge(h, v, m)]
    search_moves = safe if safe else legal
    
    remaining = len(legal)
    depth = remaining + 2 if remaining <= 12 else min(12, max(8, remaining // 2))
    
    best_move, best_score = search_moves[0], float('-inf')
    for move in order_moves(h, v, search_moves, True):
        h2, v2, cap2, captured = apply_move(h, v, cap, move, 1)
        score = minimax(h2, v2, cap2, depth-1, float('-inf'), float('inf'), captured > 0)
        if score > best_score:
            best_score, best_move = score, move
    
    return format_move(best_move)

def find_best_capture(h, v, cap, capture_moves):
    if len(capture_moves) == 1:
        return capture_moves[0]
    best_move, best_score = capture_moves[0], float('-inf')
    for move in capture_moves:
        h2, v2, cap2, captured = apply_move(h, v, cap, move, 1)
        score = minimax(h2, v2, cap2, 8, float('-inf'), float('inf'), True)
        if score > best_score:
            best_score, best_move = score, move
    return best_move

def format_move(move): return f"{move[0]},{move[1]},{move[2]}"

def get_legal_moves(h, v):
    moves = [(r, c, 'H') for r in range(5) for c in range(4) if h[r, c] == 0]
    moves += [(r, c, 'V') for r in range(4) for c in range(5) if v[r, c] == 0]
    return moves

def affected_boxes(r, c, d):
    boxes = []
    if d == 'H':
        if r > 0: boxes.append((r-1, c))
        if r < 4: boxes.append((r, c))
    else:
        if c > 0: boxes.append((r, c-1))
        if c < 4: boxes.append((r, c))
    return boxes

def box_edges(h, v, r, c): return (h[r,c]!=0)+(h[r+1,c]!=0)+(v[r,c]!=0)+(v[r,c+1]!=0)

def count_completions(h, v, move):
    r, c, d = move
    h2, v2 = h.copy(), v.copy()
    (h2 if d=='H' else v2)[r if d=='H' else r, c] = 1
    return sum(1 for br, bc in affected_boxes(r, c, d) if box_edges(h2, v2, br, bc) == 4)

def creates_three_edge(h, v, move):
    r, c, d = move
    h2, v2 = h.copy(), v.copy()
    (h2 if d=='H' else v2)[r if d=='H' else r, c] = 1
    return any(box_edges(h2, v2, br, bc) == 3 for br, bc in affected_boxes(r, c, d))

def apply_move(h, v, cap, move, player):
    r, c, d = move
    h2, v2, cap2 = h.copy(), v.copy(), cap.copy()
    (h2 if d=='H' else v2)[r, c] = player
    captured = sum(1 for br, bc in affected_boxes(r, c, d) if cap2[br, bc] == 0 and box_edges(h2, v2, br, bc) == 4 and (cap2.__setitem__((br, bc), player) or True))
    return h2, v2, cap2, captured

def evaluate(cap): return int(np.sum(cap[:4,:4] == 1) - np.sum(cap[:4,:4] == -1))

def order_moves(h, v, moves, our_turn):
    scored = [((count_completions(h, v, m) * 1000) - (500 if count_completions(h, v, m) == 0 and creates_three_edge(h, v, m) else 0), m) for m in moves]
    scored.sort(reverse=True)
    return [m for _, m in scored]

def minimax(h, v, cap, depth, alpha, beta, our_turn):
    moves = get_legal_moves(h, v)
    if not moves or depth == 0:
        return evaluate(cap)
    
    if our_turn:
        best = float('-inf')
        for move in order_moves(h, v, moves, True):
            h2, v2, cap2, captured = apply_move(h, v, cap, move, 1)
            score = minimax(h2, v2, cap2, depth-1, alpha, beta, captured > 0)
            best = max(best, score)
            alpha = max(alpha, score)
            if beta <= alpha: break
        return best
    else:
        best = float('inf')
        for move in order_moves(h, v, moves, False):
            h2, v2, cap2, captured = apply_move(h, v, cap, move, -1)
            score = minimax(h2, v2, cap2, depth-1, alpha, beta, captured == 0)
            best = min(best, score)
            beta = min(beta, score)
            if beta <= alpha: break
        return best
