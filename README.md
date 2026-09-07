# NLP Speech Chatbot

Speech chatbot dedicato alle opere di **Caravaggio** e
**Battistello Caracciolo** visitabili nell'area urbana di Napoli.

Il sistema accetta domande testuali o vocali, combina una pipeline
NLP deterministica con un LLM locale e interroga una knowledge base
Neo4j popolata a partire da dati DBpedia.

Durante il normale utilizzo, **Neo4j è l'unica fonte di verità
fattuale**: l'LLM interpreta la richiesta e sceglie i tool da
utilizzare, ma non genera autonomamente fatti artistici.

## Funzionalità principali

- input testuale e vocale;
- interfaccia grafica Tkinter;
- modalità terminale;
- Speech-to-Text con Whisper locale o Google Speech Recognition;
- Text-to-Speech;
- preprocessing e normalizzazione condivisa;
- classificazione degli intenti;
- riconoscimento e linking delle entità;
- fuzzy matching per titoli incompleti o con errori;
- gestione di alias, incluso Michelangelo Merisi / Caravaggio;
- memoria conversazionale persistente;
- follow-up contestuali;
- riferimenti ordinali a risultati precedenti;
- rilevamento deterministico delle incongruenze su autore, luogo e data;
- comprensione semantica tramite Qwen 3 8B eseguito localmente con Ollama;
- tool calling controllato;
- risposte grounded basate sui risultati Neo4j;
- fallback automatico alla pipeline deterministica quando l'LLM non è disponibile.

## Dominio

Il chatbot è progettato per rispondere esclusivamente su:

- Caravaggio;
- Battistello Caracciolo;
- le loro opere presenti nella knowledge base;
- i musei e i luoghi di Napoli associati a tali opere.

Le domande chiaramente esterne al dominio vengono rifiutate senza
utilizzare conoscenza esterna.

## Requisiti

Ambiente di sviluppo verificato:

- Windows 11;
- Python 3.12.5;
- Neo4j 5;
- Ollama;
- modello `qwen3:8b`;
- microfono per le funzionalità vocali.

## Installazione Python

Creare e attivare l'ambiente virtuale:

    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1

Installare le dipendenze:

    pip install -r requirements.txt

Dipendenze principali:

- `neo4j`;
- `python-dotenv`;
- `SpeechRecognition`;
- `PyAudio`;
- `pyttsx3`;
- `faster-whisper`;
- `ollama`.

## Configurazione

Copiare il file di esempio:

    Copy-Item .env.example .env

Configurare Neo4j:

    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=replace_with_local_password
    NEO4J_DATABASE=neo4j

Configurare Speech-to-Text e LLM:

    STT_ENGINE=whisper
    LLM_ENABLED=true
    OLLAMA_MODEL=qwen3:8b

Il file `.env` locale non deve essere versionato.

## Configurazione Ollama

Scaricare il modello:

    ollama pull qwen3:8b

Verificare i modelli caricati:

    ollama ps

Scaricare dalla memoria il modello manualmente:

    ollama stop qwen3:8b

Il client Ollama usa:

- `think=False`, per evitare il reasoning esteso non necessario;
- `keep_alive="30m"`, per mantenere il modello caricato dopo una richiesta;
- massimo 4 tool call per singola risposta dell'agent.

Il modello configurato di default è `qwen3:8b`.

## Abilitazione o disabilitazione dell'LLM

Modalità Hybrid:

    LLM_ENABLED=true

Modalità completamente deterministica:

    LLM_ENABLED=false

Quando l'LLM è abilitato, la factory crea `HybridChatbotService`.
Quando è disabilitato, viene utilizzato direttamente `ChatbotService`.

Se l'agent LLM genera un errore durante una richiesta, il servizio
Hybrid utilizza automaticamente il servizio deterministico come fallback.

## Speech-to-Text

Whisper locale:

    STT_ENGINE=whisper

Google Speech Recognition:

    STT_ENGINE=google

Whisper è la modalità locale prevista per l'utilizzo principale.

## Avvio della GUI

Con Neo4j attivo e, in modalità Hybrid, Ollama disponibile:

    python .\gui_main.py

La GUI consente:

- inserimento testuale;
- input vocale;
- selezione del motore STT;
- visualizzazione della conversazione;
- riproduzione TTS della risposta.

## Avvio da terminale

    python .\main.py

La modalità terminale mantiene una singola sessione conversazionale
per tutta la durata del processo.

## Architettura Hybrid

Il sistema separa la comprensione linguistica dalla verifica fattuale.

Flusso semplificato:

    testo o voce
        |
        v
    preprocessing e NLU deterministico
        |
        +--> intent preliminare
        +--> entity linking
        +--> fuzzy matching
        +--> claim extraction
        +--> context resolution
        |
        v
    verifica deterministica delle incongruenze
        |
        v
    Qwen 3 8B
    interpretazione semantica e scelta dei tool
        |
        v
    tool autorizzati
        |
        v
    KnowledgeRepository
        |
        v
    Neo4j
        |
        v
    GroundedAnswerRenderer
        |
        v
    BotResponse
        |
        +--> memoria conversazionale
        +--> testo
        +--> TTS

