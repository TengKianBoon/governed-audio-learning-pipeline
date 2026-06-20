from __future__ import annotations

import json
import html
import os
from pathlib import Path

from .summary import extract_keywords, is_meaningful_keyword
from .utils import utc_now_iso, write_text


DEFAULT_GRAPH = {"nodes": [], "edges": [], "updated_at": None}

FRAMEWORK_TITLE = "Enterprise AI Solutions Architecturing and Framework"
FRAMEWORK_OWNER_LABEL = "TKB Enterprise AI Solutions Framework"
FRAMEWORK_SHORT_LABEL = "Enterprise AI Solutions Framework"
FRAMEWORK_TAGLINE = (
    "Enterprise AI solution architecture, application design, governance, and delivery framework "
    "built from reviewed learning inputs, OpenAI-assisted synthesis, operator review, cost controls, "
    "and privacy-preserving publishing."
)

FLOW_STAGES = [
    {
        "id": "context",
        "label": "Context Capture",
        "subtitle": "Business signals, source evidence, and learning intake",
        "accent": "#0f766e",
        "terms": {"audio", "video", "source", "recording", "youtube", "incoming", "phone", "context"},
    },
    {
        "id": "solution-design",
        "label": "Solution Design",
        "subtitle": "Use cases, process fit, requirements, and before-after flow",
        "accent": "#b45309",
        "terms": {
            "business",
            "scenario",
            "solution",
            "requirement",
            "requirements",
            "process",
            "workflow",
            "workflows",
            "translation",
            "transcription",
            "transcript",
            "whisper",
            "chunk",
            "stitching",
            "english",
        },
    },
    {
        "id": "architecture-choice",
        "label": "Architecture Choice",
        "subtitle": "Models, providers, data boundaries, and integration patterns",
        "accent": "#4f46e5",
        "terms": {
            "architecture",
            "architecturing",
            "model",
            "models",
            "vendor",
            "provider",
            "integration",
            "data",
            "portability",
            "enterprise",
        },
    },
    {
        "id": "application-design",
        "label": "Application Design",
        "subtitle": "Agents, orchestration, MCP, skills, hooks, memory, and code structure",
        "accent": "#2563eb",
        "terms": {"agent", "agents", "orchestration", "mcp", "hook", "hooks", "memory", "program", "code"},
    },
    {
        "id": "assurance",
        "label": "Assurance & Operations",
        "subtitle": "Quality gates, privacy, costs, observability, and human review",
        "accent": "#be123c",
        "terms": {
            "quality",
            "guardrail",
            "guardrails",
            "gates",
            "governance",
            "privacy",
            "cost",
            "retry",
            "regression",
            "evaluation",
            "test",
            "trace",
            "production",
        },
    },
    {
        "id": "delivery",
        "label": "Delivery Assets",
        "subtitle": "Reference notes, public packages, decks, visuals, and NotebookLM handoff",
        "accent": "#15803d",
        "terms": {"portfolio", "publish", "public", "notebooklm", "deck", "infographic", "deliver", "delivery"},
    },
]

PUBLIC_CONCEPTS = {
    "agent": "Agentic System Improvement",
    "orchestration": "Agent Orchestration",
    "workflow": "Solution Workflow Design",
    "workflows": "Solution Workflow Design",
    "hook": "Workflow Hooks",
    "hooks": "Workflow Hooks",
    "memory": "Long-Term Memory",
    "quality": "Quality Gates",
    "gates": "Quality Gates",
    "cost": "Cost Governance",
    "governance": "AI Governance",
    "chunk": "Chunking & Stitching",
    "english": "Transcription & Translation",
    "transcript": "Transcription & Translation",
    "enterprise": "Enterprise AI Solution Architecture",
    "learning": "Enterprise Learning Loop",
    "architecture": "Architecture Decision Framework",
    "human review": "Human-in-the-Loop Review",
    "mindmap": "Architecture Knowledge Graph",
    "model": "Model Selection Strategy",
    "portfolio": "Portfolio Publishing",
    "production": "Production Readiness",
    "regression": "Regression Testing",
    "research": "Enterprise AI Research",
    "trace": "Observability & Trace-Driven Improvement",
    "test": "Regression Evaluation",
    "company": "Enterprise Differentiation",
    "vendor": "Provider Strategy",
    "provider": "Provider Strategy",
    "privacy": "Privacy & Data Boundary",
}

