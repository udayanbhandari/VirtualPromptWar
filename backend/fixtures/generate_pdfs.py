"""
Generate realistic PDF files from the text fixtures for Phase 1 testing.
"""

from pathlib import Path
from fpdf import FPDF

FIXTURES_DIR = Path(__file__).parent


class ContractPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def create_pdf(txt_path: Path, pdf_path: Path):
    text = txt_path.read_text(encoding="utf-8")
    lines = text.strip().split("\n")

    pdf = ContractPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    # First line as title
    title = lines[0].strip()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(w=pdf.epw, h=8, text=title, align="C")
    pdf.ln(4)

    # Divider line
    pdf.set_draw_color(203, 213, 225)
    pdf.set_line_width(0.5)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(4)

    # Body lines
    for line in lines[1:]:
        line_str = line.strip()
        if not line_str:
            pdf.ln(2)
            continue

        clean_str = (
            line_str.replace("“", '"')
            .replace("”", '"')
            .replace("’", "'")
            .replace("—", "-")
        )

        # Section headers
        if clean_str[0].isdigit() and ("." in clean_str[:4]) and (clean_str.isupper() or len(clean_str) < 40):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(30, 41, 59)
            pdf.ln(2)
            pdf.multi_cell(w=pdf.epw, h=6, text=clean_str)
            pdf.ln(1)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(w=pdf.epw, h=5.5, text=clean_str)

    pdf.output(str(pdf_path))
    print(f"Generated: {pdf_path.name} ({pdf_path.stat().st_size} bytes)")


def main():
    for txt_file in FIXTURES_DIR.glob("*.txt"):
        pdf_file = FIXTURES_DIR / f"{txt_file.stem}.pdf"
        create_pdf(txt_file, pdf_file)


if __name__ == "__main__":
    main()
