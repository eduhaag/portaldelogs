# -*- coding: utf-8 -*-
"""
===============================
ProfilerAnalyzer - O detetive dos .out!
===============================
Aqui a gente investiga arquivos de profiler, faz contas, organiza tudo e ainda deixa pronto para análise.
Comentários didáticos e um toque de humor para quem for encarar o legado Progress.

Baseado principalmente em:
- importTTProfileSessionProf
- importTTSourceProf
- importTTCallTreeDataProf
- importTTTotaisProf
- cálculos finais de ImportDataProf
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import math
import shlex


@dataclass
class ProfileSession:
    version: int
    date: str
    description: str
    time: str
    user: str
    total_time: float = 0.0


@dataclass
class Source:
    srcid: int
    name: str
    listname: str = ""
    crc_val: int = 0
    call_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    cumulative_time: float = 0.0
    session_percent: float = 0.0
    first_line: int = 0
    srcfile: str = ""
    line_stats: List[Dict[str, Any]] = field(default_factory=list)


class ProgressProfilerParser:
    def __init__(self, content: str):
        self.lines = [line.strip() for line in content.splitlines() if line.strip()]
        self.session: Optional[ProfileSession] = None
        self.sources: Dict[int, Source] = {}
        self.calltree: List[Tuple[int, int, int, int]] = []
        self.totals: List[Tuple[int, int, int, float, float]] = []
        self.trace_info: List[Tuple[int, int, float, float]] = []

    def parse(self):
        if not self.lines:
            raise ValueError("Arquivo profiler vazio")

        cursor = 0
        self.session, cursor = self._parse_session_header(cursor)
        cursor = self._skip_separator(cursor)
        cursor = self._parse_sources(cursor)
        cursor = self._skip_separator(cursor)
        cursor = self._parse_call_tree(cursor)
        cursor = self._skip_separator(cursor)
        cursor = self._parse_totals(cursor)
        cursor = self._skip_separator(cursor)
        cursor = self._parse_trace_info(cursor)
        self._calculate_statistics()

    def _skip_separator(self, cursor: int) -> int:
        while cursor < len(self.lines) and self.lines[cursor] == '.':
            cursor += 1
        return cursor

    def _parse_session_header(self, cursor: int) -> Tuple[ProfileSession, int]:
        raw_line = self.lines[cursor]

        # Extract JSON metadata if present (profiler v3+)
        json_meta = {}
        header_part = raw_line
        json_start = raw_line.find(' {')
        if json_start >= 0:
            json_str = raw_line[json_start + 1:]
            header_part = raw_line[:json_start]
            import json as _json
            try:
                json_meta = _json.loads(json_str)
            except Exception:
                pass

        # Custom tokenizer for the header: handles quoted strings
        tokens = []
        i = 0
        h = header_part.strip()
        while i < len(h):
            if h[i] == '"':
                end = h.find('"', i + 1)
                if end == -1:
                    end = len(h)
                tokens.append(h[i + 1:end])
                i = end + 1
            elif h[i] == ' ':
                i += 1
            else:
                end = h.find(' ', i)
                if end == -1:
                    end = len(h)
                tokens.append(h[i:end])
                i = end

        if len(tokens) < 3 or not self._is_int(tokens[0]):
            raise ValueError("Cabeçalho do profiler inválido")

        session = ProfileSession(
            version=int(tokens[0]),
            date=tokens[1] if len(tokens) > 1 else "",
            description=tokens[2] if len(tokens) > 2 else "",
            time=tokens[3] if len(tokens) > 3 else "",
            user=tokens[4] if len(tokens) > 4 else "",
        )

        if 'TotTime' in json_meta:
            session.total_time = float(json_meta['TotTime'])

        return session, cursor + 1

    def _parse_sources(self, cursor: int) -> int:
        while cursor < len(self.lines):
            if self.lines[cursor] == '.':
                break
            tokens = self._tokenize_line(self.lines[cursor])
            if not self._looks_like_source(tokens):
                break

            srcid = int(tokens[0])
            srcname = tokens[1]
            listname = tokens[2] if len(tokens) >= 3 else ""
            # v3 format: srcid "name" "listname" start_line end_line "flags"
            crc_val = 0
            if len(tokens) >= 5 and self._is_int(tokens[3]) and self._is_int(tokens[4]):
                crc_val = int(tokens[4])
            elif self._is_int(tokens[-1]):
                crc_val = int(tokens[-1])

            self.sources[srcid] = Source(
                srcid=srcid,
                name=srcname,
                listname=listname,
                crc_val=crc_val,
                srcfile=self._extract_srcfile(srcname),
            )
            cursor += 1

        return cursor

    def _parse_call_tree(self, cursor: int) -> int:
        while cursor < len(self.lines):
            if self.lines[cursor] == '.':
                break
            tokens = self._tokenize_line(self.lines[cursor])
            if not self._looks_like_call_tree(tokens):
                break

            caller, caller_line, callee, callcnt = (int(token) for token in tokens[:4])
            self.calltree.append((caller, caller_line, callee, callcnt))
            cursor += 1

        return cursor

    def _parse_totals(self, cursor: int) -> int:
        while cursor < len(self.lines):
            if self.lines[cursor] == '.':
                break
            tokens = self._tokenize_line(self.lines[cursor])
            if not self._looks_like_totals(tokens):
                break

            self.totals.append(
                (
                    int(tokens[0]),
                    int(tokens[1]),
                    int(tokens[2]),
                    float(tokens[3]),
                    float(tokens[4]),
                )
            )
            cursor += 1

        return cursor

    def _parse_trace_info(self, cursor: int) -> int:
        while cursor < len(self.lines):
            if self.lines[cursor] == '.':
                break
            tokens = self._tokenize_line(self.lines[cursor])
            if len(tokens) == 4 and self._is_int(tokens[0]) and self._is_int(tokens[1]) and self._is_float(tokens[2]) and self._is_float(tokens[3]):
                self.trace_info.append((int(tokens[0]), int(tokens[1]), float(tokens[2]), float(tokens[3])))
                cursor += 1
                continue
            break

        return cursor

    def _calculate_statistics(self):
        if not self.session:
            raise ValueError("Sessão do profiler não inicializada")

        for caller, caller_line, callee, callcnt in self.calltree:
            if callee in self.sources:
                self.sources[callee].call_count += callcnt

        for srcid, lineno, stmtcnt, tot_acttime, cumtime in self.totals:
            source = self.sources.get(srcid)
            if source:
                source.total_time += tot_acttime
                if lineno > 0:
                    source.line_stats.append(
                        {
                            "srcid": srcid,
                            "line": lineno,
                            "calls": stmtcnt,
                            "time_total_ms": tot_acttime,
                            "time_avg_ms": (tot_acttime / stmtcnt) if stmtcnt else 0.0,
                            "cum_time_ms": cumtime,
                        }
                    )
                    if source.first_line == 0:
                        source.first_line = lineno
                elif lineno == 0:
                    source.cumulative_time = cumtime

            if lineno == 0 and srcid in (0, 1):
                self.session.total_time = max(self.session.total_time, cumtime)

        if self.session.total_time == 0:
            self.session.total_time = sum(source.total_time for source in self.sources.values())

        for source in self.sources.values():
            if source.call_count > 0:
                source.avg_time = source.total_time / source.call_count
            if self.session.total_time > 0:
                source.session_percent = (source.total_time * 100.0) / self.session.total_time
            if source.cumulative_time == 0:
                source.cumulative_time = source.total_time
            if source.first_line == 0:
                source.first_line = 1

    def to_raw_data(self) -> Dict[str, Any]:
        modules = []
        lines = []
        edges = []

        for source in sorted(self.sources.values(), key=lambda item: item.total_time, reverse=True):
            modules.append(
                {
                    "srcid": source.srcid,
                    "module": source.name,
                    "procedure": source.name,
                    "calls": source.call_count,
                    "time_total_ms": source.total_time,
                    "time_avg_ms": source.avg_time,
                    "time_cumulative_ms": source.cumulative_time,
                    "percent": source.session_percent,
                    "listname": source.listname,
                    "srcfile": source.srcfile,
                    "first_line": source.first_line,
                }
            )
            lines.extend(
                {
                    "module": source.name,
                    **line_stat,
                }
                for line_stat in source.line_stats
            )

        for caller, caller_line, callee, callcnt in self.calltree:
            caller_src = self.sources.get(caller)
            callee_src = self.sources.get(callee)
            edges.append(
                {
                    "caller": caller_src.name if caller_src else str(caller),
                    "caller_id": caller,
                    "caller_line": caller_line,
                    "callee": callee_src.name if callee_src else str(callee),
                    "callee_id": callee,
                    "calls": callcnt,
                    "time_total_ms": callee_src.total_time if callee_src else 0.0,
                }
            )

        return {
            "session": {
                "version": self.session.version if self.session else 0,
                "date": self.session.date if self.session else "",
                "description": self.session.description if self.session else "",
                "time": self.session.time if self.session else "",
                "user": self.session.user if self.session else "",
                "total_time": self.session.total_time if self.session else 0.0,
            },
            "modules": modules,
            "lines": sorted(lines, key=lambda item: item.get("time_total_ms", 0), reverse=True),
            "call_tree_edges": edges,
            "trace_info_count": len(self.trace_info),
        }

    @staticmethod
    def _tokenize_line(line: str) -> List[str]:
        try:
            return shlex.split(line, posix=True)
        except ValueError:
            return line.split()

    @staticmethod
    def _is_int(value: str) -> bool:
        try:
            int(value)
            return True
        except Exception:
            return False

    @staticmethod
    def _is_float(value: str) -> bool:
        try:
            float(value)
            return True
        except Exception:
            return False

    def _looks_like_source(self, tokens: List[str]) -> bool:
        if len(tokens) < 3:
            return False
        if not self._is_int(tokens[0]):
            return False
        # At least one token must be non-integer (the source name)
        if all(self._is_int(t) or self._is_float(t) for t in tokens):
            return False
        return True

    def _looks_like_call_tree(self, tokens: List[str]) -> bool:
        return len(tokens) == 4 and all(self._is_int(token) for token in tokens)

    def _looks_like_totals(self, tokens: List[str]) -> bool:
        return (
            len(tokens) == 5
            and self._is_int(tokens[0])
            and self._is_int(tokens[1])
            and self._is_int(tokens[2])
            and self._is_float(tokens[3])
            and self._is_float(tokens[4])
        )

    @staticmethod
    def _extract_srcfile(srcname: str) -> str:
        if " " in srcname:
            return srcname.rsplit(" ", 1)[-1]
        return srcname


def classify_severity(percent: float) -> str:
    if percent >= 40:
        return "critical"
    if percent >= 20:
        return "high"
    if percent >= 10:
        return "medium"
    if percent >= 5:
        return "low"
    return "minimal"


def intelligent_ranking(sources: Dict[int, Source], limit: int = 10) -> List[Dict[str, Any]]:
    ranking = []
    for source in sources.values():
        impact = source.total_time * math.log(source.call_count + 1)
        ranking.append(
            {
                "procedure": source.name,
                "calls": source.call_count,
                "total_time": source.total_time,
                "avg_time": source.avg_time,
                "percent": source.session_percent,
                "impact_score": round(impact, 4),
                "severity": classify_severity(source.session_percent),
            }
        )

    ranking.sort(key=lambda item: item["impact_score"], reverse=True)
    return ranking[:limit]


def detect_n_plus_one(sources: Dict[int, Source]) -> List[Dict[str, Any]]:
    suspects = []
    for source in sources.values():
        if source.call_count >= 100 and source.avg_time <= 0.01:
            suspects.append(
                {
                    "procedure": source.name,
                    "calls": source.call_count,
                    "avg_time": source.avg_time,
                    "percent": source.session_percent,
                }
            )
    return suspects


def session_health_score(sources: Dict[int, Source]) -> float:
    if not sources:
        return 100.0

    critical_count = sum(1 for source in sources.values() if source.session_percent >= 30)
    max_concentration = max((source.session_percent for source in sources.values()), default=0)

    score = 100.0
    score -= critical_count * 10
    score -= max_concentration * 0.5
    return max(0.0, round(score, 2))


def build_call_tree(parser: ProgressProfilerParser) -> List[Dict[str, Any]]:
    nodes: Dict[int, Dict[str, Any]] = {}

    for source in parser.sources.values():
        nodes[source.srcid] = {
            "id": source.srcid,
            "name": source.name,
            "calls": source.call_count,
            "total_time": source.total_time,
            "percent": round(source.session_percent, 2),
            "children": [],
        }

    for caller, _caller_line, callee, _callcnt in parser.calltree:
        if caller in nodes and callee in nodes and nodes[callee] not in nodes[caller]["children"]:
            nodes[caller]["children"].append(nodes[callee])

    called_ids = {callee for _, _, callee, _ in parser.calltree}
    return [node for srcid, node in nodes.items() if srcid not in called_ids]


def analyze_profiler_data(parser: ProgressProfilerParser) -> Dict[str, Any]:
    raw_data = parser.to_raw_data()
    modules = raw_data["modules"]
    lines = raw_data["lines"]
    edges = raw_data["call_tree_edges"]

    top_modules_by_time = sorted(modules, key=lambda item: item.get("time_total_ms", 0), reverse=True)[:10]
    top_modules_by_calls = sorted(modules, key=lambda item: item.get("calls", 0), reverse=True)[:10]
    top_modules_by_avg_time = sorted(modules, key=lambda item: item.get("time_avg_ms", 0), reverse=True)[:10]
    top_lines = sorted(lines, key=lambda item: item.get("time_total_ms", 0), reverse=True)[:10]

    problematic_modules = []
    for module in modules:
        issues = []
        if module.get("time_avg_ms", 0) > 1.0:
            issues.append(f"Alto tempo médio: {module['time_avg_ms']:.4f}ms")
        if module.get("calls", 0) > 1000:
            issues.append(f"Muitas chamadas: {module['calls']:,}")
        if module.get("time_total_ms", 0) > 500:
            issues.append(f"Alto tempo total: {module['time_total_ms']:.4f}ms")
        if issues:
            problematic_modules.append(
                {
                    "module": module["module"],
                    "issues": issues,
                    "calls": module.get("calls", 0),
                    "time_total_ms": module.get("time_total_ms", 0),
                    "time_avg_ms": module.get("time_avg_ms", 0),
                }
            )

    recommendations = []
    if problematic_modules:
        recommendations.append(f"📊 {len(problematic_modules)} módulo(s) com indício de gargalo")
    if any(module.get("time_avg_ms", 0) > 2.0 for module in modules):
        recommendations.append("⚠️ Há módulos com tempo médio acima de 2ms")
    if any(module.get("calls", 0) > 2000 for module in modules):
        recommendations.append("🔄 Há módulos com volume de chamadas muito alto")
    if parser.session and parser.session.total_time > 5000:
        recommendations.append(f"🕒 Tempo total elevado: {parser.session.total_time / 1000:.2f}s")
    if not recommendations:
        recommendations.append("✅ Sessão de profiler dentro dos parâmetros esperados")

    return {
        "session": raw_data["session"],
        "summary": {
            "total_modules": len(modules),
            "total_lines": len(lines),
            "total_calls": sum(module.get("calls", 0) for module in modules),
            "total_time_ms": parser.session.total_time if parser.session else 0.0,
            "avg_time_per_call": (
                (sum(module.get("time_total_ms", 0) for module in modules) / sum(module.get("calls", 0) for module in modules))
                if sum(module.get("calls", 0) for module in modules) > 0
                else 0.0
            ),
            "health_score": session_health_score(parser.sources),
            "trace_info_count": raw_data["trace_info_count"],
        },
        "top_modules_by_time": top_modules_by_time,
        "top_modules_by_calls": top_modules_by_calls,
        "top_modules_by_avg_time": top_modules_by_avg_time,
        "top_lines": top_lines,
        "problematic_modules": problematic_modules[:10],
        "call_tree_stats": {
            "total_relationships": len(edges),
            "unique_callers": len({edge.get("caller") for edge in edges}),
            "unique_callees": len({edge.get("callee") for edge in edges}),
        },
        "recommendations": recommendations,
    }


class ProfilerAnalyzer:
    def analyze_file_content(self, content: str) -> Dict[str, Any]:
        try:
            parser = ProgressProfilerParser(content)
            parser.parse()

            analysis = analyze_profiler_data(parser)
            call_tree = build_call_tree(parser)
            top_bottlenecks = intelligent_ranking(parser.sources)
            n_plus_one_suspects = detect_n_plus_one(parser.sources)
            raw_data = parser.to_raw_data()

            return {
                "success": True,
                "session": analysis["session"],
                "summary": analysis["summary"],
                "top_bottlenecks": top_bottlenecks,
                "n_plus_one_suspects": n_plus_one_suspects,
                "call_tree": call_tree,
                "raw_data": raw_data,
                "analysis": {
                    **analysis,
                    "top_bottlenecks": top_bottlenecks,
                    "n_plus_one_suspects": n_plus_one_suspects,
                    "call_tree": call_tree,
                },
            }
        except Exception as exc:
            return {
                "success": False,
                "error": f"Erro ao analisar arquivo: {str(exc)}",
            }