L'intent deterministico viene passato al modello come **indicazione
semantica**, non come vincolo assoluto. In questo modo il modello può
gestire anche richieste composte senza sostituire la pipeline NLP.

## Tool LLM autorizzati

L'agent può utilizzare esclusivamente i seguenti tool:

- `get_artwork_information`;
- `list_artworks_by_artist`;
- `list_artworks_by_place`;
- `list_places`;
- `list_places_with_artworks`;
- `get_artist_information`;
- `get_place_information`;
- `search_artworks`.

Il modello non può:

- eseguire query Cypher arbitrarie;
- interrogare DBpedia direttamente;
- modificare Neo4j;
- utilizzare tool non presenti nella whitelist.

### Tool composito luoghi-opere

`list_places_with_artworks` gestisce richieste come:

> Quali musei posso visitare e quali opere si trovano in ciascuno?

Il tool riusa le operazioni del repository già disponibili:

    list_places()
        |
        v
    list_artworks_by_place(place)

Il risultato viene poi raggruppato dal renderer per luogo.

## Grounding

Neo4j rimane l'unica fonte di verità durante la conversazione.

L'LLM:

1. interpreta la richiesta;
2. sceglie uno o più tool;
3. fornisce gli argomenti strutturati.

Il contenuto fattuale finale viene invece prodotto dal
`GroundedAnswerRenderer` sulla base dei risultati restituiti dal database.

Questo riduce il rischio di hallucination e mantiene separati:

- interpretazione semantica;
- accesso ai dati;
- generazione della risposta fattuale.

## Memoria conversazionale

Ogni sessione mantiene uno stato tramite `MemoryRepository`.

Il sistema conserva, tra le altre informazioni:

- ultimo intent;
- artista corrente;
- opera corrente;
- luogo corrente;
- risultati dell'ultima lista;
- opzioni di chiarimento.

Questo permette conversazioni come:

    Quali opere di Caravaggio posso vedere a Napoli?
    Dove si trova il secondo elencato?
    A quando risale il dipinto?
    Mentre il terzo elencato dove si trova?

I riferimenti ordinali utilizzano l'ordine effettivo della lista precedente.

## Inconsistency detection

Il sistema verifica deterministicamente claim relativi a:

- autore dell'opera;
- luogo dell'opera;
- data dell'opera.

Esempi:

    Il Martirio di sant'Orsola è di Battistello Caracciolo?

    Le Sette opere di Misericordia si trovano
    al Museo di Capodimonte?

    Il Martirio di sant'Orsola è stato realizzato nel 1607?

Quando viene rilevata un'incongruenza, la correzione viene ricavata
direttamente dal repository e ha priorità sulla risposta dell'LLM.

## Fuzzy matching

Il sistema supporta titoli incompleti o con piccoli errori, ad esempio:

    Dove si trova il Martirio di sant Orsloa?

    Descrivimi la Flagellazione.

Le soglie condivise sono:

- `>= 0.90`: corrispondenza accettata;
- `0.75 - 0.90`: corrispondenza ambigua;
- `< 0.75`: nessuna corrispondenza affidabile.

## Test automatici

Eseguire l'intera suite:

    python -m pytest -q

Stato finale verificato:

    296 test superati
    25 subtest superati
    0 fallimenti

La suite finale produce inoltre alcune warning di deprecazione note,
principalmente relative a `SpeechRecognition` e `datetime.utcnow()`.
Tali warning non causano fallimenti dei test.

## Test funzionale finale

È stato inoltre eseguito un test manuale end-to-end nella stessa
sessione GUI, comprendente:

- informazioni su artista;
- informazioni e descrizione di opere;
- autore, luogo e data;
- richieste composte;
- memoria conversazionale;
- riferimenti ordinali;
- elenchi per artista;
- elenchi per luogo;
- elenco dei luoghi;
- luoghi con opere associate;
- informazioni sui musei;
- alias di artista;
- fuzzy matching;
- titoli incompleti;
- incongruenze;
- confronto tra artisti;
- formulazioni naturali;
- domande fuori dominio.

Esito finale del maxi-test:

    26 / 26 tipologie superate

I dettagli sono documentati in:

    docs/testing/final-functional-test-matrix.md

## Struttura principale

    src/
    |-- core/
    |-- database/
    |-- dialogue/
    |-- gui/
    |-- knowledge/
    |-- llm/
    |-- nlp/
    `-- speech/

    docs/
    |-- specifications/
    |-- step-reports/
    `-- testing/

    main.py
    gui_main.py
    tests/

## Contratti condivisi

La specifica condivisa originale è:

    docs/specifications/shared-spec-v1.0.md

Le estensioni condivise approvate successivamente vengono documentate
in una versione successiva della specifica, mantenendo invariata la
v1.0 originale.

## Principi progettuali

Il progetto segue alcuni principi fondamentali:

1. Neo4j è la fonte di verità fattuale durante il runtime.
2. L'LLM interpreta il linguaggio naturale, non sostituisce il database.
3. Gli accessi alla conoscenza avvengono attraverso repository e tool controllati.
4. Le inconsistenze verificabili vengono gestite deterministicamente.
5. La memoria conversazionale è separata dalla knowledge base.
6. Le dipendenze vengono fornite tramite dependency injection.
7. Il sistema mantiene un fallback deterministico quando l'LLM non è disponibile.
