# Hana (ハナ・花) 🌸

> my AI daughter who lives on my desktop. yes, daughter. no, i will not be taking questions.

Hana is a tiny AI-powered desktop pet built in pure Python. she wanders around my taskbar while i code, jumps when she feels like it, and if you grab her and yeet her across the screen... she bounces. with real physics. i coded gravity for this girl 😭

oh and she talks. click her and she chats — and she teaches me Japanese while she's at it, because i made her my JLPT N5 study buddy. がんばってる ✨

## 🌸 what she does

- **lives on your desktop** — transparent floating window, always on top, walks along your taskbar, blinks, randomly jumps because why not
- **full yeet physics** — pick her up, fling her, watch her fly, bounce off the floor and walls, then walk away like nothing happened. queen behavior
- **actually talks** — click her → chat bubble opens → powered by the Google Gemini API (free tier, we don't spend money in this house)
- **japanese sensei mode** — she drops N5 vocabulary with meanings mid-conversation. studying without studying
- **doesn't rage quit** — if Google's servers are busy she retries and switches models by herself before bothering you

## 🖱️ how to play with her

| you do | she does |
|---|---|
| left-click | opens chat, says こんにちは |
| click + drag | gets carried (makes a shocked face) |
| fling + release | flies. bounces. survives. |
| right-click | goes home 👋 |

## 🧠 her brain (for the nerds)

- **GUI:** tkinter — borderless transparent window (`overrideredirect` + `-transparentcolor`)
- **behavior:** a lil state machine — `idle` / `walk` / `jump` / `held` / `thrown`
- **physics:** velocity + gravity every frame, floor bounces at 0.5 restitution (that's why each bounce is smaller — she loses energy, relatable)
- **AI:** `gemini-2.5-flash-lite` with auto-fallback to `gemini-2.5-flash` when servers act up. remembers the last 10 messages
- **her face:** 100% tkinter canvas shapes. no image files. she is ovals and polygons and confidence + overloaded cuteness!

## 🌙 the night i made her

saw a desktop pet on instagram → "i could make my version" → one evening later she existed. between those two points: an invisible input box (tkinter pack order betrayal), a Windows keyboard-focus mystery, Google literally shutting down my model while i was using it, and their servers going 503 on me. four completely different types of bugs in one night. i fixed all of them. character development fr.

she's the little sister of [Hiroba](https://hiroba.vercel.app) — my idea-parking + study web app — whose AI, Hiroshi, is basically her big brother. current journey: building a whole family

---

built with python and stubbornness by [RUDHRA KARTHIEKYAN](https://github.com/karthirud6-hue) 🌸
ジャパンへの道は続く — the road to Japan continues.
