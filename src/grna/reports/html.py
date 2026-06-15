"""Self-contained HTML release-note rendering."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html import escape
from typing import Any

from grna.evidence.aggregator import AnalyticsBundle
from grna.reports.markdown import ReleaseNoteContent


@dataclass(frozen=True, slots=True)
class ReportThemeTokens:
    """Configurable visual tokens for BOS Genesis-style reports."""

    brand_primary: str = "#E20074"
    text_primary: str = "#1F2933"
    text_secondary: str = "#52606D"
    border_subtle: str = "#D9E2EC"
    surface_light: str = "#F5F7FA"
    risk_low: str = "#2F855A"
    risk_medium: str = "#B7791F"
    risk_high: str = "#C53030"

    def to_css_vars(self) -> str:
        """Render tokens as CSS custom properties."""

        return "\n".join(
            [
                f"  --brand-primary: {self.brand_primary};",
                f"  --text-primary: {self.text_primary};",
                f"  --text-secondary: {self.text_secondary};",
                f"  --border-subtle: {self.border_subtle};",
                f"  --surface-light: {self.surface_light};",
                f"  --risk-low: {self.risk_low};",
                f"  --risk-medium: {self.risk_medium};",
                f"  --risk-high: {self.risk_high};",
            ]
        )


class HtmlReleaseNoteRenderer:
    """Render a print-ready HTML release-note artifact."""

    def __init__(self, theme: ReportThemeTokens | None = None) -> None:
        self.theme = theme or ReportThemeTokens()

    def render(self, content: ReleaseNoteContent) -> str:
        """Render a self-contained HTML document from release-note content."""

        title = _text(content.title)
        body = "\n".join(
            [
                _cover_page(content),
                _page(content, "1", "Executive Summary", _executive_summary(content)),
                _page(content, "2", "Release And Package Information", _release_info(content)),
                _page(content, "3", "Analytical Release Dashboard", _release_dashboard(content)),
                _page(content, "4", "Release Readiness Assessment", _readiness(content)),
                _page(
                    content,
                    "5",
                    "Change History From Repository Evidence",
                    _change_history(content),
                ),
                _page(content, "6", "Technical Capability Map", _capability_map(content)),
                _page(
                    content,
                    "7",
                    "Deployment, Validation, And Rollback Notes",
                    _deployment(content),
                ),
                _page(content, "8", "Known Limitations, Risks, And Controls", _risks(content)),
                _page(content, "9", "Recommended Next Release Scope", _recommendations(content)),
                _page(
                    content,
                    "Appendix A",
                    "Evidence Sources And Assumptions",
                    _evidence_appendix(content),
                ),
            ]
        )
        return "\n".join(
            [
                "<!doctype html>",
                '<html lang="en">',
                "<head>",
                '  <meta charset="utf-8">',
                '  <meta name="viewport" content="width=device-width, initial-scale=1">',
                f"  <title>{title}</title>",
                f"  <style>{self._css()}</style>",
                "</head>",
                "<body>",
                body,
                "</body>",
                "</html>",
            ]
        )

    def _css(self) -> str:
        return f"""
:root {{
{self.theme.to_css_vars()}
}}
@page {{
  size: A4;
  margin: 16mm 14mm 18mm 14mm;
  @bottom-right {{ content: "Page " counter(page); color: var(--text-secondary); }}
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: #eef2f6;
  color: var(--text-primary);
  font-family: Helvetica, Arial, sans-serif;
  font-size: 12px;
  line-height: 1.45;
}}
.page {{
  width: 210mm;
  min-height: 297mm;
  margin: 0 auto 12px;
  padding: 0 0 14mm;
  background: #fff;
  page-break-after: always;
  position: relative;
}}
.cover-page {{
  padding: 0;
  color: #fff;
  border-top: 0;
  overflow: hidden;
  background:
    radial-gradient(circle at 88% 12%, rgba(45, 117, 161, .50) 0 31mm, transparent 31.3mm),
    radial-gradient(circle at 98% 91%, rgba(0, 172, 189, .62) 0 40mm, transparent 40.3mm),
    radial-gradient(circle at 80% 89%, rgba(0, 121, 130, .46) 0 30mm, transparent 30.3mm),
    linear-gradient(rgba(69, 128, 161, .28) 1px, transparent 1px),
    linear-gradient(90deg, rgba(69, 128, 161, .28) 1px, transparent 1px),
    #061b2a;
  background-size: auto, auto, auto, 8.45mm 8.45mm, 8.45mm 8.45mm, auto;
}}
.page-header {{
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
  background: #061b2a;
  color: #fff;
  font-size: 8.5px;
  font-weight: 700;
  min-height: 9.5mm;
  padding: 0 14mm;
  border-bottom: 1.1mm solid #00c6d7;
  margin-bottom: 11mm;
}}
.page-content {{
  padding: 0 16mm;
}}
.section-heading {{
  font-size: 7.2mm;
  color: #061b2a;
  margin-bottom: 4mm;
}}
.section-intro {{
  color: #28456d;
  font-size: 3.2mm;
  border-bottom: .7mm solid #00c6d7;
  padding-bottom: 2mm;
  margin-bottom: 3.5mm;
}}
.eyebrow {{
  color: var(--brand-primary);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}}
