# NLP Speech Chatbot

Speech chatbot dedicato alle opere di Caravaggio e Battistello
Caracciolo visitabili nell'area urbana di Napoli.

Il sistema accetta domande testuali o vocali, interroga una
knowledge base Neo4j popolata a partire da DBpedia e restituisce
una risposta testuale accompagnata da sintesi vocale.

## Funzionalità

- input testuale e vocale;
- Speech-to-Text con Whisper o Google;
- Text-to-Speech;
- riconoscimento di intenti ed entità;
- fuzzy matching;
- memoria conversazionale persistente;
- rilevamento delle incongruenze;
- comprensione linguistica tramite LLM locale;
- risposte basate esclusivamente sui dati Neo4j;
- interfaccia grafica Tkinter;
- modalità terminale.

## Requisiti

- Windows 11;
- Python 3.12.5;
- Neo4j 5;
- Ollama;
- microfono per l'input vocale.

## Installazione Python

Creare e attivare l'ambiente virtuale:

    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1

Installare le dipendenze:

    pip install -r requirements.txt

## Configurazione

Copiare il file di esempio:

    Copy-Item .env.example .env

Inserire nel file `.env` i dati di Neo4j:

    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=replace_with_local_password
    NEO4J_DATABASE=neo4j

## Configurazione Ollama

Scaricare il modello:

    ollama pull qwen3:8b

Configurare nel file `.env`:

    LLM_ENABLED=true
    OLLAMA_MODEL=qwen3:8b

Per disattivare l'LLM:

    LLM_ENABLED=false

## Speech-to-Text

Whisper locale:

    STT_ENGINE=whisper

Google Speech Recognition:

    STT_ENGINE=google

## Avvio GUI

Con Neo4j e Ollama attivi:

    python .\gui_main.py

## Avvio da terminale

    python .\main.py

## Architettura LLM

L'LLM interpreta la domanda e seleziona esclusivamente tool
controllati. Non può generare query Cypher arbitrarie.

Flusso:

    testo o voce
        ↓
    comprensione linguistica
        ↓
    tool autorizzati
        ↓
    KnowledgeRepository
        ↓
    Neo4j
        ↓
    risposta grounded
        ↓
    testo e TTS

Neo4j rimane l'unica fonte di verità. La risposta finale viene
costruita esclusivamente dai risultati restituiti dal database.

Se Ollama non è disponibile, il sistema usa automaticamente la
pipeline deterministica.

## Test

Eseguire l'intera suite:

    python -m pytest -q

Stato verificato:

    278 test superati
    21 subtest superati
    0 fallimenti

## Struttura principale

    src/
    ├── database/
    ├── dialogue/
    ├── gui/
    ├── llm/
    ├── nlp/
    └── speech/

    main.py
    gui_main.py
    tests/
