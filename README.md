# Projeto BM

Aplicação acadêmica em Python e Streamlit para dimensionamento simplificado de uma
unidade convencional de bombeio mecânico. Autoria original: Nuno Henrique Albuquerque
Pires, Engenharia de Petróleo, Universidade Federal de Alagoas.

## Executar

Requer Python 3.11 ou superior e Streamlit 1.66 ou superior. No PowerShell, a partir desta pasta:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

A entrada original `1_⚙BM.py` continua funcionando, como atalho para a mesma interface.
As dependências têm intervalos de compatibilidade; não há lockfile de instalação.

## Uso

1. Preencha as abas **Poço e fluido**, **Unidade e hastes** e **Critérios de cálculo**.
2. Clique em **Calcular dimensionamento**. Alterações no formulário só são aplicadas
   após o envio; a primeira abertura usa um exemplo preenchido.
3. Consulte o resumo, as capacidades nominais e os alertas de hastes/velocidade.
4. Compare as cartas ideal e aproximada e consulte a memória de cálculo.
5. Em **Exportar relatório**, prepare e baixe o PDF e o Excel. Os downloads permanecem
   disponíveis até os dados enviados mudarem.

O aplicativo usa unidades de campo: in, ft, lbf, psi, ciclos/min, STB/d e hp. A eficiência
é apresentada em porcentagem e convertida em fração antes dos cálculos.

## Organização

```text
app.py                   Interface, formulário e navegação
bm.py                    Entradas, cálculos, capacidades e ciclo dinamométrico
reports.py               Gráfico e exportações PDF/Excel
1_⚙BM.py                 Entrada original, compatível com a nova interface
.streamlit/config.toml   Tema visual
visuals.py               Origem dos dados e leitura visual do dimensionamento
assets/pumping_system.html  Animação SVG interativa, sem recursos externos
assets/pump_motion.js     Geometria articulada da ilustração
tests/                   Regressões numéricas e testes da interface
```

Os cálculos não dependem de Streamlit, pandas ou estado global. Relatórios e tela
consomem os mesmos resultados. Os arquivos são gerados em memória, sem banco de dados.

## Experiência visual

- **Sistema em movimento:** unidade detalhada com motor, correia, redutor,
  contrapeso, biela, balancim, cabo, haste e cabeça do poço. O mecanismo desenhado
  resolve a interseção entre duas circunferências para manter a biela e o braço
  traseiro rígidos durante todo o ciclo. A geometria visual é fixa e ilustrativa;
  não representa um desenho dimensional da unidade escolhida.
- **Bomba ampliada:** corte da camisa e do pistão com válvulas fixa e de passeio.
  O ciclo ideal mostra admissão na subida e passagem pelo pistão na descida.
  As duas vistas usam a mesma fase normalizada, mas têm escalas próprias; não há
  propagação de ondas, defasagem elástica nem simulação de pressão, gás ou defeitos.
  A sequência pressupõe bomba cheia, independentemente da eficiência informada.
- **Controles do movimento:** pausa, câmera lenta em 0,25× e seleção manual de um
  ponto do ciclo. A cadência em 1× utiliza N do projeto; os valores de S, Sp e
  profundidade são mostrados nos desenhos, sem definir suas amplitudes gráficas.
  Há navegação por teclado, preferência por movimento reduzido e pausa fora de
  vista. Em telas estreitas, as duas vistas são empilhadas.
- **Origem dos dados:** fontes sugeridas por parâmetro (registros do poço, análise
  do óleo, placa, desenho dimensional e especificações). Os valores iniciais são
  ilustrativos, não importados de um caso real documentado.
- **Dos dados aos resultados:** cartões conectam profundidade, fluido e dimensões
  às estimativas de carga, produção e potência.
- **Cartas comparadas:** envoltória ideal tracejada e ciclo de superfície aproximado
  em amarelo, com sentidos de subida/descida e capacidade estrutural da TAG. As duas
  curvas usam as entradas enviadas no formulário. PDF e Excel incluem a comparação;
  a planilha também contém os 721 pontos do ciclo aproximado.

A animação é HTML/SVG local, sem serviços, imagens remotas ou novas dependências de
JavaScript. O conteúdo de `st.iframe` é gerado a partir do template do repositório e
de números validados; não aceita HTML informado pelo usuário.

