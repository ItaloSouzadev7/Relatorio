// BANCO DE DADOS CENTRAL
// Este arquivo é a fonte da verdade para todos os módulos.

const LIDEA_DATA = {
    "timestamp": "2025-06-25T14:30:00",
    "contabil": {
        "lucro": 15637292.45,
        "receita": 38621924.56,
        "despesas": 3102232.00
    },
    "fiscal": {
        "impostos": 3438234.30,
        "regime": "Lucro Real"
    },
    "dp": {
        "headcount": 142,
        "admissoes": 4,
        "demissoes": 1
    },
    "legal": {
        "status": "Regular",
        "pendencias": 0
    }
};

// Fallback para LocalStorage
if (!localStorage.getItem('lidea_db_v1')) {
    localStorage.setItem('lidea_db_v1', JSON.stringify(LIDEA_DATA));
}