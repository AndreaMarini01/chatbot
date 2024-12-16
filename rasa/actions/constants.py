import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TMDB_API_KEY")
base_url = "https://api.themoviedb.org/3"

MOVIES_GENRE_MAP = {
    "azione": 28,
    "avventura": 12,
    "animazione": 16,
    "animato": 16,
    "commedia": 35,
    "comico": 35,
    "crime": 80,
    "documentario": 99,
    "dramma": 18,
    "drammatico": 18,
    "famiglia": 10751,
    "per famiglie": 10751,
    "fantasy": 14,
    "storia": 36,
    "storico": 36,
    "horror": 27,
    "musica": 10402,
    "musical": 10402,
    "mistero": 9648,
    "romantico": 10749,
    "romance": 10749,
    "fantascienza": 878,
    "sci-fi": 878,
    "fantascientifico": 878,
    "thriller": 53,
    "guerra": 10752,
    "western": 37
}

TV_GENRE_MAP = {
    "azione": 10759,
    "avventura": 10759,
    "azione e avventura": 10759,
    "animazione": 16,
    "animata": 16,
    "commedia": 35,
    "comica": 35,
    "crime": 80,
    "documentario": 99,
    "dramma": 18,
    "famiglia": 10751,
    "per famiglie": 10751,
    "bambini": 10762,
    "per bambini": 10762,
    "mistero": 9648,
    "notizie": 10763,
    "reality": 10764,
    "fantascienza": 10765,
    "sci-fi": 10765,
    "fantascientifica": 10765,
    "fantasy": 10765,
    "soap": 10766,
    "soap opera": 10766,
    "talk": 10767,
    "guerra": 10768,
    "politica": 10768,
    "western": 37
}
