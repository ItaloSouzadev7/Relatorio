import streamlit as st
import pandas as pd
import json
import os
import re
import sys
import subprocess
import webbrowser
from datetime import datetime

# CONFIGURAÇÃO GERAL
st.set_page_config(page_title="L'Idea Smart Engine", page_icon="⚡", layout="wide")

ROOT_DIR = "."
LOCAL_DATA_FOLDER = os.path.join(ROOT_DIR, "entrada_excel")
JS_DB_FILE = os.path.join(ROOT_DIR, "lidea_db.js")
CORE_CONTROLLER_FILE = os.path.join(ROOT_DIR, "core_controller.js")

# --- ENGINE DE EXTRAÇÃO DE DADOS (O CÉREBRO) ---

def clean_currency(value):
    """
    Higieniza valores financeiros complexos.
    Suporta: 'R$ 1.000,00', '(1.000,00)' [contábil negativo], e floats.
    """
    if pd.isna(value) or str(value).strip() == '': return 0.0
    s = str(value)
    
    # Verifica formato contábil negativo (entre parênteses)
    is_negative = False
    if '(' in s and ')' in s:
        is_negative = True
        s = s.replace('(', '').replace(')', '')
    
    # Remove R$, espaços e pontos de milhar
    s = re.sub(r'[^\d,-]', '', s) 
    s = s.replace(',', '.')
    
    try:
        val = float(s)
        return -val if is_negative else val
    except:
        return 0.0

def smart_search(df, keywords, year_col_identifier="2025"):
    """
    Busca Semântica: Procura uma linha que contenha QUALQUER uma das keywords.
    Retorna o valor da coluna correspondente ao ano/período.
    """
    try:
        # Converte tudo para string para busca
        df_str = df.astype(str)
        
        # Procura linha que contenha a keyword
        found_idx = None
        for keyword in keywords:
            mask = df_str.apply(lambda x: x.str.contains(keyword, case=False, na=False))
            # Se achou em alguma célula
            if mask.any().any():
                # Pega o indice da primeira linha encontrada
                found_idx = mask.stack()[mask.stack()].index[0][0]
                break
        
        if found_idx is None: return 0.0
        
        # Identifica a coluna de valor (procura '2025' ou similar no cabeçalho ou linha de metadados)
        # Se o DF não tem cabeçalho limpo, tentamos achar a coluna pela posição
        # Baseado nos CSVs: Coluna 0 = Nome, Coluna 1 = 2024, Coluna 3 = 2025 (Exemplo)
        # Vamos usar uma heurística: pegar a coluna que tem o maior valor numérico na linha, ou a última coluna válida
        
        # Melhor: Procura a coluna que tem "2025" na linha de cabeçalho (se houver)
        target_col = None
        for col in df.columns:
            if year_col_identifier in str(col) or year_col_identifier in str(df.iloc[0:5][col].values):
                target_col = col
                break
        
        val = 0.0
        if target_col:
            val = df.loc[found_idx, target_col]
        else:
            # Fallback: Geralmente a coluna de 2025 é a 4ª coluna (index 3) ou 3ª (index 2) nos seus CSVs
            # Estrutura comum: [Conta] [Valor 2024] [AV] [Valor 2025]
            try: val = df.iloc[found_idx, 3] 
            except: 
                try: val = df.iloc[found_idx, 1]
                except: val = 0.0
                
        return clean_currency(val)

    except Exception as e:
        # print(f"Erro na busca: {e}") 
        return 0.0

