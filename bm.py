"""Modelo simplificado de bombeio mecânico convencional, em unidades de campo.

Equações e limites de aplicação documentados no README. Sem dependências de UI.
"""

from dataclasses import dataclass, fields
from math import isfinite, pi, sqrt
import re


MODEL_NOTE = (
    "Estimativa acadêmica para unidade convencional, coluna de hastes uniforme e óleo "
    "homogêneo. A carga de fluido usa a coluna hidrostática até a profundidade da bomba; "
    "o nível dinâmico é usado na elevação líquida. Não inclui ondas elásticas, gás livre, "
    "água, desvio do poço ou um modelo de atrito viscoso. A comparação de capacidades "
    "não substitui a seleção pelo catálogo do fabricante."
)
REFERENCES = (
    ("Guo, Liu e Tan · Petroleum Production Engineering, 2ª ed., 2017", "https://www.sciencedirect.com/book/9780128093740/petroleum-production-engineering"),
    ("Merey (2020) · Equações de dimensionamento de BM, tabela 3", "https://doi.org/10.18466/cbayarfbe.646805"),
    ("Tenaris · Sucker Rods Catalogue, Goodman modificado, p. 69", "https://www.tenaris.com/media/ugtdh5xw/suckerrodstechnicalcatalogue-6.pdf"),
    ("Sunnda · Catálogo de unidades convencionais, p. 60", "https://www.sunnda.com/catalog/sunnda-composite-catalog.pdf"),
)


@dataclass(frozen=True)
class PumpTag:
    code: str
    torque_capacity: float  # lbf.in
    load_capacity: float  # lbf
    stroke_capacity: float  # in


def decode_pump_tag(value: str) -> PumpTag:
    """Lê C-[torque em mil lbf.in]D-[carga em cem lbf]-[curso em in]."""
    code = value.strip().upper()
    match = re.fullmatch(r"C-([1-9][0-9]{0,5})D-([1-9][0-9]{0,5})-([1-9][0-9]{0,5})", code)
    if not match:
        raise ValueError("TAG inválida. Use C-456D-256-120, com valores positivos. O modelo aceita unidades convencionais com redutor duplo (C / D).")
    torque, load, stroke = map(int, match.groups())
    return PumpTag(code, torque * 1000.0, load * 100.0, float(stroke))


@dataclass(frozen=True)
class ProjectInputs:
    depth: float = 4000.0
    oil_api: float = 29.0
    rod_diameter: float = 0.75
    plunger_diameter: float = 2.5
    steel_weight: float = 490.0
    tubing_od: float = 3.5
    tubing_id: float = 2.992
    pitman_length: float = 114.0
    crank_radius: float = 37.0
    beam_rear: float = 96.05
    beam_front: float = 111.0
    acceleration_limit: float = 0.5
    speed: float = 12.0
    use_limit_speed: bool = False
    anchored_tubing: bool = True
    elastic_modulus: float = 30_000_000.0
    tensile_strength: float = 115_000.0
    service_factor: float = 0.9
    motor_factor: float = 1.5
    volume_factor: float = 1.15
    efficiency: float = 0.8
    wellhead_pressure: float = 100.0
    fluid_level: float = 4000.0


# Campo: descrição legível e unidade. Compartilhado pela interface e relatórios.
INPUT_LABELS = {
    "depth": ("Profundidade da bomba", "ft"),
    "oil_api": ("Grau API do óleo", "°API"),
    "rod_diameter": ("Diâmetro da haste", "in"),
    "plunger_diameter": ("Diâmetro do pistão", "in"),
    "steel_weight": ("Peso específico das hastes", "lbf/ft³"),
    "tubing_od": ("Diâmetro externo da tubulação", "in"),
    "tubing_id": ("Diâmetro interno da tubulação", "in"),
    "pitman_length": ("Comprimento da biela · h", "in"),
    "crank_radius": ("Raio da manivela · c", "in"),
    "beam_rear": ("Braço traseiro do balancim · d1", "in"),
    "beam_front": ("Braço dianteiro do balancim · d2", "in"),
    "acceleration_limit": ("Limite de aceleração", "g"),
    "speed": ("Velocidade informada", "ciclos/min"),
    "use_limit_speed": ("Usar velocidade limite calculada", ""),
    "anchored_tubing": ("Tubulação ancorada", ""),
    "elastic_modulus": ("Módulo de elasticidade", "psi"),
    "tensile_strength": ("Resistência mínima à tração do material", "psi"),
    "service_factor": ("Fator de serviço das hastes", ""),
    "motor_factor": ("Fator de dimensionamento do motor", ""),
    "volume_factor": ("Fator volume de formação · Bo", "rb/STB"),
    "efficiency": ("Eficiência volumétrica", "fração"),
    "wellhead_pressure": ("Pressão na cabeça do poço", "psig"),
    "fluid_level": ("Profundidade do nível dinâmico", "ft"),
}

