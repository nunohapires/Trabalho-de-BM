"""Gráfico e relatórios derivados do mesmo conjunto de entradas e resultados."""

from dataclasses import asdict
from io import BytesIO
from xml.sax.saxutils import escape

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image, LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, TableStyle,
)

from bm import (
    CARD_NOTE, INPUT_LABELS, MODEL_NOTE, REFERENCES, RESULT_LABELS, ProjectInputs, PumpTag,
    approximate_dynamometer, capacity_checks, operating_warnings,
)


def format_number(value: float, decimals: int = 1) -> str:
    """Apresentação pt-BR sem alterar locale global do processo Streamlit."""
    return f"{value:,.{decimals}f}".translate(str.maketrans(",.", ".,"))


def input_table(p: ProjectInputs) -> pd.DataFrame:
    return pd.DataFrame([
        {"Parâmetro": INPUT_LABELS[key][0], "Valor": value, "Unidade": INPUT_LABELS[key][1]}
        for key, value in asdict(p).items()
    ])


def result_table(results: dict[str, float]) -> pd.DataFrame:
    return pd.DataFrame([
        {"Parâmetro": label, "Símbolo": symbol, "Valor": results[key], "Unidade": unit}
        for key, (label, symbol, unit) in RESULT_LABELS.items()
    ])


def dynamometer_figure(r: dict[str, float], *, p: ProjectInputs | None = None,
                       dark: bool = False, load_capacity: float | None = None) -> Figure:
    """Compara a envoltória ideal com um ciclo elástico/inercial aproximado."""
    background = "#000000" if dark else "#ffffff"
    foreground = "#f1f5f9" if dark else "#172b3a"
    accent = "#2dd4bf" if dark else "#0f766e"
    estimated = "#fbbf24" if dark else "#b45309"
    grid_color = "#27272a" if dark else "#e2e8f0"
    fig = Figure(figsize=(9, 4.5), layout="constrained", facecolor=background)
    FigureCanvasAgg(fig)
    ax = fig.subplots()
    ax.set_facecolor(background)
    ax.tick_params(colors=foreground)
    ax.xaxis.label.set_color(foreground)
    ax.yaxis.label.set_color(foreground)
    stroke, low, high = r["surface_stroke"], r["min_load"], r["peak_load"]
    x, y = [0, 0, stroke, stroke, 0], [low, high, high, low, low]
    ax.fill(x, y, color=accent, alpha=0.10)
    ax.plot(x, y, color=accent, linewidth=1.8, linestyle="--", label="Ideal · envoltória")
    points = []
    if p is not None:
        try:
            points = approximate_dynamometer(p, r)
        except ValueError:
            ax.text(.5, .5, "Aproximação indisponível\nAlongamento elástico ≥ curso S",
                    transform=ax.transAxes, ha="center", color=foreground, fontsize=9)
    if points:
        positions, loads = zip(*points)
        ax.plot(positions, loads, color=estimated, linewidth=2.8, label="Aproximada · elasticidade + inércia")
        for index, label, offset in [(180, "Subida →", 18), (540, "← Descida", -24)]:
            ax.annotate(label, points[index], xytext=(0, offset), textcoords="offset points",
                        ha="center", color=estimated, fontsize=10)
            ax.annotate("", xy=points[index+20], xytext=points[index],
                        arrowprops={"arrowstyle": "->", "color": estimated, "lw": 2.5})
    ax.set(xlabel="Deslocamento da haste polida (in)", ylabel="Carga (lbf)")
    ax.set_xlim(-stroke * 0.05, stroke * 1.08)
    span = max(high - low, 1)
    ax.set_ylim(min(0, low - span * 0.12, min((v for _, v in points), default=low) - span*.12),
                max(high, load_capacity or high, max((v for _, v in points), default=high)) * 1.16)
    if low < 0:
        ax.axhline(0, color="#b45309", linestyle="--", linewidth=1)
    ax.annotate(f"PPRL  {format_number(high, 0)} lbf", (stroke * 0.02, high),
                xytext=(0, 10), textcoords="offset points", ha="left", color=accent)
    ax.annotate(f"MPRL  {format_number(low, 0)} lbf", (stroke * 0.02, low),
                xytext=(0, -18), textcoords="offset points", ha="left", color=foreground)
    if load_capacity is not None:
        ax.axhline(load_capacity, color="#f87171" if dark else "#b91c1c", linestyle="--", linewidth=1.3)
        ax.text(stroke*.02, load_capacity, f"Capacidade da unidade · {format_number(load_capacity, 0)} lbf",
                color="#f87171" if dark else "#b91c1c", fontsize=9, va="bottom")
    ax.grid(axis="y", color=grid_color, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.01), ncol=2,
              frameon=False, labelcolor=foreground, fontsize=9)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(grid_color)
    ax.spines["left"].set_color(grid_color)
    return fig


def chart_png(results: dict[str, float], p: ProjectInputs | None = None, load_capacity: float | None = None) -> bytes:
    buffer = BytesIO()
    dynamometer_figure(results, p=p, load_capacity=load_capacity).savefig(buffer, format="png", dpi=160)
    return buffer.getvalue()