PUBLIC_TOPIC_BLOCKLIST = {
    "ideas",
    "mock",
    "mode",
}

PUBLIC_PACKAGE_BLOCKLIST = {
    "sample",
    "fixture",
    "mock",
}


def load_graph(path: Path) -> dict:
    if not path.exists():
        return DEFAULT_GRAPH.copy()
    return json.loads(path.read_text(encoding="utf-8"))


def save_graph(path: Path, graph: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    graph["updated_at"] = utc_now_iso()
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")


def evaluate_delta(english_text: str, learning_slug: str, graph: dict) -> dict:
    concepts = extract_keywords(english_text, limit=20)
    existing = {str(node.get("label", "")).lower() for node in graph.get("nodes", [])}
    overlaps = [concept for concept in concepts if concept.lower() in existing]
    novel = [concept for concept in concepts if concept.lower() not in existing]
    overlap_score = round(len(overlaps) / max(len(concepts), 1), 2)
    novelty_score = round(len(novel) / max(len(concepts), 1), 2)
    if novelty_score >= 0.4:
        recommendation = "add"
    elif overlaps:
        recommendation = "update"
    else:
        recommendation = "needs_review"
    return {
        "learning_slug": learning_slug,
        "concepts": concepts,
        "overlaps": overlaps,
        "novel": novel,
        "overlap_score": overlap_score,
        "novelty_score": novelty_score,
        "recommendation": recommendation,
        "review_required": True,
    }


def apply_delta(graph: dict, delta: dict, private_link: str, public_link: str | None = None) -> dict:
    labels = {str(node.get("label", "")).lower(): node for node in graph.get("nodes", [])}
    for concept in delta.get("concepts", []):
        if not is_meaningful_keyword(str(concept)):
            continue
        key = concept.lower()
        if key not in labels:
            node = {
                "id": key.replace(" ", "-"),
                "label": concept,
                "private_links": [private_link],
                "public_links": [public_link] if public_link else [],
            }
            graph.setdefault("nodes", []).append(node)
            labels[key] = node
        else:
            node = labels[key]
            node.setdefault("private_links", [])
            node.setdefault("public_links", [])
            if private_link not in node["private_links"]:
                node["private_links"].append(private_link)
            if public_link and public_link not in node["public_links"]:
                node["public_links"].append(public_link)
    return graph


def _canonical_label(label: str) -> str | None:
    key = label.strip().lower()
    if key in PUBLIC_TOPIC_BLOCKLIST:
        return None
    return PUBLIC_CONCEPTS.get(key, label.strip())


def _node_id(label: str) -> str:
    return label.lower().replace("&", "and").replace("/", " ").replace(" ", "-")


def _stage_for_label(label: str) -> dict:
    key = label.strip().lower()
    for stage in FLOW_STAGES:
        if key in stage["terms"]:
            return stage
    for stage in FLOW_STAGES:
        if any(term in key for term in stage["terms"]):
            return stage
    if "transcription" in key or "chunk" in key or "solution" in key or "workflow" in key:
        return FLOW_STAGES[1]
    if "architecture" in key or "model" in key or "provider" in key or "vendor" in key:
        return FLOW_STAGES[2]
    if "agent" in key or "orchestration" in key or "memory" in key or "hook" in key:
        return FLOW_STAGES[3]
    if "quality" in key or "evaluation" in key or "observability" in key or "privacy" in key:
        return FLOW_STAGES[4]
    if "publish" in key or "portfolio" in key or "delivery" in key:
        return FLOW_STAGES[5]
    return FLOW_STAGES[2]


def _public_package_slug(link: str) -> str:
    normalized = link.replace("\\", "/").rstrip("/")
    if normalized.endswith("/index.html"):
        normalized = normalized.rsplit("/", 1)[0]
    return normalized.rsplit("/", 1)[-1]


def _package_date(slug: str) -> str:
    date_token = slug[:8]
    if len(date_token) == 8 and date_token.isdigit():
        return f"{date_token[:4]}-{date_token[4:6]}-{date_token[6:8]}"
    return ""


def _public_package_label(link: str, rank: int, total: int) -> str:
    slug = _public_package_slug(link)
    date = _package_date(slug)
    title_part = slug[9:] if date and len(slug) > 9 else slug
    title_tokens = [token for token in title_part.split("-") if token]
    if title_tokens and len(title_tokens[-1]) == 8:
        try:
            int(title_tokens[-1], 16)
            title_tokens = title_tokens[:-1]
        except ValueError:
            pass
    title = " ".join(token.upper() if token in {"ai", "mcp"} else token.capitalize() for token in title_tokens)
    label = " - ".join(part for part in (date, title or "Public Review Package") if part)
    if total > 1:
        prefix = "Latest reviewed package" if rank == 1 else "Earlier evidence"
        return f"{prefix}: {label}"
    return label


def _is_public_exhibit_link(link: str) -> bool:
    slug = _public_package_slug(link).lower()
    return not any(marker in slug for marker in PUBLIC_PACKAGE_BLOCKLIST)


def _is_quality_passed_public_link(link: str, output_path: Path) -> bool:
    if "://" in link:
        return True
    slug = _public_package_slug(link)
    quality_path = output_path.parent.parent / "outputs_public_review" / slug / "quality_score.json"
    if not quality_path.exists():
        return True
    try:
        quality = json.loads(quality_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(quality.get("passed"))


def _href_for_public_link(link: str, output_path: Path) -> str:
    if not link:
        return ""
    if "://" in link:
        return link
    slug = _public_package_slug(link)
    target = output_path.parent.parent / "outputs_public_review" / slug / "index.html"
    return os.path.relpath(target, start=output_path.parent).replace("\\", "/")


def _public_link_records(links: list[str], output_path: Path) -> list[dict]:
    public_links = sorted(
        [
            link
            for link in dict.fromkeys(links)
            if _is_public_exhibit_link(link) and _is_quality_passed_public_link(link, output_path)
        ],
        key=lambda link: (_package_date(_public_package_slug(link)), _public_package_slug(link)),
        reverse=True,
    )
    total = len(public_links)
    return [
        {
            "label": _public_package_label(link, index, total),
            "href": _href_for_public_link(link, output_path),
        }
        for index, link in enumerate(public_links, start=1)
    ]


def _render_node(node: dict, output_path: Path) -> dict | None:
    raw_label = str(node.get("label", "Untitled")).strip()
    label = _canonical_label(raw_label)
    if not label:
        return None
    if not is_meaningful_keyword(label):
        return None
    stage = _stage_for_label(label)
    private_links = [str(link) for link in node.get("private_links", []) if str(link).strip()]
    public_links = [
        str(link)
        for link in node.get("public_links", [])
        if str(link).strip()
    ]
    public_link_records = _public_link_records(public_links, output_path)
    if not public_link_records:
        return None
    return {
        "id": _node_id(label),
        "label": label,
        "stage": stage["id"],
        "stage_label": stage["label"],
        "accent": stage["accent"],
        "public_links": public_link_records,
        "evidence_count": len(set(private_links)),
        "public_count": len(public_link_records),
    }


def _merge_render_nodes(nodes: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for node in nodes:
        existing = merged.get(node["id"])
        if not existing:
            merged[node["id"]] = node
            continue
        seen_hrefs = {link["href"] for link in existing["public_links"]}
        for link in node["public_links"]:
            if link["href"] not in seen_hrefs:
                existing["public_links"].append(link)
                seen_hrefs.add(link["href"])
        existing["public_count"] = len(existing["public_links"])
        existing["evidence_count"] += node["evidence_count"]
    stage_order = {stage["id"]: index for index, stage in enumerate(FLOW_STAGES)}
    for node in merged.values():
        node["public_links"] = sorted(
            node["public_links"],
            key=lambda link: link["label"].replace("Latest reviewed package: ", "").replace("Earlier evidence: ", ""),
            reverse=True,
        )
        total = len(node["public_links"])
        if total > 1:
            for index, link in enumerate(node["public_links"], start=1):
                base_label = link["label"].replace("Latest reviewed package: ", "").replace("Earlier evidence: ", "")
                link["label"] = (
                    f"Latest reviewed package: {base_label}"
                    if index == 1
                    else f"Earlier evidence: {base_label}"
                )
    return sorted(merged.values(), key=lambda item: (stage_order.get(item["stage"], 99), item["label"]))


def render_mindmap_html(
    graph: dict,
    output_path: Path,
    *,
    owner_name: str = "Teng Kian Boon",
    owner_initials: str = "TKB",
    tagline: str = FRAMEWORK_TAGLINE,
) -> None:
    raw_nodes = graph.get("nodes", [])
    prepared_nodes = [node for node in (_render_node(raw_node, output_path) for raw_node in raw_nodes) if node]
    render_nodes = _merge_render_nodes(prepared_nodes)
    hidden_count = max(len(raw_nodes) - len(prepared_nodes), 0)
    stage_counts = {
        stage["id"]: len([node for node in render_nodes if node["stage"] == stage["id"]])
        for stage in FLOW_STAGES
    }
    stage_cards = []
    stage_sections = []
    for index, stage in enumerate(FLOW_STAGES, start=1):
        count = stage_counts[stage["id"]]
        stage_cards.append(
            f"""
      <section class="stage" style="--accent:{stage['accent']}">
        <div class="stage-index">{index}</div>
        <h2>{html.escape(stage['label'])}</h2>
        <p>{html.escape(stage['subtitle'])}</p>
        <strong>{count} topics</strong>
      </section>"""
        )
        topic_cards = []
        for node in [item for item in render_nodes if item["stage"] == stage["id"]]:
            node_id = html.escape(node["id"], quote=True)
            label = html.escape(node["label"])
            topic_cards.append(
                f"""
          <button class="topic-card" type="button" data-node-id="{node_id}" onclick="selectNode(this.dataset.nodeId)" style="--accent:{node['accent']}">
            <span class="topic-label">{label}</span>
            <span class="topic-meta">{node['public_count']} public review package{'s' if node['public_count'] != 1 else ''}</span>
          </button>"""
            )
        if not topic_cards:
            topic_cards.append('<p class="empty">No reviewed topics yet.</p>')
        stage_sections.append(
            f"""
      <section class="topic-section" id="stage-{html.escape(stage['id'])}">
        <div class="section-heading">
          <span class="stage-pill" style="--accent:{stage['accent']}">{index}</span>
          <div>
            <h2>{html.escape(stage['label'])}</h2>
            <p>{html.escape(stage['subtitle'])}</p>
          </div>
        </div>
        <div class="topic-grid">{''.join(topic_cards)}</div>
      </section>"""
        )
    owner_name_safe = html.escape(owner_name)
    owner_initials_safe = html.escape(owner_initials)
    tagline_safe = html.escape(tagline)
    nodes_json = json.dumps(render_nodes, ensure_ascii=False).replace("</", "<\\/")
    page_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{FRAMEWORK_TITLE}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #18212f;
      --muted: #5f6b7a;
      --line: #d9e0e8;
      --surface: #ffffff;
      --soft: #f6f8fb;
      --gold: #b45309;
      --green: #0f766e;
      --rose: #be123c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: #f7f5ef;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 16px;
      line-height: 1.5;
    }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 28px 20px 42px; }}
    header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 18px;
      align-items: end;
      padding-bottom: 18px;
      border-bottom: 2px solid var(--ink);
    }}
    h1 {{ margin: 8px 0 10px; font-size: clamp(32px, 5vw, 56px); line-height: 1.02; letter-spacing: 0; }}
    h2 {{ margin: 0; font-size: 18px; letter-spacing: 0; }}
    p {{ margin: 0; }}
    a {{ color: #1d4ed8; }}
    .owner {{ font-weight: 700; text-transform: uppercase; color: var(--green); }}
    .tagline {{ max-width: 760px; color: var(--muted); }}
    .status {{
      display: grid;
      grid-template-columns: repeat(3, minmax(110px, 1fr));
      gap: 8px;
      min-width: 330px;
    }}
    .metric {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
    }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .metric strong {{ font-size: 20px; }}
    .review {{
      margin: 18px 0;
      padding: 12px 14px;
      background: #fff8e8;
      border-left: 5px solid var(--gold);
      border-radius: 6px;
      color: #553008;
    }}
    .pipeline {{
      display: grid;
      grid-template-columns: repeat(6, minmax(130px, 1fr));
      gap: 10px;
      margin: 20px 0;
      align-items: stretch;
    }}
    .stage {{
      position: relative;
      min-height: 156px;
      background: var(--surface);
      border: 1px solid var(--line);
      border-top: 5px solid var(--accent);
      border-radius: 8px;
      padding: 14px;
    }}
    .stage::after {{
      content: "";
      position: absolute;
      right: -10px;
      top: 50%;
      width: 10px;
      border-top: 2px solid #8c98a8;
    }}
    .stage:last-child::after {{ display: none; }}
    .stage-index {{
      display: inline-grid;
      place-items: center;
      width: 30px;
      height: 30px;
      margin-bottom: 12px;
      border-radius: 50%;
      background: var(--accent);
      color: white;
      font-weight: 700;
    }}
    .stage p {{ min-height: 48px; margin: 6px 0 10px; color: var(--muted); font-size: 14px; }}
    .stage strong {{ color: var(--accent); }}
    .map-layout {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 340px;
      gap: 18px;
      align-items: start;
    }}
    .topic-section {{
      margin-bottom: 14px;
      padding: 16px;
      background: rgba(255, 255, 255, .76);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .section-heading {{
      display: flex;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
    }}
    .section-heading p {{ color: var(--muted); font-size: 14px; }}
    .stage-pill {{
      display: inline-grid;
      place-items: center;
      flex: 0 0 32px;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: var(--accent);
      color: white;
      font-weight: 700;
    }}
    .topic-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 10px;
    }}
    .topic-card {{
      display: grid;
      gap: 8px;
      min-height: 88px;
      width: 100%;
      text-align: left;
      background: var(--surface);
      border: 1px solid var(--line);
      border-left: 5px solid var(--accent);
      border-radius: 8px;
      padding: 12px;
      color: var(--ink);
      cursor: pointer;
    }}
    .topic-card:hover, .topic-card.active {{
      outline: 2px solid var(--accent);
      outline-offset: 1px;
    }}
    .topic-label {{ font-weight: 700; text-transform: capitalize; }}
    .topic-meta {{ color: var(--muted); font-size: 13px; }}
    .detail-panel {{
      position: sticky;
      top: 16px;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .detail-panel h2 {{ font-size: 22px; text-transform: capitalize; }}
    .detail-stage {{
      display: inline-block;
      margin: 8px 0 12px;
      padding: 4px 8px;
      border-radius: 999px;
      color: white;
      background: var(--detail-accent, var(--green));
      font-size: 13px;
      font-weight: 700;
    }}
    .link-list {{ display: grid; gap: 8px; margin-top: 10px; }}
    .link-list a {{
      display: block;
      overflow-wrap: anywhere;
      padding: 8px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--soft);
      text-decoration: none;
    }}
    .empty {{ color: var(--muted); padding: 8px 0; }}
    footer {{
      margin-top: 20px;
      padding-top: 14px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 14px;
    }}
    @media (max-width: 980px) {{
      header, .map-layout {{ grid-template-columns: 1fr; }}
      .status {{ min-width: 0; }}
      .pipeline {{ grid-template-columns: repeat(2, minmax(150px, 1fr)); }}
      .stage::after {{ display: none; }}
      .detail-panel {{ position: static; }}
    }}
    @media (max-width: 560px) {{
      main {{ padding: 20px 14px 34px; }}
      .pipeline, .status {{ grid-template-columns: 1fr; }}
      .topic-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <div class="owner">{html.escape(FRAMEWORK_OWNER_LABEL)}</div>
      <h1>{html.escape(FRAMEWORK_TITLE)}</h1>
      <p class="tagline">Built by {owner_name_safe}. {tagline_safe}</p>
    </div>
    <aside class="status" aria-label="Mindmap status">
      <div class="metric"><span>Solution concepts</span><strong>{len(render_nodes)}</strong></div>
      <div class="metric"><span>Framework branches</span><strong>{len(FLOW_STAGES)}</strong></div>
      <div class="metric"><span>Filtered weak terms</span><strong>{hidden_count}</strong></div>
    </aside>
  </header>
  <div class="review">AI tools assist synthesis and formatting; Teng Kian Boon owns the solution architecture framing, review decisions, and public publishing choices. Public exhibit links only sanitized review packages.</div>
  <p>Updated: {html.escape(str(graph.get('updated_at') or 'not yet updated'))}</p>
  <section class="pipeline" aria-label="Enterprise AI solution architecture framework flow">
    {''.join(stage_cards)}
  </section>
  <section class="map-layout" aria-label="Solution architecture topic map">
    <div>
      {''.join(stage_sections)}
    </div>
    <aside class="detail-panel" id="detail-panel" style="--detail-accent:#0f766e">
      <h2 id="detail-title">No topic selected</h2>
      <span class="detail-stage" id="detail-stage">Framework branch</span>
      <p id="detail-summary">Reviewed concepts appear here as the Enterprise AI solutions framework grows over time.</p>
      <div class="link-list" id="detail-links"></div>
    </aside>
  </section>
  <footer>Public artifacts are sanitized for review. Private transcripts, raw source files, and internal evidence paths stay outside the public exhibit.</footer>
</main>
<script>
const mindmapNodes = {nodes_json};

function escapeHtml(value) {{
  return String(value).replace(/[&<>"']/g, function(character) {{
    return ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}})[character];
  }});
}}

