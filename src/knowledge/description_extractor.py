import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


INPUT_PATH = Path("data/processed/combined_knowledge.json")

WIKIPEDIA_TITLES = {
    "http://dbpedia.org/resource/The_Flagellation_of_Christ_(Caravaggio)":
        "Flagellazione di Cristo (Caravaggio)",
    "http://dbpedia.org/resource/The_Martyrdom_of_Saint_Ursula_(Caravaggio)":
        "Martirio di sant'Orsola",
    "http://dbpedia.org/resource/The_Seven_Works_of_Mercy_(Caravaggio)":
        "Sette opere di Misericordia",
    "http://it.dbpedia.org/resource/Battesimo_di_Cristo_(Battistello_Caracciolo)":
        "Battesimo di Cristo (Battistello Caracciolo)",
    "http://it.dbpedia.org/resource/Cristo_alla_colonna_(Battistello_Caracciolo)":
        "Cristo alla colonna (Battistello Caracciolo)",
    "http://it.dbpedia.org/resource/Crocifissione_di_Cristo_(Battistello_Caracciolo)":
        "Crocifissione di Cristo (Battistello Caracciolo)",
    "http://it.dbpedia.org/resource/Immacolata_Concezione_con_san_Domenico_e_san_Francesco_di_Paola":
        "Immacolata Concezione con san Domenico e san Francesco di Paola",
    "http://it.dbpedia.org/resource/Lavanda_dei_piedi_(Caracciolo)":
        "Lavanda dei piedi (Battistello Caracciolo)",
    "http://it.dbpedia.org/resource/Liberazione_di_san_Pietro_(Caracciolo)":
        "Liberazione di san Pietro (Battistello Caracciolo)",
    "http://it.dbpedia.org/resource/Madonna_delle_anime_purganti_tra_san_Francesco_e_santa_Chiara":
        "Madonna delle anime purganti tra san Francesco e santa Chiara",
    "http://it.dbpedia.org/resource/Storie_di_Consalvo_di_Córdoba":
        "Storie di Consalvo di Córdoba",
}


def fetch_wikipedia_extract(title: str) -> str:
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": "1",
        "redirects": "1",
        "titles": title,
        "format": "json",
        "formatversion": "2",
    }

    url = (
        "https://it.wikipedia.org/w/api.php?"
        + urlencode(params)
    )

    request = Request(
        url,
        headers={
            "User-Agent": (
                "NLP-University-Project/1.0 "
                "(educational research)"
            )
        },
    )

    retry_delays = (5, 10, 20)

    for attempt in range(len(retry_delays) + 1):
        try:
            with urlopen(request, timeout=20) as response:
                data = json.load(response)
            break

        except HTTPError as error:
            if error.code != 429 or attempt == len(retry_delays):
                raise

            delay = retry_delays[attempt]
            print(
                f"HTTP 429 per {title}. "
                f"Nuovo tentativo tra {delay} secondi..."
            )
            time.sleep(delay)

    page = data["query"]["pages"][0]
    extract = page.get("extract")

    if not isinstance(extract, str) or not extract.strip():
        raise ValueError(
            f"Nessun testo Wikipedia disponibile per: {title}"
        )

    return extract.strip()


def extract_description_section(text: str) -> str:
    preferred_sections = (
        "Descrizione e stile",
        "Storia e descrizione",
        "Descrizione",
    )

    for section_name in preferred_sections:
        pattern = (
            rf"^==\s*{re.escape(section_name)}\s*==\s*\n"
            rf"(.*?)(?=^==\s|\Z)"
        )

        match = re.search(
            pattern,
            text,
            flags=re.MULTILINE | re.DOTALL,
        )

        if match is not None:
            return match.group(1).strip()

    raise ValueError(
        "Nessuna sezione descrittiva riconosciuta"
    )


def enrich_descriptions(data: dict) -> dict:
    for artwork in data["artworks"]:
        uri = artwork["uri"]

        if uri not in WIKIPEDIA_TITLES:
            raise KeyError(
                f"Nessuna pagina Wikipedia configurata per: {uri}"
            )

        title = WIKIPEDIA_TITLES[uri]
        wikipedia_text = fetch_wikipedia_extract(title)
        description = extract_description_section(wikipedia_text)

        artwork["description"] = description

        print(
            f"Description recuperata: {artwork['title']} "
            f"({len(description)} caratteri)"
        )

        time.sleep(3)

    return data


def main() -> None:
    print(f"Dataset: {INPUT_PATH}")
    print(f"Pagine Wikipedia configurate: {len(WIKIPEDIA_TITLES)}")


if __name__ == "__main__":
    main()
