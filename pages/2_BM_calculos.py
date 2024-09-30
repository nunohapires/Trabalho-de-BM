import streamlit as st
import numpy as np
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
from reportlab.lib.utils import ImageReader

st.set_page_config(
    page_title="Pojeto",
    page_icon="⚙",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.sidebar.image('logo_nuno.jpg',)
st.sidebar.markdown(" *Desenvolvido pelo estudante de engenharia de petróleo Nuno Henrique Albuquerque Pires,[Universidade Federal de Alagoas].* ")
st.title(' Projeto Projeto BM! ⚙🛢')
st.subheader('Unidade de bombeio')

st.divider() #######################################################################

import streamlit as st

def decode_pump_tag(tag):
    """
    Decodifica uma tag de unidade de bombeio mecânico e retorna as especificações.
    Parâmetros:
    tag (str): A tag da unidade de bombeio (ex: "C-456D-256-120").
    Retorna:
    dict: Um dicionário com as especificações da unidade de bombeio.
    """
    try:
        parts = tag.split('-')
        tipo_unidade = parts[0]
        comprimento_braco = parts[1]
        torque_contrapeso = parts[2]
        curso_cavalo = parts[3]
    except IndexError:
        return "Formato de tag inválido. Use o formato C-456D-256-120."

    comprimento_braco_num = ''.join(filter(str.isdigit, comprimento_braco))

    info = {
        "Tipo da Unidade": "Convencional" if tipo_unidade == 'C' else "Desconhecido",
        "Comprimento do Braço": f"{comprimento_braco_num} polegadas",
        "Torque do Contrapeso": f"{torque_contrapeso} inch-lbs",
        "Curso do Cavalo": f"{curso_cavalo} polegadas"
    }
    return info

# Interface Streamlit
st.markdown("##### Informações Tag de Bombeio Mecânico")
st.write("Utilize o formato de TAG: **C-123D-123-123**")

# Entrada do código da TAG
with st.popover("Exemplo de onde encontrar a tag"):
        st.markdown("Espero ter ajudado 👋")
        st.image('tag.png')

original_tag = st.text_input("Digite o código da bomba (TAG):", value='C-456D-256-120')
# Decodificação e exibição dos resultados
decoded_info = decode_pump_tag(original_tag)

# Exibindo de forma mais atraente com Streamlit
if isinstance(decoded_info, dict):
    st.success("Tag decodificada com sucesso!")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tipo da Unidade", decoded_info.get("Tipo da Unidade"))
        st.metric("Comprimento do Braço", decoded_info.get("Comprimento do Braço"))
    with col2:
        st.metric("Torque do Contrapeso", decoded_info.get("Torque do Contrapeso"))
        st.metric("Curso do Cavalo", decoded_info.get("Curso do Cavalo"))
else:
    st.error(decoded_info)

# Unpacking das informações
tipo_unidade = decoded_info.get("Tipo da Unidade")
comprimento_braco = decoded_info.get("Comprimento do Braço")
torque_contrapeso = decoded_info.get("Torque do Contrapeso")
curso_cavalo = decoded_info.get("Curso do Cavalo")

# Definindo o layout em duas colunas 
col1, col2 = st.columns(2)
with col1:
    yaco = st.number_input('Peso específico do aço ou de outro material usado(lbf/ft³):',value=490)
    D = st.number_input('Profundidade de assentamento(ft):',value=4000)
with col2:
    Api = st.number_input('API do oleo :', value = 29)
    Ar = st.number_input('Diametro da seção transversal da haste(in):',value=0.75)
D_pistao = st.number_input('Diametro do pistão (in):',value=2.5)
col1,col2,col3,col4 = st.columns(4)

with col1:
    # peso da coluna de haste no ar
    st.markdown('### Peso da coluna de haste no ar ')
    Wr = (yaco*D*(np.pi*(((Ar)/2)**2)))/144
    st.latex(f"W_{{\\text{{r}}}} = {Wr:.2f} \\text{{ lbf}}")

with col2:
    # Empuxo nas hastes (lbf)
    st.markdown('### Empuxo nas hastes (lbf)')
    d_fluido = (141.5/(Api + 131.5))
    Ef = d_fluido*62.4*(Wr/yaco)
    st.latex(f"E_{{\\text{{f}}}} = {Ef:.2f} \\text{{ lbf}}")

with col3:
    st.markdown('### Peso estático da coluna imersa ou flutuante (lbf)')
    Wrf = Wr - Ef
    st.latex(f"W_{{\\text{{rf}}}} = {Wrf:.2f} \\text{{ lbf}}")

with col4:
    st.markdown('### Peso da coluna de fluido (lbf)')
    # calculando a area do pistao
    Ap = np.pi*(D_pistao/2)**2
    Fo = (62.4*d_fluido*D*Ap)/144
    st.latex(f"F_{{\\text{{o}}}} = {Fo:.2f} \\text{{ lbf}}")

st.divider() #############################################################

# adicionando as variaveis que faltam
st.markdown('### Calculando os outros parametros')
col1,col2 = st.columns(2)
with col1:
    h = st.number_input('Altura do suporte ou componente específico da instalação(in)',value=114)
    c = st.number_input('Curso do êmbolo (o movimento para cima e para baixo)(in)',value=37)
    dp = st.number_input('Diâmetro externo da tubulação de produção(in)',value=3)
with col2:
    L = st.number_input('Fator de desaceleração',value=0.5)
    d1 = st.number_input('Diâmetro do cilindro de sucção (ou diâmetro interno do pistão)(in)',value=96.05)
    d2 = st.number_input('Diâmetro do êmbolo ou do pistão (in)',value=111)

# comom estamos usandfo para a UB comum par afins de simplificao sao usaremos o valor como positivo 
# Cálculo das expressões principais
M = 1 + (c / h)
E = 30 * 10**6
S = 2 * c * d2 / d1
N = np.sqrt(70471.2 * L / (S * (1 + c / h)))
# Cálculo da área transversal (exemplo)
At = np.pi * (dp / 2) ** 2
constante = 70471.2
# Calculando os termos intermediários
termo1 = (12 * D / E) * Wrf * (1 / At + 1 / Ar)
termo2 = (12 * D / E)*((S * N**2 * Wr * M) / (constante * Ar))
# Calculando Sp de acordo com a equação original
Sp = S - termo1 - termo2

col1,col2,col3 = st.columns(3)
with col1:
    st.markdown(':blue-background[Comprimento efetivo do curso do pistão (in)]')
    st.latex(f"S_{{\\text{{p}}}} = {Sp:.2f} \\text{{ in}}")

    sig1 = (Wr * M * S * N**2) / constante
    sig2 = (Wr * (1 - (c / h)) * S * N**2) / constante

    st.markdown(':blue-background[Esforço dinâmico (lbf)]')
    st.latex(f"Sig_{{\\text{{max}}}} = {sig1:.2f} \\text{{ lbf}}")
    st.latex(f"Sig_{{\\text{{min}}}} = {sig2:.2f} \\text{{ lbf}}")
with col2:
    st.markdown(':blue-background[Peak Polished Rod Load (Carga máxima)]')
    PPRL = Wrf + Fo + sig1
    st.latex(f"PPRL_{{\\text{{carga máxima}}}} = {PPRL:.2f} \\text{{ lbf}}")

    st.markdown(':blue-background[Minimum Polished Rod Load(carga mínima, lbf)]')
    MPRL = Wrf - sig2 
    st.latex(f"MPRL_{{\\text{{carga mínima}}}} = {MPRL:.2f} \\text{{ lbf}}")
with col3:
    st.markdown(':blue-background[Efeito de contrabalanceio (lbf)]')
    Cbe = (PPRL + MPRL)/2
    st.latex(f"PPRL_{{\\text{{Efeito de contrabalanceio}}}} = {Cbe:.2f} \\text{{ lbf}}")

    st.markdown(':blue-background[Peak Torque - Torque máximo(lbf.in)]')
    Pt = (PPRL - MPRL)*Sp/4
    st.latex(f"Pt_{{\\text{{Torque máximo}}}} = {Pt:.2f} \\text{{ lbf.in}}")

st.divider() ###################################################################

st.markdown('### Para que a coluna de hastes dure no mínimo 10 milhões de ciclos é recomendado pela API de acordo com a seguinte equação')
st.markdown('O fator de seguranca geralmente varia de 30% ate 50% (1.30 - 1.50)')
F = st.number_input('Usando o fator de segurança :',value=1.50)
col1,col2,col3 = st.columns(3)
with col1 :
    st.markdown(':red-background[Tensão mínima de ruptura]')
    T = PPRL/(np.pi*(((Ar)/2)**2))
    st.latex(f"T_{{\\text{{mínima}}}} = {T:.2f} \\text{{ Psi}}")
with col2:
    st.markdown(':red-background[Tensão mínima presente]')
    Sig_min = MPRL/(np.pi*(((Ar)/2)**2))
    st.latex(f"Pt_{{\\text{{mínima}}}} = {Sig_min:.2f} \\text{{ Psi}}")
with col3:
    st.markdown(':red-background[Tensão máxima admissível]')
    Sig_adm = ((T/4) + (0.5625*Sig_min))*Sp*F
    st.latex(f"Sig_{{\\text{{ADM}}}} = {Sig_adm:.2f} \\text{{ Psi}}")

st.divider() #####################################################################
st.markdown('## Potência necessária para elevar os fluidos (hp)')
def viscosidade_oleo_morto_por_densidade(densidade):
    """
    Calcula a viscosidade do óleo morto (μ_od) a partir da densidade usando a correlação de Beal.
    
    Parâmetro:
    densidade: Densidade do óleo em g/cm³
    
    Retorna:
    μ_od: Viscosidade do óleo morto em centipoise (cp)
    """
    log_mu_od = 1.8653 - 0.025086 * Api
    mu_od = 10 ** log_mu_od
    return mu_od

def viscosidade_oleo_saturado_por_bo(densidade, Rs, Bo):
    """
    Calcula a viscosidade do óleo saturado (μ_o) a partir da densidade e fator volume de formação Bo.
    
    Parâmetros:
    densidade: Densidade do óleo em g/cm³
    Rs: Relação gás-óleo (scf/STB)
    Bo: Fator volume de formação de óleo (bbl/STB)
    
    Retorna:
    μ_o: Viscosidade do óleo saturado em centipoise (cp)
    """
    mu_od = viscosidade_oleo_morto_por_densidade(densidade)
    exponent = 0.43 + (8.33 / (Rs + 150))
    mu_o = mu_od / (10 ** exponent)
    
    # Correção adicional por Bo (se aplicável)
    mu_o_corrigido = mu_o * Bo
    return mu_o_corrigido

col1,col2 = st.columns(2)
with col1:
    Rs = st.number_input('O valor de Rs usado em (scf/STB): ', value= 200)
    Bo = st.number_input('O valor do Bo ', value= 1.15)
    Ev = st.number_input('Usando uma eficência de (ex : 80%):', value= 80)
    Ev = Ev/100
mu_o = viscosidade_oleo_saturado_por_bo(d_fluido, Rs, Bo) # nao tocar aqui para nao bugar ou arrume tudo kkkkk

with col2 :
    Visc_oleo = st.number_input('o valor calculado da viscosidade do oleo (corrija se necessário)(cp)',value = mu_o)
    pth = st.number_input('A pressao na cabeca do posso e de: (psig)', value= 100)
    Ha = st.number_input('Profundidade de fluido no anular (ft)',value = D)
with col1:
    st.markdown('### :blue-background[Vazao estimada]')
    q = 0.1484*((np.pi*(((Ap)/2)**2))*Sp*Ev*N)/Bo
    st.latex(f"q_{{\\text{{o}}}} = {q:.2f} \\text{{ Stb/day}}")

    st.markdown('### :blue-background[Net lift]')
    Ln = Ha + (pth/0.433*Visc_oleo)
    st.latex(f"Ln_{{\\text{{}}}} = {q:.2f} \\text{{ ft}}")
with col2:
    st.markdown('### :blue-background[Potência necessária]')
    p_fluido = 7.36e-6*q*Visc_oleo*Ln
    st.latex(f"P_{{\\text{{fluido}}}} = {p_fluido:.2f} \\text{{ hp}}")

    st.markdown('### :blue-background[Potência necessária para superar perdas por atrito]')
    p_atrito = 6.31e-7 * Wr *S*N
    st.latex(f"P_{{\\text{{atrito}}}} = {p_atrito:.2f} \\text{{ hp}}")

st.markdown('### :blue-background[Potência total do motor principal]')
p_motor = F*(p_fluido + p_atrito)
st.latex(f"P_{{\\text{{total}}}} = {p_motor:.2f} \\text{{ hp}}")

st.divider() ####################################################################
# vamos tentar plotar a carta dinamometrica 
# usando o pandas para criar uma tabela para gearar os pontos 'ideais' para o plot usando o proprio streamlit 
# Definindo os dados para formar um polígono fechado
data = {
    'Deslocamento(in)': [0, 0, Sp, Sp, 0],  # O ponto 0 é repetido para fechar o polígono
    'Carga(lbf)': [MPRL, PPRL, PPRL, MPRL, MPRL]  # O último ponto deve ter o mesmo valor que o primeiro
}
df = pd.DataFrame(data)

# Criando o gráfico
st.markdown('## Carta dinamométrica ideal')

plt.figure(figsize=(10, 6))
plt.plot(df['Deslocamento(in)'], df['Carga(lbf)'], marker='o')
plt.fill(df['Deslocamento(in)'], df['Carga(lbf)'], alpha=0.2)  # Preencher a área sob a linha
plt.title('Carta Dinamométrica Ideal')
plt.xlabel('Deslocamento (in)')
plt.ylabel('Carga (lbf)')
plt.grid()
plt.xlim(left=0)  # Definir o limite inferior do eixo x
plt.ylim(bottom=0)  # Definir o limite inferior do eixo y

# Exibir o gráfico no Streamlit
st.pyplot(plt)

# Função para gerar a nova TAG
def gerar_nova_tag(Wr, PPRL, Sp):
    tipo_unidade = 'C'
    comprimento_braco = int(Wr / 10)
    torque_contrapeso = int(PPRL / 10)
    curso_cavalo = int(Sp)
    nova_tag = f"{tipo_unidade}-{comprimento_braco}D-{torque_contrapeso}-{curso_cavalo}"
    return nova_tag


# Função para gerar o gráfico da carta dinamométrica
def gerar_grafico(df):
    fig, ax = plt.subplots()
    ax.fill_between(df['Deslocamento(in)'], df['Carga(lbf)'], color="skyblue", alpha=0.5)
    ax.plot(df['Deslocamento(in)'], df['Carga(lbf)'], color="Slateblue", alpha=0.6, linewidth=2)
    ax.set_title('Carta Dinamométrica Ideal')
    ax.set_xlabel('Deslocamento (in)')
    ax.set_ylabel('Carga (lbf)')
    
    buffer = BytesIO()
    plt.savefig(buffer, format="PNG")
    plt.close(fig)
    buffer.seek(0)
    return buffer


# Função para gerar o PDF
def gerar_pdf(decoded_info, nova_tag, Wr, Ef, Wrf, Fo, Sp, sig1, sig2, PPRL, MPRL, Cbe, Pt, T, Sig_min, Sig_adm, p_fluido, p_atrito, p_motor, df, chart_buffer):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    
    width, height = A4
    
    # Título
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.darkblue)
    c.drawString(100, height - 50, "Relatório do Projeto BM - Unidade de Bombeio")
    
    # Informações Importantes - Nova TAG
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.black)
    c.drawString(100, height - 100, "Informações Importantes")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 130, f"TAG Gerada: {nova_tag}")
    
    # Informações Decodificadas
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, height - 160, "Informações Decodificadas da TAG Original")
    
    c.setFont("Helvetica", 10)
    y_position = height - 180
    for key, value in decoded_info.items():
        c.drawString(100, y_position, f"{key}: {value}")
        y_position -= 20
    
    # Resultados dos Cálculos
    c.setFont("Helvetica-Bold", 14)
    y_position -= 20
    c.drawString(100, y_position, "Resultados dos Cálculos")
    
    c.setFont("Helvetica", 10)
    resultados = [
        (f"Peso da Coluna de Haste no Ar: {Wr:.2f} lbf", f"Empuxo nas Hastes: {Ef:.2f} lbf"),
        (f"Peso Estático da Coluna Imersa: {Wrf:.2f} lbf", f"Peso da Coluna de Fluido: {Fo:.2f} lbf"),
        (f"Comprimento Efetivo do Curso do Pistão: {Sp:.2f} in", ""),
        (f"Esforço Dinâmico Máximo: {sig1:.2f} lbf", f"Esforço Dinâmico Mínimo: {sig2:.2f} lbf"),
        (f"Carga Máxima do Polido (PPRL): {PPRL:.2f} lbf", f"Carga Mínima do Polido (MPRL): {MPRL:.2f} lbf"),
        (f"Efeito de Contrabalanceio: {Cbe:.2f} lbf", f"Torque Máximo: {Pt:.2f} lbf.in"),
        (f"Tensão Mínima de Ruptura: {T:.2f} Psi", f"Tensão Mínima Presente: {Sig_min:.2f} Psi"),
        (f"Tensão Máxima Admissível: {Sig_adm:.2f} Psi", ""),
        (f"Potência Necessária para Elevar os Fluidos: {p_fluido:.2f} hp", f"Potência para Superar Atrito: {p_atrito:.2f} hp"),
        (f"Potência Total do Motor: {p_motor:.2f} hp", "")
    ]
    
    y_position -= 20
    for linha in resultados:
        c.drawString(100, y_position, linha[0])
        if linha[1]:
            c.drawString(350, y_position, linha[1])
        y_position -= 20
    
    # Nova página para o gráfico
    c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, "Carta Dinamométrica Ideal")
    
    # Adicionar o gráfico da carta dinamométrica ao PDF
    c.drawImage(ImageReader(chart_buffer), 100, height - 400, width=400, height=300)
    
    # Rodapé com autoria
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(100, 50, "Relatório elaborado por Nuno Henrique Albuquerque Pires")
    
    # Finalizar o PDF
    c.save()
    
    buffer.seek(0)
    return buffer

