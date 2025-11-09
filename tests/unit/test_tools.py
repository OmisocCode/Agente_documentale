"""
Unit tests for tools (PDF, LaTeX, Template).
"""

import pytest
import tempfile
from pathlib import Path

from src.tools.latex_tools import LaTeXProcessor
from src.tools.template_tools import TemplateRenderer
from src.models.block import ClassifiedBlock, ClassifiedChapter
from src.models.enums import BlockType, BlockAction


class TestLaTeXProcessor:
    """Tests for LaTeX processing tools."""

    @pytest.fixture
    def processor(self):
        """Create LaTeX processor instance."""
        return LaTeXProcessor()

    def test_extract_inline_formula(self, processor):
        """Test extraction of inline formulas."""
        text = "The formula $x^2 + y^2 = r^2$ is the equation of a circle."

        formulas = processor.extract_formula(text)

        assert len(formulas) > 0
        assert "x^2 + y^2 = r^2" in [f["latex"] for f in formulas]

    def test_extract_display_formula(self, processor):
        """Test extraction of display formulas."""
        text = "The integral: $$\\int_0^1 x^2 dx = \\frac{1}{3}$$"

        formulas = processor.extract_formula(text)

        assert len(formulas) > 0
        # Check that we extracted something
        assert any("int" in f["latex"].lower() for f in formulas)

    def test_detect_theorem(self, processor):
        """Test theorem detection."""
        text = """
Theorem 1: Bézout's Identity
Let a and b be integers not both zero...
        """

        theorems = processor.detect_theorem_blocks(text)

        assert len(theorems) > 0
        assert theorems[0]["type"] == BlockType.THEOREM

    def test_detect_definition(self, processor):
        """Test definition detection."""
        text = """
Definition 1: Prime Number
A prime number is a natural number greater than 1...
        """

        definitions = processor.detect_definitions(text)

        assert len(definitions) > 0
        assert definitions[0]["type"] == BlockType.DEFINITION

    def test_detect_proof(self, processor):
        """Test proof detection."""
        text = """
Proof: We proceed by induction on n.
Base case: n = 1...
        """

        proofs = processor.detect_proofs(text)

        assert len(proofs) > 0
        assert proofs[0]["type"] == BlockType.PROOF

    def test_split_into_blocks(self, processor):
        """Test splitting text into blocks."""
        text = """
This is some narrative text explaining concepts.

Theorem 1: Test Theorem
This is the theorem statement.

More narrative text here.
        """

        blocks = processor.split_into_blocks(text)

        # Should have at least narrative and theorem blocks
        assert len(blocks) >= 2

        block_types = [b["type"] for b in blocks]
        assert BlockType.NARRATIVE in block_types
        assert BlockType.THEOREM in block_types

    def test_clean_latex(self, processor):
        """Test LaTeX cleaning."""
        dirty_latex = "  x  =  y  +  z  "
        clean = processor.clean_latex(dirty_latex)

        assert "=" in clean
        assert clean.count(" ") < dirty_latex.count(" ")

    def test_extract_unicode_math(self, processor):
        """Test Unicode math extraction."""
        text = "The sum ∑ᵢ₌₁ⁿ i² = n(n+1)(2n+1)/6"

        unicode_math = processor.extract_unicode_math(text)

        assert len(unicode_math) > 0

    def test_formula_confidence(self, processor):
        """Test formula confidence calculation."""
        # Formula with LaTeX commands should have high confidence
        high_conf_latex = "\\frac{1}{2} + \\sqrt{x}"
        confidence = processor._calculate_formula_confidence(high_conf_latex)

        assert confidence > 0.5

        # Simple text should have lower confidence
        low_conf_latex = "abc"
        confidence_low = processor._calculate_formula_confidence(low_conf_latex)

        assert confidence_low <= confidence


