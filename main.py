import csv
import os
import textwrap

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

# --- Costanti di configurazione per le carte ---
CARD_WIDTH = 6 * cm
CARD_HEIGHT = 4 * cm
CARDS_PER_ROW = 3
CARDS_PER_COL = 6
MARGIN_X = 1 * cm
MARGIN_Y = 2 * cm
GAP = 0.5 * cm
FONT_SIZE = 14
TAG_FONT_SIZE = 10


def draw_text(canv, x, y, width, height, text, tag):
    """
    Disegna il testo centrato all'interno della carta e il tag in basso a destra.

    :param canv: Oggetto canvas di ReportLab
    :param x: Posizione X della carta
    :param y: Posizione Y della carta
    :param width: Larghezza della carta
    :param height: Altezza della carta
    :param text: Testo da scrivere (lato A o lato B)
    :param tag: Tag associato alla carta
    """
    text = text.replace('-', '-\n')  # Va a capo sui trattini
    lines = []
    for chunk in text.split('\n'):
        lines.extend(textwrap.wrap(chunk, width=30))

    canv.setFont("Helvetica-Bold", FONT_SIZE)
    line_height = FONT_SIZE * 1.4
    start_y = y + height / 2 + (len(lines) / 2) * line_height - line_height

    for line in lines:
        canv.drawCentredString(x + width / 2, start_y, line)
        start_y -= line_height

    canv.setFont("Helvetica-Oblique", TAG_FONT_SIZE)
    canv.drawRightString(x + width - 0.3 * cm, y + 0.3 * cm, f"[{tag}]")


def load_flashcards(csv_file_path):
    """
    Carica le flashcard da un file CSV.

    :param csv_file_path: Percorso al file CSV contenente 'Lato A', 'Lato B' e 'Tag'
    :return: Lista di dizionari con i contenuti delle flashcard
    """
    with open(csv_file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        return list(reader)


def create_flashcard_page(canv, cards, is_front=True):
    """
    Crea una pagina di flashcard (fronte o retro).

    :param canv: Oggetto canvas su cui disegnare
    :param cards: Lista delle flashcard da disegnare
    :param is_front: True per il lato A, False per il lato B
    """
    width, height = A4
    total_per_page = CARDS_PER_ROW * CARDS_PER_COL

    for i, card in enumerate(cards):
        idx = i % total_per_page
        row = idx // CARDS_PER_ROW
        col = idx % CARDS_PER_ROW

        x = MARGIN_X + col * (CARD_WIDTH + GAP)
        y = height - MARGIN_Y - (row + 1) * CARD_HEIGHT - row * GAP

        # Lato retro specchiato orizzontalmente
        if not is_front:
            col = CARDS_PER_ROW - 1 - col
            x = MARGIN_X + col * (CARD_WIDTH + GAP)

        canv.rect(x, y, CARD_WIDTH, CARD_HEIGHT)

        text = card["Lato A"] if is_front else card["Lato B"]
        draw_text(canv, x, y, CARD_WIDTH, CARD_HEIGHT, text, card["Tag"])

        # Passa alla pagina successiva ogni tot carte
        if (i + 1) % total_per_page == 0:
            canv.showPage()


def generate_flashcard_pdfs(cards, front_path, back_path):
    """
    Genera i PDF separati per fronte e retro.

    :param cards: Lista di flashcard
    :param front_path: Nome del file PDF per il fronte
    :param back_path: Nome del file PDF per il retro
    """
    fronte = canvas.Canvas(front_path, pagesize=A4)
    retro = canvas.Canvas(back_path, pagesize=A4)

    create_flashcard_page(fronte, cards, is_front=True)
    create_flashcard_page(retro, cards, is_front=False)

    fronte.save()
    retro.save()


def merge_pdfs(front_path, back_path, output_path):
    """
    Unisce i PDF fronte e retro in un unico file finale.

    :param front_path: Percorso al PDF fronte
    :param back_path: Percorso al PDF retro
    :param output_path: Nome del file PDF finale
    """
    try:
        from PyPDF2 import PdfReader, PdfWriter

        front_pdf = PdfReader(front_path)
        back_pdf = PdfReader(back_path)
        writer = PdfWriter()

        for f_page, b_page in zip(front_pdf.pages, back_pdf.pages):
            writer.add_page(f_page)
            writer.add_page(b_page)

        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"✅ PDF finale generato: {output_path}")
        os.remove(front_path)
        os.remove(back_path)

    except ImportError:
        print("⚠️ Installare PyPDF2 per unificare i PDF: pip install PyPDF2")
        print(f"I file separati sono: {front_path} e {back_path}")


def generate_flashcards(csv_file, output_pdf="flashcards_finale.pdf"):
    """
    Funzione principale per generare le flashcard da un file CSV.

    :param csv_file: Percorso al file CSV
    :param output_pdf: Nome del file PDF finale unificato
    """
    cards = load_flashcards(csv_file)
    front_path = "flashcards_fronte.pdf"
    back_path = "flashcards_retro.pdf"

    generate_flashcard_pdfs(cards, front_path, back_path)
    merge_pdfs(front_path, back_path, output_pdf)


if __name__ == "__main__":
    generate_flashcards("flashcards.csv")
