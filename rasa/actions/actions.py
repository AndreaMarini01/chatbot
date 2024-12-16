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
            dispatcher.utter_message(text="_Non ho capito il titolo del film, puoi ripetere?_")
            return []

        if not api_key:
            dispatcher.utter_message(text="_Manca la chiave API. Non posso recuperare i dettagli del film._")
            return []

        search_data = search_movie_by_title(title)

        results = search_data.get("results", [])
        if not results:
            dispatcher.utter_message(text=f"_Non ho trovato nessun film con questo titolo: *{title}*._")
            return []

        movie = results[0]
        movie_id = movie.get("id")

        if not movie_id:
            dispatcher.utter_message(text="_Non sono riuscito a recuperare l'ID del film._")
            return []

        details_data = get_movie_details(movie_id)
        movie_title = details_data.get("title", "Titolo non disponibile")
        overview = details_data.get("overview", "Nessuna trama disponibile")
        release_date = details_data.get("release_date", "Data di uscita non disponibile")

        # Formattiamo la trama con una lunghezza ragionevole (se è troppo lunga)
        truncated_overview = overview[:500] + "..." if len(overview) > 500 else overview

        message = (
            f"🎬 *{movie_title}*\n\n"
            f"📅 _Data di uscita:_ {release_date}\n\n"
            f"📝 *Trama:*\n{truncated_overview}"
        )

        dispatcher.utter_message(text=message)
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
            dispatcher.utter_message(text="_Non ho trovato film recentemente usciti._")
            return []

        # Titolo del messaggio
        messaggio = "🎬 *Film recentemente in sala:*\n"
        for movie in results[:5]:
            title = movie.get("title", "Titolo non disponibile")
            release_date = movie.get("release_date", "Data non disponibile")
            overview = movie.get("overview", "Trama non disponibile")

            # Truncare l'overview se troppo lunga
            truncated_overview = overview[:300] + "..." if len(overview) > 300 else overview

            messaggio += (
                f"\n• *{title}*"
                f"\n📅 Uscita: {release_date}"
                f"\n📝 {truncated_overview}\n"
            )

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
            dispatcher.utter_message(text="_Non ho capito il genere che cerchi. Puoi ripetere?_")
            return []

        genre_id = MOVIES_GENRE_MAP.get(genere.lower())
        if not genre_id:
            dispatcher.utter_message(text=f"_Non conosco il genere *{genere}*, prova con un altro._")
            return []

        data = get_movies_by_genre(genre_id)
        results = data.get("results", [])

        if not results:
            dispatcher.utter_message(text=f"_Non ho trovato film del genere *{genere}*._")
            return []

        messaggio = f"🎬 *Ecco alcuni film del genere {genere}:*\n"
        for movie in results[:5]:
            title = movie.get("title", "Titolo non disponibile")
            overview = movie.get("overview", "Trama non disponibile")

            truncated_overview = overview[:300] + "..." if len(overview) > 300 else overview

            messaggio += (
                f"\n• *{title}*\n"
                f"📝 {truncated_overview}\n"
            )

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

        # Placeholder: qui potresti chiamare TMDb per i provider di streaming.
        # Per ora mettiamo un messaggio statico.
        dispatcher.utter_message(text="📺 Questo film è disponibile su *Netflix*")
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
            dispatcher.utter_message(text="_Non ho capito il titolo del film, puoi ripetere?_")
            return []

        if not api_key:
            dispatcher.utter_message(text="_Manca la chiave API. Non posso recuperare le recensioni._")
            return []

        search_data = search_movie_by_title(titolo)
        results = search_data.get("results", [])
        if not results:
            dispatcher.utter_message(text=f"_Non ho trovato alcun film con il titolo *{titolo}*._")
            return []

        movie = results[0]
        movie_id = movie.get("id")

        if not movie_id:
            dispatcher.utter_message(text="_Non sono riuscito a recuperare l'ID del film._")
            return []

        reviews_data = get_movie_reviews(movie_id)
        reviews = reviews_data.get("results", [])

        if reviews:
            # Titolo del messaggio
            dispatcher.utter_message(text=f"🎬 *Recensioni per {movie.get('title', 'il film')}*:")

            # Mostriamo fino a 5 recensioni
            for review in reviews[:5]:
                author = review.get("author", "Autore sconosciuto")
                content = review.get("content", "Recensione non disponibile")
                truncated_content = content[:500].strip()

                # Aggiungere i puntini di sospensione se la recensione è stata troncata
                if len(content) > 500:
                    truncated_content += "..."

                message = (
                    f"\n👤 *Autore:* {author}\n"
                    f"📝 *Recensione:*\n{truncated_content}\n"
                )
                dispatcher.utter_message(text=message)
        else:
            dispatcher.utter_message(text="_Non sono disponibili recensioni per questo film._")

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

        from tmdb_utils import make_tmdb_request
        popular_data = make_tmdb_request("/movie/popular", {"language": "it-IT"})
        movies = popular_data.get("results", [])

        if not movies:
            dispatcher.utter_message(text="_Non ho trovato film popolari al momento._")
            return []

        response = "🎬 *Ecco i film più popolari:*\n"
        for idx, movie in enumerate(movies[:5], start=1):
            title = movie.get("title", "Titolo non disponibile")
            release_date = movie.get("release_date", "Data di uscita non disponibile")
            response += f"\n{idx}. *{title}*\n📅 Uscita: {release_date}\n"

        dispatcher.utter_message(text=response)

        return []
