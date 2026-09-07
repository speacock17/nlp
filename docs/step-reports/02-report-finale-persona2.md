# Report finale — Persona 2

## Obiettivo

Realizzare e integrare i componenti di Natural Language Processing,
dialogue management, memoria conversazionale, generazione della
risposta, Speech-to-Text, Text-to-Speech, interfaccia grafica e
integrazione con un Large Language Model locale per uno speech
chatbot dedicato alle opere di Caravaggio e Battistello Caracciolo
visitabili nell'area urbana di Napoli.

Il sistema finale combina una pipeline NLP deterministica con un
LLM locale, mantenendo Neo4j come unica fonte di verità fattuale
durante il runtime.

## Attività svolte

Sono state implementate e integrate le seguenti funzionalità:

- preprocessing e normalizzazione del testo;
- classificazione degli intenti;
- riconoscimento delle entità;
- entity linking;
- fuzzy matching;
- riconoscimento di alias;
- riconoscimento di riferimenti ordinali;
- estrazione dei claim;
- rilevamento delle incongruenze;
- gestione del contesto conversazionale;
- memoria persistente;
- risoluzione dei follow-up;
- generazione deterministica delle risposte;
- Speech-to-Text;
- Text-to-Speech;
- interfaccia grafica Tkinter;
- modalità terminale;
- integrazione con Qwen 3 8B tramite Ollama;
- tool calling controllato;
- risposta grounded basata su Neo4j;
- fallback automatico alla pipeline deterministica;
- ottimizzazione dei tempi di risposta dell'LLM;
- supporto alle richieste composte;
- supporto all'elenco dei luoghi;
- supporto all'elenco dei luoghi con le rispettive opere;
- documentazione finale e test funzionali end-to-end.

## Architettura finale

L'architettura finale è Hybrid.

Il flusso principale è:

    input testuale o vocale
        |
        v
    preprocessing
        |
        v
    NLU deterministico
        |
        +--> intent preliminare
        +--> entity recognition
        +--> entity linking
        +--> fuzzy matching
        +--> claim extraction
        +--> context resolution
        |
        v
    inconsistency detection
        |
        v
    HybridChatbotService
        |
        +--> ToolCallingAgent
        |       |
        |       v
        |   Qwen 3 8B
        |       |
        |       v
        |   tool autorizzati
        |       |
        |       v
        |   KnowledgeRepository
        |       |
        |       v
        |     Neo4j
        |
        +--> fallback deterministico
        |
        v
    BotResponse
        |
        +--> memoria conversazionale
        +--> output testuale
        +--> TTS

La pipeline deterministica non è stata sostituita dall'LLM.

L'LLM viene utilizzato principalmente per interpretare la semantica
della richiesta e scegliere i tool appropriati.

Le informazioni fattuali vengono invece recuperate dal database.

## NLP deterministico

La pipeline NLP gestisce:

- intenti;
- entità;
- claim;
- fuzzy matching;
- contesto;
- riferimenti ordinali;
- inconsistenze.

Tra gli intenti supportati sono presenti:

- `LIST_ARTWORKS_BY_ARTIST`;
- `ARTWORK_LOCATION`;
- `ARTWORK_AUTHOR`;
- `ARTWORK_DATE`;
- `ARTWORK_DESCRIPTION`;
- `ARTIST_INFO`;
- `LIST_PLACES`;
- `PLACE_ARTWORKS`;
- `COMPARE_ARTISTS`;
- `FOLLOW_UP`;
- `OUT_OF_SCOPE`;
- `UNKNOWN`.

Il tipo di entità `ORDINAL` permette di interpretare espressioni
come:

    il primo
    il secondo
    il terzo

rispetto ai risultati memorizzati nella conversazione.

## Fuzzy matching

Il sistema permette di riconoscere titoli:

- incompleti;
- scritti con piccoli errori;
- espressi con varianti compatibili.

Esempi verificati:

    Martirio di sant Orsloa

    Flagellazione

Le soglie condivise sono:

- punteggio >= 0.90: match accettato;
- punteggio tra 0.75 e 0.90: match ambiguo;
- punteggio < 0.75: nessun match affidabile.

## Alias

È stato gestito esplicitamente l'alias:

    Michelangelo Merisi
    Merisi
    Caravaggio

Queste forme vengono ricondotte allo stesso artista.

## Memoria conversazionale

La memoria utilizza `MemoryRepository`.

Lo stato della conversazione conserva, tra le altre informazioni:

- ultimo intent;
- artista corrente;
- opera corrente;
- luogo corrente;
- risultati dell'ultima lista;
- indice del turno;
- opzioni di chiarimento.

Questo permette follow-up come:

    Quali opere di Caravaggio posso vedere a Napoli?

    Dove si trova il secondo elencato?

    A quando risale il dipinto?

    Mentre il terzo elencato dove si trova?

Il sistema mantiene sia l'opera corrente sia la lista originale
necessaria per risolvere successivi riferimenti ordinali.

## Inconsistency detection

Sono gestiti deterministicamente claim relativi a:

