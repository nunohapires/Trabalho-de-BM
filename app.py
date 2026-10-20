"""Interface Streamlit do Projeto BM. Execute: streamlit run app.py."""

from dataclasses import asdict
from pathlib import Path

import streamlit as st

from bm import (
    CARD_NOTE, INPUT_LABELS, MODEL_NOTE, REFERENCES, ProjectInputs, calculate, capacity_checks,
    approximate_dynamometer, decode_pump_tag, operating_warnings,
)
from reports import dynamometer_figure, export_excel, export_pdf, format_number, result_table
from visuals import show_data_sources, show_reasoning, show_system


ROOT = Path(__file__).resolve().parent


def number(key, *, minimum=0.001, maximum=None, step=None, help=None):
    default = getattr(st.session_state.get("project_inputs", ProjectInputs()), key)
    label, unit = INPUT_LABELS[key]
    return st.number_input(
        f"{label} ({unit})" if unit else label,
        min_value=float(minimum), max_value=maximum, value=default,
        step=step, key=key, help=help,
        format="%.3f" if key in {"rod_diameter", "tubing_od", "tubing_id"} else None,
    )


def project_form():
    saved = st.session_state.get("project_inputs", ProjectInputs())
    st.subheader("01 / Dados do projeto")
    st.caption("Preencha os grupos abaixo e clique em Calcular. Os resultados refletem o último envio do formulário.")
    with st.form("project_form", border=True):
        well, equipment, criteria = st.tabs(["Poço e fluido", "Unidade e hastes", "Critérios de cálculo"])
        with well:
            st.caption("No esquema: poço e nível dinâmico em azul; pistão e fluido em turquesa. Consulte registros do poço, teste de nível e análise do óleo.")
            left, middle, right = st.columns(3)
            with left:
                depth = number("depth", minimum=1.0, maximum=30000.0, step=100.0)
                fluid_level = number("fluid_level", minimum=0.0, maximum=30000.0, step=100.0,
                                     help="Distância vertical da superfície ao nível dinâmico, e não a altura de submergência.")
            with middle:
                oil_api = number("oil_api", minimum=0.1, maximum=100.0, step=0.5)
                wellhead_pressure = number("wellhead_pressure", minimum=0.0, maximum=20000.0, step=10.0)
            with right:
                volume_factor = number("volume_factor", minimum=0.01, maximum=10.0, step=0.05)
                efficiency = st.number_input("Eficiência volumétrica (%)", min_value=1.0, max_value=100.0,
                                             value=saved.efficiency * 100, step=1.0, key="efficiency_percent") / 100
        with equipment:
            st.caption("Consulte a placa e o desenho dimensional da unidade, além das especificações da bomba, das hastes e da tubulação.")
            tag_text = st.text_input("TAG da unidade", value=st.session_state.get("project_tag", "C-456D-256-120"), max_chars=40, key="unit_tag",
                                     help="C = convencional; 456 = torque em mil lbf·in; D = redutor duplo; 256 = carga em cem lbf; 120 = curso máximo em in.")
            left, middle, right = st.columns(3)
            with left:
                rod_diameter = number("rod_diameter", minimum=0.1, maximum=5.0, step=0.125)
                plunger_diameter = number("plunger_diameter", minimum=0.1, maximum=10.0, step=0.25)
                steel_weight = number("steel_weight", minimum=1.0, maximum=1000.0, step=10.0)
            with middle:
                tubing_od = number("tubing_od", minimum=0.1, maximum=20.0, step=0.125)
                tubing_id = number("tubing_id", minimum=0.1, maximum=20.0, step=0.001)
                anchored_tubing = st.checkbox("Tubulação ancorada", value=saved.anchored_tubing, key="anchored_tubing",
                                              help="Desconsidera o alongamento da tubulação; a área metálica continua sendo calculada.")
            with right:
                crank_radius = number("crank_radius", minimum=0.1, maximum=200.0, step=1.0)
                pitman_length = number("pitman_length", minimum=0.1, maximum=1000.0, step=1.0)
                beam_rear = number("beam_rear", minimum=0.1, maximum=1000.0, step=1.0)
                beam_front = number("beam_front", minimum=0.1, maximum=1000.0, step=1.0)
        with criteria:
            st.caption("Aqui você define como a unidade opera e as margens adotadas no estudo. Esses critérios não são extraídos da TAG.")
            left, middle, right = st.columns(3)
            with left:
                speed = number("speed", minimum=0.1, maximum=100.0, step=0.5)
                acceleration_limit = number("acceleration_limit", minimum=0.01, maximum=1.0, step=0.05)
                use_limit_speed = st.checkbox("Usar velocidade limite calculada", value=saved.use_limit_speed, key="use_limit_speed",
                                              help="Quando marcado, substitui a velocidade informada pelo limite obtido da geometria e da aceleração.")
            with middle:
                tensile_strength = number("tensile_strength", minimum=1000.0, maximum=300000.0, step=5000.0,
                                          help="Propriedade do material, obtida na especificação da haste. Não é a tensão calculada a partir da carga.")
                service_factor = number("service_factor", minimum=0.01, maximum=1.0, step=0.05,
                                        help="Fator redutor aplicado ao Goodman modificado. Deve ser definido conforme material e ambiente.")
            with right:
                motor_factor = number("motor_factor", minimum=1.0, maximum=3.0, step=0.05,
                                      help="Margem aplicada à soma das potências hidráulica e de atrito. Independente do fator de serviço das hastes.")
                elastic_modulus = number("elastic_modulus", minimum=100000.0, maximum=100000000.0, step=1000000.0)
        st.form_submit_button("Calcular dimensionamento", type="primary", width="stretch", key="calculate_project")
    return tag_text, ProjectInputs(
        depth=depth, oil_api=oil_api, rod_diameter=rod_diameter, plunger_diameter=plunger_diameter,
        steel_weight=steel_weight, tubing_od=tubing_od, tubing_id=tubing_id,
        pitman_length=pitman_length, crank_radius=crank_radius, beam_rear=beam_rear, beam_front=beam_front,
        acceleration_limit=acceleration_limit, speed=speed, use_limit_speed=use_limit_speed,
        anchored_tubing=anchored_tubing, elastic_modulus=elastic_modulus, tensile_strength=tensile_strength,
        service_factor=service_factor, motor_factor=motor_factor, volume_factor=volume_factor,
        efficiency=efficiency, wellhead_pressure=wellhead_pressure, fluid_level=fluid_level,
    )


