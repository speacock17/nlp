# Matrice finale dei test funzionali

## Configurazione del test

Il test funzionale finale è stato eseguito manualmente attraverso
l'interfaccia grafica Tkinter, mantenendo la stessa sessione
conversazionale per tutta la sequenza.

Componenti attivi:

- interfaccia grafica Tkinter;
- input testuale;
- Qwen 3 8B tramite Ollama;
- `HybridChatbotService`;
- pipeline NLP deterministica;
- knowledge base Neo4j;
- memoria conversazionale;
- grounded answer generation.

Data del test finale: settembre 2026.

## Risultato complessivo

- 26 tipologie di domanda testate;
- 24 casi superati;
- 2 limitazioni note;
- nessun crash;
- nessuna anomalia di accesso a Neo4j;
- memoria conversazionale funzionante;
- inconsistency detection funzionante;
- fuzzy matching funzionante;
- tool calling funzionante.

Le due limitazioni residue sono descritte nella sezione finale e sono
state accettate come edge case non bloccanti per la consegna.

## Matrice

| ID | Area | Domanda | Risultato ottenuto | Esito |
|---|---|---|---|---|
| F01 | Informazioni artista | Chi era Caravaggio? | Restituite le informazioni disponibili su Caravaggio. | SUPERATO |
| F02 | Informazioni opera | Parlami della Flagellazione di Cristo. | Restituiti autore, luogo, data, tecnica e descrizione disponibili. | SUPERATO |
| F03 | Descrizione opera | Cosa rappresenta la Flagellazione di Cristo? | Restituita la descrizione disponibile nel database senza aggiungere informazioni esterne. | SUPERATO |
| F04 | Richiesta composta | Parlami di Caravaggio e dimmi anche quali sue opere posso visitare a Napoli. | Informazioni sull'artista più elenco delle 3 opere di Caravaggio presenti nel database. | SUPERATO |
| F05 | Riferimento ordinale | Dove si trova il secondo elencato? | Risolta correttamente la seconda opera della lista precedente: Sette opere di Misericordia, Pio Monte della Misericordia. | SUPERATO |
| F06 | Follow-up contestuale | A quando risale il dipinto? | Conservato il riferimento all'opera corrente e restituito l'anno 1607. | SUPERATO |
| F07 | Ritorno alla lista | Mentre il terzo elencato dove si trova? | Recuperato correttamente il terzo elemento della lista originale: Martirio di sant'Orsola, Palazzo Zevallos. | SUPERATO |
| F08 | Autore opera | Chi ha dipinto le Sette opere di Misericordia? | Caravaggio. | SUPERATO |
| F09 | Luogo opera | Dove si trova il Martirio di sant'Orsola? | Palazzo Zevallos, Napoli. | SUPERATO |
| F10 | Data opera | In che anno è stata realizzata la Flagellazione di Cristo? | 1607. | SUPERATO |
| F11 | Richiesta composta opera | Chi ha dipinto il Martirio di sant'Orsola e dove si trova? | Restituiti correttamente autore Caravaggio e Palazzo Zevallos. | SUPERATO |
| F12 | Opere per luogo | Quali opere posso vedere al Museo nazionale di Capodimonte? | Restituite le 4 opere presenti nel database presso Capodimonte. | SUPERATO |
| F13 | Lista luoghi | Quali musei posso visitare a Napoli? | Restituiti i 7 luoghi presenti nella knowledge base. | SUPERATO |
| F14 | Luoghi con opere | Quali musei posso visitare e quali opere del database si trovano in ciascuno? | Restituiti i 7 luoghi con le relative 11 opere, raggruppate correttamente. | SUPERATO |
| F15 | Informazioni luogo | Parlami del Museo nazionale di Capodimonte. | Restituiti città, indirizzo e descrizione disponibili. | SUPERATO |
| F16 | Alias artista | Quali opere di Michelangelo Merisi posso vedere a Napoli? | Alias normalizzato correttamente a Caravaggio e restituite le 3 opere. | SUPERATO |
| F17 | Fuzzy matching | Dove si trova il Martirio di sant Orsloa? | Titolo con errore ricondotto al Martirio di sant'Orsola; restituito Palazzo Zevallos. | SUPERATO |
| F18 | Titolo incompleto | Descrivimi la Flagellazione. | Titolo incompleto ricondotto alla Flagellazione di Cristo e restituita la descrizione disponibile. | SUPERATO |
| F19 | Incongruenza autore | Il Martirio di sant'Orsola è di Battistello Caracciolo? | Autore errato rilevato deterministicamente e corretto in Caravaggio. | SUPERATO |
| F20 | Incongruenza luogo | Le Sette opere di Misericordia si trovano al Museo di Capodimonte? | Luogo errato rilevato e corretto in Pio Monte della Misericordia. | SUPERATO |
| F21 | Incongruenza data | Il Martirio di sant'Orsola è stato realizzato nel 1607? | Data corretta restituita: 1610. | SUPERATO |
| F22 | Affermazione corretta | Il Martirio di sant'Orsola si trova a Palazzo Zevallos? | Confermata implicitamente la collocazione corretta a Palazzo Zevallos. | SUPERATO |
| F23 | Confronto artisti | Confronta Caravaggio e Battistello Caracciolo. | Restituite informazioni grounded su entrambi gli artisti. | SUPERATO |
| F24 | Artista fuori knowledge base | Quali opere di Artemisia Gentileschi posso vedere a Napoli? | Il sistema ha restituito erroneamente le opere di Caravaggio, recuperando un contesto precedente. | NON SUPERATO |
| F25 | Formulazione naturale filtrata per artista | Sono a Napoli e vorrei vedere qualche quadro di Battistello Caracciolo: dove posso andare? | Il sistema ha restituito tutti i luoghi e tutte le opere invece di limitarsi a Battistello Caracciolo. | NON SUPERATO |
| F26 | Fuori dominio | Qual è il miglior ristorante vicino al Museo di Capodimonte? | Domanda correttamente riconosciuta come fuori dominio, senza fornire informazioni esterne. | SUPERATO |

