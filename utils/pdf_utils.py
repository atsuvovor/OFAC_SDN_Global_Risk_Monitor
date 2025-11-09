import os
import re
import tempfile
import plotly.io as pio
from fpdf import FPDF
from html import unescape
# ------------------------------------------------------------
# Utility: clean non-ASCII text (prevents FPDF encoding errors)
# ------------------------------------------------------------
def remove_non_ascii(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return re.sub(r"[^\x00-\x7F]+", " ", text)


# ------------------------------------------------------------
# Utility: save Plotly figure to temporary PNG image
# ------------------------------------------------------------
def save_fig_to_temp(fig):
    temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    pio.write_image(fig, temp_path)
    return temp_path

def html_to_text(html: str) -> str:
    """
    Convert HTML string to plain text for PDF output.
    - Strips all HTML tags
    - Unescapes HTML entities
    """
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", "", html)  # naive tag stripping
    text = unescape(text)                # decode & unescape entities
    return text
    
# ------------------------------------------------------------
# Main: create combined PDF with text + figures
# ------------------------------------------------------------
def create_combined_pdf(sections, pdf_path: str):
    """
    Create a PDF that includes both text and Plotly figures.

    Args:
        sections (list): list of dicts like:
            [
                {"title": "Overview", "content": "Summary text here"},
                {"title": "SDN Risk Heatmap", "figure": fig1},
                {"title": "Country Breakdown", "figure": fig2},
            ]
        pdf_path (str): destination file path for PDF
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    for section in sections:
        title = section.get("title", "")
        content = section.get("content")
        fig = section.get("figure")

        # Section title
        if title:
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, title, ln=True)
            pdf.ln(3)
            pdf.set_font("Helvetica", size=12)

        # Add text content
        if content:
            clean_text = remove_non_ascii(content)
            pdf.multi_cell(0, 8, clean_text)
            pdf.ln(5)

        # Add figure as image
        if fig is not None:
            try:
                fig_path = save_fig_to_temp(fig)
                pdf.image(fig_path, w=180)
                os.remove(fig_path)
                pdf.ln(10)
            except Exception as e:
                pdf.multi_cell(0, 8, f"[⚠️ Could not render figure: {e}]")
                pdf.ln(5)

    pdf.output(pdf_path)
    return pdf_path
