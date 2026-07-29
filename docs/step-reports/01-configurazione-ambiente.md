# Step 1 — Configurazione dell’ambiente di sviluppo

## Obiettivo

Predisporre un ambiente di sviluppo riproducibile per il modulo della Persona 1, comprendente Python, Git, Docker, Neo4j e il collegamento tra l’applicazione Python e il database a grafo.

## Attività svolte

- Verifica di Python 3.12.5.
- Verifica di Git 2.50.1.
- Identificazione dell’architettura Apple Silicon ARM64.
- Installazione e verifica di Docker Desktop.
- Test di Docker mediante l’immagine `hello-world`.
- Configurazione dell’autenticazione con GitHub.
- Collegamento al repository `speacock17/nlp`.
- Creazione del branch personale `matteo`.
- Creazione dell’ambiente virtuale Python `.venv`.
- Configurazione del file `.gitignore`.
- Creazione dei file `.env` e `.env.example`.
- Configurazione di Neo4j tramite Docker Compose.
- Creazione dei volumi persistenti per dati e log.
- Creazione della cartella `data/import`.
- Avvio di Neo4j Community 5.26.28.
- Verifica di Neo4j Browser.
- Verifica della query Cypher `RETURN 1 AS ok`.
- Installazione dei pacchetti `neo4j` e `python-dotenv`.
- Verifica della connessione Python-Neo4j.
- Creazione del file `requirements.txt`.
- Commit e push della configurazione sul branch `matteo`.

## File prodotti

- `.env.example`
- `compose.yaml`
- `requirements.txt`
- `data/import/.gitkeep`

Il file `.env` contiene le credenziali locali ed è escluso dal versionamento tramite `.gitignore`.

## Utilità pratica

La configurazione permette di avviare Neo4j in maniera uniforme tramite Docker Compose e di collegarsi al database sia dal Browser di Neo4j sia dall’applicazione Python.

La presenza di `.env.example` documenta le variabili richieste senza pubblicare credenziali sensibili. Il file `requirements.txt` consente di reinstallare le stesse dipendenze Python su un altro computer.

## Significato teorico

Docker realizza l’isolamento del database rispetto al sistema operativo. L’ambiente virtuale Python isola invece le dipendenze dell’applicazione dalle altre installazioni presenti nel computer.

I volumi Docker rendono persistenti dati e log, separando il ciclo di vita del database da quello del container.

Il protocollo Bolt, esposto sulla porta 7687, viene utilizzato dal driver Python per comunicare con Neo4j. La porta 7474 espone invece l’interfaccia web Neo4j Browser.

## Verifiche effettuate

Sono stati verificati:

1. il funzionamento del motore Docker;
2. l’avvio del container Neo4j;
3. l’esposizione delle porte 7474 e 7687;
4. l’accesso tramite Neo4j Browser;
5. l’esecuzione di una query Cypher;
6. il caricamento delle credenziali dal file `.env`;
7. la connessione tramite il driver Python ufficiale.

Il percorso verificato è:

`Python → driver Neo4j → protocollo Bolt → database Neo4j`

## Contributo al progetto

Questo step fornisce l’infrastruttura necessaria per:

- importare i dati ottenuti da DBpedia;
- popolare il grafo Neo4j;
- eseguire query Cypher;
- implementare i repository applicativi;
- persistere la memoria conversazionale;
- integrare il modulo della Persona 1 con quello della Persona 2.