## Verifica della memoria conversazionale

Le domande F04-F07 sono state eseguite consecutivamente nella stessa
sessione per verificare la memoria.

Sequenza:

1. richiesta delle opere di Caravaggio;
2. riferimento al secondo elemento;
3. richiesta della data senza ripetere il titolo;
4. ritorno al terzo elemento della lista originale.

Il sistema ha mantenuto correttamente:

- opera corrente;
- lista precedente;
- ordine dei risultati;
- riferimenti ordinali;
- contesto necessario ai follow-up.

## Verifica delle inconsistenze

Sono state verificate tre categorie:

- autore errato;
- luogo errato;
- data errata.

In tutti i casi testati la correzione è stata ottenuta
deterministicamente attraverso i dati della knowledge base.

## Verifica del fuzzy matching

Sono stati verificati:

- errore ortografico nel titolo:
  `Martirio di sant Orsloa`;
- titolo parziale:
  `Flagellazione`.

Entrambi i casi sono stati ricondotti all'opera corretta.

## Verifica delle richieste composte

Sono state verificate richieste contenenti più informazioni nello
stesso turno.

Esempi:

- informazioni sull'artista + opere visitabili;
- autore dell'opera + luogo;
- lista dei musei + opere presenti in ciascuno.

Il sistema ha utilizzato correttamente più tool oppure il tool
composito appropriato.

## Limitazioni note

### L01 - Entità esterna al dominio in presenza di contesto precedente

Domanda:

    Quali opere di Artemisia Gentileschi posso vedere a Napoli?

Durante il test il sistema ha recuperato erroneamente Caravaggio dal
contesto precedente invece di indicare che Artemisia Gentileschi non
è presente nel dominio supportato.

La limitazione riguarda la gestione di entità non riconosciute quando
è disponibile un artista precedente nella memoria conversazionale.

### L02 - Richiesta naturale filtrata per artista

Domanda:

    Sono a Napoli e vorrei vedere qualche quadro di
    Battistello Caracciolo: dove posso andare?

Il modello ha selezionato `list_places_with_artworks` invece di
`list_artworks_by_artist`, restituendo anche opere di Caravaggio.

La risposta rimane grounded e non contiene informazioni inventate,
ma il filtro semantico richiesto dall'utente non viene rispettato.

## Valutazione

Il test finale copre le principali capacità richieste dal progetto:

- informazioni su artisti, opere e luoghi;
- query per artista e per luogo;
- richieste composte;
- memoria conversazionale;
- follow-up;
- riferimenti ordinali;
- fuzzy matching;
- alias;
- inconsistency detection;
- tool calling;
- grounding;
- gestione fuori dominio.

Risultato finale:

    24 / 26 tipologie superate

Le due limitazioni residue sono edge case di interpretazione
semantica e gestione del contesto e non compromettono il normale
funzionamento delle principali funzionalità del chatbot.

## Test automatici

La suite automatica finale è stata verificata con:

    python -m pytest -q

Risultato:

    295 test superati
    25 subtest superati
    0 fallimenti
