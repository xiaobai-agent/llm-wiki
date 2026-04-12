# Chat History Distillation: From Conversations to Knowledge

> **TL;DR**: Instead of storing raw chat logs, distill them into structured knowledge that can be searched, inherited by future agents, and compressed by 90%+ while retaining core value.

## The Problem

AI agents accumulate massive conversation histories over time:
- Context compression causes early discussions to be forgotten
- Valuable insights are scattered across casual chats
- Cross-session retrieval is difficult
- Knowledge cannot be migrated to new agents

## Industry Consensus

Major memory frameworks (Mem0, Zep, Letta, Cognee) agree:

> **Don't store raw conversations. Store distilled knowledge.**

```
Raw Conversations → Extract Atomic Facts → Embed Vectors → Store/Retrieve
```

### AWS AgentCore Research Data

| Memory Type | Accuracy | Compression Rate |
|-------------|----------|------------------|
| Semantic Memory | 70-74% | 89-94% |
| Preference Memory | 79% | 68% |
| **Summary Memory** | **83%** | **95%** |

**Conclusion**: Summary memory achieves 95% compression with 83% accuracy — the optimal balance.

## Architecture: Three-Layer Distillation

```
┌─────────────────────────────────────────────────┐
│  Raw Chat History (backup, keep in original platform) │
└─────────────────────────────────────────────────┘
                        ↓ Export
┌─────────────────────────────────────────────────┐
│  JSON/JSONL Format (local temporary storage)          │
└─────────────────────────────────────────────────┘
                        ↓ Process by Week
┌─────────────────────────────────────────────────┐
│  Layer 1: Timeline Summaries                          │
│  - Granularity: Weekly                                │
│  - Content: "What we discussed this week"             │
│  - Storage: wiki/timelines/2024-W01.md                │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│  Layer 2: Atomic Facts                                │
│  - Granularity: Single facts                          │
│  - Content: User's opinions, decisions, preferences   │
│  - Storage: Append to related concept pages           │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│  Layer 3: Backlog Ideas                               │
│  - Granularity: Ideas/possibilities                   │
│  - Content: Discussed but not executed                │
│  - Storage: wiki/ideas/backlog.md                     │
└─────────────────────────────────────────────────┘
```

## Two Modes: Historical + Incremental

### Mode 1: Historical Batch Processing (One-time)

For existing chat history:

1. **Export**: Use platform API to export all history as JSONL
2. **Slice**: Split by week
3. **Distill**: LLM extracts summaries, facts, and ideas
4. **Review**: Human spot-checks results
5. **Ingest**: Write to Wiki structure

**Estimated cost**: $30-50 for 2GB of chat history

### Mode 2: Real-time Distillation (Ongoing)

For daily new conversations — **the key innovation**:

#### Option A: Batch (Weekly)
```
Every Sunday → Export this week → LLM distill → Ingest
```
- Delay: 1 week
- Simple but not fresh

#### Option B: Daily Batch
```
Every midnight → Export yesterday → LLM distill → Ingest
```
- Delay: 1 day
- More API cost

#### Option C: Real-time (Recommended ⭐)

The agent **proactively identifies** content worth recording during conversation and writes immediately.

**Trigger conditions**:
- User makes an explicit decision
- Discussion produces a new insight
- User expresses important preference
- New project/person/concept mentioned

**Advantages**:
- Zero delay — ingested during conversation
- Full context — agent understands intent best in the moment
- No extra cost — no separate distillation scripts
- User can confirm — "Agent, record this"

#### Recommended: C + A Hybrid

- **Daily**: Real-time distillation during conversations
- **Weekly**: Sunday review to catch anything missed + generate timeline summary

## Prompt Templates

### Timeline Summary Prompt

```
You are a knowledge organizer. Below is one week's chat history.

Please output:
1. **Topics**: List 3-5 main topics discussed this week
2. **Key Progress**: What decisions/conclusions were reached
3. **To Follow Up**: Items mentioned but not completed

Format: Markdown, concise, 1-2 sentences per topic.
Keep specific names, dates, and project names.

Chat history:
{messages_json}
```

### Atomic Facts Extraction Prompt

```
You are a fact extractor. From the conversation below, extract what the USER expressed:
- Explicit opinions
- Decisions made
- Preferences stated
- Important information mentioned

Requirements:
1. Only extract USER statements, ignore AI responses
2. Each fact should be self-contained
3. Preserve specific details (numbers, names, dates)
4. Return empty list if nothing worth extracting

Output JSON:
{
  "facts": [
    {"fact": "...", "date": "2024-01-15", "topic": "..."},
    ...
  ]
}

Chat history:
{messages_json}
```

