import json, random, re, threading
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import requests
import streamlit as st

MODEL = "qwen2.5:3b"  
OLLAMA = "http://localhost:11434"
PROFILE_FILE, LOG_FILE, SETTINGS_FILE = Path("profile.json"), Path("log.json"), Path("settings.json")

PLACES = ["room", "study", "common", "outside", "commute"]
PLACE_LABELS = {"room": "My room (hostel/home)", "study": "Library / classroom (silent)",
                "common": "Canteen / common area", "outside": "Outside / campus",
                "commute": "On the way / commuting"}
COMPANY_LABELS = {"alone": "Alone", "friends": "Friends / roommates nearby", "family": "Family around"}
TIMES = {"5 min": 5, "10 min": 10, "15 min": 15, "30 min": 30, "1 hour": 60, "2 hours": 120, "3+ hours": 200}
MOODS = ["tired", "restless", "bored", "stressed"]
ALL_C = ("alone", "friends", "family")
NOSTUDY = ["room", "common", "outside", "commute"]
HOME = ["room", "common", "outside"]

DEFAULT_PROFILE = {
    "name": "Sam",
    "goals": ["fitness", "reading", "creative", "social", "learning", "music"],
    "interests": ["chess", "anime", "lo-fi music", "space videos", "card games", "robotics", "coding",
                  "LeetCode problems", "keeping the room clean", "learning Japanese", "exercise"],
    "music": ["Coldplay", "Lady Gaga"],
    "friends": ["Alex", "Jordan"],
    "family": ["Mom", "Dad"],
    "gear": ["notebook"],
    "language_learning": "Japanese",
    "places": [
        {"name": "Campus ground", "minutes_away": 2, "cost": False},
        {"name": "City park", "minutes_away": 5, "cost": False},
        {"name": "College cafe", "minutes_away": 6, "cost": True},
    ],
    "watchlist": [
        {"title": "Example Anime", "minutes": 24, "offline": False},
        {"title": "Example Movie", "minutes": 120, "offline": False},
    ],
    "avoid": [],
    "notes": "Hostel student. Roommates are usually around in the evening. Likes exercise and chess. Wants to get better at coding. Prefers short, specific suggestions.",
}


def mk(id, text, cat, lo, hi, moods=None, places=PLACES, company=ALL_C, hours=(0, 24), online=False,
       cost=False, loud=False, intense=False, heavy=False, gear=(), need=(), interest=(), goals=(), tags=(), w=1.0):
    return dict(locals())

