# Example Session: Building Your Wiki

> This shows a real conversation flow between a user and their AI assistant using the LLM Wiki schema.

---

## Step 1: User Sends an Article

**User:**
> Here's a great article about prompt engineering: https://example.com/prompt-tips
> Add it to my wiki.

**AI does:**
1. Fetches the article content
2. Saves to `raw/articles/2024-04-01-prompt-engineering-tips.md`
3. Creates `pages/sources/prompt-engineering-tips-summary.md`
4. Creates `pages/concepts/prompt-engineering.md` (new concept!)
5. Updates `index.md`

**AI responds:**
> ✅ Added to your wiki:
> - Saved raw source (5,200 words)
> - Created concept page: **Prompt Engineering** (new!)
> - Created source summary: Prompt Engineering Tips
> - Index updated (3 pages total)

---

## Step 2: User Adds a Related Article Later

**User:**
> Just read this — it's about Chain of Thought prompting: https://example.com/cot-prompting
> Wiki this.

**AI does:**
1. Saves to `raw/articles/2024-04-05-chain-of-thought-prompting.md`
2. Creates `pages/sources/cot-prompting-summary.md`
3. **Updates** existing `pages/concepts/prompt-engineering.md` with CoT section
4. Updates `index.md`

**AI responds:**
> ✅ Added to your wiki:
> - Saved raw source (3,100 words)
> - **Updated** concept page: **Prompt Engineering** — added Chain of Thought section (now 2 sources!)
> - Created source summary: Chain of Thought Prompting
> - Index updated (4 pages total)

**This is knowledge compounding in action** — the concept page gets richer with every new source.

---

## Step 3: User Asks a Question

**User:**
> What do I know about prompt engineering?

**AI responds:**
> Based on your wiki (2 sources):
>
> **Prompt Engineering** is [synthesized knowledge from both articles]...
>
> Key techniques you've collected:
> 1. [From source 1]
> 2. Chain of Thought prompting [From source 2]
>
> Sources: prompt-engineering-tips.md, cot-prompting.md

---

## Step 4: User Adds Personal Notes

**User:**
> I just realized something — CoT works way better when you give the AI a persona first. Save this insight.

**AI does:**
1. Saves to `raw/notes/2024-04-07-cot-persona-insight.md`
2. **Updates** `pages/concepts/prompt-engineering.md` with user's insight
3. Creates `pages/insights/persona-plus-cot.md` (cross-source insight!)
4. Updates `index.md`

**AI responds:**
> ✅ Great insight! Added to your wiki:
> - Saved as personal note
> - Updated concept page: **Prompt Engineering**
> - Created insight page: **Persona + CoT Synergy** — connecting your observation with existing knowledge
> - Index updated (5 pages total)

---

## What Your Wiki Looks Like After This

```
wiki/
├── index.md                     (5 pages, 3 sources)
├── raw/
│   ├── articles/
│   │   ├── 2024-04-01-prompt-engineering-tips.md
│   │   └── 2024-04-05-chain-of-thought-prompting.md
│   └── notes/
│       └── 2024-04-07-cot-persona-insight.md
└── pages/
    ├── concepts/
    │   └── prompt-engineering.md          ← 3 sources, growing!
    ├── sources/
    │   ├── prompt-engineering-tips-summary.md
    │   └── cot-prompting-summary.md
    └── insights/
        └── persona-plus-cot.md            ← Your original thinking!
```

**5 pages. 3 sources. Knowledge compounding. In 10 minutes.**