## Modelo e equações

Modelo concentrado, com coluna uniforme de hastes e óleo homogêneo. Não inclui ondas
elásticas, gás livre, água, desvio do poço ou um modelo de atrito viscoso. A comparação
de capacidades é uma verificação preliminar; não seleciona um modelo comercial.

Símbolos: `D` = profundidade da bomba; `H` = profundidade do nível dinâmico;
`c` = raio da manivela; `h` = comprimento da biela; `d1/d2` = braços traseiro/dianteiro
do balancim; `E` = módulo de elasticidade; `L` = limite de aceleração em múltiplos de g.

| Grandeza | Equação |
| --- | --- |
| Densidade relativa | `SG = 141,5 / (API + 131,5)` |
| Áreas de haste e pistão | `Ar = π dr²/4`; `Ap = π dp²/4` |
| Área metálica da tubulação | `At = π (De² − Di²)/4` |
| Peso das hastes | `Wr = γaço D Ar / 144` |
| Empuxo | `Ef = 62,4 SG Wr / γaço` |
| Peso imerso | `Wrf = Wr − Ef` |
| Carga hidrostática | `Fo = 62,4 SG D Ap / 144` |
| Curso de superfície | `S = 2 c d2/d1` |
| Velocidade limite | `Nlim = √[70471,2 L / (S (1+c/h))]` |
| Esforços dinâmicos | `Fup = Wr S N² (1+c/h)/70471,2`; `Fdown = Wr S N² (1−c/h)/70471,2` |
| Cargas | `PPRL = Wrf + Fo + Fup`; `MPRL = Wrf − Fdown` |
| Alongamentos | `er = 12 D Fo/(E Ar)`; `et = 12 D Fo/(E At)` ou zero quando ancorada |
| Sobrecurso | `eo = 12 D Fup/(E Ar)` |
| Curso efetivo | `Sp = S − er − et + eo` |
| Contrabalanceio | `CBE = (PPRL + MPRL)/2` |
| Torque máximo estimado | `Tpeak = (PPRL − MPRL) S/4` |
| Tensões | `σmax = PPRL/Ar`; `σmin = MPRL/Ar` |
| Goodman modificado | `σadm = SF (Tmaterial/4 + 0,5625 σmin)` |
| Deslocamento teórico | `PD = (1440/9702) Ap Sp N` |
| Vazão em condições de tanque | `q = PD Ev/Bo` |
| Elevação líquida | `Ln = H + pth/[(62,4/144) SG]` |
| Potência hidráulica empírica | `Ph = 7,36×10⁻⁶ q SG Ln` |
| Potência de atrito | `Pf = 6,31×10⁻⁷ Wr S N` |
| Potência do motor | `Pmotor = Fmotor (Ph + Pf)` |

A carga hidrostática adota a coluna completa até `D`; o nível dinâmico `H` entra apenas
na elevação líquida, conforme a simplificação original. A potência hidráulica preserva
a correlação empírica em vazão de tanque das referências, sem conversão adicional por
Bo. O fator de serviço `SF`, de 0 a 1, reduz a tensão admissível; a margem do motor é
independente e maior ou igual a 1. A resistência à tração é uma propriedade informada
do material. Não se promete vida útil em ciclos. Carga mínima negativa é indicada
como compressão, fora do domínio da verificação de Goodman usada aqui.

A carta ideal é uma **envoltória retangular de superfície**, com `S`, `PPRL` e
`MPRL`. A curva aproximada acrescenta transferência elástica e inércia em um ciclo
concentrado. Nenhuma das duas é uma medição ou uma carta de fundo. `Sp` pode superar
`S` devido ao sobrecurso e é usado na vazão, não no curso nominal da unidade.

### Ciclo dinamométrico aproximado

Para `θ` entre 0 e 2π, `r = c/h` e `δ = er + et`, usamos:

- `x(θ) = S/2 (1 − cos θ) + r S/8 (1 − cos 2θ)`.
- `Fd(θ) = Wr S N²/70471,2 (cos θ + r cos 2θ)`, coerente com a segunda
  derivada de `x`; `N` é a velocidade efetivamente utilizada no dimensionamento.