def export_excel(p: ProjectInputs, tag: PumpTag, r: dict[str, float]) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter", engine_kwargs={"options": {"strings_to_formulas": False, "strings_to_urls": False}}) as writer:
        sheets = {
            "Entradas": input_table(p),
            "Resultados": result_table(r),
            "Capacidades": pd.DataFrame(capacity_checks(tag, r)),
            "Método": pd.DataFrame({"Informação": [
                f"TAG avaliada: {tag.code}", MODEL_NOTE,
                "Carta idealizada de superfície: usa S, PPRL e MPRL; não é uma carta medida.", CARD_NOTE,
                *operating_warnings(p, r), *[f"{label}: {url}" for label, url in REFERENCES],
            ]}),
        }
        try:
            sheets["Pontos da carta"] = pd.DataFrame(approximate_dynamometer(p, r), columns=["Deslocamento (in)", "Carga aproximada (lbf)"])
        except ValueError as error:
            sheets["Método"].loc[len(sheets["Método"])] = str(error)
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, index=False)
            sheet = writer.sheets[name]
            sheet.freeze_panes(1, 0)
            sheet.autofilter(0, 0, len(frame), len(frame.columns) - 1)
            header = writer.book.add_format({"bold": True, "bg_color": "#0F766E", "font_color": "white"})
            for column, label in enumerate(frame.columns):
                sheet.write(0, column, label, header)
                sheet.set_column(column, column, 52 if column == 0 else 22)
        method = writer.sheets["Método"]
        method.set_column(0, 0, 110, writer.book.add_format({"text_wrap": True}))
        for row in range(1, len(sheets["Método"]) + 1):
            method.set_row(row, 65)
        chart = writer.book.add_worksheet("Cartas de superfície")
        chart.insert_image("B2", "carta.png", {"image_data": BytesIO(chart_png(r, p, tag.load_capacity)), "x_scale": 0.65, "y_scale": 0.65})
    return buffer.getvalue()


def export_pdf(p: ProjectInputs, tag: PumpTag, r: dict[str, float]) -> bytes:
    """Tabelas com quebra automática, cabeçalhos repetidos e todas as entradas."""
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5 * cm,
                                 leftMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.7 * cm)
    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#115e59")
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 13
    story = [Paragraph("Projeto BM | Relatório de dimensionamento", styles["Title"]),
             Paragraph(f"Unidade convencional · TAG {tag.code}", styles["BodyText"]), Spacer(1, 12)]

    def add_table(title, headings, rows, widths):
        story.append(Paragraph(title, styles["Heading2"]))
        data = [[Paragraph(escape(str(cell)), styles["BodyText"]) for cell in row] for row in [headings, *rows]]
        table = LongTable(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ccfbf1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(table)

    checks = capacity_checks(tag, r)
    add_table("Capacidade da unidade", ["Critério", "Demanda", "Capacidade", "Situação"], [
        [row["Critério"], f'{format_number(row["Demanda"], 2)} {row["Unidade"]}',
         f'{format_number(row["Capacidade"], 2)} {row["Unidade"]}', "Atende" if row["Atende"] else "Excedida"]
        for row in checks
    ], [5 * cm, 4.5 * cm, 4.5 * cm, 4 * cm])
    for warning in operating_warnings(p, r):
        story.append(Paragraph(escape(warning), styles["BodyText"]))
    story.append(Paragraph(MODEL_NOTE, styles["BodyText"]))
    story.append(PageBreak())
    entries = input_table(p).copy()
    entries["Valor"] = entries["Valor"].map(lambda value: ("Sim" if value else "Não") if isinstance(value, bool) else format_number(value, 4))
    add_table("Dados de entrada", list(entries.columns), entries.values.tolist(), [10 * cm, 4 * cm, 4 * cm])
    story.append(PageBreak())
    rows = [[label, format_number(r[key], 4), unit] for key, (label, _, unit) in RESULT_LABELS.items()]
    add_table("Memória de cálculo · Resultados", ["Parâmetro", "Valor", "Unidade"], rows, [10 * cm, 4 * cm, 4 * cm])
    story.append(PageBreak())
    story.extend([
        Paragraph("Cartas dinamométricas de superfície", styles["Heading2"]),
        Image(BytesIO(chart_png(r, p, tag.load_capacity)), width=18 * cm, height=9 * cm),
        Paragraph("Ideal: envoltória retangular com S, PPRL e MPRL. " + CARD_NOTE, styles["BodyText"]),
        Spacer(1, 16), Paragraph("Referências", styles["Heading2"]),
    ])
    for label, url in REFERENCES:
        story.append(Paragraph(f'{escape(label)}<br/><link href="{escape(url)}" color="#0f766e">{escape(url)}</link>', styles["BodyText"]))

    def footer(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(1.5 * cm, 0.9 * cm, "Projeto BM · Nuno Henrique Albuquerque Pires · UFAL")
        canvas.drawRightString(A4[0] - 1.5 * cm, 0.9 * cm, f"Página {doc.page}")

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
