# Specifica condivisa v1.0

## Stato

**Versione:** 1.0
**Stato:** congelata
**Branch ufficiale:** `main`
**Versione Python:** 3.12.5

Questa specifica costituisce il contratto comune tra Persona 1 e Persona 2.

I contenuti definiti in questa specifica non possono essere modificati
autonomamente da nessuna delle due persone.

Qualsiasi modifica deve essere:

1. concordata nella chat principale del progetto;
2. applicata sul branch `main`;
3. documentata;
4. identificata mediante una nuova versione della specifica;
5. recepita da entrambi i moduli.

## Obiettivo del progetto

Realizzare uno speech chatbot dedicato alle opere di Caravaggio e
Battistello Caracciolo visitabili nell'area urbana di Napoli.

Il flusso generale della conoscenza è:

`DBpedia → query SPARQL → dati JSON → normalizzazione → Neo4j`

Durante il normale utilizzo, il chatbot interroga Neo4j e non DBpedia
direttamente.

## Componenti comuni congelati

Sono parte del contratto condiviso:

- intenti;
- tipi di entità;
- tipi di claim;
- tipi di incongruenza;
- modelli e nomi dei relativi campi;
- tipi dei campi e valori predefiniti;
- struttura dei risultati;
- interfaccia `KnowledgeRepository`;
- interfaccia `MemoryRepository`;
- firme e nomi dei metodi;
- regole di normalizzazione;
- soglie di fuzzy matching;
- modalità di dependency injection nel `DialogueManager`.

## Modelli condivisi

I modelli comuni sono:

- `Artist`;
- `Place`;
- `Artwork`;
- `EntityMention`;
- `Claim`;
- `NLUResult`;
- `Inconsistency`;
- `DialogueState`;
- `ConversationTurn`;
- `BotResponse`.

## Repository condivisi

Le interfacce ufficiali sono:

- `KnowledgeRepository`;
- `MemoryRepository`.

Le implementazioni definitive previste sono:

- `Neo4jKnowledgeRepository`;
- `Neo4jMemoryRepository`.

La Persona 2 può utilizzare implementazioni temporanee compatibili:

- `MockKnowledgeRepository`;
- `MockMemoryRepository`.

Non deve essere introdotta un'interfaccia generica denominata
`Neo4jRepository`.

## Dependency injection

Il `DialogueManager` deve ricevere dall'esterno:

- `knowledge_repository`;
- `memory_repository`.

Non deve creare direttamente le implementazioni concrete dei repository.

## Valori mancanti

I valori non disponibili devono essere rappresentati mediante `None`.

Non devono essere usate stringhe arbitrarie come:

- `"unknown"`;
- `"not available"`;
- `"N/A"`.

## Normalizzazione

Tutti i moduli devono utilizzare la stessa funzione condivisa:

`normalize_text`

Non devono essere implementate versioni alternative della normalizzazione
nei moduli personali.

## Fuzzy matching

Le soglie condivise sono:

- punteggio maggiore o uguale a `0.90`: corrispondenza accettata;
- punteggio compreso tra `0.75` e `0.90`: corrispondenza ambigua;
- punteggio inferiore a `0.75`: nessuna corrispondenza affidabile.

## Organizzazione del lavoro

Il branch `main` contiene esclusivamente la base e i contratti comuni.

I moduli specifici vengono sviluppati nei branch personali e devono dipendere
dalla specifica condivisa senza modificarla autonomamente.
