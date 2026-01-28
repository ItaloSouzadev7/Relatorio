import streamlit as st
import pandas as pd
import json
import os
import re
from datetime import datetime

# CONFIGURAÇÕES GLOBAIS
ROOT_DIR = "."
CSV_FOLDER = os.path.join(ROOT_DIR, "entrada_csv")
JS_DB_FILE = os.path.join(ROOT_DIR, "lidea_db.js")
CORE_CONTROLLER_FILE = os.path.join(ROOT_DIR, "core_controller.js")

st.set_page_config(page_title="L'Idea Fixer", page_icon="🛠️", layout="wide")

st.title("🛠️ L'Idea: Painel de Correção e Integração")
st.markdown("Este painel gerencia a integridade dos dados e corrige a estrutura HTML automaticamente.")

# --- MÓDULO 1: GERADOR DO CONTROLADOR (LÓGICA) ---
def generate_core_controller():
    """Cria o arquivo core_controller.js que gerencia a lógica no navegador."""
    content = """/**
 * L'IDEA CORE CONTROLLER
 * Gerencia sincronização de dados e renderização.
 */
const SYSTEM_VERSION = 'v2_2025_AUTO';

function initSystem() {
    console.log("[Core] Inicializando...");
    
    if (typeof LIDEA_DATA === 'undefined') {
        console.error("ERRO: lidea_db.js ausente.");
        return;
    }

    // Cache Busting: Se versão mudou, atualiza localStorage
    const storedVersion = localStorage.getItem('lidea_version');
    if (storedVersion !== SYSTEM_VERSION) {
        console.info("[Core] Atualizando dados locais...");
        localStorage.setItem('lidea_db_v1', JSON.stringify(LIDEA_DATA));
        localStorage.setItem('lidea_version', SYSTEM_VERSION);
    }
    
    renderPageData();
}

function renderPageData() {
    const db = JSON.parse(localStorage.getItem('lidea_db_v1') || '{}');
    if (!db.contabil) return; // Dados inválidos

    const fmt = (val) => val ? val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : 'R$ 0,00';

    // Mapeamento ID -> Valor (Adicione novos IDs aqui)
    const bindings = {
        'kpi-lucro': () => fmt(db.contabil.resumo.lucro_operacional),
        'kpi-impostos': () => fmt(db.fiscal.total_impostos),
        'kpi-headcount': () => db.dp.headcount,
        'val-receita': () => fmt(db.contabil.resumo.receita_bruta),
        'val-lucro': () => fmt(db.contabil.resumo.lucro_operacional),
        'val-impostos': () => fmt(db.fiscal.total_impostos),
        'val-headcount': () => db.dp.headcount,
        'val-status': () => db.legal.status // Tratamento especial pode ser necessário p/ HTML
    };

    for (const [id, fn] of Object.entries(bindings)) {
        const el = document.getElementById(id);
        if (el) {
            // Se for status, mantém o ícone se possível, ou apenas texto
            if(id === 'val-status') el.innerHTML = `<div class="w-2 h-2 rounded-full bg-emerald-500 inline-block mr-1"></div> ${fn()}`;
            else el.innerText = fn();
        }
    }
    
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

document.addEventListener('DOMContentLoaded', initSystem);
"""
    with open(CORE_CONTROLLER_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    return "✅ core_controller.js gerado/atualizado."

# --- MÓDULO 2: PROCESSADOR DE DADOS (CSVs) ---
def process_csvs():
    """Lê CSVs e gera lidea_db.js"""
    if not os.path.exists(CSV_FOLDER):
        os.makedirs(CSV_FOLDER)
        return "⚠️ Pasta 'entrada_csv' criada. Adicione arquivos CSV nela."

    # Estrutura Base
    db = {
        "meta": {"update": datetime.now().strftime("%d/%m/%Y %H:%M")},
        "contabil": {"resumo": {"receita_bruta": 0, "lucro_operacional": 0}},
        "fiscal": {"total_impostos": 0},
        "dp": {"headcount": 0},
        "legal": {"status": "Regular"}
    }
    
    log = []
    
    # Processamento Contábil
    path_contabil = os.path.join(CSV_FOLDER, "contabil.csv")
    if os.path.exists(path_contabil):
        try:
            df = pd.read_csv(path_contabil, sep=';')
            # Lógica flexível: tenta achar colunas
            if 'Valor' in df.columns:
                 # Exemplo simplificado de extração
                val_rec = df[df['Conta'].str.contains('Receita', na=False)]['Valor'].iloc[0] if not df[df['Conta'].str.contains('Receita')].empty else "0"
                val_lucro = df[df['Conta'].str.contains('Lucro', na=False)]['Valor'].iloc[0] if not df[df['Conta'].str.contains('Lucro')].empty else "0"
                
                db['contabil']['resumo']['receita_bruta'] = float(str(val_rec).replace(',', '.'))
                db['contabil']['resumo']['lucro_operacional'] = float(str(val_lucro).replace(',', '.'))
                log.append("✅ Dados Contábeis importados.")
        except Exception as e:
            log.append(f"❌ Erro no Contábil: {e}")
    else:
        log.append("⚠️ contabil.csv não encontrado (usando zeros).")

    # (Adicione lógica similar para Fiscal e DP aqui conforme seus CSVs reais)
    
    # Salvar JS
    js_content = f"const LIDEA_DATA = {json.dumps(db, indent=4)};"
    with open(JS_DB_FILE, "w", encoding="utf-8") as f:
        f.write(js_content)
    
    return "\n".join(log)

# --- MÓDULO 3: CORRETOR DE HTML (CIRURGIA) ---
def patch_html_files():
    """
    Varre HTMLs, remove scripts hardcoded antigos e injeta o novo controlador.
    Inteligente o suficiente para saber se usa ./ ou ../
    """
    files_to_patch = []
    # Varre raiz e pasta Modulos
    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            if file.endswith(".html"):
                files_to_patch.append(os.path.join(root, file))
    
    log = []
    for file_path in files_to_patch:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 1. Determina caminho relativo dos scripts
        is_in_subdir = "Modulos" in file_path
        script_prefix = "../" if is_in_subdir else "./"
        
        new_scripts = f"""
    <!-- L'IDEA CORE SYSTEM -->
    <script src="{script_prefix}lidea_db.js"></script>
    <script src="{script_prefix}core_controller.js"></script>
</body>"""

        # 2. Remove script antigo (lógica inline anterior)
        # Regex procura por <script> que contém "localStorage" e remove a tag inteira
        pattern_remove = r'<script>[\s\S]*?localStorage\.getItem[\s\S]*?</script>'
        cleaned_content = re.sub(pattern_remove, '', content)
        
        # 3. Verifica se já tem os scripts novos para não duplicar
        if "core_controller.js" not in cleaned_content:
            # Insere antes do </body>
            final_content = cleaned_content.replace('</body>', new_scripts)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(final_content)
            log.append(f"✅ Arquivo corrigido: {file_path}")
        else:
            log.append(f"ℹ️ Arquivo já estava atualizado: {file_path}")

    return "\n".join(log)

# --- INTERFACE VISUAL ---

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Ingestão de Dados")
    uploaded_file = st.file_uploader("Solte seus CSVs aqui (contabil.csv, etc)", accept_multiple_files=True)
    if uploaded_file:
        for up_file in uploaded_file:
            # Salva o arquivo na pasta
            with open(os.path.join(CSV_FOLDER, up_file.name), "wb") as f:
                f.write(up_file.getbuffer())
        st.success("Arquivos salvos! Agora processe os dados.")

    if st.button("Processar CSVs e Atualizar Banco"):
        res = process_csvs()
        st.text(res)
        if "✅" in res:
            st.success("Base de dados lidea_db.js atualizada!")

with col2:
    st.subheader("2. Estrutura do Sistema")
    if st.button("CORRIGIR TUDO (Gera Core + Patch HTML)"):
        status_core = generate_core_controller()
        st.text(status_core)
        
        status_html = patch_html_files()
        st.text(status_html)
        
        st.balloons()
        st.success("Sistema Corrigido! Abra o index.html agora.")

st.divider()
st.info("💡 Como usar: Carregue os CSVs na esquerda -> Clique em Processar -> Clique em Corrigir Tudo na direita.")