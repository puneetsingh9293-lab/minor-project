import datetime
import hashlib
import io
import re
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# =========================================================
# DESIGN: same mixed theme as the app.
# Light pages for reading, dark panels for the banner, the
# verdict gauge and the roadmap flowchart.
# =========================================================

INK = colors.HexColor("#14262B")
INK_2 = colors.HexColor("#3B4F55")
MUTED = colors.HexColor("#66787D")
LINE = colors.HexColor("#D3DAD5")
PAPER = colors.HexColor("#F1F3EF")
GOLD = colors.HexColor("#F2A900")
CREAM = colors.HexColor("#FFF3D1")
CREAM_SOFT = colors.HexColor("#FFF9E6")
MINT = colors.HexColor("#6EE0B2")
CORAL = colors.HexColor("#FF8F7E")
RISK = colors.HexColor("#B4382C")
WHITE = colors.white

CONTENT_W = 540  # letter width 612 minus 2 x 36pt margins

# Same palettes and hashing as the app, so the logo in the PDF matches the one on screen.
LOGO_PALETTES = [
    ("#14262B", "#F2A900", "#FFF3D1"),
    ("#1D7A57", "#FFFFFF", "#C9F2E0"),
    ("#2B3A8F", "#FFD166", "#DDE3FF"),
    ("#B4382C", "#FFF3D1", "#FFD9D2"),
    ("#4B2E83", "#6EE0B2", "#E7DDFB"),
    ("#0F5E73", "#F2A900", "#D5F1F8"),
]


# =========================================================
# SMALL HELPERS
# =========================================================

def _hash(text):
    return int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)


