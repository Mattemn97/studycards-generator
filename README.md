# 🃏 Generatore di Flashcard PDF
Questo progetto genera automaticamente flashcard stampabili in formato PDF a partire da un file CSV. Le carte vengono organizzate in modo ottimale per la stampa fronte-retro, con testi personalizzabili su **Lato A** e **Lato B**, e un campo **Tag** per classificazione o categorie.

## 📂 Struttura del progetto
flashcard_generator/
- flashcards.csv # File di input (modificabile)
- main.py # Script principale
- README.md # Questo file

## 🛠 Requisiti
- Python ≥ 3.7
- [reportlab](https://pypi.org/project/reportlab/)
- [PyPDF2](https://pypi.org/project/PyPDF2/) *(opzionale, ma consigliato per unire i PDF fronte e retro)*

Installa le dipendenze con:
```bash
pip install reportlab PyPDF2
```

📄 Formato del file CSV
Il file flashcards.csv deve contenere tre colonne separate da ;:
```csv
Lato A;Lato B;Tag
Che cos'è un algoritmo?;Una sequenza finita di istruzioni...;Informatica
Capitale della Francia?;Parigi;Geografia
```

▶️ Utilizzo
Esegui lo script principale:

```bash
python main.py
```

Alla fine, otterrai:
- flashcards_finale.pdf: PDF pronto da stampare fronte-retro
- (temporanei) flashcards_fronte.pdf e flashcards_retro.pdf se PyPDF2 non è installato

🎯 Caratteristiche
- Supporta la stampa fronte-retro con allineamento speculare
- Adatta il testo al layout con word wrapping intelligente
- Gestisce automaticamente il numero di carte per pagina
- Ogni carta mostra un tag in basso a destra

📌 Suggerimenti
- Usa trattini - per forzare l'andata a capo nel testo
- I tag possono essere usati per filtrare o ordinare il contenuto
- Puoi usare questo tool per vocabolari, quiz, definizioni, date storiche, ecc.

💡 Personalizzazioni possibili
- Cambia dimensioni carta/modello nel file main.py
- Aggiungi colori, loghi o font personalizzati
- Integra un’interfaccia CLI o GUI

📬 Contatti
Per suggerimenti o miglioramenti, apri una Issue o contattami tramite GitHub!
