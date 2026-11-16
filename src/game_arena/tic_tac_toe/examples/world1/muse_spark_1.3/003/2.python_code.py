
def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        empties0 = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
        if not empties0:
            return (0, 0)
        if len(empties0) == 1:
            return empties0[0]

        # flatten to tuple of 9, 1=us, -1=opp, 0=empty
        s0 = tuple(board[r][c] for r in range(3) for c in range(3))

        LINES = ((0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6))

        def winner_of(s):
            for a,b,c in LINES:
                v = s[a]
                if v != 0 and v == s[b] and v == s[c]:
                    return v
            return 0

        # immediate win check for speed
        for (r,c) in empties0:
            idx = r*3+c
            lst = list(s0); lst[idx]=1
            if winner_of(tuple(lst)) == 1:
                return (r,c)

        # minimax from our perspective: +1 win, 0 draw, -1 loss
        memo = {}
        def minimax(s, player):
            key = (s, player)
            if key in memo:
                return memo[key]
            w = winner_of(s)
            if w != 0:
                # w is 1 or -1, which equals score from our view
                memo[key] = (w, 0)
                return memo[key]
            if all(v != 0 for v in s):
                memo[key] = (0, 0)
                return memo[key]
            if player == 1:  # maximizing (us)
                best_score = -2
                best_depth = 0
                first = True
                for i in range(9):
                    if s[i]==0:
                        lst = list(s); lst[i]=1; ns=tuple(lst)
                        sc, d = minimax(ns, -1)
                        d = d+1
                        if first:
                            best_score, best_depth = sc, d
                            first=False
                        elif sc > best_score:
                            best_score, best_depth = sc, d
                        elif sc == best_score:
                            if sc == 1:
                                if d < best_depth:
                                    best_depth = d
                            else:  # draw or loss: delay
                                if d > best_depth:
                                    best_depth = d
                memo[key]=(best_score,best_depth)
                return memo[key]
            else:  # minimizing (opponent)
                best_score = 2
                best_depth = 0
                first = True
                for i in range(9):
                    if s[i]==0:
                        lst = list(s); lst[i]=-1; ns=tuple(lst)
                        sc, d = minimax(ns, 1)
                        d = d+1
                        if first:
                            best_score, best_depth = sc, d
                            first=False
                        elif sc < best_score:
                            best_score, best_depth = sc, d
                        elif sc == best_score:
                            if sc == -1:
                                if d < best_depth:
                                    best_depth = d
                            else:  # draw or opp loss: delay
                                if d > best_depth:
                                    best_depth = d
                memo[key]=(best_score,best_depth)
                return memo[key]

        # evaluate all our legal moves
        move_infos = []  # (r,c,score,depth,child_state)
        best_score = -2
        best_depth = 0
        first = True
        for (r,c) in empties0:
            idx = r*3+c
            lst = list(s0); lst[idx]=1; ns=tuple(lst)
            sc, d = minimax(ns, -1)
            d = d+1
            move_infos.append((r,c,sc,d,ns))
            if first:
                best_score, best_depth = sc, d
                first=False
            elif sc > best_score:
                best_score, best_depth = sc, d
            elif sc == best_score:
                if sc == 1:
                    if d < best_depth:
                        best_depth = d
                else:
                    if d > best_depth:
                        best_depth = d

        candidates = [(r,c,ns) for (r,c,sc,d,ns) in move_infos if sc==best_score]
        # if only one optimal or winning/losing forced with depth tie, still use expectimax for draws
        # filter by best depth for winning case to keep fastest win
        if best_score == 1:
            min_d = min(d for (r,c,sc,d,ns) in move_infos if sc==best_score)
            candidates = [(r,c,ns) for (r,c,sc,d,ns) in move_infos if sc==best_score and d==min_d]
            # among fastest wins, pick one (prefer corners) - return first by preference
            pref = {(0,0):0,(0,2):1,(2,0):2,(2,2):3,(1,1):4,(0,1):5,(1,0):6,(1,2):7,(2,1):8}
            candidates.sort(key=lambda x: pref.get((x[0],x[1]),9))
            return (candidates[0][0], candidates[0][1])
        if len(candidates)==1:
            return (candidates[0][0], candidates[0][1])

        # expectimax tie-break: opponent random, we optimal
        memo_e = {}
        def expected(s, player):
            key=(s,player)
            if key in memo_e:
                return memo_e[key]
            w = winner_of(s)
            if w != 0:
                memo_e[key]=float(w)
                return float(w)
            if all(v!=0 for v in s):
                memo_e[key]=0.0
                return 0.0
            children=[]
            for i in range(9):
                if s[i]==0:
                    lst=list(s); lst[i]=player; children.append(tuple(lst))
            if not children:
                memo_e[key]=0.0
                return 0.0
            if player==1:
                v=max(expected(ch,-1) for ch in children)
                memo_e[key]=v
                return v
            else:
                v=sum(expected(ch,1) for ch in children)/len(children)
                memo_e[key]=v
                return v

        pref = {(0,0):0,(0,2):1,(2,0):2,(2,2):3,(1,1):4,(0,1):5,(1,0):6,(1,2):7,(2,1):8}
        best_exp = None
        best_move = (candidates[0][0], candidates[0][1])
        # order by preference for deterministic tie break
        candidates.sort(key=lambda x: pref.get((x[0],x[1]),9))
        for (r,c,ns) in candidates:
            e = expected(ns, -1)
            if best_exp is None or e > best_exp + 1e-12:
                best_exp = e
                best_move = (r,c)
        return (int(best_move[0]), int(best_move[1]))
    except Exception:
        try:
            for r in range(3):
                for c in range(3):
                    if board[r][c]==0:
                        return (r,c)
        except Exception:
            pass
        return (0,0)
