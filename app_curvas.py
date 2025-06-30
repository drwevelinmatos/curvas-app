import streamlit as st
import numpy as np
import pandas as pd
from scipy import stats
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="App Curvas 2.0", layout="wide")

# Título e descrição
st.title("App Curvas 2.0 - Avaliação de Crescimento")
st.markdown("""
**Aplicativo clínico para avaliação de crescimento e desenvolvimento (0-18 anos)**  
Baseado nas curvas da OMS com extensões para prematuros e síndrome de Down.
""")

# --- Entradas de Dados ---
with st.sidebar:
    st.header("Dados do Paciente")
    
    # Sexo
    sexo = st.radio("Sexo", ["Masculino", "Feminino"])
    
    # Idade
    col1, col2 = st.columns(2)
    with col1:
        anos = st.number_input("Anos", min_value=0, max_value=18, value=5)
    with col2:
        meses = st.number_input("Meses", min_value=0, max_value=11, value=0)
    idade_total_meses = anos * 12 + meses
    
    # Medidas antropométricas
    peso = st.number_input("Peso (kg)", min_value=0.1, value=20.0)
    estatura = st.number_input("Estatura (cm)", min_value=10.0, value=110.0)
    perimetro_cefalico = st.number_input("Perímetro Cefálico (cm)", min_value=10.0, value=50.0)
    
    # Altura dos pais
    estatura_pai = st.number_input("Estatura do Pai (cm)", min_value=100.0, value=175.0)
    estatura_mae = st.number_input("Estatura da Mãe (cm)", min_value=100.0, value=160.0)
    
    # Idade óssea
    col3, col4 = st.columns(2)
    with col3:
        anos_osso = st.number_input("Idade Óssea (Anos)", min_value=0, max_value=18, value=5)
    with col4:
        meses_osso = st.number_input("Idade Óssea (Meses)", min_value=0, max_value=11, value=0)
    idade_ossea_total = anos_osso * 12 + meses_osso
    
    # Grupos especiais
    grupo_especial = st.radio("Grupo Especial", ["Nenhum", "Prematuro", "Síndrome de Down"])
    semanas_prematuridade = None
    if grupo_especial == "Prematuro":
        semanas_prematuridade = st.number_input("Idade Gestacional ao Nascer (semanas)", min_value=22, max_value=37, value=32)

# --- Cálculos Principais ---
# Cálculo de IMC
imc = peso / ((estatura/100) ** 2)

# Estrutura de dados para armazenar tabelas LMS da OMS (exemplo simplificado)
oms_lms_data = {
    "masculino": {
        "peso": pd.DataFrame({
            "idade_meses": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "L": [0.3487]*13,
            "M": [3.3464, 4.4709, 5.5675, 6.3762, 7.0023, 7.5105, 7.934, 8.297, 8.6151, 8.9014, 9.1649, 9.4122, 9.6479],
            "S": [0.14602]*13
        }),
        "estatura": pd.DataFrame({
            "idade_meses": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "L": [1]*13,
            "M": [49.8842, 54.7244, 58.4249, 61.4292, 63.886, 65.9026, 67.6236, 69.1645, 70.5994, 71.9634, 73.2652, 74.5073, 75.6878],
            "S": [0.0364]*13
        }),
        "imc": pd.DataFrame({
            "idade_meses": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "L": [1]*13,
            "M": [13.4, 14.1, 14.5, 14.8, 15.1, 15.3, 15.5, 15.7, 15.9, 16.1, 16.3, 16.5, 16.7],
            "S": [0.1]*13
        }),
        "pc": pd.DataFrame({
            "idade_meses": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "L": [1]*13,
            "M": [34.5, 37.1, 39.1, 40.5, 41.7, 42.7, 43.6, 44.4, 45.1, 45.7, 46.3, 46.8, 47.3],
            "S": [0.04]*13
        })
    },
    "feminino": {
        "peso": pd.DataFrame({
            "idade_meses": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "L": [0.3809]*13,
            "M": [3.2322, 4.1873, 5.1282, 5.8458, 6.4237, 6.8985, 7.297, 7.6456, 7.958, 8.2429, 8.5071, 8.7551, 8.9885],
            "S": [0.14171]*13
        }),
        "estatura": pd.DataFrame({
            "idade_meses": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "L": [1]*13,
            "M": [49.1477, 53.6872, 57.0673, 59.8029, 62.0899, 64.0413, 65.7263, 67.2243, 68.5994, 69.8949, 71.131, 72.3127, 73.4443],
            "S": [0.03557]*13
        }),
        "imc": pd.DataFrame({
            "idade_meses": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "L": [1]*13,
            "M": [13.3, 13.9, 14.3, 14.6, 14.9, 15.1, 15.3, 15.5, 15.7, 15.9, 16.1, 16.3, 16.5],
            "S": [0.1]*13
        }),
        "pc": pd.DataFrame({
            "idade_meses": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "L": [1]*13,
            "M": [33.9, 36.6, 38.5, 39.9, 41.1, 42.1, 43, 43.8, 44.5, 45.1, 45.7, 46.2, 46.7],
            "S": [0.04]*13
        })
    }
}

