#!/usr/bin/env python3
"""
Script para migrar todos os padrões Datasul para MongoDB
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from datasul_patterns_loader import DatasulPatternsLoader

async def migrate_datasul_patterns_to_mongodb():
    """Migra todos os padrões Datasul do código para o MongoDB"""
    
    # Conectar ao MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    if not mongo_url:
        print("❌ MONGO_URL não encontrada nas variáveis de ambiente")
        return False
    
    client = AsyncIOMotorClient(mongo_url)
    db = client.log_analyzer
    
    print("🔄 MIGRAÇÃO DOS PADRÕES DATASUL PARA MONGODB")
    print("=" * 60)
    
    try:
        # Carregar padrões do código atual
        loader = DatasulPatternsLoader()
        all_patterns = loader.get_all_patterns_with_solutions()
        
        print(f"📋 Encontrados {len(all_patterns)} padrões para migrar")
        
        # Verificar se já existem padrões Datasul no banco
        existing_count = await db.datasul_patterns.count_documents({})
        if existing_count > 0:
            print(f"⚠️  Já existem {existing_count} padrões Datasul no banco")
            response = input("Deseja limpar e reimportar? (s/N): ")
            if response.lower() == 's':
                await db.datasul_patterns.delete_many({})
                print("🗑️  Padrões antigos removidos")
            else:
                print("❌ Migração cancelada")
                client.close()
                return False
        
        # Migrar cada padrão
        migrated_count = 0
        for pattern_data in all_patterns:
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
                "source": "datasul_migration",
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "version": "1.0",
                "usage_count": 0,  # Para estatísticas futuras
                "last_detected": None,  # Último log que detectou este padrão
                "priority": _get_priority(pattern_data.get("severity", "Médio")),
                "regex_valid": _validate_regex(pattern_data.get("pattern", "")),
                "metadata": {
                    "complexity": _calculate_complexity(pattern_data.get("pattern", "")),
                    "keywords": _extract_keywords(pattern_data.get("description", "")),
                    "related_modules": _extract_modules(pattern_data.get("category", ""))
                }
            }
            
            # Inserir no MongoDB
            await db.datasul_patterns.insert_one(datasul_pattern)
            migrated_count += 1
            
            if migrated_count % 10 == 0:
                print(f"   ✅ {migrated_count}/{len(all_patterns)} padrões migrados...")
        
        # Criar índices para performance
        print("📈 Criando índices para otimização...")
        
        await db.datasul_patterns.create_index("pattern")
        await db.datasul_patterns.create_index("category")
        await db.datasul_patterns.create_index("tag")
        await db.datasul_patterns.create_index("severity")
        await db.datasul_patterns.create_index("active")
        await db.datasul_patterns.create_index([("active", 1), ("priority", -1)])
        await db.datasul_patterns.create_index("created_at")
        
        print(f"✅ Migração concluída: {migrated_count} padrões Datasul salvos no MongoDB")
        print("✅ Índices criados para otimização de consultas")
        
        # Verificação final
        final_count = await db.datasul_patterns.count_documents({"active": True})
        print(f"✅ Verificação: {final_count} padrões ativos no banco")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
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
    important_words = [w for w in words if len(w) > 3 and w not in ['para', 'como', 'deve', 'pode', 'está', 'foram', 'será']]
    return important_words[:5]  # Top 5 palavras-chave

def _extract_modules(category: str) -> list:
    """Extrai módulos relacionados da categoria"""
    module_map = {
        "FAT/NFe": ["faturamento", "fiscal", "nfe"],
        "Infra/Framework": ["infraestrutura", "servidor", "sistema"],
        "DataServer/DB": ["banco", "database", "dados"],
        "Financeiro": ["financeiro", "contas", "pagamento"],
        "Programa/Rotina": ["programa", "rotina", "código"]
    }
    return module_map.get(category, ["geral"])

async def create_management_views():
    """Cria views agregadas para gestão dos padrões"""
    
    mongo_url = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client.log_analyzer
    
    print("\n📊 Criando views de gestão...")
    
    try:
        # View de padrões por categoria
        patterns_by_category = [
            {
                "$match": {"active": True}
            },
            {
                "$group": {
                    "_id": "$category",
                    "count": {"$sum": 1},
                    "avg_priority": {"$avg": "$priority"},
                    "patterns": {"$push": {"pattern": "$pattern", "tag": "$tag"}}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]
        
        # Executar agregação para verificar
        result = await db.datasul_patterns.aggregate(patterns_by_category).to_list(100)
        print("✅ View de categorias criada:")
        for item in result:
            print(f"   - {item['_id']}: {item['count']} padrões")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erro ao criar views: {e}")
        client.close()

if __name__ == "__main__":
    print("🚀 Iniciando migração dos padrões Datasul...")
    success = asyncio.run(migrate_datasul_patterns_to_mongodb())
    
    if success:
        print("\n📊 Criando views de gestão...")
        asyncio.run(create_management_views())
        print("\n🎉 MIGRAÇÃO COMPLETA! Todos os padrões Datasul estão agora no MongoDB.")
    else:
        print("\n❌ Migração falhou. Verifique os logs de erro.")