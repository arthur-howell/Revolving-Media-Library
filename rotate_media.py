#!/usr/bin/env python3
import os
import json
import time
from pathlib import Path

# ===== CONFIG =====
# These directories define the structure of the entire media system.
# MOVIES_DIR is the full archive.
# CORE_DIR is the protected library of permanent titles.
# ROTATION_DIR is the curated rotating shelf built using symbolic links.
MOVIES_DIR = Path("/mnt/movies")
CORE_DIR = Path("/mnt/core_movies")
ROTATION_DIR = Path("/mnt/rotation_movies")

# LOG_DIR stores small state files that let the rotation system track its activity over time.
LOG_DIR = Path("/mnt/movies/.logs")

# CORE_CACHE_FILE was used by a previous version of this project.
# It remains here for compatibility. You can remove it if unused.
CORE_CACHE_FILE = LOG_DIR / "core_hashes.json"

# STATE_FILE stores the timestamp of the last run so the script can identify new files.
STATE_FILE = LOG_DIR / "rotation_state.json"

# Maximum number of rotation entries allowed at any given time.
# This number comes from cognitive load research and long term observation.
# Around a thousand items is large enough to provide variety but small enough to feel curated.
MAX_ROTATION_ITEMS = 1000

# Symbolic links older than this number of days are removed.
# This gives the system a predictable rhythm and prevents the rotation shelf from going stale.
LINK_MAX_AGE_DAYS = 30

# Names that should be ignored during scans of the archive.
# These are noise files created by macOS, Synology, Syncthing, and similar tools.
IGNORE_NAMES = {".DS_Store", "@eaDir", ".stfolder", ".stversions"}

# Ensure required directories exist. This prevents failures on first run.
LOG_DIR.mkdir(parents=True, exist_ok=True)
ROTATION_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    """Simple timestamped logger so each step can be seen clearly in the terminal."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_state():
    """Load the previous run's timestamp. If none exists, assume this is the first run."""
    if not STATE_FILE.exists():
        return {"last_run": 0}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict):
    """Save the timestamp of the current run so the next execution can detect new entries."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def load_core_dirnames() -> set[str]:
    """
    Load names of all files or directories inside the core library.
    Anything in CORE_DIR is treated as permanent and never included in rotation.
    """
    names = set()
    if CORE_DIR.exists():
        for p in CORE_DIR.iterdir():
            if p.is_dir() or p.is_file():
                names.add(p.name)
    return names


def list_rotation_links():
    """
    Return a list of all symbolic links in the rotation directory.
    Only links matter because the rotation shelf should contain no real files.
    """
    links = []
    for p in ROTATION_DIR.iterdir():
        if p.is_symlink():
            links.append(p)
    return links


def remove_old_links(links):
    """
    Remove symbolic links that have aged past the configured limit.
    This ensures the rotation shelf does not become stale.
    """
    now = time.time()
    cutoff = now - (LINK_MAX_AGE_DAYS * 24 * 60 * 60)
    removed = 0
    for link in links:
        try:
            st = link.lstat()
            # Remove links older than the cutoff.
            if st.st_mtime < cutoff:
                link.unlink(missing_ok=True)
                removed += 1
        except FileNotFoundError:
            # Broken links should always be removed.
            link.unlink(missing_ok=True)
            removed += 1
        except Exception as e:
            log(f"Warning removing old link {link}: {e}")
    if removed:
        log(f"Removed {removed} old rotation links")
    return removed


def scan_movies():
    """
    Scan the full archive.
    Only real movie folders or files are collected.
    Noise entries are filtered out.
    """
    items = []
    for entry in MOVIES_DIR.iterdir():
        if entry.name in IGNORE_NAMES:
            continue
        if entry.is_dir() or entry.is_file():
            items.append(entry)
    return items


def main():
    log("=== Rotation build start ===")
    state = load_state()
    last_run_ts = state.get("last_run", 0)

    # Load names of core movies so they can be excluded from rotation logic.
    core_names = load_core_dirnames()
    log(f"Loaded {len(core_names)} core names")

    # Load current symbolic links in rotation and clear out stale ones.
    current_links = list_rotation_links()
    remove_old_links(current_links)
    current_links = list_rotation_links()
    current_link_names = {p.name for p in current_links}

    # Collect all media from the archive for sorting.
    all_movies = scan_movies()
    now_ts = time.time()

    # Separate new movies from older ones based on modification timestamp.
    # New movies always take priority in rotation so fresh content is surfaced immediately.
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

    # Sort new entries by newest first.
    new_movies.sort(key=lambda t: t[0], reverse=True)

    log(f"Found {len(new_movies)} movies new since last run")
    log(f"Found {len(old_movies)} older movies")

    # Determine how many new rotation entries can be added.
    current_count = len(current_links)
    to_fill = MAX_ROTATION_ITEMS - current_count
    added = 0

    def create_link(target: Path):
        """
        Create a symbolic link inside the rotation directory pointing to the real file.
        Linking avoids moving data and prevents filesystem wear.
        """
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

    # First wave: add new movies.
    # This ensures the rotation shelf always highlights recently added items.
    for _, movie in new_movies:
        if added >= to_fill:
            break
        if movie.name in current_link_names:
            continue
        create_link(movie)

    # Second wave: fill any remaining slots with older items.
    # Sorted alphabetically for consistent behavior across runs.
    if added < to_fill:
        old_movies.sort(key=lambda p: p.name.lower())
        for movie in old_movies:
            if added >= to_fill:
                break
            if movie.name in current_link_names:
                continue
            create_link(movie)

    log(f"Rotation now has about {len(list_rotation_links())} items")

    # Save the current timestamp for use in the next run.
    state["last_run"] = now_ts
    save_state(state)
    log("=== Rotation build complete ===")


if __name__ == "__main__":
    main()

