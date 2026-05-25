#!/usr/bin/env python3
"""
Build index.html from content files.
Usage: python build.py
"""

import json
import re
from pathlib import Path

ROOT    = Path(__file__).parent
CONTENT = ROOT / "content"


# ── Markdown helpers ──────────────────────────────────────────────────────────

def inline_md(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*",     r"<em>\1</em>",         text)
    return text


def emphasize_label(text):
    return re.sub(r"^([^:]+):", r"<strong>\1:</strong>", text, count=1)

def md_to_html(text):
    """Convert paragraphs, ## headings, - lists, **bold**, *italic* to HTML."""
    blocks = re.split(r"\n{2,}", text.strip())
    html = []
    for block in blocks:
        lines = block.strip().split("\n")
        first = lines[0]
        if first.startswith("## "):
            html.append(f'<div class="interests-label">{inline_md(first[3:])}</div>')
        elif first.startswith("- "):
            items = "".join(
                f"<li>{inline_md(l[2:])}</li>" for l in lines if l.startswith("- ")
            )
            html.append(f'<ul class="interests-list">{items}</ul>')
        else:
            para = " ".join(inline_md(l) for l in lines)
            html.append(f"<p>{para}</p>")
    return "\n".join(html)


def split_about_sections(text):
    blocks = re.split(r"\n{2,}", text.strip())
    intro_blocks = []
    interest_lines = []
    in_interests = False

    for block in blocks:
        lines = block.strip().split("\n")
        first = lines[0]
        if first.startswith("## "):
            in_interests = True
            continue
        if in_interests or first.startswith("- "):
            interest_lines.extend(l for l in lines if l.startswith("- "))
        else:
            intro_blocks.append(block)

    intro_html = md_to_html("\n\n".join(intro_blocks))
    interests_html = (
        '<ul class="interests-list">'
        + "".join(f"<li>{inline_md(l[2:])}</li>" for l in interest_lines)
        + "</ul>"
        if interest_lines
        else ""
    )
    return intro_html, interests_html


# ── Section builders ──────────────────────────────────────────────────────────

def build_social(meta):
    email_icon = (
        '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="2" y="4" width="20" height="16" rx="2"/>'
        '<path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>'
    )
    phone_icon = (
        '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>'
    )
    web_icon = (
        '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
    )
    parts = []
    if meta.get("email"):
        parts.append(f'<a href="mailto:{meta["email"]}" class="contact-item"><span class="contact-icon">{email_icon}</span><span>{meta["email"]}</span></a>')
    if meta.get("phone"):
        parts.append(f'<span class="contact-item"><span class="contact-icon">{phone_icon}</span><span>{meta["phone"]} (Zalo)</span></span>')
    for key, label in [("github", "GitHub"), ("linkedin", "LinkedIn"), ("scholar", "Scholar")]:
        if meta.get(key):
            parts.append(f'<a href="{meta[key]}" class="contact-item"><span>{label}</span></a>')
    return "\n".join(parts)


def build_skills(skills):
    rows = []
    for s in skills:
        rows.append(
            f'<div class="skill-row">'
            f'<span class="skill-label">{s["label"]}</span>'
            f'<span class="skill-value">{s["value"]}</span>'
            f'</div>'
        )
    return "\n".join(rows)


def build_publications(pubs):
    papers = []
    models = []
    reviews = []

    def render_item(p, item_class, tag_label):
        byline_parts = [f'<span class="venue">{p["venue"]}</span>']
        if p.get("date") and p["date"] != p["venue"]:
            byline_parts.extend(['<span class="pub-sep"></span>', f'<span>{p["date"]}</span>'])
        if p.get("role"):
            byline_parts.append(f' · <span class="role">{p["role"]}</span>')
        byline = "".join(byline_parts)

        return f"""\
        <article class="{item_class}">
          <div class="pub-head">
            <div class="pub-meta">
              <span class="pub-type">{tag_label}</span>
              <span class="pub-year">{p["date"]}</span>
            </div>
          </div>
          <div class="pub-title">{p['title']}</div>
          <div class="pub-byline">{byline}</div>
          <p class="pub-desc">{p['desc']}</p>
        </article>"""

    for p in pubs:
        status = p.get("status", "published")
        if status == "review":
            reviews.append(render_item(p, "pub-item pub-review", "Under Review"))
        elif p["type"] == "model":
            models.append(render_item(p, "pub-item pub-model", "Model"))
        else:
            papers.append(render_item(p, "pub-item pub-paper", "Paper"))

    return (
        '<div class="pub-columns">'
        '<div class="pub-column"><div class="pub-column-title">Papers</div>'
        '<div class="pub-stack">\n' + "\n".join(papers) + "\n</div></div>"
        '<div class="pub-column"><div class="pub-column-title">Models</div>'
        '<div class="pub-stack">\n' + "\n".join(models + reviews) + "\n</div></div>"
        '</div>'
    )


def build_experience(jobs):
    items = []
    for j in jobs:
        period     = j.get("period") or "—"
        is_current = "present" in period.lower()
        dot_class  = "exp-dot current" if is_current else "exp-dot"
        company_text = j["org"].replace(" · ", " - ")
        location_line = f'<div class="exp-location">{j["location"]}</div>' if j.get("location") else ""
        company = f'<div class="exp-org">{company_text}</div>{location_line}'
        location_time_parts = []
        if period:
            location_time_parts.append(period)
        location_time = (
            f'<div class="exp-meta">{" · ".join(location_time_parts)}</div>'
            if location_time_parts
            else ""
        )
        bullets    = ""
        if j.get("bullets"):
            lis     = "".join(f"<li>{emphasize_label(b)}</li>" for b in j["bullets"])
            bullets = f'<ul class="exp-bullets">{lis}</ul>'
        items.append(f"""\
        <article class="exp-item">
          <div class="exp-head">
            <div>
              <div class="exp-role-line">
                <div class="exp-role">{j['role']}</div>
              </div>
              {company}
              {location_time}
            </div>
          </div>
          {bullets}
        </article>""")
    return "\n".join(items)


def build_education(edu):
    # Degrees
    degree_items = []
    for d in edu["degrees"]:
        degree_items.append(f"""\
      <article class="edu-item">
        <div class="edu-head">
          <div>
            <div class="edu-degree">{d['degree']}</div>
            <div class="edu-inst">{d['institution']}</div>
          </div>
          <div class="edu-period">{d['period']}</div>
        </div>
      </article>""")
    degrees_html = '<div class="edu-list">\n' + "\n".join(degree_items) + "\n</div>"

    # Languages
    lang_html = f'<p class="edu-lang">{edu["languages"]}</p>' if edu.get("languages") else ""

    # Awards
    awards_html = ""
    if edu.get("awards"):
        lis = "".join(f"<li>{a}</li>" for a in edu["awards"])
        awards_html = (
            '<div class="awards-label">Leadership &amp; Community</div>'
            f'<ul class="awards-list">{lis}</ul>'
        )

    return degrees_html + lang_html + awards_html


# ── Main ──────────────────────────────────────────────────────────────────────

def build():
    meta  = json.loads((CONTENT / "meta.json").read_text())
    about_raw = (CONTENT / "about.md").read_text()
    about = md_to_html(about_raw)
    about_intro, about_interests = split_about_sections(about_raw)
    pubs  = json.loads((CONTENT / "publications.json").read_text())
    exp   = json.loads((CONTENT / "experience.json").read_text())
    skills = json.loads((CONTENT / "skills.json").read_text())
    edu   = json.loads((CONTENT / "education.json").read_text())

    template = (ROOT / "template.html").read_text()

    resume_url = meta.get("resume_url") or (f'mailto:{meta["email"]}?subject=CV%20Request' if meta.get("email") else "#")
    resume_label = "Download CV" if meta.get("resume_url") else "Request CV"

    replacements = {
        "{{META_NAME}}":      meta["name"],
        "{{META_ALIAS}}":     meta.get("alias", ""),
        "{{META_INITIALS}}":  "".join(part[0] for part in meta["name"].split()[:2]).upper(),
        "{{META_ROLE}}":      meta["role"],
        "{{META_ORG}}":       meta["org"],
        "{{META_TAGLINE}}":   meta["tagline"],
        "{{META_HERO_TITLE}}": "Research-minded, Production-disciplined",
        "{{META_HERO_DESC}}": "AI Research Engineer at ATMRI (NTU).",
        "{{SOCIAL_LINKS}}":   build_social(meta),
        "{{ABOUT}}":          about,
        "{{ABOUT_INTRO}}":    about_intro,
        "{{ABOUT_INTERESTS}}": about_interests,
        "{{SKILLS}}":         build_skills(skills),
        "{{PUBLICATIONS}}":   build_publications(pubs),
        "{{EXPERIENCE}}":     build_experience(exp),
        "{{EDUCATION}}":      build_education(edu),
        "{{RESUME_URL}}":     resume_url,
        "{{RESUME_LABEL}}":   resume_label,
    }

    output = template
    for key, val in replacements.items():
        output = output.replace(key, val)

    out = ROOT / "index.html"
    out.write_text(output)
    print(f"Built → {out}")


if __name__ == "__main__":
    build()
