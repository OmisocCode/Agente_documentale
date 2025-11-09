"""
Template rendering tools for Composer Agent (Task 3).

Provides tools for rendering HTML templates, configuring MathJax,
selecting CSS themes, and generating navigation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

from src.models.block import ClassifiedChapter
from src.models.enums import BlockType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TemplateRenderer:
    """
    HTML template rendering with Jinja2.

    Handles rendering of chapter HTML, navigation, and MathJax integration.
    """

    def __init__(self, template_dir: str = "src/templates"):
        """
        Initialize template renderer.

        Args:
            template_dir: Directory containing Jinja2 templates
        """
        self.template_dir = Path(template_dir)

        # Create template directory if it doesn't exist
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["block_type_class"] = self._block_type_to_css_class
        self.env.filters["render_latex"] = self._render_latex_inline

        logger.info(f"Template renderer initialized with dir: {template_dir}")

    def _block_type_to_css_class(self, block_type: BlockType) -> str:
        """
        Convert block type to CSS class name.

        Args:
            block_type: BlockType enum

        Returns:
            CSS class name
        """
        return f"block-{block_type.value}"

    def _render_latex_inline(self, latex: str) -> str:
        """
        Wrap LaTeX for inline MathJax rendering.

        Args:
            latex: LaTeX string

        Returns:
            MathJax-compatible HTML
        """
        # Use \( \) for inline math
        return f"\\({latex}\\)"

    def render_template(
        self, template_name: str, context: Dict[str, Any]
    ) -> str:
        """
        Render a Jinja2 template.

        Args:
            template_name: Name of template file (e.g., "chapter.html")
            context: Template context dictionary

        Returns:
            Rendered HTML

        Example:
            >>> renderer = TemplateRenderer()
            >>> html = renderer.render_template("chapter.html", {"title": "Chapter 1"})
        """
        try:
            template = self.env.get_template(template_name)
            html = template.render(context)
            logger.debug(f"Rendered template: {template_name}")
            return html
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise

    def render_chapter(
        self,
        chapter: ClassifiedChapter,
        css_theme: str = "math-document",
        include_mathjax: bool = True,
        navigation: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Render a complete chapter HTML.

        Args:
            chapter: ClassifiedChapter to render
            css_theme: CSS theme name
            include_mathjax: Whether to include MathJax
            navigation: Navigation links (prev/next chapter)

        Returns:
            Complete HTML for chapter

        Example:
            >>> html = renderer.render_chapter(chapter, css_theme="lecture-notes")
        """
        context = {
            "chapter": chapter,
            "title": chapter.title,
            "css_theme": css_theme,
            "include_mathjax": include_mathjax,
            "mathjax_config": self.get_mathjax_config() if include_mathjax else None,
            "navigation": navigation or {},
            "has_math": chapter.has_mathematical_content(),
            "block_stats": {
                "total": chapter.get_block_count(),
                "theorems": len(chapter.get_theorems()),
                "definitions": len(chapter.get_definitions()),
                "formulas": len(chapter.get_formulas()),
            },
        }

        return self.render_template("chapter.html", context)

    def render_index(
        self,
        chapters: List[ClassifiedChapter],
        title: str = "Document Index",
        css_theme: str = "math-document",
    ) -> str:
        """
        Render index/table of contents page.

        Args:
            chapters: List of chapters
            title: Document title
            css_theme: CSS theme

        Returns:
            Index HTML
        """
        context = {
            "title": title,
            "chapters": chapters,
            "css_theme": css_theme,
            "total_chapters": len(chapters),
        }

        return self.render_template("index.html", context)

    def get_mathjax_config(self, version: str = "3.2.2") -> str:
        """
        Get MathJax configuration HTML.

        Args:
            version: MathJax version

        Returns:
            MathJax script tags
        """
        config = f"""
<script>
  MathJax = {{
    tex: {{
      inlineMath: [['\\\\(', '\\\\)']],
      displayMath: [['\\\\[', '\\\\]'], ['$$', '$$']],
      processEscapes: true,
      processEnvironments: true
    }},
    options: {{
      skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
    }}
  }};
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@{version}/es5/tex-mml-chtml.js"></script>
        """.strip()

        return config

    def inject_mathjax(self, html: str, version: str = "3.2.2") -> str:
        """
        Inject MathJax into existing HTML.

        Args:
            html: HTML content
            version: MathJax version

        Returns:
            HTML with MathJax injected
        """
        mathjax_config = self.get_mathjax_config(version)

        # Insert before closing </head> tag
        if "</head>" in html:
            html = html.replace("</head>", f"{mathjax_config}\n</head>")
        else:
            # Fallback: insert at beginning
            html = mathjax_config + "\n" + html

        return html

    def select_css_theme(self, document_type: str = "math-document") -> str:
        """
        Select CSS file based on document type.

        Args:
            document_type: Type of document (math-document, lecture-notes, presentation)

        Returns:
            Path to CSS file
        """
        theme_map = {
            "math-document": "css/math-document.css",
            "lecture-notes": "css/lecture-notes.css",
            "presentation": "css/presentation.css",
        }

        css_path = theme_map.get(document_type, theme_map["math-document"])
        logger.debug(f"Selected CSS theme: {css_path}")

        return css_path

    def generate_navigation(
        self,
        chapters: List[ClassifiedChapter],
        current_index: int,
    ) -> Dict[str, str]:
        """
        Generate navigation links for a chapter.

        Args:
            chapters: All chapters
            current_index: Index of current chapter

        Returns:
            Dictionary with prev/next links

        Example:
            >>> nav = renderer.generate_navigation(chapters, 2)
            >>> print(nav["prev"])  # Link to previous chapter
        """
        navigation = {}

        # Previous chapter
        if current_index > 0:
            prev_chapter = chapters[current_index - 1]
            navigation["prev"] = {
                "id": prev_chapter.chapter_id,
                "title": prev_chapter.title,
                "url": f"{prev_chapter.chapter_id}.html",
            }

        # Next chapter
        if current_index < len(chapters) - 1:
            next_chapter = chapters[current_index + 1]
            navigation["next"] = {
                "id": next_chapter.chapter_id,
                "title": next_chapter.title,
                "url": f"{next_chapter.chapter_id}.html",
            }

        # Index
        navigation["index"] = {
            "title": "Table of Contents",
            "url": "index.html",
        }

        return navigation

    def create_default_templates(self) -> None:
        """
        Create default template files if they don't exist.

        Creates basic templates for chapter.html and index.html.
        """
        # Chapter template
        chapter_template = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="{{ css_theme }}">
    {% if include_mathjax %}
    {{ mathjax_config|safe }}
    {% endif %}
