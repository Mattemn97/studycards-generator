#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generatore di flashcard stampabili (fronte/retro)
Interazione guidata passo-passo + barra di progresso con tqdm.
Ora con opzione per impostare la dimensione del font principale.
"""

import csv
import os
import textwrap
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

# --- Tentativo import tqdm (fallback se mancante) ---
try:
    from tqdm import tqdm
except Exception:
    tqdm = None

# --- Costanti di configurazione per le carte (puoi modificarle) ---
CARD_WIDTH = 6 * cm
CARD_HEIGHT = 4 * cm
CARDS_PER_ROW = 3
CARDS_PER_COL = 6
MARGIN_X = 1 * cm
MARGIN_Y = 2 * cm
GAP = 0.5 * cm

# Dimensione di default (modificabile dall'utente durante il flusso guidato)
FONT_SIZE = 11
TAG_FONT_SIZE = 10


# ---------------- funzioni di disegno ----------------
def draw_text(canv, x, y, width, height, text, tag):
    """
    Disegna il testo centrato all'interno della carta e il tag in basso a destra.
    Usa le variabili globali FONT_SIZE e TAG_FONT_SIZE.
    """
    # Forza a capo sui trattini e wrap intelligente
    text = text.replace('-', '-\n')
    lines = []
    for chunk in text.split('\n'):
        # la larghezza di wrap è fissa, funziona bene nella maggior parte dei casi
        lines.extend(textwrap.wrap(chunk, width=30))

    canv.setFont("Helvetica-Bold", FONT_SIZE)
    line_height = FONT_SIZE * 1.4
    # Calcola la posizione verticale iniziale per centrare verticalmente
    start_y = y + height / 2 + (len(lines) / 2) * line_height - line_height

    for line in lines:
        canv.drawCentredString(x + width / 2, start_y, line)
        start_y -= line_height

    canv.setFont("Helvetica-Oblique", TAG_FONT_SIZE)
    canv.drawRightString(x + width - 0.3 * cm, y + 0.3 * cm, f"[{tag}]")


# ---------------- caricamento csv ----------------
def load_flashcards(csv_file_path):
    """
    Carica le flashcard da CSV con delimiter ';' (compatibile con le tue preferenze).
    Normalizza i nomi delle colonne (cerca 'lato a', 'lato b', 'tag' anche con spazi/case diversi).
    """
    with open(csv_file_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        if not reader.fieldnames:
            raise ValueError("CSV senza intestazioni o file vuoto.")

        # Normalizza i nomi dei campi per cercare le colonne richieste
        normalized = {}
        for fn in reader.fieldnames:
            key = fn.strip().lower().replace(' ', '').replace('_', '')
            normalized[key] = fn  # mapping dal normalized -> original

        # Prova mappature comuni
        map_latoa = normalized.get('latoa') or normalized.get('sidea') or normalized.get('a')
        map_latob = normalized.get('latob') or normalized.get('sideb') or normalized.get('b')
        map_tag = normalized.get('tag') or normalized.get('labels') or normalized.get('etichetta') or normalized.get('tags')

        if not map_latoa or not map_latob:
            raise ValueError("CSV manca colonne necessarie. Serve 'Lato A' e 'Lato B' (anche con nomi leggermente diversi).")

        cards = []
        for row in reader:
            la = row.get(map_latoa, '').strip()
            lb = row.get(map_latob, '').strip()
            tg = row.get(map_tag, '').strip() if map_tag else ''
            # Salta righe vuote
            if not la and not lb:
                continue
            cards.append({"Lato A": la, "Lato B": lb, "Tag": tg})
        return cards


# ---------------- creazione pagine ----------------
def create_flashcard_page(canv, cards, is_front=True, pbar=None):
    """
    Crea le pagine per fronte o retro. Se pbar è presente, viene aggiornato per ogni carta.
    Il retro è specchiato orizzontalmente per facilitare il double-sided printing.
    """
    width, height = A4
    total_per_page = CARDS_PER_ROW * CARDS_PER_COL

    for i, card in enumerate(cards):
        idx = i % total_per_page
        row = idx // CARDS_PER_ROW
        col = idx % CARDS_PER_ROW

        # posizione x: se retro -> specchia orizzontalmente
        if is_front:
            x = MARGIN_X + col * (CARD_WIDTH + GAP)
        else:
            mirror_col = CARDS_PER_ROW - 1 - col
            x = MARGIN_X + mirror_col * (CARD_WIDTH + GAP)

        y = height - MARGIN_Y - (row + 1) * CARD_HEIGHT - row * GAP

        canv.rect(x, y, CARD_WIDTH, CARD_HEIGHT)

        text = card.get("Lato A", "") if is_front else card.get("Lato B", "")
        draw_text(canv, x, y, CARD_WIDTH, CARD_HEIGHT, text, card.get("Tag", ""))

        if pbar:
            try:
                pbar.update(1)
            except Exception:
                pass

        # Avanza pagina ogni tot carte (ReportLab salverà comunque l'ultima pagina a .save())
        if (i + 1) % total_per_page == 0:
            canv.showPage()


def generate_flashcard_pdfs(cards, front_path, back_path):
    """
    Genera i PDF separati per fronte e retro, con barra di progresso se tqdm è disponibile.
    """
    fronte = canvas.Canvas(front_path, pagesize=A4)
    retro = canvas.Canvas(back_path, pagesize=A4)

    # Se tqdm disponibile, crea una barra totale (fronte + retro)
    pbar = None
    if tqdm:
        total = len(cards) * 2
        pbar = tqdm(total=total, desc="Generazione flashcards", unit="card")

    # Disegna lato fronte e retro aggiornando la stessa pbar
    create_flashcard_page(fronte, cards, is_front=True, pbar=pbar)
    create_flashcard_page(retro, cards, is_front=False, pbar=pbar)

    if pbar:
        pbar.close()

    fronte.save()
    retro.save()


# ---------------- unione PDF ----------------
def merge_pdfs(front_path, back_path, output_path, remove_intermediate=True):
    """
    Unisce i PDF fronte e retro nel file finale.
    Se PyPDF2 non è installato, stampa i percorsi dei file separati.
    """
    try:
        from PyPDF2 import PdfReader, PdfWriter
    except Exception:
        print("\n⚠️ PyPDF2 non trovato: installa con 'pip install PyPDF2' per unire automaticamente i PDF.")
        print(f"I file generati sono: {front_path} e {back_path}")
        return

    front_pdf = PdfReader(front_path)
    back_pdf = PdfReader(back_path)
    writer = PdfWriter()

    nf = len(front_pdf.pages)
    nb = len(back_pdf.pages)
    if nf != nb:
        print(f"\n⚠️ Attenzione: pagine fronte ({nf}) != retro ({nb}). Procedo comunque con l'unione.")

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
        try:
            os.remove(front_path)
            os.remove(back_path)
        except Exception:
            pass


# ---------------- flusso guidato ----------------
def guided_flow():
    global FONT_SIZE, TAG_FONT_SIZE

    os.system('cls' if os.name == 'nt' else 'clear')
    print("— Generatore flashcard (guidato) —\n")
    print("Ti guiderò passo passo. Se vuoi uscire in qualsiasi prompt, premi INVIO senza inserire nulla.\n")

    # 1) Percorso CSV
    while True:
        csv_path = input("1) Inserisci il percorso al file CSV (delimiter ';'): ").strip()
        if csv_path == "":
            print("Uscita richiesta. A presto!")
            return
        if not os.path.isfile(csv_path):
            print("❌ File non trovato. Riprova (oppure premi INVIO per uscire).")
            continue
        try:
            cards = load_flashcards(csv_path)
            if not cards:
                print("❌ Il CSV non contiene carte valide. Controlla il file.")
                continue
            break
        except Exception as e:
            print(f"❌ Errore nel leggere CSV: {e}")
            print("Controlla l'intestazione e che il separatore sia ';'. Riprova.")

    # 2) Nome file PDF finale
    out_name = input("\n2) Inserisci il nome del file PDF finale (premi INVIO per 'flashcards_finale.pdf'): ").strip()
    if out_name == "":
        out_name = "flashcards_finale.pdf"
    # assicurati estensione
    if not out_name.lower().endswith(".pdf"):
        out_name += ".pdf"

    # 3) Vuoi mantenere i file intermedi?
    keep_mid = input("\n3) Vuoi mantenere i file intermedi (fronte/reto)? [s/N]: ").strip().lower()
    keep_mid_flag = keep_mid == 's' or keep_mid == 'si'

    # 4) Dimensione del font principale
    while True:
        font_input = input("\n4) Dimensione del font principale (numero intero, default 11): ").strip()
        if font_input == "":
            # mantieni valore di default
            break
        try:
            v = int(font_input)
            if v < 6 or v > 72:
                print("Inserisci un intero tra 6 e 72. Riprova.")
                continue
            FONT_SIZE = v
            # imposta TAG_FONT_SIZE proporzionalmente, con minimo 8
            TAG_FONT_SIZE = max(8, int(round(FONT_SIZE * 0.85)))
            break
        except ValueError:
            print("Valore non valido. Inserisci un numero intero. Riprova.")

    # Feedback prima di partire
    print("\nPronto a generare le flashcard con le seguenti impostazioni:")
    print(f" - CSV: {csv_path}")
    print(f" - Carte trovate: {len(cards)}")
    print(f" - Output finale: {out_name}")
    print(f" - Mantieni intermedi: {'Sì' if keep_mid_flag else 'No'}")
    print(f" - Font principale: {FONT_SIZE} pt, Tag font: {TAG_FONT_SIZE} pt")
    if tqdm is None:
        print("\nℹ️ Nota: 'tqdm' non è installato. Vedi 'pip install tqdm' per la barra di progresso.")
    input("\nPremi INVIO per iniziare...")

    # Percorsi intermedi
    front_path = "flashcards_fronte.pdf"
    back_path = "flashcards_retro.pdf"

    # 5) Generazione (con barra se disponibile)
    print("\n⏳ Generazione in corso...")
    generate_flashcard_pdfs(cards, front_path, back_path)

    # 6) Merge automatico
    merge_pdfs(front_path, back_path, out_name, remove_intermediate=not keep_mid_flag)

    print("\nTutto fatto! Buona stampa 🎉")


# ---------------- entrypoint ----------------
if __name__ == "__main__":
    guided_flow()
