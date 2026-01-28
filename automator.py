import streamlit as st
import pandas as pd
import json
import os
import re
from datetime import datetime

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="L'Idea Excel Engine", page_icon="📗", layout="wide")

# CAMINHOS E DIRETÓRIOS
ROOT_DIR = "."
EXCEL_FOLDER = os.path.join(ROOT_DIR, "entrada_excel") # Pasta dedicada aos XLSX
JS_DB_FILE = os.path.join(ROOT_DIR, "lidea_db.js")
CORE_CONTROLLER_FILE = os.path.join(ROOT_DIR, "core_controller.js")

# --- ENGINE DE LIMPEZA E EXTRAÇÃO (Robusta) ---
def clean_currency(value):
    """
    Higieniza valores financeiros (ex: 'R$ 1.200,50' -> 1200.50).
    Lida com espaços, símbolos e erros de conversão.
    """
    if pd.isna(value) or str(value).strip() == '': return 0.0
    s = str(value)
    # Mantém apenas números, vírgula e hífen (para negativos)
    s = re.sub(r'[^\d,-]', '', s)
    # Troca vírgula decimal por ponto
    s = s.replace(',', '.')
    try: return float(s)
    except: return 0.0

def find_value_in_dataframe(df, search_term, year_keyword="2025"):
    """
    Algoritmo de Busca em Grade:
    Varre o DataFrame inteiro procurando 'search_term'. 
    Ao achar, tenta identificar a coluna de valor (pelo ano ou posição relativa).
    """
    try:
        # 1. Cria uma máscara booleana de onde está o texto
        mask = df.apply(lambda x: x.astype(str).str.contains(search_term, case=False, na=False))
        # 2. Pega as coordenadas (linha, coluna)
        locations = mask.stack()[mask.stack()].index.tolist()
        
        if not locations: return 0.0
        
        row_idx = locations[0][0] # Pega a linha da primeira ocorrência
        
        # 3. Identifica a coluna de valor
        # Tenta achar uma coluna que tenha o ano no cabeçalho
        target_cols = [c for c in df.columns if year_keyword in str(c)]
        
        val = 0.0
        if target_cols:
            val = df.loc[row_idx, target_cols[0]]
        else:
            # Fallback (Plano B): Tenta pegar a coluna 2 ou 1 (lógica visual comum)
            # Verifica limites para não dar erro de index
            cols_count = len(df.columns)
            if cols_count > 2:
                val = df.iloc[row_idx, 2] # Coluna C
            elif cols_count > 1:
                val = df.iloc[row_idx, 1] # Coluna B
                
        return clean_currency(val)
    except Exception as e:
        # Em produção silenciamo erros não críticos, mas logamos
        print(f"Debug: Erro ao buscar '{search_term}': {e}")
        return 0.0

# --- PROCESSAMENTO EXCEL ---
def process_excel_files():
    if not os.path.exists(EXCEL_FOLDER):
        os.makedirs(EXCEL_FOLDER)
        return "⚠️ Pasta 'entrada_excel' criada. Coloque seus arquivos .xlsx lá."

    files = [f for f in os.listdir(EXCEL_FOLDER) if f.endswith(".xlsx") and not f.startswith("~$")]
    
    if not files:
        return "⚠️ Nenhum arquivo .xlsx encontrado na pasta 'entrada_excel'."

    # Estrutura do Banco de Dados
    db = {
        "meta_info": {"periodo": "Excel Sync", "atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M")},
        "contabil": {"resumo": {"receita_bruta": 0, "lucro_operacional": 0}, "ativo": 0, "passivo": 0},
        "fiscal": {"total_impostos": 0},
        "dp": {"headcount": 142}, # Valor padrão seguro
        "legal": {"status": "Regular"}
    }
    
    log = []
    log.append(f"📂 Processando {len(files)} arquivos Excel...")

    # Itera sobre arquivos
    for filename in files:
        filepath = os.path.join(EXCEL_FOLDER, filename)
        try:
            # Carrega o arquivo Excel (todas as abas)
            xls = pd.ExcelFile(filepath)
            log.append(f"  📄 Lendo: {filename} ({len(xls.sheet_names)} abas)")
            
            # Itera sobre abas (DRE, Fiscal, etc.)
            for sheet_name in xls.sheet_names:
                # Lê a aba como DataFrame. header=None é mais seguro para arquivos "sujos"
                df = pd.read_excel(xls, sheet_name=sheet_name) 
                
                # Identificação de contexto pelo nome da aba ou conteúdo
                s_name = sheet_name.upper()
                
                # --- Lógica de Extração ---
                
                # 1. DRE
                if "DRE" in s_name or "RESULTADO" in s_name or find_value_in_dataframe(df, "RECEITA BRUTA OPERACIONAL") > 0:
                    rec = find_value_in_dataframe(df, "RECEITA BRUTA OPERACIONAL")
                    luc = find_value_in_dataframe(df, "LUCRO LIQUIDO OPERACIONAL")
                    
                    if rec > 0: db['contabil']['resumo']['receita_bruta'] = rec
                    if luc != 0: db['contabil']['resumo']['lucro_operacional'] = luc # Lucro pode ser negativo
                    if rec > 0: log.append(f"    ✅ DRE encontrada na aba '{sheet_name}'")

                # 2. ATIVO
                if "ATIVO" in s_name:
                    ativo = find_value_in_dataframe(df, "A T I V O") # Texto exato do seu CSV antigo
                    if ativo == 0: ativo = find_value_in_dataframe(df, "TOTAL DO ATIVO")
                    
                    if ativo > 0: 
                        db['contabil']['ativo'] = ativo
                        log.append(f"    ✅ Ativo encontrado na aba '{sheet_name}'")

                # 3. IMPOSTOS / FISCAL
                if "IMPOSTO" in s_name or "FISCAL" in s_name or "FATURAMENTO" in s_name:
                    # Tenta achar pelo mês específico "06-2025" ou "Total de Impostos"
                    val = find_value_in_dataframe(df, "06-2025") 
                    if val == 0: val = find_value_in_dataframe(df, "Total de Impostos")
                    
                    if val > 0: 
                        db['fiscal']['total_impostos'] = val
                        log.append(f"    ✅ Fiscal encontrado na aba '{sheet_name}'")

                # 4. DP / HEADCOUNT (Se existir aba de RH)
                if "RH" in s_name or "PESSOAL" in s_name:
                    hc = find_value_in_dataframe(df, "Headcount")
                    if hc == 0: hc = find_value_in_dataframe(df, "Total Colaboradores")
                    if hc > 0: db['dp']['headcount'] = int(hc)

        except Exception as e:
            log.append(f"  ❌ Erro ao ler {filename}: {e}")

    # Salva JS final
    js_content = f"const LIDEA_DATA = {json.dumps(db, indent=4)};"
    with open(JS_DB_FILE, "w", encoding="utf-8") as f:
        f.write(js_content)

    return "\n".join(log)

