
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
