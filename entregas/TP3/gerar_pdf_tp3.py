"""
Gera o PDF do relatório do TP3 a partir de relatorio_tp3.md.

Uso (a partir de qualquer pasta):
    python entregas/TP3/gerar_pdf_tp3.py
    python entregas/TP3/gerar_pdf_tp3.py --output maite_silva_PB_TP3.pdf

Requer: reportlab (já listado em eda/requirements.txt).

Markdown suportado: títulos (#, ##, ###), parágrafos com **negrito**, *itálico*, `código`
e [links](url), listas com "- " e "1. ", tabelas, imagens ![legenda](caminho), blocos de
código, citações "> " (caixa destacada, usada nas seções a preencher), e os marcadores
<!-- pagebreak --> (quebra de página) e <!-- toc --> (sumário).

O marcador {{data}} é substituído pela data do dia em que o script é executado.
"""

import argparse
import html
import re
from datetime import date
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
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "relatorio_tp3.md"

LARGURA_UTIL = A4[0] - 4 * cm
AZUL = colors.HexColor("#1F3A5F")
CINZA_CLARO = colors.HexColor("#F2F2F2")
AMARELO_CLARO = colors.HexColor("#FFF8E1")


def registrar_fontes() -> tuple[str, str, str]:
    fontes = Path(r"C:\Windows\Fonts")
    if (fontes / "arial.ttf").exists():
        pdfmetrics.registerFont(TTFont("Arial", str(fontes / "arial.ttf")))
        pdfmetrics.registerFont(TTFont("Arial-Bold", str(fontes / "arialbd.ttf")))
        pdfmetrics.registerFont(TTFont("Arial-Italic", str(fontes / "ariali.ttf")))
        pdfmetrics.registerFont(TTFont("Arial-BoldItalic", str(fontes / "arialbi.ttf")))
        pdfmetrics.registerFontFamily(
            "Arial",
            normal="Arial",
            bold="Arial-Bold",
            italic="Arial-Italic",
            boldItalic="Arial-BoldItalic",
        )
        return "Arial", "Arial-Bold", "Arial-Italic"
    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


FONTE, FONTE_NEGRITO, FONTE_ITALICO = registrar_fontes()

styles = getSampleStyleSheet()
ESTILOS = {
    "capa_titulo": ParagraphStyle(
        "capa_titulo",
        fontName=FONTE_NEGRITO,
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=AZUL,
        spaceAfter=10,
    ),
    "capa_subtitulo": ParagraphStyle(
        "capa_subtitulo",
        fontName=FONTE_NEGRITO,
        fontSize=15,
        leading=20,
        alignment=TA_CENTER,
        spaceAfter=40,
    ),
    "capa_info": ParagraphStyle(
        "capa_info",
        fontName=FONTE,
        fontSize=11,
        leading=16,
        alignment=TA_CENTER,
        spaceAfter=8,
    ),
    "h1": ParagraphStyle(
        "h1",
        keepWithNext=1,
        fontName=FONTE_NEGRITO,
        fontSize=16,
        leading=20,
        textColor=AZUL,
        spaceBefore=26,
        spaceAfter=12,
    ),
    "h2": ParagraphStyle(
        "h2",
        keepWithNext=1,
        fontName=FONTE_NEGRITO,
        fontSize=13,
        leading=17,
        textColor=AZUL,
        spaceBefore=20,
        spaceAfter=9,
    ),
    "h3": ParagraphStyle(
        "h3",
        keepWithNext=1,
        fontName=FONTE_NEGRITO,
        fontSize=11,
        leading=15,
        spaceBefore=14,
        spaceAfter=7,
    ),
    "corpo": ParagraphStyle(
        "corpo", fontName=FONTE, fontSize=10, leading=15, spaceAfter=9
    ),
    "celula": ParagraphStyle("celula", fontName=FONTE, fontSize=8.5, leading=11),
    "celula_cab": ParagraphStyle(
        "celula_cab",
        fontName=FONTE_NEGRITO,
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    ),
    "legenda": ParagraphStyle(
        "legenda",
        fontName=FONTE_ITALICO,
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
        spaceAfter=22,
    ),
    "destaque": ParagraphStyle(
        "destaque", fontName=FONTE, fontSize=9.5, leading=13, spaceAfter=3
    ),
    "codigo": ParagraphStyle(
        "codigo",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7.5,
        leading=10,
        backColor=CINZA_CLARO,
        borderPadding=6,
        spaceBefore=8,
        spaceAfter=16,
    ),
    "toc_titulo": ParagraphStyle(
        "toc_titulo",
        fontName=FONTE_NEGRITO,
        fontSize=16,
        leading=20,
        textColor=AZUL,
        spaceAfter=12,
    ),
}