STATIC = [
    mk("stretch", "Stand up and stretch your neck, shoulders and back", "move", 3, 15),
    mk("walk_in", "Walk around your floor or corridor for 5 minutes, phone away", "move", 5, 20, places=["room", "study", "common"]),
    mk("walk_out", "Walk outside for 10 minutes, phone in pocket", "move", 10, 60, places=["room", "study", "common", "outside"], hours=(6, 22), goals=["fitness"]),
    mk("walk_with", "Ask someone nearby to take a short walk with you", "connect", 10, 60, company=("friends", "family"), places=HOME, hours=(6, 22), goals=["social", "fitness"]),
    mk("squats", "Do 15 squats and 10 push-ups (wall push-ups are fine)", "move", 3, 15, moods=["restless", "bored", "stressed"], places=["room", "outside"], hours=(6, 22.5), goals=["fitness"], tags=["exercise"]),
    mk("dance", "Put in earphones and dance for one full song", "move", 3, 15, moods=["restless", "bored", "stressed"], places=["room"], company=("alone",), hours=(7, 23), goals=["fitness", "music"]),
    mk("ball", "Get a quick game going with whoever is around: football, badminton, anything", "move", 30, 180, moods=["restless", "bored"], places=HOME, company=("friends",), hours=(6, 21), intense=True, goals=["fitness", "social"], tags=["exercise"]),
    mk("workout", "Do a solo workout: a short run or a bodyweight circuit", "move", 30, 120, moods=["restless", "bored", "stressed"], places=["room", "outside"], hours=(6, 21.5), intense=True, goals=["fitness"], tags=["exercise"]),
    mk("sketch", "Doodle or sketch anything for 10 minutes", "create", 5, 30, moods=["bored", "stressed", "restless"], gear=["notebook"], goals=["creative"]),
    mk("guitar", "Practice one chord change or riff on your guitar", "create", 10, 60, places=["room"], hours=(8, 22), loud=True, gear=["guitar"], goals=["music", "creative"]),
    mk("write", "Write 5 honest sentences about your day or what's on your mind", "create", 5, 30, moods=["stressed", "bored", "tired"], gear=["notebook"], places=["room", "study", "common", "outside"], goals=["creative"]),
    mk("project", "Make one tiny thing: a small script, edit, poster or design", "create", 30, 240, moods=["bored", "restless"], places=["room", "study", "common"], heavy=True, goals=["creative", "learning"]),
    mk("photo", "Take 5 interesting photos of ordinary things around you", "create", 10, 45, moods=["bored", "restless"], places=["common", "outside"], hours=(6, 18.5), goals=["creative"]),
    mk("call_friend", "Call or voice-message one friend from your list", "connect", 5, 60, places=["room", "common", "outside"], hours=(9, 22), need=["friends"], goals=["social"]),
    mk("msg_friend", "Text a friend you haven't talked to in a while", "connect", 3, 15, hours=(8, 23), need=["friends"], goals=["social"]),
    mk("family", "Call or send a voice note to someone in your family", "connect", 3, 30, places=NOSTUDY, hours=(8, 22), need=["family"], goals=["social"]),
    mk("chat_near", "Sit and talk with someone nearby for 10 minutes, phones away", "connect", 10, 60, company=("friends", "family"), places=HOME, goals=["social"]),
    mk("chai", "Ask someone nearby to grab chai or a snack with you", "connect", 20, 120, company=("friends",), places=HOME, hours=(7, 22), cost=True, goals=["social"]),
    mk("group_game", "Ask people nearby for a quick card or word game", "fun", 15, 90, moods=["bored", "restless"], company=("friends", "family"), places=HOME, loud=True, goals=["social"]),
    mk("short_video", "Watch one short video about something you're curious about, then stop", "learn", 5, 30, moods=["bored", "tired", "stressed"], places=NOSTUDY, online=True, goals=["learning"]),
    mk("new_words", "Learn 5 new words in the language you're learning", "learn", 5, 20, need=["language_learning"], goals=["learning"]),
    mk("read", "Read a few pages of a book or one long article", "learn", 10, 60, moods=["bored", "stressed"], heavy=True, goals=["reading"]),
    mk("read_about", "Read about a project or idea from your interests that you've never tried", "learn", 30, 180, moods=["bored", "restless"], places=["room", "study", "common"], online=True, heavy=True, goals=["learning"]),
    mk("podcast", "Listen to a podcast or talk on something you like, earphones in", "learn", 10, 60, moods=["tired", "bored", "stressed"], places=["room", "common", "outside", "commute"], online=True, goals=["learning"]),
    mk("breathe", "Close your eyes and breathe slowly for 2 minutes: in for 4 seconds, out for 6", "rest", 3, 15),
    mk("eyes", "Drink some water and look at something far away for 2 minutes", "rest", 3, 10),
    mk("nap", "Set an alarm and take a 15 minute nap", "rest", 15, 30, moods=["tired"], places=["room"], hours=(12, 17)),
    mk("lie_down", "Lie down with earphones, eyes closed and no screen for 10 minutes", "rest", 10, 30, moods=["tired", "stressed"], places=["room"]),
    mk("daylight", "Step outside and stand in daylight for 5 minutes", "rest", 5, 15, moods=["tired", "stressed"], places=["room", "study", "common", "outside"], hours=(7, 17.5)),
    mk("music", "Listen to a few songs by one artist you like, earphones in, nothing else open", "rest", 5, 40, moods=["tired", "stressed", "bored"], need=["music"], goals=["music"]),
    mk("tidy", "Clear and tidy just your desk for 5 minutes", "rest", 5, 15, moods=["stressed", "restless", "bored"], places=["room"]),
    mk("plan", "Write tomorrow's top 3 tasks on paper", "rest", 5, 10, moods=["stressed"], gear=["notebook"], places=["room", "study", "common"], hours=(17, 24)),
    mk("snack", "Make yourself a simple snack or chai", "rest", 10, 40, places=["room"], hours=(7, 22), gear=["kitchen"]),
    mk("puzzle", "Do one quick puzzle: sudoku, a chess puzzle or a riddle", "fun", 5, 30, moods=["bored", "restless"], heavy=True),
    mk("funny", "Watch one funny video, just one, then put the phone down", "fun", 3, 15, moods=["stressed", "tired", "bored"], places=NOSTUDY, online=True),
    mk("timed_scroll", "If you really need a mindless scroll, set a 10 minute timer first and stop when it rings", "rest", 5, 20, moods=["tired", "stressed"], w=0.4),
    mk("leetcode", "Solve one easy LeetCode problem, or redo one you got wrong before", "learn", 20, 90, moods=["bored", "restless"], places=["room", "study", "common"], online=True, heavy=True, interest=["leetcode"], goals=["learning"]),
    mk("code_idea", "Write down one small coding or robotics project idea in your notebook", "create", 5, 20, gear=["notebook"], interest=["coding", "robot"], goals=["creative"]),
    mk("robot_video", "Watch one short video on how a robot or machine works, then stop", "learn", 5, 30, moods=["bored", "tired", "stressed"], places=NOSTUDY, online=True, interest=["robot"], goals=["learning"]),
    mk("space_video", "Watch one short space video, then stop", "learn", 5, 30, moods=["bored", "tired", "stressed"], places=NOSTUDY, online=True, interest=["space"], goals=["learning"]),
    mk("chess_puzzles", "Solve 3 chess puzzles", "fun", 5, 30, moods=["bored", "restless"], online=True, heavy=True, interest=["chess"]),
    mk("chess_game", "Ask someone nearby for a quick game of chess", "fun", 15, 60, moods=["bored", "restless"], company=("friends",), places=HOME, interest=["chess"], goals=["social"]),
    mk("cards", "Start a quick round of cards with whoever is around", "fun", 15, 90, moods=["bored", "restless"], company=("friends",), places=HOME, loud=True, interest=["card"], goals=["social"]),
    mk("plank", "Hold a plank for 30 seconds, rest, and repeat 3 times", "move", 3, 15, moods=["restless", "bored", "stressed"], places=["room", "outside"], hours=(6, 22.5), goals=["fitness"], tags=["exercise"]),
    mk("room_reset", "Do a 10 minute room reset: make the bed, clear the desk, sweep the floor", "rest", 10, 30, moods=["stressed", "restless", "bored"], places=["room"], hours=(7, 23), interest=["clean"]),
]
SAFE = next(a for a in STATIC if a["id"] == "breathe")


