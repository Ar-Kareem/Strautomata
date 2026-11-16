
import time

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def gen_moves(b, player):
    moves = []
    for fr in range(6):
        for fc in range(6):
            if b[fr*6+fc] != player:
                continue
            for dr,dc in DIRS:
                r,c = fr+dr, fc+dc
                while 0<=r<6 and 0<=c<6 and b[r*6+c]==0:
                    for dr2,dc2 in DIRS:
                        ar,ac = r+dr2, c+dc2
                        while 0<=ar<6 and 0<=ac<6:
                            if b[ar*6+ac]==0 or (ar==fr and ac==fc):
                                moves.append((fr,fc,r,c,ar,ac))
                                ar+=dr2; ac+=dc2
                            else:
                                break
                    r+=dr; c+=dc
    return moves

def apply_mv(b, mv, player):
    fr,fc,tr,tc,ar,ac = mv
    b[fr*6+fc] = 0
    b[tr*6+tc] = player
    b[ar*6+ac] = -1

def undo_mv(b, mv, player):
    fr,fc,tr,tc,ar,ac = mv
    b[ar*6+ac] = 0
    b[tr*6+tc] = 0
    b[fr*6+fc] = player

def mobility(b, player):
    count = 0
    for r in range(6):
        for c in range(6):
            if b[r*6+c] != player:
                continue
            for dr,dc in DIRS:
                nr,nc = r+dr, c+dc
                while 0<=nr<6 and 0<=nc<6 and b[nr*6+nc]==0:
                    count += 1
                    nr+=dr; nc+=dc
    return count

def evaluate(b):
    return mobility(b, 1) - mobility(b, 2)

def policy(board):
    start = time.time()
    b = [int(board[r,c]) for r in range(6) for c in range(6)]
    
    my_moves = gen_moves(b, 1)
    if not my_moves:
        return "0,0:0,0:0,0"
    
    # Shallow score + sort our moves
    scored = []
    for mv in my_moves:
        apply_mv(b, mv, 1)
        # Check immediate win
        opp_has = False
        for fr in range(6):
            if opp_has: break
            for fc in range(6):
                if b[fr*6+fc] != 2: continue
                for dr,dc in DIRS:
                    nr,nc = fr+dr, fc+dc
                    if 0<=nr<6 and 0<=nc<6 and b[nr*6+nc]==0:
                        opp_has = True
                        break
                if opp_has: break
        if not opp_has:
            undo_mv(b, mv, 1)
            fr,fc,tr,tc,ar,ac = mv
            return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
        s = evaluate(b)
        undo_mv(b, mv, 1)
        scored.append((s, mv))
    
    scored.sort(reverse=True, key=lambda x: x[0])
    
    best_move = scored[0][1]
    best_score = -10**9
    
    K = 10
    for shallow_s, mv in scored[:K]:
        if time.time() - start > 0.75:
            break
        apply_mv(b, mv, 1)
        opp_moves = gen_moves(b, 2)
        if not opp_moves:
            undo_mv(b, mv, 1)
            fr,fc,tr,tc,ar,ac = mv
            return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
        
        worst = 10**9
        cutoff = False
        for omv in opp_moves:
            apply_mv(b, omv, 2)
            s = evaluate(b)
            undo_mv(b, omv, 2)
            if s < worst:
                worst = s
            if worst <= best_score:
                cutoff = True
                break
        
        undo_mv(b, mv, 1)
        
        if not cutoff and worst > best_score:
            best_score = worst
            best_move = mv
    
    fr,fc,tr,tc,ar,ac = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
