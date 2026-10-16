#!/usr/bin/env python3
"""Mirror Stanford GameMaster games for local offline use.

From the repo root, regenerate the mirror with:                                                                                                                                                                                                                                           
                                                                                                                                                                                                                                                                                            
  python src/game_arena/stanford_gamemaster/stanford_gamemaster_fetch.py                                                                                                                                                                                                                    

  That will recreate the mirror at src/game_arena/stanford_gamemaster/offline_mirror. It needs network access because it re-downloads the Stanford pages and assets.                                                                                                                        

  Then start the local server with:                                    

  python -m http.server -d src/game_arena/stanford_gamemaster/offline_mirror 6767                                                             

  Open http://localhost:6767/.                                         

This script fetches the public GameMaster game list, stores each rulesheet as a
plain text file, and writes offline HTML copies of the information / standalone /
human / manager pages with shared asset paths rewritten to local files.

The mirrored pages are intended for local use. Stanford's `epilog.js` header
includes redistribution restrictions, so this script downloads third-party
assets on demand instead of vendoring them in this repository.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen


BASE_URL = "http://gamemaster.stanford.edu"
HOMEPAGE_URL = f"{BASE_URL}/homepage"
GAME_LIST_URL = f"{HOMEPAGE_URL}/showgames.php"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "offline_mirror"
LOCAL_ASSET_FILES = ("vs_llm.js", "vs_llm.worker.js", "vs_llm_random_bot.py")

ASSETS = {
    "epilog.js": f"{BASE_URL}/epilog/javascript/epilog.js",
    "standalone.js": f"{BASE_URL}/javascript/standalone.js",
    "ggp.jpg": f"{BASE_URL}/images/ggp.jpg",
    "ggpquad.jpeg": f"{BASE_URL}/images/ggpquad.jpeg",
    "pencil.gif": f"{BASE_URL}/images/pencil.gif",
}

PAGE_TYPES = ("info", "standalone", "human", "manager")
GAME_RE = re.compile(r"standalone\.php\?game=([A-Za-z0-9_]+)")
LIBRARY_RE = re.compile(
    r"<textarea[^>]*id=['\"]library['\"][^>]*>(.*?)</textarea>",
    re.IGNORECASE | re.DOTALL,
)
ROLE_RE = re.compile(r"^\s*role\(([^()]+)\)", re.MULTILINE)
LIBRARY_ASSET_RE = re.compile(r"\.\./library/[^'\"\s<>)]+")


def fetch_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": "CA-arena Stanford GameMaster mirror"})
    with urlopen(req) as response:
        payload = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "CA-arena Stanford GameMaster mirror"})
    with urlopen(req) as response:
        return response.read()


def unique_games(index_html: str) -> list[str]:
    return sorted(set(GAME_RE.findall(index_html)))


def extract_rules(page_html: str) -> str:
    match = LIBRARY_RE.search(page_html)
    if not match:
        raise ValueError("Could not find <textarea id='library'> in standalone page")
    return html.unescape(match.group(1)).strip() + "\n"


def extract_roles(rules_text: str) -> list[str]:
    return ROLE_RE.findall(rules_text)


def slugify_route_part(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "bot"


def dedupe_slug(candidate: str, used: set[str]) -> str:
    if candidate not in used:
        used.add(candidate)
        return candidate
    suffix = 2
    while f"{candidate}-{suffix}" in used:
        suffix += 1
    resolved = f"{candidate}-{suffix}"
    used.add(resolved)
    return resolved


def vs_llm_route(game: str) -> str:
    return f"/vs_llm/{game}/"


def route_to_output_path(output_dir: Path, route_path: str) -> Path:
    return output_dir / route_path.lstrip("/") / "index.html"


def rewrite_page(page_html: str, page_type: str) -> str:
    rewritten = page_html
    replacements = {
        "/epilog/javascript/epilog.js": "/assets/epilog.js",
        "../assets/epilog.js": "/assets/epilog.js",
        "../javascript/standalone.js": "/assets/standalone.js",
        "../assets/standalone.js": "/assets/standalone.js",
        "../images/ggp.jpg": "/assets/ggp.jpg",
        "../assets/ggp.jpg": "/assets/ggp.jpg",
        "../images/ggpquad.jpeg": "/assets/ggpquad.jpeg",
        "../assets/ggpquad.jpeg": "/assets/ggpquad.jpeg",
        "../images/pencil.gif": "/assets/pencil.gif",
        "../assets/pencil.gif": "/assets/pencil.gif",
        "href='index.php'": "href='/index.html'",
        'href="index.php"': 'href="/index.html"',
        "href='../index.html'": "href='/index.html'",
        'href="../index.html"': 'href="/index.html"',
        "../library/": "/library/",
        'window.open("../standalone/': 'window.open("/standalone/',
        'window.open("../human/': 'window.open("/human/',
        'window.open("../manager/': 'window.open("/manager/',
    }
    for old, new in replacements.items():
        rewritten = rewritten.replace(old, new)

    rewritten = re.sub(
        r'window\.open\("standalone\.php\?game=([^"]+)","_blank"\)',
        r'window.open("/standalone/\1.html","_blank")',
        rewritten,
    )
    rewritten = re.sub(
        r'window\.open\("human\.php\?game=([^"]+)","_blank"\)',
        r'window.open("/human/\1.html","_blank")',
        rewritten,
    )
    rewritten = re.sub(
        r'window\.open\("manager\.php\?game=([^"]+)","_blank"\)',
        r'window.open("/manager/\1.html","_blank")',
        rewritten,
    )

    if page_type == "standalone":
        rewritten = re.sub(
            r"function makeurl \(\)\s*\{return \"standalone\.php\".*?\}",
            "function makeurl ()\n {return '/standalone/' + game + '.html'}",
            rewritten,
            count=1,
            flags=re.DOTALL,
        )
        rewritten = re.sub(
            r"function makeurl \(\)\s*\{return game \+ '\.html'\}",
            "function makeurl ()\n {return '/standalone/' + game + '.html'}",
            rewritten,
            count=1,
        )

    return rewritten


def inject_before_head_close(page_html: str, snippet: str) -> str:
    marker = "</head>"
    if marker not in page_html:
        raise ValueError("Could not find </head> while injecting local script")
    return page_html.replace(marker, snippet + "\n" + marker, 1)


def build_vs_llm_page(page_html: str, page_config: dict[str, object]) -> str:
    rewritten = rewrite_page(page_html, "standalone")
    rewritten = rewritten.replace("<title>Standalone</title>", "<title>VS_LLM</title>", 1)
    rewritten = rewritten.replace("Protocol: standalone", "Protocol: vs_llm", 1)
    rewritten = re.sub(
        r"function makeurl \(\)\s*\{return .*?\}",
        "function makeurl ()\n"
        " {return (window.VS_LLM_CONFIG && window.VS_LLM_CONFIG.currentPath) || ('/vs_llm/' + game + '/')}",
        rewritten,
        count=1,
        flags=re.DOTALL,
    )
    config_json = json.dumps(page_config, sort_keys=True)
    return inject_before_head_close(
        rewritten,
        "\n".join(
            (
                f"  <script type='text/javascript'>window.VS_LLM_CONFIG = {config_json};</script>",
                "  <script type='text/javascript' src='/assets/vs_llm.js'></script>",
            )
        ),
    )


def extract_library_asset_paths(page_html: str) -> set[str]:
    return set(LIBRARY_ASSET_RE.findall(page_html))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def generate_index(output_dir: Path, manifest: list[dict[str, object]]) -> None:
    rows = []
    for item in manifest:
        game = str(item["game"])
        roles = ", ".join(item["roles"]) if item["roles"] else "unknown"
        prompt_filename = f"w_{game}_prompt_example.txt"
        prompt_path = output_dir / "prompts" / prompt_filename
        human_vs_llm_path = item.get("human_vs_llm_path")
        llm_vs_llm_path = item.get("llm_vs_llm_path")
        if isinstance(human_vs_llm_path, str) and human_vs_llm_path:
            human_vs_llm_cell = f"<a href='{html.escape(human_vs_llm_path)}'>HUMAN VS LLM</a>"
        else:
            human_vs_llm_cell = ""
        if isinstance(llm_vs_llm_path, str) and llm_vs_llm_path:
            llm_vs_llm_cell = f"<a href='{html.escape(llm_vs_llm_path)}'>LLM VS LLM</a>"
        else:
            llm_vs_llm_cell = ""
        if prompt_path.exists():
            prompt_cell = f"<a href='prompts/{html.escape(prompt_filename)}'>Prompt</a>"
        else:
            prompt_cell = ""
        rows.append(
            "<tr>"
            f"<td>{html.escape(game)}</td>"
            f"<td>{html.escape(roles)}</td>"
            f"<td>{human_vs_llm_cell}</td>"
            f"<td>{llm_vs_llm_cell}</td>"
            f"<td>{prompt_cell}</td>"
            f"<td><a href='info/{html.escape(game)}.html'>Information</a></td>"
            f"<td><a href='standalone/{html.escape(game)}.html'>Standalone</a></td>"
            "</tr>"
        )
    index_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>LLMs in GameMaster</title>
  <style>
    body {{
      font-family: sans-serif;
      margin: 2rem;
      color: #1f2937;
      background: #f8fafc;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      background: white;
    }}
    th, td {{
      border: 1px solid #cbd5e1;
      padding: 0.5rem 0.75rem;
      text-align: left;
    }}
    th {{
      background: #e2e8f0;
    }}
    code {{
      background: #e2e8f0;
      padding: 0.1rem 0.3rem;
    }}
  </style>
</head>
<body>
  <h1>LLMs in GameMaster</h1>
  <p>Hosted on April 3, 2026, will be taken down soon.</p>
  <table>
    <thead>
      <tr>
        <th>Game</th>
        <th>Roles</th>
        <th>HUMAN VS LLM</th>
        <th>LLM VS LLM</th>
        <th>Prompt</th>
        <th>Information</th>
        <th>Standalone</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body>
</html>
"""
    write_text(output_dir / "index.html", index_html)