- autore;
- luogo;
- data.

Tipi principali di incongruenza:

- `WRONG_AUTHOR`;
- `WRONG_LOCATION`;
- `IMPOSSIBLE_DATE`;
- `ENTITY_NOT_FOUND`;
- `AMBIGUOUS_ENTITY`.

Le correzioni vengono ricavate dal repository.

La verifica deterministica ha priorità sulla risposta dell'LLM.

## Integrazione LLM

Il modello utilizzato è:

    qwen3:8b

eseguito localmente attraverso Ollama.

La factory crea `HybridChatbotService` quando:

    LLM_ENABLED=true

e utilizza direttamente `ChatbotService` quando:

    LLM_ENABLED=false

Il modello non ha accesso diretto a Neo4j e non può eseguire query
Cypher arbitrarie.

## Tool autorizzati

L'agent può utilizzare esclusivamente:

- `get_artwork_information`;
- `list_artworks_by_artist`;
- `list_artworks_by_place`;
- `list_places`;
- `list_places_with_artworks`;
- `get_artist_information`;
- `get_place_information`;
- `search_artworks`.

Il numero massimo di tool call per singola risposta è 4.

## Grounding

La risposta fattuale finale non viene generata liberamente dal
modello.

Il flusso è:

    LLM
        |
        v
    tool call
        |
        v
    KnowledgeRepository
        |
        v
    Neo4j
        |
        v
    GroundedAnswerRenderer

In questo modo il modello interpreta il linguaggio naturale, mentre
Neo4j rimane la fonte di verità.

## Richieste composte

Il sistema supporta richieste contenenti più esigenze nello stesso
turno.

Esempi verificati:

    Parlami di Caravaggio e dimmi anche quali sue opere posso
    visitare a Napoli.

    Chi ha dipinto il Martirio di sant'Orsola e dove si trova?

    Quali musei posso visitare e quali opere del database si
    trovano in ciascuno?

Per il caso luoghi + opere è stato introdotto il tool applicativo:

    list_places_with_artworks

che riusa:

    KnowledgeRepository.list_places()

e:

    KnowledgeRepository.list_artworks_by_place(place_name)

senza introdurre nuove query o nuovi metodi condivisi.

## Ottimizzazione delle prestazioni LLM

Durante i test iniziali Qwen 3 8B presentava tempi di risposta
elevati, dovuti in particolare al reasoning interno del modello.

Il client Ollama è stato configurato con:

    think=False

e:

    keep_alive="30m"

Questa modifica ha ridotto in modo sostanziale la latenza delle
richieste warm.

Il modello rimane caricato in memoria per un periodo di inattività,
riducendo il costo delle richieste successive.

## Speech-to-Text

Sono supportati due motori:

    STT_ENGINE=whisper

oppure:

    STT_ENGINE=google

Whisper rappresenta la modalità locale principale.

Google Speech Recognition può essere utilizzato come alternativa.

## Text-to-Speech

Le risposte del chatbot possono essere riprodotte vocalmente tramite
il componente Text-to-Speech.

La funzionalità è integrata sia nell'applicazione sia nella GUI.

## Interfaccia grafica

L'interfaccia Tkinter permette:

- inserimento manuale della domanda;
- acquisizione vocale;
- selezione del motore STT;
- visualizzazione della conversazione;
- riproduzione vocale della risposta;
- mantenimento della stessa sessione conversazionale.

Entry point:

    python .\gui_main.py

## Modalità terminale

È disponibile anche l'esecuzione da terminale:

    python .\main.py

La sessione viene mantenuta per tutta la durata dell'applicazione.

## File e componenti principali prodotti

Tra i componenti principali del contributo Persona 2 sono presenti:

    src/dialogue/
    src/gui/
    src/llm/
    src/nlp/
    src/speech/

Sono inoltre utilizzati i contratti comuni presenti in:

    src/core/

e i repository implementati attraverso:

    KnowledgeRepository
    MemoryRepository

Documentazione finale:

    README.md

    docs/specifications/shared-spec-v1.1.md

    docs/testing/final-functional-test-matrix.md

## Specifica condivisa

La specifica originale:

    docs/specifications/shared-spec-v1.0.md

rimane invariata.

La versione:

    docs/specifications/shared-spec-v1.1.md

documenta le estensioni condivise successive:

- `Intent.LIST_PLACES`;
- `EntityType.ORDINAL`;
- `KnowledgeRepository.list_places()`.

Il tool `list_places_with_artworks` rimane invece una funzionalità
applicativa del livello LLM e non modifica ulteriormente il contratto
del repository.

## Verifiche automatiche

La suite completa è stata eseguita con:

    python -m pytest -q

Risultato finale:

    296 test superati
    25 subtest superati
    0 fallimenti

Sono presenti warning di deprecazione noti che non causano fallimenti,
principalmente relativi a:

- `SpeechRecognition`;
- `datetime.utcnow()`.

## Test funzionale finale

È stato eseguito un maxi-test manuale end-to-end attraverso la GUI,
mantenendo una sola sessione conversazionale.