# Função para calcular Z-score usando interpolação LMS
def calcular_z_score_oms(valor, parametro, sexo, idade_meses):
    df = oms_lms_data[sexo][parametro]
    l = np.interp(idade_meses, df['idade_meses'], df['L'])
    m = np.interp(idade_meses, df['idade_meses'], df['M'])
    s = np.interp(idade_meses, df['idade_meses'], df['S'])
    if l == 0:
        z = (np.log(valor / m)) / s
    else:
        z = ((valor / m) ** l - 1) / (l * s)
    return z

# Função para calcular percentil a partir do Z-score
def calcular_percentil(z_score):
    return stats.norm.cdf(z_score) * 100

# Cálculo do Alvo Parental
def calcular_alvo_parental(estatura_pai, estatura_mae, sexo):
    if sexo == "Masculino":
        return (estatura_mae + estatura_pai + 13) / 2
    else:
        return (estatura_mae + estatura_pai - 13) / 2

alvo_parental = calcular_alvo_parental(estatura_pai, estatura_mae, sexo)
canal_familiar = (alvo_parental - 10, alvo_parental + 10)

# Cálculo dos Z-scores
sexo_code = "masculino" if sexo == "Masculino" else "feminino"
z_peso = calcular_z_score_oms(peso, "peso", sexo_code, idade_total_meses)
z_estatura = calcular_z_score_oms(estatura, "estatura", sexo_code, idade_total_meses)
z_pc = calcular_z_score_oms(perimetro_cefalico, "pc", sexo_code, idade_total_meses)
z_imc = calcular_z_score_oms(imc, "imc", sexo_code, idade_total_meses)

# Diagnósticos
st.header("Resultados da Avaliação")
st.subheader("Indicadores de Crescimento")
resultados = {
    "Parâmetro": ["Peso/Idade", "Estatura/Idade", "PC/Idade", "IMC/Idade"],
    "Z-score": [z_peso, z_estatura, z_pc, z_imc],
    "Percentil (%)": [calcular_percentil(z_peso), calcular_percentil(z_estatura), calcular_percentil(z_pc), calcular_percentil(z_imc)]
}
st.table(pd.DataFrame(resultados))

st.subheader("Diagnósticos")
diagnosticos = []
if z_estatura < -2:
    diagnosticos.append(f"**Baixa estatura** (Z = {z_estatura:.2f})")
if idade_total_meses < 60:
    if z_imc > 3:
        diagnosticos.append(f"**Obesidade** (IMC Z = {z_imc:.2f})")
    elif z_imc > 2:
        diagnosticos.append(f"**Sobrepeso** (IMC Z = {z_imc:.2f})")
else:
    if z_imc > 2:
        diagnosticos.append(f"**Obesidade** (IMC Z = {z_imc:.2f})")
    elif z_imc > 1:
        diagnosticos.append(f"**Sobrepeso** (IMC Z = {z_imc:.2f})")

if diagnosticos:
    for diag in diagnosticos:
        st.markdown(f"- {diag}")
else:
    st.markdown("Nenhum diagnóstico crítico detectado.")