class TestTemplateRenderer:
    """Tests for template rendering."""

    @pytest.fixture
    def temp_template_dir(self):
        """Create temporary template directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup is automatic for temp dirs

    @pytest.fixture
    def renderer(self, temp_template_dir):
        """Create template renderer instance."""
        renderer = TemplateRenderer(template_dir=temp_template_dir)
        # Create default templates
        renderer.create_default_templates()
        return renderer

    @pytest.fixture
    def sample_chapter(self):
        """Create sample classified chapter."""
        blocks = [
            ClassifiedBlock(
                type=BlockType.NARRATIVE,
                content="This is introductory text.",
                action=BlockAction.SUMMARIZE,
            ),
            ClassifiedBlock(
                type=BlockType.THEOREM,
                content="Every even number greater than 2 is the sum of two primes.",
                action=BlockAction.VERBATIM,
                name="Goldbach's Conjecture",
            ),
            ClassifiedBlock(
                type=BlockType.FORMULA,
                content="$x^2 + y^2 = z^2$",
                action=BlockAction.LATEX,
                latex="x^2 + y^2 = z^2",
            ),
        ]

        return ClassifiedChapter(
            chapter_id="ch1",
            title="Introduction to Number Theory",
            blocks=blocks,
        )

    def test_create_default_templates(self, temp_template_dir):
        """Test default template creation."""
        renderer = TemplateRenderer(template_dir=temp_template_dir)
        renderer.create_default_templates()

        template_dir = Path(temp_template_dir)

        assert (template_dir / "chapter.html").exists()
        assert (template_dir / "index.html").exists()

    def test_render_chapter(self, renderer, sample_chapter):
        """Test chapter rendering."""
        html = renderer.render_chapter(sample_chapter)

        assert html is not None
        assert "Introduction to Number Theory" in html
        assert "Goldbach" in html

    def test_get_mathjax_config(self, renderer):
        """Test MathJax configuration generation."""
        config = renderer.get_mathjax_config()

        assert "MathJax" in config
        assert "cdn.jsdelivr.net" in config

    def test_inject_mathjax(self, renderer):
        """Test MathJax injection."""
        html = "<html><head></head><body>Test</body></html>"

        html_with_mathjax = renderer.inject_mathjax(html)

        assert "MathJax" in html_with_mathjax
        assert html_with_mathjax.count("<head>") == 1  # Should not duplicate head

    def test_select_css_theme(self, renderer):
        """Test CSS theme selection."""
        theme = renderer.select_css_theme("math-document")
        assert "math-document.css" in theme

        theme = renderer.select_css_theme("lecture-notes")
        assert "lecture-notes.css" in theme

        theme = renderer.select_css_theme("presentation")
        assert "presentation.css" in theme

    def test_generate_navigation(self, renderer):
        """Test navigation generation."""
        chapters = [
            ClassifiedChapter(chapter_id="ch1", title="Chapter 1", blocks=[]),
            ClassifiedChapter(chapter_id="ch2", title="Chapter 2", blocks=[]),
            ClassifiedChapter(chapter_id="ch3", title="Chapter 3", blocks=[]),
        ]

        # Navigation for middle chapter
        nav = renderer.generate_navigation(chapters, current_index=1)

        assert "prev" in nav
        assert "next" in nav
        assert "index" in nav

        assert nav["prev"]["id"] == "ch1"
        assert nav["next"]["id"] == "ch3"

    def test_navigation_first_chapter(self, renderer):
        """Test navigation for first chapter (no prev)."""
        chapters = [
            ClassifiedChapter(chapter_id="ch1", title="Chapter 1", blocks=[]),
            ClassifiedChapter(chapter_id="ch2", title="Chapter 2", blocks=[]),
        ]

        nav = renderer.generate_navigation(chapters, current_index=0)

        assert "prev" not in nav  # No previous chapter
        assert "next" in nav
        assert nav["next"]["id"] == "ch2"

    def test_navigation_last_chapter(self, renderer):
        """Test navigation for last chapter (no next)."""
        chapters = [
            ClassifiedChapter(chapter_id="ch1", title="Chapter 1", blocks=[]),
            ClassifiedChapter(chapter_id="ch2", title="Chapter 2", blocks=[]),
        ]

        nav = renderer.generate_navigation(chapters, current_index=1)

        assert "prev" in nav
        assert "next" not in nav  # No next chapter

    def test_render_index(self, renderer):
        """Test index page rendering."""
        chapters = [
            ClassifiedChapter(chapter_id="ch1", title="Chapter 1", blocks=[]),
            ClassifiedChapter(chapter_id="ch2", title="Chapter 2", blocks=[]),
        ]

        html = renderer.render_index(chapters, title="Test Document")

        assert "Test Document" in html
        assert "Chapter 1" in html
        assert "Chapter 2" in html

    def test_block_type_css_class(self, renderer):
        """Test block type to CSS class conversion."""
        css_class = renderer._block_type_to_css_class(BlockType.THEOREM)
        assert css_class == "block-theorem"

        css_class = renderer._block_type_to_css_class(BlockType.FORMULA)
        assert css_class == "block-formula"

    def test_render_latex_inline(self, renderer):
        """Test inline LaTeX rendering."""
        latex = "x^2 + y^2"
        rendered = renderer._render_latex_inline(latex)

        assert "\\(" in rendered
        assert "\\)" in rendered
        assert latex in rendered


# Note: PDF Tools tests would require actual PDF files
# For now, we skip those tests in the basic suite
class TestPDFExtractor:
    """Tests for PDF extraction (requires PDF files)."""

    def test_pdf_extractor_placeholder(self):
        """Placeholder test for PDF extractor."""
        # In a real test environment, you would:
        # 1. Create a sample PDF file
        # 2. Test extraction with PDFExtractor
        # 3. Verify extracted text, TOC, structure, etc.

        # For now, just ensure imports work
        from src.tools.pdf_tools import PDFExtractor

        assert PDFExtractor is not None

    # Additional tests would require:
    # - Sample PDF files in tests/fixtures/
    # - Tests for extract_text()
    # - Tests for detect_toc()
    # - Tests for detect_headings()
    # - Tests for analyze_structure()
    # - Tests for search_text()