def load_vs_llm_elos(output_dir: Path) -> dict[str, dict[str, str]]:
    csv_path = output_dir / "elos_all_bots.csv"
    if not csv_path.exists():
        return {}

    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return {}
        bot_id_column = reader.fieldnames[0]
        elo_by_game: dict[str, dict[str, str]] = {}
        for row in reader:
            bot_id = str(row.get(bot_id_column, "")).strip()
            if not bot_id:
                continue
            for column_name, value in row.items():
                if column_name in (bot_id_column, "Median ELO"):
                    continue
                if value is None:
                    continue
                elo_text = str(value).strip()
                if not elo_text:
                    continue
                elo_by_game.setdefault(column_name, {})[bot_id] = elo_text
    return elo_by_game


def load_vs_llm_game_stats(output_dir: Path) -> dict[str, dict[str, dict[str, str]]]:
    stats_dir = output_dir / "game_stats"
    if not stats_dir.exists():
        return {}

    stats_by_game: dict[str, dict[str, dict[str, str]]] = {}
    for csv_path in sorted(stats_dir.glob("model_stats_*.csv")):
        game = csv_path.stem.removeprefix("model_stats_")
        with csv_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                continue
            bot_id_column = reader.fieldnames[0]
            game_stats: dict[str, dict[str, str]] = {}
            for row in reader:
                bot_id = str(row.get(bot_id_column, "")).strip()
                if not bot_id:
                    continue
                game_stats[bot_id] = {
                    str(column_name).strip(): str(value).strip()
                    for column_name, value in row.items()
                    if column_name != bot_id_column and column_name is not None and value is not None
                }
            if game_stats:
                stats_by_game[game] = game_stats
    return stats_by_game


