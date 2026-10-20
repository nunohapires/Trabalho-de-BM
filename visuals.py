"""Ilustração didática, origem dos dados e leitura do dimensionamento."""

from dataclasses import asdict
from html import escape
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from bm import INPUT_LABELS, ProjectInputs
from reports import format_number


DIAGRAM = Path(__file__).resolve().parent / "assets" / "pumping_system.html"

# Fontes sugeridas para preencher o projeto; não são medições importadas.
DATA_SOURCES = (
    ("Poço e fluido", "Registros de completação, teste de nível e pressão, análise do óleo e estudo PVT.",
     ("depth", "fluid_level", "wellhead_pressure", "oil_api", "volume_factor")),
    ("Unidade e geometria", "Placa da unidade e desenho dimensional do fabricante. A TAG fornece capacidades; as dimensões são informadas separadamente.",
     ("crank_radius", "pitman_length", "beam_rear", "beam_front")),
    ("Hastes, bomba e tubulação", "Folhas de especificação da bomba, das hastes e da tubulação; registro de ancoragem.",
     ("rod_diameter", "plunger_diameter", "steel_weight", "tubing_od", "tubing_id", "anchored_tubing", "elastic_modulus", "tensile_strength")),
    ("Critérios de operação", "Velocidade de operação, eficiência estimada e critérios definidos para o estudo conforme material e ambiente.",
     ("speed", "use_limit_speed", "acceleration_limit", "efficiency", "service_factor", "motor_factor")),
)


def system_html(p: ProjectInputs, r: dict[str, float]) -> str:
    payload = json.dumps({"inputs": asdict(p), "results": r}, allow_nan=False).replace("<", "\\u003c")
    motion = DIAGRAM.with_name("pump_motion.js").read_text(encoding="utf-8")
    return DIAGRAM.read_text(encoding="utf-8").replace("__BM_DATA__", payload).replace("__BM_MOTION__", motion)


def show_system(p, r):
    st.iframe(system_html(p, r), height="content", alt="Animação didática de bombeio mecânico com peças selecionáveis e dados do projeto")
    st.caption("A cadência e os valores exibidos vêm do projeto. A geometria é ilustrativa e a bomba ampliada mostra um ciclo ideal; gás, pressões e falhas de válvulas não são simulados.")


def data_sources_table(p: ProjectInputs) -> pd.DataFrame:
    rows = []
    for group, source, keys in DATA_SOURCES:
        for key in keys:
            value = getattr(p, key)
            display = ("Sim" if value else "Não") if isinstance(value, bool) else format_number(value, 3)
            rows.append({"Grupo": group, "Dado": INPUT_LABELS[key][0], "Valor informado": display,
                         "Unidade": INPUT_LABELS[key][1], "Onde obter": source})
    return pd.DataFrame(rows)


def show_data_sources(p):
    with st.expander("De onde vêm os dados que eu preciso informar?"):
        st.caption("Fontes sugeridas para consulta. Os campos são preenchidos por você; o exemplo inicial não é um poço real documentado.")
        st.dataframe(data_sources_table(p), hide_index=True, width="stretch")
        st.markdown("**Placa da unidade → capacidades** · **Dados do poço → carga de fluido** · **Dimensões e material → movimento e tensões** · **Critérios escolhidos → margens e produção estimada**")


def show_reasoning(p, r):
    """Conecta os valores de entrada aos resultados sem depender de equações na tela."""
    cards = [
        ("01", "Do poço à carga", "#60a5fa",
         f"{format_number(p.depth, 0)} ft de profundidade + óleo de {format_number(p.oil_api)} °API + pistão de {format_number(p.plunger_diameter, 2)} in",
         f"{format_number(r['fluid_load'], 0)} lbf", "carga hidrostática de fluido"),
        ("02", "Do movimento à produção", "#2dd4bf",
         f"{format_number(r['plunger_stroke'])} in de curso efetivo + {format_number(r['operating_speed'])} ciclos/min + {format_number(p.efficiency * 100, 0)}% de eficiência + Bo {format_number(p.volume_factor, 2)}",
         f"{format_number(r['flow_rate'])} STB/d", "vazão estimada em condições de tanque"),
        ("03", "Da elevação à potência", "#fbbf24",
         f"{format_number(r['hydraulic_power'])} hp para o fluido + {format_number(r['friction_power'])} hp de atrito × margem {format_number(p.motor_factor, 2)} aplicada à soma",
         f"{format_number(r['motor_power'])} hp", "potência requerida do motor"),
    ]
    html = '<div class="bm-flow">'
    for index, title, color, inputs, result, label in cards:
        html += f'<article class="bm-flow-card" style="--accent:{color}"><span>{index} / {title}</span><p>{escape(inputs)}</p><div class="bm-flow-arrow">↓</div><strong>{escape(result)}</strong><small>{label}</small></article>'
    st.html(html + "</div>")
