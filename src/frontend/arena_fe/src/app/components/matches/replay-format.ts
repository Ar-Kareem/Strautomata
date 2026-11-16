/** Decoder for the binary `.rpl` replay files written by `src/frontend/replay_format.py` (format documented there). */

const MAGIC = 'RPL1';
const EXPLICIT_PLAYERS = 2;

export interface ReplayEntry {
  moves: [number, unknown][];
  think: (number | null)[];
  exception?: string;
  timeout_hit?: unknown;
  returns?: unknown;
  other?: unknown;
}

interface ReplayHeader {
  bot: string;
  pairs: [string, number][];
  extras: Record<string, unknown>[];
}

/** Undo the gzip layer (skipped when a server already decoded it via Content-Encoding). */
export const gunzip = async (bytes: Uint8Array): Promise<Uint8Array> => {
  if (bytes[0] !== 0x1f || bytes[1] !== 0x8b) {
    return bytes;
  }
  const stream = new Blob([bytes as BlobPart]).stream().pipeThrough(new DecompressionStream('gzip'));
  return new Uint8Array(await new Response(stream).arrayBuffer());
};

export class ReplayFile {
  readonly bot: string;
  private readonly header: ReplayHeader;
  private readonly body: number;
  private offsets: Map<string, number[]> | null = null;

  constructor(
    private readonly buf: Uint8Array,
    private readonly vocab: unknown[]
  ) {
    if (new TextDecoder().decode(buf.subarray(0, 4)) !== MAGIC) {
      throw new Error('Not a replay file');
    }
    const [len, pos] = this.varint(4);
    this.header = JSON.parse(new TextDecoder().decode(buf.subarray(pos, pos + len))) as ReplayHeader;
    this.bot = this.header.bot;
    this.body = pos + len;
  }

  /** The `slot`-th match against `other`, or null when the file has no such match. */
  entry(other: string, slot: number): ReplayEntry | null {
    const start = this.index().get(other)?.[slot];
    return start === undefined ? null : this.decode(start);
  }

  private varint(pos: number): [number, number] {
    let n = 0;
    let mul = 1;
    for (;;) {
      const b = this.buf[pos++];
      n += (b & 0x7f) * mul;
      if (b < 0x80) {
        return [n, pos];
      }
      mul *= 128;
    }
  }

  private skip(pos: number, count: number): number {
    for (let i = 0; i < count; i++) {
      while (this.buf[pos++] >= 0x80) {
        // continuation byte
      }
    }
    return pos;
  }

  /** Start offset of every record, found by skipping over the varints once. */
  private index(): Map<string, number[]> {
    if (this.offsets) {
      return this.offsets;
    }
    const offsets = new Map<string, number[]>();
    let pos = this.body;
    for (const [other, count] of this.header.pairs) {
      const starts: number[] = [];
      for (let i = 0; i < count; i++) {
        starts.push(pos);
        let plies: number;
        let mode: number;
        [plies, pos] = this.varint(pos);
        [mode, pos] = this.varint(pos);
        pos = this.skip(pos, (mode === EXPLICIT_PLAYERS ? 3 : 2) * plies + 1);
      }
      offsets.set(other, starts);
    }
    this.offsets = offsets;
    return offsets;
  }

  private decode(start: number): ReplayEntry {
    let pos = start;
    let plies: number;
    let mode: number;
    [plies, pos] = this.varint(pos);
    [mode, pos] = this.varint(pos);
    const players: number[] = [];
    for (let i = 0; i < plies; i++) {
      if (mode === EXPLICIT_PLAYERS) {
        let p: number;
        [p, pos] = this.varint(pos);
        players.push(p);
      } else {
        players.push((mode + i) % 2);
      }
    }
    const moves: [number, unknown][] = [];
    for (const p of players) {
      let id: number;
      [id, pos] = this.varint(pos);
      moves.push([p, this.vocab[id]]);
    }
    const think: (number | null)[] = [];
    for (let i = 0; i < plies; i++) {
      let t: number;
      [t, pos] = this.varint(pos);
      think.push(t === 0 ? null : (t - 1) / 100);
    }
    const [ref] = this.varint(pos);
    return { moves, think, ...(ref ? this.header.extras[ref - 1] : {}) };
  }
}
