"""
===============================
Version Compare Service - O Sherlock Holmes das versões!
===============================
Aqui a gente compara versões, encontra diferenças e resolve mistérios de patch como um verdadeiro detetive.
Comentários didáticos e bem humorados para quem gosta de investigação e código limpo!
"""

import logging
import os
import re
from functools import lru_cache
from time import monotonic
from typing import Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)

MODULE_HINT_PREFIXES = {
    "ft": ["ftp"],
    "cd": ["cdp"],
    "btb": ["btb"],
    "men": ["men"],
    "prmupc": ["prmupc"],
    "bodi": ["dibo"],
}

DEFAULT_LIB_DIRECTORY = (
    os.environ.get("VERSION_COMPARE_LIB_DIRECTORY")
    or os.environ.get("BASE_LIB_DIRECTORY")
    or r"\\engjv-fsbin.sp01.local\patch_repository\ems2"
)
DEFAULT_PROGRESS_LIB_DIRECTORY = (
    os.environ.get("VERSION_COMPARE_PROGRESS_LIB_DIRECTORY")
    or os.environ.get("PROGRESS_BASE_LIB_DIRECTORY")
    or r"\\engjv-fsbin.sp01.local\progress_repository\ems2"
)

VERSION_FOLDER_RE = re.compile(
    r"^(?P<version>\d+\.\d+\.\d+\.\d+)(?:-(?P<suffix>[A-Za-z0-9._-]+))?$"
)
EMBEDDED_VERSION_RE = re.compile(rb"\[\[+(\d+\.\d+\.\d+\.\d+)\[\[+")
NUMERIC_VERSION_RE = re.compile(r"(\d+\.\d+\.\d+\.\d+)")
NUMERIC_VERSION_BYTES_RE = re.compile(rb"(\d+\.\d+\.\d+\.\d+)")
PROGRAM_HEADER_RE = re.compile(r"^Programa\s+Versao\s+Programa Pai\s+Data\s+Hora", re.IGNORECASE)
TERMINAL_SECTION_RE = re.compile(
    r"^(Matriz Trad Org\s+Empresa Ext|Bases de Dados conectadas|Alias das Bases de Dados)",
    re.IGNORECASE,
)
PIPE_FUNCTION_RE = re.compile(
    r"^(?P<contexto>[^|]+?)\s*\|\s*(?P<funcao>[^|]+?)\s*\|\s*(?P<valor>[^|]+?)\s*\|\s*(?P<programa>[^|]*?)\s*$"
)
SIMPLE_FUNCTION_RE = re.compile(r"^(?P<funcao>(?:SPP|FN)[A-Z0-9_\-]+)\s+(?P<valor>\S+)\s*$", re.IGNORECASE)
SKIP_PROGRAMS_WITHOUT_EMBEDDED_VERSION = {
    "FT0527B.R",
}