def dynamic(p):
    """Candidates built from the person's own saved places and watchlist, with real travel/runtime maths."""
    out = []
    for pl in p.get("places", []):
        trip = 2 * pl["minutes_away"] + 10
        out.append(mk(f"place:{pl['name']}", f"Walk to {pl['name']} ({pl['minutes_away']} min away), spend a few minutes there, then head back",
                      "fun", trip, 400, moods=["bored", "restless", "stressed"], places=["room", "study", "common", "outside"],
                      hours=(6, 21.5), cost=pl.get("cost", False), goals=["fitness"]))
    for m in p.get("watchlist", []):
        out.append(mk(f"watch:{m['title']}", f"Watch '{m['title']}' from your watchlist ({m['minutes']} min)", "fun", m["minutes"] + 5, 600,
                      moods=["bored", "tired", "stressed"], places=["room", "common"], hours=(6, 23), online=not m.get("offline", False)))
    lang = p.get("language_learning")
    if lang:
        out.append(mk("lang_write", f"Write 5 {lang} words or characters by hand and say each one out loud", "learn", 5, 25, gear=["notebook"], goals=["learning"]))
    return out


def feasible(a, c, p):
    h = c["hour"]
    return (c["place"] in a["places"] and c["company"] in a["company"]
            and a["lo"] <= c["minutes"] <= a["hi"] and a["hours"][0] <= h < a["hours"][1]
            and not (a["loud"] and (h >= 22 or h < 7))
            and not (a["online"] and not c["online"])
            and not (a["cost"] and not c["can_spend"])
            and not (a["intense"] and c["mood"] == "tired")
            and not (c["mood"] == "tired" and ((a["moods"] and "tired" not in a["moods"])
                                               or (not a["moods"] and a["cat"] in ("learn", "create"))))
            and not (a["heavy"] and c["after"] == "studying" and c["minutes"] <= 30)
            and all(g in p.get("gear", []) for g in a["gear"])
            and all(p.get(k) for k in a["need"])
            and (not a["interest"] or any(k in x.lower() for k in a["interest"] for x in p.get("interests", [])))
            and not set(a["tags"]) & set(p.get("avoid", [])))


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def log_event(event, a):
    log = load(LOG_FILE, [])
    log.append({"time": datetime.now().isoformat(timespec="seconds"), "id": a["id"], "cat": a["cat"], "event": event})
    LOG_FILE.write_text(json.dumps(log, indent=1), encoding="utf-8")