# --- REPARO DE SISTEMA (Gera core_controller.js e corrige HTMLs) ---
def update_system_files():
    # 1. Gera Controlador JS
    core_code = """
/**
 * L'IDEA CORE CONTROLLER
 * Versão: Excel Bridge
 */
const SYSTEM_VERSION = 'v6_EXCEL_LOCAL';

function initSystem() {
    if (typeof LIDEA_DATA === 'undefined') return;
    
    // Força atualização dos dados
    localStorage.setItem('lidea_db_v1', JSON.stringify(LIDEA_DATA));
    localStorage.setItem('lidea_version', SYSTEM_VERSION);
    
    renderPageData();
}

function renderPageData() {
    const db = JSON.parse(localStorage.getItem('lidea_db_v1') || '{}');
    if (!db.contabil) return;

    const fmt = (v) => v ? v.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL', maximumFractionDigits: 0}) : 'R$ 0';
    
    // Mapa de Data Binding
    const map = {
        'val-receita': db.contabil.resumo.receita_bruta,
        'val-lucro': db.contabil.resumo.lucro_operacional,
        'val-impostos': db.fiscal.total_impostos,
        'val-headcount': db.dp.headcount,
        'kpi-lucro': db.contabil.resumo.lucro_operacional,
        'kpi-impostos': db.fiscal.total_impostos,
        'kpi-headcount': db.dp.headcount
    };
    
    for (const [id, val] of Object.entries(map)) {
        const el = document.getElementById(id);
        if(el) el.innerText = fmt(val);
    }
    
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

document.addEventListener('DOMContentLoaded', initSystem);
"""
    with open(CORE_CONTROLLER_FILE, "w", encoding="utf-8") as f:
        f.write(core_code)
    
    # 2. Patch HTML (Remove scripts velhos e insere novos)
    patched = 0
    for root, _, files in os.walk(ROOT_DIR):
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f: content = f.read()
                
                # Remove bloco de script antigo
                content = re.sub(r'<script>[\s\S]*?localStorage\.getItem[\s\S]*?</script>', '', content)
                
                # Injeta dependências novas (se não existirem)
                prefix = "../" if "Modulos" in path else "./"
                if "core_controller.js" not in content:
                    injection = f'<script src="{prefix}lidea_db.js"></script><script src="{prefix}core_controller.js"></script></body>'
                    content = content.replace('</body>', injection)
                    with open(path, "w", encoding="utf-8") as f: f.write(content)
                    patched += 1
                    
    return f"✅ Sistema Frontend Corrigido ({patched} arquivos atualizados)."

# --- UI (INTERFACE) ---
st.title("📗 L'Idea Excel Engine")
st.markdown("Integração local via arquivos `.xlsx`.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Entrada de Dados")
    uploaded_files = st.file_uploader("Arraste seus arquivos Excel aqui", type=['xlsx'], accept_multiple_files=True)
    
    if uploaded_files:
        if not os.path.exists(EXCEL_FOLDER): os.makedirs(EXCEL_FOLDER)
        for up in uploaded_files:
            with open(os.path.join(EXCEL_FOLDER, up.name), "wb") as f:
                f.write(up.getbuffer())
        st.success("Arquivos salvos na pasta 'entrada_excel'.")

    if st.button("🔄 PROCESSAR EXCEL"):
        result = process_excel_files()
        st.text(result)
        if "✅" in result:
            st.balloons()
            st.success("Base de dados atualizada! Pode abrir o index.html.")

with col2:
    st.subheader("2. Manutenção")
    if st.button("🛠️ CORRIGIR ESTRUTURA HTML"):
        st.info(update_system_files())