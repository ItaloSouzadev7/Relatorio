/**
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