def inline(texto: str) -> str:
    """Converte a marcação inline do Markdown para a marcação do reportlab"""

    texto = html.escape(texto, quote=False)
    texto = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<link href="{m.group(2)}" color="#1F5FAF">{m.group(1)}</link>',
        texto,
    )
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    texto = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", texto)
    texto = re.sub(
        r"`([^`]+)`",
        r'<font name="Courier" size="8.5" backColor="#EEEEEE">\1</font>',
        texto,
    )
    return texto


class Documento(SimpleDocTemplate):
    """Registra os títulos no sumário à medida que as páginas são montadas"""

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in ("h1", "h2"):
            nivel = 0 if flowable.style.name == "h1" else 1
            texto = flowable.getPlainText()
            chave = f"secao-{id(flowable)}"
            self.canv.bookmarkPage(chave)
            self.canv.addOutlineEntry(texto, chave, level=nivel)
            self.notify("TOCEntry", (nivel, texto, self.page, chave))


def rodape(canvas, doc):
    if doc.page == 1:
        return
    canvas.saveState()
    canvas.setFont(FONTE, 8)
    canvas.setFillColor(colors.HexColor("#777777"))
    canvas.drawString(2 * cm, 1.2 * cm, "EduBot Analytics - Relatório TP3")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.restoreState()


