# app_curvas_streamlit.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import os

# Garantir scipy instalado
try:
    from scipy.stats import norm
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "scipy"])
    from scipy.stats import norm

# ====== Carregar Curvas OMS (exemplo: altura meninos 0-5, 5-19) ======
@st.cache_data
def load_curves():
    curves = {}
    base = "https://raw.githubusercontent.com/growthcharts/WHO/master/data/"
    curves['height_boys_0_5'] = pd.read_csv(base + "height_for_age_boys_0-5.csv")
    curves['height_boys_5_19'] = pd.read_csv(base + "height_for_age_boys_5-19years.csv")
    curves['height_girls_0_5'] = pd.read_csv(base + "height_for_age_girls_0-5.csv")
    curves['height_girls_5_19'] = pd.read_csv(base + "height_for_age_girls_5-19years.csv")
    curves['bmi_boys_0_5'] = pd.read_csv(base + "bmi_for_age_boys_0-5.csv")
    curves['bmi_boys_5_19'] = pd.read_csv(base + "bmi_for_age_boys_5-19years.csv")
    curves['bmi_girls_0_5'] = pd.read_csv(base + "bmi_for_age_girls_0-5.csv")
    curves['bmi_girls_5_19'] = pd.read_csv(base + "bmi_for_age_girls_5-19years.csv")
    return curves

curves = load_curves()

# ====== Funções de cálculo ======
def calcular_idade(data_nasc, data_medida):
    nasc = datetime.strptime(data_nasc, "%Y-%m-%d").date()
    medida = datetime.strptime(data_medida, "%Y-%m-%d").date()
    dias = (medida - nasc).days
    anos = dias // 365
    meses = (dias % 365) // 30
    idade_anos = dias / 365.25
    idade_meses = dias // 30
    return anos, meses, idade_anos, idade_meses

def calcular_percentil_zscore(idade, valor, parametro, sexo):
    # Define curva
    if parametro == "estatura":
        if idade <= 5:
            curva = curves[f'height_{sexo}_0_5']
            idade_col = 'Month'
            idade_ref = idade * 12
        else:
            curva = curves[f'height_{sexo}_5_19']
            idade_col = 'Age'
            idade_ref = idade
    elif parametro == "imc":
        if idade <= 5:
            curva = curves[f'bmi_{sexo}_0_5']
            idade_col = 'Month'
            idade_ref = idade * 12
        else:
            curva = curves[f'bmi_{sexo}_5_19']
            idade_col = 'Age'
            idade_ref = idade
    else:
        return None, None
    # Linha mais próxima
    idx = (curva[idade_col] - idade_ref).abs().idxmin()
    linha = curva.loc[idx]
    L, M, S = linha['L'], linha['M'], linha['S']
    if L != 0:
        z = ((valor / M) ** L - 1) / (L * S)
    else:
        z = (np.log(valor / M)) / S
    percentil = norm.cdf(z) * 100
    return percentil, z

def alvo_parental(altura_mae, altura_pai, sexo):
    correcao = 13 if sexo == "boys" else -13
    alvo_central = (altura_mae + altura_pai + correcao) / 2
    return alvo_central - 8.5, alvo_central + 8.5

def diagnostico(percentil_est, z_imc, alvo, idade_ossea, idade_cronologica):
    diag = []
    rec = []
    if percentil_est is not None:
        if percentil_est < 3:
            diag.append("Baixa estatura")
            rec.append("Investigar causas endócrinas, genéticas ou nutricionais")
        elif percentil_est > 97:
            diag.append("Alta estatura")
            rec.append("Avaliar puberdade precoce ou síndromes")
    if z_imc is not None:
        if z_imc > 2:
            diag.append("Sobrepeso/Obesidade")
            rec.append("Orientar hábitos alimentares e atividade física")
        elif z_imc < -2:
            diag.append("Baixo peso")
            rec.append("Avaliar ingestão calórica e possíveis patologias")
    if alvo and percentil_est is not None:
        alvo_min, alvo_max = alvo
        if percentil_est < 25 and (alvo_min + alvo_max) / 2 > 50:
            diag.append("Desvio do padrão familiar")
            rec.append("Sugerir investigação adicional")
    if idade_ossea is not None and idade_cronologica is not None:
        dif = idade_ossea - idade_cronologica
        if dif < -2:
            diag.append("Atraso de idade óssea >2 anos")
            rec.append("Solicitar dosagens hormonais e USG ovários/testículos")
        elif dif > 2:
            diag.append("Avanço de idade óssea >2 anos")
            rec.append("Avaliar puberdade precoce")
    return diag, rec