def show_results(p, tag, r):
    st.subheader("02 / Análise do dimensionamento")
    st.caption(f"Unidade {tag.code} · Coluna uniforme · Velocidade utilizada: {format_number(r['operating_speed'], 2)} ciclos/min")
    columns = st.columns(4)
    for column, label, value, unit in zip(
        columns,
        ["Vazão estimada", "Potência do motor", "Carga máxima", "Curso efetivo"],
        [r["flow_rate"], r["motor_power"], r["peak_load"], r["plunger_stroke"]],
        ["STB/d", "hp", "lbf", "in"], strict=True,
    ):
        column.metric(label, format_number(value), border=True)
        column.caption(unit)

    checks = capacity_checks(tag, r)
    warnings = operating_warnings(p, r)
    if all(row["Atende"] for row in checks):
        st.success("A unidade atende às demandas estimadas de carga, torque e curso.", icon="✅")
    else:
        st.error("Uma ou mais demandas ultrapassam a capacidade da unidade. Confira os critérios abaixo.")
    for warning in warnings:
        st.warning(warning, icon="⚠️")

    st.markdown("#### Dos dados aos resultados")
    show_reasoning(p, r)

    unit_tab, chart_tab, calculations_tab, downloads_tab = st.tabs([
        "Capacidade da unidade", "Carta dinamométrica", "Memória de cálculo", "Exportar relatório",
    ])
    with unit_tab:
        st.caption("A comparação utiliza o curso de superfície S. O curso efetivo Sp é utilizado na estimativa de vazão.")
        for column, row in zip(st.columns(3), checks, strict=True):
            with column, st.container(border=True):
                st.markdown(f"**{row['Critério']}**")
                usage = row["Utilização (%)"]
                st.metric("Utilização", f"{format_number(usage)}%", label_visibility="collapsed")
                st.progress(min(usage / 100, 1.0))
                st.caption(f"Demanda: {format_number(row['Demanda'])} {row['Unidade']}  \nCapacidade: {format_number(row['Capacidade'])} {row['Unidade']}")
                st.markdown(":green[✓ Atende]" if row["Atende"] else ":red[Capacidade excedida]")
        st.caption("A TAG identifica capacidades nominais; a seleção de outro modelo deve ser feita em catálogo.")
        with st.expander("Verificação das hastes e velocidade"):
            left, right = st.columns(2)
            left.metric("Tensão máxima", f"{format_number(r['max_stress'], 0)} psi")
            right.metric("Tensão admissível", f"{format_number(r['allowable_stress'], 0)} psi")
            st.caption(f"Tensão mínima: {format_number(r['min_stress'], 0)} psi · Limite de velocidade: {format_number(r['speed_limit'], 2)} ciclos/min")
            if r["min_load"] < 0:
                st.error("Goodman não aplicável: carga mínima em compressão.")
            elif r["max_stress"] > r["allowable_stress"]:
                st.warning("As hastes excedem a tensão admissível.")
            else:
                st.success("As hastes atendem ao critério simplificado de tensão admissível.")
    with chart_tab:
        st.markdown("**Do modelo ideal ao ciclo aproximado**")
        st.caption("As duas cartas usam o projeto calculado: mesma geometria, velocidade, fluido e coluna de hastes.")
        st.pyplot(dynamometer_figure(r, p=p, dark=True, load_capacity=tag.load_capacity), width="stretch")
        left, middle, right = st.columns(3)
        left.info("**Ideal · linha tracejada**\n\nLimites de carga PPRL e MPRL usados no dimensionamento. A largura é o curso de superfície S.")
        middle.info("**Aproximada · linha amarela**\n\nA carga é transferida ao longo do movimento. A elasticidade inclina as laterais e a inércia curva os trechos de subida e descida.")
        right.info("**Medida · dados de campo**\n\nUma carta real exige registrar carga e posição da haste durante o ciclo. Essa medição ainda não foi importada.")
        try:
            points = approximate_dynamometer(p, r)
        except ValueError as error:
            st.warning(str(error))
        else:
            lower, upper = min(v for _, v in points), max(v for _, v in points)
            st.caption(f"Ciclo aproximado: {format_number(lower, 0)} a {format_number(upper, 0)} lbf · Transferência elástica: {format_number(r['rod_stretch'] + r['tubing_stretch'])} in · Período: {format_number(60 / r['operating_speed'], 2)} s")
        with st.expander("Como esta carta aproximada é construída?"):
            st.write(CARD_NOTE)
            st.markdown("**1. Movimento:** uma aproximação harmônica usa o curso S e a razão manivela/biela.\n\n**2. Transferência de carga:** a carga do fluido é assumida e liberada gradualmente ao longo de er + et.\n\n**3. Inércia:** a aceleração e o peso das hastes modificam a carga durante o ciclo.")
            st.caption("O traçado não recebe ruído artificial nem é ajustado para coincidir com os extremos da carta ideal. Eficiência volumétrica e nível dinâmico não alteram a curva neste modelo de coluna hidrostática completa.")
            st.markdown("[Referência conceitual: Echometer · QRod Help and User Guide](https://www.echometer.com/Portals/0/Quick%20Reference%20Guides/QRod%20Help%20and%20User%20Guide.pdf). A aproximação didática deste projeto não reproduz o simulador QRod.")
    with calculations_tab:
        st.dataframe(result_table(r), hide_index=True, width="stretch",
                     column_config={"Valor": st.column_config.NumberColumn(format="%.4f")})
        st.caption("Valores sem arredondamento intermediário. As unidades estão indicadas em cada linha.")
    with downloads_tab:
        st.markdown("**Leve o dimensionamento com você**")
        st.write("Os arquivos incluem as entradas utilizadas, os resultados, a comparação de capacidades, os alertas e a comparação das cartas de superfície.")
        signature = (tuple(asdict(p).items()), tag.code)
        if st.session_state.get("report_signature") != signature:
            st.session_state.pop("report_files", None)
            st.session_state["report_signature"] = signature
        if st.button("Preparar PDF e Excel", type="primary", key="prepare_reports"):
            try:
                with st.spinner("Preparando os relatórios…"):
                    files = (export_pdf(p, tag, r), export_excel(p, tag, r))
                st.session_state["report_files"] = files
            except (OSError, ValueError, RuntimeError) as error:
                st.error(f"Não foi possível gerar os relatórios: {error}")
        if "report_files" in st.session_state:
            pdf, excel = st.session_state["report_files"]
            left, right = st.columns(2)
            left.download_button("Baixar relatório PDF", data=pdf, file_name="relatorio_projeto_bm.pdf",
                                 mime="application/pdf", width="stretch", on_click="ignore")
            right.download_button("Baixar planilha Excel", data=excel, file_name="resultados_projeto_bm.xlsx",
                                  mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                  width="stretch", on_click="ignore")
    with st.expander("Premissas e limites do modelo"):
        st.write(MODEL_NOTE)
        st.caption("A potência é estimada pela correlação empírica em vazão de tanque. Viscosidade e Rs não entram nessas equações.")


