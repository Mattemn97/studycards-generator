#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generatore di flashcard stampabili (fronte/retro)
- Interazione guidata passo-passo
- Scelta del formato A (A0-A6)
- Calcolo automatico layout (righe, colonne, carte per pagina)
- Anteprima impostazioni prima della generazione
"""

import csv
import os
import textwrap
from reportlab.lib.pagesizes import A0, A1, A2, A3, A4, A5, A6
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from tqdm import tqdm

# --- Mappa dei formati disponibili ---
FORMATS = {
    "A0": A0,
    "A1": A1,
    "A2": A2,
    "A3": A3,
    "A4": A4,
    "A5": A5,
    "A6": A6,
}

# --- Configurazione di base ---
MARGIN_X = 0.0 * cm
MARGIN_Y = 0.0 * cm
GAP = 0.0 * cm
FONT_SIZE = 11
TAG_FONT_SIZE = 10


# ---------------- Disegno delle carte ----------------
def draw_text(canv, x, y, width, height, text, tag):
    """Disegna il testo centrato e il tag in basso a destra."""
    text = text.replace('-', '-\n')
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


# ---------------- Caricamento CSV ----------------
def load_flashcards(csv_file_path):
    """Carica flashcard da CSV con delimitatore ';'."""
    with open(csv_file_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        if not reader.fieldnames:
            raise ValueError("CSV senza intestazioni o file vuoto.")

        normalized = {fn.strip().lower().replace(' ', '').replace('_', ''): fn for fn in reader.fieldnames}

        map_a = normalized.get('latoa') or normalized.get('sidea') or normalized.get('a')
        map_b = normalized.get('latob') or normalized.get('sideb') or normalized.get('b')
        map_tag = normalized.get('tag') or normalized.get('labels') or normalized.get('etichetta') or normalized.get('tags')

        if not map_a or not map_b:
            raise ValueError("CSV manca colonne 'Lato A' e 'Lato B'.")

        cards = []
        for row in reader:
            la = row.get(map_a, '').strip()
            lb = row.get(map_b, '').strip()
            tg = row.get(map_tag, '').strip() if map_tag else ''
            if not la and not lb:
                continue
            cards.append({"Lato A": la, "Lato B": lb, "Tag": tg})
        return cards


# ---------------- Creazione Pagine ----------------
def create_flashcard_page(canv, cards, page_size, card_w, card_h, per_row, per_col, is_front=True, pbar=None):
    """Crea le pagine per fronte o retro (retro specchiato) con griglia centrata."""
    width, height = page_size
    total_per_page = per_row * per_col

    # --- Calcolo area occupata dalla griglia ---
    grid_w = per_row * card_w + (per_row - 1) * GAP
    grid_h = per_col * card_h + (per_col - 1) * GAP

    # --- Calcolo offset per centramento ---
    offset_x = (width - grid_w) / 2
    offset_y = (height - grid_h) / 2

    for i, card in enumerate(cards):
        idx = i % total_per_page
        row = idx // per_row
        col = idx % per_row

        # Posizionamento colonna (specchiata se retro)
        if is_front:
            x = offset_x + col * (card_w + GAP)
        else:
            mirror_col = per_row - 1 - col
            x = offset_x + mirror_col * (card_w + GAP)

        # Posizionamento riga
        y = height - offset_y - (row + 1) * card_h - row * GAP

        # Disegna il contorno e il testo
        canv.rect(x, y, card_w, card_h)
        text = card.get("Lato A", "") if is_front else card.get("Lato B", "")
        draw_text(canv, x, y, card_w, card_h, text, card.get("Tag", ""))

        if pbar:
            pbar.update(1)

        if (i + 1) % total_per_page == 0:
            canv.showPage()



# ---------------- Generazione PDF ----------------
def generate_flashcard_pdfs(cards, page_size, card_w, card_h, per_row, per_col, front_path, back_path):
    """Genera i PDF separati per fronte e retro."""
    fronte = canvas.Canvas(front_path, pagesize=page_size)
    retro = canvas.Canvas(back_path, pagesize=page_size)

    pbar = tqdm(total=len(cards) * 2, desc="Generazione PDF", unit="card")

    create_flashcard_page(fronte, cards, page_size, card_w, card_h, per_row, per_col, True, pbar)
    create_flashcard_page(retro, cards, page_size, card_w, card_h, per_row, per_col, False, pbar)

    if pbar:
        pbar.close()

    fronte.save()
    retro.save()


# ---------------- Unione Fronte + Retro ----------------
def merge_pdfs(front_path, back_path, output_path, remove_intermediate=True):
    """Unisce fronte e retro in un unico PDF."""
    try:
        from PyPDF2 import PdfReader, PdfWriter
    except Exception:
        print("\n⚠ PyPDF2 non trovato. Installa con 'pip install PyPDF2'.")
        print(f"I file generati sono: {front_path} e {back_path}")
        return

    front_pdf = PdfReader(front_path)
    back_pdf = PdfReader(back_path)
    writer = PdfWriter()

    nf, nb = len(front_pdf.pages), len(back_pdf.pages)
    n = max(nf, nb)
    for i in range(n):
        if i < nf:
            writer.add_page(front_pdf.pages[i])
        if i < nb:
            writer.add_page(back_pdf.pages[i])

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"\n✅ PDF finale generato: {output_path}")
    if remove_intermediate:
        for p in (front_path, back_path):
            try:
                os.remove(p)
            except Exception:
                pass


# ---------------- Flusso guidato ----------------
def guided_flow():
    global FONT_SIZE, TAG_FONT_SIZE

    os.system('cls' if os.name == 'nt' else 'clear')
    print("— Generatore Flashcard (completo) —\n")

    # Percorso CSV
    while True:
        csv_path = input("1) Inserisci il percorso del file CSV: ").strip()
        if not os.path.isfile(csv_path):
            print("❌ File non trovato. Riprova.")
            continue
        cards = load_flashcards(csv_path)
        if not cards:
            print("❌ Nessuna carta trovata.")
            continue
        break

    # Scelta formato carta
    print("\n2) Scegli il formato della pagina (A0-A6):")
    for fmt in FORMATS:
        print(f"   - {fmt}")
    while True:
        fmt_choice = input("Formato [default A4]: ").strip().upper() or "A4"
        if fmt_choice in FORMATS:
            page_size = FORMATS[fmt_choice]
            break
        print("❌ Formato non valido. Riprova.")
    width, height = page_size

    # Dimensioni carte
    print("\n3) Imposta dimensioni carta (cm, default 6x4):")
    try:
        card_w = (float(input("   Larghezza: ") or 6)) * cm
        card_h = (float(input("   Altezza: ") or 4)) * cm
    except ValueError:
        card_w, card_h = 6 * cm, 4 * cm
        print("⚠ Valori non validi, uso default.")

    # Font
    try:
        FONT_SIZE = int(input("\n4) Font principale: ") or 11)
        TAG_FONT_SIZE = max(8, int(FONT_SIZE * 0.85))
    except ValueError:
        FONT_SIZE = 11
        TAG_FONT_SIZE = 10
    
    # Margini e gap
    try:
        MARGIN_X = int(input("\n4) Margine orizzontale dal bordo: ") or 0.5) * cm
        MARGIN_Y = int(input("\n4) Margine vercicale dal bordo: ") or 0.5) * cm
        GAP = int(input("\n4) Margine tra le carte: ") or 0.5) * cm
    except ValueError:
        MARGIN_X = 0.5 * cm
        MARGIN_Y = 0.5 * cm
        GAP = 0.5 * cm

    # Calcolo layout automatico
    usable_w = width - 2 * MARGIN_X + GAP
    usable_h = height - 2 * MARGIN_Y + GAP
    per_row = max(1, int(usable_w // (card_w + GAP)))
    per_col = max(1, int(usable_h // (card_h + GAP)))
    per_page = per_row * per_col

    # Anteprima impostazioni
    print("\n📋 Anteprima impostazioni:")
    print(f"   • Formato pagina: {fmt_choice} ({width/cm:.1f}x{height/cm:.1f} cm)")
    print(f"   • Dimensione carta: {card_w/cm:.1f}x{card_h/cm:.1f} cm")
    print(f"   • Margini: {MARGIN_X/cm:.1f}x{MARGIN_Y/cm:.1f} cm, gap {GAP/cm:.1f} cm")
    print(f"   • Layout: {per_row} colonne x {per_col} righe = {per_page} carte per pagina")
    print(f"   • Font principale: {FONT_SIZE} pt, tag: {TAG_FONT_SIZE} pt")
    print(f"   • Numero carte totali: {len(cards)} → {len(cards)//per_page + 1} pagine circa\n")

    if input("Procedere con la generazione? [S/n]: ").strip().lower() in ("n", "no"):
        print("❌ Operazione annullata.")
        return

    # Generazione effettiva
    out_name = input("\nNome PDF finale [flashcards.pdf]: ").strip() or "flashcards.pdf"
    front_path = "flashcards_fronte.pdf"
    back_path = "flashcards_retro.pdf"

    print("\n⏳ Generazione in corso...")
    generate_flashcard_pdfs(cards, page_size, card_w, card_h, per_row, per_col, front_path, back_path)
    merge_pdfs(front_path, back_path, out_name)
    print("\n✅ Tutto fatto! Buona stampa 🎉")


# ---------------- Entrypoint ----------------
if __name__ == "__main__":
    guided_flow()
