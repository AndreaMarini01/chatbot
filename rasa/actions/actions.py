from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FormValidation, EventType
from rasa_sdk.types import DomainDict

from .constants import MOVIES_GENRE_MAP, api_key, TV_GENRE_MAP
from .tmdb_utils import (
    search_movie_by_title,
    get_movie_details,
    get_now_playing_movies,
    get_movies_by_genre,
    get_movie_reviews,
    get_movie_watch_providers,
    get_TV_details,
    get_series_reviews,
    search_TV_by_title,
    get_favourite,
    search_TV_latest, get_favourite_tv, get_tv_by_genre
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


class ActionMoviesByGenre(Action):
    """
    Azione per ottenere film di un certo genere.
    """

    def name(self) -> Text:
        return "movies_by_genre"

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
    Azione per indicare dove guardare un film.
    """

    def name(self) -> Text:
        return "action_where_to_watch"

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

        providers_data = get_movie_watch_providers(movie_id)
        providers = providers_data.get("results", {}).get("IT", dict())

        if not providers:
            dispatcher.utter_message(text="_Non ho trovato informazioni sui provider per questo film._")
            return []

        flatrate_providers = providers.get("flatrate", [])
        rent_providers = providers.get("rent", [])
        buy_providers = providers.get("buy", [])

        if not flatrate_providers and not rent_providers and not buy_providers:
            dispatcher.utter_message(text="_Non ho trovato informazioni sui provider per questo film._")
            return []

        messaggio = f"🎬 *🇮🇹 Dove guardare {movie.get('title', 'il film')}*:\n"

        if flatrate_providers:
            messaggio += "\n📺 *Incluso in abbonamento:*"
            for provider in flatrate_providers:
                provider_name = provider.get("provider_name", "Provider sconosciuto")
                messaggio += f"\n• {provider_name}"

        if rent_providers:
            messaggio += "\n\n📺 *In noleggio:*"
            for provider in rent_providers:
                provider_name = provider.get("provider_name", "Provider sconosciuto")
                messaggio += f"\n• {provider_name}"

        if buy_providers:
            messaggio += "\n\n📺 *In vendita:*"
            for provider in buy_providers:
                provider_name = provider.get("provider_name", "Provider sconosciuto")
                messaggio += f"\n• {provider_name}"

        dispatcher.utter_message(text=messaggio)


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
                truncated_content = content[:600].strip()

                # Aggiungere i puntini di sospensione se la recensione è stata troncata
                if len(content) > 600:
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


        popular_data = get_favourite()
        movies = popular_data.get("results", [])
        print(movies)

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


"""
action for series TV
"""

class ActionTvDetails(Action):
    """
    Azione per recuperare i dettagli di una serieTV dato il titolo.
    """

    def name(self) -> Text:
        return "action_TV_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        title = tracker.get_slot("titolo_serieTV")

        if not title:
            dispatcher.utter_message(text="_Non ho capito il titolo della serie tv, puoi ripetere?_")
            return []

        if not api_key:
            dispatcher.utter_message(text="_Manca la chiave API. Non posso recuperare i dettagli del film._")
            return []

        search_data = search_TV_by_title(title)

        results = search_data.get("results", [])
        if not results:
            dispatcher.utter_message(text=f"_Non ho trovato nessuna serie TV con questo titolo: *{title}*._")
            return []

        serie_tv = results[0]
        series_id = serie_tv.get("id")

        if not series_id:
            dispatcher.utter_message(text="_Non sono riuscito a recuperare l'ID della SerieTV._")
            return []

        details_data = get_TV_details(series_id)
        serie_tv_title = details_data.get("name", "Titolo non disponibile")
        overview = details_data.get("overview", "Nessuna trama disponibile")
        release_date = details_data.get("first_air_date", "Data di uscita non disponibile")
        # Formattiamo la trama con una lunghezza ragionevole (se è troppo lunga)
        truncated_overview = overview[:500] + "..." if len(overview) > 500 else overview

        message = (
            f"🎬 *{serie_tv_title}*\n\n"
            f"📅 _Data di uscita:_ {release_date}\n\n"
            f"📝 *Trama:*\n{truncated_overview}"
        )

        dispatcher.utter_message(text=message)
        return []


class ActionTVRecentReleases(Action):
    """
    Azione per ottenere le serie tv appena uscite.
    """
    def name(self) -> Text:
        return "action_recent_releases_TV"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        data = search_TV_latest()
        results = data.get("results", [])

        if not results:
            dispatcher.utter_message(text="_Non ho nessuna serie tv uscita di  recentemente")
            return []

        # Titolo del messaggio
        messaggio = "🎬 *Serie tv recente*\n"
        for serie in results[:5]:
            title = serie.get("name", "Titolo non disponibile")
            release_date = serie.get("first_air_date", "Data non disponibile")
            overview = serie.get("overview", "Trama non disponibile")

            # Truncare l'overview se troppo lunga
            truncated_overview = overview[:300] + "..." if len(overview) > 300 else overview

            messaggio += (
                f"\n• *{title}*"
                f"\n📅 Uscita: {release_date}"
                f"\n📝 {truncated_overview}\n"
            )

        dispatcher.utter_message(text=messaggio)
        return []


class ActionPopularTv(Action):
    """
    Azione per ottenere le serie tv più popolari.
    """

    def name(self) -> Text:
        return "popular_TV"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:


        popular_data = get_favourite_tv()
        series = popular_data.get("results", [])

        if not series:
            dispatcher.utter_message(text="_Non ho trovato serie tv popolari al momento._")
            return []

        response = "🎬 *Ecco le serie tv più popolari:*\n"
        for idx, movie in enumerate(series[:5], start=1):
            title = movie.get("name", "Titolo non disponibile")
            release_date = movie.get("first_air_date", "Data di uscita non disponibile")
            response += f"\n{idx}. *{title}*\n📅 Uscita: {release_date}\n"

        dispatcher.utter_message(text=response)

        return []

class ActionTvByGenre(Action):
    """
    Azione per ottenere le serie tv di un certo genere.
    """

    def name(self) -> Text:
        return "TV_by_genre"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        genere = tracker.get_slot("genere")
        if not genere:
            dispatcher.utter_message(text="_Non ho capito il genere che cerchi. Puoi ripetere?_")
            return []

        genre_id = TV_GENRE_MAP.get(genere.lower())
        if not genre_id:
            dispatcher.utter_message(text=f"_Non conosco il genere *{genere}*, prova con un altro._")
            return []

        data = get_tv_by_genre(genre_id)
        results = data.get("results", [])

        if not results:
            dispatcher.utter_message(text=f"_Non ho trovato serie del genere *{genere}*._")
            return []

        messaggio = f"🎬 *Ecco alcune serie  del genere {genere}:*\n"
        for movie in results[:5]:
            title = movie.get("name", "Titolo non disponibile")
            overview = movie.get("first_air_date", "Trama non disponibile")

            truncated_overview = overview[:300] + "..." if len(overview) > 300 else overview

            messaggio += (
                f"\n• *{title}*\n"
                f"📝 {truncated_overview}\n"
            )

        dispatcher.utter_message(text=messaggio)
        return []

# actions.py
class ActionSetContextTitle(Action):
    def name(self) -> Text:
        return "action_set_context_title"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [SlotSet("context_ricerca", "title")]


class ActionAskMovieOrSeries(Action):
    def name(self) -> Text:
        return "action_ask_movie_or_series"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_chiedi_film_o_serie")
        return []
    
class ActionAskRewiewsSeries(Action):
    def name(self) -> Text:
        return "TV_reviews"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        titolo = tracker.get_slot("titolo_serieTV")

        if not titolo:
            dispatcher.utter_message(text="_Non ho capito il titolo della serie tv, puoi ripetere?_")
            return []
        
        if not api_key:
            dispatcher.utter_message(text="_Manca la chiave API. Non posso recuperare le recensioni._")
            return []
        
        search_data = search_TV_by_title(titolo)
        results = search_data.get("results", [])
        if not results:
            dispatcher.utter_message(text=f"_Non ho trovato alcuna serie tv con il titolo *{titolo}*._")
            return []
        
        serie_tv = results[0]
        series_id = serie_tv.get("id")

        if not series_id:
            dispatcher.utter_message(text="_Non sono riuscito a recuperare l'ID della serie tv._")
            return []
        
        reviews_data = get_series_reviews(series_id)
        reviews = reviews_data.get("results", [])

        if reviews:
            # Titolo del messaggio
            dispatcher.utter_message(text=f"🎬 *Recensioni per {serie_tv.get('name', 'la serie tv')}*:")

            # Mostriamo fino a 5 recensioni
            for review in reviews[:5]:
                author = review.get("author", "Autore sconosciuto")
                content = review.get("content", "Recensione non disponibile")
                truncated_content = content[:600].strip()

                # Aggiungere i puntini di sospensione se la recensione è stata troncata
                if len(content) > 600:
                    truncated_content += "..."

                message = (
                    f"\n👤 *Autore:* {author}\n"
                    f"📝 *Recensione:*\n{truncated_content}\n"
                )
                dispatcher.utter_message(text=message)
        else:   
            dispatcher.utter_message(text="_Non sono disponibili recensioni per questa serie tv._")

        return []

class ValidateFormFilm(FormValidationAction):
    def name(self) -> Text:
        return "validate_form_film"

    def validate_titolo_film(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        if not slot_value:
            dispatcher.utter_message(text="Non ho capito il titolo del film, puoi ripetere?")
            return {"titolo_film": None}
        return {"titolo_film": slot_value}

    def validate_anno(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        # Controlla l’intent dell’ultimo messaggio
        last_intent = tracker.latest_message.get("intent", {}).get("name")
        dispatcher.utter_message(text=f"[DEBUG] L'intent è: {last_intent}. Slot_value: {slot_value}")

        if last_intent == "affirm":
            dispatcher.utter_message(text="Ok, mostrerò anche l'anno di uscita.")
            return {"anno": "Sì"}

        if last_intent == "deny":
            dispatcher.utter_message(text="Ok, niente anno.")
            return {"anno": None}

        # Se qui arrivi, vuol dire che l'utente non ha detto né 'sì' né 'no'
        if not slot_value:
            dispatcher.utter_message(text="Non ho capito se vuoi sapere l'anno, puoi ripetere?")
            return {"anno": None}

        return {"anno": slot_value}

    def validate_genere_form(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        # Controlla l’intent dell’ultimo messaggio
        last_intent = tracker.latest_message.get("intent", {}).get("name")
        dispatcher.utter_message(text=f"[DEBUG] L'intent è: {last_intent}. Slot_value: {slot_value}")

        if last_intent == "affirm":
            dispatcher.utter_message(text="Ok, mostrerò anche il genere.")
            return {"genere": "Sì"}

        if last_intent == "deny":
            dispatcher.utter_message(text="Ok, niente genere.")
            return {"genere": None}

        # Se qui arrivi, vuol dire che l'utente non ha detto né 'sì' né 'no'
        if not slot_value:
            dispatcher.utter_message(text="Non ho capito se vuoi sapere l'anno, puoi ripetere?")
            return {"genere": None}

        return {"genere": slot_value}


class ActionProvideFilmDetails(Action):
    def name(self) -> Text:
        return "action_provide_film_details"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
    ) -> List[EventType]:

        titolo = tracker.get_slot("titolo_film")
        anno_choice = tracker.get_slot(
            "anno")  # può essere "Sì", None, o un numero se in futuro l'utente inserisce un anno
        genere_coiche = tracker.get_slot("genere")

        # Per esempio:
        search_data = search_movie_by_title(titolo)

        results = search_data.get("results", [])
        if not results:
            dispatcher.utter_message(text=f"_Non ho trovato nessun film con questo titolo: *{titolo}*._")
            return []

        movie = results[0]
        movie_id = movie.get("id")

        if not movie_id:
            dispatcher.utter_message(text="_Non sono riuscito a recuperare l'ID del film._")
            return []

        details_data = get_movie_details(movie_id)


        trama = details_data.get("overview", "Nessuna trama trovata.")
        anno_uscita = details_data.get("release_date", "sconosciuto")
        genere=details_data.get("genres", "sconosciuto")

        # genere è una lista di dizionari, quindi per ottenere il nome del genere, possiamo usare una list comprehension
        genere = ", ".join([g["name"] for g in genere])
        # Se anno_choice == "Sì", allora includi l'anno. Altrimenti no.
        # O, se un giorno 'anno' fosse un numero, lo gestisci qui.

        if anno_choice == "Sì" and genere_coiche == "Sì" :
            # L'utente vuole l'anno
            dispatcher.utter_message(
                text=f"Ecco i dettagli per '{titolo}':\nTrama: {trama}\nAnno di uscita: {anno_uscita} \nGenere: {genere}"
            )
        if anno_choice == "Sì" and genere_coiche == None:
            # L'utente vuole l'anno
            dispatcher.utter_message(
                text=f"Ecco i dettagli per '{titolo}':\nTrama: {trama}\nAnno di uscita: {anno_uscita}"
            )
        if anno_choice == None and genere_coiche == "Sì":
            # L'utente vuole l'anno
            dispatcher.utter_message(
                text=f"Ecco i dettagli per '{titolo}':\nTrama: {trama}\nGenere: {genere}"
            )
        else:
            # L'utente NON vuole l'anno
            dispatcher.utter_message(
                text=f"Ecco i dettagli per '{titolo}':\nTrama: {trama}"
            )

        return []