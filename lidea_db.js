// BANCO DE DADOS CENTRAL - L'IDEA CORP
// Atualizado com dados dos CSVs de Junho/2025

const LIDEA_DATA = {
    "meta_info": {
        "periodo": "Junho/2025",
        "comparativo": "Junho/2024",
        "timestamp": new Date().toISOString()
    },
    "contabil": {
        "resumo": {
            "receita_bruta": 38621924.56,
            "lucro_operacional": 15637292.45,
            "ativo_total": 63804162.76,
            "passivo_total": 49250599.56 // Conforme CSV Passivo
        },
        "dre_detalhada": [
            { "conta": "Receita Bruta Operacional", "valor_2025": 38621924.56, "ah": "67,34%" },
            { "conta": "(-) Deduções da Receita", "valor_2025": -3599009.10, "ah": "12,69%" },
            { "conta": "Receita Líquida", "valor_2025": 35022915.46, "ah": "76,14%" },
            { "conta": "(-) CMV / CPV", "valor_2025": -13903170.64, "ah": "125,56%" },
            { "conta": "(=) Lucro Bruto", "valor_2025": 21119744.82, "ah": "53,95%" },
            { "conta": "(-) Despesas Operacionais", "valor_2025": -5670877.94, "ah": "100,24%" },
            { "conta": "(=) Lucro Líquido Operacional", "valor_2025": 15637292.45, "ah": "354,36%" }
        ],
        "ativo_top5": [
            { "conta": "Estoques", "valor": 32669466.86, "av": "51,20%" },
            { "conta": "Clientes (Recebíveis)", "valor": 15157303.88, "av": "23,76%" },
            { "conta": "Aplicações Liquidez", "valor": 3828773.06, "av": "6,00%" },
            { "conta": "Imobilizado", "valor": 14470377.85, "av": "22,68%" },
            { "conta": "Bancos Movimento", "valor": 1758695.18, "av": "2,76%" }
        ],
        "passivo_top5": [
            { "conta": "Adiantamento Clientes", "valor": 3346170.39, "av": "6,79%" },
            { "conta": "Fornecedores", "valor": 1726234.51, "av": "3,51%" },
            { "conta": "Provisão Férias/13º", "valor": 1116377.30, "av": "2,27%" },
            { "conta": "Empréstimos CP", "valor": 730645.24, "av": "1,48%" },
            { "conta": "Obrigações Sociais", "valor": 245230.13, "av": "0,50%" }
        ]
    },
    "indices": {
        "liquidez": {
            "corrente": { "valor": 7.07, "status": "Excelente" },
            "seca": { "valor": 5.57, "status": "Excelente" },
            "geral": { "valor": 6.74, "status": "Excelente" },
            "imediata": { "valor": 1.03, "status": "Bom" }
        },
        "capital_giro": {
            "ccl": 47777361.55,
            "ncg": 37673062.96,
            "saldo_tesouraria": 7391697.79
        },
        "lucratividade": {
            "margem_operacional": 40.5,
            "roi": 12.5,
            "roe": 28.2
        },
        "definicoes": [
            { "titulo": "Liquidez Corrente", "desc": "Indicador que mostra a capacidade de uma empresa de quitar todas suas dívidas a curto prazo. Fórmula: Ativo Circulante / Passivo Circulante. Ideal => 1." },
            { "titulo": "Necessidade de Capital de Giro (NCG)", "desc": "Montante mínimo que uma empresa deve ter em caixa para manter a empresa funcionando. Fórmula: Contas a Receber + Estoque – Contas a pagar." },
            { "titulo": "Saldo de Tesouraria", "desc": "Diferença entre o Ativo Circulante Financeiro e o Passivo Circulante Financeiro. Termômetro dos riscos de descompasso financeiro." },
            { "titulo": "Margem Operacional", "desc": "Avalia o quanto a companhia consegue gerar para cada R$ 1 real em vendas líquidas. Fórmula: Lucro Operacional / Receita Líquida." }
        ]
    },
    "fiscal": {
        "faturamento_anual": 38621924.56,
        "total_impostos": 3438234.30,
        "carga_tributaria_percentual": 8.90,
        "comparativo_2024_percentual": 9.95,
        "detalhe_impostos": [
            { "nome": "PIS", "valor": 222095.98 },
            { "nome": "COFINS", "valor": 1023190.41 },
            { "nome": "ICMS (Estimado)", "valor": 1200000.00 },
            { "nome": "IRPJ/CSLL", "valor": 992947.91 }
        ]
    },
    "dp": {
        "custo_pessoal_total": 3102232.00, // Custo Pessoal DRE
        "headcount": 142,
        "admissoes": 4,
        "demissoes": 1
    },
    "legal": {
        "status": "Regular",
        "pendencias": 0,
        "obs": "Todas as CNDs validadas conforme relatório de conformidade."
    }
};

// Fallback para LocalStorage para garantir persistência local
if (!localStorage.getItem('lidea_db_v1') || true) { // O 'true' força a atualização com os novos dados do CSV
    localStorage.setItem('lidea_db_v1', JSON.stringify(LIDEA_DATA));
}