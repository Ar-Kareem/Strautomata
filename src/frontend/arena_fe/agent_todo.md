# Agent Todo


GUI guidelines:
1- player A should go first (unless the game hardcodes player 2 to go first like breakthrough & chess)
2- valid human moves should be highlighted
    3.1- If human input requires two inputs (A -> B), then after picking A, all legal B moves should be highlighted. And if a player picks A1 then picks a different A2, instead of saying (A1 -> A2 is illegal) it should simply swap A1 with A2 and highlight all legal (A2 -> B) moves.
    3.2- If human input requires two inputs (A -> B), then picking A twice should toggle it off as that piece was never picked. (i.e. similar to placing hand on a chess piece then taking the hand off without moving the piece)
3- Should show "Loading Game..." when game is loading.
4- Corners
    5.1 Top left should say GAME NAME BOARD \n Player: X (where X is the bot name of the active player) (For this only use bot names, no displaying "Player 1" or "Player A" or "Turn 1")
    5.2 Top right should say "White: X · Black: Y".
    5.3 Legend should be "*white_dot* White: Y *black_dot* Black: X".

Bug checks:
1- when bot A wins it shows bot A
2- same for bot B
3- when human is A and wins it shows "human won"
4- same for human being B
5- colors do not flicker when match is playing (sign that state is being parsed dynamically which should not happen)
6- When A is slow and B is fast, the GUI should say "Active: A" not B.
7- On new game, the board should be empty.



