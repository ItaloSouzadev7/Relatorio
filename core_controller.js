
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
