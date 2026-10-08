# PROJECT INTERVIEW PREP PROMPT
## (Point antigravity/Claude Code at the actual repo folder and run this)

---

You are reverse-engineering my codebase so I can explain it fluently in interviews.
Read EVERY file in this repo — not just the README.
Then produce TWO documents back-to-back, exactly as specified below.

---

# ═══════════════════════════════════════
# DOCUMENT 1: INTERVIEW NOTES V1
# Save as: [PROJECTNAME]_interview_notes.md
# ═══════════════════════════════════════

Produce a dense technical reference document with EXACTLY these 8 sections.
No filler. No "let's dive in." Dense bullets only.

---

## 1. TECH STACK AUDIT
- List every language, framework, library, DB, cloud service actually used
- Grep imports, requirements.txt, package.json — don't guess
- For each: one line on WHY it's used in THIS project specifically (not generic descriptions)

## 2. ARCHITECTURE MAP
- High-level system diagram in plain text (boxes + arrows)
- Data flow: input → processing → output, step by step, with actual file/function names
- Identify the 3–5 core files that do the real work vs boilerplate/scaffolding

## 3. KEY ALGORITHMS / LOGIC
- Every non-trivial algorithm, model, or logic block
- Plain English explanation first, then technical explanation
- Flag anything that looks generated, copied, or that I probably can't explain cold

## 4. DESIGN DECISIONS + TRADEOFFS
- For each major choice (DB, architecture pattern, model, sync/async, etc.):
  - What was chosen
  - Plausible alternative
  - Why this one wins or loses
- Call out naive/bad choices an interviewer would poke at

## 5. INTERVIEW-READY SUMMARY (STAR FORMAT)
- 30-second elevator pitch
- 2-minute deep version (problem → approach → implementation → result)
- STAR breakdown: Situation / Task / Action / Result (explicit)

## 6. ANTICIPATED QUESTIONS + ANSWERS
- 15 likely interviewer questions covering:
  - "Why did you do X?"
  - "What if you had to scale this?"
  - "What would you do differently?"
  - "Explain this specific function/algorithm"
  - "What was the hardest part?"
- Answer each in 2–4 sentences, technical, direct, no fluff

## 7. WEAK SPOTS TO PRE-EMPT
- Shallow, copy-pasted, or unjustified parts of the codebase
- Honest one-liner for each: how to answer if grilled, without bluffing

## 8. METRICS / RESULTS CHECK
- Every number already claimed in code/README/comments (accuracy, latency, epochs, dataset size, etc.)
- Flag any metric being cited that ISN'T backed by code/logs (so I don't get caught overclaiming)
- List what I should NOT cite without re-running evaluation

---

# ═══════════════════════════════════════
# DOCUMENT 2: OVERVIEW (PLAIN ENGLISH)
# Save as: [PROJECTNAME]_overview.md
# ═══════════════════════════════════════

Produce a plain-English overview. Zero jargon unless explained.
This is for explaining the project to anyone — technical or non-technical.
Use the exact sections below.

---

## THE PROBLEM YOU SOLVED
- What real-world problem does this project address?
- Who has this problem? Why does it hurt?
- What was the existing solution and why is it bad/missing?

## ONE SENTENCE VERSION
> One crisp sentence that captures what the project does.

## THE TWO (OR THREE) CORE IDEAS
- What are the 2–3 fundamental concepts the project is built on?
- Explain each in 2–3 sentences like you're talking to a smart non-engineer

## WHAT IT ACTUALLY DOES — THE USER JOURNEY
- Walk through the experience step by step from a user's perspective
- Separate flows if there are multiple user types (e.g., Admin vs Regular User)
- What does the user see, click, upload, receive?

## HOW IT WORKS — THE KEY MECHANISMS
- For each major technical mechanism: explain it with an analogy
- Format as a table: Mechanism | What It Checks | Analogy
- No code. Pure concept.

## THE KEY INNOVATION / DIFFERENTIATOR
- What is the one design decision or combination that makes this stand out?
- Why can't you just use X alone (without Y)?

## THE TECH, IN PLAIN ENGLISH
- Table: Component | What It Is (plain English) | Why This Was Used
- No version numbers. No implementation details. Just what it is and why.

## THE SYSTEM DIAGRAM (SIMPLE)
- ASCII art flowchart — input → processing steps → output
- Maximum 10 lines. Keep it scannable.

## INTERVIEW TALKING POINTS
Provide all three:

### 30 Seconds
[Write the exact words to say — rehearsal-ready]

### 2 Minutes
[Bullet outline of what to cover in order]

### 5 Minutes
[Additional depth to add: what extra concepts to explain]

## THE ONE THING THAT IMPRESSES PEOPLE
> One standout feature or insight, written as a memorable quote you can drop in any interview.

---

# HOW TO USE THIS PROMPT

1. Open antigravity (or Claude Code / Cursor) in the actual project repo folder
2. Paste this entire prompt
3. The AI will read all files and produce both documents automatically
4. Save outputs as:
   - PROJECTNAME_interview_notes.md
   - PROJECTNAME_overview.md
5. Before any interview:
   - 5-minute refresh → read Section 5 + 6 of interview_notes
   - 2-minute refresh → read "30 seconds" and "2 minutes" from overview

---

# PROJECTS TO RUN THIS ON

- [ ] Document Forensics
- [ ] IndusTech
- [ ] Early Exit DL
- [ ] Zombie Resource Hunter
