import streamlit as st
import pandas as pd
import json
import os
import re
import time
from datetime import datetime

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="L'Idea Smart Hub", page_icon="🧠", layout="wide")

# CAMINHOS PADRÃO
ROOT_DIR = "."
LOCAL_EXCEL_FOLDER = os.path.join(ROOT_DIR, "entrada_excel") 
JS_DB_FILE = os.path.join(ROOT_DIR, "lidea_db.js")
CORE_CONTROLLER_FILE = os.path.join(ROOT_DIR, "core_controller.js")

# --- SIDEBAR: CONFIGURAÇÃO DE ORIGEM ---
st.sidebar.header("☁️ Origem dos Dados")
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

# --- PROCESSADOR DE DADOS (DATA ENGINE) ---
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
                
                # Regras de Extração
                if "DRE" in s_name or "RESULTADO" in s_name:
                    rec = find_value_in_dataframe(df, "RECEITA BRUTA OPERACIONAL")
                    luc = find_value_in_dataframe(df, "LUCRO LIQUIDO OPERACIONAL")
                    if rec > 0: db['contabil']['resumo']['receita_bruta'] = rec
                    if luc != 0: db['contabil']['resumo']['lucro_operacional'] = luc
                    if rec > 0: log.append(f"  ✅ DRE encontrada em {filename}")

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
        log.append("\n✨ Banco de Dados (lidea_db.js) Atualizado!")
    except Exception as e: return f"❌ Erro ao salvar JS: {e}"

    return "\n".join(log)

# --- REPARADOR DE SISTEMA (SMART LINKER) ---
def repair_system_connections():
    """
    Esta função é a 'Automação Suprema' de correção.
    Ela calcula matematicamente onde cada arquivo está e corrige os links.
    """
    
    # 1. Gera o Controlador JS (O Cérebro)
    core_code = """
const SYSTEM_VERSION = 'v8_SMART_LINK';

function initSystem() {
    // Tenta carregar dados. Se falhar, tenta ler do localStorage antigo para não quebrar.
    if (typeof LIDEA_DATA !== 'undefined') {
        localStorage.setItem('lidea_db_v1', JSON.stringify(LIDEA_DATA));
        localStorage.setItem('lidea_version', SYSTEM_VERSION);
        console.log("L'Idea: Dados carregados do arquivo JS.");
    } else {
        console.warn("L'Idea: LIDEA_DATA não encontrado. Usando cache.");
    }
    renderPageData();
}

function renderPageData() {
    const db = JSON.parse(localStorage.getItem('lidea_db_v1') || '{}');
    if (!db.contabil) return; // Dados inválidos ou vazios

    const fmt = (v) => v ? v.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL', maximumFractionDigits: 0}) : 'R$ 0';
    
    const map = {
        'val-receita': db.contabil.resumo.receita_bruta,
        'val-lucro': db.contabil.resumo.lucro_operacional,
        'val-impostos': db.fiscal.total_impostos,
        'val-headcount': db.dp.headcount,
        'kpi-lucro': db.contabil.resumo.lucro_operacional,
        'kpi-impostos': db.fiscal.total_impostos,
        'kpi-headcount': db.dp.headcount,
        'val-ativo': db.contabil.ativo // Novo ID mapeado
    };
    
    for (const [id, val] of Object.entries(map)) {
        const el = document.getElementById(id);
        if(el) el.innerText = fmt(val);
    }
    
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// Inicia assim que o DOM estiver pronto
document.addEventListener('DOMContentLoaded', initSystem);
"""
    with open(CORE_CONTROLLER_FILE, "w", encoding="utf-8") as f:
        f.write(core_code)
    
    # 2. Correção Inteligente dos HTMLs (A Cirurgia)
    log = []
    patched_count = 0
    
    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                
                # --- CÁLCULO DE DISTÂNCIA (O Segredo) ---
                # Calcula a distância relativa da pasta atual até a raiz
                # Ex: Raiz -> rel_path = "."
                # Ex: Modulos -> rel_path = ".."
                rel_path = os.path.relpath(ROOT_DIR, start=root)
                prefix = rel_path + "/" if rel_path != "." else "./"
                
                # Normaliza barras para Windows/Linux
                prefix = prefix.replace("\\", "/")

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Remove scripts antigos (Limpeza)
                content = re.sub(r'<script src=".*?lidea_db.js"></script>', '', content)
                content = re.sub(r'<script src=".*?core_controller.js"></script>', '', content)
                content = re.sub(r'<script>[\s\S]*?localStorage\.getItem[\s\S]*?</script>', '', content)

                # Gera novas tags com o caminho CORRETO calculado
                new_scripts = f"""
    <!-- L'IDEA SMART LINK (Auto-Generated) -->
    <script src="{prefix}lidea_db.js"></script>
    <script src="{prefix}core_controller.js"></script>
</body>"""
                
                # Injeta
                if "</body>" in content:
                    content = content.replace("</body>", new_scripts)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    patched_count += 1
                    log.append(f"  ✅ {file}: Caminho ajustado para '{prefix}'")
                else:
                    log.append(f"  ⚠️ {file}: Tag </body> não encontrada.")

    return f"SISTEMA REPARADO COM SUCESSO!\n{patched_count} arquivos HTML reconectados à Raiz.\n\n" + "\n".join(log)

# --- INTERFACE ---
st.title("🧠 L'Idea Smart Hub")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Sincronizar Dados")
    target_folder = drive_path_input if use_drive_mode else LOCAL_EXCEL_FOLDER
    
    if not use_drive_mode:
        up = st.file_uploader("Upload Excel", type=['xlsx'], accept_multiple_files=True)
        if up:
            if not os.path.exists(LOCAL_EXCEL_FOLDER): os.makedirs(LOCAL_EXCEL_FOLDER)
            for f in up:
                with open(os.path.join(LOCAL_EXCEL_FOLDER, f.name), "wb") as w: w.write(f.getbuffer())
            st.success("Arquivos carregados.")

    if st.button("🔄 LER DADOS (EXCEL/DRIVE)", type="primary"):
        st.code(process_files(target_folder))
        st.balloons()

with col2:
    st.subheader("2. Reparar Módulos")
    st.info("Clique abaixo se os gráficos/números não aparecerem ao mudar de página.")
    if st.button("🛠️ CORRIGIR LINKS DOS MÓDULOS"):
        st.text(repair_system_connections())
        st.success("Links corrigidos! Atualize a página do navegador (F5).")

st.divider()
st.caption("Modo Gestor Ágil: 1. Aponte o Drive. 2. Clique em Ler Dados. 3. Clique em Corrigir Links (uma vez).")