def build_dropdown_label(label: str, elo_text: str, no_blame_score: str) -> str:
    suffix_parts = []
    if elo_text:
        try:
            suffix_parts.append(f"ELO {int(float(elo_text))}")
        except ValueError:
            suffix_parts.append(f"ELO {elo_text}")
    if no_blame_score:
        try:
            suffix_parts.append(f"NB {float(no_blame_score):.2f}")
        except ValueError:
            suffix_parts.append(f"NB {no_blame_score}")
    if not suffix_parts:
        return label
    return f"{label} ({', '.join(suffix_parts)})"


def build_vs_llm_bot_manifest(
    examples_root: Path,
    elo_by_game: dict[str, dict[str, str]] | None = None,
    game_stats_by_game: dict[str, dict[str, dict[str, str]]] | None = None,
) -> dict[str, list[dict[str, str]]]:
    manifest: dict[str, list[dict[str, str]]] = {}
    if not examples_root.exists():
        return manifest

    for world_dir in sorted(examples_root.glob("w_*")):
        if not world_dir.is_dir():
            continue
        game = world_dir.name[2:]
        bots: list[dict[str, str]] = []
        per_model_count: dict[str, int] = {}
        bot_files = sorted(world_dir.glob("*/*/2.python_code.py"))
        for bot_file in bot_files:
            if not bot_file.is_file():
                continue
            model = bot_file.parent.parent.name
            per_model_count[model] = per_model_count.get(model, 0) + 1

        model_slug_by_name: dict[str, str] = {}
        used_model_slugs: set[str] = set()
        for model in sorted(per_model_count):
            model_slug_by_name[model] = dedupe_slug(slugify_route_part(model), used_model_slugs)

        for bot_file in bot_files:
            if not bot_file.is_file():
                continue
            model = bot_file.parent.parent.name
            run_id = bot_file.parent.name
            info_path = bot_file.with_name("0.info.json")
            display_name = model
            if info_path.exists():
                try:
                    info_json = json.loads(info_path.read_text(encoding="utf-8"))
                    model_info = info_json.get("model", {})
                    save_name = model_info.get("save_name")
                    if isinstance(save_name, str) and save_name.strip():
                        display_name = save_name.strip()
                except Exception:
                    pass
            label = f"{display_name} / {run_id}"
            model_route_slug = model_slug_by_name[model]
            run_route_slug = slugify_route_part(run_id)
            route_key = f"{model_route_slug}/{run_route_slug}"
            bot_id = f"{model}/{run_id}"
            elo_text = None
            if elo_by_game:
                elo_text = elo_by_game.get(game, {}).get(bot_id)
            no_blame_score = ""
            if game_stats_by_game:
                no_blame_score = game_stats_by_game.get(game, {}).get(bot_id, {}).get("No_Blame_Score", "")
            bots.append(
                {
                    "bot_id": bot_id,
                    "label": label,
                    "dropdown_label": build_dropdown_label(label, elo_text or "", no_blame_score),
                    "model": model,
                    "run_id": run_id,
                    "route_model_slug": model_route_slug,
                    "route_run_slug": run_route_slug,
                    "route_key": route_key,
                    "source_path": f"examples/{world_dir.name}/{model}/{run_id}/2.python_code.py",
                    "elo": elo_text or "",
                    "no_blame_score": no_blame_score,
                    "requires_legal_moves": False,
                }
            )
        if bots:
            random_elo = ""
            if elo_by_game:
                random_elo = elo_by_game.get(game, {}).get("random", "")
            random_no_blame_score = ""
            if game_stats_by_game:
                random_no_blame_score = game_stats_by_game.get(game, {}).get("random", {}).get("No_Blame_Score", "")
            random_label = "random"
            random_dropdown_label = build_dropdown_label(random_label, random_elo, random_no_blame_score)
            bots.append(
                {
                    "bot_id": "random",
                    "label": random_label,
                    "dropdown_label": random_dropdown_label,
                    "model": "random",
                    "run_id": "",
                    "route_model_slug": "random",
                    "route_run_slug": "",
                    "route_key": "random",
                    "source_path": "assets/vs_llm_random_bot.py",
                    "elo": random_elo,
                    "no_blame_score": random_no_blame_score,
                    "requires_legal_moves": True,
                }
            )
        manifest[game] = bots
    return manifest


