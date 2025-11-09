#!/usr/bin/env python3
"""
Create a simple test PDF for testing the chapter extraction.
"""
import fitz  # PyMuPDF

def create_test_pdf(output_path: str, num_pages: int = 5):
    """Create a simple test PDF with multiple pages."""
    doc = fitz.open()

    for i in range(num_pages):
        page = doc.new_page(width=595, height=842)  # A4 size

        # Add title
        text = f"Chapter {i + 1}\n\n"
        text += f"This is page {i + 1} of the test document.\n\n"
        text += "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        text += "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n\n"

        # Add some mathematical-looking content
        text += "Mathematical Content:\n"
        text += f"Theorem {i + 1}: Let $x \\in \\mathbb{{R}}$ be a real number.\n"
        text += f"Then $x^2 \\geq 0$ for all $x$.\n\n"
        text += "Proof: This follows from the definition of square.\n"

        # Insert text
        page.insert_text(
            (50, 50),
            text,
            fontsize=12,
            fontname="helv"
        )

    # Save PDF
    doc.save(output_path)
    doc.close()
    print(f"Created test PDF: {output_path} with {num_pages} pages")

if __name__ == "__main__":
    create_test_pdf("data/samples/test.pdf", num_pages=5)
