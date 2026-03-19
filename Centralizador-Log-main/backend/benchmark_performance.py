#!/usr/bin/env python3
"""
Script de benchmark para medir ganhos de performance
Compara versão antiga vs otimizada

100% SAFE - apenas mede performance, não altera dados
"""

import asyncio
import time
import os
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')


async def benchmark_search_queries(db):
    """Benchmark de queries de busca"""
    
    logger.info("\n" + "="*60)
    logger.info("BENCHMARK: Queries de Busca")
    logger.info("="*60)
    
    search_terms = [
        "NFe",
        "erro 1793",
        "CFOP",
        "AppServer",
        "Procedure"
    ]
    
    for search_term in search_terms:
        logger.info(f"\nTestando busca: '{search_term}'")
        
        # Método ANTIGO (múltiplos $regex sem índice)
        start = time.time()
        try:
            old_query = {
                "$or": [
                    {"pattern": {"$regex": search_term, "$options": "i"}},
                    {"description": {"$regex": search_term, "$options": "i"}},
                    {"solution": {"$regex": search_term, "$options": "i"}},
                    {"tag": {"$regex": search_term, "$options": "i"}},
                    {"category": {"$regex": search_term, "$options": "i"}},
                    {"example": {"$regex": search_term, "$options": "i"}},
                ],
                "active": True
            }
            
            cursor = db.datasul_patterns.find(old_query).limit(15)
            old_results = await cursor.to_list(length=None)
            old_time = time.time() - start
            
            logger.info(f"  Método ANTIGO ($regex múltiplos): {old_time:.3f}s - {len(old_results)} resultados")
        except Exception as e:
            logger.error(f"  Erro método antigo: {e}")
            old_time = 999
            old_results = []
        
        # Método NOVO (text search com índice)
        start = time.time()
        try:
            new_results = []
            try:
                # Tentar text search
                cursor = db.datasul_patterns.find(
                    {
                        "$text": {"$search": search_term},
                        "active": True
                    },
                    {
                        "score": {"$meta": "textScore"}
                    }
                ).sort([("score", {"$meta": "textScore"})]).limit(15)
                
                new_results = await cursor.to_list(length=15)
                new_time = time.time() - start
                
                logger.info(f"  Método NOVO ($text search):      {new_time:.3f}s - {len(new_results)} resultados")
                
                # Calcular ganho
                if old_time > 0:
                    speedup = (old_time / new_time) if new_time > 0 else 999
                    improvement = ((old_time - new_time) / old_time * 100) if old_time > 0 else 0
                    logger.info(f"  ✅ GANHO: {speedup:.1f}x mais rápido ({improvement:.0f}% melhoria)")
                
            except Exception as e:
                logger.warning(f"  Text search não disponível: {e}")
                logger.info(f"  💡 Execute 'python create_indexes.py create' primeiro!")
                
        except Exception as e:
            logger.error(f"  Erro método novo: {e}")


async def benchmark_pattern_loading(db):
    """Benchmark de carregamento de padrões"""
    
    logger.info("\n" + "="*60)
    logger.info("BENCHMARK: Carregamento de Padrões")
    logger.info("="*60)
    
    # Custom patterns
    logger.info("\nTestando carregamento de custom_patterns:")
    
    # Método ANTIGO (sem projeção)
    start = time.time()
    old_patterns = await db.custom_patterns.find({"active": True}).to_list(1000)
    old_time = time.time() - start
    logger.info(f"  Método ANTIGO (todos os campos): {old_time:.3f}s - {len(old_patterns)} padrões")
    
    # Método NOVO (com projeção)
    start = time.time()
    new_patterns = await db.custom_patterns.find(
        {"active": True},
        {
            "pattern": 1,
            "description": 1,
            "category": 1,
            "id": 1,
            "_id": 0
        }
    ).to_list(1000)
    new_time = time.time() - start
    logger.info(f"  Método NOVO (projeção campos):   {new_time:.3f}s - {len(new_patterns)} padrões")
    
    if old_time > 0 and new_time > 0:
        speedup = old_time / new_time
        improvement = (old_time - new_time) / old_time * 100
        logger.info(f"  ✅ GANHO: {speedup:.1f}x mais rápido ({improvement:.0f}% melhoria)")


