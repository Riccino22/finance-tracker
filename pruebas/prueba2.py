from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("6495121 (1) copy.pdf")
print(result.document.export_to_markdown())