#!/usr/bin/env python3
"""
Script para migrar os novos 155 padrões Datasul do arquivo JSON para MongoDB
"""

import asyncio
import os
import uuid
import json
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

async def migrate_new_patterns_to_mongodb():
    """Migra os novos padrões do arquivo JSON para o MongoDB"""
    
    # Conectar ao MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    if not mongo_url:
        print("❌ MONGO_URL não encontrada nas variáveis de ambiente")
        return False
    
    client = AsyncIOMotorClient(mongo_url)
    db = client.log_analyzer
    
    print("🔄 MIGRAÇÃO DOS NOVOS 155 PADRÕES DATASUL PARA MONGODB")
    print("=" * 60)
    
    try:
        # Carregar padrões do arquivo JSON
        json_file = "/app/datasul_mais_150_erros.json"
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
        
        for pattern_data in new_patterns:
            # Verificar se já existe um padrão similar
            existing_pattern = await db.datasul_patterns.find_one({
                "pattern": pattern_data.get("pattern", "")
            })
            
            if existing_pattern:
                print(f"   ⚠️  Padrão já existe: {pattern_data.get('pattern', '')[:50]}...")
                duplicates_count += 1
                continue
            
            # Estrutura otimizada para o MongoDB
            datasul_pattern = {
                "id": str(uuid.uuid4()),
                "pattern": pattern_data.get("pattern", ""),
                "description": pattern_data.get("description", ""),
                "category": pattern_data.get("category", "FAT/NFe"),
                "severity": pattern_data.get("severity", "Médio"),
                "example": pattern_data.get("example", ""),
                "solution": pattern_data.get("solution", ""),
                "tag": pattern_data.get("tag", "Datasul"),
                "source": pattern_data.get("source", "datasul_mais_150_erros"),
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "version": "1.1",
                "usage_count": 0,  # Para estatísticas futuras
                "last_detected": None,  # Último log que detectou este padrão
                "priority": _get_priority(pattern_data.get("severity", "Médio")),
                "regex_valid": _validate_regex(pattern_data.get("pattern", "")),
                "metadata": {
                    "complexity": _calculate_complexity(pattern_data.get("pattern", "")),
                    "keywords": _extract_keywords(pattern_data.get("description", "")),
                    "related_modules": _extract_modules(pattern_data.get("category", "")),
                    "batch_import": "datasul_mais_150_erros_2024"
                }
            }
            
            # Inserir no MongoDB
            await db.datasul_patterns.insert_one(datasul_pattern)
            migrated_count += 1
            
            if migrated_count % 10 == 0:
                print(f"   ✅ {migrated_count}/{len(new_patterns)} novos padrões migrados...")
        
        # Atualizar índices (caso não existam)
        print("📈 Verificando/criando índices para otimização...")
        
        try:
            await db.datasul_patterns.create_index("pattern")
            await db.datasul_patterns.create_index("category")
            await db.datasul_patterns.create_index("tag")
            await db.datasul_patterns.create_index("severity")
            await db.datasul_patterns.create_index("active")
            await db.datasul_patterns.create_index([("active", 1), ("priority", -1)])
            await db.datasul_patterns.create_index("created_at")
            print("✅ Índices verificados/criados")
        except Exception as idx_error:
            print(f"⚠️  Alguns índices já existem: {idx_error}")
        
        print(f"✅ Migração concluída:")
        print(f"   - {migrated_count} novos padrões adicionados")
        print(f"   - {duplicates_count} padrões duplicados ignorados")
        
        # Verificação final
        final_count = await db.datasul_patterns.count_documents({"active": True})
        print(f"✅ Total de padrões ativos no banco: {final_count}")
        
        # Estatísticas por categoria
        print("\n📊 Estatísticas dos novos padrões por categoria:")
        pipeline = [
            {"$match": {"active": True, "metadata.batch_import": "datasul_mais_150_erros_2024"}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        categories = await db.datasul_patterns.aggregate(pipeline).to_list(100)
        for cat in categories:
            print(f"   - {cat['_id']}: {cat['count']} padrões")
        
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
    if special_chars > 10:
        return "alta"
    elif special_chars > 5:
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
    return important_words[:5]  # Top 5 palavras-chave

def _extract_modules(category: str) -> list:
    """Extrai módulos relacionados da categoria"""
    module_map = {
        "FAT/NFe": ["faturamento", "fiscal", "nfe"],
        "FAT/NFCe": ["faturamento", "fiscal", "nfce"],
        "FAT/NFSe": ["faturamento", "fiscal", "nfse"],
        "Infra/Framework": ["infraestrutura", "servidor", "sistema"],
        "Infra/Tomcat": ["infraestrutura", "tomcat", "web"],
        "DataServer/DB": ["banco", "database", "dados"],
        "Financeiro/Integração": ["financeiro", "contas", "integração"],
        "MRE/Recebimento": ["materiais", "recebimento", "compras"],
        "Estoque/Logística": ["estoque", "logística", "materiais"],
        "PCP/Chão de Fábrica": ["produção", "fabrica", "pcp"],
        "Fiscal/SPED": ["fiscal", "sped", "escrituração"],
        "WMS/Expedição": ["wms", "expedição", "logística"],
        "Integrações/API": ["integração", "api", "webservice"],
        "Framework/Segurança": ["framework", "segurança", "acesso"],
        "Auditoria/Logs": ["auditoria", "logs", "trilha"],
        "Faturamento/Negócio": ["faturamento", "vendas", "negócio"],
        "Programa/Rotina": ["programa", "rotina", "código"],
        "Framework/Log": ["framework", "log", "sistema"],
        "Infra/Log": ["infraestrutura", "log", "sistema"]
    }
    return module_map.get(category, ["geral"])

async def verify_patterns_loaded():
    """Verifica se os padrões foram carregados corretamente"""
    
    mongo_url = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client.log_analyzer
    
    print("\n🔍 VERIFICAÇÃO DOS PADRÕES CARREGADOS")
    print("=" * 50)
    
    try:
        # Contagem total
        total_patterns = await db.datasul_patterns.count_documents({"active": True})
        print(f"📊 Total de padrões ativos: {total_patterns}")
        
        # Padrões do novo lote
        new_batch_count = await db.datasul_patterns.count_documents({
            "active": True, 
            "metadata.batch_import": "datasul_mais_150_erros_2024"
        })
        print(f"🆕 Padrões do novo lote: {new_batch_count}")
        
        # Top 5 categorias
        pipeline = [
            {"$match": {"active": True}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        top_categories = await db.datasul_patterns.aggregate(pipeline).to_list(5)
        print(f"\n🏆 Top 5 categorias:")
        for cat in top_categories:
            print(f"   {cat['_id']}: {cat['count']} padrões")
        
        # Teste de alguns padrões específicos
        sample_patterns = [
            "CFOP\\\\s*5101\\\\s*(inv(á|a)lido|n(ã|a)o\\\\s*permitido)",
            "NCM\\\\s*0406\\\\.90\\\\.90\\\\s*(inv(á|a)lido|desatualizado)",
            "Procedure:"
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
    print("🚀 Iniciando migração dos novos 155 padrões Datasul...")
    success = asyncio.run(migrate_new_patterns_to_mongodb())
    
    if success:
        print("\n🔍 Verificando carregamento...")
        asyncio.run(verify_patterns_loaded())
        print("\n🎉 MIGRAÇÃO DOS NOVOS PADRÕES COMPLETA!")
    else:
        print("\n❌ Migração falhou. Verifique os logs de erro.")