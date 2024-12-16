from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from constants import MOVIES_GENRE_MAP, api_key
from tmdb_utils import (
    search_movie_by_title,
    get_movie_details,
    get_now_playing_movies,
    get_movies_by_genre,
    get_movie_reviews
)


class ActionMovieDetails(Action):
    """
    Azione per recuperare i dettagli di un film dato il titolo.
    """
    def name(self) -> Text:
        return "action_movie_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        title = tracker.get_slot("titolo_film")

        if not title:
            dispatcher.utter_message(text="Non ho capito il titolo del film, puoi ripetere?")
            return []

        if not api_key:
            dispatcher.utter_message(text="Manca la chiave API. Non posso recuperare i dettagli del film.")
            return []

        search_data = search_movie_by_title(title)

        results = search_data.get("results", [])
        if not results:
            dispatcher.utter_message(text="Non ho trovato nessun film con questo titolo.")
            return []

        movie = results[0]
        movie_id = movie.get("id")

        if not movie_id:
            dispatcher.utter_message(text="Non sono riuscito a recuperare l'ID del film.")
            return []

        details_data = get_movie_details(movie_id)
        movie_title = details_data.get("title", "Titolo non disponibile")
        overview = details_data.get("overview", "Nessuna trama disponibile")
        release_date = details_data.get("release_date", "Data di uscita non disponibile")

        dispatcher.utter_message(
            text=f"Ecco i dettagli su {movie_title}:\nTrama: {overview}\nData di uscita: {release_date}"
        )
        return []


class ActionRecentReleases(Action):
    """
    Azione per ottenere i film appena usciti.
    """
    def name(self) -> Text:
        return "action_recent_releases"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        data = get_now_playing_movies()
        results = data.get("results", [])

        if not results:
            dispatcher.utter_message(text="Non ho trovato film recentemente usciti.")
            return []

        messaggio = "Ecco alcuni film attualmente in sala:\n"
        for movie in results[:5]:
            title = movie.get("title", "Titolo non disponibile")
            release_date = movie.get("release_date", "Data non disponibile")
            overview = movie.get("overview", "Trama non disponibile")
            messaggio += f"\n• {title} (uscito il {release_date})\n{overview}\n"

        dispatcher.utter_message(text=messaggio)
        return []


class ActionSearchByGenre(Action):
    """
    Azione per ottenere film di un certo genere.
    """
    def name(self) -> Text:
        return "action_search_by_genre"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        genere = tracker.get_slot("genere")
        if not genere:
            dispatcher.utter_message(text="Non ho capito il genere che cerchi.")
            return []

        genre_id = MOVIES_GENRE_MAP.get(genere.lower())
        if not genre_id:
            dispatcher.utter_message(text=f"Non conosco il genere {genere}, prova con un altro.")
            return []

        data = get_movies_by_genre(genre_id)
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
    """
    Azione placeholder per indicare dove guardare un film.
    """
    def name(self) -> Text:
        return "action_where_to_watch"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Qui potresti implementare una chiamata a TMDb per watch providers
        # Per ora uso un placeholder
        dispatcher.utter_message(text="Questo film è disponibile su Netflix")
        return []


class MovieReviews(Action):
    """
    Azione per ottenere le recensioni di un film.
    """
    def name(self) -> Text:
        return "movie_reviews"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        titolo = tracker.get_slot("titolo_film")

        if not titolo:
            dispatcher.utter_message(text="Non ho capito il titolo del film, puoi ripetere?")
            return []

        if not api_key:
            dispatcher.utter_message(text="Manca la chiave API. Non posso recuperare i dettagli del film.")
            return []

        search_data = search_movie_by_title(titolo)

        results = search_data.get("results", [])
        if not results:
            dispatcher.utter_message(text="Non ho trovato nessun film con questo titolo.")
            return []

        movie = results[0]
        movie_id = movie.get("id")

        if not movie_id:
            dispatcher.utter_message(text="Non sono riuscito a recuperare l'ID del film.")
            return []

        reviews_data = get_movie_reviews(movie_id)
        reviews = reviews_data.get("results", [])

        if reviews:
            for review in reviews[:5]:
                author = review.get("author", "Autore sconosciuto")
                content = review.get("content", "Recensione non disponibile")
                truncated_content = content[:500]
                dispatcher.utter_message(
                    text=f"Autore: {author}\nRecensione: {truncated_content}"
                )
        else:
            dispatcher.utter_message(text="Non sono disponibili recensioni per questo film.")

        return []


class PopularMovies(Action):
    """
    Azione per ottenere i film più popolari.
    """
    def name(self) -> Text:
        return "popular_movies"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Esempio di come usare direttamente tmdb_utils
        # Se preferisci, puoi creare una funzione "get_popular_movies()" in tmdb_utils.
        from tmdb_utils import make_tmdb_request
        popular_data = make_tmdb_request("/movie/popular", {"language": "it-IT"})
        movies = popular_data.get("results", [])

        if not movies:
            dispatcher.utter_message(text="Non ho trovato film popolari al momento.")
            return []

        response = "Ecco i film più popolari:\n"
        for idx, movie in enumerate(movies[:5], start=1):
            title = movie.get("title", "Titolo non disponibile")
            release_date = movie.get("release_date", "Data di uscita non disponibile")
            response += f"{idx}. {title} (Data di uscita: {release_date})\n"

        dispatcher.utter_message(text=response)

        return []
