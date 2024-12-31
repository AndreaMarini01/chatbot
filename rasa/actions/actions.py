from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FormValidation, EventType, ActiveLoop
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
            dispatcher.utter_message(text=f"Non ho trovato nessun film con questo titolo: {title}.")
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

        # Formattiamo la trama con una lunghezza ragionevole (se è troppo lunga)
        truncated_overview = overview[:500] + "..." if len(overview) > 500 else overview

        message = (
            f"🎬 {movie_title}\n\n"
            f"📅 Data di uscita: {release_date}\n\n"
            f"📝 Trama:\n{truncated_overview}"
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
            dispatcher.utter_message(text="Non ho trovato film recentemente usciti.")
            return []

        # Titolo del messaggio
        messaggio = "🎬 Film recentemente in sala:\n"
        for movie in results[:5]:
            title = movie.get("title", "Titolo non disponibile")
            release_date = movie.get("release_date", "Data non disponibile")
            overview = movie.get("overview", "Trama non disponibile")

            # Truncare l'overview se troppo lunga
            truncated_overview = overview[:300] + "..." if len(overview) > 300 else overview

            messaggio += (
                f"\n• {title}"
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
            dispatcher.utter_message(text="Non ho capito il genere che cerchi. Puoi ripetere?")
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

        messaggio = f"🎬 Ecco alcuni film del genere {genere}:\n"
        for movie in results[:5]:
            title = movie.get("title", "Titolo non disponibile")
            overview = movie.get("overview", "Trama non disponibile")

            truncated_overview = overview[:300] + "..." if len(overview) > 300 else overview

            messaggio += (
                f"\n• {title}\n"
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
            dispatcher.utter_message(text="Non ho capito il titolo del film, puoi ripetere?")
            return []

        if not api_key:
            dispatcher.utter_message(text="Manca la chiave API. Non posso recuperare i dettagli del film.")
            return []

        search_data = search_movie_by_title(title)

        results = search_data.get("results", [])
        if not results:
            dispatcher.utter_message(text=f"Non ho trovato nessun film con questo titolo: {title}.")
            return []

        movie = results[0]
        movie_id = movie.get("id")

        if not movie_id:
            dispatcher.utter_message(text="Non sono riuscito a recuperare l'ID del film.")
            return []

        providers_data = get_movie_watch_providers(movie_id)
        providers = providers_data.get("results", {}).get("IT", dict())

        if not providers:
            dispatcher.utter_message(text="Non ho trovato informazioni sui provider per questo film.")
            return []

        flatrate_providers = providers.get("flatrate", [])
        rent_providers = providers.get("rent", [])
        buy_providers = providers.get("buy", [])

        if not flatrate_providers and not rent_providers and not buy_providers:
            dispatcher.utter_message(text="Non ho trovato informazioni sui provider per questo film.")
            return []

        messaggio = f"🎬 🇮🇹 Dove guardare {movie.get('title', 'il film')}:\n"

        if flatrate_providers:
            messaggio += "\n📺 Incluso in abbonamento:"
            for provider in flatrate_providers:
                provider_name = provider.get("provider_name", "Provider sconosciuto")
                messaggio += f"\n• {provider_name}"

        if rent_providers:
            messaggio += "\n\n📺 In noleggio:"
            for provider in rent_providers:
                provider_name = provider.get("provider_name", "Provider sconosciuto")
                messaggio += f"\n• {provider_name}"

        if buy_providers:
            messaggio += "\n\n📺 In vendita:"
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
            dispatcher.utter_message(text="Non ho capito il titolo del film, puoi ripetere?")
            return []

        if not api_key:
            dispatcher.utter_message(text="Manca la chiave API. Non posso recuperare le recensioni.")
            return []

        search_data = search_movie_by_title(titolo)
        results = search_data.get("results", [])
        if not results:
            dispatcher.utter_message(text=f"Non ho trovato alcun film con il titolo {titolo}.")
            return []

        movie = results[0]
        movie_id = movie.get("id")

        if not movie_id:
            dispatcher.utter_message(text="Non sono riuscito a recuperare l'ID del film.")
            return []

        reviews_data = get_movie_reviews(movie_id)
        reviews = reviews_data.get("results", [])

        if reviews:
            # Titolo del messaggio
            dispatcher.utter_message(text=f"🎬 Recensioni per {movie.get('title', 'il film')}:")

            # Mostriamo fino a 5 recensioni
            for review in reviews[:5]:
                author = review.get("author", "Autore sconosciuto")
                content = review.get("content", "Recensione non disponibile")
                truncated_content = content[:600].strip()

                # Aggiungere i puntini di sospensione se la recensione è stata troncata
                if len(content) > 600:
                    truncated_content += "..."

                message = (
                    f"\n👤 Autore: {author}\n"
                    f"📝 Recensione:\n{truncated_content}\n"
                )
                dispatcher.utter_message(text=message)
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


        popular_data = get_favourite()
        movies = popular_data.get("results", [])
        print(movies)

        if not movies:
            dispatcher.utter_message(text="Non ho trovato film popolari al momento.")
            return []

        response = "🎬 Ecco i film più popolari:\n"
        for idx, movie in enumerate(movies[:5], start=1):
            title = movie.get("title", "Titolo non disponibile")
            release_date = movie.get("release_date", "Data di uscita non disponibile")
            response += f"\n{idx}. {title}\n📅 Uscita: {release_date}\n"

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
            dispatcher.utter_message(text="Non ho capito il titolo della serie tv, puoi ripetere?")
            return []

        if not api_key:
            dispatcher.utter_message(text="Manca la chiave API. Non posso recuperare i dettagli del film.")
            return []

        search_data = search_TV_by_title(title)

        results = search_data.get("results", [])
        if not results:
            dispatcher.utter_message(text=f"Non ho trovato nessuna serie TV con questo titolo: {title}.")
            return []

        serie_tv = results[0]
        series_id = serie_tv.get("id")

        if not series_id:
            dispatcher.utter_message(text="Non sono riuscito a recuperare l'ID della SerieTV.")
            return []

        details_data = get_TV_details(series_id)
        serie_tv_title = details_data.get("name", "Titolo non disponibile")
        overview = details_data.get("overview", "Nessuna trama disponibile")
        release_date = details_data.get("first_air_date", "Data di uscita non disponibile")
        # Formattiamo la trama con una lunghezza ragionevole (se è troppo lunga)
        truncated_overview = overview[:500] + "..." if len(overview) > 500 else overview

        message = (
            f"🎬 {serie_tv_title}\n\n"
            f"📅 Data di uscita: {release_date}\n\n"
            f"📝 Trama:\n{truncated_overview}"
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
            dispatcher.utter_message(text="Non ho nessuna serie tv uscita di  recentemente")
            return []

        # Titolo del messaggio
        messaggio = "🎬 Serie tv recenten"
        for serie in results[:5]:
            title = serie.get("name", "Titolo non disponibile")
            release_date = serie.get("first_air_date", "Data non disponibile")
            overview = serie.get("overview", "Trama non disponibile")

            # Truncare l'overview se troppo lunga
            truncated_overview = overview[:300] + "..." if len(overview) > 300 else overview

            messaggio += (
                f"\n• {title}"
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
            dispatcher.utter_message(text="Non ho trovato serie tv popolari al momento.")
            return []

        response = "🎬 Ecco le serie tv più popolari:\n"
        for idx, movie in enumerate(series[:5], start=1):
            title = movie.get("name", "Titolo non disponibile")
            release_date = movie.get("first_air_date", "Data di uscita non disponibile")
            response += f"\n{idx}. {title}\n📅 Uscita: {release_date}\n"

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
            dispatcher.utter_message(text="Non ho capito il genere che cerchi. Puoi ripetere?")
            return []

        genre_id = TV_GENRE_MAP.get(genere.lower())
        if not genre_id:
            dispatcher.utter_message(text=f"Non conosco il genere{genere}, prova con un altro.")
            return []

        data = get_tv_by_genre(genre_id)
        results = data.get("results", [])

        if not results:
            dispatcher.utter_message(text=f"Non ho trovato serie del genere {genere}.")
            return []

        messaggio = f"🎬 Ecco alcune serie  del genere {genere}:\n"
        for movie in results[:5]:
            title = movie.get("name", "Titolo non disponibile")
            overview = movie.get("first_air_date", "Trama non disponibile")

            truncated_overview = overview[:300] + "..." if len(overview) > 300 else overview

            messaggio += (
                f"\n• {title}\n"
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
            dispatcher.utter_message(text="Non ho capito il titolo della serie tv, puoi ripetere?")
            return []
        
        if not api_key:
            dispatcher.utter_message(text="Manca la chiave API. Non posso recuperare le recensioni.")
            return []
        
        search_data = search_TV_by_title(titolo)
        results = search_data.get("results", [])
        if not results:
            dispatcher.utter_message(text=f"Non ho trovato alcuna serie tv con il titolo {titolo}.")
            return []
        
        serie_tv = results[0]
        series_id = serie_tv.get("id")

        if not series_id:
            dispatcher.utter_message(text="Non sono riuscito a recuperare l'ID della serie tv.")
            return []
        
        reviews_data = get_series_reviews(series_id)
        reviews = reviews_data.get("results", [])

        if reviews:
            # Titolo del messaggio
            dispatcher.utter_message(text=f"🎬 Recensioni per {serie_tv.get('name', 'la serie tv')}:")

            # Mostriamo fino a 5 recensioni
            for review in reviews[:5]:
                author = review.get("author", "Autore sconosciuto")
                content = review.get("content", "Recensione non disponibile")
                truncated_content = content[:600].strip()

                # Aggiungere i puntini di sospensione se la recensione è stata troncata
                if len(content) > 600:
                    truncated_content += "..."

                message = (
                    f"\n👤 Autore: {author}\n"
                    f"📝 Recensione:\n{truncated_content}\n"
                )
                dispatcher.utter_message(text=message)
        else:   
            dispatcher.utter_message(text="Non sono disponibili recensioni per questa serie tv.")

        return []


class ValidateFormFilm(FormValidationAction):
    def name(self) -> Text:
        return "validate_form_film"

    def validate_titolo_film_form(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        last_intent = tracker.latest_message.get("intent", {}).get("name")

        # 1) Se Rasa non capisce o l’utente dice qualcosa di nonsense:
        if last_intent in ["out_of_scope", "nlu_fallback"]:
            dispatcher.utter_message(
                text="Non ho capito il titolo del film. Per favore riscrivi correttamente il titolo.")
            return {"titolo_film_form": None}

        # 2) Se lo slot è vuoto o composto da soli spazi:
        if not slot_value or len(slot_value.strip()) == 0:
            dispatcher.utter_message(text="Non ho capito il titolo del film, puoi ripetere?")
            return {"titolo_film_form": None}

        # 3) Altrimenti accettiamo il titolo
        return {"titolo_film_form": slot_value}

    def validate_anno_form(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        last_intent = tracker.latest_message.get("intent", {}).get("name")

        # Se siamo in fallback/out_of_scope, restiamo nel form e chiediamo di ripetere:
        if last_intent in ["out_of_scope", "nlu_fallback"]:
            dispatcher.utter_message(text="Non ho capito se vuoi l'anno o no. Rispondi 'sì' oppure 'no'.")
            return {"anno_form": None}

        if last_intent == "affirm":
            return {"anno_form": "Sì"}

        if last_intent == "deny":
            dispatcher.utter_message(text="Ok, niente anno.")
            return {"anno_form": "NO"}

        # Se qui arrivi, vuol dire che l’utente non ha detto né 'sì' né 'no',
        # e non è un fallback out_of_scope, ma comunque non abbiamo un valore utile
        if not slot_value:
            dispatcher.utter_message(text="Devi specificare se vuoi l'anno. Scrivi 'sì' se lo vuoi, 'no' se non lo vuoi.")
            return {"anno_form": None}

        # Se per qualche ragione slot_value esiste, lo teniamo
        return {"anno_form": slot_value}

    def validate_genere_form(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        last_intent = tracker.latest_message.get("intent", {}).get("name")

        if last_intent in ["out_of_scope", "nlu_fallback"]:
            dispatcher.utter_message(text="Non ho capito se vuoi il genere. Rispondi 'sì' oppure 'no'.")
            return {"genere_form": None}

        if last_intent == "affirm":
            return {"genere_form": "Sì"}

        if last_intent == "deny":
            dispatcher.utter_message(text="Ok, niente genere.")
            return {"genere_form": "NO"}

        if not slot_value:
            dispatcher.utter_message(
                text="Devi specificare se vuoi il genere. Scrivi 'sì' se lo vuoi, 'no' se non lo vuoi.")
            return {"genere_form": None}

        return {"genere_form": slot_value}


class ActionProvideFilmDetails(Action):
    def name(self) -> Text:
        return "action_provide_film_details"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
    ) -> List[EventType]:

        titolo = tracker.get_slot("titolo_film_form")
        anno_choice = tracker.get_slot("anno_form")  # può essere "Sì", None, o un numero se in futuro l'utente inserisce un anno
        genere_coiche = tracker.get_slot("genere_form")

        # Per esempio:
        search_data = search_movie_by_title(titolo)

        results = search_data.get("results", [])
        if not results:
            dispatcher.utter_message(text=f"_Non ho trovato nessun film con questo titolo: {titolo}.")
            return []

        movie = results[0]
        movie_id = movie.get("id")

        if not movie_id:
            dispatcher.utter_message(text="Non sono riuscito a recuperare l'ID del film.")
            return []

        details_data = get_movie_details(movie_id)

        trama = details_data.get("overview", "Nessuna trama trovata.")
        anno_uscita = details_data.get("release_date", "sconosciuto")
        genere = details_data.get("genres", "sconosciuto")

        # genere è una lista di dizionari, quindi per ottenere il nome del genere, possiamo usare una list comprehension
        genere = ", ".join([g["name"] for g in genere])

        # Creazione del messaggio con formattazione professionale
        if anno_choice == "Sì" and genere_coiche == "Sì":
            # L'utente vuole l'anno e il genere
            dispatcher.utter_message(
                text=f"🎬 Dettagli del film: {titolo}\n\n"
                     f"📝 Trama: {trama}\n"
                     f"📅 Anno di uscita: {anno_uscita}\n"
                     f"🎭 Genere: {genere}"
            )
        elif anno_choice == "Sì" and genere_coiche == "NO":
            # L'utente vuole solo l'anno
            dispatcher.utter_message(
                text=f"🎬 Dettagli del film: {titolo}\n\n"
                     f"📝 Trama: {trama}\n"
                     f"📅 Anno di uscita: {anno_uscita}"
            )
        elif anno_choice == "NO" and genere_coiche == "Sì":
            # L'utente vuole solo il genere
            dispatcher.utter_message(
                text=f"🎬 Dettagli del film: {titolo}\n\n"
                     f"📝 Trama: {trama}\n"
                     f"🎭 Genere: {genere}"
            )
        else:
            # L'utente non vuole né l'anno né il genere
            dispatcher.utter_message(
                text=f"🎬 Dettagli del film: {titolo}\n\n"
                     f"📝 Trama: {trama}"
            )

        return []


class ActionResetSlots(Action):
    def name(self) -> str:
        return "action_reset_slots"

    def run(self, dispatcher, tracker, domain):
        # Slot da resettare
        slots_to_reset = [
            "titolo_film",
            "titolo_film_form",
            "titolo_serieTV",
            "genere",
            "genere_form",
            "attore",
            "anno",
            "anno_form",
            "context_ricerca",
            "tipo_contenuto",
            "titolo_film_image_form",
            "anno_image_form",
        ]

        return [SlotSet(slot, None) for slot in slots_to_reset]


class ActionGetImageFilm(Action):
    def name(self) -> Text:
        return "action_provide_film_image"
    
    async def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
    ) -> List[EventType]:
        
        titolo = tracker.get_slot("titolo_film_image_form")
        anno = tracker.get_slot("anno_image_form")
        
        # Se il titolo non è stato fornito
        if not titolo:
            dispatcher.utter_message(text="Per favore, fornisci il titolo di un film.")
            return []
        
        # Effettua la ricerca del film
        search_data = search_movie_by_title(titolo)
        results = search_data.get("results", [])
        
        if not results:
            dispatcher.utter_message(text=f"_Non ho trovato nessun film con il titolo *{titolo}*._")
            return []
        
        # Ottieni il primo risultato
        movie = results[0]
        poster_path = movie.get("poster_path")
        
        # Se l'anno è stato richiesto, invialo insieme all'immagine
        if anno:
            release_year = movie.get("release_date", "").split("-")[0]  # Estrai l'anno
            dispatcher.utter_message(text=f"Il film *{titolo}* è uscito nel {release_year}.")
        
        if poster_path:
            # Costruisci l'URL completo per l'immagine
            image_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            # Invia l'immagine tramite Telegram
            dispatcher.utter_message(image=image_url)
            return []
        else:
            dispatcher.utter_message(text="Non ho trovato l'immagine del film.")
            return []
class ValidateFormLocandina(FormValidationAction):
    def name(self) -> str:
        return "validate_form_locandina"

    def validate_titolo_film_image_form(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        last_intent = tracker.latest_message.get("intent", {}).get("name")

        # Se Rasa non capisce o l’utente dice qualcosa di nonsense (fallback/out_of_scope):
        if last_intent in ["out_of_scope", "nlu_fallback"]:
            dispatcher.utter_message(
                text="Non ho capito il titolo del film. Per favore riscrivi correttamente il titolo."
            )
            return {"titolo_film_image_form": None}

        # Se lo slot è vuoto o composto da soli spazi:
        if not slot_value or len(slot_value.strip()) == 0:
            dispatcher.utter_message(
                text="Non ho capito il titolo del film, puoi ripetere?"
            )
            return {"titolo_film_image_form": None}

        # Se il valore sembra valido, lo accettiamo:
        return {"titolo_film_image_form": slot_value}

    def validate_anno_image_form(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        last_intent = tracker.latest_message.get("intent", {}).get("name")

        # Se siamo in fallback/out_of_scope, restiamo nel form e chiediamo di ripetere:
        if last_intent in ["out_of_scope", "nlu_fallback"]:
            dispatcher.utter_message(text="Non ho capito se vuoi l'anno o no. Rispondi 'sì' oppure 'no'.")
            return {"anno_image_form": None}

        # Se l'utente risponde "sì", accettiamo l'anno:
        if last_intent == "affirm":
            return {"anno_image_form": "Sì"}

        # Se l'utente risponde "no", non accettiamo l'anno:
        if last_intent == "deny":
            dispatcher.utter_message(text="Ok, niente anno.")
            return {"anno_image_form": "NO"}

        # Se lo slot è vuoto o l'utente non ha fornito una risposta chiara:
        if not slot_value:
            dispatcher.utter_message(text="Devi specificare se vuoi l'anno. Scrivi 'sì' se lo vuoi, 'no' se non lo vuoi.")
            return {"anno_image_form": None}

        # Se per qualche motivo il valore esiste, lo accettiamo:
        return {"anno_image_form": slot_value}
