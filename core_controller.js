
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
