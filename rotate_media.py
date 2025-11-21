#!/usr/bin/env python3
import os
import json
import time
from pathlib import Path

# ===== CONFIG =====
MOVIES_DIR = Path("/mnt/movies")
CORE_DIR = Path("/mnt/core_movies")
ROTATION_DIR = Path("/mnt/rotation_movies")
LOG_DIR = Path("/mnt/movies/.logs")
CORE_CACHE_FILE = LOG_DIR / "core_hashes.json"   # from your existing script
STATE_FILE = LOG_DIR / "rotation_state.json"

MAX_ROTATION_ITEMS = 1000
LINK_MAX_AGE_DAYS = 30
IGNORE_NAMES = {".DS_Store", "@eaDir", ".stfolder", ".stversions"}

# make sure dirs exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
ROTATION_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_state():
    if not STATE_FILE.exists():
        return {"last_run": 0}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def load_core_dirnames() -> set[str]:
    names = set()
    if CORE_DIR.exists():
        for p in CORE_DIR.iterdir():
            if p.is_dir():
                names.add(p.name)
            elif p.is_file():
                names.add(p.name)
    return names


def list_rotation_links():
    links = []
    for p in ROTATION_DIR.iterdir():
        if p.is_symlink():
            links.append(p)
    return links


def remove_old_links(links):
    """Remove symlinks older than LINK_MAX_AGE_DAYS."""
    now = time.time()
    cutoff = now - (LINK_MAX_AGE_DAYS * 24 * 60 * 60)
    removed = 0
    for link in links:
        try:
            st = link.lstat()
            if st.st_mtime < cutoff:
                link.unlink(missing_ok=True)
                removed += 1
        except FileNotFoundError:
            # broken link
            link.unlink(missing_ok=True)
            removed += 1
        except Exception as e:
            log(f"Warning removing old link {link}: {e}")
    if removed:
        log(f"Removed {removed} old rotation links")
    return removed


def scan_movies():
    """Flat scan of /mnt/movies."""
    items = []
    for entry in MOVIES_DIR.iterdir():
        if entry.name in IGNORE_NAMES:
            continue
        if not (entry.is_dir() or entry.is_file()):
            continue
        items.append(entry)
    return items


def main():
    log("=== Rotation build start ===")
    state = load_state()
    last_run_ts = state.get("last_run", 0)

    core_names = load_core_dirnames()
    log(f"Loaded {len(core_names)} core names")

    # current rotation links
    current_links = list_rotation_links()
    remove_old_links(current_links)
    current_links = list_rotation_links()
    current_link_names = {p.name for p in current_links}

    # scan movies
    all_movies = scan_movies()
    now_ts = time.time()

    # separate new since last run
    new_movies = []
    old_movies = []
    for item in all_movies:
        if item.name in core_names:
            continue
        try:
            mtime = item.stat().st_mtime
        except FileNotFoundError:
            continue
        if mtime > last_run_ts:
            new_movies.append((mtime, item))
        else:
            old_movies.append(item)

    # newest first for new movies
    new_movies.sort(key=lambda t: t[0], reverse=True)

    log(f"Found {len(new_movies)} movies new since last run")
    log(f"Found {len(old_movies)} older movies")

    # start filling rotation
    current_count = len(current_links)
    to_fill = MAX_ROTATION_ITEMS - current_count
    added = 0

    def create_link(target: Path):
        nonlocal added
        link_path = ROTATION_DIR / target.name
        if link_path.exists():
            return
        try:
            os.symlink(str(target), str(link_path))
            added += 1
            log(f"Linked {link_path} -> {target}")
        except Exception as e:
            log(f"Error linking {target}: {e}")

    # 1. always bring in brand new movies first
    for _, movie in new_movies:
        if added >= to_fill:
            break
        if movie.name in current_link_names:
            continue
        create_link(movie)

    # 2. fill remaining slots with older stuff not yet linked
    if added < to_fill:
        # sort older movies alphabetically for stable behavior
        old_movies.sort(key=lambda p: p.name.lower())
        for movie in old_movies:
            if added >= to_fill:
                break
            if movie.name in current_link_names:
                continue
            create_link(movie)

    log(f"Rotation now has about {len(list_rotation_links())} items")

    # update state
    state["last_run"] = now_ts
    save_state(state)
    log("=== Rotation build complete ===")


if __name__ == "__main__":
    main()