def _initials(text):
    words = re.findall(r"[A-Z][a-z0-9]*|[a-z0-9]+", text or "")
    if not words:
        return "AI"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def _safe(text):
    """Make text safe for the built-in PDF fonts."""
    t = "" if text is None else str(text)
    for a, b in (("\u2192", "->"), ("\u2265", ">="), ("\u2264", "<="), ("\u2019", "'"),
                 ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'), ("\u2026", "...")):
        t = t.replace(a, b)
    return t.encode("latin-1", "replace").decode("latin-1")


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _pct(v):
    v = _num(v)
    return f"{v:.0f}" if abs(v - round(v)) < 0.05 else f"{v:.1f}"


def _fit_font(text, font, size, max_w, min_size=11):
    while size > min_size and stringWidth(text, font, size) > max_w:
        size -= 1
    return size


def _clip(text, font, size, max_w):
    if stringWidth(text, font, size) <= max_w:
        return text
    while text and stringWidth(text + "...", font, size) > max_w:
        text = text[:-1]
    return text.rstrip() + "..."


# =========================================================
# GENERATED LOGO (drawn straight onto the PDF canvas)
# =========================================================

def draw_logo(c, x, y, size, name, seed=0):
    """Draw the generated logo with its lower-left corner at (x, y)."""
    h = _hash(f"{(name or 'idea').lower()}|{seed}")
    bg, fg, soft = (colors.HexColor(v) for v in LOGO_PALETTES[h % len(LOGO_PALETTES)])
    kind = (h // 7) % 4
    ini = _safe(_initials(name))

    c.saveState()
    # Work in the same 120 x 120, y-down space as the on-screen SVG logo.
    c.translate(x, y + size)
    c.scale(size / 120.0, -(size / 120.0))

    def label(tx, ty, fs, fill):
        c.saveState()
        c.translate(tx, ty)
        c.scale(1, -1)  # flip back so the text is upright
        c.setFillColor(fill)
        c.setFont("Helvetica-Bold", fs)
        c.drawCentredString(0, 0, ini)
        c.restoreState()

    def rounded_clip():
        p = c.beginPath()
        p.roundRect(0, 0, 120, 120, 32)
        c.clipPath(p, stroke=0, fill=0)

    if kind == 0:  # soft square with a spark
        c.saveState()
        rounded_clip()
        c.setFillColor(bg)
        c.rect(0, 0, 120, 120, fill=1, stroke=0)
        c.setFillColor(fg)
        c.setFillAlpha(0.18)
        c.circle(18, 112, 46, fill=1, stroke=0)
        c.setFillAlpha(1)
        c.circle(96, 26, 12, fill=1, stroke=0)
        c.restoreState()
        label(60, 76, 46, soft)
    elif kind == 1:  # ring
        c.setFillColor(bg)
        c.circle(60, 60, 58, fill=1, stroke=0)
        c.setStrokeColor(fg)
        c.setLineWidth(3)
        c.circle(60, 60, 47, fill=0, stroke=1)
        c.setFillColor(fg)
        c.circle(60, 13, 5, fill=1, stroke=0)
        label(60, 74, 42, soft)
    elif kind == 2:  # hexagon with a pulse line
        p = c.beginPath()
        p.moveTo(60, 4)
        for px, py in ((110, 32), (110, 88), (60, 116), (10, 88), (10, 32)):
            p.lineTo(px, py)
        p.close()
        c.setFillColor(bg)
        c.drawPath(p, fill=1, stroke=0)
        c.setStrokeColor(fg)
        c.setLineWidth(4)
        c.setLineCap(1)
        c.setLineJoin(1)
        q = c.beginPath()
        q.moveTo(26, 84)
        for px, py in ((44, 84), (52, 70), (64, 98), (72, 84), (94, 84)):
            q.lineTo(px, py)
        c.drawPath(q, fill=0, stroke=1)
        label(60, 62, 34, soft)
    else:  # split corner
        c.saveState()
        rounded_clip()
        c.setFillColor(bg)
        c.rect(0, 0, 120, 120, fill=1, stroke=0)
        c.setFillColor(fg)
        c.setFillAlpha(0.92)
        t = c.beginPath()
        t.moveTo(120, 40)
        t.lineTo(120, 120)
        t.lineTo(30, 120)
        t.close()
        c.drawPath(t, fill=1, stroke=0)
        c.restoreState()
        label(52, 66, 44, soft)

    c.restoreState()


def draw_brand_mark(c, x, y, size):
    """The AI Startup Validator mark: a shield with a check."""
    c.saveState()
    c.translate(x, y + size)
    c.scale(size / 30.0, -(size / 30.0))
    c.setFillColor(INK)
    c.roundRect(0, 0, 30, 30, 8, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.8)
    c.setLineJoin(1)
    p = c.beginPath()
    p.moveTo(15, 4.5)
    p.lineTo(24, 8)
    p.lineTo(24, 15)
    p.curveTo(24, 20, 20.2, 23.6, 15, 25.5)
    p.curveTo(9.8, 23.6, 6, 20, 6, 15)
    p.lineTo(6, 8)
    p.close()
    c.drawPath(p, fill=0, stroke=1)
    c.setStrokeColor(MINT)
    c.setLineWidth(2.2)
    c.setLineCap(1)
    k = c.beginPath()
    k.moveTo(10.6, 15.2)
    k.lineTo(13.7, 18.2)
    k.lineTo(19.6, 11.8)
    c.drawPath(k, fill=0, stroke=1)
    c.restoreState()


# =========================================================
# CUSTOM FLOWABLES
# =========================================================

class Banner(Flowable):
    """Dark cover banner with the generated logo, title and a decorative chart."""

    def __init__(self, title, brand, seed, width=CONTENT_W, height=104):
        super().__init__()
        self.title, self.brand, self.seed = title, brand, seed
        self.width, self.height = width, height

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c, w, h = self.canv, self.width, self.height
        hh = _hash(f"{(self.brand or 'idea').lower()}|{self.seed}")
        bg, fg, soft = (colors.HexColor(v) for v in LOGO_PALETTES[hh % len(LOGO_PALETTES)])
        shift = (hh // 11) % 40

        c.saveState()
        p = c.beginPath()
        p.roundRect(0, 0, w, h, 16)
        c.clipPath(p, stroke=0, fill=0)

        c.setFillColor(INK)
        c.rect(0, 0, w, h, fill=1, stroke=0)
        try:
            c.linearGradient(0, h, w, 0, (INK, bg), extend=False)
        except Exception:
            pass

        # dot grid
        c.setFillColor(WHITE)
        c.setFillAlpha(0.13)
        for gx in range(8, int(w), 22):
            for gy in range(8, int(h), 22):
                c.circle(gx, gy, 1, fill=1, stroke=0)

        # soft circles
        c.setFillColor(fg)
        c.setFillAlpha(0.14)
        c.circle(w - 150 + shift, h - 6, 70, fill=1, stroke=0)
        c.setFillColor(soft)
        c.setFillAlpha(0.10)
        c.circle(w - 40 - shift, 4, 52, fill=1, stroke=0)

        # rising bars + trend line
        heights = [16, 26, 22, 36, 32, 50, 64]
        bx = w - 250 + shift
        c.setFillColor(soft)
        c.setFillAlpha(0.16)
        for i, v in enumerate(heights):
            c.roundRect(bx + i * 26, 0, 14, v, 4, fill=1, stroke=0)
        c.setFillAlpha(1)
        c.setStrokeColor(fg)
        c.setLineWidth(2)
        c.setLineCap(1)
        c.setLineJoin(1)
        line = c.beginPath()
        for i, v in enumerate(heights):
            px, py = bx + i * 26 + 7, v + 10
            line.moveTo(px, py) if i == 0 else line.lineTo(px, py)
        c.drawPath(line, fill=0, stroke=1)
        c.setFillColor(fg)
        c.circle(bx + 6 * 26 + 7, heights[-1] + 10, 3.6, fill=1, stroke=0)

        # logo + text
        draw_logo(c, 24, (h - 62) / 2.0, 62, self.brand, self.seed)
        text_x = 24 + 62 + 18
        max_w = w - text_x - 150
        title = _safe(self.title)
        size = _fit_font(title, "Helvetica-Bold", 23, max_w)
        title = _clip(title, "Helvetica-Bold", size, max_w)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", size)
        c.drawString(text_x, h / 2.0 + 2, title)
        c.setFillAlpha(0.8)
        c.setFont("Helvetica", 9.5)
        c.drawString(text_x, h / 2.0 - 16, "AI Startup Validator  |  Feasibility & risk report")
        c.setFont("Helvetica", 8.5)
        c.drawString(text_x, h / 2.0 - 30, datetime.date.today().strftime("%d %B %Y"))
        c.restoreState()


class SectionHeading(Flowable):
    """Heading with a gold marker."""

    def __init__(self, text, width=CONTENT_W):
        super().__init__()
        self.text, self.width = _safe(text), width
        self.spaceBefore, self.spaceAfter = 14, 6
        self.keepWithNext = True

    def wrap(self, aw, ah):
        return self.width, 22

    def draw(self):
        c = self.canv
        c.setFillColor(GOLD)
        c.roundRect(0, 3, 4, 16, 2, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 13.5)
        c.drawString(13, 6, self.text)


class VerdictPanel(Flowable):
    """Dark panel with a gauge for the survival score."""

    def __init__(self, status, succ, fail, width=CONTENT_W, height=118):
        super().__init__()
        self.status = _safe(str(status or "N/A")).upper()
        self.succ = max(0.0, min(100.0, _num(succ)))
        self.fail = max(0.0, min(100.0, _num(fail)))
        self.width, self.height = width, height

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c, w, h = self.canv, self.width, self.height
        if "SUCCESS" in self.status:
            good = True
        elif "FAIL" in self.status:
            good = False
        else:
            good = self.succ >= 50
        accent = MINT if good else CORAL

        c.saveState()
        c.setFillColor(INK)
        c.roundRect(0, 0, w, h, 16, fill=1, stroke=0)

        # gauge
        cx, cy, r = 110, 26, 66
        c.setLineCap(1)
        c.setLineWidth(11)
        c.setStrokeColor(WHITE)
        c.setStrokeAlpha(0.15)
        c.arc(cx - r, cy - r, cx + r, cy + r, 180, -180)
        c.setStrokeAlpha(1)
        if self.succ > 0:
            c.setStrokeColor(accent)
            c.arc(cx - r, cy - r, cx + r, cy + r, 180, -180 * self.succ / 100.0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(cx, cy + 8, f"{_pct(self.succ)}%")
        c.setFillColor(colors.HexColor("#A9B9BC"))
        c.setFont("Helvetica", 8.5)
        c.drawCentredString(cx, cy - 8, "chance of success")

        # verdict + stats
        x = 238
        c.setFillColor(colors.HexColor("#A9B9BC"))
        c.setFont("Helvetica", 9)
        c.drawString(x, h - 26, "Verdict")
        c.setFillColor(accent)
        size = _fit_font(self.status, "Helvetica-Bold", 22, w - x - 24, 12)
        c.setFont("Helvetica-Bold", size)
        c.drawString(x, h - 52, self.status)
        c.setStrokeColor(WHITE)
        c.setStrokeAlpha(0.16)
        c.setLineWidth(0.8)
        c.line(x, 56, w - 24, 56)
        c.setStrokeAlpha(1)
        for sx, val, lab in ((x, self.succ, "Success probability"), (x + 150, self.fail, "Failure risk")):
            c.setFillColor(WHITE)
            c.setFont("Helvetica-Bold", 18)
            c.drawString(sx, 30, f"{_pct(val)}%")
            c.setFillColor(colors.HexColor("#A9B9BC"))
            c.setFont("Helvetica", 8.5)
            c.drawString(sx, 16, lab)
        c.restoreState()


class RoadmapFlow(Flowable):
    """Roadmap flowchart drawn on a dark panel: one box per phase, joined by arrows."""

    PAD, GAP, FONT, SIZE = 20, 20, "Helvetica-Bold", 9.5

    def __init__(self, phases, width=CONTENT_W):
        super().__init__()
        self.width = width
        self.box_w = width - 60
        self.items = []
        for phase in phases:
            lines = simpleSplit(_safe(phase), self.FONT, self.SIZE, self.box_w - 52)
            if len(lines) > 2:
                lines = lines[:2]
                lines[1] = _clip(lines[1] + " ...", self.FONT, self.SIZE, self.box_w - 52)
            self.items.append((lines, max(36, 16 + 12 * len(lines))))

    def wrap(self, aw, ah):
        total = 2 * self.PAD + sum(h for _, h in self.items) + self.GAP * max(0, len(self.items) - 1)
        self.height = total
        return self.width, total

    def draw(self):
        c, w, total = self.canv, self.width, self.height
        c.saveState()
        c.setFillColor(INK)
        c.roundRect(0, 0, w, total, 16, fill=1, stroke=0)
        # glow (clipped to the panel so it never spills past the rounded corners)
        c.saveState()
        clip = c.beginPath()
        clip.roundRect(0, 0, w, total, 16)
        c.clipPath(clip, stroke=0, fill=0)
        c.setFillColor(GOLD)
        c.setFillAlpha(0.10)
        c.circle(w - 40, total - 10, 80, fill=1, stroke=0)
        c.restoreState()

        y = total - self.PAD
        bx = (w - self.box_w) / 2.0
        for i, (lines, bh) in enumerate(self.items):
            top, bottom = y, y - bh
            c.setFillColor(CREAM)
            c.setStrokeColor(GOLD)
            c.setLineWidth(1.2)
            c.roundRect(bx, bottom, self.box_w, bh, 9, fill=1, stroke=1)
            # number badge
            c.setFillColor(INK)
            c.circle(bx + 22, bottom + bh / 2.0, 10, fill=1, stroke=0)
            c.setFillColor(GOLD)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(bx + 22, bottom + bh / 2.0 - 3.5, str(i + 1))
            # text
            c.setFillColor(INK)
            c.setFont(self.FONT, self.SIZE)
            ty = bottom + bh / 2.0 + (len(lines) - 1) * 6 - 3.4
            for ln in lines:
                c.drawString(bx + 44, ty, ln)
                ty -= 12
            # arrow to next box
            if i < len(self.items) - 1:
                mx = w / 2.0
                c.setStrokeColor(colors.HexColor("#9FB4B0"))
                c.setLineWidth(1.6)
                c.line(mx, bottom, mx, bottom - self.GAP + 6)
                c.setFillColor(colors.HexColor("#9FB4B0"))
                a = c.beginPath()
                a.moveTo(mx - 5, bottom - self.GAP + 8)
                a.lineTo(mx + 5, bottom - self.GAP + 8)
                a.lineTo(mx, bottom - self.GAP + 1)
                a.close()
                c.drawPath(a, fill=1, stroke=0)
            y = bottom - self.GAP
        c.restoreState()


class Avatar(Flowable):
    """Small generated round avatar for a team role."""

    def __init__(self, label, size=24):
        super().__init__()
        self.label, self.size = label, size

    def wrap(self, aw, ah):
        return self.size, self.size

    def draw(self):
        c, s = self.canv, self.size
        h = _hash((self.label or "role").lower())
        bg, fg, soft = (colors.HexColor(v) for v in LOGO_PALETTES[h % len(LOGO_PALETTES)])
        c.setFillColor(bg)
        c.circle(s / 2.0, s / 2.0, s / 2.0, fill=1, stroke=0)
        c.setStrokeColor(fg)
        c.setLineWidth(1)
        c.circle(s / 2.0, s / 2.0, s / 2.0 - 1.6, fill=0, stroke=1)
        c.setFillColor(soft)
        c.setFont("Helvetica-Bold", s * 0.36)
        c.drawCentredString(s / 2.0, s / 2.0 - s * 0.13, _safe(_initials(self.label)))


def _footer(canv, doc):
    canv.saveState()
    canv.setStrokeColor(LINE)
    canv.setLineWidth(0.6)
    canv.line(36, 34, 576, 34)
    draw_brand_mark(canv, 36, 15, 14)
    canv.setFillColor(INK)
    canv.setFont("Helvetica-Bold", 8)
    canv.drawString(56, 19, "AI Startup Validator")
    canv.setFillColor(MUTED)
    canv.setFont("Helvetica", 8)
    canv.drawRightString(576, 19, f"Page {doc.page}")
    canv.restoreState()


# =========================================================
# REPORT
# =========================================================

def generate_pdf_report(startup_name, original_desc, concept_data, prediction_result, plan_data=None, logo_seed=0):
    """
    Generates the AI Startup Validator PDF report.
    `logo_seed` should match the app's logo shuffle so the PDF logo is the one on screen.
    """
    concept_data = concept_data or {}
    prediction_result = prediction_result or {}
    original_desc = original_desc or ""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=48,
        title="AI Startup Validator Report",
        author="AI Startup Validator",
    )

    styles = getSampleStyleSheet()
    body_style = ParagraphStyle("BodyStyle", parent=styles["Normal"], fontSize=9.2, leading=13.5, textColor=INK_2)
    bold_body = ParagraphStyle("BoldBody", parent=styles["Normal"], fontSize=9.2, leading=13.5, textColor=INK, fontName="Helvetica-Bold")
    label_style = ParagraphStyle("Label", parent=styles["Normal"], fontSize=8.5, leading=11, textColor=MUTED, fontName="Helvetica-Bold", spaceAfter=2)
    table_text = ParagraphStyle("TableText", parent=styles["Normal"], fontSize=8.6, leading=11.5, textColor=INK_2)
    th_style = ParagraphStyle("TH", parent=styles["Normal"], fontSize=8.8, leading=11, textColor=WHITE, fontName="Helvetica-Bold")
    note_style = ParagraphStyle("Note", parent=table_text, textColor=MUTED, fontName="Helvetica-Oblique")

    v_name = startup_name.strip() if startup_name and startup_name.strip() else "Startup Validation Report"
    brand = startup_name.strip() if startup_name and startup_name.strip() else (" ".join(original_desc.split()[:2]) or "Idea")

    story = [Banner(v_name, brand, logo_seed), Spacer(1, 4)]

    # 1. Concept ---------------------------------------------------------
    story.append(SectionHeading("1. Startup Concept & Decomposition"))
    story.append(Paragraph("YOUR PITCH", label_style))
    story.append(Paragraph(escape(original_desc), body_style))
    story.append(Spacer(1, 8))

    sharp = Table(
        [[[Paragraph("SHARPER VERSION", label_style),
           Paragraph(escape(concept_data.get("enhanced_description", "")), body_style)]]],
        colWidths=[CONTENT_W],
    )
    sharp.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM_SOFT),
        ("LINEBEFORE", (0, 0), (0, -1), 3, GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.append(sharp)
    story.append(Spacer(1, 10))

    problems = [Paragraph("PROBLEMS ADDRESSED", label_style)] + [
        Paragraph(f"&bull; {escape(p)}", body_style) for p in concept_data.get("problems_identified", [])
    ]
    users = [Paragraph("TARGET USERS", label_style)] + [
        Paragraph(f"&bull; {escape(u)}", body_style) for u in concept_data.get("target_users", [])
    ]
    cols = Table([[problems, users]], colWidths=[CONTENT_W / 2.0, CONTENT_W / 2.0])
    cols.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 14),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    story.append(cols)

    # 2. Verdict ---------------------------------------------------------
    story.append(SectionHeading("2. Machine Learning Viability Assessment"))
    story.append(VerdictPanel(
        prediction_result.get("status", "N/A"),
        prediction_result.get("success_probability", 0),
        prediction_result.get("failure_probability", 0),
    ))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "Note: This prediction is based on patterns learned from historical startup datasets and should be "
        "treated as an analytical risk indicator, not a real-world guarantee.",
        note_style,
    ))

    # 3. Risks -----------------------------------------------------------
    story.append(SectionHeading("3. Major Risk Factors (Synthesized Intelligence)"))
    for idx, r in enumerate(concept_data.get("major_risks", []), 1):
        card = Table(
            [[[Paragraph(f"{idx}. {escape(str(r.get('title', 'Risk')))}", bold_body),
               Spacer(1, 2),
               Paragraph(escape(str(r.get("explanation", ""))), body_style)]]],
            colWidths=[CONTENT_W],
        )
        card.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PAPER),
            ("LINEBEFORE", (0, 0), (0, -1), 3, RISK),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ]))
        story.append(card)
        story.append(Spacer(1, 6))

    # Plan sections ------------------------------------------------------
    if plan_data:
        story.append(SectionHeading("4. Recommended Concept Improvements"))
        imp_data = [[Paragraph("Your idea now", th_style), Paragraph("Upgrade", th_style), Paragraph("Why it helps", th_style)]]
        for imp in plan_data.get("improvements", []):
            imp_data.append([
                Paragraph(escape(str(imp.get("current", ""))), table_text),
                Paragraph(escape(str(imp.get("suggested", ""))), table_text),
                Paragraph(escape(str(imp.get("rationale", ""))), table_text),
            ])
        t_imp = Table(imp_data, colWidths=[160, 180, 200], repeatRows=1)
        t_imp.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INK),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PAPER]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
            ("BOX", (0, 0), (-1, -1), 0.5, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t_imp)

        # Roadmap + flowchart
        stages = plan_data.get("roadmap_stages", [])
        story.append(SectionHeading("5. Execution Roadmap"))
        if stages:
            story.append(RoadmapFlow([s.get("phase", "") for s in stages]))
            story.append(Spacer(1, 10))
        for stage in stages:
            story.append(Paragraph(escape(str(stage.get("phase", ""))), bold_body))
            story.append(Paragraph(escape(str(stage.get("details", ""))), body_style))
            story.append(Spacer(1, 5))

        # Skills & team
        story.append(SectionHeading("6. Required Skills & Team Architecture"))
        skill_data = [[Paragraph("Key skill / capability", th_style), Paragraph("Why it is needed", th_style)]]
        for sk in plan_data.get("required_skills", []):
            skill_data.append([
                Paragraph(f"<b>{escape(str(sk.get('skill', '')))}</b>", table_text),
                Paragraph(escape(str(sk.get("purpose", ""))), table_text),
            ])
        t_sk = Table(skill_data, colWidths=[180, 360], repeatRows=1)
        t_sk.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INK),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PAPER]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
            ("BOX", (0, 0), (-1, -1), 0.5, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t_sk)
        story.append(Spacer(1, 12))

        team = plan_data.get("recommended_team", [])
        if team:
            story.append(Paragraph("Recommended initial team", bold_body))
            story.append(Spacer(1, 4))
            rows = []
            for tm in team:
                role = str(tm.get("role", ""))
                rows.append([
                    Avatar(role),
                    Paragraph(
                        f"<b>{escape(role)} (x{escape(str(tm.get('count', 1)))})</b><br/>"
                        f"{escape(str(tm.get('description', '')))}",
                        table_text,
                    ),
                ])
            t_team = Table(rows, colWidths=[36, CONTENT_W - 36])
            t_team.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
                ("LEFTPADDING", (0, 0), (0, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            story.append(t_team)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return buffer