### Backlog Ideas Prompt

```
You are an idea collector. From the conversation below, find:
- Ideas discussed but NOT executed
- Alternative approaches mentioned
- Items marked as "later" or "someday"

Output JSON:
{
  "ideas": [
    {"idea": "...", "context": "...", "date": "..."},
    ...
  ]
}

Chat history:
{messages_json}
```

## Directory Structure Extension

```
wiki/
├── pages/           # Existing
├── raw/             # Existing
├── meta/            # Existing
├── timelines/       # NEW - Weekly summaries
│   ├── 2024-W01.md
│   ├── 2024-W02.md
│   └── ...
├── facts/           # NEW - Uncategorized atomic facts
│   └── uncategorized.md
├── ideas/           # NEW - Backlog ideas
│   └── backlog.md
└── index.md
```

## Quality Assurance

### Human Review (Light Touch)

| Level | Review Method | Time Required |
|-------|---------------|---------------|
| Real-time | Agent says "recorded", user glances | ~0 |
| Weekly | Agent sends summary, user skims | 5 min/week |
| Historical | Agent sends summary, user spot-checks | 30 min (one-time) |

**Principle**: Trust agent judgment. Agent asks when uncertain.

### Deduplication

```python
def deduplicate_facts(new_facts, existing_facts):
    """Semantic similarity-based deduplication"""
    unique = []
    for new in new_facts:
        if not is_semantically_similar(new, existing_facts):
            unique.append(new)
    return unique
```

### Version Control

All distillation results are Git-managed:
- Rollback to any version
- Processing logs preserved

## Security Considerations

### Sensitive Information Filtering

Auto-filter before distillation:
- API Keys / Tokens
- Passwords
- ID numbers, bank cards
- Private contact info

### Data Retention Policy

| Data Type | Location | Retention |
|-----------|----------|-----------|
| Raw chat history | Original platform | Permanent (platform handles) |
| Export JSONL | Local temporary | Delete after processing |
| Distilled results | Wiki + Git | Permanent with version control |

## Why Is This Complex? (Not Just "A Script")

A common question: "Can't you just write a quick script?"

No — this is a **data pipeline**, not a single script. Here's why:

### Challenge 1: Paginated Data Retrieval

Most chat APIs return 50-100 messages per request. For 2GB of history, that's **tens of thousands** of API calls. You need:
- Pagination handling
- Checkpoint/resume on failure
- Rate limiting to avoid bans

### Challenge 2: Multi-modal Content

Chat history isn't just text:
- Images need downloading and storing
- Files need separate handling
- Voice messages need transcription
- Videos need metadata extraction

Each type has different storage and processing requirements.

### Challenge 3: Three-Layer Distillation Logic

Each layer requires:
1. **Prompt design** — carefully tuned for extraction
2. **Output parsing** — handle LLM format variations
3. **Wiki integration** — write to correct location
4. **Index updates** — keep wiki/index.md current

That's 12 sub-tasks (4 × 3 layers), not 1.

### Challenge 4: Deduplication and Incremental Updates

After historical processing, the system must:
- Track processed message IDs
- Avoid duplicate facts
- Support daily incremental runs
- Handle edge cases (edited messages, deleted messages)

### The Analogy

| Type | What It Is | Complexity |
|------|-----------|------------|
| Previous scripts | "Cook one dish" | 3 steps, done |
| This project | "Build a kitchen assembly line" | Multi-stage pipeline |

---

## Implementation Timeline

| Phase | Work | Duration |
|-------|------|----------|
| Phase 0 | API permissions | 0.5 day |
| Phase 1 | Export script | 1 day |
| Phase 2 | Distillation script | 2 days |
| Phase 3 | Batch historical data | 1 day |
| Phase 4 | Incremental mechanism | 1 day |

**Total**: ~5-6 days

## Future Evolution

1. **Incremental Automation**: Cron job for weekly processing
2. **Vector Search**: When Wiki exceeds 500 pages, add embeddings
3. **Cross-Agent Migration**: Markdown format is universal, any agent can read

## References

- Mem0 Architecture Paper: https://arxiv.org/abs/2504.19413
- AWS AgentCore Memory: https://aws.amazon.com/blogs/machine-learning/building-smarter-ai-agents-agentcore-long-term-memory-deep-dive/
- Awesome-AI-Memory: https://github.com/IAAR-Shanghai/Awesome-AI-Memory

---

*This document is part of the [LLM Wiki](https://github.com/xiaobai-agent/llm-wiki) project.*
