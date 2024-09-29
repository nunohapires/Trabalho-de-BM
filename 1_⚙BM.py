#importações necessarias  
import streamlit as st 

#configurações da pagina 
st.set_page_config(
    layout="wide",
    page_title="HOME Projeto BM",
    initial_sidebar_state="expanded",
    page_icon="⚙",
)

st.markdown("# Projeto Projeto BM! ⚙🛢") 
st.sidebar.image('logo_nuno.jpg',)
st.sidebar.markdown(" *Desenvolvido pelo estudante de engenharia de petróleo Nuno Henrique Albuquerque Pires,[Universidade Federal de Alagoas].* ")

with st.expander("Informações Adicionais"):
    st.markdown('- Esse web app foi feito para projetar o uso do Bombeio Mecânico (BM) .')
    st.markdown('- Esse web app foi desenvolvido com base nas equações do livro Petroleum Production Engineering Second Edition .')
    st.markdown('- Referência : Guo, Boyun, Xinghui Liu, e Xuehao Tan. Petroleum Production Engineering. 2ª ed., Gulf Professional Publishing, 2017.')
    st.markdown("[Clique aqui para acessar o Google](https://www.amazon.com/Petroleum-Production-Engineering-Boyun-Guo/dp/0128093749)")

st.markdown(
    """
O trabalho a ser realizado envolve o desenvolvimento de um projeto de Bombeio Mecânico (BM) utilizando Python,
com uma interface interativa criada em Streamlit. 
O objetivo é modelar e automatizar o processo, 
criando uma planilha geral dentro do ambiente de desenvolvimento, 
que abrange desde a definição dos parâmetros de projeto até a resolução de exercícios específicos alocados nos slides de BM. 
A interface permitirá visualizar os cálculos e a carta dinamométrica do sistema de forma dinâmica e intuitiva, 
facilitando a análise e a tomada de decisões. Este projeto visa oferecer uma ferramenta customizável e de fácil uso para otimizar as operações de produção de petróleo, 
integrando cálculos complexos com visualizações interativas.

"""
)

col1,col2,col3 = st.columns(3)
with col1:
    st.image('cavalo.png')
with col2 : 
    st.image('tag.png')
with col3 :
    st.image('carta.png')