# ====== Streamlit App ======
st.set_page_config(page_title="App Clínico Curvas de Crescimento", layout="wide")
st.title("App Clínico - Curvas de Crescimento e Desenvolvimento")

# Simples "banco de dados" em sessão
if "pacientes" not in st.session_state:
    st.session_state["pacientes"] = []
if "medidas" not in st.session_state:
    st.session_state["medidas"] = []

# Tabs
aba = st.tabs(["Cadastro Paciente", "Registro Medidas", "Relatório e Gráficos"])

# === 1. Cadastro Paciente ===
with aba[0]:
    st.header("Cadastro de Paciente")
    with st.form("cad_paciente"):
        nome = st.text_input("Nome completo")
        data_nasc = st.date_input("Data de nascimento", value=date(2020,1,1), format="YYYY-MM-DD")
        sexo = st.selectbox("Sexo", ["Masculino", "Feminino"])
        prematuro = st.checkbox("Prematuro?")
        idade_gestacional = st.number_input("Idade gestacional ao nascer (semanas)", min_value=20, max_value=44, value=40) if prematuro else 40
        sindrome_down = st.checkbox("Síndrome de Down?")
        altura_mae = st.number_input("Altura da mãe (cm)", min_value=100.0, max_value=220.0, value=160.0)
        altura_pai = st.number_input("Altura do pai (cm)", min_value=100.0, max_value=220.0, value=170.0)
        submitted = st.form_submit_button("Salvar Paciente")
        if submitted:
            st.session_state["pacientes"].append({
                "nome": nome,
                "data_nasc": data_nasc.strftime("%Y-%m-%d"),
                "sexo": "boys" if sexo == "Masculino" else "girls",
                "prematuro": prematuro,
                "idade_gestacional": idade_gestacional,
                "sindrome_down": sindrome_down,
                "altura_mae": altura_mae,
                "altura_pai": altura_pai
            })
            st.success("Paciente cadastrado!")

    st.subheader("Pacientes cadastrados")
    if st.session_state["pacientes"]:
        st.dataframe(pd.DataFrame(st.session_state["pacientes"]))

# === 2. Registro de Medidas ===
with aba[1]:
    st.header("Registro de Medidas")
    if not st.session_state["pacientes"]:
        st.warning("Cadastre pelo menos um paciente primeiro.")
    else:
        nomes = [p["nome"] for p in st.session_state["pacientes"]]
        idx_paciente = st.selectbox("Escolha o paciente", range(len(nomes)), format_func=lambda i: nomes[i])
        paciente = st.session_state["pacientes"][idx_paciente]
        with st.form("reg_medidas"):
            data_medida = st.date_input("Data da medição", value=date.today(), format="YYYY-MM-DD")
            peso = st.number_input("Peso (kg)", min_value=1.0, max_value=200.0, value=20.0)
            estatura = st.number_input("Estatura (cm)", min_value=30.0, max_value=220.0, value=110.0)
            pc = st.number_input("Perímetro cefálico (cm)", min_value=20.0, max_value=70.0, value=50.0)
            idade_ossea = st.number_input("Idade óssea (anos)", min_value=0.0, max_value=20.0, value=0.0, step=0.1)
            submitted2 = st.form_submit_button("Salvar Medida")
            if submitted2:
                st.session_state["medidas"].append({
                    "paciente": idx_paciente,
                    "data_medida": data_medida.strftime("%Y-%m-%d"),
                    "peso": peso,
                    "estatura": estatura,
                    "pc": pc,
                    "idade_ossea": idade_ossea if idade_ossea > 0 else None
                })
                st.success("Medição registrada!")
        # Histórico
        st.subheader("Histórico de Medidas")
        medidas_pac = [m for m in st.session_state["medidas"] if m["paciente"] == idx_paciente]
        if medidas_pac:
            st.dataframe(pd.DataFrame(medidas_pac))