# Alvo Parental
st.subheader("Alvo Parental")
st.markdown(f"""
- **Alvo Parental Calculado:** {alvo_parental:.1f} cm  
- **Canal Familiar:** {canal_familiar[0]:.1f} cm a {canal_familiar[1]:.1f} cm  
- **Percentil Atual vs. Alvo:** {calcular_percentil(z_estatura):.1f}% (Relacionar com curva)
""")

# Idade Óssea
diferenca_idade = idade_ossea_total - idade_total_meses
st.subheader("Avaliação de Idade Óssea")
st.markdown(f"""
- **Diferença Idade Óssea-Cronológica:** {diferenca_idade/12:.1f} anos  
- **Interpretação:** {'Atraso' if diferenca_idade < -6 else 'Avanço' if diferenca_idade > 6 else 'Adequada'}  
- **Relação com Crescimento:** {'Potencial recuperação estatural' if diferenca_idade < -6 else 'Redução potencial crescimento' if diferenca_idade > 6 else 'Normal'}
""")

# Curvas de Fenton para prematuros (exemplo simplificado)
fenton_data = {
    "peso": pd.DataFrame({
        "idade_gestacional_semanas": [24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40],
        "P3": [500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100],
        "P50": [600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200],
        "P97": [700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200, 2300]
    })
}

def calcular_z_score_fenton(valor, parametro, idade_gestacional_semanas):
    df = fenton_data[parametro]
    p50 = np.interp(idade_gestacional_semanas, df['idade_gestacional_semanas'], df['P50'])
    sd = (df['P97'] - df['P3']) / (2 * 1.96)
    z = (valor - p50) / sd
    return z

# Avaliação para prematuros
if grupo_especial == "Prematuro" and semanas_prematuridade:
    idade_corrigida_semanas = semanas_prematuridade + (idade_total_meses * 4.345)
    if idade_corrigida_semanas <= 50:
        z_peso = calcular_z_score_fenton(peso*1000, "peso", idade_corrigida_semanas)  # peso em gramas
        z_estatura = calcular_z_score_fenton(estatura, "peso", idade_corrigida_semanas)  # exemplo simplificado
        z_pc = calcular_z_score_fenton(perimetro_cefalico, "peso", idade_corrigida_semanas)  # exemplo simplificado
    else:
        z_peso = calcular_z_score_oms(peso, "peso", sexo_code, idade_total_meses)

# Visualização gráfica das curvas
def plotar_curva(parametro, sexo, idade_meses, valor_paciente):
    fig = go.Figure()
    df = oms_lms_data[sexo][parametro]
    fig.add_trace(go.Scatter(x=df['idade_meses'], y=df['M'], line=dict(dash='dash'), name='P50'))
    fig.add_trace(go.Scatter(x=df['idade_meses'], y=df['M'] - 2*df['S'], line=dict(dash='dot'), name='P3'))
    fig.add_trace(go.Scatter(x=df['idade_meses'], y=df['M'] + 2*df['S'], line=dict(dash='dot'), name='P97'))
    fig.add_trace(go.Scatter(x=[idade_meses], y=[valor_paciente], mode='markers', name='Paciente', marker=dict(size=12, color='red')))
    fig.update_layout(title=f"Curva de {parametro.capitalize()} - {sexo.capitalize()}", xaxis_title="Idade (meses)", yaxis_title=parametro.capitalize())
    return fig

st.subheader("Visualização Gráfica")
st.plotly_chart(plotar_curva("estatura", sexo_code, idade_total_meses, estatura))

# Diagnósticos e condutas para Síndrome de Down
if grupo_especial == "Síndrome de Down":
    st.subheader("Avaliação para Síndrome de Down")
    st.markdown("""
    - Utilizar curvas específicas para Síndrome de Down
    - Avaliar risco de obesidade e hipotireoidismo
    """)

# Notas de Rodapé
st.caption("""
**Fontes:**  
Curvas OMS | Curvas Fenton | Diagnósticos clínicos
*Resultados baseados em modelos estatísticos - avaliação clínica complementar é essencial*
""")