def weight(a, c, p, log):
    w, now = a["w"], datetime.now()
    if a["moods"]:
        w *= 2 if c["mood"] in a["moods"] else 0.2
    if set(a["goals"]) & set(p.get("goals", [])):
        w *= 1.5
    if a["interest"]:
        w *= 1.5 
    done = sum(1 for e in log if e["event"] == "done" and e["cat"] == a["cat"] and now - datetime.fromisoformat(e["time"]) < timedelta(days=7))
    w /= 1 + done 
    for e in log[-30:]:
        if e["id"] == a["id"]:
            age = now - datetime.fromisoformat(e["time"])
            if e["event"] == "shown" and age < timedelta(hours=3): w *= 0.2
            if e["event"] == "skipped" and age < timedelta(hours=24): w *= 0.3
            if e["event"] == "cant" and age < timedelta(days=3): w *= 0.05
    return w


def candidates(c, p, seen, n=5):
    log = load(LOG_FILE, [])
    pool = [a for a in STATIC + dynamic(p) if feasible(a, c, p)]
    fresh = [a for a in pool if a["id"] not in seen]
    pool = fresh or pool
    ws, out = [weight(a, c, p, log) for a in pool], []
    while pool and len(out) < n:
        i = random.choices(range(len(pool)), ws)[0]
        out.append(pool.pop(i)); ws.pop(i)
    return out or [SAFE]


SYSTEM = """You write one short, friendly suggestion for a college student on a break, so they don't doom-scroll.
The activity is ALREADY chosen and is possible for them right now. Only word it nicely.
RULES
1. Do not change the activity or add requirements (no extra people, equipment or travel).
2. Use only facts from CONTEXT and PROFILE. Never invent people, places, titles, prices or weather. A name may appear only if it is in PROFILE or in the activity.
3. message: max 2 short sentences, like a friend texting. No lecture about phones, no guilt, no emojis.
4. first_step: one concrete action doable in 10 seconds, max 12 words.
Reply with JSON only: {"message": "...", "first_step": "..."}
Example: {"message": "You've been sitting a while, so stand up and stretch your back. Two minutes will help.", "first_step": "Stand up and roll your shoulders back."}"""


