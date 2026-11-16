import type { Type } from '@angular/core';
import { ArenaGoGuiComponent } from './go/arena-go-gui.component';
import { ArenaBreakthroughGuiComponent } from './breakthrough/arena-breakthrough-gui.component';
import { ArenaAmazonsGuiComponent } from './amazons/arena-amazons-gui.component';
import { ArenaChessGuiComponent } from './chess/arena-chess-gui.component';
import { ArenaBattleshipsGuiComponent } from './battleships/arena-battleships-gui.component';
import { ArenaConnect4GuiComponent } from './connect4/arena-connect4-gui.component';
import { ArenaCheckersGuiComponent } from './checkers/arena-checkers-gui.component';
import { ArenaClobberGuiComponent } from './clobber/arena-clobber-gui.component';
import { ArenaDotsAndBoxesGuiComponent } from './dots-and-boxes/arena-dots-and-boxes-gui.component';
import { ArenaHexGuiComponent } from './hex/arena-hex-gui.component';
import { ArenaNimGuiComponent } from './nim/arena-nim-gui.component';
import { ArenaTicTacToeGuiComponent } from './tic-tac-toe/arena-tic-tac-toe-gui.component';
import { ArenaTicTacToe3dGuiComponent } from './tic-tac-toe-3d/arena-tic-tac-toe-3d-gui.component';
import { ArenaPentagoGuiComponent } from './pentago/arena-pentago-gui.component';
import { ArenaLinesOfActionGuiComponent } from './lines-of-action/arena-lines-of-action-gui.component';
import { ArenaBackgammonGuiComponent } from './backgammon/arena-backgammon-gui.component';
import { ArenaOthelloGuiComponent } from './othello/arena-othello-gui.component';
import { ArenaMancalaGuiComponent } from './mancala/arena-mancala-gui.component';
import { ArenaHavannahGuiComponent } from './havannah/arena-havannah-gui.component';

export const GAME_GUI_MAP: Record<string, Type<unknown>> = {
  amazons: ArenaAmazonsGuiComponent,
  backgammon: ArenaBackgammonGuiComponent,
  battleships: ArenaBattleshipsGuiComponent,
  breakthrough: ArenaBreakthroughGuiComponent,
  checkers: ArenaCheckersGuiComponent,
  chess: ArenaChessGuiComponent,
  clobber: ArenaClobberGuiComponent,
  connect4: ArenaConnect4GuiComponent,
  dots_and_boxes: ArenaDotsAndBoxesGuiComponent,
  go: ArenaGoGuiComponent,
  havannah: ArenaHavannahGuiComponent,
  hex: ArenaHexGuiComponent,
  lines_of_action: ArenaLinesOfActionGuiComponent,
  mancala: ArenaMancalaGuiComponent,
  nim: ArenaNimGuiComponent,
  othello: ArenaOthelloGuiComponent,
  pentago: ArenaPentagoGuiComponent,
  tic_tac_toe: ArenaTicTacToeGuiComponent,
  tic_tac_toe_3d: ArenaTicTacToe3dGuiComponent
};
