from pathlib import Path
import sys
import time

from rich import print
DEFAULT_PDF = Path(__file__).resolve().parents[2] / "data" / "invoice-1-3.pdf"


def preview(text: str, limit: int = 400) -> str:
	cleaned = " ".join(text.split())
	return cleaned[:limit] + ("..." if len(cleaned) > limit else "")


def run_docling(pdf_path: Path) -> dict:
	try:
		from docling.document_converter import DocumentConverter
	except ImportError as exc:
		raise RuntimeError("Install Docling with: pip install docling") from exc

	start = time.perf_counter()
	document = DocumentConverter().convert(str(pdf_path)).document
	text = document.export_to_markdown()
	return {
		"seconds": time.perf_counter() - start,
		"pages": len(getattr(document, "pages", {}) or {}),
		"characters": len(text),
		"preview": preview(text),
		"output": "Markdown with document structure",
	}


def run_liteparse(pdf_path: Path) -> dict:
	try:
		from liteparse import LiteParse
	except ImportError as exc:
		raise RuntimeError(
			"Install LiteParse with: npm install -g @llamaindex/liteparse && pip install liteparse"
		) from exc

	start = time.perf_counter()
	result = LiteParse().parse(str(pdf_path), ocr_enabled=True)
	pages = result.pages or []
	text_items = sum(len(page.textItems) for page in pages)
	return {
		"seconds": time.perf_counter() - start,
		"pages": len(pages),
		"characters": len(result.text),
		"preview": preview(result.text),
		"output": f"Plain text with {text_items} positioned text items",
	}


def print_report(name: str, report: dict) -> None:
	print(f"\n{name}")
	print("-" * len(name))
	print(f"Time: {report['seconds']:.2f}s")
	print(f"Pages: {report['pages']}")
	print(f"Characters: {report['characters']:,}")
	print(f"Output: {report['output']}")
	print(f"Preview: {report['preview']}")


def resolve_pdf_path() -> Path:
	chosen = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_PDF
	return chosen if chosen.is_absolute() else chosen.resolve()


def main() -> None:
	pdf_path = resolve_pdf_path()
	if not pdf_path.exists():
		raise SystemExit(f"PDF not found: {pdf_path}")

	print(f"Comparing Docling vs LiteParse on: {pdf_path}")
	reports = {}

	for name, runner in (("Docling", run_docling), ("LiteParse", run_liteparse)):
		try:
			reports[name] = runner(pdf_path)
		except Exception as exc:
			print(f"\n{name} failed: {exc}")

	for name in ("Docling", "LiteParse"):
		if name in reports:
			print_report(name, reports[name])

	if len(reports) == 2:
		fastest = min(reports, key=lambda parser: reports[parser]["seconds"])
		slowest = max(reports, key=lambda parser: reports[parser]["seconds"])
		gap = reports[slowest]["seconds"] - reports[fastest]["seconds"]
		print(f"\nFastest parser: {fastest} ({gap:.2f}s quicker than {slowest})")


if __name__ == "__main__":
	main()