Sono state testate 26 diverse tipologie di richiesta.

Risultato:

    26 / 26 tipologie superate

Sono state verificate:

- informazioni su artista;
- informazioni su opera;
- descrizione;
- autore;
- luogo;
- data;
- richieste composte;
- query per artista;
- query per luogo;
- lista musei;
- lista musei con opere;
- informazioni sui luoghi;
- alias;
- fuzzy matching;
- titoli incompleti;
- memoria conversazionale;
- follow-up;
- riferimenti ordinali;
- inconsistenze;
- confronto tra artisti;
- formulazioni naturali;
- fuori dominio.

## Limitazioni residue

Sono rimasti due edge case accettati.

### Entità esterna al dominio

Con la domanda:

    Quali opere di Artemisia Gentileschi posso vedere a Napoli?

il sistema ha recuperato erroneamente l'artista precedente dalla
memoria conversazionale.

### Richiesta naturale filtrata per artista

Con la domanda:

    Sono a Napoli e vorrei vedere qualche quadro di
    Battistello Caracciolo: dove posso andare?

il modello ha restituito tutti i luoghi e le opere invece di
applicare correttamente il filtro per artista.

Entrambe le risposte rimangono grounded rispetto a Neo4j, ma la
selezione semantica non è perfetta.

Le limitazioni sono documentate in:

    docs/testing/final-functional-test-matrix.md

## Utilità pratica

Il sistema permette a un utente di esplorare attraverso linguaggio
naturale le opere del dominio presenti a Napoli.

La combinazione tra pipeline NLP e LLM permette di gestire sia
formulazioni strutturate sia richieste più naturali.

La memoria permette una conversazione multi-turno senza richiedere
la ripetizione continua di artisti e opere.

L'interfaccia vocale permette inoltre di utilizzare il chatbot senza
input esclusivamente testuale.

## Significato teorico

Il progetto combina diversi concetti tipici del Natural Language
Processing.

La pipeline deterministica realizza:

- intent classification;
- named entity recognition;
- entity linking;
- fuzzy matching;
- claim extraction;
- dialogue state tracking.

L'LLM introduce una componente di comprensione semantica più
flessibile.

Il tool calling separa però il reasoning linguistico dal recupero
delle informazioni.

Questo produce un'architettura grounded nella quale:

    linguaggio naturale -> interpretazione -> tool -> database

invece di:

    linguaggio naturale -> generazione libera della risposta

La separazione riduce il rischio di hallucination e rende il sistema
più controllabile.

## Decisioni progettuali principali

Durante lo sviluppo sono state adottate le seguenti decisioni:

1. mantenere Neo4j come unica fonte fattuale a runtime;
2. non interrogare direttamente DBpedia durante la conversazione;
3. non permettere all'LLM di generare Cypher;
4. mantenere la pipeline NLP deterministica;
5. usare Qwen per interpretazione semantica e tool selection;
6. verificare deterministicamente le inconsistenze;
7. usare dependency injection per i repository;
8. mantenere separata la memoria dalla knowledge base;
9. introdurre `list_places()` come estensione condivisa;
10. implementare `list_places_with_artworks` come tool composito
    senza modificare ulteriormente il repository;
11. mantenere un fallback deterministico;
12. utilizzare Qwen 3 8B come modello locale definitivo;
13. disabilitare il reasoning esteso tramite `think=False`;
14. mantenere il modello warm con `keep_alive="30m"`.

## Problemi risolti

Tra i principali problemi affrontati durante lo sviluppo:

- riconoscimento di titoli con errori;
- gestione di titoli incompleti;
- riconoscimento degli alias;
- follow-up senza ripetizione dell'opera;
- riferimenti ordinali a liste precedenti;
- conservazione della lista dopo un follow-up;
- correzione di autore errato;
- correzione di luogo errato;
- correzione di data errata;
- gestione della forma plurale nelle affermazioni di luogo;
- richieste artista + opere nello stesso turno;
- elenco generale dei luoghi;
- elenco dei luoghi con le opere associate;
- scelta errata di tool artista/opera;
- latenza elevata del modello locale;
- fallback quando l'LLM non è disponibile.

## Contributo al progetto

Il contributo della Persona 2 completa il livello di interazione tra
utente e knowledge base.

La Persona 1 fornisce acquisizione, qualità dei dati, schema,
popolamento e repository.

La Persona 2 fornisce:

- comprensione del linguaggio naturale;
- gestione del dialogo;
- memoria;
- rilevamento delle incongruenze;
- integrazione LLM;
- generazione delle risposte;
- interazione vocale;
- interfaccia utente.

Il risultato è un chatbot completo in grado di trasformare una
domanda testuale o vocale in una risposta grounded ottenuta dai dati
Neo4j.

## Stato finale

Il modulo Persona 2 è considerato funzionalmente completo per la
consegna.

Stato verificato:

    branch: persona2
    test automatici: 296 superati
    subtest: 25 superati
    fallimenti: 0
    test funzionale end-to-end: 26/26 tipologie superate

Le 26 tipologie del maxi-test funzionale finale risultano superate.
