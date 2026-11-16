"""Decode Next.js RSC flight payload (self.__next_f.push) and find JSON objects containing given keys."""
import re, json, sys

def flight_text(html: str) -> str:
    parts = []
    for m in re.finditer(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html):
        try:
            parts.append(json.loads('"' + m.group(1) + '"'))
        except Exception:
            pass
    return "".join(parts)

def find_objects(text: str, must_keys, max_n=100000):
    """Scan for balanced JSON objects/arrays whose serialized form contains all must_keys."""
    out = []
    dec = json.JSONDecoder()
    for key in must_keys[:1]:
        for m in re.finditer(re.escape('"' + key + '"'), text):
            # walk backwards to find enclosing '{'
            i = m.start()
            depth = 0
            j = i
            while j >= 0:
                c = text[j]
                if c in '}]':
                    depth += 1
                elif c in '{[':
                    if depth == 0:
                        break
                    depth -= 1
                j -= 1
            if j < 0:
                continue
            try:
                obj, end = dec.raw_decode(text, j)
            except Exception:
                continue
            if all(('"' + k + '"') in text[j:end] for k in must_keys):
                out.append(obj)
    return out

if __name__ == "__main__":
    html = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
    txt = flight_text(html)
    if len(sys.argv) > 2:
        objs = find_objects(txt, sys.argv[2].split(","))
        print(len(objs), "objects")
        for o in objs[:3]:
            print(json.dumps(o)[:1500])
    else:
        sys.stdout.write(txt)
