"""
Composer Agent - Task 3: Generate HTML output.

Uses Template Tools to render navigable HTML with styling.
"""

from pathlib import Path
from typing import Optional

from src.agents.base_agent import BaseAgent
from src.models.enums import AgentTask
from src.models.state import AgentState
from src.tools.template_tools import TemplateRenderer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ComposerAgent(BaseAgent):
    """
    Composer Agent - generates HTML output from classified chapters.

    Uses Template Tools to:
    - Render chapter HTML with MathJax
    - Generate navigation links
    - Create index page
    - Apply CSS themes
    - Generate navigable HTML site
    """

    def __init__(
        self,
        llm_provider: str = "groq",
        model: Optional[str] = None,
        css_theme: str = "math-document",
    ):
        """
        Initialize Composer Agent.

        Args:
            llm_provider: LLM provider (groq, anthropic, openai)
            model: Model name (if None, uses config default)
            css_theme: CSS theme to use (math-document, lecture-notes, presentation)
        """
        super().__init__(
            task=AgentTask.TASK_3_COMPOSER,
            llm_provider=llm_provider,
            model=model,
        )

        self.css_theme = css_theme

        # Initialize template renderer
        self.renderer = TemplateRenderer()

        # Create default templates if they don't exist
        self.renderer.create_default_templates()

    def execute(self, state: AgentState) -> AgentState:
        """
        Execute HTML generation.

        Args:
            state: Current workflow state (must have classified_document)

        Returns:
            Updated state with html_files and output_dir populated
        """
        if not state.classified_document:
            raise ValueError("Classified document is required for composition")

        logger.info(
            f"Generating HTML for {len(state.classified_document.chapters)} chapters"
        )

        # Determine output directory
        output_dir = self._get_output_dir(state)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copy CSS files
        self._copy_css_files(output_dir)

        # Generate chapter HTML files
        html_files = {}
        chapters = state.classified_document.chapters

        for i, chapter in enumerate(chapters):
            logger.info(f"Rendering chapter: {chapter.title}")

            # Generate navigation
            navigation = self.renderer.generate_navigation(chapters, current_index=i)

            # Render chapter HTML
            html = self.renderer.render_chapter(
                chapter=chapter,
                css_theme=f"css/{self.css_theme}.css",
                include_mathjax=True,
                navigation=navigation,
            )

            # Write to file
            chapter_file = output_dir / f"{chapter.chapter_id}.html"
            chapter_file.write_text(html, encoding="utf-8")

            html_files[chapter.chapter_id] = str(chapter_file)

            logger.info(f"  Written to: {chapter_file}")

        # Generate index page
        index_html = self.renderer.render_index(
            chapters=chapters,
            title=self._get_document_title(state),
            css_theme=f"css/{self.css_theme}.css",
        )

        index_file = output_dir / "index.html"
        index_file.write_text(index_html, encoding="utf-8")

        logger.info(f"Index page written to: {index_file}")

        # Update state
        state.html_files = html_files
        state.output_dir = str(output_dir)

        logger.info(f"HTML generation complete: {len(html_files)} chapters + index")

        return state

    def _get_output_dir(self, state: AgentState) -> Path:
        """
        Get output directory path.

        Args:
            state: Workflow state

        Returns:
            Path to output directory
        """
        # Use config output dir if specified
        config = self.config
        base_dir = Path(config.output.get("base_dir", "outputs"))

        # Create subdirectory based on PDF name
        pdf_name = Path(state.pdf_path).stem
        output_dir = base_dir / pdf_name

        return output_dir

    def _get_document_title(self, state: AgentState) -> str:
        """
        Get document title.

        Args:
            state: Workflow state

        Returns:
            Document title
        """
        # Use PDF filename as default title
        pdf_name = Path(state.pdf_path).stem

        # Capitalize and clean up
        title = pdf_name.replace("_", " ").replace("-", " ").title()

        return title

    def _copy_css_files(self, output_dir: Path) -> None:
        """
        Copy CSS files to output directory.

        Args:
            output_dir: Output directory
        """
        import shutil

        # CSS source directory
        css_src = Path("src/templates/css")

        if not css_src.exists():
            logger.warning(f"CSS source directory not found: {css_src}")
            return

        # CSS destination directory
        css_dest = output_dir / "css"
        css_dest.mkdir(parents=True, exist_ok=True)

        # Copy CSS files
        for css_file in css_src.glob("*.css"):
            dest_file = css_dest / css_file.name
            shutil.copy2(css_file, dest_file)
            logger.debug(f"Copied CSS: {css_file.name}")

        logger.info(f"CSS files copied to: {css_dest}")
