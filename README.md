# Rotating Movie Library System  
A structured method for keeping a large media archive fresh through controlled rotation, symbolic linking, and stable separation of core and non core titles.

---

## Purpose

Large libraries work against the brain over time. When the environment becomes too stable, interest fades, even if the content is good. Research from NASA’s Behavioral Health and Performance division, along with studies of Antarctic overwinter personnel and other long duration confinement groups, shows a consistent pattern. People need novelty at regular intervals to sustain motivation, curiosity, and emotional stability. When novelty drops below that threshold, perception flattens. Activities that were once engaging start to feel automatic.

I experienced the same drift in my own media collection. After many years building the library, perfecting the layout, and curating thousands of titles, the sense of discovery weakened. The library did not change even as I did. I found myself choosing familiar movies out of habit, not interest. The collection had turned into a closed loop. It was too large to explore fully, too static to surprise me, and too predictable to spark new engagement.

This project solves that problem by creating a living section of the library that changes on a predictable schedule. It preserves the archive, keeps favorites protected, and creates a rotation pool that remains small enough to feel curated but large enough to offer real variety.

---

## Directory Structure

You must create the following directories:

```
/mnt/movies
/mnt/core_movies
/mnt/rotation_movies
```

### `/mnt/movies`  
The complete archive. Every movie file or folder resides here. Nothing in this directory should be touched or moved by hand once the system is stable.

### `/mnt/core_movies`  
The protected library. Titles placed here remain available at all times. This directory can be set read only to avoid accidental edits. Add only the films you want permanent access to.

### `/mnt/rotation_movies`  
The active catalog. The script populates this directory using symbolic links pointing to the real files inside `/mnt/movies`. Linking avoids file loss, disc thrashing, and long transfer times. The rotation directory feels like a curated shelf that changes with each run.

---

## Why a Rotation System Matters

Psychological research shows that people respond best to environments that shift gently over time. Three findings matter here.

1. Long duration confinement studies show reduced cognitive engagement when the environment becomes monotonous  
2. NASA’s isolation research notes that novelty boosts attention, mood, and sense of agency  
3. Overwinter personnel in polar stations report improved resilience when exposed to small but frequent changes  
4. Digital environments behave the same way because the user treats them as part of their perceptual surroundings

A large static library creates a subtle form of mental isolation. The individual interacts with the same structure every time. Even if new movies are added, the scale of the archive hides them. The brain stops registering change, and choice becomes routine. Without rotation, the library eventually feels like the same set of options in a different order.

The rotation system fixes this by forcing novelty to the surface. Fresh titles appear quickly. Older titles reappear in a stable rhythm. The library stays familiar enough to be comfortable but dynamic enough to feel alive.

---

## Mission of the Script

The script manages the rotation directory by scanning three sources: the full library, the core library, and the rotation shelf. It classifies all non core titles as new or old based on modification time.

Its core operations are:

1. Remove old or broken symbolic links so the rotation directory stays clean  
2. Identify new titles added since the last run  
3. Fill available rotation slots with new titles first  
4. Fill remaining space with older titles in alphabetical order

It uses symbolic links to avoid moving files, which prevents data loss and reduces disc operations. The underlying archive remains unmodified at all times.

A timestamp file saved at the end of the run allows the script to track what has changed in the archive.

---

## Why the Size Ratios Matter

The rotation directory uses a specific scale because of how humans process large collections.

1. A rotation size near one thousand items feels substantial without overwhelming the mind. Cognitive load studies show that people interact more consistently with sets below the high overload threshold.  
2. The rotation must be large enough to avoid repetition. If the pool is too small, the rotation becomes predictable. A thousand items produces enough variation to break habitual viewing cycles.  
3. The link age limit of thirty days creates a predictable rhythm. A month is long enough for a person to watch or sample titles but short enough to prevent stagnation.  
4. The ratio of core to rotation follows a pattern that supports both stability and novelty. Roughly three times as many rotation items as core items ensures that the permanent favorites remain fixed while the active shelf feels different each time you return to it.

This ratio comes from direct observation and from research on how novelty supports long term engagement. The larger rotation pool continuously introduces new entries without overwhelming the user with a second full archive.

---

## Installation

1. Place the script in any location on the system  
2. Ensure the three directories listed above exist  
3. Run the script manually to generate the first rotation set  
4. Optionally schedule the script with cron or systemd timers  

Example cron entry:

```
0 3 * * * /usr/bin/python3 /path/to/script.py
```

This example runs the script once per day at 3 AM.

---

## Safety Considerations

The script uses symbolic links to avoid dangerous operations. Even so, a few good practices apply.

1. Do not store any unrelated files inside the rotation directory  
2. Avoid modifying the archive while the script is running  
3. Keep the core directory separate and treat it as protected  
4. Maintain backups of the archive on a separate storage system

This system assumes the archive is stable. It does not attempt to repair damaged files or reorganize directory structures.

---

## Performance Notes

The script performs a flat scan of `/mnt/movies`. On large libraries with many thousands of entries, this is fast enough on SSDs and acceptable on spinning drives. Link creation is lightweight and does not stress the filesystem.

The script keeps no heavy metadata. It only tracks timestamps and directory names. This keeps the tool durable across upgrades.

---

## Extending the System

You can enhance the system in several ways:

1. Add genre based rotation by tagging directories  
2. Create separate rotation pools for TV, documentaries, or anime  
3. Add a logging dashboard to track watch patterns  
4. Introduce weight based selection that favors some categories over others

The script is intentionally simple so that extensions remain easy.

---

## Final Note

Your core library should match your taste, not a number. Add as many fixed favorites as you want. After that, build your full archive so that the rotation section is roughly three times the size of the core. This keeps the experience fresh over the long term without eroding the stability of your permanent set.