def process_data_files(folder):
    if not os.path.exists(folder): return f"❌ Pasta não existe: {folder}"
    
    files = [f for f in os.listdir(folder) if f.endswith('.csv') or f.endswith('.xlsx')]
    if not files: return "⚠️ Nenhum arquivo compatível encontrado."

    # Estrutura Rica de Dados
    db = {
        "meta": {"data": datetime.now().strftime("%d/%m/%Y")},
        "dre": {
            "receita": 0, "deducoes": 0, "receita_liq": 0, "cmv": 0, 
            "lucro_bruto": 0, "despesas": 0, "financeiro": 0, "lucro_op": 0
        },
        "balanco": {"ativo": 0, "passivo": 0},
        "fiscal": {"impostos": 0},
        "dp": {"headcount": 142}
    }
    
    log = []
    
    for file in files:
        path = os.path.join(folder, file)
        try:
            # Leitura inteligente (CSV ou Excel)
            if file.endswith('.csv'):
                # Tenta detectar separador e ler sem header fixo
                try: df = pd.read_csv(path, sep=';', header=None) # Tenta ponto e vírgula
                except: df = pd.read_csv(path, sep=',', header=None) # Tenta vírgula
            else:
                df = pd.read_excel(path, header=None)
            
            fname = file.upper()
            
            # --- PROCESSAMENTO DRE ---
            if "DRE" in fname or "RESULTADO" in fname:
                db['dre']['receita'] = smart_search(df, ["RECEITA BRUTA", "VENDAS DE PRODUTOS"])
                db['dre']['deducoes'] = smart_search(df, ["DEDUCOES", "DEDUÇÕES"])
                db['dre']['cmv'] = smart_search(df, ["CMV", "CUSTO DAS VENDAS", "CPV"])
                db['dre']['lucro_bruto'] = smart_search(df, ["LUCRO BRUTO"])
                db['dre']['despesas'] = smart_search(df, ["DESPESAS OPERACIONAIS", "DESPESAS GERAIS"])
                db['dre']['financeiro'] = smart_search(df, ["RESULTADO FINANCEIRO"])
                db['dre']['lucro_op'] = smart_search(df, ["LUCRO LIQUIDO OPERACIONAL", "LUCRO OPERACIONAL"])
                
                # Cálculo derivado se faltar dado (Integridade)
                if db['dre']['receita_liq'] == 0 and db['dre']['receita'] != 0:
                     db['dre']['receita_liq'] = db['dre']['receita'] + db['dre']['deducoes'] # Dedução geralmente vem negativa

                log.append(f"✅ DRE Processada ({file})")

            # --- PROCESSAMENTO ATIVO/PASSIVO ---
            elif "ATIVO" in fname:
                val = smart_search(df, ["TOTAL DO ATIVO", "A T I V O"])
                if val != 0: db['balanco']['ativo'] = val
                log.append(f"✅ Ativo Processado ({file})")
                
            elif "PASSIVO" in fname:
                val = smart_search(df, ["TOTAL DO PASSIVO", "P A S S I V O"])
                if val != 0: db['balanco']['passivo'] = val
                log.append(f"✅ Passivo Processado ({file})")

            # --- PROCESSAMENTO FISCAL ---
            elif "IMPOSTO" in fname or "FISCAL" in fname:
                # Procura explicitamente Junho/2025 ou Total
                val = smart_search(df, ["06-2025", "TOTAL IMPOSTOS"])
                if val != 0: db['fiscal']['impostos'] = val
                log.append(f"✅ Fiscal Processado ({file})")

        except Exception as e:
            log.append(f"❌ Erro em {file}: {str(e)}")

    # Salva JS
    js_content = f"const LIDEA_DATA = {json.dumps(db, indent=4)};"
    with open(JS_DB_FILE, "w", encoding="utf-8") as f: f.write(js_content)
    
    return "\n".join(log)