class VersionCompareService:
    """
    Serviço de comparação de versões
    (Detecta diferenças, resolve mistérios e evita bugs fantasma)
    """
    def __init__(self, base_lib_directory: str | None = None, progress_lib_directory: str | None = None):
        self.base_lib_directory = base_lib_directory or DEFAULT_LIB_DIRECTORY
        self.progress_lib_directory = progress_lib_directory or DEFAULT_PROGRESS_LIB_DIRECTORY
        self.version_directories: Dict[str, str] = {}
        self.version_folder_names: Dict[str, str] = {}
        self.bin_gui_path_cache: Dict[str, Optional[str]] = {}
        self.progress_bin_gui_path_cache: Dict[str, Optional[str]] = {}
        self.program_file_cache: Dict[str, Dict[str, str]] = {}
        self.program_relative_path_cache: Dict[str, List[str]] = {}
        self.program_search_cache: Dict[Tuple[str, str, str], Optional[str]] = {}
        self.version_directory_cache: Dict[str, Dict[str, str]] = {}
        self.search_root_directory_cache: Dict[str, Dict[str, str]] = {}
        self.directory_program_index_cache: Dict[str, Dict[str, str]] = {}
        self.directory_listing_cache: Dict[str, Dict[str, str]] = {}
        self.relative_directory_resolution_cache: Dict[Tuple[str, str], Optional[str]] = {}
        self.relative_program_resolution_cache: Dict[Tuple[str, str], Optional[str]] = {}
        self.embedded_version_cache: Dict[str, Optional[str]] = {}
        self.reload_index()

    def _build_index(self) -> None:
        self.version_directories = {}
        self.version_folder_names = {}

        if not os.path.isdir(self.base_lib_directory):
            logger.warning(
                "Repositorio de patches nao acessivel: %s",
                self.base_lib_directory,
            )
            return

        for folder in os.listdir(self.base_lib_directory):
            folder_path = os.path.join(self.base_lib_directory, folder)
            if not os.path.isdir(folder_path):
                continue

            match = VERSION_FOLDER_RE.match(folder)
            if not match:
                continue

            version = match.group("version")
            self.version_directories[version] = folder_path
            self.version_folder_names[version] = folder

        logger.info(
            "Catalogadas %d versoes no repositorio de patches",
            len(self.version_directories),
        )

    def reload_index(self) -> None:
        self.bin_gui_path_cache = {}
        self.progress_bin_gui_path_cache = {}
        self.program_file_cache = {}
        self.program_relative_path_cache = {}
        self.program_search_cache = {}
        self.version_directory_cache = {}
        self.search_root_directory_cache = {}
        self.directory_program_index_cache = {}
        self.directory_listing_cache = {}
        self.relative_directory_resolution_cache = {}
        self.relative_program_resolution_cache = {}
        self.embedded_version_cache = {}
        self._build_index()

    @staticmethod
    @lru_cache(maxsize=256)
    def get_base_and_fix(product_version: str) -> Tuple[str, int]:
        parts = product_version.strip().split(".")
        if len(parts) < 4:
            raise ValueError("Formato invalido de versao do produto")

        return ".".join(parts[:3]), int(parts[3])

    @staticmethod
    def _version_tuple(version: str) -> Tuple[int, ...]:
        numeric_version = VersionCompareService._extract_numeric_version(version)
        return tuple(int(part) for part in numeric_version.split("."))

    @staticmethod
    def _extract_numeric_version(version: str) -> str:
        match = NUMERIC_VERSION_RE.search(str(version or "").strip())
        if not match:
            raise ValueError(f"Versao invalida: {version}")
        return match.group(1)

    @staticmethod
    def _normalize_program_filename(value: str) -> str:
        candidate = os.path.basename(value.replace("\\", "/")).strip().upper()
        if not candidate:
            return ""

        stem, ext = os.path.splitext(candidate)
        if ext == ".R":
            return candidate
        if ext:
            return f"{stem}.R"
        return f"{candidate}.R"

    @staticmethod
    def _is_active_function_value(value: str) -> Optional[bool]:
        normalized = str(value or "").strip().lower()
        if normalized in {"sim", "yes", "true", "ativo", "ativa", "on", "1"}:
            return True
        if normalized in {"nao", "não", "no", "false", "inativo", "inativa", "off", "0"}:
            return False
        return None

    @classmethod
    def _build_active_function_entry(
        cls,
        funcao: str,
        valor: str,
        origem: str | None = None,
        programa: str | None = None,
    ) -> dict:
        raw_value = str(valor or "").strip()
        active_status = cls._is_active_function_value(raw_value)
        function_entry = {
            "funcao": funcao.strip(),
            "valor": raw_value,
        }

        if active_status is not None:
            function_entry["ativa"] = active_status

        if origem and origem.strip():
            function_entry["origem"] = origem.strip()
        if programa and programa.strip():
            function_entry["programa"] = programa.strip()

        return function_entry

    def _candidate_versions(self, product_version: str) -> List[str]:
        base_version, current_fix = self.get_base_and_fix(product_version)
        candidates: List[str] = []

        candidate_fixes = [current_fix, current_fix - 1, current_fix - 2]
        seen_fixes = set()
        for fix in candidate_fixes:
            if fix < 1 or fix in seen_fixes:
                continue
            seen_fixes.add(fix)
            version = f"{base_version}.{fix}"
            if version in self.version_directories:
                candidates.append(version)

        return candidates

    def _get_bin_gui_path(self, version: str) -> Optional[str]:
        if version in self.bin_gui_path_cache:
            return self.bin_gui_path_cache[version]

        version_root = self.version_directories.get(version)
        if not version_root:
            self.bin_gui_path_cache[version] = None
            return None

        candidate = os.path.join(version_root, "progress_12", "bin-gui")
        if os.path.isdir(candidate):
            self.bin_gui_path_cache[version] = candidate
            return candidate

        logger.warning("Caminho progress_12/bin-gui nao encontrado em %s", version_root)
        self.bin_gui_path_cache[version] = None
        return None

    def _get_progress_bin_gui_path(self, product_version: str) -> Optional[str]:
        if product_version in self.progress_bin_gui_path_cache:
            return self.progress_bin_gui_path_cache[product_version]

        base_version, _current_fix = self.get_base_and_fix(product_version)
        progress_root = os.path.join(
            self.progress_lib_directory,
            f"{base_version}-SNAPSHOT",
            "progress_12",
            "bin-gui",
        )
        if os.path.isdir(progress_root):
            self.progress_bin_gui_path_cache[product_version] = progress_root
            return progress_root
        self.progress_bin_gui_path_cache[product_version] = None
        return None

    def _get_directory_listing(self, directory_path: str) -> Dict[str, str]:
        cached_listing = self.directory_listing_cache.get(directory_path)
        if cached_listing is not None:
            return cached_listing

        listing: Dict[str, str] = {}
        try:
            for entry in os.listdir(directory_path):
                listing.setdefault(entry.lower(), entry)
        except OSError:
            listing = {}

        self.directory_listing_cache[directory_path] = listing
        return listing

    def _ensure_program_file_index(self, version: str) -> Dict[str, str]:
        cached_index = self.program_file_cache.get(version)
        if cached_index is not None:
            return cached_index

        program_index: Dict[str, str] = {}
        search_root = self._get_bin_gui_path(version)
        if search_root:
            for root, _dirs, files in os.walk(search_root):
                for filename in files:
                    if not filename.lower().endswith(".r"):
                        continue
                    program_index.setdefault(filename.upper(), os.path.join(root, filename))

        self.program_file_cache[version] = program_index
        logger.info("Indexado sob demanda %s: %d fontes .r", version, len(program_index))
        return program_index

    def _normalize_relative_directory(self, value: str) -> str:
        normalized_path = self._normalize_relative_program_path(value)
        if not normalized_path:
            return ""
        parent_directory = os.path.dirname(normalized_path)
        return "" if parent_directory == "." else parent_directory

    def _normalize_relative_program_path(self, value: str) -> str:
        raw_value = str(value or "").replace("/", os.sep).replace("\\", os.sep).strip()
        if not raw_value:
            return ""

        normalized_parts = [part for part in raw_value.split(os.sep) if part and part not in (".", "..")]
        if not normalized_parts:
            return ""

        normalized_filename = self._normalize_program_filename(normalized_parts[-1])
        if not normalized_filename:
            return ""

        if len(normalized_parts) == 1:
            return normalized_filename

        return os.path.join(*normalized_parts[:-1], normalized_filename)

    def _remember_relative_path(self, lookup_key: str, relative_path: str) -> None:
        normalized_key = self._normalize_program_filename(lookup_key)
        normalized_path = self._normalize_relative_program_path(relative_path)
        if not normalized_key or not normalized_path:
            return

        cached_paths = self.program_relative_path_cache.setdefault(normalized_key, [])
        if normalized_path in cached_paths:
            return

        cached_paths.insert(0, normalized_path)

    def _build_relative_path_hints(
        self,
        source_key: str,
        source_info: Dict[str, str],
        lookup_candidates: List[str],
    ) -> List[str]:
        raw_candidates = [
            str(source_info.get("programa_original", "")),
            str(source_info.get("caminho", "")),
            str(source_info.get("appc", "")),
            str(source_info.get("upc", "")),
            str(source_info.get("programa", "")),
            source_key,
        ]

        relative_hints: List[str] = []
        for raw_candidate in raw_candidates:
            normalized_hint = self._normalize_relative_program_path(raw_candidate)
            if normalized_hint and normalized_hint not in relative_hints:
                relative_hints.append(normalized_hint)

        for candidate in lookup_candidates:
            for cached_hint in self.program_relative_path_cache.get(candidate, []):
                if cached_hint not in relative_hints:
                    relative_hints.append(cached_hint)

        return relative_hints

    def _build_directory_hints(
        self,
        source_key: str,
        source_info: Dict[str, str],
        lookup_candidates: List[str],
        relative_path_hints: List[str],
    ) -> List[str]:
        directory_hints: List[str] = []

        def add_hint(raw_value: str) -> None:
            normalized_directory = self._normalize_relative_directory(raw_value)
            if normalized_directory and normalized_directory not in directory_hints:
                directory_hints.append(normalized_directory)

        add_hint(source_key)
        add_hint(str(source_info.get("programa_original", "")))
        add_hint(str(source_info.get("caminho", "")))
        add_hint(str(source_info.get("appc", "")))
        add_hint(str(source_info.get("upc", "")))

        for relative_path in relative_path_hints:
            add_hint(relative_path)

        for candidate in lookup_candidates:
            stem = os.path.splitext(candidate)[0].lower()
            alpha_prefix_match = re.match(r"([a-z]+)", stem)
            if not alpha_prefix_match:
                continue

            alpha_prefix = alpha_prefix_match.group(1)
            module_hints = []
            for prefix, mapped_directories in MODULE_HINT_PREFIXES.items():
                if alpha_prefix.startswith(prefix):
                    module_hints.extend(mapped_directories)
            if len(alpha_prefix) >= 4:
                module_hints.append(alpha_prefix[:4])
            if len(alpha_prefix) >= 3:
                module_hints.append(alpha_prefix[:3])

            for module_hint in module_hints:
                if module_hint and module_hint not in directory_hints:
                    directory_hints.append(module_hint)

        return directory_hints

    def _get_version_directories(self, version: str) -> Dict[str, str]:
        cached_directories = self.version_directory_cache.get(version)
        if cached_directories is not None:
            return cached_directories

        directories: Dict[str, str] = {}
        search_root = self._get_bin_gui_path(version)
        if search_root:
            directories[""] = search_root
            try:
                with os.scandir(search_root) as entries:
                    for entry in entries:
                        if entry.is_dir():
                            directories[entry.name.lower()] = entry.path
            except OSError:
                pass

        self.version_directory_cache[version] = directories
        return directories

    def _get_search_root_directories(self, search_root: str) -> Dict[str, str]:
        cached_directories = self.search_root_directory_cache.get(search_root)
        if cached_directories is not None:
            return cached_directories

        directories: Dict[str, str] = {"": search_root}
        if os.path.isdir(search_root):
            try:
                with os.scandir(search_root) as entries:
                    for entry in entries:
                        if entry.is_dir():
                            directories[entry.name.lower()] = entry.path
            except OSError:
                pass

        self.search_root_directory_cache[search_root] = directories
        return directories

    def _resolve_relative_directory(self, search_root: str, relative_directory: str) -> Optional[str]:
        cache_key = (search_root, relative_directory)
        if cache_key in self.relative_directory_resolution_cache:
            return self.relative_directory_resolution_cache[cache_key]

        if not relative_directory:
            self.relative_directory_resolution_cache[cache_key] = search_root
            return search_root

        current_path = search_root
        for segment in relative_directory.replace("/", os.sep).replace("\\", os.sep).split(os.sep):
            if not segment:
                continue

            matched_segment = self._get_directory_listing(current_path).get(segment.lower())
            if not matched_segment:
                self.relative_directory_resolution_cache[cache_key] = None
                return None

            current_path = os.path.join(current_path, matched_segment)

        resolved_path = current_path if os.path.isdir(current_path) else None
        self.relative_directory_resolution_cache[cache_key] = resolved_path
        return resolved_path

    def _iter_candidate_directories(
        self,
        version: str,
        directory_hints: List[str],
    ) -> List[str]:
        version_directories = self._get_version_directories(version)
        search_root = version_directories.get("")
        if not search_root:
            return []

        candidate_directories: List[str] = []
        for directory_hint in directory_hints:
            resolved_directory = self._resolve_relative_directory(search_root, directory_hint)
            if resolved_directory and resolved_directory not in candidate_directories:
                candidate_directories.append(resolved_directory)
                continue

            top_level_directory = version_directories.get(directory_hint.lower())
            if top_level_directory and top_level_directory not in candidate_directories:
                candidate_directories.append(top_level_directory)

        return candidate_directories

    def _iter_candidate_directories_from_root(
        self,
        search_root: str,
        directory_hints: List[str],
    ) -> List[str]:
        search_root_directories = self._get_search_root_directories(search_root)
        candidate_directories: List[str] = []

        for directory_hint in directory_hints:
            resolved_directory = self._resolve_relative_directory(search_root, directory_hint)
            if resolved_directory and resolved_directory not in candidate_directories:
                candidate_directories.append(resolved_directory)
                continue

            top_level_directory = search_root_directories.get(directory_hint.lower())
            if top_level_directory and top_level_directory not in candidate_directories:
                candidate_directories.append(top_level_directory)

        return candidate_directories

    def _search_program_in_directory(
        self,
        directory_path: str,
        candidate_filename: str,
    ) -> Optional[str]:
        cache_key = (directory_path, candidate_filename.upper(), "directory")
        if cache_key in self.program_search_cache:
            return self.program_search_cache[cache_key]

        directory_index = self.directory_program_index_cache.get(directory_path)
        if directory_index is None:
            directory_index = {}
            for root, _dirs, files in os.walk(directory_path):
                for filename in files:
                    if not filename.lower().endswith(".r"):
                        continue
                    directory_index.setdefault(filename.upper(), os.path.join(root, filename))
            self.directory_program_index_cache[directory_path] = directory_index

        found_path = directory_index.get(candidate_filename.upper())

        self.program_search_cache[cache_key] = found_path
        return found_path

    def _resolve_relative_program_path(self, search_root: str, relative_path: str) -> Optional[str]:
        normalized_relative_path = self._normalize_relative_program_path(relative_path)
        if not normalized_relative_path:
            return None

        cache_key = (search_root, normalized_relative_path)
        if cache_key in self.relative_program_resolution_cache:
            return self.relative_program_resolution_cache[cache_key]

        current_path = search_root
        for segment in normalized_relative_path.split(os.sep):
            matched_segment = self._get_directory_listing(current_path).get(segment.lower())
            if not matched_segment:
                direct_path = os.path.join(current_path, segment)
                if not os.path.exists(direct_path):
                    self.relative_program_resolution_cache[cache_key] = None
                    return None
                current_path = direct_path
                continue

            current_path = os.path.join(current_path, matched_segment)

        resolved_path = current_path if os.path.isfile(current_path) else None
        self.relative_program_resolution_cache[cache_key] = resolved_path
        return resolved_path

    def _extract_embedded_version(self, file_path: str) -> Optional[str]:
        if file_path in self.embedded_version_cache:
            return self.embedded_version_cache[file_path]

        try:
            with open(file_path, "rb") as file_handle:
                matches = self._extract_embedded_versions_from_stream(file_handle)
        except OSError as exc:
            logger.warning("Falha ao ler %s: %s", file_path, exc)
            self.embedded_version_cache[file_path] = None
            return None

        if not matches:
            try:
                with open(file_path, "rb") as file_handle:
                    content = file_handle.read()
            except OSError as exc:
                logger.warning("Falha ao reler %s: %s", file_path, exc)
                self.embedded_version_cache[file_path] = None
                return None

            matches = [match.decode("ascii") for match in EMBEDDED_VERSION_RE.findall(content)]

        if not matches:
            self.embedded_version_cache[file_path] = None
            return None

        embedded_version = max(matches, key=self._version_tuple)
        self.embedded_version_cache[file_path] = embedded_version
        return embedded_version

    @staticmethod
    def _extract_embedded_versions_from_stream(file_handle) -> List[str]:
        marker = b"[[["
        overlap = 128
        chunk_size = 64 * 1024
        versions_found: List[str] = []
        buffer = b""
        absolute_offset = 0
        processed_marker_positions = set()

        while True:
            chunk = file_handle.read(chunk_size)
            if not chunk:
                break

            buffer += chunk
            search_from = 0
            while True:
                marker_index = buffer.find(marker, search_from)
                if marker_index == -1:
                    break

                if marker_index > 0 and buffer[marker_index - 1:marker_index] == b"[":
                    search_from = marker_index + 1
                    continue

                absolute_marker_index = absolute_offset + marker_index
                if absolute_marker_index in processed_marker_positions:
                    search_from = marker_index + len(marker)
                    continue

                processed_marker_positions.add(absolute_marker_index)

                version_start = marker_index + len(marker)
                while version_start < len(buffer) and buffer[version_start:version_start + 1] == b"[":
                    version_start += 1

                version_window = buffer[version_start: version_start + 64]
                numeric_match = NUMERIC_VERSION_BYTES_RE.match(version_window)
                if numeric_match:
                    version_text = numeric_match.group(1).decode("ascii", errors="ignore")
                    if version_text:
                        versions_found.append(version_text)

                search_from = marker_index + len(marker)

            if len(buffer) > overlap:
                absolute_offset += len(buffer) - overlap
                buffer = buffer[-overlap:]

        return versions_found

    def _build_lookup_candidates(self, source_key: str, source_info: Dict[str, str]) -> List[str]:
        raw_candidates = [
            str(source_info.get("programa_original", "")),
            str(source_info.get("caminho", "")),
            str(source_info.get("programa", "")),
            source_key,
        ]

        normalized_candidates: List[str] = []
        for raw_candidate in raw_candidates:
            candidate = self._normalize_program_filename(raw_candidate)
            if candidate and candidate not in normalized_candidates:
                normalized_candidates.append(candidate)

        return normalized_candidates

    @staticmethod
    def _should_skip_program_without_embedded_version(lookup_candidates: List[str]) -> bool:
        return any(candidate in SKIP_PROGRAMS_WITHOUT_EMBEDDED_VERSION for candidate in lookup_candidates)

    def _find_reference_program(
        self,
        product_version: str,
        candidate_versions: List[str],
        lookup_candidates: List[str],
        relative_path_hints: List[str],
        directory_hints: List[str],
        metrics: Optional[Dict[str, int]] = None,
    ) -> Optional[Dict[str, str]]:
        for candidate_version in candidate_versions:
            attempted_file_paths = set()
            search_root = self._get_bin_gui_path(candidate_version)
            if search_root:
                for relative_hint in relative_path_hints:
                    file_path = self._resolve_relative_program_path(search_root, relative_hint)
                    if not file_path:
                        continue
                    normalized_file_path = os.path.normcase(file_path)
                    if normalized_file_path in attempted_file_paths:
                        continue
                    attempted_file_paths.add(normalized_file_path)

                    official_version = self._extract_embedded_version(file_path) or ""
                    if not official_version:
                        if metrics is not None:
                            metrics["files_without_embedded_version"] = metrics.get("files_without_embedded_version", 0) + 1
                        continue

                    for lookup_candidate in lookup_candidates:
                        self._remember_relative_path(lookup_candidate, relative_hint)

                    if metrics is not None:
                        metrics["direct_path_hits"] = metrics.get("direct_path_hits", 0) + 1

                    return {
                        "requested_program": os.path.basename(file_path).upper(),
                        "file_path": file_path,
                        "official_version": official_version,
                        "version_folder": candidate_version,
                        "folder_name": self.version_folder_names.get(candidate_version, candidate_version),
                    }

            for candidate_directory in self._iter_candidate_directories(candidate_version, directory_hints):
                for candidate in lookup_candidates:
                    file_path = self._search_program_in_directory(candidate_directory, candidate)
                    if not file_path:
                        continue
                    normalized_file_path = os.path.normcase(file_path)
                    if normalized_file_path in attempted_file_paths:
                        continue
                    attempted_file_paths.add(normalized_file_path)

                    official_version = self._extract_embedded_version(file_path) or ""
                    if not official_version:
                        if metrics is not None:
                            metrics["files_without_embedded_version"] = metrics.get("files_without_embedded_version", 0) + 1
                        continue

                    if search_root:
                        relative_path = os.path.relpath(file_path, search_root)
                        self._remember_relative_path(candidate, relative_path)

                    if metrics is not None:
                        metrics["targeted_directory_hits"] = metrics.get("targeted_directory_hits", 0) + 1

                    return {
                        "requested_program": candidate,
                        "file_path": file_path,
                        "official_version": official_version,
                        "version_folder": candidate_version,
                        "folder_name": self.version_folder_names.get(candidate_version, candidate_version),
                    }

        progress_search_root = self._get_progress_bin_gui_path(product_version)
        if not progress_search_root:
            return None

        base_version, _current_fix = self.get_base_and_fix(product_version)
        progress_folder_name = f"{base_version}-SNAPSHOT"
        attempted_file_paths = set()

        for relative_hint in relative_path_hints:
            file_path = self._resolve_relative_program_path(progress_search_root, relative_hint)
            if not file_path:
                continue
            normalized_file_path = os.path.normcase(file_path)
            if normalized_file_path in attempted_file_paths:
                continue
            attempted_file_paths.add(normalized_file_path)

            official_version = self._extract_embedded_version(file_path) or ""
            if not official_version:
                if metrics is not None:
                    metrics["files_without_embedded_version"] = metrics.get("files_without_embedded_version", 0) + 1
                continue

            for lookup_candidate in lookup_candidates:
                self._remember_relative_path(lookup_candidate, relative_hint)

            if metrics is not None:
                metrics["progress_repository_hits"] = metrics.get("progress_repository_hits", 0) + 1

            return {
                "requested_program": os.path.basename(file_path).upper(),
                "file_path": file_path,
                "official_version": official_version,
                "version_folder": base_version,
                "folder_name": progress_folder_name,
            }

        for candidate_directory in self._iter_candidate_directories_from_root(progress_search_root, directory_hints):
            for candidate in lookup_candidates:
                file_path = self._search_program_in_directory(candidate_directory, candidate)
                if not file_path:
                    continue
                normalized_file_path = os.path.normcase(file_path)
                if normalized_file_path in attempted_file_paths:
                    continue
                attempted_file_paths.add(normalized_file_path)

                official_version = self._extract_embedded_version(file_path) or ""
                if not official_version:
                    if metrics is not None:
                        metrics["files_without_embedded_version"] = metrics.get("files_without_embedded_version", 0) + 1
                    continue

                relative_path = os.path.relpath(file_path, progress_search_root)
                self._remember_relative_path(candidate, relative_path)

                if metrics is not None:
                    metrics["progress_repository_hits"] = metrics.get("progress_repository_hits", 0) + 1

                return {
                    "requested_program": candidate,
                    "file_path": file_path,
                    "official_version": official_version,
                    "version_folder": base_version,
                    "folder_name": progress_folder_name,
                }

        return None

    @staticmethod
    def extract_header(content: str) -> dict:
        header: dict = {}

        for key, label in [
            ("criado_por", r"Criado por\s*\.+:\s*(.+)"),
            ("criado_em", r"Criado em\s*\.+:\s*(.+)"),
            ("empresa", r"Empresa\s*\.+:\s*(.+)"),
            ("progress", r"Progress\s*\.+:\s*(.+)"),
        ]:
            match = re.search(label, content)
            if match:
                header[key] = match.group(1).strip()

        match = re.search(r"Versao Produto\s*\.:\s*(.+)", content)
        if match:
            header["versao_produto_completa"] = match.group(1).strip()

        match = re.search(r"Versao Produto\s*\.:.*?(\d+\.\d+\.\d+(?:\.\d+)?)", content)
        if match:
            header["versao_produto"] = match.group(1).strip()

        return header

    @staticmethod
    def extract_product_version(content: str) -> str:
        header_match = re.search(r"Versao Produto\s*\.:(.*)", content)
        if not header_match:
            raise ValueError("Extrato nao possui versao no cabecalho.")

        header_value = header_match.group(1).strip()
        if not header_value:
            raise ValueError("Extrato nao possui versao no cabecalho.")

        version_match = re.search(r"(\d+\.\d+\.\d+(?:\.\d+)?)", header_value)
        if not version_match:
            raise ValueError("Extrato nao possui versao no cabecalho.")

        return version_match.group(1).strip()

    @staticmethod
    def extract_all_client_data(content: str) -> dict:
        lines = content.splitlines()

        sources: Dict[str, dict] = {}
        programs_with_appc: List[dict] = []
        programs_with_upc: List[dict] = []
        programs_with_dpc: List[dict] = []
        especificos: List[dict] = []
        funcoes_ativas: List[dict] = []
        execucoes: List[dict] = []
        databases: List[str] = []
        aliases: List[dict] = []

        current_program: str | None = None
        in_program_section = False
        program_section_started = False

        p_prog = re.compile(
            r"^([A-Za-z0-9/\\_\-\.]+)\s+"
            r"(\S+)\s+"
            r"(\S+)\s+"
            r"(\d{2}/\d{2}/\d{2})\s+"
            r"(\d{2}:\d{2}:\d{2})"
        )
        p_func = re.compile(
            r"^([A-Za-z0-9_\-]+)\s+"
            r"(\S+\.p[y]?)\s+"
            r"(\S+)\s+"
            r"(\d{2}/\d{2}/\d{2})\s+"
            r"(\d{2}:\d{2}:\d{2})"
        )
        p_appc = re.compile(r"^\s+APPC\s*:\s*(.+)", re.IGNORECASE)
        p_spp = re.compile(r"^(SPP_\S+)\s+(\S+)\s*$")
        p_upc = re.compile(r"^\s+UPC\s*:\s*(.+)", re.IGNORECASE)
        p_dpc = re.compile(r"^\s+DPC\s*:\s*(.+)", re.IGNORECASE)
        p_espec = re.compile(r"^\s+ESPEC\s*:\s*(.+)", re.IGNORECASE)
        p_sep = re.compile(r"^[-=]{5,}$")
        p_exec = re.compile(r"Inicio Execu.*?:\s*(.+)", re.IGNORECASE)

        skip_prefixes = (
            "*", "Criado", "Versao Produto", "Empresa", "Progress",
            "Programa ", "-----",
        )

        for line in lines:
            stripped = line.strip()

            if PROGRAM_HEADER_RE.match(stripped):
                in_program_section = True
                program_section_started = True
                current_program = None
                continue

            if program_section_started and TERMINAL_SECTION_RE.match(stripped):
                break

            if not stripped:
                continue

            if p_sep.match(stripped):
                continue

            if not in_program_section:
                fallback_program_match = p_prog.match(stripped)
                if fallback_program_match:
                    in_program_section = True
                else:
                    continue

            if any(stripped.startswith(prefix) for prefix in skip_prefixes):
                continue

            appc_match = p_appc.match(line)
            if appc_match and current_program:
                appc_path = appc_match.group(1).strip()
                programs_with_appc.append({"programa": current_program, "caminho": appc_path, "tipo": "APPC"})
                source = sources.get(current_program)
                if source is not None:
                    source["appc"] = appc_path
                continue

            upc_match = p_upc.match(line)
            if upc_match and current_program:
                upc_path = upc_match.group(1).strip()
                programs_with_upc.append({"programa": current_program, "caminho": upc_path, "tipo": "UPC"})
                source = sources.get(current_program)
                if source is not None:
                    source["upc"] = upc_path
                continue

            dpc_match = p_dpc.match(line)
            if dpc_match and current_program:
                programs_with_dpc.append({"programa": current_program, "caminho": dpc_match.group(1).strip()})
                continue

            espec_match = p_espec.match(line)
            if espec_match and current_program:
                especificos.append({"programa": current_program, "caminho": espec_match.group(1).strip()})
                continue

            spp_match = p_spp.match(stripped)
            if spp_match:
                funcoes_ativas.append(VersionCompareService._build_active_function_entry(
                    funcao=spp_match.group(1),
                    valor=spp_match.group(2),
                ))
                continue

            pipe_function_match = PIPE_FUNCTION_RE.match(stripped)
            if pipe_function_match:
                funcoes_ativas.append(VersionCompareService._build_active_function_entry(
                    funcao=pipe_function_match.group("funcao"),
                    valor=pipe_function_match.group("valor"),
                    origem=pipe_function_match.group("contexto"),
                    programa=pipe_function_match.group("programa"),
                ))
                continue

            simple_function_match = SIMPLE_FUNCTION_RE.match(stripped)
            if simple_function_match:
                funcoes_ativas.append(VersionCompareService._build_active_function_entry(
                    funcao=simple_function_match.group("funcao"),
                    valor=simple_function_match.group("valor"),
                ))
                continue

            exec_match = p_exec.search(stripped)
            if exec_match:
                execucoes.append({"nome": exec_match.group(1).strip()})
                continue

            program_match = p_prog.match(stripped)
            if program_match:
                program_raw = program_match.group(1).strip()
                version = program_match.group(2).strip()
                parent = program_match.group(3).strip()
                date = program_match.group(4).strip()
                time_ = program_match.group(5).strip()
                key = os.path.basename(program_raw.replace("\\", "/")).upper()

                try:
                    VersionCompareService._version_tuple(version)
                except ValueError:
                    continue

                if key not in sources or VersionCompareService._version_tuple(version) > VersionCompareService._version_tuple(sources[key]["versao"]):
                    sources[key] = {
                        "programa": key,
                        "programa_original": program_raw,
                        "versao": version,
                        "programa_pai": parent,
                        "data": date,
                        "hora": time_,
                    }

                current_program = key
                continue

            function_match = p_func.match(stripped)
            if function_match:
                key = function_match.group(1).strip().upper()
                path = function_match.group(2).strip()
                version = function_match.group(3).strip()
                date = function_match.group(4).strip()
                time_ = function_match.group(5).strip()

                try:
                    VersionCompareService._version_tuple(version)
                except ValueError:
                    continue

                if key not in sources or VersionCompareService._version_tuple(version) > VersionCompareService._version_tuple(sources[key]["versao"]):
                    sources[key] = {
                        "programa": key,
                        "programa_original": function_match.group(1).strip(),
                        "versao": version,
                        "caminho": path,
                        "data": date,
                        "hora": time_,
                    }

                current_program = key
                continue

        return {
            "sources": sources,
            "programs_with_appc": programs_with_appc,
            "programs_with_upc": programs_with_upc,
            "upc_program_names": sorted({item["programa"] for item in programs_with_upc}),
            "programs_with_dpc": programs_with_dpc,
            "especificos": especificos,
            "funcoes_ativas": funcoes_ativas,
            "execucoes": execucoes,
            "databases": sorted(set(databases)),
            "aliases": aliases,
        }

    def compare_versions(
        self,
        product_version: str,
        client_sources: Dict[str, Dict[str, str]],
        upc_program_names: List[str],
    ) -> dict:
        compare_start = monotonic()
        candidate_versions = self._candidate_versions(product_version)
        metrics: Dict[str, int] = {
            "candidate_versions": len(candidate_versions),
            "programs_seen": len(client_sources),
            "full_index_lookups": 0,
            "direct_path_hits": 0,
            "targeted_directory_hits": 0,
            "primary_index_hits": 0,
            "files_without_embedded_version": 0,
            "skipped_known_programs": 0,
            "progress_repository_hits": 0,
        }
        result: dict = {
            "desatualizados": [],
            "ok": [],
            "adiantado_customizado": [],
            "nao_encontrado": [],
            "index_warning": None,
        }

        progress_search_root = self._get_progress_bin_gui_path(product_version)

        if not candidate_versions and not progress_search_root:
            result["index_warning"] = (
                f"Nenhuma pasta encontrada para a versao base {product_version} "
                f"em {self.base_lib_directory} ou {self.progress_lib_directory}."
            )
            for source_key, source_info in client_sources.items():
                if source_key in upc_program_names:
                    continue
                result["nao_encontrado"].append({
                    "programa": source_key,
                    "cliente": source_info.get("versao", ""),
                })
            result["compare_metrics"] = {
                **metrics,
                "compare_versions_ms": round((monotonic() - compare_start) * 1000, 2),
            }
            return result

        for source_key, source_info in client_sources.items():
            if source_key in upc_program_names:
                continue

            client_version = str(source_info.get("versao", "")).strip()
            if not client_version:
                result["nao_encontrado"].append({"programa": source_key, "cliente": ""})
                continue

            lookup_candidates = self._build_lookup_candidates(source_key, source_info)
            relative_path_hints = self._build_relative_path_hints(
                source_key,
                source_info,
                lookup_candidates,
            )
            directory_hints = self._build_directory_hints(
                source_key,
                source_info,
                lookup_candidates,
                relative_path_hints,
            )
            reference = self._find_reference_program(
                product_version,
                candidate_versions,
                lookup_candidates,
                relative_path_hints,
                directory_hints,
                metrics,
            )

            if not reference or not reference.get("official_version"):
                if self._should_skip_program_without_embedded_version(lookup_candidates):
                    metrics["skipped_known_programs"] = metrics.get("skipped_known_programs", 0) + 1
                    continue

                result["nao_encontrado"].append({
                    "programa": source_key,
                    "cliente": client_version,
                })
                continue

            official_version = str(reference["official_version"])
            client_tuple = self._version_tuple(client_version)
            official_tuple = self._version_tuple(official_version)
            build_diff = abs(official_tuple[-1] - client_tuple[-1])
            common_entry = {
                "programa": source_key,
                "cliente": client_version,
                "fix_encontrada": reference["folder_name"],
                "caminho_encontrado": reference["file_path"],
                "versao_encontrada": official_version,
            }

            if client_tuple < official_tuple:
                result["desatualizados"].append({
                    **common_entry,
                    "deveria_estar": official_version,
                    "diferenca_builds": build_diff,
                })
            elif client_tuple > official_tuple:
                result["adiantado_customizado"].append({
                    **common_entry,
                    "referencia_oficial": official_version,
                    "diferenca_builds": build_diff,
                })
            else:
                result["ok"].append({
                    **common_entry,
                    "referencia_oficial": official_version,
                })

        result["compare_metrics"] = {
            **metrics,
            "programs_compared": len(result["desatualizados"]) + len(result["ok"]) + len(result["adiantado_customizado"]),
            "compare_versions_ms": round((monotonic() - compare_start) * 1000, 2),
        }
        return result

    def compare_content(self, content: str) -> dict:
        total_start = monotonic()
        header_start = monotonic()
        header = self.extract_header(content)
        header_ms = round((monotonic() - header_start) * 1000, 2)

        version_start = monotonic()
        product_version = ""
        version_warning: str | None = None
        product_version_missing = False
        try:
            product_version = self.extract_product_version(content)
        except ValueError as exc:
            product_version_missing = True
            version_warning = (
                f"{exc} A comparacao de versoes nao foi executada, mas os dados extras do extrato foram carregados."
            )
        product_version_ms = round((monotonic() - version_start) * 1000, 2)

        parse_start = monotonic()
        client_data = self.extract_all_client_data(content)
        parse_client_data_ms = round((monotonic() - parse_start) * 1000, 2)

        compare_start = monotonic()
        if product_version:
            comparison = self.compare_versions(
                product_version,
                client_data["sources"],
                client_data["upc_program_names"],
            )
        else:
            comparison = {
                "desatualizados": [],
                "ok": [],
                "adiantado_customizado": [],
                "nao_encontrado": [],
                "index_warning": version_warning,
                "compare_metrics": {
                    "candidate_versions": 0,
                    "programs_seen": len(client_data["sources"]),
                    "full_index_lookups": 0,
                    "direct_path_hits": 0,
                    "targeted_directory_hits": 0,
                    "primary_index_hits": 0,
                    "files_without_embedded_version": 0,
                    "skipped_known_programs": 0,
                    "progress_repository_hits": 0,
                    "programs_compared": 0,
                    "compare_versions_ms": 0,
                },
            }
        compare_versions_ms = round((monotonic() - compare_start) * 1000, 2)

        summary = {
            "total_programas_cliente": len(client_data["sources"]),
            "total_comparados": (
                len(comparison["desatualizados"])
                + len(comparison["ok"])
                + len(comparison["adiantado_customizado"])
            ),
            "desatualizados": len(comparison["desatualizados"]),
            "ok": len(comparison["ok"]),
            "adiantado_customizado": len(comparison["adiantado_customizado"]),
            "nao_encontrado": len(comparison["nao_encontrado"]),
            "com_appc": len(client_data["programs_with_appc"]),
            "com_upc": len(client_data["programs_with_upc"]),
            "com_dpc": len(client_data["programs_with_dpc"]),
            "especificos": len(client_data["especificos"]),
            "funcoes_ativas": len(client_data["funcoes_ativas"]),
        }

        timings = {
            "extract_header_ms": header_ms,
            "extract_product_version_ms": product_version_ms,
            "extract_client_data_ms": parse_client_data_ms,
            "compare_versions_ms": compare_versions_ms,
            "total_compare_content_ms": round((monotonic() - total_start) * 1000, 2),
        }

        compare_metrics = comparison.pop("compare_metrics", {})

        return {
            "product_version": product_version,
            "product_version_missing": product_version_missing,
            "product_version_warning": version_warning,
            "header": header,
            "summary": summary,
            **comparison,
            "programas_com_appc": client_data["programs_with_appc"],
            "programas_com_upc": client_data["programs_with_upc"],
            "programas_com_dpc": client_data["programs_with_dpc"],
            "especificos": client_data["especificos"],
            "funcoes_ativas": client_data["funcoes_ativas"],
            "execucoes": client_data["execucoes"],
            "databases": client_data["databases"],
            "aliases": client_data["aliases"],
            "programas_detalhe": list(client_data["sources"].values()),
            "index_info": self.get_index_metadata(),
            "timings": timings,
            "compare_metrics": compare_metrics,
        }

    def get_index_metadata(self) -> dict:
        indexed_versions = sorted(
            self.version_folder_names.values(),
            key=lambda item: self._version_tuple(VERSION_FOLDER_RE.match(item).group("version")) if VERSION_FOLDER_RE.match(item) else (0,),
            reverse=True,
        )
        return {
            "base_lib_directory": self.base_lib_directory,
            "progress_lib_directory": self.progress_lib_directory,
            "directory_exists": os.path.isdir(self.base_lib_directory),
            "progress_directory_exists": os.path.isdir(self.progress_lib_directory),
            "versoes_indexadas": indexed_versions,
            "total_versoes": len(self.version_directories),
            "total_programas_indexados": sum(len(programs) for programs in self.program_file_cache.values()),
        }


version_compare_service = VersionCompareService()
