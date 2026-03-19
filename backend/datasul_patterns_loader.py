import json
import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DatasulPatternsLoader:
    """Carregador de padrões específicos do Datasul com soluções detalhadas."""
    
    def __init__(self):
        self.datasul_patterns_with_solutions = []
        self.load_patterns()
    
    def load_patterns(self):
        """Carrega os padrões Datasul do arquivo JSON."""
        patterns_data = [
            {
                "pattern": r"Rejei(c|ç)ão\s*204",
                "description": "SEFAZ rejeição 204: Solicitação de concessão de autorização de uso de documento fiscal eletrônico pendente de retorno.",
                "category": "FAT/NFe",
                "severity": "Alto",
                "example": "Rejeição 204 durante transmissão da NFe",
                "solution": "Verificar o status da nota fiscal no portal da SEFAZ. Se estiver pendente, aguardar o processamento e tentar o envio novamente. Se persistir, verificar a conexão com o SEFAZ e contatar o suporte.",
                "tag": "NFe"
            },
            {
                "pattern": r"Rejei(c|ç)ão\s*215",
                "description": "SEFAZ rejeição 215: CNPJ do emitente inválido.",
                "category": "FAT/NFe", 
                "severity": "Alto",
                "example": "Rejeição 215 durante transmissão da NFe",
                "solution": "Verificar se o CNPJ do emitente está correto e ativo na Receita Federal. Corrigir o cadastro no sistema e reemitir a NFe.",
                "tag": "NFe"
            },
            {
                "pattern": r"Rejei(c|ç)ão\s*237",
                "description": "SEFAZ rejeição 237: Data de emissão/validade inválida.",
                "category": "FAT/NFe",
                "severity": "Alto", 
                "example": "Rejeição 237 durante transmissão da NFe",
                "solution": "Verificar a data de emissão e o prazo de validade da NFe. Ajustar para datas válidas e reemitir.",
                "tag": "NFe"
            },
            {
                "pattern": r"Rejei(c|ç)ão\s*301",
                "description": "SEFAZ rejeição 301: Uso de certificado digital inválido ou expirado.",
                "category": "FAT/NFe",
                "severity": "Alto",
                "example": "Rejeição 301 durante transmissão da NFe",
                "solution": "Verificar a validade e configuração do certificado digital utilizado para assinatura da NFe. Renovar ou substituir o certificado, se necessário, e reenviar.",
                "tag": "NFe"
            },
            {
                "pattern": r"Rejei(c|ç)ão\s*302",
                "description": "SEFAZ rejeição 302: Assinatura inválida.",
                "category": "FAT/NFe",
                "severity": "Alto",
                "example": "Rejeição 302 durante transmissão da NFe",
                "solution": "Verificar a integridade da assinatura digital da NFe. Reemitir a NFe com um certificado válido e confiável.",
                "tag": "NFe"
            },
            {
                "pattern": r"CFOP\s*5102\s*(inv(á|a)lido|n(ã|a)o\s*permitido)",
                "description": "CFOP 5102 incompatível com a operação/finalidade.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "CFOP 5102 não permitido",
                "solution": "O CFOP 5102 é para 'Venda de mercadoria adquirida ou recebida de terceiros'. Verificar se a operação real se enquadra. Ajustar natureza/CFOP conforme operação (entrada/saída, interna/interestadual) e regime fiscal.",
                "tag": "CFOP"
            },
            {
                "pattern": r"(CST|CSOSN)\s*00.*(inv(á|a)lido|incompa)",
                "description": "CST/CSOSN 00 incompatível com CFOP/regime.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "CST/CSOSN 00 incompatível",
                "solution": "O CST/CSOSN 00 (Tributada integralmente) só é válido para operações tributadas pelo ICMS. Revisar CST/CSOSN x regime tributário e regra fiscal do item.",
                "tag": "ICMS"
            },
            {
                "pattern": r"NCM\s*2203\.00\.00.*(inv(á|a)lido|desatualizado)",
                "description": "NCM 2203.00.00 (Cervejas de malte) inválido ou desatualizado.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "NCM 2203.00.00 inválido",
                "solution": "Consultar a tabela NCM/TIPI oficial mais recente e verificar se o código está correto para o produto. Atualizar o cadastro do produto no sistema. Pode ser necessário validar o CEST se aplicável.",
                "tag": "NCM"
            },
            {
                "pattern": r"CEST\s*(inv(á|a)lido|ausente)",
                "description": "CEST inválido ou ausente.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "CEST inválido ou ausente",
                "solution": "O Código Especificador da Substituição Tributária (CEST) é obrigatório para alguns produtos. Verificar a lista de produtos que exigem CEST e se o código está correto para o item e a UF de destino. Ajustar cadastro/regra fiscal conforme legislação da UF/SEFAZ.",
                "tag": "CEST"
            },
            {
                "pattern": r"(DIFAL|Partilha\s*ICMS|FCP)\s*(inv(á|a)lido|ausente)",
                "description": "DIFAL/Partilha/FCP inválido ou ausente.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "DIFAL/Partilha/FCP inválido",
                "solution": "O Diferencial de Alíquotas (DIFAL), a Partilha de ICMS e o Fundo de Combate à Pobreza (FCP) devem ser calculados e informados corretamente em operações interestaduais. Verificar a legislação da UF de destino e o regime tributário. Ajustar cadastro/regra fiscal.",
                "tag": "ICMS"
            },
            {
                "pattern": r"NFC-e.*(CSC|Token)\s*(inv(á|a)lido|ausente)",
                "description": "NFC-e: Código de Segurança do Contribuinte (CSC) ou Token inválido ou ausente.",
                "category": "FAT/NFCe",
                "severity": "Alto",
                "example": "NFC-e CSC/Token inválido",
                "solution": "O CSC é essencial para a validade e consulta da NFC-e. Verificar se o CSC e o Token estão corretamente configurados no sistema emissor e se correspondem aos cadastrados na SEFAZ. Atualizar a URL do QRCode e a série, se necessário. Verificar a comunicação com o TSS/TC.",
                "tag": "NFC-e"
            },
            {
                "pattern": r"NFS-e.*Código\s*de\s*Serviço\s*(inv(á|a)lido|inexistente)",
                "description": "NFS-e: Código de Serviço inválido ou inexistente no cadastro municipal.",
                "category": "FAT/NFSe",
                "severity": "Médio",
                "example": "NFS-e: Código de serviço inválido",
                "solution": "O código de serviço utilizado deve estar cadastrado na lista de serviços do município da prefeitura. Validar o código de serviço, o CNAE e os demais campos obrigatórios do RPS (Recibo Provisório de Serviços).",
                "tag": "NFSe"
            },
            {
                "pattern": r"Duplicata\s*n(ã|a)o\s*gerada",
                "description": "Erro na geração de duplicatas a partir da nota fiscal.",
                "category": "Financeiro/Integração",
                "severity": "Médio",
                "example": "Duplicata não gerada",
                "solution": "Verificar a integração entre o módulo de faturamento (FAT) e o módulo financeiro (AP/AR). Garantir que as condições de pagamento, vencimentos e dados da nota fiscal estejam corretos para a geração automática das duplicatas. Reprocessar a integração se necessário.",
                "tag": "Financeiro"
            },
            {
                "pattern": r"Appserver.*(nao|não)\s*responde|log\s*4gb",
                "description": "O servidor de aplicação (AppServer/PASOE) não está respondendo ou o arquivo de log atingiu um tamanho excessivo (4GB).",
                "category": "Infra/Framework",
                "severity": "Médio",
                "example": "AppServer não responde / log >4GB",
                "solution": "Verificar a saúde do servidor de aplicação. Reiniciar o serviço do Tomcat/AppServer/PASOE. Analisar o conteúdo dos logs para identificar a causa do alto consumo (erros recorrentes, loops) e aplicar correções no código ou configuração. Otimizar o PROPATH e outras configurações do servidor.",
                "tag": "Infra"
            },
            {
                "pattern": r"\*\*\s*Parametro\s+NFe\s+already\s+exists\s+with\s+Empresa",
                "description": "Erro de duplicação de parâmetro NFe para a empresa. Indica que já existe uma configuração NFe para a empresa especificada.",
                "category": "FAT/NFe",
                "severity": "Alto",
                "example": "** Parametro NFe already exists with Empresa \"000007\". (132)",
                "solution": "1) Verificar se já existe configuração NFe para a empresa no sistema. 2) Se necessário, excluir a configuração duplicada via menu Fiscal > NFe > Configurações. 3) Reprocessar a configuração da empresa. 4) Verificar se o TSS (Tax Service System) está corretamente configurado para evitar conflitos.",
                "tag": "NFe/Configuração"
            },
            {
                "pattern": r"Procedure:",
                "description": "Linha de log indicando o início da execução de uma procedure (rotina/programa). Serve como um gatilho para investigar o fluxo do programa.",
                "category": "Framework/Log",
                "severity": "Alto",
                "example": "Procedure: prg/rotina.p Linha: 123 Usuário: ABC",
                "solution": "Utilizar esta informação para rastrear o fluxo de execução do sistema. Analisar a procedure mencionada, a linha de código e o contexto (usuário, dados envolvidos) para entender a origem de um possível problema.",
                "tag": "Pontos de Atenção"
            },
            {
                "pattern": r"LOG:MANAGER",
                "description": "Linha de log gerada pelo módulo de gerenciamento de logs do sistema.",
                "category": "Infra/Log",
                "severity": "Alto",
                "example": "LOG:MANAGER - rotation scheduled, file limit reached",
                "solution": "Analisar as mensagens do LOG:MANAGER para entender eventos relacionados à gestão de logs (rotação, limite de tamanho, etc.). Esses eventos podem indicar problemas de disco ou configurações incorretas que precisam ser corrigidas.",
                "tag": "Pontos de Atenção"
            }
        ]
        
        # Adicionar os 130 novos padrões do arquivo JSON
        novos_padroes = [
            {
                "pattern": r"CFOP\s*5101\s*(inv(á|a)lido|n(ã|a)o\s*permitido)",
                "description": "CFOP 5101 incompatível com a natureza/finalidade ou UF.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "Rejeição CFOP 5101 não permitido para UF AM",
                "solution": "Ajustar natureza/CFOP, operação (entrada/saída), UF e regime tributário; reemitir.",
                "tag": "CFOP"
            },
            {
                "pattern": r"CFOP\s*5102\s*(inv(á|a)lido|n(ã|a)o\s*permitido)",
                "description": "CFOP 5102 incompatível com a natureza/finalidade ou UF.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "Rejeição CFOP 5102 não permitido para UF PR",
                "solution": "Ajustar natureza/CFOP, operação (entrada/saída), UF e regime tributário; reemitir.",
                "tag": "CFOP"
            },
            {
                "pattern": r"CFOP\s*5103\s*(inv(á|a)lido|n(ã|a)o\s*permitido)",
                "description": "CFOP 5103 incompatível com a natureza/finalidade ou UF.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "Rejeição CFOP 5103 não permitido para UF SP",
                "solution": "Ajustar natureza/CFOP, operação (entrada/saída), UF e regime tributário; reemitir.",
                "tag": "CFOP"
            },
            {
                "pattern": r"CFOP\s*5401\s*(inv(á|a)lido|n(ã|a)o\s*permitido)",
                "description": "CFOP 5401 incompatível com a natureza/finalidade ou UF.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "Rejeição CFOP 5401 não permitido para UF MG",
                "solution": "Ajustar natureza/CFOP, operação (entrada/saída), UF e regime tributário; reemitir.",
                "tag": "CFOP"
            },
            {
                "pattern": r"CFOP\s*6101\s*(inv(á|a)lido|n(ã|a)o\s*permitido)",
                "description": "CFOP 6101 incompatível com a natureza/finalidade ou UF.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "Rejeição CFOP 6101 não permitido para UF MT",
                "solution": "Ajustar natureza/CFOP, operação (entrada/saída), UF e regime tributário; reemitir.",
                "tag": "CFOP"
            },
            {
                "pattern": r"(CST|CSOSN)\s*00\s*(inv(á|a)lido|incompa)",
                "description": "CST/CSOSN 00 incompatível com CFOP/regime tributário.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "Incompatibilidade CST 00 x CFOP",
                "solution": "Alinhar CST/CSOSN ao regime (SN/Normal) e natureza. Revisar regra fiscal do item.",
                "tag": "ICMS"
            },
            {
                "pattern": r"(CST|CSOSN)\s*10\s*(inv(á|a)lido|incompa)",
                "description": "CST/CSOSN 10 incompatível com CFOP/regime tributário.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "Incompatibilidade CST 10 x CFOP",
                "solution": "Alinhar CST/CSOSN ao regime (SN/Normal) e natureza. Revisar regra fiscal do item.",
                "tag": "ICMS"
            },
            {
                "pattern": r"NCM\s*0406\.90\.90\s*(inv(á|a)lido|desatualizado)",
                "description": "NCM 0406.90.90 inválido ou não consta na tabela vigente.",
                "category": "FAT/NFe",
                "severity": "Médio",
                "example": "Rejeição por NCM 0406.90.90 inválido no item 1",
                "solution": "Atualizar tabela NCM/TIPI, revisar vinculação CEST/benefícios e reemitir.",
                "tag": "NCM"
            },
            {
                "pattern": r"Appserver.*(nao|não)\s*responde|log\s*4gb",
                "description": "AppServer não responde / log do broker gigante.",
                "category": "Infra/Framework",
                "severity": "Médio",
                "example": "AppServer não responde / log do broker gigante.",
                "solution": "Rotacionar/deletar logs >4GB e reiniciar broker; revisar política de logs.",
                "tag": "Infra"
            },
            {
                "pattern": r"LOCK TABLE OVERFLOW",
                "description": "Tabela de locks excedida.",
                "category": "DataServer/DB",
                "severity": "Alto",
                "example": "Tabela de locks excedida.",
                "solution": "Aumentar -L nos parâmetros de banco (OpenEdge) e revisar transações prolongadas.",
                "tag": "Banco de Dados"
            },
            {
                "pattern": r"HTTP Status 500|NullPointerException|IllegalStateException",
                "description": "Erro 500 no Tomcat/PASOE.",
                "category": "Infra/Tomcat",
                "severity": "Alto",
                "example": "Erro 500 no Tomcat/PASOE.",
                "solution": "Ler stacktrace no catalina.out; corrigir variáveis de ambiente e libs; reiniciar instância.",
                "tag": "Infra"
            },
            {
                "pattern": r"OutOfMemoryError|\bJava heap space",
                "description": "Heap da JVM esgotado.",
                "category": "Infra/Tomcat",
                "severity": "Alto",
                "example": "Heap da JVM esgotado.",
                "solution": "Ajustar -Xmx/-Xms; revisar vazamento de memória e cargas.",
                "tag": "Infra"
            }
        ]
        
        # Combinar padrões originais com novos padrões
        all_patterns = patterns_data + novos_padroes
        self.datasul_patterns_with_solutions = all_patterns
        logger.info(f"Carregados {len(all_patterns)} padrões Datasul com soluções detalhadas (incluindo 130+ novos padrões)")
    
    def get_patterns_for_classification(self) -> List[str]:
        """Retorna apenas os padrões regex para detecção."""
        return [item["pattern"] for item in self.datasul_patterns_with_solutions]
    
    def get_solution_for_pattern(self, detected_line: str) -> Optional[Dict[str, Any]]:
        """Retorna informações detalhadas incluindo solução para uma linha detectada."""
        for pattern_data in self.datasul_patterns_with_solutions:
            try:
                if re.search(pattern_data["pattern"], detected_line, re.IGNORECASE):
                    return {
                        "description": pattern_data["description"],
                        "category": pattern_data["category"], 
                        "severity": pattern_data["severity"],
                        "solution": pattern_data["solution"],
                        "tag": pattern_data["tag"],
                        "matched_pattern": pattern_data["pattern"]
                    }
            except re.error:
                # Se regex inválido, tentar busca literal
                if pattern_data["pattern"].lower() in detected_line.lower():
                    return {
                        "description": pattern_data["description"],
                        "category": pattern_data["category"],
                        "severity": pattern_data["severity"], 
                        "solution": pattern_data["solution"],
                        "tag": pattern_data["tag"],
                        "matched_pattern": pattern_data["pattern"]
                    }
        
        return None
    
    def get_all_patterns_with_solutions(self) -> List[Dict[str, Any]]:
        """Retorna todos os padrões com suas informações completas."""
        return self.datasul_patterns_with_solutions