def show_method():
    st.caption("PROJETO BM / DOCUMENTAÇÃO")
    st.title("Método e referências")
    st.write("Ferramenta acadêmica para estudar o dimensionamento de bombeio mecânico convencional.")
    st.info(MODEL_NOTE)
    st.subheader("Como os resultados são obtidos")
    for title, formula in [
        ("Densidade relativa e áreas", r"SG=\frac{141.5}{API+131.5},\quad A_r=\frac{\pi d_r^2}{4},\quad A_p=\frac{\pi d_p^2}{4},\quad A_t=\frac{\pi(D_e^2-D_i^2)}{4}"),
        ("Curso de superfície e velocidade limite", r"S=2c\frac{d_2}{d_1},\quad N_{lim}=\sqrt{\frac{70471.2 L}{S(1+c/h)}}"),
        ("Curso efetivo", r"S_p=S-\frac{12D F_o}{E A_r}-e_t+\frac{12D W_r S N^2(1+c/h)}{70471.2 E A_r}"),
        ("Vazão em condições de tanque", r"q=\frac{1440}{9702}\frac{A_p S_p N E_v}{B_o}"),
        ("Verificação das hastes", r"\sigma_{adm}=SF\left(\frac{T_{material}}{4}+0.5625\,\sigma_{min}\right)"),
        ("Elevação líquida e potência", r"L_n=H+\frac{p_{th}}{(62.4/144)SG},\quad P_m=F_m(7.36\times10^{-6}qSG L_n+6.31\times10^{-7}W_r S N)"),
    ]:
        with st.expander(title):
            st.latex(formula)
    st.caption("Comprimentos e diâmetros em in; profundidades em ft; forças em lbf; tensões em psi; velocidade em ciclos/min. O fator SF das hastes é independente da margem Fm do motor.")
    st.subheader("Leitura da TAG")
    st.code("C - 456 D - 256 - 120\n    │   │     │     └─ curso máximo: 120 in\n    │   │     └─────── carga da estrutura: 25.600 lbf\n    │   └───────────── redutor duplo\n    └───────────────── torque nominal: 456.000 lbf·in", language="text")
    st.subheader("Referências utilizadas")
    for label, url in REFERENCES:
        st.markdown(f"- [{label}]({url})")
    with st.expander("Sobre o projeto original"):
        st.write("Desenvolvido por Nuno Henrique Albuquerque Pires, estudante de Engenharia de Petróleo da Universidade Federal de Alagoas (UFAL).")
        st.image(str(ROOT / "cavalo.png"), caption="Unidade de bombeio mecânico", width=420)