RESULT_LABELS = {
    "specific_gravity": ("Densidade relativa do óleo", "SG", ""),
    "rod_area": ("Área transversal da haste", "Ar", "in²"),
    "plunger_area": ("Área do pistão", "Ap", "in²"),
    "tubing_area": ("Área metálica da tubulação", "At", "in²"),
    "rod_weight": ("Peso das hastes no ar", "Wr", "lbf"),
    "buoyancy": ("Empuxo nas hastes", "Ef", "lbf"),
    "buoyant_weight": ("Peso das hastes imersas", "Wrf", "lbf"),
    "fluid_load": ("Carga hidrostática de fluido", "Fo", "lbf"),
    "surface_stroke": ("Curso da haste polida", "S", "in"),
    "speed_limit": ("Velocidade limite calculada", "Nlim", "ciclos/min"),
    "operating_speed": ("Velocidade utilizada", "N", "ciclos/min"),
    "rod_stretch": ("Alongamento das hastes por carga de fluido", "er", "in"),
    "tubing_stretch": ("Alongamento da tubulação", "et", "in"),
    "overtravel": ("Sobrecurso dinâmico estimado", "eo", "in"),
    "plunger_stroke": ("Curso efetivo do pistão", "Sp", "in"),
    "dynamic_max": ("Esforço dinâmico na subida", "Fdin,max", "lbf"),
    "dynamic_min": ("Esforço dinâmico na descida", "Fdin,min", "lbf"),
    "peak_load": ("Carga máxima da haste polida", "PPRL", "lbf"),
    "min_load": ("Carga mínima da haste polida", "MPRL", "lbf"),
    "counterbalance": ("Efeito de contrabalanceio", "CBE", "lbf"),
    "peak_torque": ("Torque máximo estimado", "Tpeak", "lbf·in"),
    "max_stress": ("Tensão máxima calculada", "σmax", "psi"),
    "min_stress": ("Tensão mínima calculada", "σmin", "psi"),
    "allowable_stress": ("Tensão admissível · Goodman modificado", "σadm", "psi"),
    "displacement": ("Deslocamento volumétrico teórico", "PD", "bbl/d"),
    "flow_rate": ("Vazão estimada em condições de tanque", "q", "STB/d"),
    "net_lift": ("Elevação líquida · net lift", "Ln", "ft"),
    "hydraulic_power": ("Potência hidráulica estimada", "Ph", "hp"),
    "friction_power": ("Potência para superar atrito", "Pf", "hp"),
    "motor_power": ("Potência requerida do motor", "Pmotor", "hp"),
}


def validate_inputs(p: ProjectInputs) -> None:
    for field in fields(p):
        value = getattr(p, field.name)
        label = INPUT_LABELS[field.name][0]
        if field.name in {"use_limit_speed", "anchored_tubing"}:
            if not isinstance(value, bool):
                raise ValueError(f"{label}: selecione sim ou não.")
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError(f"{label}: informe um número finito.")
        if field.name in {"fluid_level", "wellhead_pressure"}:
            if value < 0:
                raise ValueError(f"{label}: o valor não pode ser negativo.")
        elif field.name == "oil_api":
            if not 0 < value <= 100:
                raise ValueError("Grau API: use um valor entre 0 (exclusivo) e 100.")
        elif value <= 0:
            raise ValueError(f"{label}: o valor deve ser maior que zero.")
    if p.tubing_id >= p.tubing_od:
        raise ValueError("O diâmetro interno da tubulação deve ser menor que o externo.")
    if p.rod_diameter >= p.tubing_id:
        raise ValueError("A haste deve ter diâmetro menor que o diâmetro interno da tubulação.")
    if p.crank_radius >= p.pitman_length:
        raise ValueError("O raio da manivela deve ser menor que o comprimento da biela (c < h).")
    if p.fluid_level > p.depth:
        raise ValueError("O nível dinâmico não pode estar abaixo da profundidade da bomba.")
    if not 0 < p.efficiency <= 1 or not 0 < p.service_factor <= 1:
        raise ValueError("Eficiência e fator de serviço devem estar entre 0 (exclusivo) e 1.")
    if p.motor_factor < 1:
        raise ValueError("O fator de dimensionamento do motor deve ser maior ou igual a 1.")
    if p.acceleration_limit > 1:
        raise ValueError("Use um limite de aceleração de até 1 g neste modelo.")
    if p.steel_weight <= 62.4 * 141.5 / (p.oil_api + 131.5):
        raise ValueError("O peso específico das hastes deve superar o do fluido neste modelo de coluna tracionada.")