function linkMarkup(records) {{
  if (!records.length) {{
    return '<p class="empty">No public review package linked yet.</p>';
  }}
  return records.map(function(record) {{
    return '<a href="' + escapeHtml(record.href) + '" target="_blank" rel="noreferrer">' +
      escapeHtml(record.label) + '</a>';
  }}).join('');
}}

function selectNode(id) {{
  const node = mindmapNodes.find(function(item) {{ return item.id === id; }});
  if (!node) {{ return; }}
  document.querySelectorAll('.topic-card').forEach(function(card) {{
    card.classList.toggle('active', card.dataset.nodeId === id);
  }});
  document.getElementById('detail-panel').style.setProperty('--detail-accent', node.accent);
  document.getElementById('detail-title').textContent = node.label;
  document.getElementById('detail-stage').textContent = node.stage_label;
  document.getElementById('detail-summary').textContent =
    node.label + ' is mapped into the ' + node.stage_label + ' branch of the Enterprise AI solutions architecture framework. ' +
    node.evidence_count + ' internal evidence package(s) are tracked privately but not exposed in this public view.';
  document.getElementById('detail-links').innerHTML =
    '<h3>Public review packages</h3>' + linkMarkup(node.public_links);
}}

if (mindmapNodes.length) {{
  selectNode(mindmapNodes[0].id);
}}
</script>
</body>
</html>
"""
    write_text(output_path, page_html)
