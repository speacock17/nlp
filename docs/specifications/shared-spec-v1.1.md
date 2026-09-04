# Specifica condivisa v1.1

## Stato

**Versione:** 1.1
**Versione precedente:** 1.0
**Branch ufficiale:** `main`
**Versione Python:** 3.12.5

Questa specifica estende la specifica condivisa v1.0 senza
sostituirla.

La versione originale rimane disponibile in:

    docs/specifications/shared-spec-v1.0.md

Tutti i vincoli, i modelli, le interfacce e le regole definiti nella
v1.0 restano validi, salvo le estensioni esplicitamente documentate
in questo file.

## Obiettivo della revisione

La versione 1.1 documenta le estensioni del contratto condiviso
necessarie per supportare:

- richieste relative all'elenco dei luoghi presenti nella knowledge base;
- accesso uniforme ai luoghi attraverso `KnowledgeRepository`;
- riferimenti ordinali ai risultati di una lista precedente.

Non vengono introdotte modifiche incompatibili con le interfacce
preesistenti.

## Estensione degli intenti

È aggiunto il seguente valore all'enum `Intent`:

    LIST_PLACES = "list_places"

L'intent rappresenta richieste generiche come:

    Quali musei posso visitare a Napoli?

    Quali luoghi sono presenti nel database?

La presenza dell'intent permette alla pipeline NLP e al servizio
Hybrid di distinguere una richiesta relativa all'elenco dei luoghi
da una richiesta relativa alle opere presenti in uno specifico luogo.

## Estensione dei tipi di entità

L'enum `EntityType` comprende inoltre:

    ORDINAL = "ordinal"

Il tipo `ORDINAL` viene utilizzato per riferimenti contestuali quali:

    il primo
    il secondo
    il terzo

L'ordinale non rappresenta una nuova entità della knowledge base.
Serve invece alla risoluzione del contesto conversazionale e viene
interpretato rispetto all'ordine dei risultati memorizzati nel
`DialogueState`.

## Estensione di KnowledgeRepository

L'interfaccia condivisa `KnowledgeRepository` comprende il metodo:

    def list_places(self) -> list[Place]:
        ...

Il metodo deve:

- restituire oggetti `Place`;
- restituire esclusivamente luoghi presenti nella knowledge base;
- non accedere direttamente a fonti esterne durante il runtime;
- essere implementato da tutte le implementazioni concrete del
  repository utilizzate dal sistema;
- produrre un risultato deterministico rispetto ai dati disponibili.

## Implementazioni coinvolte

Le implementazioni compatibili comprendono:

- `Neo4jKnowledgeRepository`;
- `MockKnowledgeRepository`.

Entrambe devono rispettare la stessa firma:

    list_places() -> list[Place]

L'implementazione Neo4j utilizza il database locale come fonte di
verità.

L'implementazione mock viene utilizzata nei test senza modificare il
contratto pubblico.

## Utilizzo nel livello LLM

L'estensione del repository permette al livello LLM di esporre il
tool controllato:

    list_places

Il tool costituisce un adattatore verso `KnowledgeRepository` e non
modifica il contratto del repository.

È inoltre presente a livello applicativo il tool composito:

    list_places_with_artworks

Questo tool non introduce nuovi metodi condivisi.

La sua implementazione riutilizza:

    KnowledgeRepository.list_places()

e:

    KnowledgeRepository.list_artworks_by_place(place_name)

Di conseguenza `list_places_with_artworks` rimane una funzionalità
del livello LLM/applicativo e non richiede ulteriori modifiche alla
specifica condivisa.

## Dependency injection

Rimane invariata la regola della v1.0.

I repository vengono forniti dall'esterno ai servizi che ne hanno
bisogno.

In particolare, il livello LLM accede ai dati attraverso
`KnowledgeToolExecutor`, che riceve un'istanza compatibile con
`KnowledgeRepository`.

Non vengono create connessioni Neo4j direttamente all'interno
dell'LLM.

## Fonte di verità

Rimane invariato il principio definito nella versione 1.0:

    DBpedia -> acquisizione e preparazione dati -> Neo4j

Durante il normale utilizzo del chatbot:

    chatbot -> KnowledgeRepository -> Neo4j

DBpedia non viene interrogata direttamente dal chatbot.

L'LLM non rappresenta una fonte fattuale.

## Compatibilità

La versione 1.1 è additiva.

Le funzionalità introdotte non modificano:

- i modelli `Artist`, `Artwork` e `Place`;
- i tipi di claim;
- i tipi di inconsistenza;
- le firme dei metodi già presenti;
- le soglie di fuzzy matching;
- `normalize_text`;
- `MemoryRepository`;
- le regole di dependency injection.

Il codice che implementava correttamente la specifica v1.0 rimane
concettualmente compatibile; le implementazioni concrete di
`KnowledgeRepository` devono inoltre implementare `list_places()`.

## Contratto condiviso risultante

Le principali estensioni rispetto alla v1.0 sono quindi:

1. nuovo intent:

       LIST_PLACES

2. supporto ai riferimenti ordinali tramite:

       EntityType.ORDINAL

3. nuovo metodo condiviso:

       KnowledgeRepository.list_places() -> list[Place]

4. nessuna nuova dipendenza diretta tra LLM e Neo4j;

5. nessuna modifica ai principi di normalizzazione, fuzzy matching,
   dependency injection e rappresentazione dei valori mancanti.

## Versionamento

La specifica v1.0 non deve essere modificata retroattivamente.

Eventuali ulteriori modifiche ai contratti condivisi dovranno essere
documentate in una nuova versione della specifica.
