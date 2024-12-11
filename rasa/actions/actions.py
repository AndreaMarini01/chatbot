from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import os, requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("TMDB_API_KEY")
base_url = "https://api.themoviedb.org/3"

GENRE_MAP = {
    "azione": 28,
    "avventura": 12,
    "animazione": 16,
    "commedia": 35,
    "crime": 80,
    "documentario": 99,
    "dramma": 18,
    "famiglia": 10751,
    "fantasy": 14,
    "storia": 36,
    "horror": 27,
    "musica": 10402,
    "mistero": 9648,
    "romantico": 10749,
    "fantascienza": 878,
    "thriller": 53,
    "guerra": 10752,
    "western": 37
}

class ActionMovieDetails(Action):
    def name(self) -> Text:
        return "action_movie_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        titolo = tracker.get_slot("titolo_film")

        if not titolo:
            dispatcher.utter_message(text="Non ho capito il titolo del film, puoi ripetere?")
            return []

        # DEBUG: Stampa il titolo estratto
        print(f"DEBUG: Titolo estratto: {titolo}")

        if not api_key:
            dispatcher.utter_message(text="Manca la chiave API. Non posso recuperare i dettagli del film.")
            return []

        # Prima chiamata: ricerca del film per titolo
        url_search = f"{base_url}/search/movie?api_key={api_key}&query={titolo}&language=it-IT"
        r_search = requests.get(url_search)

        # DEBUG: Stampa lo status code della ricerca
        print(f"DEBUG: Status code ricerca film: {r_search.status_code}")

        if r_search.status_code != 200:
            dispatcher.utter_message(text="Si è verificato un errore nella chiamata all'API TMDb per la ricerca.")
            return []

        search_data = r_search.json()

        # DEBUG: Stampa la risposta della ricerca
        print(f"DEBUG: Risultati ricerca: {search_data}")

        if not search_data.get("results"):
            dispatcher.utter_message(text="Non ho trovato nessun film con questo titolo.")
            return []

        # Ottieni l'ID del primo film trovato
        movie = search_data["results"][0]
        movie_id = movie.get("id")

        if not movie_id:
            dispatcher.utter_message(text="Non sono riuscito a recuperare l'ID del film.")
            return []

        # DEBUG: Stampa l'ID del film trovato
        print(f"DEBUG: ID del film trovato: {movie_id}")

        # Seconda chiamata: dettagli del film tramite ID
        url_details = f"{base_url}/movie/{movie_id}?api_key={api_key}&language=it-IT"
        r_details = requests.get(url_details)

        # DEBUG: Stampa lo status code della chiamata ai dettagli
        print(f"DEBUG: Status code dettagli film: {r_details.status_code}")

        if r_details.status_code != 200:
            dispatcher.utter_message(text="Si è verificato un errore nella chiamata all'API TMDb per i dettagli del film.")
            return []

        details_data = r_details.json()

        # DEBUG: Stampa la risposta dei dettagli
        print(f"DEBUG: Dettagli film: {details_data}")

        # Recupera le informazioni dai dettagli
        title = details_data.get("title", "Titolo non disponibile")
        overview = details_data.get("overview", "Nessuna trama disponibile")
        release_date = details_data.get("release_date", "Data di uscita non disponibile")

        # Risposta finale
        dispatcher.utter_message(
            text=f"Ecco i dettagli su {title}:\nTrama: {overview}\nData di uscita: {release_date}"
        )
        return []



class ActionRecentReleases(Action):
    def name(self) -> Text:
        return "action_recent_releases"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Chiamata a TMDb per ottenere i film in sala
        url_now_playing = f"{base_url}/movie/now_playing?api_key={api_key}&language=it-IT"
        r = requests.get(url_now_playing)
        data = r.json()

        # Controlliamo i risultati
        results = data.get("results", [])
        if not results:
            dispatcher.utter_message(text="Non ho trovato film recentemente usciti.")
            return []

        # Prepariamo una risposta user-friendly
        messaggio = "Ecco alcuni film attualmente in sala:\n"
        # Limitiamo il numero di film per non sovraccaricare l'utente
        for movie in results[:5]:
            title = movie.get("title", "Titolo non disponibile")
            release_date = movie.get("release_date", "Data non disponibile")
            overview = movie.get("overview", "Trama non disponibile")
            messaggio += f"\n• {title} (uscito il {release_date})\n{overview}\n"

        dispatcher.utter_message(text=messaggio)
        return []


class ActionSearchByGenre(Action):
    def name(self) -> Text:
        return "action_search_by_genre"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        genere = tracker.get_slot("genere")
        if not genere:
            dispatcher.utter_message(text="Non ho capito il genere che cerchi.")
            return []

        genre_id = GENRE_MAP.get(genere.lower())
        if not genre_id:
            dispatcher.utter_message(text=f"Non conosco il genere {genere}, prova con un altro.")
            return []

        # Chiamata a TMDb per film del genere selezionato
        url_genre = f"{base_url}/discover/movie?api_key={api_key}&with_genres={genre_id}&language=it-IT"
        r = requests.get(url_genre)
        data = r.json()
        results = data.get("results", [])

        if not results:
            dispatcher.utter_message(text=f"Non ho trovato film del genere {genere}.")
            return []

        messaggio = f"Ecco alcuni film del genere {genere}:\n"
        for movie in results[:5]:
            title = movie.get("title", "Titolo non disponibile")
            overview = movie.get("overview", "Trama non disponibile")
            messaggio += f"\n• {title}\n{overview}\n"

        dispatcher.utter_message(text=messaggio)
        return []


class ActionWhereToWatch(Action):
    def name(self) -> Text:
        return "action_where_to_watch"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Qui implementi la chiamata a TMDb per sapere dove vedere un film

        watch_provider = "Netflix"
        dispatcher.utter_message(text=f"Questo film è disponibile su {watch_provider}")
        return []