def main():
    st.set_page_config(page_title="Projeto BM · Dimensionamento", page_icon="⚙️", layout="wide")
    st.html("""<style>
    .stMainBlockContainer {max-width: 1280px; padding: 3.5rem 2rem 3rem;}
    h1 {letter-spacing: -0.045em;}
    h2, h3 {letter-spacing: -0.025em;}
    h1, h2, h3, h4 {scroll-margin-top: 5rem;}
    [data-testid="stMetricValue"] {font-variant-numeric: tabular-nums; font-size: clamp(1.2rem, 2.2vw, 2rem);}
    [data-testid="stMetricLabel"] {min-height: 2.6rem; align-items: flex-start;}
    [data-testid="stMetricLabel"] [data-testid="stMarkdownContainer"],
    [data-testid="stMetricLabel"] p {white-space: normal; overflow: visible; text-overflow: clip;}
    [data-testid="stSidebar"] {border-right: 1px solid #27272a;}
    [data-testid^="stBaseButton-primary"] {color: #001b18;}
    .bm-flow {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;margin:.4rem 0 1.7rem;}
    .bm-flow-card {padding:1.1rem;border:1px solid #263337;border-top:3px solid var(--accent);border-radius:12px;background:#080d0f;}
    .bm-flow-card>span {font-size:.8rem;color:var(--accent);font-weight:600;}
    .bm-flow-card p {font-size:.85rem;color:#a6b5bf;line-height:1.6;min-height:5.4rem;margin:.8rem 0 0;}
    .bm-flow-card strong {display:block;font-size:1.5rem;color:#edf4f7;}
    .bm-flow-card small {display:block;color:#a6b5bf;margin-top:.3rem;}
    .bm-flow-arrow {color:var(--accent);font-size:1.3rem;margin:.3rem 0;}
    @media(max-width:900px) {.bm-flow {grid-template-columns:1fr}.bm-flow-card p {min-height:0;}}
    </style>""")
    with st.sidebar:
        st.markdown("## ⚙️ Projeto BM")
        st.caption("ENGENHARIA DE PETRÓLEO")
        st.divider()
        page = st.radio("Navegação", ["Dimensionamento", "Método e referências"], label_visibility="collapsed")
        st.divider()
        st.markdown("**Um projeto, todas as etapas.**")
        st.markdown("[01 · Entenda o sistema](#o-sistema-em-movimento)\n\n[02 · Informe os dados](#01-dados-do-projeto)\n\n[03 · Analise o dimensionamento](#02-analise-do-dimensionamento)")
        st.divider()
        st.caption("Nuno Henrique Albuquerque Pires\n\nUniversidade Federal de Alagoas")
    if page == "Método e referências":
        show_method()
        return
    st.caption("PROJETO BM / UNIDADE CONVENCIONAL")
    st.title("Dimensionamento de bombeio mecânico")
    st.write("Entenda o movimento, conheça os dados e acompanhe cada resultado.")
    overview = st.container()
    tag_text, inputs = project_form()
    st.session_state["project_inputs"] = inputs
    st.session_state["project_tag"] = tag_text
    try:
        tag = decode_pump_tag(tag_text)
        results = calculate(inputs)
    except (ValueError, OverflowError, ZeroDivisionError) as error:
        st.session_state.pop("report_files", None)
        st.error(str(error))
        st.info("Corrija os dados e envie o formulário novamente para visualizar os resultados.")
        st.stop()
    with overview:
        st.subheader("O sistema em movimento")
        show_system(inputs, results)
        show_data_sources(inputs)
    st.divider()
    show_results(inputs, tag, results)


if __name__ == "__main__":
    main()
