import streamlit as st
import pandas as pd
import json
import os
import re
import subprocess
import webbrowser
import sys
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="L'Idea Smart Hub", page_icon="🧠", layout="wide")

# CAMINHOS PADRÃO
ROOT_DIR = "."
LOCAL_EXCEL_FOLDER = os.path.join(ROOT_DIR, "entrada_excel") 
JS_DB_FILE = os.path.join(ROOT_DIR, "lidea_db.js")
CORE_CONTROLLER_FILE = os.path.join(ROOT_DIR, "core_controller.js")

# --- SIDEBAR: CONFIGURAÇÃO ---
st.sidebar.header("☁️ Configuração")
default_drive = os.path.join(os.path.expanduser("~"), "Google Drive")
if not os.path.exists(default_drive): default_drive = "G:\\Meu Drive"

drive_path_input = st.sidebar.text_input("Caminho da Pasta:", value=default_drive)
use_drive_mode = st.sidebar.checkbox("Ler desta pasta (Drive/Local)", value=True)

# --- CORE: FUNÇÕES DE LIMPEZA E EXTRAÇÃO ---
def clean_currency(value):
    if pd.isna(value) or str(value).strip() == '': return 0.0
    s = str(value)
    s = re.sub(r'[^\d,-]', '', s)
    s = s.replace(',', '.')
    try: return float(s)
    except: return 0.0

def find_value_in_dataframe(df, search_term, year_keyword="2025"):
    try:
        mask = df.apply(lambda x: x.astype(str).str.contains(search_term, case=False, na=False))
        locations = mask.stack()[mask.stack()].index.tolist()
        if not locations: return 0.0
        row_idx = locations[0][0]
        
        target_cols = [c for c in df.columns if year_keyword in str(c)]
        val = 0.0
        if target_cols: val = df.loc[row_idx, target_cols[0]]
        else:
            cols_count = len(df.columns)
            if cols_count > 2: val = df.iloc[row_idx, 2]
            elif cols_count > 1: val = df.iloc[row_idx, 1]
        return clean_currency(val)
    except: return 0.0

# --- DATA ENGINE ---
def process_files(target_folder):
    if not os.path.exists(target_folder):
        return f"❌ A pasta não existe: {target_folder}"

    files = [f for f in os.listdir(target_folder) if f.endswith(".xlsx") and not f.startswith("~$")]
    if not files: return f"⚠️ Nenhum arquivo .xlsx encontrado em: {target_folder}"

    db = {
        "meta_info": {"periodo": "Smart Sync", "atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M")},
        "contabil": {"resumo": {"receita_bruta": 0, "lucro_operacional": 0}, "ativo": 0, "passivo": 0},
        "fiscal": {"total_impostos": 0},
        "dp": {"headcount": 142},
        "legal": {"status": "Regular"}
    }
    
    log = []
    log.append(f"📂 Processando {len(files)} arquivos...")

    for filename in files:
        filepath = os.path.join(target_folder, filename)
        try:
            xls = pd.ExcelFile(filepath)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name) 
                s_name = sheet_name.upper()
                
                if "DRE" in s_name or "RESULTADO" in s_name:
                    rec = find_value_in_dataframe(df, "RECEITA BRUTA OPERACIONAL")
                    luc = find_value_in_dataframe(df, "LUCRO LIQUIDO OPERACIONAL")
                    if rec > 0: db['contabil']['resumo']['receita_bruta'] = rec
                    if luc != 0: db['contabil']['resumo']['lucro_operacional'] = luc
                    if rec > 0: log.append(f"  ✅ DRE: {filename}")

                if "ATIVO" in s_name:
                    ativo = find_value_in_dataframe(df, "A T I V O")
                    if ativo == 0: ativo = find_value_in_dataframe(df, "TOTAL DO ATIVO")
                    if ativo > 0: db['contabil']['ativo'] = ativo

                if "FISCAL" in s_name or "IMPOSTO" in s_name or "FATURAMENTO" in s_name:
                    val = find_value_in_dataframe(df, "06-2025")
                    if val == 0: val = find_value_in_dataframe(df, "Total de Impostos")
                    if val > 0: db['fiscal']['total_impostos'] = val

        except Exception as e: log.append(f"  ❌ Erro {filename}: {str(e)}")

    js_content = f"const LIDEA_DATA = {json.dumps(db, indent=4)};"
    try:
        with open(JS_DB_FILE, "w", encoding="utf-8") as f: f.write(js_content)
        log.append("\n✨ Banco de Dados Atualizado!")
    except Exception as e: return f"❌ Erro JS: {e}"

    return "\n".join(log)

