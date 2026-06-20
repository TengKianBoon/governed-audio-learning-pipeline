# Agent Contracts

Rule: no contract, no agent.

## Template

```text
AGENT: <name>
PHASE: <n>   MODEL: <small|medium|strong>   ISOLATION: <shared|worktree>
OBJECTIVE: <one-sentence outcome>
OUTPUT FORMAT: <files / functions / report shape>
ALLOW: <tools, data, files>
FORBID: <private data, unsafe actions, unrelated edits>
BOUNDARIES: owns <...>; must not edit <...>
DONE = : <golden test or acceptance check>
RETRY: max 3, reflect-before-retry, escalate on 3rd failure
DEPENDS ON: <contracts/files/gates>
```

## MVP Agents

```text
AGENT: orchestrator
OBJECTIVE: Route tasks, maintain build journal, and enforce human checkpoints.
DONE = : every task is passed by verifier, parked in triage, or awaiting human review.
```

```text
AGENT: media-transcription-agent
OBJECTIVE: Convert supported media to transcripts without modifying originals.
DONE = : sample audio, sample video, and long-file chunk plan tests pass.
```

```text
AGENT: verifier
OBJECTIVE: Check outputs against tests, score gates, and privacy rules.
DONE = : verdict includes pass/fail, score, and exact failing evidence.
```

```text
AGENT: mindmap-curator
OBJECTIVE: Compare new learning notes against the enterprise AI mindmap and produce a delta recommendation.
DONE = : overlap, novelty, and recommended action are present.
```

```text
AGENT: publishing-agent
OBJECTIVE: Produce sanitized public-review artifacts only.
DONE = : no raw audio, full private transcript, secret, or long source excerpt is copied.
```