def has_unknown_names(msg, allowed):
    allowed = allowed.lower()
    for sent in re.split(r"(?<=[.!?])\s+", msg.strip()):
        for w in sent.split()[1:]:
            w = w.strip(".,!?;:\"'()")
            if w[:1].isupper() and w != "I" and not w.startswith("I'") and w.lower() not in allowed:
                return True
    return False


def ask(p, c, cands):
    """Python already picked cands[0]. The model only words it (short prompt = fast)."""
    a = cands[0]
    small = {k: p.get(k) for k in ("name", "interests", "music", "friends", "family", "language_learning", "notes")}
    ctx = f"{PLACE_LABELS[c['place']]}; {COMPANY_LABELS[c['company']]}; {c['clock']}; {c['minutes']} min free; feeling {c['mood']}."
    user = f"CONTEXT: {ctx}\nPROFILE: {json.dumps(small)}\nACTIVITY: {a['text']}"
    allowed = json.dumps(p) + " " + a["text"]
    try:
        r = requests.post(f"{OLLAMA}/api/chat", timeout=60, json={
            "model": MODEL, "stream": False, "format": "json", "keep_alive": "30m",
            "options": {"temperature": 0.5, "num_predict": 120, "num_ctx": 1536},
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]})
        r.raise_for_status()
        d = json.loads(r.json()["message"]["content"])
        msg, step = str(d["message"]).strip(), str(d["first_step"]).strip()
        if 0 < len(msg) <= 300 and 0 < len(step) <= 100 and not has_unknown_names(msg + " " + step, allowed):
            return a, msg, step
    except requests.exceptions.ConnectionError:
        raise
    except Exception:
        pass
    return a, a["text"] + ".", "Start now, phone face down." 


@st.cache_resource
def warm_model():
    """Load the model into memory in the background so the first click isn't slow."""
    def go():
        try:
            requests.post(f"{OLLAMA}/api/generate", json={"model": MODEL, "prompt": "", "keep_alive": "30m"}, timeout=180)
        except Exception:
            pass
    threading.Thread(target=go, daemon=True).start()
    return True


@st.cache_data(ttl=60)
def model_status():
    try:
        names = [m["name"] for m in requests.get(f"{OLLAMA}/api/tags", timeout=2).json()["models"]]
        return "ok" if MODEL in names or f"{MODEL}:latest" in names else "missing"
    except Exception:
        return "down"


# ---------------- UI ----------------
st.set_page_config(page_title="Break Buddy", page_icon="🌿")
warm_model()
st.title("🌿 Break Buddy")
st.caption("Runs on this computer only. Nothing leaves it.")

if not PROFILE_FILE.exists():
    PROFILE_FILE.write_text(json.dumps(DEFAULT_PROFILE, indent=2), encoding="utf-8")
profile = load(PROFILE_FILE, DEFAULT_PROFILE)
S = st.session_state
S.setdefault("cur", None); S.setdefault("doing", False); S.setdefault("seen", set()); S.setdefault("ctx", None)
DEFAULTS = {"tlabel": "10 min", "mood": "tired", "place": "room", "company": "alone",
            "studying": True, "online": True, "spend": False}
VALID = {"tlabel": list(TIMES), "mood": MOODS, "place": PLACES, "company": list(COMPANY_LABELS)}
saved = {k: v for k, v in load(SETTINGS_FILE, {}).items() if k in DEFAULTS and (k not in VALID or v in VALID[k])}
for k, v in {**DEFAULTS, **saved}.items():
    S.setdefault(k, v)

MOOD_L = {"tired": "😴 Tired", "restless": "⚡ Restless", "bored": "😐 Bored", "stressed": "😣 Stressed"}
PLACE_S = {"room": "🛏 Room", "study": "📚 Library", "common": "🍽 Canteen", "outside": "🌳 Outside", "commute": "🚌 Travelling"}
COMP_S = {"alone": "Alone", "friends": "With friends", "family": "With family"}


