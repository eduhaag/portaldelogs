#!/usr/bin/env python3
"""
Script para migrar os novos 165 padrões Datasul/Progress para MongoDB
"""

import asyncio
import os
import uuid
import json
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

async def migrate_165_new_patterns():
    """Migra os novos 165 padrões do arquivo JSON para o MongoDB"""
    
    # Conectar ao MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    if not mongo_url:
        print("❌ MONGO_URL não encontrada nas variáveis de ambiente")
        return False
    
    client = AsyncIOMotorClient(mongo_url)
    db = client.log_analyzer
    
    print("🔄 MIGRAÇÃO DOS NOVOS 165 PADRÕES DATASUL/PROGRESS PARA MONGODB")
    print("=" * 70)
    
    try:
        # Carregar padrões do arquivo JSON
        json_file = "/app/datasul_progress_165_erros.json"
        if not os.path.exists(json_file):
            print(f"❌ Arquivo {json_file} não encontrado")
            return False
        
        with open(json_file, 'r', encoding='utf-8') as f:
            new_patterns = json.load(f)
        
        print(f"📋 Encontrados {len(new_patterns)} novos padrões para migrar")
        
        # Verificar quantos padrões já existem no banco
        existing_count = await db.datasul_patterns.count_documents({})
        print(f"📊 Existem {existing_count} padrões já cadastrados no banco")
        
        # Migrar cada novo padrão
        migrated_count = 0
        duplicates_count = 0
        updated_count = 0
        
        for pattern_data in new_patterns:
            # Verificar se já existe um padrão similar
            existing_pattern = await db.datasul_patterns.find_one({
                "pattern": pattern_data.get("pattern", "")
            })
            
            if existing_pattern:
                # Atualizar padrão existente com informações mais recentes
                update_data = {
                    "description": pattern_data.get("description", ""),
                    "category": pattern_data.get("category", "Geral"),
                    "severity": pattern_data.get("severity", "Médio"),
                    "example": pattern_data.get("example", ""),
                    "solution": pattern_data.get("solution", ""),
                    "tag": pattern_data.get("tag", "Progress"),
                    "source": pattern_data.get("source", "datasul_progress_165_erros"),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "version": "1.2",
                    "metadata.batch_import": "datasul_progress_165_erros_2024",
                    "metadata.updated_with_new_batch": True
                }
                
                await db.datasul_patterns.update_one(
                    {"_id": existing_pattern["_id"]}, 
                    {"$set": update_data}
                )
                updated_count += 1
                print(f"   🔄 Padrão atualizado: {pattern_data.get('pattern', '')[:50]}...")
                continue
            
            # Estrutura otimizada para o MongoDB
            datasul_pattern = {
                "id": str(uuid.uuid4()),
                "pattern": pattern_data.get("pattern", ""),
                "description": pattern_data.get("description", ""),
                "category": pattern_data.get("category", "Geral"),
                "severity": pattern_data.get("severity", "Médio"),
                "example": pattern_data.get("example", ""),
                "solution": pattern_data.get("solution", ""),
                "tag": pattern_data.get("tag", "Progress"),
                "source": pattern_data.get("source", "datasul_progress_165_erros"),
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "version": "1.2",
                "usage_count": 0,
                "last_detected": None,
                "priority": _get_priority(pattern_data.get("severity", "Médio")),
                "regex_valid": _validate_regex(pattern_data.get("pattern", "")),
                "metadata": {
                    "complexity": _calculate_complexity(pattern_data.get("pattern", "")),
                    "keywords": _extract_keywords(pattern_data.get("description", "")),
                    "related_modules": _extract_modules(pattern_data.get("category", "")),
                    "batch_import": "datasul_progress_165_erros_2024",
                    "pattern_type": _classify_pattern_type(pattern_data.get("pattern", "")),
                    "error_code": _extract_error_code(pattern_data.get("pattern", "")),
                    "system_component": _identify_component(pattern_data.get("category", ""))
                }
            }
            
            # Inserir no MongoDB
            await db.datasul_patterns.insert_one(datasul_pattern)
            migrated_count += 1
            
            if migrated_count % 10 == 0:
                print(f"   ✅ {migrated_count}/{len(new_patterns)} novos padrões migrados...")
        
        # Atualizar/verificar índices
        print("📈 Verificando/criando índices para otimização...")
        
        try:
            await db.datasul_patterns.create_index("pattern")
            await db.datasul_patterns.create_index("category")
            await db.datasul_patterns.create_index("tag")
            await db.datasul_patterns.create_index("severity")
            await db.datasul_patterns.create_index("active")
            await db.datasul_patterns.create_index([("active", 1), ("priority", -1)])
            await db.datasul_patterns.create_index("created_at")
            await db.datasul_patterns.create_index("source")
            await db.datasul_patterns.create_index("metadata.batch_import")
            await db.datasul_patterns.create_index("metadata.error_code")
            print("✅ Índices verificados/criados")
        except Exception as idx_error:
            print(f"⚠️  Alguns índices já existem: {idx_error}")
        
        print(f"\n✅ Migração concluída:")
        print(f"   - {migrated_count} novos padrões adicionados")
        print(f"   - {updated_count} padrões existentes atualizados")
        print(f"   - {duplicates_count} padrões duplicados (não alterados)")
        
        # Verificação final
        final_count = await db.datasul_patterns.count_documents({"active": True})
        print(f"✅ Total de padrões ativos no banco: {final_count}")
        
        # Estatísticas por categoria dos novos padrões
        print(f"\n📊 Estatísticas dos novos padrões por categoria:")
        pipeline = [
            {"$match": {"active": True, "metadata.batch_import": "datasul_progress_165_erros_2024"}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        categories = await db.datasul_patterns.aggregate(pipeline).to_list(100)
        for cat in categories:
            print(f"   - {cat['_id']}: {cat['count']} padrões")
        
        # Estatísticas por severidade
        print(f"\n📊 Estatísticas por severidade:")
        pipeline_severity = [
            {"$match": {"active": True, "metadata.batch_import": "datasul_progress_165_erros_2024"}},
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        severities = await db.datasul_patterns.aggregate(pipeline_severity).to_list(10)
        for sev in severities:
            print(f"   - {sev['_id']}: {sev['count']} padrões")
        
        # Top tags
        print(f"\n📊 Top 10 tags:")
        pipeline_tags = [
            {"$match": {"active": True, "metadata.batch_import": "datasul_progress_165_erros_2024"}},
            {"$group": {"_id": "$tag", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        tags = await db.datasul_patterns.aggregate(pipeline_tags).to_list(10)
        for tag in tags:
            print(f"   - {tag['_id']}: {tag['count']} padrões")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        import traceback
        traceback.print_exc()
        client.close()
        return False

def _get_priority(severity: str) -> int:
    """Converte severidade em prioridade numérica"""
    priority_map = {
        "Crítico": 5,
        "Alto": 4,
        "Médio": 3,
        "Baixo": 2,
        "Informativo": 1
    }
    return priority_map.get(severity, 3)

def _validate_regex(pattern: str) -> bool:
    """Valida se o padrão regex é válido"""
    try:
        import re
        re.compile(pattern)
        return True
    except:
        return False

def _calculate_complexity(pattern: str) -> str:
    """Calcula complexidade do padrão"""
    if not pattern:
        return "baixa"
    
    special_chars = len([c for c in pattern if c in r'.*+?^${}[]|()\|'])
    if special_chars > 15:
        return "alta"
    elif special_chars > 8:
        return "média"
    else:
        return "baixa"

def _extract_keywords(description: str) -> list:
    """Extrai palavras-chave da descrição"""
    if not description:
        return []
    
    keywords = []
    words = description.lower().split()
    important_words = [w for w in words if len(w) > 3 and w not in ['para', 'como', 'deve', 'pode', 'está', 'foram', 'será', 'erro', 'problema']]
    return important_words[:5]

def _extract_modules(category: str) -> list:
    """Extrai módulos relacionados da categoria"""
    module_map = {
        "OpenEdge/DB": ["banco", "database", "dados", "blob", "lob"],
        "OpenEdge/ABL": ["código", "abl", "4gl", "programa"],
        "Infra/Tomcat": ["infraestrutura", "tomcat", "web", "pool"],
        "FAT/NFe": ["faturamento", "fiscal", "nfe"],
        "Estoque": ["estoque", "materiais", "movimentação"],
        "Financeiro": ["financeiro", "contas", "pagamento"],
        "Compras": ["compras", "fornecedor", "pedido"],
        "Vendas": ["vendas", "cliente", "pedido"],
        "Producao": ["produção", "manufatura", "pcp"],
        "Qualidade": ["qualidade", "controle", "inspeção"],
        "Manutencao": ["manutenção", "equipamento", "ordem"],
        "RH": ["recursos", "humanos", "folha", "funcionário"],
        "Contabil": ["contábil", "contabilidade", "lançamento"],
        "Fiscal": ["fiscal", "tributos", "impostos"],
        "CRM": ["crm", "cliente", "relacionamento"],
        "BI/Analise": ["bi", "análise", "relatório", "dashboard"]
    }
    return module_map.get(category, ["geral"])

def _classify_pattern_type(pattern: str) -> str:
    """Classifica o tipo do padrão"""
    if not pattern:
        return "genérico"
    
    pattern_lower = pattern.lower()
    
    if any(code in pattern_lower for code in ["ft", "ar", "ee", "mg", "cr", "cp"]):
        return "código_programa"
    elif "cfop" in pattern_lower or "ncm" in pattern_lower or "cst" in pattern_lower:
        return "fiscal"
    elif any(db in pattern_lower for db in ["blob", "cannot", "lock", "transaction"]):
        return "database"
    elif any(net in pattern_lower for net in ["pool", "connection", "timeout", "hikari"]):
        return "infraestrutura"
    elif "temp.table" in pattern_lower or "unknown.*table" in pattern_lower:
        return "abl_code"
    else:
        return "genérico"

def _extract_error_code(pattern: str) -> str:
    """Extrai código de erro do padrão se existir"""
    import re
    
    # Procurar por códigos como FT1234, AR5678, etc.
    code_match = re.search(r'([A-Z]{2}\d{4,5})', pattern)
    if code_match:
        return code_match.group(1)
    
    # Procurar por códigos numéricos entre parênteses
    numeric_match = re.search(r'\((\d{2,5})\)', pattern)
    if numeric_match:
        return f"({numeric_match.group(1)})"
    
    return ""

def _identify_component(category: str) -> str:
    """Identifica componente do sistema baseado na categoria"""
    component_map = {
        "OpenEdge/DB": "Database Engine",
        "OpenEdge/ABL": "ABL Runtime",
        "Infra/Tomcat": "Application Server", 
        "FAT/NFe": "Fiscal Module",
        "Estoque": "Inventory Module",
        "Financeiro": "Financial Module",
        "Compras": "Purchase Module",
        "Vendas": "Sales Module",
        "Producao": "Manufacturing Module",
        "Qualidade": "Quality Module",
        "Manutencao": "Maintenance Module",
        "RH": "HR Module",
        "Contabil": "Accounting Module",
        "Fiscal": "Tax Module",
        "CRM": "CRM Module",
        "BI/Analise": "BI/Analytics Module"
    }
    return component_map.get(category, "General System")

async def verify_new_patterns():
    """Verifica se os novos padrões foram carregados corretamente"""
    
    mongo_url = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client.log_analyzer
    
    print("\n🔍 VERIFICAÇÃO DOS NOVOS PADRÕES CARREGADOS")
    print("=" * 60)
    
    try:
        # Contagem total
        total_patterns = await db.datasul_patterns.count_documents({"active": True})
        print(f"📊 Total de padrões ativos: {total_patterns}")
        
        # Padrões do novo lote
        new_batch_count = await db.datasul_patterns.count_documents({
            "active": True, 
            "metadata.batch_import": "datasul_progress_165_erros_2024"
        })
        print(f"🆕 Padrões do novo lote (165): {new_batch_count}")
        
        # Teste de alguns padrões específicos
        sample_patterns = [
            "\\\\(210\\\\)\\\\s*Cannot\\\\s*read\\\\s*BLOB",
            "Unknown\\\\s*table\\\\s*tt\\\\-\\\\w+",
            "Pool\\\\s*exhausted|HikariPool\\\\-\\\\d+.*timeout",
            "CFOP\\\\s*da\\\\s*remessa\\\\s*inv(á|a)lido",
            "FT7394\\\\s*\\\\-\\\\s*(Falha|Erro)"
        ]
        
        print(f"\n🧪 Teste de padrões específicos:")
        for pattern in sample_patterns:
            exists = await db.datasul_patterns.find_one({"pattern": pattern, "active": True})
            status = "✅ Encontrado" if exists else "❌ Não encontrado"
            print(f"   {status}: {pattern[:50]}...")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        client.close()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando migração dos novos 165 padrões Datasul/Progress...")
    success = asyncio.run(migrate_165_new_patterns())
    
    if success:
        print("\n🔍 Verificando carregamento...")
        asyncio.run(verify_new_patterns())
        print("\n🎉 MIGRAÇÃO DOS 165 NOVOS PADRÕES COMPLETA!")
    else:
        print("\n❌ Migração falhou. Verifique os logs de erro.")