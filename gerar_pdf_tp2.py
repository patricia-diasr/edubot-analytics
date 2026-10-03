import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "relatorio_tp2.md"
OUTPUT = ROOT / "maite_silva_PB_TP2.pdf"

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="TitleArial",
        parent=styles["Title"],
        fontName="Arial-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=16,
    )
)
styles.add(
    ParagraphStyle(
        name="Heading1Arial",
        parent=styles["Heading1"],
        fontName="Arial-Bold",
        fontSize=15,
        leading=19,
        spaceBefore=12,
        spaceAfter=7,
    )
)
styles.add(
    ParagraphStyle(
        name="Heading2Arial",
        parent=styles["Heading2"],
        fontName="Arial-Bold",
        fontSize=12,
        leading=15,
        spaceBefore=9,
        spaceAfter=5,
    )
)
styles.add(
    ParagraphStyle(
        name="BodyArial",
        parent=styles["BodyText"],
        fontName="Arial",
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )
)
styles.add(
    ParagraphStyle(
        name="CodeArial",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        backColor=colors.HexColor("#F2F2F2"),
        borderPadding=6,
    )
)


def inline_markup(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"`(.+?)`", r'<font name="Courier">\1</font>', escaped)
    return escaped


def build_story():
    story = []
    bullets = []
    code_lines = []
    in_code = False

    def flush_bullets():
        nonlocal bullets
        if bullets:
            story.append(
                ListFlowable(
                    [
                        ListItem(Paragraph(item, styles["BodyArial"]))
                        for item in bullets
                    ],
                    bulletType="bullet",
                    leftIndent=18,
                )
            )
            story.append(Spacer(1, 4))
            bullets = []

    for raw_line in SOURCE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if line.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), styles["CodeArial"]))
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(raw_line)
            continue

        if not line:
            flush_bullets()
            continue
        if line.startswith("- "):
            bullets.append(inline_markup(line[2:]))
            continue

        flush_bullets()
        if line.startswith("# "):
            story.append(Paragraph(inline_markup(line[2:]), styles["TitleArial"]))
        elif line.startswith("## "):
            story.append(Paragraph(inline_markup(line[3:]), styles["Heading1Arial"]))
        elif line.startswith("### "):
            story.append(Paragraph(inline_markup(line[4:]), styles["Heading2Arial"]))
        elif re.match(r"^\d+\.\s", line):
            story.append(Paragraph(inline_markup(line), styles["BodyArial"]))
        else:
            story.append(Paragraph(inline_markup(line), styles["BodyArial"]))

    flush_bullets()
    story.append(PageBreak())
    story.append(Paragraph("Figuras da EDA", styles["Heading1Arial"]))

    figures = [
        (
            "Heatmap de correlação",
            ROOT / "eda" / "figures" / "fig7_heatmap_correlacao.png",
        ),
        (
            "Comprimento por categoria",
            ROOT / "eda" / "figures" / "fig8_scatter_comprimento.png",
        ),
        ("Comprimento e ruído", ROOT / "eda" / "figures" / "fig9_scatter_ruido.png"),
    ]
    for caption, path in figures:
        story.append(Paragraph(caption, styles["Heading2Arial"]))
        image = Image(str(path))
        image._restrictSize(17 * cm, 10.5 * cm)
        story.append(image)
        story.append(Spacer(1, 10))

    return story


document = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    rightMargin=2 * cm,
    leftMargin=2 * cm,
    topMargin=1.8 * cm,
    bottomMargin=1.8 * cm,
    title="EduBot Analytics - TP2",
    author="Maitê Mota Belo de Souza Silva e Patricia Dias Rodrigues",
)
document.build(build_story())
print(f"PDF gerado em {OUTPUT}")
