import requests
from typing import Optional, Dict
from .constants import api_key, base_url

def make_tmdb_request(endpoint: str, params: Optional[Dict] = None) -> dict:
    """
    Funzione per effettuare una richiesta all'API di TMDB.

    :param endpoint: L'endpoint dell'API a cui fare la richiesta
    :param params: I parametri da passare alla richiesta
    :return: Il dizionario con i dati della risposta
    """
    if params is None:
        params = {}
    params["api_key"] = api_key
    if "language" not in params:
        params["language"] = "it-IT"
    url = f"{base_url}{endpoint}"
    r = requests.get(url, params=params)
    if r.status_code == 200:
        return r.json()
    else:
        return {}

def search_movie_by_title(title: str) -> dict:
    """
    Funzione per cercare un film per titolo.

    :param title: Il titolo del film da cercare
    :return: Il dizionario con i dati del film cercato
    """
    data = make_tmdb_request("/search/movie", {"query": title})
    return data

def get_movie_details(movie_id: int) -> dict:
    """
    Funzione per ottenere i dettagli di un film.

    :param movie_id: L'ID del film di cui ottenere i dettagli
    :return: Il dizionario con i dettagli del film
    """
    data = make_tmdb_request(f"/movie/{movie_id}")
    return data

def get_now_playing_movies() -> dict:
    """
    Funzione per ottenere i film attualmente in programmazione.

    :return: Il dizionario con i dati dei film attualmente in programmazione
    """
    data = make_tmdb_request("/movie/now_playing")
    return data

def get_movies_by_genre(genre_id: int) -> dict:
    """
    Funzione per ottenere i film di un determinato genere.

    :param genre_id: L'ID del genere di cui ottenere i film
    :return: Il dizionario con i dati dei film del genere specificato
    """
    data = make_tmdb_request("/discover/movie", {"with_genres": genre_id})
    return data

def get_movie_reviews(movie_id: int) -> dict:
    """
    Funzione per ottenere le recensioni di un film.

    :param movie_id: L'ID del film di cui ottenere le recensioni
    :return: Il dizionario con i dati delle recensioni del film
    """
    data = make_tmdb_request(f"/movie/{movie_id}/reviews", {"page": 1})
    return data

def get_favourite() -> dict:
    """
    Funzione per ottenere i dettagli dei film preferiti.

    :param nessuno
    :return: Il dizionario con i dettagli dei film preferiti
    """
    data = make_tmdb_request(f"/movie/popular")
    return data

def get_TV_details(series_id: int) -> dict:
    """
    Funzione per ottenere i dettagli di un film.

    :param series_id: L'ID della serie di cui ottenere i dettagli
    :return: Il dizionario con i dettagli del film
    """
    data = make_tmdb_request(f"/tv/{series_id}")
    return data



def search_TV_by_title(title: str) -> dict:
    """
    Funzione per cercare un film per titolo.

    :param title: Il titolo del film da cercare
    :return: Il dizionario con i dati del film cercato
    """
    data = make_tmdb_request("/search/tv", {"query": title})
    return data

def search_TV_latest() -> dict:
    """
    Funzione per cercare le ultime serie tv aggiungte.

    :param nessuno
    :return: Il dizionario con i dati delle ultime serie tv aggiunte
    """
    data = make_tmdb_request("/tv/on_the_air")
    return data

def get_series_reviews(series_id: int) -> dict:
    """
    Funzione per ottenere le recensioni di un film.

    :param movie_id: L'ID del film di cui ottenere le recensioni
    :return: Il dizionario con i dati delle recensioni del film
    """
    data = make_tmdb_request(f"/tv/{series_id}/reviews", {"page": 1})
    return data