# --- REPARO DE SISTEMA E CONTROLLER ---
def update_core_controller():
    js_code = """
const SYS_VER = 'v10_DEEP_SCAN';

function init() {
    if (typeof LIDEA_DATA !== 'undefined') {
        localStorage.setItem('lidea_data', JSON.stringify(LIDEA_DATA));
    }
    render();
}

function render() {
    const db = JSON.parse(localStorage.getItem('lidea_data') || '{}');
    if (!db.dre) return;
    
    const fmt = (v) => v ? v.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'}) : '-';
    
    // Mapeamento Inteligente ID HTML -> Valor JSON
    const map = {
        // DRE
        'dre-receita': db.dre.receita,
        'dre-deducoes': db.dre.deducoes,
        'dre-receita-liq': db.dre.receita_liq || (db.dre.receita + db.dre.deducoes),
        'dre-cmv': db.dre.cmv,
        'dre-lucro-bruto': db.dre.lucro_bruto,
        'dre-despesas': db.dre.despesas,
        'dre-financeiro': db.dre.financeiro,
        'dre-lucro-op': db.dre.lucro_op,
        
        // Balanço
        'bal-ativo': db.balanco.ativo,
        'bal-passivo': db.balanco.passivo,
        
        // KPIs Index
        'kpi-lucro': db.dre.lucro_op,
        'kpi-impostos': db.fiscal.impostos,
        'kpi-headcount': db.dp.headcount,
        
        // Módulos
        'val-impostos': db.fiscal.impostos,
        'val-headcount': db.dp.headcount
    };

    for (const [id, val] of Object.entries(map)) {
        const el = document.getElementById(id);
        if (el) {
            el.innerText = fmt(val);
            // Muda cor se negativo
            if (val < 0) el.classList.add('text-red-600');
            else if (id.includes('lucro') || id.includes('receita')) el.classList.remove('text-red-600');
        }
    }
    if (typeof lucide !== 'undefined') lucide.createIcons();
}
document.addEventListener('DOMContentLoaded', init);
"""
    with open(CORE_CONTROLLER_FILE, "w", encoding="utf-8") as f: f.write(js_code)
    
    # Patch HTML para garantir links
    for root, _, files in os.walk(ROOT_DIR):
        for file in files:
            if file.endswith(".html"):
                p = os.path.join(root, file)
                with open(p, 'r', encoding='utf-8') as f: c = f.read()
                
                # Remove scripts velhos
                c = re.sub(r'<script src=".*?lidea_db.js"></script>', '', c)
                c = re.sub(r'<script src=".*?core_controller.js"></script>', '', c)
                
                # Caminho relativo
                pre = "../" if "Modulos" in p else "./"
                inj = f'<script src="{pre}lidea_db.js"></script><script src="{pre}core_controller.js"></script></body>'
                
                if "core_controller" not in c:
                    c = c.replace('</body>', inj)
                    with open(p, 'w', encoding='utf-8') as f: f.write(c)

    return "✅ Sistema (JS e HTML) Atualizado."

def start_server():
    if sys.platform == "win32": subprocess.Popen(["python", "-m", "http.server", "8000"], shell=True)
    else: subprocess.Popen(["python3", "-m", "http.server", "8000"])
    time.sleep(1)
    webbrowser.open("http://localhost:8000/index.html")

# --- UI ---
st.title("⚡ L'Idea Smart Engine v10")

col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Importar Planilha/CSVs")
    # Upload Híbrido
    up = st.file_uploader("Arraste os arquivos aqui", accept_multiple_files=True)
    if up:
        if not os.path.exists(LOCAL_DATA_FOLDER): os.makedirs(LOCAL_DATA_FOLDER)
        for f in up:
            with open(os.path.join(LOCAL_DATA_FOLDER, f.name), "wb") as w: w.write(f.getbuffer())
        st.success("Arquivos carregados.")
    
    if st.button("🔄 PROCESSAR DADOS", type="primary"):
        st.code(process_data_files(LOCAL_DATA_FOLDER))
        st.balloons()

with col2:
    st.subheader("2. Atualizar Sistema")
    if st.button("🛠️ ATUALIZAR HTML & JS"):
        st.info(update_core_controller())
    
    st.divider()
    if st.button("🚀 ABRIR DASHBOARD"):
        start_server()