nova_tag = gerar_nova_tag(Wr, PPRL, Sp)
if original_tag == nova_tag:
    st.success("A unidade foi dimensionada com sucesso!")
else:
    st.warning(f"A TAG sugerida é {nova_tag}, pois a original não atendia aos parâmetros.")

chart_buffer = gerar_grafico(df)
if st.button("Gerar PDF"):
        buffer = gerar_pdf(decoded_info, nova_tag, Wr, Ef, Wrf, Fo, Sp, sig1, sig2, PPRL, MPRL, Cbe, Pt, T, Sig_min, Sig_adm, p_fluido, p_atrito, p_motor, df, chart_buffer)
        st.download_button("Download PDF", buffer, "relatorio_projeto_BM.pdf", "application/pdf")
        
# Adicionando uma seção para exportar resultados para uma planilha
st.markdown('## Exportar Resultados')

# Criação do DataFrame com todos os resultados
resultados = {
    'Parâmetro': [
        'Peso específico do aço', 'Profundidade de assentamento', 'API do óleo', 
        'Diâmetro da seção transversal da haste', 'Diâmetro do pistão', 
        'Peso da coluna de haste no ar', 'Empuxo nas hastes', 
        'Peso estático da coluna imersa ou flutuante', 'Peso da coluna de fluido', 
        'Altura do suporte', 'Curso do êmbolo', 'Diâmetro externo da tubulação de produção',
        'Fator de desaceleração', 'Diâmetro do cilindro de sucção', 'Diâmetro do êmbolo',
        'Comprimento efetivo do curso do pistão', 'Esforço dinâmico (max)', 
        'Esforço dinâmico (min)', 'Carga máxima', 'Carga mínima', 'Efeito de contrabalanceio',
        'Torque máximo', 'Tensão mínima de ruptura', 'Tensão mínima presente', 
        'Tensão máxima admissível', 'Vazão estimada', 'Net lift', 'Potência necessária', 
        'Potência necessária para superar perdas por atrito', 'Potência total do motor principal'
    ],
    'Valor': [
        yaco, D, Api, Ar, D_pistao, Wr, Ef, Wrf, Fo, h, c, dp, L, d1, d2, 
        Sp, sig1, sig2, PPRL, MPRL, Cbe, Pt, T, Sig_min, Sig_adm, 
        q, Ln, p_fluido, p_atrito, p_motor
    ],
    'Unidade': [
        'kg/m³', 'ft', '°API', 'in²', 'ft', 
        'lbf', 'lbf', 'lbf', 'lbf', 
        'ft', 'ft', 'ft', '', 
        'ft', 'ft', 'ft', 
        'ft', 'lbf', 'lbf', 
        'lbf', 'lbf', 'lbf', 
        'lbf·in', 'Psi', 'Psi', 'Psi', 
        'STB/day', 'ft', 'hp', 
        'hp', 'hp'
    ]
}

df_resultados = pd.DataFrame(resultados)

# Criando um arquivo Excel
excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    df_resultados.to_excel(writer, sheet_name='Resultados', index=False)

# Mostrando o botão para download do Excel
st.download_button(
    label='Baixar Resultados em Excel',
    data=excel_buffer.getvalue(),
    file_name='resultados_projeto_bm.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

st.markdown('- Os valores calculados da carta')
df