def build_vs_llm_page_config(
    *,
    current_path: str,
    default_mode: str,
    default_human_bot_route: str | None = None,
    default_llm_bot_a_route: str | None = None,
    default_llm_bot_b_route: str | None = None,
) -> dict[str, object]:
    return {
        "currentPath": current_path,
        "defaultMode": default_mode,
        "defaultHumanBotRoute": default_human_bot_route,
        "defaultLlmBotARoute": default_llm_bot_a_route,
        "defaultLlmBotBRoute": default_llm_bot_b_route,
    }


def write_vs_llm_pages(
    output_dir: Path,
    game: str,
    standalone_html: str,
) -> None:
    generic_human_route = vs_llm_route(game)
    write_text(
        route_to_output_path(output_dir, generic_human_route),
        build_vs_llm_page(
            standalone_html,
            build_vs_llm_page_config(
                current_path=generic_human_route,
                default_mode="human_vs_llm",
            ),
        ),
    )


def sync_local_overlay(output_dir: Path) -> None:
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    for asset_name in LOCAL_ASSET_FILES:
        source_path = Path(__file__).resolve().parent / asset_name
        if not source_path.exists():
            raise FileNotFoundError(f"Missing local Stanford asset: {source_path}")
        write_text(assets_dir / asset_name, source_path.read_text(encoding="utf-8"))

    examples_root = output_dir / "examples"
    if not examples_root.exists():
        examples_root = Path(__file__).resolve().parent / "examples"
    game_stats_by_game = load_vs_llm_game_stats(output_dir)
    vs_llm_manifest = build_vs_llm_bot_manifest(
        examples_root,
        load_vs_llm_elos(output_dir),
        game_stats_by_game,
    )
    write_text(
        assets_dir / "vs_llm_bots.json",
        json.dumps(vs_llm_manifest, indent=2) + "\n",
    )
    write_text(
        assets_dir / "vs_llm_game_stats.json",
        json.dumps(game_stats_by_game, indent=2) + "\n",
    )

    vs_llm_dir = output_dir / "vs_llm"
    if vs_llm_dir.exists():
        shutil.rmtree(vs_llm_dir)

    standalone_dir = output_dir / "standalone"
    if standalone_dir.exists():
        for standalone_path in sorted(standalone_dir.glob("*.html")):
            game = standalone_path.stem
            if not vs_llm_manifest.get(game):
                continue
            write_vs_llm_pages(
                output_dir,
                game,
                standalone_path.read_text(encoding="utf-8"),
            )

    manifest_path = output_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest:
            game = str(item["game"])
            roles = item.get("roles") or []
            if vs_llm_manifest.get(game):
                item["human_vs_llm_path"] = f"vs_llm/{game}/?mode=human_vs_llm"
                if isinstance(roles, list) and len(roles) == 2:
                    item["llm_vs_llm_path"] = f"vs_llm/{game}/?mode=llm_vs_llm"
                else:
                    item.pop("llm_vs_llm_path", None)
                item["vs_llm_path"] = f"vs_llm/{game}/"
            else:
                item.pop("human_vs_llm_path", None)
                item.pop("llm_vs_llm_path", None)
                item.pop("vs_llm_path", None)
        write_text(manifest_path, json.dumps(manifest, indent=2) + "\n")
        generate_index(output_dir, manifest)