</head>
<body>
    <nav class="navigation">
        <div class="nav-links">
            {% if navigation.prev %}
            <a href="{{ navigation.prev.url }}" class="nav-prev">← {{ navigation.prev.title }}</a>
            {% endif %}

            {% if navigation.index %}
            <a href="{{ navigation.index.url }}" class="nav-index">📚 {{ navigation.index.title }}</a>
            {% endif %}

            {% if navigation.next %}
            <a href="{{ navigation.next.url }}" class="nav-next">{{ navigation.next.title }} →</a>
            {% endif %}
        </div>
    </nav>

    <main class="chapter-content">
        <h1 class="chapter-title">{{ chapter.title }}</h1>

        {% if chapter.summary %}
        <div class="chapter-summary">
            <h2>Riassunto</h2>
            <p>{{ chapter.summary }}</p>
        </div>
        {% endif %}

        <div class="blocks">
        {% for block in chapter.blocks %}
            <div class="{{ block.type|block_type_class }}">
                {% if block.name %}
                <h3 class="block-name">{{ block.name }}</h3>
                {% endif %}

                {% if block.type.value == "formula" and block.latex %}
                <div class="formula">
                    $${{ block.latex }}$$
                </div>
                {% else %}
                <div class="block-content">
                    {{ block.content }}
                </div>
                {% endif %}

                {% if block.needs_review %}
                <div class="review-flag">⚠️ Richiede revisione</div>
                {% endif %}
            </div>
        {% endfor %}
        </div>
    </main>

    <footer>
        <p>Generato da PDF Math Agent</p>
    </footer>

    <button id="back-to-top" onclick="window.scrollTo({top: 0, behavior: 'smooth'})">↑</button>
</body>
</html>
"""

        # Index template
        index_template = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="{{ css_theme }}">
</head>
<body>
    <main class="index-content">
        <h1>{{ title }}</h1>

        <div class="index-stats">
            <p>Totale capitoli: {{ total_chapters }}</p>
        </div>

        <nav class="table-of-contents">
            <ul>
            {% for chapter in chapters %}
                <li>
                    <a href="{{ chapter.chapter_id }}.html">
                        {{ chapter.title }}
                    </a>
                    <span class="chapter-stats">
                        ({{ chapter.get_block_count() }} blocchi
                        {% if chapter.has_mathematical_content() %}
                        - Contenuto matematico
                        {% endif %})
                    </span>
                </li>
            {% endfor %}
            </ul>
        </nav>
    </main>

    <footer>
        <p>Generato da PDF Math Agent</p>
    </footer>
</body>
</html>
"""

        # Write templates
        chapter_path = self.template_dir / "chapter.html"
        if not chapter_path.exists():
            chapter_path.write_text(chapter_template, encoding="utf-8")
            logger.info(f"Created template: {chapter_path}")

        index_path = self.template_dir / "index.html"
        if not index_path.exists():
            index_path.write_text(index_template, encoding="utf-8")
            logger.info(f"Created template: {index_path}")


# Convenience functions
def render_chapter_html(
    chapter: ClassifiedChapter, css_theme: str = "math-document"
) -> str:
    """
    Render chapter to HTML (convenience function).

    Args:
        chapter: Chapter to render
        css_theme: CSS theme

    Returns:
        HTML string
    """
    renderer = TemplateRenderer()
    return renderer.render_chapter(chapter, css_theme=css_theme)


def inject_mathjax_into_html(html: str) -> str:
    """
    Inject MathJax into HTML (convenience function).

    Args:
        html: HTML content

    Returns:
        HTML with MathJax
    """
    renderer = TemplateRenderer()
    return renderer.inject_mathjax(html)