# --- SMART REPAIR (CORREÇÃO DE LINKS E SCRIPTS) ---
def repair_system_connections():
    # 1. Gera Controlador JS
    core_code = """
const SYSTEM_VERSION = 'v9_FULL_PATH';
function initSystem() {
    if (typeof LIDEA_DATA !== 'undefined') {
        localStorage.setItem('lidea_db_v1', JSON.stringify(LIDEA_DATA));
        localStorage.setItem('lidea_version', SYSTEM_VERSION);
    }
    renderPageData();
}
function renderPageData() {
    const db = JSON.parse(localStorage.getItem('lidea_db_v1') || '{}');
    if (!db.contabil) return;
    const fmt = (v) => v ? v.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL', maximumFractionDigits: 0}) : 'R$ 0';
    const map = {
        'val-receita': db.contabil.resumo.receita_bruta,
        'val-lucro': db.contabil.resumo.lucro_operacional,
        'val-impostos': db.fiscal.total_impostos,
        'val-headcount': db.dp.headcount,
        'kpi-lucro': db.contabil.resumo.lucro_operacional,
        'kpi-impostos': db.fiscal.total_impostos,
        'kpi-headcount': db.dp.headcount,
        'val-ativo': db.contabil.ativo
    };
    for (const [id, val] of Object.entries(map)) {
        const el = document.getElementById(id);
        if(el) el.innerText = fmt(val);
    }
    if (typeof lucide !== 'undefined') lucide.createIcons();
}
document.addEventListener('DOMContentLoaded', initSystem);
"""
    with open(CORE_CONTROLLER_FILE, "w", encoding="utf-8") as f: f.write(core_code)
    
    # 2. Correção de HTML (Scripts e Links)
    log = []
    patched_count = 0
    
    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                
                # Detecta se é Raiz ou Módulo
                is_module = "Modulos" in root or "Modulos" in file_path
                prefix = "../" if is_module else "./"
                
                # Define os links corretos para a Sidebar baseado na localização
                # Se estou no módulo: ../index.html | ./contabil.html
                # Se estou na raiz: ./index.html | ./Modulos/contabil.html
                if is_module:
                    link_home = "../index.html"
                    link_contabil = "./contabil.html"
                    link_fiscal = "./fiscal.html"
                    link_dp = "./dp.html"
                    link_legal = "./legal.html"
                else:
                    link_home = "./index.html"
                    link_contabil = "./Modulos/contabil.html"
                    link_fiscal = "./Modulos/fiscal.html"
                    link_dp = "./Modulos/dp.html"
                    link_legal = "./Modulos/legal.html"

                with open(file_path, "r", encoding="utf-8") as f: content = f.read()

                # --- FIX 1: SCRIPTS ---
                content = re.sub(r'<script src=".*?lidea_db.js"></script>', '', content)
                content = re.sub(r'<script src=".*?core_controller.js"></script>', '', content)
                content = re.sub(r'<script>[\s\S]*?localStorage\.getItem[\s\S]*?</script>', '', content)
                
                # --- FIX 2: LINKS DA SIDEBAR (Cirurgia com Regex) ---
                # Procura padrões antigos e substitui pelos calculados
                # Substitui link para Index
                content = re.sub(r'href="[\./]*index\.html"', f'href="{link_home}"', content)
                # Substitui links para módulos (generalizado para pegar ./contabil ou ./Modulos/contabil)
                content = re.sub(r'href="[\./]*(Modulos/)?contabil\.html"', f'href="{link_contabil}"', content)
                content = re.sub(r'href="[\./]*(Modulos/)?fiscal\.html"', f'href="{link_fiscal}"', content)
                content = re.sub(r'href="[\./]*(Modulos/)?dp\.html"', f'href="{link_dp}"', content)
                content = re.sub(r'href="[\./]*(Modulos/)?legal\.html"', f'href="{link_legal}"', content)

                # Injeta Scripts no final
                new_scripts = f"""<script src="{prefix}lidea_db.js"></script><script src="{prefix}core_controller.js"></script></body>"""
                if "</body>" in content:
                    content = content.replace("</body>", new_scripts)
                    with open(file_path, "w", encoding="utf-8") as f: f.write(content)
                    patched_count += 1
    
    return f"SISTEMA REPARADO: {patched_count} arquivos.\nLinks e Scripts corrigidos."

# --- SERVIDOR WEB AUTOMÁTICO ---
def start_server():
    """Inicia um servidor web simples na porta 8000 e abre o navegador."""
    # Comando para rodar python -m http.server 8000 em background
    if sys.platform == "win32":
        subprocess.Popen(["python", "-m", "http.server", "8000"], shell=True)
    else:
        subprocess.Popen(["python3", "-m", "http.server", "8000"])
    
    time.sleep(1) # Espera subir
    webbrowser.open("http://localhost:8000/index.html")
    return "🚀 Servidor Iniciado! Verifique a nova aba do navegador."

# --- INTERFACE ---
st.title("🧠 L'Idea Smart Hub v2")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Dados")
    target_folder = drive_path_input if use_drive_mode else LOCAL_EXCEL_FOLDER
    
    if not use_drive_mode:
        up = st.file_uploader("Upload Excel", type=['xlsx'], accept_multiple_files=True)
        if up:
            if not os.path.exists(LOCAL_EXCEL_FOLDER): os.makedirs(LOCAL_EXCEL_FOLDER)
            for f in up:
                with open(os.path.join(LOCAL_EXCEL_FOLDER, f.name), "wb") as w: w.write(f.getbuffer())

    if st.button("🔄 LER DADOS", type="primary"):
        st.code(process_files(target_folder))
        st.balloons()

with col2:
    st.subheader("2. Sistema e Acesso")
    st.info("Passo A: Corrija os links quebrados.")
    if st.button("🛠️ CORRIGIR LINKS"):
        st.text(repair_system_connections())
        st.success("Links Ajustados.")
    
    st.divider()
    st.info("Passo B: Abra como um site real (Suprema Automação).")
    if st.button("🚀 ABRIR SITE (SERVIDOR WEB)"):
        msg = start_server()
        st.success(msg)

st.divider()
st.caption("Instruções: 1. Ler Dados -> 2. Corrigir Links -> 3. Abrir Site (Servidor Web). Nunca mais terá erro de caminho.")