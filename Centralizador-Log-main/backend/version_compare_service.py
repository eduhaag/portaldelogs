import os
import re
from functools import lru_cache
from typing import Dict, List, Tuple

from packaging.version import Version


DEFAULT_LIB_DIRECTORY = (
    os.environ.get("VERSION_COMPARE_LIB_DIRECTORY")
    or os.environ.get("BASE_LIB_DIRECTORY")
    or r"C:\LIBS"
)


class VersionCompareService:
    def __init__(self, base_lib_directory: str | None = None):
        self.base_lib_directory = base_lib_directory or DEFAULT_LIB_DIRECTORY
        self.version_index = self.build_index()

    def build_index(self) -> Dict[str, Dict[int, Dict[str, str]]]:
        index: Dict[str, Dict[int, Dict[str, str]]] = {}

        if not os.path.isdir(self.base_lib_directory):
            return index

        for folder in os.listdir(self.base_lib_directory):
            match = re.match(r"(\d+\.\d+\.\d+)-(\d+)", folder)
            if not match:
                continue

            base = match.group(1)
            fix = int(match.group(2))

            folder_path = os.path.join(self.base_lib_directory, folder)
            extrato_path = os.path.join(folder_path, "extrato_oficial.log")

            if not os.path.exists(extrato_path):
                continue

            with open(extrato_path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()

            sources: Dict[str, str] = {}
            pattern = re.compile(
                r"^([A-Z0-9/\-_.]+)\s+(\d+\.\d+\.\d+\.\d+)",
                re.MULTILINE,
            )

            for match in pattern.finditer(content):
                program = match.group(1).strip()
                version = match.group(2).strip()

                if program in sources:
                    if Version(version) > Version(sources[program]):
                        sources[program] = version
                else:
                    sources[program] = version

            index.setdefault(base, {})[fix] = sources

        return index

    def reload_index(self) -> Dict[str, Dict[int, Dict[str, str]]]:
        self.version_index = self.build_index()
        return self.version_index

    @staticmethod
    @lru_cache(maxsize=256)
    def get_base_and_fix(product_version: str) -> Tuple[str, int]:
        parts = product_version.split(".")
        if len(parts) < 4:
            raise ValueError("Formato inválido de versão do produto")

        base = ".".join(parts[:3])
        fix = int(parts[3])
        return base, fix

    @staticmethod
    def extract_product_version(content: str) -> str:
        match = re.search(r"Versao Produto\s*\.:([\d\.]+)", content)
        if not match:
            raise ValueError("Versão do produto não encontrada")
        return match.group(1).strip()

    @staticmethod
    def extract_client_sources(content: str) -> Tuple[Dict[str, str], List[str]]:
        lines = content.splitlines()

        sources: Dict[str, str] = {}
        programs_with_upc = set()
        current_program = None

        program_pattern = re.compile(r"^([A-Z0-9/\-_.]+)\s+(\d+\.\d+\.\d+\.\d+)")
        upc_pattern = re.compile(r"UPC\s*:", re.IGNORECASE)

        for line in lines:
            stripped = line.strip()

            program_match = program_pattern.match(stripped)
            if program_match:
                current_program = program_match.group(1).strip()
                sources[current_program] = program_match.group(2).strip()
                continue

            if upc_pattern.search(stripped) and current_program:
                programs_with_upc.add(current_program)

        return sources, sorted(programs_with_upc)

    def compare_versions(
        self,
        product_version: str,
        client_sources: Dict[str, str],
        programs_with_upc: List[str],
    ) -> dict:
        base, client_fix = self.get_base_and_fix(product_version)

        if base not in self.version_index:
            raise ValueError(
                f"Base {base} não encontrada no índice configurado em {self.base_lib_directory}"
            )

        result = {
            "product_version": product_version,
            "desatualizados": [],
            "ok": [],
            "nao_encontrado": [],
            "programas_com_upc": programs_with_upc,
        }

        base_data = self.version_index[base]

        for source, client_version in client_sources.items():
            if source in programs_with_upc:
                continue

            official_version = None
            official_fix = None

            for fix in range(client_fix, -1, -1):
                if fix not in base_data:
                    continue

                if source in base_data[fix]:
                    official_version = base_data[fix][source]
                    official_fix = fix
                    break

            if not official_version:
                result["nao_encontrado"].append(
                    {
                        "programa": source,
                        "cliente": client_version,
                    }
                )
                continue

            if Version(client_version) < Version(official_version):
                diff = int(official_version.split(".")[-1]) - int(client_version.split(".")[-1])

                result["desatualizados"].append(
                    {
                        "programa": source,
                        "cliente": client_version,
                        "deveria_estar": official_version,
                        "fix_encontrada": f"{base}-{official_fix}",
                        "diferenca_builds": diff,
                    }
                )
            else:
                result["ok"].append(
                    {
                        "programa": source,
                        "cliente": client_version,
                        "referencia_oficial": official_version,
                        "fix_encontrada": f"{base}-{official_fix}",
                    }
                )

        result["summary"] = {
            "total_programas_cliente": len(client_sources),
            "total_comparados": len(result["desatualizados"]) + len(result["ok"]) + len(result["nao_encontrado"]),
            "desatualizados": len(result["desatualizados"]),
            "ok": len(result["ok"]),
            "nao_encontrado": len(result["nao_encontrado"]),
            "com_upc": len(programs_with_upc),
        }
        result["index_info"] = self.get_index_metadata()

        return result

    def compare_content(self, content: str) -> dict:
        product_version = self.extract_product_version(content)
        client_sources, programs_with_upc = self.extract_client_sources(content)
        return self.compare_versions(product_version, client_sources, programs_with_upc)

    def get_index_metadata(self) -> dict:
        indexed_fixes = sum(len(fixes) for fixes in self.version_index.values())
        indexed_program_versions = sum(
            len(programs)
            for fixes in self.version_index.values()
            for programs in fixes.values()
        )

        return {
            "base_lib_directory": self.base_lib_directory,
            "directory_exists": os.path.isdir(self.base_lib_directory),
            "indexed_bases": len(self.version_index),
            "indexed_fixes": indexed_fixes,
            "indexed_program_versions": indexed_program_versions,
        }


version_compare_service = VersionCompareService()