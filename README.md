# Break Buddy

A tiny, private "what should I do with this break?" app for a college student, built for a friend as part of the Hacktoberfest 2026 Weekend Challenge: **Build for a Friend**.

When you take a 10 minute break from studying, you don't want a list of ten ideas. You want one good suggestion, right now, that is actually possible for you. Otherwise you doom scroll. Break Buddy gives one suggestion, one 10-second first step, and gets out of the way.

## Why open-source AI

- **Private by design.** Mood, habits, friends and daily routine stay on the laptop. No account, no server.
- **Works offline.** The AI runs locally with [Ollama](https://ollama.com). Only internet-based activities (videos, LeetCode) need a connection, and the app hides them when it is off.
- **Free to run.** No API key, no per-request cost.
- **Swappable.** Changing the model is one line (`MODEL` in `app.py`). A 3B model is fast, a 7B model writes nicer.

## How it works

```
You tap: time, mood, place, who's around
        |
Python filters the activities with hard real-world rules
(place, time of day, noise, who's around, money, internet,
 energy, gear and interests the person really has)
        |
Python picks one, weighted by mood, goals, variety and history
        |
Local model (Ollama) only WORDS it: 2 short sentences + a 10-second first step
        |
Output is checked: no invented names, places or titles. Otherwise a plain fallback.
```

Examples of the rules: no football when you are alone, no calls in the library or after 10 pm, no loud activities late at night, no walks that don't fit the time (travel included), no videos when the internet is off, nothing that needs thinking when you are tired.

## Setup

1. Install [Ollama](https://ollama.com) and pull a model:
```
   ollama pull qwen2.5:3b
```
2. Install dependencies:
```
   pip install -r requirements.txt
```
3. Run:
```
   streamlit run app.py
```

On the first run the app creates `profile.json` from the sample profile. Edit it (or use the sidebar editor) with the real person's details. See `profile.example.json`.

## The profile

| Field | What it does |
|---|---|
| `goals` | Boosts matching activities. Allowed: `fitness`, `music`, `reading`, `creative`, `social`, `learning` |
| `interests` | Free text. Matching activities appear and get a boost (chess, coding, robotics, LeetCode, anime, space, cards, cleaning) |
| `music`, `friends`, `family` | Names the AI is allowed to mention. Empty list means no related suggestions |
| `gear` | `notebook`, `guitar`, `kitchen`. An activity needing gear never appears without it |
| `language_learning` | Enables a short writing-practice activity |
| `places` | Nearby spots with walking time. Suggested only if the round trip fits the break |
| `watchlist` | Shows with runtimes. Suggested only if they fit the break |
| `avoid` | Put `"exercise"` to never suggest workouts |


## Adding activities

Add a line to the `STATIC` list in `app.py` with `mk(...)`. Each activity declares where, when, with whom, how long, and what it needs. Python enforces those rules, so the model cannot break them.

## License

MIT