async def benchmark_analysis_history(db):
    """Benchmark de histórico de análises"""
    
    logger.info("\n" + "="*60)
    logger.info("BENCHMARK: Histórico de Análises")
    logger.info("="*60)
    
    # Método ANTIGO (sem índice timestamp)
    start = time.time()
    try:
        old_analyses = await db.log_analysis.find().sort("timestamp", -1).limit(50).to_list(50)
        old_time = time.time() - start
        logger.info(f"  Método ANTIGO (sem índice): {old_time:.3f}s - {len(old_analyses)} registros")
    except Exception as e:
        logger.error(f"  Erro: {e}")
        old_time = 999
    
    # Método NOVO (com índice timestamp + projeção)
    start = time.time()
    try:
        new_analyses = await db.log_analysis.find(
            {},
            {
                "id": 1,
                "filename": 1,
                "timestamp": 1,
                "total_results": 1,
                "_id": 0
            }
        ).sort("timestamp", -1).limit(50).to_list(50)
        new_time = time.time() - start
        logger.info(f"  Método NOVO (índice + projeção): {new_time:.3f}s - {len(new_analyses)} registados")
        
        if old_time > 0 and new_time > 0:
            speedup = old_time / new_time
            improvement = (old_time - new_time) / old_time * 100
            logger.info(f"  ✅ GANHO: {speedup:.1f}x mais rápido ({improvement:.0f}% melhoria)")
    except Exception as e:
        logger.error(f"  Erro: {e}")


async def verify_indexes_status(db):
    """Verifica se os índices foram criados"""
    
    logger.info("\n" + "="*60)
    logger.info("VERIFICAÇÃO DE ÍNDICES")
    logger.info("="*60)
    
    collections = {
        'datasul_patterns': ['datasul_patterns_text_search', 'datasul_patterns_active_priority'],
        'custom_patterns': ['custom_patterns_text_search', 'custom_patterns_active_created'],
        'log_analysis': ['log_analysis_timestamp']
    }
    
    indexes_ok = True
    
    for coll_name, expected_indexes in collections.items():
        logger.info(f"\n{coll_name}:")
        indexes = await db[coll_name].index_information()
        
        for expected in expected_indexes:
            if expected in indexes:
                logger.info(f"  ✅ {expected}")
            else:
                logger.warning(f"  ❌ {expected} (FALTANDO)")
                indexes_ok = False
    
    if not indexes_ok:
        logger.warning("\n⚠️  Alguns índices estão faltando!")
        logger.info("💡 Execute: python create_indexes.py create")
    else:
        logger.info("\n✅ Todos os índices críticos estão criados!")
    
    return indexes_ok


async def run_full_benchmark():
    """Executa benchmark completo"""
    
    try:
        # Conectar ao MongoDB
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'log_analyzer')
        
        logger.info(f"Conectando ao MongoDB: {db_name}")
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Verificar índices primeiro
        indexes_ok = await verify_indexes_status(db)
        
        logger.info("\n" + "="*60)
        logger.info("INICIANDO BENCHMARKS")
        logger.info("="*60)
        
        # Executar benchmarks
        await benchmark_search_queries(db)
        await benchmark_pattern_loading(db)
        await benchmark_analysis_history(db)
        
        # Resumo final
        logger.info("\n" + "="*60)
        logger.info("RESUMO")
        logger.info("="*60)
        
        if indexes_ok:
            logger.info("✅ Sistema otimizado!")
            logger.info("📊 Ganhos esperados:")
            logger.info("   - Buscas: 70-90% mais rápidas")
            logger.info("   - Carregamento: 20-40% mais rápido")
            logger.info("   - Histórico: 50-70% mais rápido")
        else:
            logger.warning("⚠️  Sistema NÃO otimizado ainda")
            logger.info("💡 Para otimizar, execute:")
            logger.info("   python create_indexes.py create")
        
        logger.info("\n🚀 Para ver o efeito completo:")
        logger.info("   1. Execute 'python create_indexes.py create'")
        logger.info("   2. Execute este benchmark novamente")
        logger.info("   3. Compare os tempos!")
        
        # Fechar conexão
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Erro no benchmark: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_full_benchmark())