# === 3. Relatório e Gráficos ===
with aba[2]:
    st.header("Relatório Clínico e Gráficos")
    if not st.session_state["pacientes"] or not st.session_state["medidas"]:
        st.warning("Cadastre paciente e medidas primeiro.")
    else:
        nomes = [p["nome"] for p in st.session_state["pacientes"]]
        idx_paciente = st.selectbox("Selecione o paciente", range(len(nomes)), format_func=lambda i: nomes[i], key="rel_paciente")
        paciente = st.session_state["pacientes"][idx_paciente]
        medidas_pac = [m for m in st.session_state["medidas"] if m["paciente"] == idx_paciente]
        if not medidas_pac:
            st.warning("Registre pelo menos uma medida para este paciente.")
        else:
            medidas_df = pd.DataFrame(medidas_pac)
            medidas_df = medidas_df.sort_values("data_medida")
            ultima = medidas_df.iloc[-1]
            anos, meses, idade_anos, idade_meses = calcular_idade(paciente["data_nasc"], ultima["data_medida"])
            imc = ultima["peso"] / ((ultima["estatura"] / 100) ** 2)
            alvo = alvo_parental(paciente["altura_mae"], paciente["altura_pai"], paciente["sexo"])
            perc_est, z_est = calcular_percentil_zscore(idade_anos, ultima["estatura"], "estatura", paciente["sexo"])
            perc_imc, z_imc = calcular_percentil_zscore(idade_anos, imc, "imc", paciente["sexo"])
            diag, rec = diagnostico(perc_est, z_imc, alvo, ultima["idade_ossea"], idade_anos)
            # Relatório
            st.markdown(f"**Paciente:** {paciente['nome']}  \n"
                        f"**Idade:** {anos} anos e {meses} meses  \n"
                        f"**Sexo:** {'Masculino' if paciente['sexo']=='boys' else 'Feminino'}  \n"
                        f"**Prematuro:** {'Sim' if paciente['prematuro'] else 'Não'}  \n"
                        f"**Síndrome de Down:** {'Sim' if paciente['sindrome_down'] else 'Não'}  \n")
            st.markdown(f"**Última Medida ({ultima['data_medida']}):**  \n"
                        f"Peso: {ultima['peso']} kg  \n"
                        f"Estatura: {ultima['estatura']} cm (Percentil: {perc_est:.1f})  \n"
                        f"IMC: {imc:.1f} (Z-score: {z_imc:.2f})  \n"
                        f"Perímetro cefálico: {ultima['pc']} cm  \n"
                        f"Idade óssea: {ultima['idade_ossea'] if ultima['idade_ossea'] else 'N/A'} anos  \n"
                        f"Alvo parental: {alvo[0]:.1f} - {alvo[1]:.1f} cm")
            # Diagnóstico
            if diag or rec:
                st.markdown("**Diagnóstico:**")
                for d in diag:
                    st.markdown(f"- {d}")
                st.markdown("**Condutas/Recomendações:**")
                for r in rec:
                    st.markdown(f"- {r}")
            else:
                st.success("Sem alterações clínicas relevantes detectadas.")
            # Gráficos
            st.subheader("Evolução de Estatura e Peso")
            st.line_chart(medidas_df.set_index("data_medida")[["estatura", "peso"]])
            st.subheader("Histórico Completo")
            st.dataframe(medidas_df)

# Fim do app
