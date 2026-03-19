#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Padrões de erro TOTVS/Datasul adicionais
Inclui erros que podem aparecer de forma parcial ou com prefixos especiais
"""

# Erros podem começar com:
# - ** (dois asteriscos)
# - (Procedure: <nome>
# - Ou diretamente a mensagem

TOTVS_ADDITIONAL_ERRORS = [
    # Controladoria / Contábil
    {
        "code": "17006",
        "pattern": r"Conta Contábil.*não cadastrada",
        "description": "Conta Contábil não cadastrada para empresa",
        "category": "Controladoria",
        "severity": "Alto"
    },
    {
        "code": "545",
        "pattern": r"Estabelecimento.*não permite movimentos na data",
        "description": "Período contábil fechado",
        "category": "Controladoria",
        "severity": "Médio"
    },
    {
        "code": "17221",
        "pattern": r"Unidade de Negócio.*não pertence à Empresa",
        "description": "UN não vinculada à empresa",
        "category": "Controladoria",
        "severity": "Alto"
    },
    {
        "code": "17054",
        "pattern": r"Centro de Custo.*inválido para a Unidade de Negócio",
        "description": "Centro de Custo incompatível com UN",
        "category": "Controladoria",
        "severity": "Médio"
    },
    {
        "code": "17022",
        "pattern": r"Plano de Contas.*não é o plano principal",
        "description": "Plano de contas incorreto",
        "category": "Controladoria",
        "severity": "Alto"
    },
    {
        "code": "17111",
        "pattern": r"Não existe saldo disponível no período",
        "description": "Orçamento excedido",
        "category": "Controladoria",
        "severity": "Crítico"
    },
    {
        "code": "17043",
        "pattern": r"conta.*exige Centro de Custo",
        "description": "Centro de Custo obrigatório",
        "category": "Controladoria",
        "severity": "Médio"
    },
    {
        "code": "17044",
        "pattern": r"conta.*está inativa para lançamentos",
        "description": "Conta contábil inativa",
        "category": "Controladoria",
        "severity": "Médio"
    },
    {
        "code": "17009",
        "pattern": r"Estabelecimento.*não possui conta de lucros/perdas",
        "description": "Falta parametrização contábil",
        "category": "Controladoria",
        "severity": "Alto"
    },
    
    # Estoque / Materiais
    {
        "code": "17273",
        "pattern": r"Item.*não possui saldo em estoque",
        "description": "Saldo insuficiente em estoque",
        "category": "Estoque",
        "severity": "Alto"
    },
    {
        "code": "1433",
        "pattern": r"Depósito.*não cadastrado para o Estabelecimento",
        "description": "Depósito não vinculado ao estabelecimento",
        "category": "Estoque",
        "severity": "Médio"
    },
    {
        "code": "18210",
        "pattern": r"Lote.*com data de validade vencida",
        "description": "Lote vencido",
        "category": "Estoque",
        "severity": "Crítico"
    },
    {
        "code": "17882",
        "pattern": r"Família de Itens.*não possui conta de estoque",
        "description": "Falta conta contábil na família",
        "category": "Estoque",
        "severity": "Médio"
    },
    {
        "code": "17274",
        "pattern": r"Item.*com estoque negativo não permitido",
        "description": "Estoque negativo bloqueado",
        "category": "Estoque",
        "severity": "Alto"
    },
    {
        "code": "15881",
        "pattern": r"Requisição de Material.*já atendida",
        "description": "Requisição duplicada",
        "category": "Estoque",
        "severity": "Médio"
    },
    {
        "code": "14881",
        "pattern": r"Não existe tradução de unidade de medida",
        "description": "Falta conversão de unidade",
        "category": "Estoque",
        "severity": "Médio"
    },
    {
        "code": "17200",
        "pattern": r"Depósito não aceita transferência direta",
        "description": "Depósito com restrição",
        "category": "Estoque",
        "severity": "Médio"
    },
    {
        "code": "14662",
        "pattern": r"Item.*exige número de série",
        "description": "Rastreabilidade obrigatória",
        "category": "Estoque",
        "severity": "Alto"
    },
    {
        "code": "18991",
        "pattern": r"Quantidade de etiquetas maior que o permitido",
        "description": "Excesso de etiquetas",
        "category": "Estoque",
        "severity": "Baixo"
    },
    
    # Financeiro
    {
        "code": "26981",
        "pattern": r"Portador.*inválido para a espécie",
        "description": "Incompatibilidade entre portador e espécie",
        "category": "Financeiro",
        "severity": "Médio"
    },
    {
        "code": "17532",
        "pattern": r"Moeda.*não possui cotação para a data",
        "description": "Cotação de moeda não cadastrada",
        "category": "Financeiro",
        "severity": "Alto"
    },
    {
        "code": "26002",
        "pattern": r"Portador.*não possui agência/conta",
        "description": "Dados bancários incompletos",
        "category": "Financeiro",
        "severity": "Médio"
    },
    {
        "code": "26444",
        "pattern": r"Data de vencimento.*não pode ser dia não útil",
        "description": "Vencimento em dia não útil",
        "category": "Financeiro",
        "severity": "Baixo"
    },
    {
        "code": "26301",
        "pattern": r"Título.*já existe para o fornecedor",
        "description": "Duplicidade de título",
        "category": "Financeiro",
        "severity": "Alto"
    },
    {
        "code": "17652",
        "pattern": r"Código de Retenção de Imposto não cadastrado",
        "description": "Falta código de retenção",
        "category": "Financeiro",
        "severity": "Médio"
    },
    {
        "code": "26884",
        "pattern": r"valor da parcela não confere com o valor total",
        "description": "Divergência de valores",
        "category": "Financeiro",
        "severity": "Alto"
    },
    {
        "code": "26543",
        "pattern": r"Grupo de Fornecedores.*não permite antecipação",
        "description": "Antecipação bloqueada",
        "category": "Financeiro",
        "severity": "Médio"
    },
    {
        "code": "17551",
        "pattern": r"Moeda de fechamento do período não informada",
        "description": "Falta moeda de fechamento",
        "category": "Financeiro",
        "severity": "Alto"
    },
    {
        "code": "26001",
        "pattern": r"Conta Corrente inexistente",
        "description": "Conta bancária não cadastrada",
        "category": "Financeiro",
        "severity": "Alto"
    },
    {
        "code": "26043",
        "pattern": r"número da parcela deve ser sequencial",
        "description": "Parcelas fora de sequência",
        "category": "Financeiro",
        "severity": "Médio"
    },
    
    # Comercial / Vendas
    {
        "code": "21041",
        "pattern": r"Cliente.*com crédito suspenso ou excedido",
        "description": "Bloqueio de crédito",
        "category": "Comercial",
        "severity": "Crítico"
    },
    {
        "code": "19331",
        "pattern": r"Tabela de Preço.*fora da validade",
        "description": "Tabela de preço vencida",
        "category": "Comercial",
        "severity": "Médio"
    },
    {
        "code": "1542",
        "pattern": r"Condição de Pagamento.*não permite o número de parcelas",
        "description": "Parcelas incompatíveis",
        "category": "Comercial",
        "severity": "Médio"
    },
    {
        "code": "21005",
        "pattern": r"Não foi possível determinar o preço unitário",
        "description": "Preço não encontrado",
        "category": "Comercial",
        "severity": "Alto"
    },
    {
        "code": "20101",
        "pattern": r"Inscrição Estadual.*inválida",
        "description": "IE inválida",
        "category": "Comercial",
        "severity": "Crítico"
    },
    {
        "code": "19500",
        "pattern": r"Pedido de Venda.*já possui Nota Fiscal",
        "description": "Pedido já faturado",
        "category": "Comercial",
        "severity": "Alto"
    },
    {
        "code": "21098",
        "pattern": r"Vendedor.*não pertence à equipe",
        "description": "Vendedor não vinculado",
        "category": "Comercial",
        "severity": "Médio"
    },
    {
        "code": "20551",
        "pattern": r"Código de País.*inválido para exportação",
        "description": "País inválido",
        "category": "Comercial",
        "severity": "Alto"
    },
    {
        "code": "21552",
        "pattern": r"Índice de reajuste de contrato expirado",
        "description": "Índice de contrato vencido",
        "category": "Comercial",
        "severity": "Médio"
    },
    
    # Fiscal
    {
        "code": "19002",
        "pattern": r"Natureza de Operação.*não permite faturamento",
        "description": "Natureza bloqueada para UF",
        "category": "Fiscal",
        "severity": "Crítico"
    },
    {
        "code": "19455",
        "pattern": r"Código de Tributação.*inválido para.*ICMS",
        "description": "Tributação de ICMS incorreta",
        "category": "Fiscal",
        "severity": "Alto"
    },
    {
        "code": "18944",
        "pattern": r"Série da Nota Fiscal.*não cadastrada",
        "description": "Série não cadastrada",
        "category": "Fiscal",
        "severity": "Alto"
    },
    {
        "code": "19111",
        "pattern": r"Sequência do item na nota fiscal já existe",
        "description": "Item duplicado na NF",
        "category": "Fiscal",
        "severity": "Médio"
    },
    {
        "code": "19222",
        "pattern": r"Alíquota de ICMS não encontrada",
        "description": "Falta alíquota interestadual",
        "category": "Fiscal",
        "severity": "Alto"
    },
    {
        "code": "19333",
        "pattern": r"Conta de impostos não informada",
        "description": "Falta conta contábil de imposto",
        "category": "Fiscal",
        "severity": "Médio"
    },
    {
        "code": "19999",
        "pattern": r"soma das alíquotas.*excede 100%",
        "description": "Alíquotas inválidas",
        "category": "Fiscal",
        "severity": "Crítico"
    },
    {
        "code": "19772",
        "pattern": r"Certificado Digital expirado",
        "description": "Certificado vencido",
        "category": "Fiscal",
        "severity": "Crítico"
    },
    {
        "code": "19888",
        "pattern": r"Erro ao gerar chave de acesso",
        "description": "Erro na chave da NF-e",
        "category": "Fiscal",
        "severity": "Crítico"
    },
    {
        "code": "19045",
        "pattern": r"Mensagem da Nota Fiscal não encontrada",
        "description": "Mensagem complementar inexistente",
        "category": "Fiscal",
        "severity": "Baixo"
    },
    {
        "code": "19100",
        "pattern": r"Data de emissão não pode ser maior que a data atual",
        "description": "Data futura bloqueada",
        "category": "Fiscal",
        "severity": "Médio"
    },
    {
        "code": "19771",
        "pattern": r"Código de serviço.*não condiz com a LC 116",
        "description": "Código de ISS incorreto",
        "category": "Fiscal",
        "severity": "Alto"
    },
    {
        "code": "19330",
        "pattern": r"soma das bases.*difere do valor total",
        "description": "Divergência nas bases de cálculo",
        "category": "Fiscal",
        "severity": "Médio"
    },
    {
        "code": "19001",
        "pattern": r"Falha na validação do Schema XML",
        "description": "XML inválido",
        "category": "Fiscal",
        "severity": "Crítico"
    },
    {
        "code": "19344",
        "pattern": r"Valor do frete não informado.*CIF",
        "description": "Frete obrigatório não informado",
        "category": "Fiscal",
        "severity": "Médio"
    },
    
    # Suprimentos / Compras
    {
        "code": "2014",
        "pattern": r"Fornecedor.*está com estado Inativo",
        "description": "Fornecedor bloqueado",
        "category": "Suprimentos",
        "severity": "Alto"
    },
    {
        "code": "15033",
        "pattern": r"Item.*não é comprado para este estabelecimento",
        "description": "Item não é comprado",
        "category": "Suprimentos",
        "severity": "Médio"
    },
    {
        "code": "15222",
        "pattern": r"Item.*não possui fornecedor padrão",
        "description": "Falta fornecedor padrão",
        "category": "Suprimentos",
        "severity": "Baixo"
    },
    {
        "code": "15200",
        "pattern": r"Fornecedor não habilitado para entrega direta",
        "description": "Entrega direta bloqueada",
        "category": "Suprimentos",
        "severity": "Médio"
    },
    
    # Manufatura / Produção
    {
        "code": "25410",
        "pattern": r"Ordem de Produção.*já encerrada",
        "description": "OP fechada",
        "category": "Manufatura",
        "severity": "Alto"
    },
    {
        "code": "18552",
        "pattern": r"Quantidade.*menor que o lote mínimo",
        "description": "Abaixo do lote mínimo",
        "category": "Manufatura",
        "severity": "Médio"
    },
    {
        "code": "25100",
        "pattern": r"Quantidade reportada maior que a quantidade da Ordem",
        "description": "Produção excedente",
        "category": "Manufatura",
        "severity": "Médio"
    },
    {
        "code": "25222",
        "pattern": r"Operação.*não cadastrada para o Roteiro",
        "description": "Operação inexistente no roteiro",
        "category": "Manufatura",
        "severity": "Alto"
    },
    {
        "code": "18115",
        "pattern": r"Item.*inativo na engenharia",
        "description": "Item desativado",
        "category": "Manufatura",
        "severity": "Alto"
    },
    {
        "code": "18443",
        "pattern": r"lote.*está em inspeção",
        "description": "Lote bloqueado por qualidade",
        "category": "Manufatura",
        "severity": "Médio"
    },
    {
        "code": "18111",
        "pattern": r"Não existe estrutura ativa para o item",
        "description": "Estrutura inativa ou vencida",
        "category": "Manufatura",
        "severity": "Alto"
    },
    {
        "code": "25881",
        "pattern": r"Componente.*não possui saldo para a reserva",
        "description": "Falta matéria-prima",
        "category": "Manufatura",
        "severity": "Crítico"
    },
    
    # Segurança / Sistema
    {
        "code": "112",
        "pattern": r"Usuário.*não possui permissão",
        "description": "Falta permissão de acesso",
        "category": "Segurança",
        "severity": "Alto"
    },
    {
        "code": "22145",
        "pattern": r"Aprovação pendente para o documento",
        "description": "Workflow de aprovação",
        "category": "Sistema",
        "severity": "Médio"
    },
    {
        "code": "22001",
        "pattern": r"Usuário não possui alçada para o valor",
        "description": "Alçada insuficiente",
        "category": "Segurança",
        "severity": "Alto"
    },
    
    # Progress / Infraestrutura
    {
        "code": "5408",
        "pattern": r"Erro na execução da RPC",
        "description": "Falha de comunicação AppServer",
        "category": "Infraestrutura",
        "severity": "Crítico"
    },
    {
        "code": "2624",
        "pattern": r"registro.*está em uso por",
        "description": "Record Lock",
        "category": "Infraestrutura",
        "severity": "Médio"
    },
    {
        "code": "2",
        "pattern": r"Transação cancelada por erro.*Trigger",
        "description": "Erro em Trigger de banco",
        "category": "Infraestrutura",
        "severity": "Crítico"
    },
    {
        "code": "40",
        "pattern": r"Falta de espaço no banco de dados",
        "description": "Database cheio",
        "category": "Infraestrutura",
        "severity": "Crítico"
    },
    {
        "code": "138",
        "pattern": r"registro solicitado não foi encontrado",
        "description": "Registro não encontrado",
        "category": "Infraestrutura",
        "severity": "Médio"
    },
    {
        "code": "1006",
        "pattern": r"Erro ao tentar conectar ao banco",
        "description": "Falha de conexão DB",
        "category": "Infraestrutura",
        "severity": "Crítico"
    },
    {
        "code": "5800",
        "pattern": r"Tentativa de alteração de campo restrito",
        "description": "Campo protegido pela integração",
        "category": "Infraestrutura",
        "severity": "Médio"
    },
    
    # Cadastros Gerais
    {
        "code": "17099",
        "pattern": r"Finalidade Econômica.*não cadastrada",
        "description": "Finalidade não cadastrada",
        "category": "Cadastros",
        "severity": "Médio"
    },
    {
        "code": "14501",
        "pattern": r"Referência do Item.*não encontrada",
        "description": "Referência inexistente",
        "category": "Cadastros",
        "severity": "Médio"
    },
    {
        "code": "14200",
        "pattern": r"Item de débito direto não permite estoque",
        "description": "Tipo de item incorreto",
        "category": "Cadastros",
        "severity": "Médio"
    },
    {
        "code": "14552",
        "pattern": r"Peso bruto não pode ser menor que o peso líquido",
        "description": "Inconsistência de pesos",
        "category": "Cadastros",
        "severity": "Baixo"
    },
]

def get_additional_patterns():
    """Retorna lista de padrões regex para detectar os erros adicionais"""
    patterns = []
    
    for error in TOTVS_ADDITIONAL_ERRORS:
        # Padrão que captura o erro com ou sem prefixos
        # Aceita: **, (Procedure:, ou direto
        pattern = rf"(?:\*\*|\(Procedure:.*\)|^)\s*{error['pattern']}"
        patterns.append({
            'pattern': pattern,
            'code': error['code'],
            'description': error['description'],
            'category': error['category'],
            'severity': error['severity']
        })
    
    return patterns

def get_error_by_code(code):
    """Busca um erro específico pelo código"""
    for error in TOTVS_ADDITIONAL_ERRORS:
        if error['code'] == code:
            return error
    return None

def get_errors_by_category(category):
    """Retorna todos os erros de uma categoria específica"""
    return [e for e in TOTVS_ADDITIONAL_ERRORS if e['category'] == category]

def get_all_categories():
    """Retorna lista de categorias únicas"""
    return list(set(e['category'] for e in TOTVS_ADDITIONAL_ERRORS))
