import { Injectable } from '@angular/core';

/** what the editor held for one game: the code, the template it started from and that template's code */
export interface CreateDraft {
  code: string;
  exampleBot: string;
  /** code of the template as loaded, to tell whether the user has edited it since */
  exampleCode: string | null;
}

/**
 * Keeps the Create page's work across in-app navigation (the page component is destroyed when the
 * user leaves it): one draft per game plus the last selected game and the run settings.
 */
@Injectable({ providedIn: 'root' })
export class CreateDraftService {
  gameKey: string | null = null;
  moveTimeout: number | null = null;
  lanes: number | null = null;
  private readonly drafts = new Map<string, CreateDraft>();

  get(gameKey: string | null): CreateDraft | null {
    return this.drafts.get(gameKey ?? '') ?? null;
  }

  save(gameKey: string | null, draft: CreateDraft): void {
    this.drafts.set(gameKey ?? '', draft);
  }

  clear(gameKey: string | null): void {
    this.drafts.delete(gameKey ?? '');
  }
}
