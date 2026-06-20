AGENT: mindmap-curator
PHASE: MVP   MODEL: medium   ISOLATION: worktree
OBJECTIVE: Compare new English transcripts with the enterprise AI graph and recommend add/update/skip.
OUTPUT FORMAT: mindmap_delta.json and mindmap_review.json.
ALLOW: app/mindmap.py, private English transcripts, mindmap/graph.json.
FORBID: public links to private outputs; auto-adding low-confidence claims.
BOUNDARIES: owns mindmap logic and tests.
DONE = : delta includes concepts, overlap score, novelty score, recommendation, review_required.
RETRY: max 3, then escalate.
DEPENDS ON: english_transcribed.md.
