"""
Gera as imagens PNG dos diagramas Mermaid de um arquivo Markdown (por padrão, dfd/dfd.md).

Usa o Microsoft Edge em modo headless (já vem no Windows) para renderizar cada bloco
```mermaid``` com a biblioteca Mermaid 10.9.1 e recorta as bordas em branco.

Uso (a partir da raiz do repositório):
    python dfd/gerar_imagens.py
    python dfd/gerar_imagens.py dfd/dfd.md dfd/dfd-v3-requisicao.png dfd/dfd-v3-cicd.png
"""

import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"
PADRAO = ["dfd/dfd.md", "dfd/dfd-v3-requisicao.png", "dfd/dfd-v3-cicd.png"]

PAGINA = """<!doctype html><html><head><meta charset="utf-8">
<script src="{cdn}"></script>
<style>body{{margin:0;background:#fff;font-family:Arial}} #d{{display:inline-block;padding:24px}}</style>
</head><body><div id="d"><pre class="mermaid">{diagrama}</pre></div>
<script>mermaid.initialize({{startOnLoad: true, theme: "default",
  flowchart: {{htmlLabels: true, curve: "basis", useMaxWidth: false}},
  themeVariables: {{fontSize: "16px"}}}});</script>
</body></html>"""


def renderizar(diagrama: str, destino: Path, pasta_temp: Path) -> None:
    pagina = pasta_temp / "diagrama.html"
    captura = pasta_temp / "captura.png"
    pagina.write_text(
        PAGINA.format(cdn=MERMAID_CDN, diagrama=html.escape(diagrama)), encoding="utf-8"
    )
    subprocess.run(
        [
            EDGE,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=2",
            "--window-size=3600,2400",
            "--virtual-time-budget=15000",
            f"--screenshot={captura}",
            pagina.as_uri(),
        ],
        check=True,
        capture_output=True,
        timeout=120,
    )
    imagem = Image.open(captura).convert("RGB")
    fundo = Image.new("RGB", imagem.size, "white")
    esquerda, topo, direita, baixo = ImageChops.difference(imagem, fundo).getbbox()
    margem = 30
    imagem.crop(
        (
            max(esquerda - margem, 0),
            max(topo - margem, 0),
            min(direita + margem, imagem.width),
            min(baixo + margem, imagem.height),
        )
    ).save(destino, optimize=True)
    print(f"{destino} gerado")


def main() -> None:
    markdown, *destinos = sys.argv[1:] or PADRAO
    blocos = re.findall(r"```mermaid\n(.*?)```", Path(markdown).read_text("utf-8"), re.S)
    if len(blocos) != len(destinos):
        sys.exit(f"{markdown} tem {len(blocos)} diagramas, mas {len(destinos)} destinos")
    with tempfile.TemporaryDirectory() as pasta_temp:
        for bloco, destino in zip(blocos, destinos):
            renderizar(bloco, Path(destino), Path(pasta_temp))


if __name__ == "__main__":
    main()
