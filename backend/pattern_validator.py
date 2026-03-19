#!/usr/bin/env python3
"""
===============================
Pattern Validator - O fiscal de padrões!
===============================
Aqui a gente confere se o padrão está certinho, se não vai dar bug e se vai pegar aquele erro maroto no log.
Comentários didáticos e bem humorados para quem gosta de regex e validação!
"""

import re
import unicodedata
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """
    Remove acentos e normaliza texto para busca insensível a acentos.
    (Porque erro com acento é igual a erro sem acento: só muda o drama!)
    """
    if not text:
        return text
    # Normalizar unicode e remover acentos
    nfkd_form = unicodedata.normalize('NFKD', text)
    without_accents = ''.join([c for c in nfkd_form if not unicodedata.combining(c)])
    return without_accents.lower()

def create_partial_pattern(pattern: str) -> str:
    """
    Cria padrão regex para busca parcial, escapando caracteres especiais.
    (Aqui a gente foge dos perigos do regex selvagem, mas deixa o usuário buscar do jeito que quiser)
    """
    if not pattern:
        return pattern
    # Escapar caracteres especiais do regex, mas permitir busca parcial
    escaped = re.escape(str(pattern))
    return escaped

class PatternValidator:
    """
    Validador para padrões de erro com teste de funcionalidade
    (Tipo um professor de regex: dá bronca, mas ensina!)
    """
    
    def __init__(self):
        self.test_cases = []
        
    def validate_pattern_format(self, pattern: str) -> Dict[str, Any]:
        """
        Valida se um padrão tem formato correto e pode ser usado para detecção
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "pattern_type": "unknown",
            "complexity": "low",
            "suggestions": []
        }
        
        if not pattern or not pattern.strip():
            result["valid"] = False
            result["errors"].append("Padrão não pode estar vazio")
            return result
        
        pattern = pattern.strip()
        
        # 1. Testar se é regex válido
        try:
            re.compile(pattern)
            result["pattern_type"] = "regex"
        except re.error as e:
            # Se não for regex válido, tentar como texto literal
            try:
                escaped_pattern = re.escape(pattern)
                re.compile(escaped_pattern)
                result["pattern_type"] = "literal"
                result["warnings"].append(f"Padrão será tratado como texto literal (não regex)")
                result["suggestions"].append(f"Padrão escapado: {escaped_pattern}")
            except re.error:
                result["valid"] = False
                result["errors"].append(f"Padrão inválido como regex: {e}")
                return result
        
        # 2. Analisar complexidade
        special_chars = len([c for c in pattern if c in r'.*+?^${}[]|()\|'])
        if special_chars == 0:
            result["complexity"] = "low"
        elif special_chars <= 5:
            result["complexity"] = "medium"  
        else:
            result["complexity"] = "high"
            result["warnings"].append("Padrão complexo pode impactar performance")
        
        # 3. Verificar padrões potencialmente problemáticos
        problematic_patterns = [
            (r'^\.\*', "Começa com .* - pode ser muito genérico"),
            (r'\.\*$', "Termina com .* - pode ser muito genérico"),
            (r'^\.\+', "Começa com .+ - pode ser muito genérico"),
            (r'\.\+$', "Termina com .+ - pode ser muito genérico"),
        ]
        
        for prob_pattern, warning in problematic_patterns:
            if re.search(prob_pattern, pattern):
                result["warnings"].append(warning)
        
        # 4. Sugestões de melhoria
        if result["pattern_type"] == "literal":
            # Se é texto literal, sugerir versões mais robustas
            if " " in pattern:
                spaced_pattern = pattern.replace(" ", r"\s+")
                result["suggestions"].append(f"Para espaços flexíveis: {spaced_pattern}")
            
            # Sugerir case insensitive
            result["suggestions"].append("O sistema automaticamente faz busca case-insensitive")
        
        return result
    
    def test_pattern_matching(self, pattern: str, test_logs: List[str]) -> Dict[str, Any]:
        """
        Testa se o padrão consegue detectar erros em logs de exemplo
        """
        result = {
            "matches_found": 0,
            "total_tests": len(test_logs),
            "match_details": [],
            "no_matches": [],
            "pattern_works": False
        }
        
        # Preparar padrões para teste (como o sistema real faz)
        patterns_to_test = []
        
        # 1. Padrão original com busca parcial
        try:
            partial_pattern = create_partial_pattern(pattern)
            patterns_to_test.append(("original", re.compile(partial_pattern, re.IGNORECASE)))
        except re.error:
            pass
        
        # 2. Padrão normalizado (sem acentos)
        try:
            normalized_pattern = normalize_text(pattern)
            partial_normalized = create_partial_pattern(normalized_pattern)
            patterns_to_test.append(("normalized", re.compile(partial_normalized, re.IGNORECASE)))
        except re.error:
            pass
        
        # 3. Se é regex, testar também como regex direto
        try:
            re.compile(pattern)
            patterns_to_test.append(("regex", re.compile(pattern, re.IGNORECASE)))
        except re.error:
            pass
        
        # Testar cada log
        for i, log_line in enumerate(test_logs):
            matched = False
            match_info = {
                "log": log_line,
                "matches": []
            }
            
            # Testar linha original
            for pattern_type, compiled_pattern in patterns_to_test:
                if compiled_pattern.search(log_line):
                    match_info["matches"].append(f"{pattern_type} (original)")
                    matched = True
            
            # Testar linha normalizada
            normalized_log = normalize_text(log_line)
            for pattern_type, compiled_pattern in patterns_to_test:
                if pattern_type in ["normalized"] and compiled_pattern.search(normalized_log):
                    match_info["matches"].append(f"{pattern_type} (normalized)")
                    matched = True
            
            if matched:
                result["matches_found"] += 1
                result["match_details"].append(match_info)
            else:
                result["no_matches"].append(log_line)
        
        result["pattern_works"] = result["matches_found"] > 0
        result["match_rate"] = (result["matches_found"] / max(1, result["total_tests"])) * 100
        
        return result
    
    def validate_new_pattern(self, pattern_data: Dict[str, Any], test_logs: List[str] = None) -> Dict[str, Any]:
        """
        Validação completa de um novo padrão incluindo testes de funcionalidade
        """
        pattern = pattern_data.get("pattern", "")
        partial_pattern = pattern_data.get("partial_pattern", "")
        example = pattern_data.get("example", "")
        
        validation_result = {
            "overall_valid": True,
            "recommendations": [],
            "pattern_validation": {},
            "partial_pattern_validation": {},
            "functionality_test": {},
            "final_suggestions": []
        }
        
        # 1. Validar padrão principal
        validation_result["pattern_validation"] = self.validate_pattern_format(pattern)
        if not validation_result["pattern_validation"]["valid"]:
            validation_result["overall_valid"] = False
        
        # 2. Validar padrão parcial se fornecido
        if partial_pattern:
            validation_result["partial_pattern_validation"] = self.validate_pattern_format(partial_pattern)
        
        # 3. Preparar logs de teste
        test_logs_to_use = test_logs or []
        
        # Adicionar exemplo se fornecido
        if example and example not in test_logs_to_use:
            test_logs_to_use.append(example)
        
        # Adicionar alguns logs genéricos se não houver testes
        if not test_logs_to_use:
            generic_logs = [
                pattern,  # O próprio padrão
                f"Error: {pattern}",  # Com prefixo Error
                f"WARN {pattern} occurred",  # Com contexto
                f"[INFO] {pattern} detected"  # Com brackets
            ]
            test_logs_to_use.extend(generic_logs)
        
        # 4. Testar funcionalidade
        if pattern:
            validation_result["functionality_test"] = self.test_pattern_matching(pattern, test_logs_to_use)
            
            if not validation_result["functionality_test"]["pattern_works"]:
                validation_result["recommendations"].append(
                    "⚠️ Padrão não conseguiu detectar nenhum dos logs de teste"
                )
                validation_result["recommendations"].append(
                    "💡 Considere revisar o padrão ou fornecer exemplos mais específicos"
                )
        
        # 5. Recomendações finais
        if validation_result["pattern_validation"].get("complexity") == "high":
            validation_result["final_suggestions"].append(
                "🔧 Padrão complexo - considere simplificar para melhor performance"
            )
        
        if validation_result["functionality_test"].get("match_rate", 0) < 100 and len(test_logs_to_use) > 1:
            match_rate = validation_result["functionality_test"]["match_rate"]
            validation_result["final_suggestions"].append(
                f"📊 Taxa de detecção: {match_rate:.1f}% - considere ajustar padrão se necessário"
            )
        
        # Sugerir melhorias baseadas no tipo
        if validation_result["pattern_validation"].get("pattern_type") == "literal":
            validation_result["final_suggestions"].append(
                "💡 Para maior flexibilidade, considere usar regex com \\s+ para espaços variáveis"
            )
        
        return validation_result
    
    def suggest_pattern_improvements(self, original_pattern: str, failed_logs: List[str]) -> List[str]:
        """
        Sugere melhorias no padrão baseado em logs que falharam na detecção
        """
        suggestions = []
        
        if not failed_logs:
            return suggestions
        
        # Analisar padrões comuns nos logs que falharam
        common_words = {}
        for log in failed_logs:
            words = log.lower().split()
            for word in words:
                if len(word) > 3:  # Ignorar palavras muito pequenas
                    common_words[word] = common_words.get(word, 0) + 1
        
        # Sugerir palavras frequentes
        if common_words:
            frequent_words = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:3]
            suggestions.append(f"Palavras frequentes nos logs não detectados: {', '.join([w[0] for w in frequent_words])}")
        
        # Sugerir padrões mais flexíveis
        escaped_original = re.escape(original_pattern)
        flexible_pattern = escaped_original.replace(' ', r'\s+')
        suggestions.append(f"Padrão mais flexível: {flexible_pattern}")
        
        # Sugerir busca por palavras-chave
        key_words = original_pattern.split()
        if len(key_words) > 1:
            keyword_pattern = '|'.join(re.escape(word) for word in key_words)
            suggestions.append(f"Busca por palavra-chave: {keyword_pattern}")
        
        return suggestions

# Função de conveniência para usar no servidor
def validate_pattern_for_api(pattern_data: Dict[str, Any], test_logs: List[str] = None) -> Dict[str, Any]:
    """Função de conveniência para validação via API"""
    validator = PatternValidator()
    return validator.validate_new_pattern(pattern_data, test_logs)