def tabela(linhas: list[str]) -> Table:
    celulas = [
        [c.strip() for c in linha.strip().strip("|").split("|")]
        for linha in linhas
        if not re.match(r"^\|?\s*:?-{3,}", linha.strip())
    ]
    colunas = max(len(l) for l in celulas)
    celulas = [l + [""] * (colunas - len(l)) for l in celulas]

    # Cada coluna recebe primeiro a largura da sua maior palavra (para não quebrar
    # palavras) e o espaço que sobra é dividido conforme o tamanho do texto
    def texto_puro(texto: str) -> str:
        return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", re.sub(r"[*`]", "", texto))

    def largura_palavra(texto: str, negrito: bool) -> float:
        fonte = FONTE_NEGRITO if negrito else FONTE
        palavras = texto_puro(texto).split() or [""]
        return max(pdfmetrics.stringWidth(p, fonte, 8.5) for p in palavras)

    minimos = [
        max(largura_palavra(l[c], i == 0) for i, l in enumerate(celulas)) + 10
        for c in range(colunas)
    ]
    tamanhos = [
        min(max(len(texto_puro(l[c])) for l in celulas), 60) for c in range(colunas)
    ]
    sobra = max(LARGURA_UTIL - sum(minimos), 0)
    larguras = [m + sobra * t / sum(tamanhos) for m, t in zip(minimos, tamanhos)]
    if sum(minimos) > LARGURA_UTIL:
        larguras = [LARGURA_UTIL * m / sum(minimos) for m in minimos]

    dados = [
        [
            Paragraph(inline(c), ESTILOS["celula_cab" if i == 0 else "celula"])
            for c in linha
        ]
        for i, linha in enumerate(celulas)
    ]
    t = Table(dados, colWidths=larguras, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), AZUL),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return t


def imagem(legenda: str, caminho: str) -> KeepTogether:
    arquivo = (ROOT / caminho).resolve()
    if not arquivo.exists():
        raise FileNotFoundError(f"Imagem não encontrada: {arquivo}")
    img = Image(str(arquivo))
    img._restrictSize(LARGURA_UTIL, 11 * cm)
    return KeepTogether(
        [
            Spacer(1, 10),
            img,
            Spacer(1, 6),
            Paragraph(inline(legenda), ESTILOS["legenda"]),
        ]
    )


def caixa_destaque(linhas: list[str]) -> Table:
    conteudo = [Paragraph(inline(l), ESTILOS["destaque"]) for l in linhas]
    t = Table([[conteudo]], colWidths=[LARGURA_UTIL])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), AMARELO_CLARO),
                ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#F2B705")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return t


def lista(itens: list[str], numerada: bool) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(inline(i), ESTILOS["corpo"]), leftIndent=14) for i in itens],
        bulletType="1" if numerada else "bullet",
        bulletFormat="%s." if numerada else None,
        bulletFontName=FONTE,
        bulletFontSize=9,
        leftIndent=14,
    )


def montar_story() -> list:
    texto = SOURCE.read_text(encoding="utf-8")
    texto = texto.replace("{{data}}", date.today().strftime("%d/%m/%Y"))
    linhas = texto.splitlines()
    story = []
    capa = True  # tudo antes da primeira quebra de página é a capa
    i = 0

    while i < len(linhas):
        linha = linhas[i]
        limpa = linha.strip()

        if limpa == "<!-- pagebreak -->":
            story.append(PageBreak())
            capa = False
            i += 1
            continue

        if limpa == "<!-- toc -->":
            toc = TableOfContents()
            toc.levelStyles = [
                ParagraphStyle("toc1", fontName=FONTE_NEGRITO, fontSize=10.5, leading=16, leftIndent=0),
                ParagraphStyle("toc2", fontName=FONTE, fontSize=9.5, leading=14, leftIndent=16),
            ]
            story += [Paragraph("Sumário", ESTILOS["toc_titulo"]), toc]
            i += 1
            continue

        if not limpa:
            i += 1
            continue

        if limpa.startswith("```"):
            bloco = []
            i += 1
            while i < len(linhas) and not linhas[i].strip().startswith("```"):
                bloco.append(linhas[i])
                i += 1
            story.append(Preformatted("\n".join(bloco), ESTILOS["codigo"]))
            i += 1
            continue

        if limpa.startswith("|"):
            bloco = []
            while i < len(linhas) and linhas[i].strip().startswith("|"):
                bloco.append(linhas[i])
                i += 1
            story += [Spacer(1, 4), tabela(bloco), Spacer(1, 16)]
            continue

        if limpa.startswith(">"):
            bloco = []
            while i < len(linhas) and linhas[i].strip().startswith(">"):
                bloco.append(linhas[i].strip()[1:].strip())
                i += 1
            story += [caixa_destaque(bloco), Spacer(1, 16)]
            continue

        if re.match(r"^(- |\d+\. )", limpa):
            numerada = bool(re.match(r"^\d+\. ", limpa))
            itens = []
            while i < len(linhas) and re.match(r"^(- |\d+\. )", linhas[i].strip()):
                itens.append(re.sub(r"^(- |\d+\. )", "", linhas[i].strip()))
                i += 1
            story += [lista(itens, numerada), Spacer(1, 10)]
            continue

        figura = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", limpa)
        if figura:
            story.append(imagem(figura.group(1), figura.group(2)))
            i += 1
            continue

        if capa:
            if limpa.startswith("# "):
                story += [Spacer(1, 5 * cm), Paragraph(inline(limpa[2:]), ESTILOS["capa_titulo"])]
            elif limpa.startswith("## "):
                story.append(Paragraph(inline(limpa[3:]), ESTILOS["capa_subtitulo"]))
            else:
                story.append(Paragraph(inline(limpa), ESTILOS["capa_info"]))
        elif limpa.startswith("### "):
            story.append(Paragraph(inline(limpa[4:]), ESTILOS["h3"]))
        elif limpa.startswith("## "):
            story.append(Paragraph(inline(limpa[3:]), ESTILOS["h2"]))
        elif limpa.startswith("# "):
            story.append(Paragraph(inline(limpa[2:]), ESTILOS["h1"]))
        else:
            story.append(Paragraph(inline(limpa), ESTILOS["corpo"]))
        i += 1

    return story


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="patricia_rodrigues_PB_TP3.pdf",
        help="nome do PDF gerado dentro da pasta entregas/TP3",
    )
    args = parser.parse_args()
    output = ROOT / args.output

    documento = Documento(
        str(output),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="EduBot Analytics - Relatório TP3",
        author="Maitê Mota Belo de Souza Silva e Patricia Dias Rodrigues",
    )
    documento.multiBuild(montar_story(), onFirstPage=rodape, onLaterPages=rodape)
    print(f"PDF gerado em {output}")


if __name__ == "__main__":
    main()
