import json
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path('backend').resolve()))
from version_compare_service import VersionCompareService

files = [
    Path(r'c:\Users\thaizy.castro\Downloads\ext_ver - 2026-03-17T160406.490.log'),
    Path(r'c:\Users\thaizy.castro\Downloads\ext_ver - 2026-03-13T162512.878.log'),
    Path(r'c:\Users\thaizy.castro\Downloads\ext_ver 4 (1).log'),
]

service = VersionCompareService()
for path in files:
    content = path.read_text(encoding='utf-8', errors='ignore')
    header = service.extract_header(content)
    started = time.perf_counter()
    try:
        result = service.compare_content(content)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        summary = result['summary']
        print(json.dumps({
            'file': str(path.name),
            'header_product_version': header.get('versao_produto'),
            'product_version': result.get('product_version'),
            'elapsed_ms': elapsed_ms,
            'summary': summary,
            'sample_not_found': result['nao_encontrado'][:5],
            'sample_outdated': result['desatualizados'][:3],
        }, ensure_ascii=False))
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        print(json.dumps({
            'file': str(path.name),
            'header_product_version': header.get('versao_produto'),
            'elapsed_ms': elapsed_ms,
            'error': str(exc),
        }, ensure_ascii=False))