- Na subida, `u = limitar(x/δ, 0, 1)`; na descida,
  `u = limitar(1 − (S−x)/δ, 0, 1)`.
- `F(θ) = Wrf + Fo u + Fd(θ)`.

A transferência linear de `Fo` ao longo do alongamento total é uma aproximação
elástica. A carga não é normalizada para atingir PPRL/MPRL, e não se adiciona ruído
para imitar sensores. Os extremos desse ciclo não substituem as verificações de
carga, torque ou tensão do dimensionamento. Se `δ ≥ S`, o ciclo aproximado é omitido
com aviso, mantendo a envoltória e os demais resultados disponíveis.

A forma depende de profundidade, óleo, diâmetros, ancoragem, módulo elástico,
geometria e velocidade. Neste modelo, eficiência volumétrica, Bo, pressão na cabeça
e nível dinâmico não entram no traçado: a carga de fluido mantém a hipótese de coluna
completa até a bomba. Não há diagnóstico de enchimento, gás, pancada de fluido ou
válvulas. Para uma carta real, são necessárias medições sincronizadas de carga e
posição na haste; para propagá-las ao fundo, seria necessário outro modelo.

A referência da Echometer explica a distinção entre cartas de superfície/fundo e o
papel do alongamento. As equações acima são uma construção didática deste projeto,
sem implementar a equação de ondas ou reproduzir o algoritmo do QRod.

### TAG

`C-456D-256-120` significa: unidade convencional, torque nominal do redutor de
456.000 lbf·in, redutor duplo, capacidade estrutural de 25.600 lbf e curso máximo de
120 in. A aplicação compara **carga, torque e curso separadamente**. Não gera uma TAG
fictícia nem rejeita uma unidade maior apenas por diferença no texto.

### Correções em relação à versão original

- TAG validada integralmente; entrada inválida apresenta mensagem sem interromper a aplicação com traceback.
- Áreas separadas de diâmetros; a área metálica utiliza os dois diâmetros da tubulação.
- Alongamentos usam carga de fluido; o sobrecurso dinâmico é somado ao curso efetivo.
- Torque usa curso de superfície e vazão usa a área do pistão uma única vez.
- Tensão admissível usa a resistência do material e um fator de serviço próprio.
- Elevação líquida e potência usam densidade relativa, sem confundir viscosidade com densidade.
- Retirada da estimativa de viscosidade sem temperatura e do campo Rs sem efeito no modelo corrigido.
- PDF com quebras automáticas e unidades; Excel com entradas, resultados, capacidades, método e gráfico.
- Dependências sem uso (`scikit-learn` e `plotly`) removidas.

## Verificar

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

O mecanismo visual também pode ser verificado com `node tests/test_motion.cjs`: o teste
percorre o ciclo completo e verifica comprimentos, fechamento e sequência de válvulas.

Os testes cobrem TAG inválida, capacidades maiores/menores, unidades, geometria,
fatores independentes, compressão, formulário, navegação e geração dos relatórios.

## Referências

- Guo, B.; Liu, X.; Tan, X. [Petroleum Production Engineering, 2ª ed., 2017](https://www.sciencedirect.com/book/9780128093740/petroleum-production-engineering). Referência original do projeto.
- Merey, Ş. (2020). [Comparison of Sucker Rod Pump and Progressive Cavity Pump Performances in Batı Raman Heavy Oil Field of Turkey](https://doi.org/10.18466/cbayarfbe.646805), tabela 3. Equações do modelo concentrado.
- Tenaris. [Sucker Rods Catalogue](https://www.tenaris.com/media/ugtdh5xw/suckerrodstechnicalcatalogue-6.pdf), p. 69. Goodman modificado e fatores de serviço.
- Sunnda. [Composite Catalog](https://www.sunnda.com/catalog/sunnda-composite-catalog.pdf), p. 60. Capacidades nominais de unidades convencionais.

- Echometer. [QRod Help and User Guide](https://www.echometer.com/Portals/0/Quick%20Reference%20Guides/QRod%20Help%20and%20User%20Guide.pdf). Cartas de superfície e fundo, rigidez e alongamento.

- SLB. [The Defining Series: Rod Pump Systems](https://www.slb.com/resource-library/oilfield-review/defining-series/defining-rod-pumps). Componentes e sequência ideal das válvulas na animação.