def mirror_games(output_dir: Path, selected_games: Iterable[str]) -> list[dict[str, object]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / "assets"
    for name, url in ASSETS.items():
        write_bytes(assets_dir / name, fetch_bytes(url))

    manifest: list[dict[str, object]] = []
    library_assets: set[str] = set()
    for game in selected_games:
        info_html = fetch_text(f"{HOMEPAGE_URL}/viewgame.php?game={game}")
        library_assets.update(extract_library_asset_paths(info_html))
        write_text(
            output_dir / "info" / f"{game}.html",
            rewrite_page(info_html, "info"),
        )

        standalone_html = fetch_text(f"{HOMEPAGE_URL}/standalone.php?game={game}")
        rules_text = extract_rules(standalone_html)
        roles = extract_roles(rules_text)

        write_text(output_dir / "rules" / f"{game}.hrf", rules_text)
        library_assets.update(extract_library_asset_paths(standalone_html))
        write_text(
            output_dir / "standalone" / f"{game}.html",
            rewrite_page(standalone_html, "standalone"),
        )

        for page_type in ("human", "manager"):
            page_html = fetch_text(f"{HOMEPAGE_URL}/{page_type}.php?game={game}")
            library_assets.update(extract_library_asset_paths(page_html))
            write_text(
                output_dir / page_type / f"{game}.html",
                rewrite_page(page_html, page_type),
            )

        manifest.append(
            {
                "game": game,
                "roles": roles,
                "info_path": f"info/{game}.html",
                "rules_path": f"rules/{game}.hrf",
                "standalone_path": f"standalone/{game}.html",
                "vs_llm_path": f"vs_llm/{game}/",
                "human_vs_llm_path": f"vs_llm/{game}/?mode=human_vs_llm",
                "llm_vs_llm_path": f"vs_llm/{game}/?mode=llm_vs_llm" if len(roles) == 2 else "",
                "human_path": f"human/{game}.html",
                "manager_path": f"manager/{game}.html",
            }
        )

    for rel_path in sorted(library_assets):
        local_rel_path = rel_path.removeprefix("../")
        asset_url = f"{BASE_URL}/{local_rel_path}"
        write_bytes(output_dir / local_rel_path, fetch_bytes(asset_url))

    write_text(output_dir / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    sync_local_overlay(output_dir)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Directory to write the mirror into (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--games",
        nargs="*",
        help="Specific game names to mirror. If omitted, mirror every public game.",
    )
    parser.add_argument(
        "--sync-local-only",
        action="store_true",
        help="Do not fetch from Stanford; only refresh local VS_LLM assets/pages/index for an existing mirror.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.sync_local_only:
        sync_local_overlay(args.output)
        print(
            json.dumps(
                {
                    "output_dir": str(args.output.resolve()),
                    "synced_local_overlay": True,
                },
                indent=2,
            )
        )
        return 0

    index_html = fetch_text(GAME_LIST_URL)
    all_games = unique_games(index_html)

    if not all_games:
        raise RuntimeError("No public games were found on the GameMaster index page.")

    if args.games:
        unknown = sorted(set(args.games) - set(all_games))
        if unknown:
            raise RuntimeError(f"Unknown game names: {', '.join(unknown)}")
        selected_games = sorted(args.games)
    else:
        selected_games = all_games

    manifest = mirror_games(args.output, selected_games)
    print(
        json.dumps(
            {
                "output_dir": str(args.output.resolve()),
                "game_count": len(manifest),
                "games": [item["game"] for item in manifest],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