def calculate(p: ProjectInputs) -> dict[str, float]:
    """Modelo concentrado de Guo, para coluna uniforme e fluido homogêneo."""
    validate_inputs(p)
    sg = 141.5 / (p.oil_api + 131.5)
    ar = pi * p.rod_diameter**2 / 4
    ap = pi * p.plunger_diameter**2 / 4
    at = pi * (p.tubing_od**2 - p.tubing_id**2) / 4
    wr = p.steel_weight * p.depth * ar / 144
    buoyancy = sg * 62.4 * wr / p.steel_weight
    wrf = wr - buoyancy
    fo = sg * 62.4 * p.depth * ap / 144
    ratio = p.crank_radius / p.pitman_length
    stroke = 2 * p.crank_radius * p.beam_front / p.beam_rear
    speed_limit = sqrt(70471.2 * p.acceleration_limit / (stroke * (1 + ratio)))
    speed = speed_limit if p.use_limit_speed else p.speed
    up = stroke * speed**2 * (1 + ratio) / 70471.2
    down = stroke * speed**2 * (1 - ratio) / 70471.2
    dynamic_max, dynamic_min = wr * up, wr * down
    peak, minimum = wrf + fo + dynamic_max, wrf - dynamic_min
    compliance = 12 * p.depth / p.elastic_modulus
    rod_stretch = compliance * fo / ar
    tubing_stretch = 0.0 if p.anchored_tubing else compliance * fo / at
    overtravel = compliance * dynamic_max / ar
    plunger_stroke = stroke - rod_stretch - tubing_stretch + overtravel
    if plunger_stroke <= 0:
        raise ValueError("O curso efetivo calculado é nulo ou negativo. Revise profundidade, geometria, diâmetros e velocidade.")
    maximum_stress, minimum_stress = peak / ar, minimum / ar
    allowable = (p.tensile_strength / 4 + 0.5625 * minimum_stress) * p.service_factor
    # 1440 min/d ÷ 9702 in³/bbl: usa área uma única vez.
    displacement = (1440 / 9702) * ap * plunger_stroke * speed
    flow = displacement * p.efficiency / p.volume_factor
    net_lift = p.fluid_level + p.wellhead_pressure / ((62.4 / 144) * sg)
    hydraulic = 7.36e-6 * flow * sg * net_lift
    friction = 6.31e-7 * wr * stroke * speed
    results = {
        "specific_gravity": sg,
        "rod_area": ar,
        "plunger_area": ap,
        "tubing_area": at,
        "rod_weight": wr,
        "buoyancy": buoyancy,
        "buoyant_weight": wrf,
        "fluid_load": fo,
        "surface_stroke": stroke,
        "speed_limit": speed_limit,
        "operating_speed": speed,
        "rod_stretch": rod_stretch,
        "tubing_stretch": tubing_stretch,
        "overtravel": overtravel,
        "plunger_stroke": plunger_stroke,
        "dynamic_max": dynamic_max,
        "dynamic_min": dynamic_min,
        "peak_load": peak,
        "min_load": minimum,
        "counterbalance": (peak + minimum) / 2,
        "peak_torque": (peak - minimum) * stroke / 4,
        "max_stress": maximum_stress,
        "min_stress": minimum_stress,
        "allowable_stress": allowable,
        "displacement": displacement,
        "flow_rate": flow,
        "net_lift": net_lift,
        "hydraulic_power": hydraulic,
        "friction_power": friction,
        "motor_power": p.motor_factor * (hydraulic + friction),
    }
    if not all(isfinite(value) for value in results.values()):
        raise ValueError("Os parâmetros produzem resultados fora do intervalo numérico. Revise as entradas.")
    return results


def capacity_checks(tag: PumpTag, r: dict[str, float]) -> list[dict]:
    """Compara demandas numéricas, independentemente do texto da TAG."""
    return [
        {"Critério": label, "Demanda": demand, "Capacidade": capacity,
         "Unidade": unit, "Utilização (%)": 100 * demand / capacity,
         "Atende": demand <= capacity}
        for label, demand, capacity, unit in (
            ("Carga da estrutura", r["peak_load"], tag.load_capacity, "lbf"),
            ("Torque do redutor", r["peak_torque"], tag.torque_capacity, "lbf·in"),
            ("Curso de superfície", r["surface_stroke"], tag.stroke_capacity, "in"),
        )
    ]


def operating_warnings(p: ProjectInputs, r: dict[str, float]) -> list[str]:
    warnings = []
    if r["operating_speed"] > r["speed_limit"] * (1 + 1e-9):
        warnings.append("A velocidade informada ultrapassa o limite de aceleração escolhido.")
    if r["min_load"] < 0:
        warnings.append("A carga mínima é negativa: há indicação de compressão. A verificação de Goodman não se aplica a esse regime.")
    elif r["max_stress"] > r["allowable_stress"]:
        warnings.append("A tensão máxima ultrapassa a tensão admissível das hastes.")
    if r["max_stress"] >= p.tensile_strength:
        warnings.append("A tensão máxima alcança ou ultrapassa a resistência mínima à tração informada.")
    return warnings