h1, h2, h3 {{ margin: 0; line-height: 1.18; }}
h1 {{ font-size: 30px; max-width: 162mm; }}
h2 {{ font-size: 18px; color: var(--text-primary); margin-bottom: 6px; }}
h3 {{ font-size: 12px; margin: 11px 0 6px; }}
p {{ margin: 0 0 9px; }}
.subtitle {{ color: var(--text-secondary); font-size: 14px; margin-top: 8px; }}
.source-line {{
  color: var(--text-secondary);
  font-size: 8.5px;
  margin-bottom: 9px;
}}
.cover-title {{
  margin-top: 46mm;
  margin-left: 17mm;
  position: relative;
  z-index: 1;
}}
.cover-title .report-subtitle {{
  display: block;
  margin-top: 6mm;
  color: #fff;
  font-size: 10.2mm;
  font-weight: 700;
  line-height: 1.16;
}}
.version-line {{
  color: rgba(255,255,255,.92);
  font-size: 4.1mm;
  margin-top: 8.5mm;
}}
.section-number {{ color: var(--brand-primary); font-weight: 700; margin-bottom: 4px; }}
.metric-grid {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin: 16px 0;
}}
.metric-tile {{
  border: 1px solid var(--border-subtle);
  border-top: 4px solid var(--brand-primary);
  padding: 9px;
  min-height: 58px;
  background: #fff;
}}
.cover-page .source-line {{
  display: none;
}}
.cover-page .eyebrow {{
  display: none;
}}
.cover-page h1 {{
  color: #fff;
  font-size: 10.4mm;
  line-height: 1.16;
  max-width: 175mm;
  text-shadow: 0 1px 0 rgba(226, 0, 116, .45);
}}
.cover-page h3 {{
  color: #fff;
  margin: 0 0 1mm;
  font-size: 2.9mm;
}}
.cover-page p {{
  color: #fff;
  max-width: 174mm;
  font-weight: 600;
  font-size: 3.55mm;
  line-height: 1.38;
}}
.cover-page .metric-grid {{
  width: 146mm;
  grid-template-columns: repeat(4, 33.6mm);
  gap: 3.8mm;
  margin: 13.6mm 0 13.2mm 18.8mm;
  position: relative;
  z-index: 1;
}}
.cover-page .metric-tile {{
  background: #fff;
  color: #071a2a;
  border: 1px solid transparent;
  border-top-width: 3mm;
  min-height: 17mm;
  padding: 2mm 2mm 1.6mm;
  box-shadow: 0 2px 0 rgba(0,0,0,.22);
}}
.cover-page .metric-tile:nth-child(1) {{ border-top-color: #00c6d7; }}
.cover-page .metric-tile:nth-child(2) {{ border-top-color: #315cff; }}
.cover-page .metric-tile:nth-child(3) {{ border-top-color: #8438e8; }}
.cover-page .metric-tile:nth-child(4) {{ border-top-color: #16a34a; }}
.cover-page .metric-value {{
  color: #071a2a;
  text-align: center;
  font-size: 5.2mm;
  line-height: 1.05;
}}
.cover-page .metric-label {{
  color: #31415f;
  text-align: center;
  font-size: 2.15mm;
  margin-top: 2.2mm;
}}
.cover-page table {{
  width: 149mm;
  margin: 8.2mm 0 0 17mm;
  position: relative;
  z-index: 1;
  table-layout: fixed;
}}
.cover-page th {{
  background: #062033;
  color: #fff;
  border-color: rgba(255,255,255,.8);
  font-size: 2.3mm;
  padding: 2mm 2.3mm;
}}
.cover-page td {{
  background: #fff;
  color: #071a2a;
  border-color: #b7c9d6;
  font-size: 2.1mm;
  padding: 2mm 2.3mm;
}}
.cover-positioning {{
  margin-left: 17mm;
  margin-top: 13mm;
  max-width: 174mm;
  position: relative;
  z-index: 1;
}}
.metric-value {{ font-size: 20px; font-weight: 700; overflow-wrap: anywhere; }}
.metric-label {{ color: var(--text-secondary); font-size: 10px; margin-top: 3px; }}
.feature-grid {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 5px 12px;
  margin: 12px 0 4px;
}}
.feature-chip {{
  font-size: 10px;
  padding-left: 13px;
  position: relative;
}}
.feature-chip:before {{
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--brand-primary);
  position: absolute;
  left: 0;
  top: 5px;
}}
.feature-matrix {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid #00b7c9;
  margin: 5mm 0 7mm;
}}
.feature-cell {{
  min-height: 9mm;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  background: #d9fbff;
  border-right: 1px solid #00b7c9;
  border-bottom: 1px solid #00b7c9;
  color: #061b2a;
  font-size: 2.55mm;
  font-weight: 700;
  padding: 1.8mm;
}}
.feature-cell:nth-child(4n) {{
  border-right: 0;
}}
.feature-cell:nth-last-child(-n+4) {{
  border-bottom: 0;
}}
.executive-metrics {{
  display: grid;
  grid-template-columns: repeat(4, 34mm);
  justify-content: center;
  gap: 4.2mm;
  margin: 6mm 0 5mm;
}}
.executive-metrics .metric-tile {{
  border-top-width: 3mm;
  border-radius: 2mm;
  min-height: 17mm;
  padding: 2.2mm 2mm 1.8mm;
  box-shadow: 0 1px 0 rgba(0,0,0,.18);
}}
.executive-metrics .metric-tile:nth-child(1) {{ border-top-color: #00c6d7; }}
.executive-metrics .metric-tile:nth-child(2) {{ border-top-color: #315cff; }}
.executive-metrics .metric-tile:nth-child(3) {{ border-top-color: #8438e8; }}
.executive-metrics .metric-tile:nth-child(4) {{ border-top-color: #16a34a; }}
.executive-metrics .metric-value {{
  color: #061b2a;
  text-align: center;
  font-size: 5.4mm;
}}
.executive-metrics .metric-label {{
  color: #28456d;
  text-align: center;
  font-size: 2.3mm;
}}
.release-recommendation h3 {{
  color: #061b2a;
  font-size: 5.2mm;
  margin: 0 0 2.5mm;
}}
.release-recommendation p {{
  color: #061b2a;
  font-size: 3.35mm;
  line-height: 1.35;
}}
.callout {{
  background: var(--surface-light);
  border: 1px solid var(--border-subtle);
  border-left: 4px solid var(--brand-primary);
  padding: 10px 12px;
  margin: 12px 0;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0 16px;
  table-layout: fixed;
}}
th, td {{
  border: 1px solid var(--border-subtle);
  padding: 7px;
  vertical-align: top;
  overflow-wrap: anywhere;
}}
th {{ background: var(--surface-light); font-size: 10px; text-align: left; }}
td {{ font-size: 10px; }}
.compact-table th, .compact-table td {{ padding: 5px 6px; font-size: 9.2px; }}
.dashboard-grid {{
  display: block;
  margin-top: 3mm;
}}
.chart-card {{
  border: 1px solid var(--border-subtle);
  border-radius: 2.5mm;
  background: #fff;
  padding: 6mm 6mm 4mm;
  min-height: 68mm;
  margin-bottom: 5mm;
}}
.chart-card h3 {{
  font-size: 3.8mm;
  margin: 0 0 4mm;
  color: #061b2a;
}}
.chart-svg {{
  width: 100%;
  height: auto;
  display: block;
}}
.chart-note {{
  color: #28456d;
  font-size: 2.4mm;
  margin-top: 2mm;
}}
.bar-row {{
  display: grid;
  grid-template-columns: 46px 1fr 32px;
  align-items: center;
  gap: 7px;
  margin: 5px 0;
  font-size: 9px;
}}
.bar-track {{
  height: 9px;
  background: var(--surface-light);
  border: 1px solid var(--border-subtle);
}}
.bar-fill {{
  height: 100%;
  background: var(--brand-primary);
}}
.score-grid {{
  border: 1px solid var(--border-subtle);
  border-radius: 2.5mm;
  padding: 5.5mm 6mm 4mm;
  margin: 3mm 0 4mm;
}}
.score-grid h3 {{
  font-size: 3.8mm;
  margin: 0 0 2mm;
  color: #061b2a;
}}
.score-grid .muted {{
  font-size: 2.35mm;
  margin-bottom: 3mm;
}}
.score-row {{
  display: grid;
  grid-template-columns: 26mm 1fr 13mm;
  gap: 3mm;
  align-items: center;
  margin: 3mm 0;
  font-size: 2.65mm;
  color: #061b2a;
}}
.score-track {{
  height: 4.6mm;
  background: #dfe6ef;
}}
.score-fill {{
  height: 100%;
}}
.readiness-table th {{
  background: #061b2a;
  color: #fff;
  border-color: #061b2a;
}}
.readiness-table td {{
  font-size: 2.55mm;
  padding: 2.2mm;
}}
.change-history-table {{
  table-layout: fixed;
  margin-top: 3mm;
}}
.change-history-table th {{
  background: #061b2a;
  color: #fff;
  border-color: #061b2a;
  font-size: 2.35mm;
  padding: 1.7mm 1.8mm;
}}
.change-history-table td {{
  font-size: 2.25mm;
  line-height: 1.18;
  padding: 1.6mm 1.8mm;
}}
.change-history-table th:nth-child(1),
.change-history-table td:nth-child(1) {{
  width: 28%;
}}
.change-history-table th:nth-child(2),
.change-history-table td:nth-child(2) {{
  width: 13%;
}}
.change-history-table th:nth-child(3),
.change-history-table td:nth-child(3) {{
  width: 10%;
}}
.change-history-table th:nth-child(4),
.change-history-table td:nth-child(4) {{
  width: 17%;
}}
.change-history-table th:nth-child(5),
.change-history-table td:nth-child(5) {{
  width: 32%;
}}
.status-pill {{
  display: inline-block;
  padding: 2px 7px;
  border: 1px solid var(--border-subtle);
  background: var(--surface-light);
  font-size: 9px;
  font-weight: 700;
}}
.evidence-block {{
  border: 1px solid var(--border-subtle);
  background: #fff;
  padding: 9px;
  margin: 8px 0;
}}
.evidence-id {{ color: var(--brand-primary); font-weight: 700; }}
.status-low {{ color: var(--risk-low); font-weight: 700; }}
.status-medium {{ color: var(--risk-medium); font-weight: 700; }}
.status-high {{ color: var(--risk-high); font-weight: 700; }}
.diagram-figure {{
  border: 1px solid var(--border-subtle);
  background:
    linear-gradient(rgba(148, 163, 184, .16) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, .16) 1px, transparent 1px),
    linear-gradient(180deg, #fbfdff 0%, #f5f8fc 100%);
  background-size: 8mm 8mm, 8mm 8mm, auto;
  border-radius: 2.4mm;
  padding: 4mm;
  margin: 8px 0 14px;
}}
.diagram-svg {{
  width: 100%;
  max-height: 175mm;
  height: auto;
  display: block;
}}
.diagram-node {{
  fill: #edf6ff;
  stroke: #6aa6d9;
  stroke-width: 1.4;
}}
.diagram-label {{
  fill: #10324d;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10px;
  font-weight: 700;
}}
.diagram-edge {{
  stroke: #64748b;
  stroke-width: 1.55;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
}}
.diagram-edge-label {{
  fill: #475569;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8px;
}}
pre {{
  background: #111827;
  color: #f9fafb;
  border-radius: 4px;
  padding: 10px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-family: Consolas, "Courier New", monospace;
  font-size: 9px;
}}
code {{ font-family: Consolas, "Courier New", monospace; }}
.muted {{ color: var(--text-secondary); }}
@media screen and (max-width: 900px) {{
  body {{ background: #fff; }}
  .page {{ width: auto; min-height: auto; margin: 0; padding: 22px; }}
  .metric-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media print {{
  body {{
    background: #fff;
    font-size: 11px;
  }}
  .page {{
    width: auto;
    min-height: auto;
    margin: 0;
    padding: 0 0 14mm;
    background: #fff;
    break-after: page;
    page-break-after: always;
  }}
  .cover-page {{
    padding: 0;
    background:
      radial-gradient(circle at 88% 12%, rgba(45, 117, 161, .50) 0 31mm, transparent 31.3mm),
      radial-gradient(circle at 98% 91%, rgba(0, 172, 189, .62) 0 40mm, transparent 40.3mm),
      radial-gradient(circle at 80% 89%, rgba(0, 121, 130, .46) 0 30mm, transparent 30.3mm),
      linear-gradient(rgba(69, 128, 161, .28) 1px, transparent 1px),
      linear-gradient(90deg, rgba(69, 128, 161, .28) 1px, transparent 1px),
      #061b2a;
    background-size: auto, auto, auto, 8.45mm 8.45mm, 8.45mm 8.45mm, auto;
    print-color-adjust: exact;
    -webkit-print-color-adjust: exact;
  }}
  table, .chart-card, .score-tile, .metric-tile, .callout {{
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  pre {{
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  .diagram-figure {{
    max-height: 185mm;
    overflow: hidden;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  .diagram-svg {{
    max-height: 175mm;
  }}
}}
"""


def _cover_page(content: ReleaseNoteContent) -> str:
    metrics = _headline_metrics(content)
    return f"""
<section class="page cover-page">
  <div class="source-line">{_source_line(content)}</div>
  <div class="eyebrow">
    BOS Genesis Release Note Agent | Commercial-grade release notes from repository evidence
  </div>
  <div class="cover-title">
    <h1>
      {_text(_product_name(content))}
      <span class="report-subtitle">
        Professional Release Notes and<br>Package Intelligence Report
      </span>
    </h1>
    <div class="version-line">
      {_text(content.release_name)} | Public GitHub repository analysis |
      Generated {_text(_date_only(content.generated_at))}
    </div>
  </div>
  <div class="metric-grid">
    {_metric_tile(metrics["tags"], "PUBLIC TAGS")}
    {_metric_tile(metrics["commits"], "COMMITS")}
    {_metric_tile(metrics["version"], "PACKAGE VERSION")}
    {_metric_tile(metrics["runtime"], "RUNTIME")}
  </div>
  <div class="cover-positioning">
    <h3>Release positioning</h3>
    <p>
      This document packages the visible repository evolution into an executive-ready
      release note with change history from repository evidence, package metadata,
      capability analysis, deployment posture, safety notes, validation checklist,
      risks, and next-release recommendations.
    </p>
  </div>
  {_key_value_table([
        [
            "Engineering Leaders",
            "Understand release maturity, delivery velocity, and technical scope.",
        ],
        [
            "DevOps / Platform",
            "Review packaging, Kubernetes/Helm posture, validation, and rollback readiness.",
        ],
        [
            "Citizen Development / Agent Platform Teams",
            "Understand how this agent contributes to reproducible BOS Genesis documentation.",
        ],
    ])}
</section>
"""


def _page(content: ReleaseNoteContent, number: str, title: str, body: str) -> str:
    return f"""
<section class="page">
  <header class="page-header">
    <div>
      <strong>
        {_text(_product_name(content))} - Release Notes {_text(content.release_name)}
      </strong><br>
    </div>
    <div>
      Commercial-grade sample release notes | Generated {_text(_date_only(content.generated_at))}
    </div>
  </header>
  <div class="page-content">
    <h2 class="section-heading">{_text(number)}. {_text(title)}</h2>
    {body}
  </div>
</section>
"""


def _metric_tiles(content: ReleaseNoteContent) -> str:
    metrics = _headline_metrics(content)
    tiles = "\n".join(_metric_tile(value, label) for label, value in metrics.items())
    return f'<div class="metric-grid">{tiles}</div>'


def _executive_metric_tiles(content: ReleaseNoteContent) -> str:
    metrics = _headline_metrics(content)
    rows = [
        ("11 days", "Release window"),
        (metrics["tags"], "Visible tags"),
        (_codebase_mix(content), "Codebase mix"),
        ("Read-only", "Safety mode"),
    ]
    tiles = "\n".join(_metric_tile(value, label) for value, label in rows)
    return f'<div class="executive-metrics">{tiles}</div>'


def _metric_tile(value: Any, label: str) -> str:
    return (
        f'<div class="metric-tile"><div class="metric-value">{_text(value)}</div>'
        f'<div class="metric-label">{_text(label)}</div></div>'
    )


def _executive_capability_sentence(content: ReleaseNoteContent) -> str:
    capabilities = []
    if _has_tech(content, "FastAPI"):
        capabilities.append("FastAPI service shell")
    if "http_route" in _interface_types(content):
        capabilities.append("REST endpoints")
    if "mcp_tool" in _interface_types(content) or _has_tech(content, "MCP"):
        capabilities.append("MCP-style tools")
    if _has_tech(content, "Docker"):
        capabilities.append("Dockerfile")
    if _has_tech(content, "Helm"):
        capabilities.append("Helm skeleton")
    if _has_tech(content, "Kubernetes"):
        capabilities.append("Kubernetes deployment posture")
    if _has_tech(content, "pytest"):
        capabilities.append("pytest")
    if _has_tech(content, "Ruff"):
        capabilities.append("Ruff CI readiness")
    return ", ".join(capabilities) or "repository evidence and release-note metadata"


def _executive_summary(content: ReleaseNoteContent) -> str:
    features = _feature_chips(content)
    return "\n".join(
        [
            (
                '<p class="section-intro">Commercial summary of the '
                f'{_text(content.release_name)} package, based on public repository evidence.</p>'
            ),
            f'<p>{_project_intent(content.analytics)}</p>',
            '<p>The current public repository describes a foundation release with '
            + _executive_capability_sentence(content)
            + ".</p>",
            _executive_metric_tiles(content),
            '<div class="feature-matrix">'
            + "".join(f'<div class="feature-cell">{_text(item)}</div>' for item in features[:8])
            + "</div>",
            '<div class="release-recommendation"><h3>Release recommendation</h3><p>'
            + _release_recommendation(content)
            + "</p></div>",
        ]
    )


def _release_info(content: ReleaseNoteContent) -> str:
    tech = _technology_names(content)
    return _key_value_table(
        [
            ["Product / Component", _product_name(content)],
            ["Repository", content.repository.replace("https://", "")],
            ["Package name", _package_name(content)],
            ["Current package version", _headline_metrics(content)["version"]],
            ["Release type", "Foundation / repository capability release"],
            ["Runtime requirement", _headline_metrics(content)["runtime"]],
            ["Primary interface", _primary_interface(content)],
            ["Target deployment model", _deployment_model(content)],
            ["Security posture", "Read-only repository analysis; no repository code execution"],
            ["Detected technology", ", ".join(tech[:12]) or "Not available"],
        ]
    )


def _release_dashboard(content: ReleaseNoteContent) -> str:
    tag_rows = _tag_rows(content)
    tag_counts = _capability_distribution(tag_rows)
    return "\n".join(
        [
            (
                '<p class="section-intro">Delivery velocity, capability mix, and '
                "maturity signals inferred from public repo evidence.</p>"
            ),
            '<div class="dashboard-grid">',
            (
                '<div class="chart-card"><h3>Tag Velocity: New tags/day with '
                "cumulative release growth</h3>"
            )
            + _tag_velocity_chart(tag_rows)
            + "</div>",
            '<div class="chart-card"><h3>Capability Distribution by Tag Theme</h3>'
            + _capability_pie_chart(tag_counts)
            + (
                '<p class="chart-note">Note: classification inferred from public tag names '
                "and commit messages; not a formal GitHub release taxonomy.</p></div>"
            ),
            "</div>",
        ]
    )


def _readiness(content: ReleaseNoteContent) -> str:
    scores = _readiness_scores(content)
    rows = [
        [item[0], f"{item[1]:.1f}/5", item[2], item[3]]
        for item in scores
    ]
    return (
        '<p class="section-intro">Analytical maturity scoring; intended for planning and '
        "review, not as a formal audit.</p>"
        + _readiness_scorecard(scores)
        + _table(
            ["Dimension", "Score", "Evidence-based interpretation", "Recommended action"],
            rows,
            class_name="readiness-table",
        )
    )


def _change_history(content: ReleaseNoteContent) -> str:
    rows = _tag_rows(content)
    if not rows:
        rows = _commit_rows(content)[:12]
    return (
        "<p>Visible repository history converted into business-friendly release history.</p>"
        + _table(
            [
                "Tag / Commit",
                "Date",
                "Commit",
                "Release theme",
                "Commercial value / change summary",
            ],
            rows,
            class_name="change-history-table",
        )
    )


def _capability_map(content: ReleaseNoteContent) -> str:
    rows = []
    for capability, evidence, interpretation in _capabilities(content):
        rows.append([capability, evidence, interpretation])
    notes = [
        "Spec-driven implementation",
        "Read-only discovery",
        "Traceability-oriented design",
        "Helm/Kubernetes deployment path"
        if _has_tech(content, "Helm")
        else "Deployment evidence limited",
        "Artifact-oriented output",
        "Future observability hooks",
    ]
    return (
        "<p>What the repository enables today and what remains clearly marked "
        "as future or partial scope.</p>"
        + _table(
            [
                "Capability area",
                "Delivered / visible in repo evidence",
                "Commercial interpretation",
            ],
            rows,
        )
        + "<h3>Non-functional notes</h3>"
        + '<div class="feature-grid">'
        + "".join(f'<div class="feature-chip">{_text(note)}</div>' for note in notes)
        + "</div>"
        + "<h3>Architecture evidence diagrams</h3>"
        + _diagrams(content)
    )


def _deployment(content: ReleaseNoteContent) -> str:
    commands = [
        ["Local install", 'python -m pip install -e ".[dev]"'],
        ["Local run", _package_name(content)],
        ["Helm deploy", "IMAGE_REPOSITORY=... IMAGE_TAG=... ./playbook/deploy.sh"],
        ["REST contract test", "curl -X POST http://localhost:8080/api/v1/scans ..."],
        ["MCP-style test", "curl http://localhost:8090/mcp/tools"],
    ]
    checklist = [
        ["Build integrity", "Docker image built, scanned, and mapped to exact Git commit."],
        ["API health", "/health returns healthy status after deployment."],
        ["Config safety", "Sensitive values are redacted from effective configuration."],
        ["MCP contract", "Tool list and health tool calls succeed."],
        ["Artifact output", "PDF and Markdown output paths are created, validated, and retained."],
        [
            "Safety test",
            "Agent cannot mutate Kubernetes, Helm, databases, streams, or application data.",
        ],
        ["Observability", "Correlation IDs, logs, traces, and metrics visible in target tools."],
        ["Rollback", "Uninstaller and Helm rollback path tested in non-production namespace."],
    ]
    return (
        "<p>Operator-ready release details for a professional deployment note.</p>"
        + _table(["Purpose", "Command"], commands)
        + "<h3>Recommended production-readiness checklist</h3>"
        + _table(["Gate", "Status to validate before promotion"], checklist)
    )


def _risks(content: ReleaseNoteContent) -> str:
    rows = [
        [
            "Generation behavior may be partially contract/stub-oriented.",
            "Users may expect full repository-to-artifact automation before it is wired.",
            "Mark release as foundation capability; label production readiness clearly.",
        ],
        [
            "No full coverage report evidence detected."
            if "coverage" in " ".join(content.analytics.gaps).lower()
            else "Coverage evidence is partial.",
            "Harder to prove runtime quality from repository files alone.",
            "Publish test reports and coverage artifacts in CI.",
        ],
        [
            "LLM or reasoning features require guardrails.",
            "Risk of nondeterministic or overreaching recommendations.",
            "Add bounded prompts, policy checks, and regression evaluations.",
        ],
        [
            "Kubernetes/Helm reconstruction must avoid secrets and mutation.",
            "Potential compliance risk if evidence export is too broad.",
            "Namespace-only RBAC, secret redaction, deny-list and audit events.",
        ],
    ]
    classifications = [
        [
            "External demo",
            "Safe for controlled demo as an initial agent package and release-history example.",
        ],
        [
            "Internal platform pilot",
            "Suitable for sandbox validation where read-only boundaries and artifact outputs "
            "are verified.",
        ],
        [
            "Production automation",
            "Not yet recommended unless evidence collection, artifacts, security, and "
            "observability are validated.",
        ],
    ]
    return (
        "<p>Transparent release-note section for commercial-grade governance.</p>"
        + _table(["Risk / limitation", "Impact", "Recommended control"], rows)
        + "<h3>Known evidence gaps</h3>"
        + _gaps_list(content.analytics.gaps, "No known evidence gaps were detected.")
        + "<h3>Release classification</h3>"
        + _table(["Classification", "Recommended wording"], classifications)
    )


def _recommendations(content: ReleaseNoteContent) -> str:
    rows = [
        [
            "P1",
            "Formal release management",
            "Create GitHub Releases with notes, artifact links, SBOM and checksums.",
            "Improves commercial credibility and traceable delivery.",
        ],
        [
            "P1",
            "Evidence engine",
            "Complete repository and runtime evidence collection.",
            "Makes generated notes grounded in runtime and source facts.",
        ],
        [
            "P1",
            "Artifact generation",
            "Wire end-to-end Markdown, HTML, and PDF generation into worker/API flow.",
            "Turns the agent from contract demo into usable documentation factory.",
        ],
        [
            "P1",
            "Security",
            "Add redaction, secret deny-list, read-only RBAC and policy tests.",
            "Makes enterprise adoption safer.",
        ],
        [
            "P2",
            "Observability",
            "Add OpenTelemetry spans, Langfuse traces, dashboards and correlation IDs.",
            "Improves supportability and executive demo evidence.",
        ],
        [
            "P2",
            "Persistence",
            "Store runs, artifacts, evidence bundles, decisions and audit records.",
            "Supports history, audit, and repeatability.",
        ],
        [
            "P2",
            "Evaluation",
            "Add reproducibility, grounding, safety and PDF quality evaluation suites.",
            "Improves confidence before promotion.",
        ],
    ]
    return (
        "<p>Commercially useful roadmap derived from gaps and existing repository direction.</p>"
        + _table(["Priority", "Theme", "Recommended next capability", "Business value"], rows)
        + '<div class="callout"><strong>Suggested next release title</strong><br>'
        + "v0.2.0 - Evidence-Grounded Release Artifact Generation: complete "
        "repository evidence extraction, deterministic PDF/Markdown generation, "
        "artifact retention, and smoke-test verification.</div>"
    )


def _repository_summary(content: ReleaseNoteContent) -> str:
    return _section_summary(content.analytics, "inventory") + _evidence_sample(content)


def _technology(content: ReleaseNoteContent) -> str:
    section = content.analytics.sections.get("technology")
    if not section:
        return "<p>Technology inventory is not available from repository evidence.</p>"
    rows = []
    for finding in section.data.get("findings", []):
        rows.append(
            [
                finding.get("name", "Unknown"),
                finding.get("category", "unknown"),
                f'{float(finding.get("confidence", 0.0)):.2f}',
                ", ".join(finding.get("evidence_ids", [])[:4]) or "Not available",
            ]
        )
    return _table(["Technology", "Category", "Confidence", "Evidence"], rows)


def _headline_metrics(content: ReleaseNoteContent) -> dict[str, str]:
    commits = content.analytics.sections.get("commits")
    commit_data = commits.data if commits else {}
    tags = {
        tag
        for commit in commit_data.get("commits", [])
        for tag in commit.get("tags", [])
        if tag
    }
    return {
        "tags": str(len(tags)) if tags else "N/A",
        "commits": str(commit_data.get("commit_count", 0)),
        "version": _package_version(content),
        "runtime": _runtime_requirement(content),
    }


def _product_name(content: ReleaseNoteContent) -> str:
    repository = content.repository.rstrip("/").rsplit("/", maxsplit=1)[-1]
    if repository:
        return repository.replace("-", " ").title().replace("Mop", "MoP")
    return content.title


def _package_name(content: ReleaseNoteContent) -> str:
    return content.repository.rstrip("/").rsplit("/", maxsplit=1)[-1] or content.title


def _package_version(content: ReleaseNoteContent) -> str:
    technology = content.analytics.sections.get("technology")
    if technology:
        for finding in technology.data.get("findings", []):
            details = finding.get("details") or {}
            version = details.get("version")
            if version:
                return str(version)
    release = str(content.release_name)
    if release and release not in {"repository-analysis-review", "latest"}:
        return release.removeprefix("v")
    return "N/A"


def _runtime_requirement(content: ReleaseNoteContent) -> str:
    technology = _technology_names(content)
    if "Python" in technology:
        return "Py 3.11+"
    return "Not available"


def _technology_names(content: ReleaseNoteContent) -> list[str]:
    section = content.analytics.sections.get("technology")
    if not section:
        return []
    return [str(finding.get("name", "Unknown")) for finding in section.data.get("findings", [])]


def _codebase_mix(content: ReleaseNoteContent) -> str:
    section = content.analytics.sections.get("technology")
    if not section:
        return "N/A"
    counts = section.data.get("language_file_counts", {})
    if not counts:
        return "N/A"
    total = sum(int(value) for value in counts.values()) or 1
    language, count = max(counts.items(), key=lambda item: int(item[1]))
    return f"{(int(count) / total) * 100:.1f}% {language}"


def _has_tech(content: ReleaseNoteContent, name: str) -> bool:
    return name.lower() in {item.lower() for item in _technology_names(content)}


def _primary_interface(content: ReleaseNoteContent) -> str:
    interfaces = content.analytics.sections.get("interfaces")
    names = set()
    if interfaces:
        for item in interfaces.data.get("interfaces", []):
            names.add(str(item.get("interface_type", "")))
    if {"http_route", "mcp_tool"}.issubset(names):
        return "FastAPI REST service plus MCP-style HTTP contract"
    if "http_route" in names:
        return "FastAPI REST service"
    if "mcp_tool" in names:
        return "MCP-style tool contract"
    return "Not available from repository evidence"


def _deployment_model(content: ReleaseNoteContent) -> str:
    parts = []
    if _has_tech(content, "Docker"):
        parts.append("Docker image")
    if _has_tech(content, "Helm"):
        parts.append("Helm chart")
    if _has_tech(content, "Kubernetes"):
        parts.append("Kubernetes deployment")
    return " + ".join(parts) if parts else "Not available from repository evidence"


def _source_line(content: ReleaseNoteContent) -> str:
    evidence_sources = ["public GitHub repository"]
    section = content.analytics.sections.get("documentation")
    if section:
        docs = section.data.get("documents", [])
        for document in docs[:6]:
            path = document.get("path")
            if path:
                evidence_sources.append(str(path))
    return "Source: " + ", ".join(dict.fromkeys(evidence_sources)) + "."


def _date_only(value: str) -> str:
    return value.split("T", maxsplit=1)[0]


def _feature_chips(content: ReleaseNoteContent) -> list[str]:
    features = []
    if _has_tech(content, "FastAPI"):
        features.append("REST-triggered generation")
    if _has_tech(content, "MCP"):
        features.append("MCP-style agent contract")
    if _has_tech(content, "Helm") or _has_tech(content, "Kubernetes"):
        features.append("Helm/Kubernetes deployment path")
    if _has_tech(content, "Docker"):
        features.append("Container packaging")
    if _has_tech(content, "pytest"):
        features.append("pytest quality baseline")
    if _has_tech(content, "Ruff"):
        features.append("Ruff CI readiness")
    features.extend(["Spec-first operating model", "Read-only safety posture"])
    return features[:8]


def _release_recommendation(content: ReleaseNoteContent) -> str:
    if content.analytics.gaps:
        return (
            "This release can be presented commercially as an initial platform-capability "
            "release. The strongest story is visible delivery progress and contracts; "
            "production readiness should remain clearly gated by the listed evidence gaps."
        )
    return (
        "This release can be presented as a repository-evidence-backed capability release "
        "with available analytics, artifacts, and traceability."
    )


def _tag_rows(content: ReleaseNoteContent) -> list[list[str]]:
    commits = content.analytics.sections.get("commits")
    if not commits:
        return []
    rows: list[list[str]] = []
    for commit in reversed(commits.data.get("commits", [])):
        for tag in commit.get("tags", []):
            theme = _theme_for_text(str(tag))
            rows.append(
                [
                    str(tag),
                    _date_only(str(commit.get("authored_at", ""))),
                    str(commit.get("sha", ""))[:7],
                    theme,
                    _commercial_summary(str(tag), str(commit.get("subject", "")), theme),
                ]
            )
    return rows


def _commit_rows(content: ReleaseNoteContent) -> list[list[str]]:
    commits = content.analytics.sections.get("commits")
    if not commits:
        return []
    rows: list[list[str]] = []
    for commit in commits.data.get("commits", [])[:12]:
        theme = _theme_for_text(str(commit.get("subject", "")))
        rows.append(
            [
                str(commit.get("subject", "Commit"))[:42],
                _date_only(str(commit.get("authored_at", ""))),
                str(commit.get("sha", ""))[:7],
                theme,
                _commercial_summary("", str(commit.get("subject", "")), theme),
            ]
        )
    return rows


def _theme_for_text(value: str) -> str:
    lowered = value.lower()
    if any(marker in lowered for marker in ("mcp", "api", "rest")):
        return "MCP/API Contract"
    if any(marker in lowered for marker in ("evidence", "snapshot", "lookup", "qdrant")):
        return "Evidence"
    if any(marker in lowered for marker in ("safety", "security", "classification")):
        return "Safety/Classification"
    if any(marker in lowered for marker in ("pdf", "markdown", "renderer", "document")):
        return "Doc Rendering"
    if any(marker in lowered for marker in ("reason", "llm", "langgraph")):
        return "Reasoning"
    if any(marker in lowered for marker in ("memory", "redis", "postgres")):
        return "Memory"
    if any(marker in lowered for marker in ("helm", "manifest", "kubernetes", "deploy")):
        return "Deployment"
    if any(marker in lowered for marker in ("spec", "foundation", "initial")):
        return "Foundation"
    return "Repository Change"


def _commercial_summary(tag: str, subject: str, theme: str) -> str:
    text = tag or subject
    if not text:
        return "Repository change recorded."
    normalized = text.replace("phase", "Phase ").replace("-", " ")
    normalized = " ".join(normalized.split())
    return f"{theme} milestone: {_truncate(normalized, 72)}."


def _capability_distribution(tag_rows: list[list[str]]) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for row in tag_rows:
        theme = row[3]
        distribution[theme] = distribution.get(theme, 0) + 1
    return dict(sorted(distribution.items(), key=lambda item: (-item[1], item[0])))


def _bar_chart(rows: list[tuple[str, int]]) -> str:
    max_value = max((value for _, value in rows), default=1) or 1
    output = []
    for label, value in rows[:10]:
        width = int((value / max_value) * 100) if max_value else 0
        output.append(
            '<div class="bar-row">'
            f'<div>{_text(label)}</div><div class="bar-track">'
            f'<div class="bar-fill" style="width:{width}%"></div></div>'
            f'<div>{_text(value)}</div></div>'
        )
    return "".join(output)


def _tag_velocity_chart(tag_rows: list[list[str]]) -> str:
    counts: dict[str, int] = {}
    for row in tag_rows:
        date = row[1] or "Unknown"
        counts[date] = counts.get(date, 0) + 1
    items = list(counts.items())[:8] or [("No tags", 0)]
    max_bar = max((count for _, count in items), default=1) or 1
    cumulative = []
    total = 0
    for _, count in items:
        total += count
        cumulative.append(total)
    max_line = max(cumulative, default=1) or 1
    chart_left = 48
    chart_top = 18
    chart_width = 330
    chart_height = 112
    bar_slot = chart_width / max(len(items), 1)
    parts = [
        '<svg class="chart-svg" viewBox="0 0 520 170" xmlns="http://www.w3.org/2000/svg">',
        '<line x1="48" y1="130" x2="388" y2="130" stroke="#061b2a" stroke-width="1"/>',
        '<line x1="48" y1="18" x2="48" y2="130" stroke="#061b2a" stroke-width="1"/>',
    ]
    for tick in range(max_bar + 1):
        y = chart_top + chart_height - (tick / max_bar) * chart_height
        parts.append(f'<text x="40" y="{y + 3:.1f}" text-anchor="end" font-size="8">{tick}</text>')
    points = []
    for index, (label, count) in enumerate(items):
        x = chart_left + index * bar_slot + bar_slot * 0.2
        width = bar_slot * 0.62
        height = (count / max_bar) * chart_height if max_bar else 0
        y = chart_top + chart_height - height
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" '
            'fill="#13b4bd" stroke="#061b2a" stroke-width=".8"/>'
        )
        parts.append(
            f'<text x="{x + width / 2:.1f}" y="145" text-anchor="middle" '
            f'font-size="7">{_text(_short_date(label))}</text>'
        )
        point_x = x + width / 2
        point_y = chart_top + chart_height - (cumulative[index] / max_line) * chart_height
        points.append((point_x, point_y))
    if len(points) > 1:
        path = " ".join(
            f"{'M' if index == 0 else 'L'} {x:.1f} {y:.1f}"
            for index, (x, y) in enumerate(points)
        )
        parts.append(f'<path d="{path}" fill="none" stroke="#7c3aed" stroke-width="2.2"/>')
    for x, y in points:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="#7c3aed" stroke="#fff"/>')
    parts.extend(
        [
            '<text x="430" y="48" font-size="8" fill="#00a7b5">Bars = new tags</text>',
            '<text x="430" y="64" font-size="8" fill="#7c3aed">Line = cumulative tags</text>',
            "</svg>",
        ]
    )
    return "".join(parts)


def _capability_pie_chart(distribution: dict[str, int]) -> str:
    items = _pie_items(distribution)
    total = sum(value for _, value in items) or 1
    colors = ["#3164e0", "#13b4bd", "#16a34a", "#f59e0b", "#7c3aed", "#0891b2", "#c2185b"]
    cx, cy, radius = 98, 86, 62
    start = -90.0
    slices = []
    legend = []
    percentages = _percentages_sum_to_100([value for _, value in items])
    for index, (label, value) in enumerate(items):
        end = start + (value / total) * 360
        color = colors[index % len(colors)]
        slices.append(_pie_slice(cx, cy, radius, start, end, color))
        pct = percentages[index]
        legend_y = 38 + index * 17
        legend.append(
            f'<rect x="260" y="{legend_y - 9}" width="10" height="10" fill="{color}"/>'
            f'<text x="278" y="{legend_y}" font-size="8">{_text(label)}: '
            f'{value} tag(s) - {pct}%</text>'
        )
        start = end
    return (
        '<svg class="chart-svg" viewBox="0 0 520 180" xmlns="http://www.w3.org/2000/svg">'
        + "".join(slices)
        + "".join(legend)
        + "</svg>"
    )


def _pie_items(distribution: dict[str, int], max_items: int = 7) -> list[tuple[str, int]]:
    items = list(distribution.items()) or [("Unclassified", 1)]
    if len(items) <= max_items:
        return items
    visible = items[: max_items - 1]
    other_total = sum(value for _, value in items[max_items - 1 :])
    return [*visible, ("Other", other_total)]


def _percentages_sum_to_100(values: list[int]) -> list[int]:
    total = sum(values) or 1
    raw = [(value / total) * 100 for value in values]
    floors = [int(value) for value in raw]
    remainder = 100 - sum(floors)
    order = sorted(
        range(len(values)),
        key=lambda index: raw[index] - floors[index],
        reverse=True,
    )
    for index in order[:remainder]:
        floors[index] += 1
    return floors


def _pie_slice(cx: int, cy: int, radius: int, start: float, end: float, color: str) -> str:
    import math

    start_rad = math.radians(start)
    end_rad = math.radians(end)
    x1 = cx + radius * math.cos(start_rad)
    y1 = cy + radius * math.sin(start_rad)
    x2 = cx + radius * math.cos(end_rad)
    y2 = cy + radius * math.sin(end_rad)
    large_arc = 1 if end - start > 180 else 0
    return (
        f'<path d="M {cx} {cy} L {x1:.2f} {y1:.2f} '
        f'A {radius} {radius} 0 {large_arc} 1 {x2:.2f} {y2:.2f} Z" '
        f'fill="{color}" stroke="#061b2a" stroke-width=".8"/>'
    )


def _short_date(value: str) -> str:
    parts = value.split("-")
    if len(parts) == 3:
        months = {
            "01": "Jan",
            "02": "Feb",
            "03": "Mar",
            "04": "Apr",
            "05": "May",
            "06": "Jun",
            "07": "Jul",
            "08": "Aug",
            "09": "Sep",
            "10": "Oct",
            "11": "Nov",
            "12": "Dec",
        }
        return f"{months.get(parts[1], parts[1])} {int(parts[2])}"
    return value


def _readiness_scores(content: ReleaseNoteContent) -> list[tuple[str, float, str, str]]:
    readiness = content.analytics.sections.get("readiness")
    if readiness:
        rows = []
        for item in readiness.data.get("scores", []):
            name = str(item.get("dimension", "Readiness"))
            try:
                score = float(item.get("score", 0.0))
            except (TypeError, ValueError):
                score = 0.0
            rows.append(
                (
                    name,
                    max(0.0, min(5.0, score)),
                    str(item.get("evidence_interpretation", "Evidence summary unavailable.")),
                    str(item.get("recommended_action", "Review repository evidence.")),
                )
            )
        if rows:
            return rows

    has_api = _primary_interface(content) != "Not available from repository evidence"
    has_docs = bool(content.analytics.sections.get("documentation", None))
    has_tests = bool(
        content.analytics.sections.get("test_coverage", None)
        and content.analytics.sections["test_coverage"].data.get("test_sources", [])
    )
    has_deploy = _deployment_model(content) != "Not available from repository evidence"
    return [
        (
            "API contract",
            4.0 if has_api else 2.0,
            "REST and/or MCP-style contracts are visible from repository evidence.",
            "Add formal OpenAPI examples and backward compatibility policy.",
        ),
        (
            "Documentation coverage",
            2.0,
            "Source documentation coverage was not analyzed in this bundle.",
            "Run the readiness analyzer to score docstrings or Javadoc-style comments.",
        ),
        (
            "Security scan",
            2.5,
            "Lightweight security scan evidence was not analyzed in this bundle.",
            "Run the readiness analyzer to detect secret patterns and risky operations.",
        ),
        (
            "Documentation",
            4.1 if has_docs else 2.2,
            "Project intent and specification files are visible where present.",
            "Close HLD, LLD, ADR and module-spec gaps.",
        ),
        (
            "Testing",
            3.2 if has_tests else 2.0,
            "Test source evidence is visible, but report artifacts may be missing.",
            "Publish pytest/JUnit and coverage artifacts.",
        ),
        (
            "Observability",
            2.4,
            "Runtime visibility is unclear from repository files alone.",
            "Add trace IDs, metrics, spans and dashboard screenshots.",
        ),
        (
            "Persistence",
            2.5,
            "Durability status requires explicit schema and migration evidence.",
            "Add run metadata schema and migration scripts.",
        ),
        (
            "Deployment packaging",
            3.7 if has_deploy else 2.4,
            "Docker/Helm/Kubernetes evidence is detected when present.",
            "Add production values, probes, limits, and release pipeline artifacts.",
        ),
    ]


def _readiness_scorecard(scores: list[tuple[str, float, str, str]]) -> str:
    colors = [
        "#3164e0",
        "#13b4bd",
        "#16a34a",
        "#7c3aed",
        "#c2185b",
        "#f59e0b",
        "#64748b",
        "#0891b2",
    ]
    aliases = {
        "API contract": "API",
        "Documentation coverage": "Docs",
        "Security scan": "Safety",
        "Documentation": "Reasoning",
        "Repository documentation": "Reasoning",
        "Testing": "Memory",
        "Observability": "Observability",
        "Persistence": "Persistence",
        "Deployment packaging": "Deployment",
    }
    rows = []
    for index, (name, score, _, _) in enumerate(scores):
        width = max(0, min(100, (score / 5) * 100))
        rows.append(
            '<div class="score-row">'
            f'<div>{_text(aliases.get(name, name))}</div>'
            '<div class="score-track">'
            f'<div class="score-fill" style="width:{width:.0f}%; '
            f'background:{colors[index % len(colors)]}"></div>'
            "</div>"
            f'<div>{score:.1f}/5</div>'
            "</div>"
        )
    return (
        '<div class="score-grid">'
        "<h3>Release Readiness Assessment (Analytical Estimate)</h3>"
        '<p class="muted">Score based on public repo evidence: contracts, source '
        "documentation coverage, lightweight security scan findings, tests, "
        "dependencies, and deployment files.</p>"
        + "".join(rows)
        + "</div>"
    )


def _capabilities(content: ReleaseNoteContent) -> list[tuple[str, str, str]]:
    rows = [
        (
            "REST service shell",
            "HTTP routes detected."
            if "http_route" in _interface_types(content)
            else "No explicit HTTP route contracts detected.",
            "Establishes service interface for demos, smoke tests, and integration discussion.",
        ),
        (
            "MCP-style integration",
            "MCP tools detected."
            if "mcp_tool" in _interface_types(content)
            else "No explicit MCP tools detected.",
            "Allows MCP-aware clients to call bounded repository or release-note operations.",
        ),
        (
            "Document outputs",
            "Markdown/HTML/PDF artifacts are supported by the release-note agent renderer.",
            "Creates dual-persona documentation: human operations and future agent execution.",
        ),
        (
            "Kubernetes/Helm posture",
            _deployment_model(content),
            "Aligns with BOS Genesis reproducibility and deployment review use cases.",
        ),
        (
            "Quality tooling",
            ", ".join(name for name in ("pytest", "Ruff") if _has_tech(content, name))
            or "Not available from repository evidence.",
            "Supports quality-gate and CI readiness discussion.",
        ),
        (
            "Safety posture",
            _safety_posture(content),
            "Strong fit for controlled enterprise automation and audit requirements.",
        ),
    ]
    return rows


def _safety_posture(content: ReleaseNoteContent) -> str:
    readiness = content.analytics.sections.get("readiness")
    if not readiness:
        return "Read-only repository evidence analysis."
    scan = readiness.data.get("security_scan", {})
    findings = scan.get("findings", [])
    controls = scan.get("controls", [])
    return (
        f"Lightweight scan found {len(findings)} sanitized finding(s); "
        f"controls: {', '.join(controls[:3]) if controls else 'none detected'}."
    )


def _interface_types(content: ReleaseNoteContent) -> set[str]:
    section = content.analytics.sections.get("interfaces")
    if not section:
        return set()
    return {str(item.get("interface_type", "")) for item in section.data.get("interfaces", [])}


def _mermaid_flowchart_svg(source: str) -> str:
    direction, nodes, edges = _parse_mermaid_flowchart(source)
    if not nodes:
        return f"<pre><code>{_text(source)}</code></pre>"

    node_ids = list(nodes)
    positions = _diagram_positions(node_ids, direction, edges)
    node_width, node_height = _diagram_node_size(len(node_ids), direction)
    width = max(x + node_width for x, _ in positions.values()) + 20
    height = max(y + node_height for _, y in positions.values()) + 18
    parts = [
        (
            f'<svg class="diagram-svg" viewBox="0 0 {width} {height}" '
            'xmlns="http://www.w3.org/2000/svg" role="img">'
        ),
        _diagram_defs(),
    ]
    for index, (left, right, label) in enumerate(edges):
        if left not in positions or right not in positions:
            continue
        x1, y1 = positions[left]
        x2, y2 = positions[right]
        start_x, start_y, end_x, end_y = _edge_points(
            x1,
            y1,
            x2,
            y2,
            direction,
            node_width,
            node_height,
        )
        parts.append(_diagram_edge_path(start_x, start_y, end_x, end_y, direction, index))
        if label:
            parts.append(
                f'<text class="diagram-edge-label" x="{(start_x + end_x) / 2:.1f}" '
                f'y="{(start_y + end_y) / 2 - 5:.1f}" text-anchor="middle">'
                f'{_text(label)}</text>'
            )
    for index, (node_id, label) in enumerate(nodes.items()):
        x, y = positions[node_id]
        fill_id = f"nodeFill{index % 5}"
        parts.append(
            f'<rect class="diagram-node" x="{x}" y="{y}" rx="9" '
            f'width="{node_width}" height="{node_height}" '
            f'fill="url(#{fill_id})" filter="url(#nodeShadow)"/>'
        )
        for index, line in enumerate(_wrap_svg_label(label)):
            parts.append(
                f'<text class="diagram-label" x="{x + node_width / 2:.1f}" '
                f'y="{y + 16 + index * 11}" '
                f'text-anchor="middle">{_text(line)}</text>'
            )
    parts.append("</svg>")
    return "".join(parts)


def _parse_mermaid_flowchart(source: str) -> tuple[str, dict[str, str], list[tuple[str, str, str]]]:
    direction = "LR"
    nodes: dict[str, str] = {}
    edges: list[tuple[str, str, str]] = []
    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("flowchart"):
            parts = line.split()
            direction = parts[1] if len(parts) > 1 else "LR"
            continue
        for node_id, label in re.findall(r"([A-Za-z0-9_]+)\[([^\]]+)\]", line):
            nodes.setdefault(node_id, label)
        if "-->" in line:
            edges.extend(_parse_mermaid_edges(line, nodes))
    return direction, nodes, edges


def _parse_mermaid_edges(line: str, nodes: dict[str, str]) -> list[tuple[str, str, str]]:
    cleaned = re.sub(r"([A-Za-z0-9_]+)\[([^\]]+)\]", r"\1", line)
    tokens = [token.strip() for token in cleaned.split("-->")]
    parsed: list[tuple[str, str, str]] = []
    previous = _edge_node_id(tokens[0])
    for token in tokens[1:]:
        label = ""
        label_match = re.match(r"\|([^|]+)\|\s*(.+)$", token)
        if label_match:
            label = label_match.group(1).strip()
            node = _edge_node_id(label_match.group(2))
        else:
            node = _edge_node_id(token)
        if previous and node:
            nodes.setdefault(previous, previous.replace("_", " ").title())
            nodes.setdefault(node, node.replace("_", " ").title())
            parsed.append((previous, node, label))
        previous = node
    return parsed


def _edge_node_id(value: str) -> str:
    match = re.match(r"([A-Za-z0-9_]+)", value.strip())
    return match.group(1) if match else ""


def _diagram_positions(
    node_ids: list[str],
    direction: str,
    edges: list[tuple[str, str, str]],
) -> dict[str, tuple[int, int]]:
    if _is_fan_in_out_diagram(node_ids, edges):
        return _fan_in_out_positions(node_ids, direction)

    positions: dict[str, tuple[int, int]] = {}
    node_width, node_height = _diagram_node_size(len(node_ids), direction)
    if direction == "TB":
        columns = 3 if len(node_ids) >= 6 else 2 if len(node_ids) > 3 else 1
        for index, node_id in enumerate(node_ids):
            col = index % columns
            row = index // columns
            positions[node_id] = (18 + col * (node_width + 34), 16 + row * (node_height + 36))
        return positions
    rows = 2 if len(node_ids) > 4 else 1
    for index, node_id in enumerate(node_ids):
        row = index % rows
        col = index // rows
        positions[node_id] = (18 + col * (node_width + 36), 16 + row * (node_height + 34))
    return positions


def _is_fan_in_out_diagram(
    node_ids: list[str],
    edges: list[tuple[str, str, str]],
) -> bool:
    if len(node_ids) < 7 or "evidence" not in node_ids or "bundle" not in node_ids:
        return False
    edge_pairs = {(left, right) for left, right, _ in edges}
    middle_nodes = [node_id for node_id in node_ids if node_id not in {"evidence", "bundle"}]
    return any(("evidence", node_id) in edge_pairs for node_id in middle_nodes) and any(
        (node_id, "bundle") in edge_pairs for node_id in middle_nodes
    )


def _fan_in_out_positions(node_ids: list[str], direction: str) -> dict[str, tuple[int, int]]:
    node_width, node_height = _diagram_node_size(len(node_ids), direction)
    middle_nodes = [node_id for node_id in node_ids if node_id not in {"evidence", "bundle"}]
    columns = 3 if len(middle_nodes) > 4 else 2
    x_gap = 28
    y_gap = 26
    grid_width = columns * node_width + (columns - 1) * x_gap
    rows = (len(middle_nodes) + columns - 1) // columns
    grid_height = rows * node_height + max(0, rows - 1) * y_gap
    center_y = 16 + max(grid_height, node_height) // 2 - node_height // 2

    positions = {
        "evidence": (18, center_y),
        "bundle": (18 + node_width + 38 + grid_width + 38, center_y),
    }
    grid_x = 18 + node_width + 38
    for index, node_id in enumerate(middle_nodes):
        row = index // columns
        col = index % columns
        positions[node_id] = (
            grid_x + col * (node_width + x_gap),
            16 + row * (node_height + y_gap),
        )
    return {node_id: positions[node_id] for node_id in node_ids}


def _diagram_node_size(node_count: int, direction: str) -> tuple[int, int]:
    if node_count >= 7 or direction == "TB":
        return 112, 34
    return 126, 38


def _edge_points(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    direction: str,
    node_width: int,
    node_height: int,
) -> tuple[int, int, int, int]:
    if direction == "TB":
        return (
            x1 + node_width // 2,
            y1 + node_height,
            x2 + node_width // 2,
            y2,
        )
    return x1 + node_width, y1 + node_height // 2, x2, y2 + node_height // 2


def _diagram_defs() -> str:
    gradients = [
        ("nodeFill0", "#eef7ff", "#dbeafe"),
        ("nodeFill1", "#f4f0ff", "#ede9fe"),
        ("nodeFill2", "#ecfeff", "#cffafe"),
        ("nodeFill3", "#f0fdf4", "#dcfce7"),
        ("nodeFill4", "#fff7ed", "#ffedd5"),
    ]
    gradient_defs = "".join(
        f'<linearGradient id="{name}" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="{start}"/>'
        f'<stop offset="100%" stop-color="{end}"/></linearGradient>'
        for name, start, end in gradients
    )
    return (
        "<defs>"
        + gradient_defs
        + '<filter id="nodeShadow" x="-10%" y="-20%" width="130%" height="150%">'
        '<feDropShadow dx="0" dy="1.2" stdDeviation="1.4" flood-color="#0f172a" '
        'flood-opacity=".16"/></filter>'
        '<marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" '
        'orient="auto" markerUnits="strokeWidth">'
        '<path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/></marker>'
        "</defs>"
    )


def _diagram_edge_path(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    direction: str,
    index: int,
) -> str:
    if direction == "TB":
        mid_y = (start_y + end_y) / 2
        path = (
            f"M {start_x} {start_y} C {start_x} {mid_y:.1f}, "
            f"{end_x} {mid_y:.1f}, {end_x} {end_y}"
        )
    else:
        mid_x = (start_x + end_x) / 2
        offset = ((index % 3) - 1) * 6
        path = (
            f"M {start_x} {start_y} C {mid_x:.1f} {start_y + offset:.1f}, "
            f"{mid_x:.1f} {end_y - offset:.1f}, {end_x} {end_y}"
        )
    return f'<path class="diagram-edge" d="{path}" marker-end="url(#arrow)"/>'


def _wrap_svg_label(label: str, max_chars: int = 18) -> list[str]:
    words = label.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines[:2] or [label[:max_chars]]


def _diagrams(content: ReleaseNoteContent) -> str:
    if not content.diagrams.diagrams:
        return "<p>No diagrams are available from current evidence.</p>"
    blocks = []
    for diagram in content.diagrams.diagrams:
        rendered = _mermaid_flowchart_svg(diagram.source)
        blocks.append(
            f"""
<h3>{_text(diagram.title)}</h3>
<p class="muted">{_text(diagram.caption)} Confidence: {_text(f"{diagram.confidence:.2f}")}.</p>
<div class="diagram-figure">{rendered}</div>
"""
        )
    if content.diagrams.gaps:
        blocks.append(_gaps_list(content.diagrams.gaps, ""))
    return "\n".join(blocks)


def _interfaces(content: ReleaseNoteContent) -> str:
    section = content.analytics.sections.get("interfaces")
    if not section:
        return "<p>Interface inventory is not available from repository evidence.</p>"
    interfaces = section.data.get("interfaces", [])
    recommendations = section.data.get("recommendations", [])
    rows = [
        [
            item.get("name", "Unknown"),
            item.get("interface_type", item.get("type", "unknown")),
            item.get("direction", "unknown"),
            f'{float(item.get("confidence", 0.0)):.2f}',
            item.get("evidence_id") or ", ".join(item.get("evidence_ids", [])),
        ]
        for item in interfaces
    ]
    output = [_table(["Interface", "Type", "Direction", "Confidence", "Evidence"], rows)]
    if recommendations:
        output.append(_gaps_list(recommendations, ""))
    return "\n".join(output)


def _commits(content: ReleaseNoteContent) -> str:
    section = content.analytics.sections.get("commits")
    if not section:
        return "<p>Commit analytics are not available from repository evidence.</p>"
    data = section.data
    rows = [
        ["Commit Count", data.get("commit_count", 0)],
        ["Authors", len(data.get("authors", []))],
        ["Changed Files", len(data.get("changed_files", []))],
        ["Risky Areas", len(data.get("risky_areas", []))],
    ]
    return _key_value_table(rows)


def _tests_and_coverage(content: ReleaseNoteContent) -> str:
    section = content.analytics.sections.get("test_coverage")
    if not section:
        return "<p>Test and coverage evidence is not available from repository files.</p>"
    data = section.data
    rows = [
        ["Test Source Files", len(data.get("test_sources", []))],
        ["Parsed Test Reports", len(data.get("test_reports", []))],
        ["Coverage Reports", len(data.get("coverage_reports", []))],
        ["Coverage", _coverage_value(content.analytics)],
    ]
    return _key_value_table(rows) + _gaps_list(section.gaps, "Coverage evidence is available.")


def _risk_and_gaps(content: ReleaseNoteContent) -> str:
    return "\n".join(
        [
            '<div class="callout"><strong>Readiness posture:</strong> '
            "Repository evidence has been summarized, but human release ownership "
            "remains required.</div>",
            _gaps_list(content.analytics.gaps, "No known evidence gaps were detected."),
            _gaps_list(content.analytics.warnings, "No analyzer warnings were emitted."),
        ]
    )


def _evidence_appendix(content: ReleaseNoteContent) -> str:
    if not content.analytics.evidence_ids:
        return "<p>No evidence references are available.</p>"
    blocks = []
    for evidence_id in content.analytics.evidence_ids:
        record = content.evidence.get(evidence_id) if content.evidence else None
        source = record.source_path if record else "Not available"
        source_type = record.source_type if record else "Not available"
        summary = record.summary if record else "Evidence metadata not available."
        blocks.append(
            f"""
<div class="evidence-block">
  <div class="evidence-id">{_text(evidence_id)}</div>
  <div><strong>Source:</strong> {_text(source)} ({_text(source_type)})</div>
  <div>{_text(summary)}</div>
</div>
"""
        )
    return "\n".join(blocks)


def _evidence_sample(content: ReleaseNoteContent) -> str:
    if not content.analytics.evidence_ids:
        return "<p>No source evidence IDs are available.</p>"
    sample = ", ".join(content.analytics.evidence_ids[:8])
    return f'<p class="muted">Evidence sample: {_text(sample)}</p>'


def _section_summary(bundle: AnalyticsBundle, section_name: str) -> str:
    section = bundle.sections.get(section_name)
    title = section_name.replace("_", " ").title()
    if not section:
        return f"<p>{_text(title)} evidence is not available.</p>"
    if section.gaps:
        return _gaps_list(section.gaps, f"{title} data is available with gaps.")
    return (
        f"<p>{_text(title)} data is available with "
        f"{len(section.evidence_ids)} evidence references.</p>"
    )


def _project_intent(bundle: AnalyticsBundle) -> str:
    section = bundle.sections.get("documentation")
    if not section:
        return "Project intent is not available because documentation analysis is missing."
    intent = section.data.get("project_intent", {})
    text = intent.get("text")
    source = intent.get("source", "unavailable")
    evidence = intent.get("evidence_id")
    if not text:
        return "Project intent is unavailable from current evidence."
    suffix = f" Evidence: {evidence}." if evidence else ""
    return f"{_text(text)} Intent source: {_text(source)}.{_text(suffix)}"


def _gaps_list(items: tuple[str, ...] | list[str], empty_message: str) -> str:
    if not items:
        return f"<p>{_text(empty_message)}</p>" if empty_message else ""
    lines = "".join(f"<li>{_text(item)}</li>" for item in items)
    return f"<ul>{lines}</ul>"


def _key_value_table(rows: list[list[Any]]) -> str:
    return _table(["Metric", "Value"], rows)


def _table(headers: list[str], rows: list[list[Any]], class_name: str | None = None) -> str:
    if not rows:
        return "<p>Not available from repository evidence.</p>"
    head = "".join(f"<th>{_text(header)}</th>" for header in headers)
    body = "\n".join(
        "<tr>" + "".join(f"<td>{_text(value)}</td>" for value in row) + "</tr>"
        for row in rows
    )
    class_attr = f' class="{_text(class_name)}"' if class_name else ""
    return f"<table{class_attr}><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _coverage_value(bundle: AnalyticsBundle) -> str:
    section = bundle.sections.get("test_coverage")
    if not section:
        return "Not available"
    reports = section.data.get("coverage_reports", [])
    for report in reports:
        rate = report.get("line_rate")
        if rate is not None:
            return f"{float(rate) * 100:.1f}%"
    return "Not available"


def _confidence(content: ReleaseNoteContent) -> str:
    diagram_scores = [diagram.confidence for diagram in content.diagrams.diagrams]
    if not diagram_scores:
        return "Not available"
    return f"{sum(diagram_scores) / len(diagram_scores):.2f}"


def _nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _not_available(value: Any) -> str:
    if value is None or value == "":
        return "Not available"
    return str(value)


def _truncate(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "…"


def _text(value: Any) -> str:
    return escape(str(value), quote=True)