def read_ctx():
    now = datetime.now()
    g = lambda k, d: S.get(k) or d
    return {"place": g("place", "room"), "company": g("company", "alone"), "minutes": TIMES[g("tlabel", "10 min")],
            "mood": g("mood", "tired"), "after": "studying" if S.get("studying", True) else "free time",
            "online": S.get("online", True), "can_spend": S.get("spend", False),
            "hour": now.hour + now.minute / 60, "clock": now.strftime("%H:%M")}


def suggest():
    c = S.ctx
    try:
        with st.spinner("Picking something for you..."):
            a, msg, step = ask(profile, c, candidates(c, profile, S.seen))
    except requests.exceptions.ConnectionError:
        S.cur = None
        S.err = "Can't reach Ollama. Open the Ollama app (or run `ollama serve`) and try again."
        return
    S.err = None
    S.seen.add(a["id"]); S.cur = (a, msg, step); S.doing = False
    log_event("shown", a)


def on_get():
    S.ctx = read_ctx(); S.seen = set()
    vals = {k: (DEFAULTS[k] if S.get(k) is None else S.get(k)) for k in DEFAULTS}
    SETTINGS_FILE.write_text(json.dumps(vals), encoding="utf-8") 
    suggest()


def on_other():
    log_event("skipped", S.cur[0]); suggest()


def on_cant():
    log_event("cant", S.cur[0]); suggest()


def on_start():
    log_event("started", S.cur[0]); S.doing = True


def on_done():
    log_event("done", S.cur[0]); S.cur = None; S.doing = False; S.celebrate = True


def pick(label, options, key, default, fmt):
    st.markdown(f"**{label}**")
    if hasattr(st, "pills"):
        st.pills(label, options, key=key, format_func=fmt, label_visibility="collapsed")
    else:
        st.radio(label, options, key=key, format_func=fmt,
                 horizontal=True, label_visibility="collapsed")


with st.sidebar:
    status = model_status()
    if status == "missing":
        st.warning(f"Model not installed. Run: ollama pull {MODEL}")
    elif status == "down":
        st.warning("Ollama isn't running.")
    st.subheader("This week")
    week = Counter(e["cat"] for e in load(LOG_FILE, []) if e["event"] == "done"
                   and datetime.now() - datetime.fromisoformat(e["time"]) < timedelta(days=7))
    st.write(dict(week) if week else "Nothing finished yet.")
    with st.expander("Edit profile (JSON)"):
        txt = st.text_area("profile.json", json.dumps(profile, indent=2), height=300)
        if st.button("Save profile"):
            try:
                PROFILE_FILE.write_text(json.dumps(json.loads(txt), indent=2), encoding="utf-8"); st.rerun()
            except Exception as e:
                st.error(f"Invalid JSON: {e}")

pick("How much time?", list(TIMES), "tlabel", "10 min", str)
pick("How do you feel?", MOODS, "mood", "tired", MOOD_L.get)
pick("Where are you?", PLACES, "place", "room", PLACE_S.get)
pick("Who's around?", list(COMPANY_LABELS), "company", "alone", COMP_S.get)
with st.expander("More options"):
    st.checkbox("I was just studying", key="studying")
    st.toggle("Internet works", key="online")
    st.toggle("OK to spend a little money", key="spend")

st.button("✨ What should I do?", type="primary", use_container_width=True, on_click=on_get)
if S.get("err"):
    st.error(S.err)
if S.pop("celebrate", False):
    st.balloons(); st.success("Logged. Nice work.")

if S.cur:
    a, msg, step = S.cur
    with st.container(border=True):
        st.markdown(f"### {msg}")
        st.write(f"**Start with:** {step}")
    b1, b2, b3 = st.columns(3)
    b1.button("👍 Let's do it", on_click=on_start, use_container_width=True)
    b2.button("🔄 Another", on_click=on_other, use_container_width=True)
    b3.button("🚫 Can't now", on_click=on_cant, use_container_width=True)
    if S.doing:
        st.info("Go. Phone down. Come back when you're done.")
        st.button("✅ I finished", on_click=on_done, type="primary", use_container_width=True)