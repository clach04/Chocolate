from sqlite3 import IntegrityError
from flask import Flask, url_for, request, render_template, redirect, make_response, send_file
from markupsafe import Markup
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from tmdbv3api import TMDb, Movie, TV, Episode, Person
from tmdbv3api.exceptions import TMDbException
from videoprops import get_video_properties
from pathlib import Path
from Levenshtein import distance as lev
from fuzzywuzzy import fuzz
from ask_lib import AskResult, ask
from deep_translator import GoogleTranslator
from time import mktime
from PIL import Image
import requests, os, subprocess, configparser, socket, datetime, subprocess, socket, platform, GPUtil, json, random, time, rpc, sqlalchemy, warnings, re, zipfile

start_time = mktime(time.localtime())

with warnings.catch_warnings():
   warnings.simplefilter("ignore", category = sqlalchemy.exc.SAWarning)

app = Flask(__name__)
CORS(app)

dirPath = os.getcwd()
dirPath = os.path.dirname(__file__)
app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{dirPath}/database.db'
app.config['MAX_CONTENT_LENGTH'] = 4096 * 4096
app.config['UPLOAD_FOLDER'] = f"{dirPath}/static/img/"
app.config["SECRET_KEY"] = "ChocolateDBPassword"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
loginManager = LoginManager()
loginManager.init_app(app)
loginManager.login_view = 'login'
langs_dict = GoogleTranslator().get_supported_languages(as_dict=True)

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    profilePicture = db.Column(db.String(255))
    accountType = db.Column(db.String(255))

    def __init__(self, name, password, profilePicture, accountType):
        self.name = name
        self.password = generate_password_hash(password)
        self.profilePicture = profilePicture
        self.accountType = accountType

    def __repr__(self) -> str:
        return f'<Name {self.name}>'

    def verify_password(self, pwd):
        return check_password_hash(self.password, pwd)

class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), primary_key=True)
    realTitle = db.Column(db.String(255), primary_key=True)
    cover = db.Column(db.String(255))
    banner = db.Column(db.String(255))
    slug = db.Column(db.String(255))
    description = db.Column(db.String(2550))
    note = db.Column(db.String(255))
    date = db.Column(db.String(255))
    genre = db.Column(db.String(255))
    duration = db.Column(db.String(255))
    cast = db.Column(db.String(255))
    bandeAnnonceUrl = db.Column(db.String(255))
    adult = db.Column(db.String(255))
    libraryName=db.Column(db.String(255))

    def __init__(self, id, title, realTitle, cover, banner, slug, description, note, date, genre, duration, cast, bandeAnnonceUrl, adult, libraryName):
        self.id = id
        self.title = title
        self.realTitle = realTitle
        self.cover = cover
        self.banner = banner
        self.slug = slug
        self.description = description
        self.note = note
        self.date = date
        self.genre = genre
        self.duration = duration
        self.cast = cast
        self.bandeAnnonceUrl = bandeAnnonceUrl
        self.adult = adult
        self.libraryName = libraryName
    
    def __repr__(self) -> str:
        return f"<Movies {self.title}>"

class Series(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), primary_key=True)
    originalName = db.Column(db.String(255), primary_key=True)
    genre = db.Column(db.String(255))
    duration = db.Column(db.String(255))
    description = db.Column(db.String(2550))
    cast = db.Column(db.String(255))
    bandeAnnonceUrl = db.Column(db.String(255))
    serieCoverPath = db.Column(db.String(255))
    banniere = db.Column(db.String(255))
    note = db.Column(db.String(255))
    date = db.Column(db.String(255))
    serieModifiedTime = db.Column(db.Float)
    libraryName=db.Column(db.String(255))

    def __init__(self, id, name, originalName, genre, duration, description, cast, bandeAnnonceUrl, serieCoverPath, banniere, note, date, serieModifiedTime, libraryName):
        self.id = id
        self.name = name
        self.originalName = originalName
        self.genre = genre
        self.duration = duration
        self.description = description
        self.cast = cast
        self.bandeAnnonceUrl = bandeAnnonceUrl
        self.serieCoverPath = serieCoverPath
        self.banniere = banniere
        self.note = note
        self.date = date
        self.serieModifiedTime = serieModifiedTime
        self.libraryName = libraryName
    
    def __repr__(self) -> str:
        return f"<Series {self.name}>"


class Seasons(db.Model):
    
    serie = db.Column(db.Integer, nullable=False)
    seasonId = db.Column(db.Integer, primary_key=True)
    seasonNumber = db.Column(db.Integer, primary_key=True)
    release = db.Column(db.String(255))
    episodesNumber = db.Column(db.String(255))
    seasonName = db.Column(db.String(255))
    seasonDescription = db.Column(db.Text)
    seasonCoverPath = db.Column(db.String(255))
    modifiedDate = db.Column(db.Float)

    def __init__(self, serie, release, episodesNumber, seasonNumber, seasonId, seasonName, seasonDescription, seasonCoverPath, modifiedDate):
        self.serie = serie
        self.release = release
        self.episodesNumber = episodesNumber
        self.seasonNumber = seasonNumber
        self.seasonId = seasonId
        self.seasonName = seasonName
        self.seasonDescription = seasonDescription
        self.seasonCoverPath = seasonCoverPath
        self.modifiedDate = modifiedDate

    def __repr__(self) -> str:
        return f"<Seasons {self.serie} {self.seasonNumber}>"

class Episodes(db.Model):
    seasonId = db.Column(db.Integer, nullable=False)
    episodeId = db.Column(db.Integer, primary_key=True)
    episodeName = db.Column(db.String(255), primary_key=True)
    episodeNumber = db.Column(db.Integer, primary_key=True)
    episodeDescription = db.Column(db.Text)
    episodeCoverPath = db.Column(db.String(255))
    releaseDate = db.Column(db.String(255))
    slug = db.Column(db.String(255))
    introStart = db.Column(db.Float)
    introEnd = db.Column(db.Float)

    def __init__(self, episodeId, episodeName, seasonId, episodeNumber, episodeDescription, episodeCoverPath, releaseDate, slug, introStart, introEnd):
        self.episodeId = episodeId
        self.seasonId = seasonId
        self.episodeName = episodeName
        self.episodeNumber = episodeNumber
        self.episodeDescription = episodeDescription
        self.episodeCoverPath = episodeCoverPath
        self.releaseDate = releaseDate
        self.slug = slug
        self.introStart = introStart
        self.introEnd = introEnd

    def __repr__(self) -> str:
        return f"<Episodes {self.seasonId} {self.episodeNumber}>"

class Games(db.Model):
    console = db.Column(db.String(255), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), primary_key=True)
    realTitle = db.Column(db.String(255), primary_key=True)
    cover = db.Column(db.String(255))
    description = db.Column(db.String(2550))
    note = db.Column(db.String(255))
    date = db.Column(db.String(255))
    genre = db.Column(db.String(255))
    slug = db.Column(db.String(255))
    libraryName=db.Column(db.String(255))

    def __init__(self, console, id, title, realTitle, cover, description, note, date, genre, slug, libraryName):
        self.console = console
        self.id = id
        self.title = title
        self.realTitle = realTitle
        self.cover = cover
        self.description = description
        self.note = note
        self.date = date
        self.genre = genre
        self.slug = slug
        self.libraryName = libraryName
    
    def __repr__(self) -> str:
        return f"<Games {self.title}>"

class Language(db.Model):
    language = db.Column(db.String(255), primary_key=True)
    
    def __init__(self, language):
        self.language = language
    
    def __repr__(self) -> str:
        return f"<Language {self.language}>"

class Actors(db.Model):
    name = db.Column(db.String(255), primary_key=True)
    actorId = db.Column(db.Integer, primary_key=True)
    actorImage = db.Column(db.Text)
    actorDescription = db.Column(db.String(2550))
    actorBirthDate = db.Column(db.String(255))
    actorBirthPlace = db.Column(db.String(255))
    actorPrograms = db.Column(db.Text)

    def __init__(self, name, actorId, actorImage, actorDescription, actorBirthDate, actorBirthPlace, actorPrograms):
        self.name = name
        self.actorId = actorId
        self.actorImage = actorImage
        self.actorDescription = actorDescription
        self.actorBirthDate = actorBirthDate
        self.actorBirthPlace = actorBirthPlace
        self.actorPrograms = actorPrograms
    
    def __repr__(self) -> str:
        return f"<Actors {self.name}>"

class Libraries(db.Model):
    libName = db.Column(db.String(255), primary_key=True)
    libImage = db.Column(db.String(255))
    libType = db.Column(db.String(255))
    libFolder = db.Column(db.Text)
    availableFor = db.Column(db.Text)

    def __init__(self, libName, libImage, libType, libFolder, availableFor):
        self.libName = libName
        self.libImage = libImage
        self.libType = libType
        self.libFolder = libFolder
        self.availableFor = availableFor
    
    def __repr__(self) -> str:
        return f"<Libraries {self.name}>"


with app.app_context():
  db.create_all()
  db.init_app(app)

@loginManager.user_loader
def load_user(id):
    return Users.query.get(int(id))


config = configparser.ConfigParser()

#get the directory of the python file
dir = os.path.dirname(__file__)
config.read(os.path.join(dir, 'config.ini'))
if config["ChocolateSettings"]["language"] == "Empty":
    config["ChocolateSettings"]["language"] = "EN"

#get games path
if config["ChocolateSettings"]["gamesPath"] != "Empty":
    clientID = config.get("APIKeys", "IGDBID")
    clientSecret = config.get("APIKeys", "IGDBSECRET")
    if clientID == "Empty" or clientSecret == "Empty":
        print("Follow this tutorial to get your IGDB API Keys: https://api-docs.igdb.com/#account-creation")
        clientID = input("Please enter your IGDB Client ID: ")
        clientSecret = input("Please enter your IGDB Client Secret: ")
        config.set("APIKeys", "IGDBID", clientID)
        config.set("APIKeys", "IGDBSECRET", clientSecret)
        with open(os.path.join(dir, 'config.ini'), "w") as conf:
            config.write(conf)

tmdb = TMDb()
apiKeyTMDB = config["APIKeys"]["TMDB"]
if apiKeyTMDB == "Empty":
    print("Follow this tutorial to get your TMDB API Key : https://developers.themoviedb.org/3/getting-started/introduction")
    apiKey = input("Please enter your TMDB API Key: ")
    config["APIKeys"]["TMDB"] = apiKey
tmdb.api_key = config["APIKeys"]["TMDB"]

def searchGame(game, console):
    url = f"https://www.igdb.com/search_autocomplete_all?q={game.replace(' ', '%20')}"
    return IGDBRequest(url,console)

def IGDBRequest(url, console):
    customHeaders = {
        'User-Agent': 'Mozilla/5.0 (X11; UwUntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0',
        'Accept': '*/*',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': url,
        'DNT': '1',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Referer': url,
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }
    response = requests.request("GET", url, headers=customHeaders)
    
    if response.status_code == 403:
        return None
    elif response.json() != {}:
        grantType = "client_credentials"
        getAccessToken = f"https://id.twitch.tv/oauth2/token?client_id={clientID}&client_secret={clientSecret}&grant_type={grantType}"
        token = requests.request("POST", getAccessToken)
        token = token.json()
        token = token["access_token"]

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Client-ID": clientID
        }

        games = response.json()["game_suggest"]
        for i in games:
            game=i
            gameId = game["id"]
            url = f"https://api.igdb.com/v4/games"
            body = f"fields name, cover.*, summary, total_rating, first_release_date, genres.*, platforms.*; where id = {gameId};"
            response = requests.request("POST", url, headers=headers, data=body)
            if len(response.json())==0:
                break
            game = response.json()[0]
            if "platforms" in game:
                gamePlatforms = game["platforms"]
                try:
                    platforms = [i["abbreviation"] for i in gamePlatforms]

                    realConsoleName = {
                        "GB": "Game Boy",
                        "GBA": "Game Boy Advance",
                        "GBC": "Game Boy Color",
                        "N64": "Nintendo 64",
                        "NES": "Nintendo Entertainment System",
                        "NDS": "Nintendo DS",
                        "SNES": "Super Nintendo Entertainment System",
                        "Sega Master System": "Sega Master System",
                        "Sega Mega Drive": "Sega Mega Drive",
                        "PS1": "PS1"
                    }

                    if realConsoleName[console] not in platforms and console not in platforms:
                        continue
                    #print(f"Game found: {game['name']} on {realConsoleName[console]}")
                    if "total_rating" not in game:
                        game["total_rating"] = "Unknown"
                    if "genres" not in game:
                        game["genres"] = [{"name": "Unknown"}]
                    if "summary" not in game:
                        game["summary"] = "Unknown"
                    if "first_release_date" not in game:
                        game["first_release_date"] = "Unknown"
                    if "cover" not in game:
                        game["cover"] = {"url": "//images.igdb.com/igdb/image/upload/t_cover_big/nocover.png"}

                    #translate all the data
                    game["summary"] = translate(game["summary"])
                    game["genres"][0]["name"] = translate(game["genres"][0]["name"])


                    genres = []
                    for genre in game["genres"]:
                        genres.append(genre["name"])
                    genres = ", ".join(genres)

                    gameData = {
                        "title": game["name"],
                        "cover": game["cover"]["url"].replace("//", "https://"),
                        "description": game["summary"],
                        "note": game["total_rating"],
                        "date": game["first_release_date"],
                        "genre": genres,
                        "id": game["id"]
                    }
                    return gameData
                except:
                    continue
        return None

def translate(string):
    language = config["ChocolateSettings"]["language"]
    if language == "EN":
        return string
    translated = GoogleTranslator(source='english', target=language.lower()).translate(string)
    return translated



tmdb.language = config["ChocolateSettings"]["language"].lower()
tmdb.debug = True

movie = Movie()
show = TV()

errorMessage = True
client_id = "771837466020937728"

enabledRPC = config["ChocolateSettings"]["discordrpc"]
if enabledRPC == "true":
    try:
        rpc_obj = rpc.DiscordIpcClient.for_platform(client_id)
    except OSError:
        enabledRPC == "false"
        config.set("ChocolateSettings", "discordrpc", "false")
        with open(os.path.join(dir, 'config.ini'), "w") as conf:
            config.write(conf)
searchedFilms = []
allMoviesNotSorted = []
searchedSeries = []
simpleDataSeries = {}
allSeriesNotSorted = []
allSeriesDict = {}
allSeriesDictTemp = {}

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
config.set("ChocolateSettings", "localIP", local_ip)
serverPort = config["ChocolateSettings"]["port"]
configLanguage = config["ChocolateSettings"]["language"]
with app.app_context():
    languageDB = db.session.query(Language).first()
    exists = db.session.query(Language).first() is not None
    if not exists:
        newLanguage = Language(language="EN")
        db.session.add(newLanguage)
        db.session.commit()
    languageDB = db.session.query(Language).first()
    if languageDB.language != configLanguage:
        db.session.query(Movies).delete()
        db.session.query(Series).delete()
        db.session.query(Seasons).delete()
        db.session.query(Episodes).delete()
        languageDB.language = configLanguage
        db.session.commit()

CHUNK_LENGTH = 5
genreList = {
    12: "Aventure",
    14: "Fantastique",
    16: "Animation",
    18: "Drama",
    27: "Horreur",
    28: "Action",
    35: "Comédie",
    36: "Histoire",
    37: "Western",
    53: "Thriller",
    80: "Crime",
    99: "Documentaire",
    878: "Science-fiction",
    9648: "Mystère",
    10402: "Musique",
    10749: "Romance",
    10751: "Famille",
    10752: "War",
    10759: "Action & Adventure",
    10762: "Kids",
    10763: "News",
    10764: "Reality",
    10765: "Sci-Fi & Fantasy",
    10766: "Soap",
    10767: "Talk",
    10768: "War & Politics",
    10769: "Western",
    10770: "TV Movie",
}

genresUsed = []
moviesGenre = []
movieExtension = ""
websitesTrailers = {
    "YouTube": "https://www.youtube.com/embed/",
    "Dailymotion": "https://www.dailymotion.com/video/",
    "Vimeo": "https://vimeo.com/",
}

def getMovies(libraryName):
    movie = Movie()
    path = Libraries.query.filter_by(libName=libraryName).first().libFolder
    try:
        os.chdir(path)
    except OSError as e:
        print("No movies found")
        return
    filmFileList = []
    movies = os.listdir(path)
    for movieFile in movies:
        if os.path.isfile(f"{path}/{movieFile}"):
            filmFileList.append(movieFile)

    filmFileList = filmFileList
    filmFileList.sort()

    for searchedFilm in filmFileList:
        if not isinstance(searchedFilm, str):
            continue
        if not searchedFilm.endswith("/") and searchedFilm.endswith(("mp4", "mp4v", "mov", "avi", "flv", "wmv", "asf", "mpeg", "mpg", "mkv", "ts")):
            movieTitle = searchedFilm
            originalMovieTitle = movieTitle
            size = len(movieTitle)
            movieTitle, extension = os.path.splitext(movieTitle)
            index = filmFileList.index(searchedFilm) + 1
            percentage = index * 100 / len(filmFileList)

            loadingFirstPart = ("•" * int(percentage * 0.2))[:-1]
            loadingFirstPart = f"{loadingFirstPart}➤"
            loadingSecondPart = "•" * (20 - int(percentage * 0.2))
            loading = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loadingFirstPart} \33[31m{loadingSecondPart}\33[0m] | {movieTitle} | {index}/{len(filmFileList)}                                                      "
            print("\033[?25l", end="")
            print(loading, end="\r", flush=True)
            
            with app.app_context():
                exists = db.session.query(Movies).filter_by(title=movieTitle).first() is not None
                #if exists, check if the library is the same, if not, add the library to the list
                if exists:
                    theMovie = db.session.query(Movies).filter_by(title=movieTitle).first()
                    if libraryName not in theMovie.libraryName:
                        theMovie.libraryName = theMovie.libraryName + ", " + libraryName
                        db.session.commit()
                        continue
                if not exists:
                    movie = Movie()
                    try:
                        search = movie.search(movieTitle)
                    except TMDbException:
                        print(TMDbException)
                        allMoviesNotSorted.append(search)
                        continue

                    if not search:
                        allMoviesNotSorted.append(originalMovieTitle)
                        continue
                    if config["ChocolateSettings"]["askwhichmovie"] == "false" or len(search)==1:
                        bestMatch = search[0]
                        for i in range(len(search)):
                            if (lev(movieTitle, search[i].title) < lev(movieTitle, bestMatch.title)
                                and bestMatch.title not in filmFileList):
                                bestMatch = search[i]
                            elif (lev(movieTitle, search[i].title) == lev(movieTitle, bestMatch.title)
                                and bestMatch.title not in filmFileList):
                                bestMatch = bestMatch
                            if (lev(movieTitle, bestMatch.title) == 0
                                and bestMatch.title not in filmFileList):
                                break
                    else:
                        print(f"I found {len(search)} movies for {movieTitle}                                       ")
                        for serieSearched in search:
                            indexOfTheSerie = search.index(serieSearched)
                            try:
                                print(f"{serieSearched.title} id:{indexOfTheSerie} date:{serieSearched.release_date}")
                            except:
                                print(f"{serieSearched.title} id:{indexOfTheSerie} date:Unknown")
                        valueSelected = int(input("Which movie is it (id):"))
                        if valueSelected < len(search):
                            bestMatch = search[valueSelected]

                    res = bestMatch
                    try:
                        name = res.title
                    except AttributeError as e:
                        name = res.original_title

                    movieCoverPath = f"https://image.tmdb.org/t/p/original{res.poster_path}"
                    banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
                    rewritedName = movieTitle.replace(" ", "_")
                    if not os.path.exists(
                        f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png"):
                        with open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png".replace("\\", "/"), "wb") as f:
                            f.write(requests.get(movieCoverPath).content)
                            
                        img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png".replace("\\", "/"))
                        img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.webp".replace("\\", "/"), "webp")
                        os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png")

                    if not os.path.exists(
                        f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png"):
                        with open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png", "wb") as f:
                            f.write(requests.get(banniere).content)

                        img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png")
                        img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.webp", "webp")
                        os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png")

                    banniere = f"/static/img/mediaImages/{rewritedName}_Banner.webp"
                    movieCoverPath = f"/static/img/mediaImages/{rewritedName}_Cover.webp"

                    size1 = os.path.getsize(f"{dirPath}{movieCoverPath}")
                    size2 = os.path.getsize(f"{dirPath}{banniere}")
                    if size1 < 10240:
                        movieCoverPath = "/static/img/broken.png"
                    if size2 < 10240:
                        banniere = "/static/img/brokenBanner.png"
                    description = res.overview
                    note = res.vote_average
                    try:
                        date = res.release_date
                    except AttributeError as e:
                        date = "Unknown"
                    movieId = res.id
                    details = movie.details(movieId)

                    casts = details.casts.cast
                    theCast = []
                    for cast in casts:
                        characterName = cast.character
                        actorName = (
                            cast.name.replace(" ", "_")
                            .replace("/", "")
                            .replace("\"", "")
                        )
                        imagePath = f"https://www.themoviedb.org/t/p/w600_and_h900_bestv2{cast.profile_path}"
                        if not os.path.exists(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.webp"):
                            with open(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.png", "wb") as f:
                                try:
                                    f.write(requests.get(imagePath).content)
                                    imagePath = f"/static/img/mediaImages/Actor_{actorName}.png"
                                    img = Image.open(f"/static/img/mediaImages/Actor_{actorName}.png")
                                    img.save(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.webp", "webp")
                                    os.remove(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.png")

                                except:
                                    continue
                        actor = [cast.name, characterName, imagePath, cast.id]
                        if actor not in theCast:
                            theCast.append(actor)
                        else:
                            break
                        person = Person()
                        p = person.details(cast.id)
                        exists = Actors.query.filter_by(actorId=cast.id).first() is not None
                        if not exists:
                            actor = Actors(name=cast.name, actorImage=imagePath, actorDescription=p.biography, actorBirthDate=p.birthday, actorBirthPlace=p.place_of_birth, actorPrograms=f"{movieId}", actorId=cast.id)
                            db.session.add(actor)
                            db.session.commit()
                        else:
                            actor = Actors.query.filter_by(actorId=cast.id).first()
                            actor.actorPrograms = f"{actor.actorPrograms} {movieId}"
                            db.session.commit()
                    theCast = theCast
                    try:
                        date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
                    except ValueError as e:
                        date = "Unknown"
                    except UnboundLocalError:
                        date = "Unknown"

                    genre = res.genre_ids
                    video_path = f"{path}\{originalMovieTitle}"
                    # convert seconds to hours, minutes and seconds
                    length = length_video(video_path)
                    length = str(datetime.timedelta(seconds=length))
                    length = length.split(":")

                    if len(length) == 3:
                        hours = length[0]
                        minutes = length[1]
                        seconds = str(round(float(length[2])))
                        if int(seconds) < 10:
                            seconds = f"0{seconds}"
                        length = f"{hours}:{minutes}:{seconds}"
                    elif len(length) == 2:
                        minutes = length[0]
                        seconds = str(round(float(length[1])))
                        if int(seconds) < 10:
                            seconds = f"0{seconds}"
                        length = f"{minutes}:{seconds}"
                    elif len(length) == 1:
                        seconds = str(round(float(length[0])))
                        if int(seconds) < 10:
                            seconds = f"0{seconds}"
                        length = f"00:{seconds}"
                    else:
                        length = "0"

                    duration = length

                    for genreId in genre:
                        if genreList[genreId] not in genresUsed:
                            genresUsed.append(genreList[genreId])
                        if genreList[genreId] not in moviesGenre:
                            moviesGenre.append(genreList[genreId])
                    # replace the id with the name of the genre
                    movieGenre = []
                    for genreId in genre:
                        movieGenre.append(genreList[genreId])

                    bandeAnnonce = details.videos.results
                    bandeAnnonceUrl = ""
                    if len(bandeAnnonce) > 0:
                        for video in bandeAnnonce:
                            bandeAnnonceType = video.type
                            bandeAnnonceHost = video.site
                            bandeAnnonceKey = video.key
                            if bandeAnnonceType == "Trailer":
                                try:
                                    bandeAnnonceUrl = (
                                        websitesTrailers[bandeAnnonceHost] + bandeAnnonceKey
                                    )
                                    break
                                except KeyError as e:
                                    bandeAnnonceUrl = "Unknown"
                                    print(e)
                    filmData = Movies(movieId, movieTitle, name, movieCoverPath, banniere, originalMovieTitle, description, note, date, json.dumps(movieGenre), str(duration), json.dumps(theCast), bandeAnnonceUrl, str(res["adult"]), libraryName=libraryName)
                    db.session.add(filmData)
                    db.session.commit()
        elif searchedFilm.endswith("/") == False:
            allMoviesNotSorted.append(searchedFilm)


def getSeries(libraryName):
    allSeriesPath = Libraries.query.filter_by(libName=libraryName).first().libFolder
    try:
        allSeries = [
            name
            for name in os.listdir(allSeriesPath)
            if os.path.isdir(os.path.join(allSeriesPath, name))
            and name.endswith((".rar", ".zip", ".part")) == False
        ]
    except OSError as e:
        print("No series found")
        return

    allSeasonsAppelations = ["S"]
    allEpisodesAppelations = ["E"]
    for series in allSeries:
        uglySeasonAppelations = ["Saison", "Season", series.replace(" ", ".")]
        seasons = os.listdir(f"{allSeriesPath}\\{series}")
        serieSeasons = {}
        for season in seasons:
            path = f"{allSeriesPath}/{series}"
            if (
                not (
                    season.startswith(tuple(allSeasonsAppelations))
                    and not season.endswith(
                        ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
                    )
                )
                or season.startswith(tuple(uglySeasonAppelations))
                and season.endswith((".rar", ".zip", ".part")) == False
            ):
                allSeasons = os.listdir(f"{path}")
                for allSeason in allSeasons:
                    untouchedSeries = config["ChocolateSettings"][
                        "untouchedSeries"
                    ].split(";")
                    if (
                        (
                            allSeriesPath != str(Path.home() / "Downloads")
                            or allSeriesPath != "."
                        )
                        and allSeason not in untouchedSeries
                        and (
                            allSeason.startswith(tuple(allSeasonsAppelations)) == False
                            and allSeason.endswith(
                                ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
                            )
                            == False
                        )
                        or season.startswith(tuple(uglySeasonAppelations))
                    ):
                        if os.path.isdir(f"{path}/{allSeason}") and not (allSeason.startswith(tuple(allSeasonsAppelations)) and allSeason.endswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"))):
                            print(f"For {uglySeasonAppelations[2]} : {allSeason}")
                            reponse = ask(
                                f"I found that folder, can I rename it from {allSeason} to S{allSeasons.index(allSeason)+1}",
                                AskResult.YES,
                            )
                            if reponse:
                                try:
                                    os.rename(
                                        f"{path}/{allSeason}",
                                        f"{path}/S{allSeasons.index(allSeason)+1}",
                                    )
                                except Exception as e:
                                    print(f"Something went wrong : {e}")
                            else:
                                renameNewName = input("In what do you want rename this folder ? ex: S7, S22...")
                                if renameNewName.isnumeric():
                                    renameNewName = f"S{renameNewName}"
                                elif renameNewName.startswith("S"):
                                    renameNewName=renameNewName
                                try:
                                    os.rename(
                                        f"{path}/{allSeason}",
                                        f"{path}/{renameNewName}",
                                    )
                                except Exception as e:
                                    print(f"Something went wrong : {e}")



            episodesPath = f"{path}\{season}"
            try:
                seasonNumber = season.split(" ")[1]
            except Exception as e:
                seasonNumber = season.replace("S", "")
            if os.path.isdir(episodesPath):
                episodes = os.listdir(episodesPath)
                seasonEpisodes = {}
                oldIndex = 0
                for episode in episodes:
                    episodeName, episodeExtension = os.path.splitext(episode)
                    if os.path.isfile(f"{episodesPath}/{episode}"):
                        if episodeName.startswith(
                            tuple(allEpisodesAppelations)
                        ) and episodeName.endswith(
                            ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
                        ):
                            oldIndex = episodes.index(episode)
                        else:
                            actualName = f"{episodesPath}/{episode}"
                            oldIndex = episodes.index(episode)
                            if episode.endswith((".rar", ".zip", ".part")) == False:
                                newName = f"E{episodes.index(episode)+1}{episodeExtension}"
                                reponse = ask(
                                    f"Can i rename {actualName} to {episodesPath}/{newName}",
                                    AskResult.YES,
                                )
                                if reponse:
                                    try:
                                        os.rename(
                                            actualName,
                                            f"{episodesPath}/{newName}",
                                        )
                                        episode = f"{newName}"
                                    except Exception as e:
                                        print(f"Something went wrong : {e}")
                                else:
                                    renameNewName = input("In what do you want rename this file ? ex: E7, E22...")
                                    if renameNewName.isnumeric():
                                        renameNewName = f"E{renameNewName}"
                                    elif renameNewName.startswith("E"):
                                        renameNewName=renameNewName
                                    try:
                                        os.rename(
                                            actualName,
                                            f"{episodesPath}/{renameNewName}{episodeExtension}",
                                        )
                                        episode = f"{renameNewName}{episodeExtension}"
                                    except Exception as e:
                                        print(f"Something went wrong : {e}")



                        seasonEpisodes[oldIndex + 1] = f"{path}/{season}/{episode}"
                serieSeasons[seasonNumber] = seasonEpisodes
        serieData = {}
        serieData["seasons"] = serieSeasons
        allSeriesDictTemp[series] = serieData

    allSeries = allSeriesDictTemp
    allSeriesName = []
    for series in allSeries:
        allSeriesName.append(series)
        for season in allSeries[series]["seasons"]:
            for episode in allSeries[series]["seasons"][season]:
                actualPath = allSeries[series]["seasons"][season][episode]
                HTTPPath = actualPath.replace(allSeriesPath, "")
                HTTPPath = HTTPPath.replace("\\", "/")
    for serie in allSeriesName:
        if not isinstance(serie, str):
            print(f"{serie} is not 'isinstance'")
            continue
        index = allSeriesName.index(serie) + 1
        percentage = index * 100 / len(allSeriesName)

        loadingFirstPart = ("•" * int(percentage * 0.2))[:-1]
        loadingFirstPart = f"{loadingFirstPart}➤"
        loadingSecondPart = "•" * (20 - int(percentage * 0.2))
        loading = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loadingFirstPart} \33[31m{loadingSecondPart}\33[0m] | {serie} | {index}/{len(allSeriesName)}                              "
        print("\033[?25l", end="")
        print(loading, end="\r", flush=True)
        with app.app_context():

            show = TV()
            serieTitle = serie
            originalSerieTitle = serieTitle
            serieModifiedTime = os.path.getmtime(f"{allSeriesPath}/{serieTitle}")
            try:
                search = show.search(serieTitle)
            except TMDbException as e:
                allSeriesNotSorted.append(serieTitle)
                break

            if not search:
                allSeriesNotSorted.append(serieTitle)
                print(f"{originalSerieTitle} return nothing, try to rename it, the english name return more results.")
                continue

            askForGoodSerie = config["ChocolateSettings"]["askWhichSerie"]
            if askForGoodSerie == "false" or len(search)==1:
                bestMatch = search[0]
                for i in range(len(search)):
                    if (
                        lev(serieTitle, search[i].name) < lev(serieTitle, bestMatch.name)
                        and bestMatch.name not in allSeriesName
                    ):
                        bestMatch = search[i]
                    elif (
                        lev(serieTitle, search[i].name) == lev(serieTitle, bestMatch.name)
                        and bestMatch.name not in allSeriesName
                    ):
                        bestMatch = bestMatch
                    if (
                        lev(serieTitle, bestMatch.name) == 0
                        and bestMatch.name not in allSeriesName
                    ):
                        break
            else:
                print(f"I found {len(search)} series that can be the one you want")
                for serieSearched in search:
                    indexOfTheSerie = search.index(serieSearched)
                    print(f"{serieSearched.name} id:{indexOfTheSerie}")
                valueSelected = int(input("Which serie is it (id):"))
                if valueSelected < len(search):
                    bestMatch = search[valueSelected]

            res = bestMatch
            serieId = res.id
            details = show.details(serieId)
            seasonsInfo = details.seasons
            name = res.name
            serieCoverPath = f"https://image.tmdb.org/t/p/original{res.poster_path}"
            banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
            rewritedName = serieTitle.replace(" ", "_")


            exists = db.session.query(Series).filter_by(id=serieId).first() is not None
            if not exists:
                if not os.path.exists(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png"):
                    with open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png","wb") as f:
                        f.write(requests.get(serieCoverPath).content)

                    img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png")
                    img = img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.webp", "webp")
                    os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}_Cover.png")

                if not os.path.exists(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png"):
                    with open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png","wb") as f:
                        f.write(requests.get(banniere).content)

                    img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png")
                    img = img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.webp", "webp")
                    os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}_Banner.png")
                banniere = f"/static/img/mediaImages/{rewritedName}_Banner.webp"
                serieCoverPath = f"/static/img/mediaImages/{rewritedName}_Cover.webp"
                description = res["overview"]
                note = res.vote_average
                date = res.first_air_date
                serieId = res.id
                details = show.details(serieId)
                seasonsInfo = details.seasons
                cast = details.credits.cast
                runTime = details.episode_run_time
                duration = ""
                for i in range(len(runTime)):
                    if i != len(runTime) - 1:
                        duration += f"{str(runTime[i])}:"
                    else:
                        duration += f"{str(runTime[i])}"
                seasonsInfo = details.seasons
                serieGenre = details.genres
                bandeAnnonce = details.videos.results
                bandeAnnonceUrl = ""
                if len(bandeAnnonce) > 0:
                    for video in bandeAnnonce:
                        bandeAnnonceType = video.type
                        bandeAnnonceHost = video.site
                        bandeAnnonceKey = video.key
                        if bandeAnnonceType == "Trailer" or len(bandeAnnonce) == 1:
                            try:
                                bandeAnnonceUrl = (websitesTrailers[bandeAnnonceHost] + bandeAnnonceKey
                                )
                                break
                            except KeyError as e:
                                bandeAnnonceUrl = "Unknown"
                                print(e)
                genreList = []
                for genre in serieGenre:
                    genreList.append(str(genre.name))
                newCast = []
                cast = list(cast)[:5]
                for actor in cast:
                    actorName = actor.name.replace(" ", "_").replace("/", "")
                    actorImage = f"https://image.tmdb.org/t/p/original{actor.profile_path}"
                    if not os.path.exists(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.png"):
                        with open(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.png", "wb") as f:
                            f.write(requests.get(actorImage).content)
                        img = Image.open(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.png".replace("\\", "/"))
                        img = img.save(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.webp".replace("\\", "/"), "webp")
                        os.remove(f"{dirPath}/static/img/mediaImages/Actor_{actorName}.png")

                    actorImage = f"/static/img/mediaImages/Actor_{actorName}.webp"
                    actorCharacter = actor.character
                    actor.profile_path = str(actorImage)
                    actorName = actorName.replace("_", " ")
                    thisActor = [str(actorName), str(actorCharacter), str(actorImage), str(actor.id)]
                    newCast.append(thisActor)

                    
                    person = Person()
                    p = person.details(actor.id)
                    exists = Actors.query.filter_by(actorId=actor.id).first() is not None
                    if not exists:
                        actor = Actors(name=actor.name, actorId=actor.id, actorImage=actorImage, actorDescription=p.biography, actorBirthDate=p.birthday, actorBirthPlace=p.place_of_birth, actorPrograms=f"{serieId}")
                        db.session.add(actor)
                        db.session.commit()
                    else:
                        actor = Actors.query.filter_by(actorId=actor.id).first()
                        actor.actorPrograms = f"{actor.actorPrograms} {serieId}"
                        db.session.commit()

                newCast = json.dumps(newCast[:5])
                genreList = json.dumps(genreList)
                serieObject = Series(id=serieId, name=name, originalName=originalSerieTitle, genre=genreList, duration=duration, description=description, cast=newCast, bandeAnnonceUrl=bandeAnnonceUrl, serieCoverPath=serieCoverPath, banniere=banniere, note=note, date=date, serieModifiedTime=serieModifiedTime, libraryName=libraryName)
                db.session.add(serieObject)
                db.session.commit()
                seasonsNumber = []
                seasons = os.listdir(f"{allSeriesPath}/{originalSerieTitle}")
                for season in seasons:
                    season = re.sub(r"\D", "", season)
                    seasonsNumber.append(int(season))


                for season in seasonsInfo:
                    releaseDate = season.air_date
                    episodesNumber = season.episode_count
                    seasonNumber = season.season_number
                    seasonId = season.id
                    seasonName = season.name
                    
                    try:
                        exists = Seasons.query.filter_by(seasonId=seasonId).first() is not None
                    except sqlalchemy.exc.PendingRollbackError as e:
                        db.session.rollback()
                        exists = Seasons.query.filter_by(seasonId=seasonId).first() is not None
                    if not exists and seasonNumber in seasonsNumber:
                        seasonDescription = season.overview
                        seasonCoverPath = (f"https://image.tmdb.org/t/p/original{season.poster_path}")
                        if not os.path.exists(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png"):
                            with open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png", "wb") as f:
                                f.write(requests.get(seasonCoverPath).content)
                            img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png".replace("\\", "/"))
                            img = img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.webp".replace("\\", "/"), "webp")
                            os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png")

                        seasonCoverPath = f"/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.webp"

                        allSeasonsUglyDict = os.listdir(f"{allSeriesPath}/{serie}")
                        try:
                            allSeasons = [int(season.replace("S", "")) for season in allSeasonsUglyDict]
                        except ValueError as e:
                            break
                        #get the size of the season
                        try:
                            modifiedDate = os.path.getmtime(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                        except FileNotFoundError as e:
                            continue

                        thisSeason = Seasons(serie=serieId, release=releaseDate, episodesNumber=episodesNumber, seasonNumber=seasonNumber, seasonId=seasonId, seasonName=seasonName, seasonDescription=seasonDescription, seasonCoverPath=seasonCoverPath, modifiedDate=modifiedDate)
                        
                        try:
                            db.session.add(thisSeason)
                            db.session.commit()
                        except sqlalchemy.exc.PendingRollbackError as e:
                            db.session.rollback()
                            db.session.add(thisSeason)
                            db.session.commit()
                        
                        try:
                            allEpisodes = os.listdir(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                        except FileNotFoundError as e:
                            continue

                        for episode in allEpisodes:
                            slug = f"/{serie}/S{seasonNumber}/{episode}"
                            episodeName = slug.split("/")[-1]
                            episodeName, extension = os.path.splitext(episodeName)

                            try:
                                episodeIndex = int(episodeName.replace("E", ""))
                            except:
                                break
                            showEpisode = Episode()
                            try:
                                episodeInfo = showEpisode.details(serieId, seasonNumber, episodeIndex)
                                exists = Episodes.query.filter_by(episodeId=episodeInfo.id).first() is not None
                                if not exists:
                                    coverEpisode = f"https://image.tmdb.org/t/p/original{episodeInfo.still_path}"
                                    rewritedName = originalSerieTitle.replace(" ", "_")
                                    if not os.path.exists(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png"):
                                        with open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png","wb") as f:
                                            f.write(requests.get(coverEpisode).content)

                                        img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png".replace("\\", "/"))
                                        img = img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.webp".replace("\\", "/"), "webp")
                                        os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png")
                                    coverEpisode = f"/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.webp"

                                    try:
                                        episodeData = Episodes(episodeId=episodeInfo.id, episodeName=episodeName, seasonId=seasonId, episodeNumber=episodeIndex, episodeDescription=episodeInfo.overview, episodeCoverPath=coverEpisode, releaseDate=episodeInfo.air_date, slug=slug, introStart=0.0, introEnd=0.0)
                                        db.session.add(episodeData)
                                        db.session.commit()
                                    except:
                                        pass
                            except TMDbException as e:
                                print(f"I didn't find an the episode {episodeIndex} of the season {seasonNumber} of the serie with ID {serieId}",e)

                            

            else:
                seasonsNumber = []
                seasons = os.listdir(f"{allSeriesPath}/{originalSerieTitle}")
                for season in seasons:
                    season = re.sub(r"\D", "", season)
                    seasonsNumber.append(int(season))
                theSerie = Series.query.filter_by(id=serieId).first()
                theSerieModifiedTime = theSerie.serieModifiedTime
                if serieModifiedTime > theSerieModifiedTime:
                    theSerie.serieModifiedTime = serieModifiedTime
                    db.session.commit()

                for season in seasonsInfo:
                    releaseDate = season.air_date
                    episodesNumber = season.episode_count
                    seasonNumber = season.season_number
                    seasonId = season.id
                    seasonName = season.name
                    
                    try:
                        exists = Seasons.query.filter_by(seasonId=seasonId).first() is not None
                    except sqlalchemy.exc.PendingRollbackError as e:
                        db.session.rollback()
                        exists = Seasons.query.filter_by(seasonId=seasonId).first() is not None
                    if not exists and seasonNumber in seasonsNumber:
                        seasonDescription = season.overview
                        seasonCoverPath = (f"https://image.tmdb.org/t/p/original{season.poster_path}")
                        if not os.path.exists(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png"):
                            with open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png", "wb") as f:
                                f.write(requests.get(seasonCoverPath).content)
                            img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png".replace("\\", "/"))
                            img = img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.webp".replace("\\", "/"), "webp")
                            os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.png")

                        seasonCoverPath = f"/static/img/mediaImages/{rewritedName}S{seasonNumber}_Cover.webp"

                        allSeasonsUglyDict = os.listdir(f"{allSeriesPath}/{serie}")
                        try:
                            allSeasons = [int(season.replace("S", "")) for season in allSeasonsUglyDict]
                        except ValueError as e:
                            break
                        #get the size of the season
                        try:
                            modifiedDate = os.path.getmtime(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                        except FileNotFoundError as e:
                            break
                        
                        thisSeason = Seasons(serie=serieId, release=releaseDate, episodesNumber=episodesNumber, seasonNumber=seasonNumber, seasonId=seasonId, seasonName=seasonName, seasonDescription=seasonDescription, seasonCoverPath=seasonCoverPath, modifiedDate=modifiedDate)
                        
                        try:
                            db.session.add(thisSeason)
                            db.session.commit()
                        except sqlalchemy.exc.PendingRollbackError as e:
                            db.session.rollback()
                            db.session.add(thisSeason)
                            db.session.commit()
                    elif seasonNumber in seasonsNumber:
                        thisSeason = Seasons.query.filter_by(seasonId=seasonId).first()
                        modifiedDate = os.path.getmtime(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                        modifiedDateDB = thisSeason.modifiedDate
                        if modifiedDate > modifiedDateDB:
                            thisSeason.modifiedDate = modifiedDate
                            db.session.commit()

                            try:
                                allEpisodes = os.listdir(f"{allSeriesPath}/{serie}/S{seasonNumber}")
                            except FileNotFoundError as e:
                                continue

                            for episode in allEpisodes:

                                slug = f"/{serie}/S{seasonNumber}/{episode}"
                                episodeName = slug.split("/")[-1]
                                episodeName, extension = os.path.splitext(episodeName)

                                try:
                                    episodeIndex = int(episodeName.replace("E", ""))
                                except:
                                    break
                                showEpisode = Episode()
                                try:
                                    episodeInfo = showEpisode.details(serieId, seasonNumber, episodeIndex)
                                    exists = Episodes.query.filter_by(episodeId=episodeInfo.id).first() is not None
                                    if not exists:
                                        coverEpisode = f"https://image.tmdb.org/t/p/original{episodeInfo.still_path}"
                                        rewritedName = originalSerieTitle.replace(" ", "_")
                                        if not os.path.exists(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png"):
                                            with open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png","wb") as f:
                                                f.write(requests.get(coverEpisode).content)
                                            img = Image.open(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png".replace("\\", "/"))
                                            img = img.save(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.webp".replace("\\", "/"), "webp")
                                            os.remove(f"{dirPath}/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.png")
                                        coverEpisode = f"/static/img/mediaImages/{rewritedName}S{seasonNumber}E{episodeIndex}_Cover.webp"

                                        try:
                                            episodeData = Episodes(episodeId=episodeInfo.id, episodeName=episodeName, seasonId=seasonId, episodeNumber=episodeIndex, episodeDescription=episodeInfo.overview, episodeCoverPath=coverEpisode, releaseDate=episodeInfo.air_date, slug=slug, introStart=0.0, introEnd=0.0)
                                            db.session.add(episodeData)
                                            db.session.commit()
                                        except:
                                            pass
                                except TMDbException as e:
                                    print(f"I didn't find an the episode {episodeIndex} of the season {seasonNumber} of the serie with ID {serieId}",e)

def getGames(libraryName):
    allGamesPath = Libraries.query.filter_by(libName=libraryName).first().libFolder
    try:
        allConsoles = [name for name in os.listdir(allGamesPath) if os.path.isdir(os.path.join(allGamesPath, name)) and name.endswith((".rar", ".zip", ".part")) == False]
        for console in allConsoles:
            if os.listdir(f"{allGamesPath}/{console}") == []:
                allConsoles.remove(console)

    except OSError as e:
        print("No games found")
        return
    saidPS1 = False
    supportedConsoles = ['3DO', 'Amiga', 'Atari 2600', 'Atari 5200', 'Atari 7800', 'Atari Jaguar', 'Atari Lynx', 'GB', 'GBA', 'GBC', 'N64', 'NDS', 'NES', 'SNES', 'Neo Geo Pocket', 'PSX', 'Sega 32X', 'Sega CD', 'Sega Game Gear', 'Sega Master System', 'Sega Mega Drive', 'Sega Saturn', "PS1"]
    supportedFileTypes = [".zip", ".adf", ".adz", ".dms", ".fdi", ".ipf", ".hdf", ".lha", ".slave", ".info", ".cdd", ".nrg", ".mds", ".chd", ".uae", ".m3u", ".a26", ".a52", ".a78", ".j64", ".lnx", ".gb", ".gba", ".gbc", ".n64", ".nds", ".nes", ".ngp", ".psx", ".sfc", ".smc", ".smd", ".32x", ".cd", ".gg", ".md", ".sat", ".sms"]
    for console in allConsoles:
        if console not in supportedConsoles:
            print(f"{console} is not supported or the console name is not correct, here is the list of supported consoles : {', '.join(supportedConsoles)} rename the folder to one of these names if it's the correct console")
            break
        size = len(allConsoles)
        gameName, extension = os.path.splitext(console)
        index = allConsoles.index(console) + 1
        percentage = index * 100 / size

        loadingFirstPart = ("•" * int(percentage * 0.2))[:-1]
        loadingFirstPart = f"{loadingFirstPart}➤"
        loadingSecondPart = "•" * (20 - int(percentage * 0.2))
        loading = f"{str(int(percentage)).rjust(3)}% | [\33[32m{loadingFirstPart} \33[31m{loadingSecondPart}\33[0m] | {gameName} | {index}/{len(allConsoles)}                                                      "
        print("\033[?25l", end="")
        print(loading, end="\r", flush=True)

        allFiles = os.listdir(f"{allGamesPath}/{console}")
        for file in allFiles:
            with app.app_context():
                exists = Games.query.filter_by(slug=f"{allGamesPath}/{console}/{file}").first()
                if file.endswith(tuple(supportedFileTypes)) and exists == None:
                    #select the string between ()
                    newFileName = file                    
                    newFileName = re.sub(r'\d{5} - ', '', newFileName)
                    newFileName = re.sub(r'\d{4} - ', '', newFileName)
                    newFileName = re.sub(r'\d{3} - ', '', newFileName)
                    newFileName, extension = os.path.splitext(newFileName)
                    newFileName = newFileName.rstrip()
                    newFileName = f"{newFileName}{extension}"
                    os.rename(f"{allGamesPath}/{console}/{file}", f"{allGamesPath}/{console}/{newFileName}")
                    file = newFileName
                    while ".." in newFileName:
                        newFileName = newFileName.replace("..", ".")
                    try:
                        os.rename(f"{allGamesPath}/{console}/{file}", f"{allGamesPath}/{console}/{newFileName}")
                    except FileExistsError:
                        os.remove(f"{allGamesPath}/{console}/{file}")
                    file, extension = os.path.splitext(file)

                    gameIGDB = searchGame(file, console)
                    if gameIGDB != None and gameIGDB != {}:
                        gameName = gameIGDB["title"]
                        gameRealTitle = newFileName
                        gameCover = gameIGDB["cover"]
                        gameDescription = gameIGDB["description"]
                        gameNote = gameIGDB["note"]
                        gameDate = gameIGDB["date"]
                        gameGenre = gameIGDB["genre"]
                        gameId = gameIGDB["id"]
                        gameConsole = console
                        gameSlug = f"{allGamesPath}/{console}/{newFileName}"
        
                        game = Games(console=gameConsole, id=gameId, title=gameName, realTitle=gameRealTitle, cover=gameCover, description=gameDescription, note=gameNote, date=gameDate, genre=gameGenre, slug=gameSlug, libraryName=libraryName)
                        db.session.add(game)
                        db.session.commit()
                    else:
                        print(f"I didn't find the game {file} at {console}")
                elif console == "PS1" and file.endswith(".cue") and exists == None:
                    if saidPS1 == False:
                        print(f"You need to zip all our .bin files and the .cue file in one .zip file to being able to play it")
                        saidPS1 = True
                    #check if user want to zip the files with asklib
                    value = config["ChocolateSettings"]["compressPS1Games"]
                    if value.lower() == "true":
                        #get the index of the file
                        index = allFiles.index(file)-1
                        #get all bin files before the cue file
                        allBins = []
                        while allFiles[index].endswith(".bin"):
                            allBins.append(allFiles[index])
                            index -= 1
                        #zip all the bin files and the cue file
                        fileName, extension = os.path.splitext(file)
                        with zipfile.ZipFile(f"{allGamesPath}/{console}/{fileName}.zip", 'w') as zipObj:
                            for binFiles in allBins:
                                zipObj.write(f"{allGamesPath}/{console}/{binFiles}", binFiles)
                            zipObj.write(f"{allGamesPath}/{console}/{file}", file)
                        for binFiles in allBins:
                            os.remove(f"{allGamesPath}/{console}/{binFiles}")
                        os.remove(f"{allGamesPath}/{console}/{file}")
                        file = f"{fileName}.zip"
                        newFileName = file                    
                        newFileName = re.sub(r'\d{5} - ', '', newFileName)
                        newFileName = re.sub(r'\d{4} - ', '', newFileName)
                        newFileName = re.sub(r'\d{3} - ', '', newFileName)
                        newFileName, extension = os.path.splitext(newFileName)
                        newFileName = newFileName.rstrip()
                        newFileName = f"{newFileName}{extension}"
                        os.rename(f"{allGamesPath}/{console}/{file}", f"{allGamesPath}/{console}/{newFileName}")
                        file = newFileName
                        while ".." in newFileName:
                            newFileName = newFileName.replace("..", ".")
                        try:
                            os.rename(f"{allGamesPath}/{console}/{file}", f"{allGamesPath}/{console}/{newFileName}")
                        except FileExistsError:
                            os.remove(f"{allGamesPath}/{console}/{file}")
                        file, extension = os.path.splitext(file)

                        gameIGDB = searchGame(file, console)
                        if gameIGDB != None and gameIGDB != {}:
                            gameName = gameIGDB["title"]
                            gameRealTitle = newFileName
                            gameCover = gameIGDB["cover"]
                            #download the cover
                            with open(f"{allGamesPath}/{console}/{gameRealTitle}.png", 'wb') as f:
                                f.write(requests.get(gameCover).content)
                            gameCover = f"{allGamesPath}/{console}/{gameRealTitle}.png"
                            img = Image.open(gameCover)
                            img = img.save(f"{allGamesPath}/{console}/{gameRealTitle}.webp", "webp")
                            os.remove(gameCover)
                            gameCover = f"{allGamesPath}/{console}/{gameRealTitle}.webp"

                            gameDescription = gameIGDB["description"]
                            gameNote = gameIGDB["note"]
                            gameDate = gameIGDB["date"]
                            gameGenre = gameIGDB["genre"]
                            gameId = gameIGDB["id"]
                            gameConsole = console
                            gameSlug = f"{allGamesPath}/{console}/{newFileName}"
                            exists = Games.query.filter_by(slug=gameSlug).first()
                            if exists == None:
                                game = Games(console=gameConsole, id=gameId, title=gameName, realTitle=gameRealTitle, cover=gameCover, description=gameDescription, note=gameNote, date=gameDate, genre=gameGenre, slug=gameSlug)
                                db.session.add(game)
                                try:
                                    db.session.commit()
                                except IntegrityError as e:
                                    e=e
                                    db.session.commit()
                        

                elif not file.endswith(".bin") and exists == None:
                    print(f"{file} is not supported, here's the list of supported files : \n{','.join(supportedFileTypes)}")

def length_video(path: str) -> float:
    seconds = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    return float(seconds.stdout)



def getGpuInfo() -> str:
    if platform.system() == "Windows":
        return gpuname()
    elif platform.system() == "Darwin":
        return subprocess.check_output(
            ["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"]
        ).strip()
    elif platform.system() == "Linux":
        return "impossible d'accéder au GPU"
    return ""


def gpuname() -> str:
    """Returns the model name of the first available GPU"""
    try:
        gpus = GPUtil.getGPUs()
    except:
        print("Unable to detect GPU model. Is your GPU configured? Are you running with nvidia-docker?")
        return "UNKNOWN"
    if len(gpus) == 0:
        raise ValueError("No GPUs detected in the system")
    return gpus[0].name

@app.route("/video/<video_name>.m3u8", methods=["GET"])
def create_m3u8(video_name):
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}{movieExtension}"
    duration = length_video(video_path)
    file = """
    #EXTM3U
    #EXT-X-VERSION:4
    #EXT-X-TARGETDURATION:5
    #EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
        #EXTINF:5.0,
        /chunk/{video_name}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
    #EXT-X-ENDLIST"
    """

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{video_name}.m3u8"
    )

    return response

@app.route("/video/<quality>/<video_name>.m3u8", methods=["GET"])
def create_m3u8_quality(quality, video_name):
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}{movieExtension}"
    duration = length_video(video_path)
    file = """
    #EXTM3U
    #EXT-X-VERSION:4
    #EXT-X-TARGETDURATION:5
    #EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
        #EXTINF:5.0,
        /chunk/{quality}/{video_name}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
    #EXT-X-ENDLIST"
    """

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{video_name}.m3u8"
    )

    return response

@app.route("/videoSerie/<episodeId>.m3u8", methods=["GET"])
def create_serie_m3u8(episodeId):
    seriesPath = config.get("ChocolateSettings", "SeriesPath")
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    episodePath = episode.slug
    episodePath = episodePath.replace("/", "\\")
    episodePath = f"{seriesPath}{episodePath}"
    duration = length_video(episodePath)
    file = """
    #EXTM3U
    #EXT-X-VERSION:4
    #EXT-X-TARGETDURATION:5
    #EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
        #EXTINF:5.0,
        /chunkSerie/{episodeId}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
    #EXT-X-ENDLIST"
    """

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set("Content-Disposition", "attachment", filename=f"{episodeId}.m3u8")

    return response

@app.route("/videoSerie/<quality>/<episodeId>.m3u8", methods=["GET"])
def create_serie_m3u8_quality(quality, episodeId):
    seriesPath = config.get("ChocolateSettings", "SeriesPath")
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    episodePath = episode.slug
    episodePath = episodePath.replace("/", "\\")
    episodePath = f"{seriesPath}{episodePath}"
    duration = length_video(episodePath)
    file = """
    #EXTM3U
    #EXT-X-VERSION:4
    #EXT-X-TARGETDURATION:5
    #EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
        #EXTINF:5.0,
        /chunkSerie/{quality}/{episodeId}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
    #EXT-X-ENDLIST"
    """

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set("Content-Disposition", "attachment", filename=f"{episodeId}.m3u8")

    return response

@app.route("/chunkSerie/<episodeId>-<int:idx>.ts", methods=["GET"])
def get_chunk_serie(episodeId, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH
    seriesPath = config.get("ChocolateSettings", "SeriesPath")
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    episode = episode.__dict__
    slug = episode["slug"]
    episodePath = f"{seriesPath}\{slug}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    logLevelValue = "error"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        logLevelValue,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        episodePath,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ac",
        "2",
        "-preset",
        "ultrafast",
        "-f",
        "mpegts",
        "pipe:1",
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{episodeId}-{idx}.ts"
    )

    return response

@app.route("/chunkSerie/<quality>/<episodeId>-<int:idx>.ts", methods=["GET"])
def get_chunk_serie_quality(quality, episodeId, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH
    seriesPath = config.get("ChocolateSettings", "SeriesPath")
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    episode = episode.__dict__
    slug = episode["slug"]
    episodePath = f"{seriesPath}\{slug}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    videoProperties = get_video_properties(episodePath)
    width = videoProperties["width"]
    height = videoProperties["height"]
    newWidth = float(quality)
    newHeight = round(float(width) / float(height) * newWidth)
    if (newHeight % 2) != 0:
        newHeight += 1
    logLevelValue = "error"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        logLevelValue,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        episodePath,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-vf",
        f"scale={newHeight}:{newWidth}",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ac",
        "2",
        "-preset",
        "ultrafast",
        "-f",
        "mpegts",
        "pipe:1",
    ]



    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{episodeId}-{idx}.ts"
    )

    return response


@app.route("/chunk/<video_name>-<int:idx>.ts", methods=["GET"])
def get_chunk(video_name, idx=0):
    global movieExtension
    seconds = (idx - 1) * CHUNK_LENGTH
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}{movieExtension}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    logLevelValue = "error"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        logLevelValue,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        video_path,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ac",
        "2",
        "-preset",
        "ultrafast",
        "-f",
        "mpegts",
        "pipe:1",
    ]



    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{video_name}-{idx}.ts"
    )

    return response

@app.route("/chunk/<quality>/<video_name>-<int:idx>.ts", methods=["GET"])
def get_chunk_quality(quality, video_name, idx=0):
    global movieExtension
    seconds = (idx - 1) * CHUNK_LENGTH
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}{movieExtension}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    videoProperties = get_video_properties(video_path)
    width = videoProperties["width"]
    height = videoProperties["height"]
    newWidth = float(quality)
    newHeight = round(float(width) / float(height) * newWidth)
    if (newHeight % 2) != 0:
        newHeight += 1
    logLevelValue = "error"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        logLevelValue,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        video_path,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-vf",
        f"scale={newHeight}:{newWidth}",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ac",
        "2",
        "-preset",
        "ultrafast",
        "-f",
        "mpegts",
        "pipe:1",
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", f"http://{local_ip}:{serverPort}")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{video_name}-{idx}.ts"
    )

    return response

@app.route("/chunkCaption/<language>/<index>/<video_name>.vtt", methods=["GET"])
def chunkCaption(video_name, language, index):
    global movieExtension
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}{movieExtension}"
    extractCaptionsCommand = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        video_path,
        "-map",
        f"0:{index}",
        "-f",
        "webvtt",
        "pipe:1",
    ]


    extractCaptions = subprocess.run(extractCaptionsCommand, stdout=subprocess.PIPE)

    extractCaptionsResponse = make_response(extractCaptions.stdout)
    extractCaptionsResponse.headers.set("Content-Type", "text/VTT")
    extractCaptionsResponse.headers.set(
        "Content-Disposition", "attachment", filename=f"{video_name}-{index}.vtt"
    )

    return extractCaptionsResponse


@app.route("/chunkAudio/<language>/<index>/<video_name>.mp3", methods=["GET"])
def chunkAudio(video_name, language, index):
    global movieExtension
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    video_path = f"{moviesPath}\{video_name}{movieExtension}"
    extractAudioCommand = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        video_path,
        "-map",
        f"a:{index}",
        "-f",
        "mp3",
        "pipe:1",
    ]

    extractAudio = subprocess.run(extractAudioCommand, stdout=subprocess.PIPE)

    extractAudioResponse = make_response(extractAudio.stdout)
    extractAudioResponse.headers.set("Content-Type", "audio/mpeg")
    extractAudioResponse.headers.set(
        "Content-Disposition", "attachment", filename=f"{video_name}-{index}.mp3"
    )

    return extractAudioResponse


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        accountName = request.form["name"]
        accountPassword = request.form["password"]
        try:
            f = request.files['profilePicture']
            name, extension = os.path.splitext(f.filename)
            thisdirPath = dirPath.replace("\\", "//")
            f.save(f"{thisdirPath}/static/img/{accountName}{extension}")
            profilePicture = f"/static/img/{accountName}{extension}"
            if extension == "":
                profilePicture = "/static/img/defaultUserProfilePic.png"
        except:
            profilePicture = "/static/img/defaultUserProfilePic.png"
        accountTypeInput = request.form["type"]

        if accountTypeInput == "Kid":
            accountPassword = ""

        new_user = Users(name=accountName, password=accountPassword, profilePicture=profilePicture, accountType=accountTypeInput)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError as e:
            e=e
            db.session.commit()
        login_user(new_user)
        if accountTypeInput == "Admin":
            return redirect(url_for("settings"))
        else:
            return redirect(url_for("home"))
    if request.method == "GET":
        typeOfUser = current_user.accountType
        if typeOfUser == "Admin":
            global allMoviesNotSorted
            condition = len(allMoviesNotSorted) > 0
            return render_template("settings.html", notSorted=allMoviesNotSorted, conditionIfOne=condition)
        else:
            return redirect(url_for("home"))

@app.route("/login", methods=["GET", "POST"])
def login():
    allUsers = Users.query.filter().all()
    allUsersDict = []
    for user in allUsers:
        userDict = {"name": user.name, "profilePicture": user.profilePicture, "accountType": user.accountType}
        allUsersDict.append(userDict)
    
    if len(allUsersDict)==0:
        return redirect(url_for("createAccount"))
    if request.method == "POST":
        accountName = request.form["name"]
        accountPassword = request.form["password"]
        user = Users.query.filter_by(name=accountName).first()
        if user:
            if user.verify_password(accountPassword):
                login_user(user)

                return redirect(url_for("home"))
            elif user.accountType == "Kid":
                login_user(user)
                return redirect(url_for("home"))
            else:
                return "Wrong password"
        else:
            return "Wrong username"
    return render_template("login.html", allUsers=allUsersDict)

@app.route("/createAccount", methods=["POST", "GET"])
def createAccount():
    allUsers = Users.query.filter().all()
    allUsersDict = []
    for user in allUsers:
        userDict = {"name": user.name, "profilePicture": user.profilePicture}
        allUsersDict.append(userDict)
    
    if len(allUsersDict)>0:
        return redirect(url_for("home"))

    if request.method == "POST":
        accountName = request.form["name"]
        accountPassword = request.form["password"]
        try:
            f = request.files['profilePicture']
            name, extension = os.path.splitext(f.filename)
            thisdirPath = dirPath.replace("\\", "//")
            profilePicture = f"/static/img/{accountName}{extension}"
            if extension == "":
                profilePicture = "/static/img/defaultUserProfilePic.png"
            else:
                f.save(f"{thisdirPath}{profilePicture}")
        except:
            profilePicture = "/static/img/defaultUserProfilePic.png"

        accountTypeInput = request.form["type"]
        new_user = Users(name=accountName, password=accountPassword, profilePicture=profilePicture, accountType=accountTypeInput)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        if accountTypeInput == "Admin":
            return redirect(url_for("settings"))
        else:
            return redirect(url_for("home"))
    return render_template("createAccount.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/profil", methods=["GET", "POST"])
def profil():
    user = current_user
    currentUsername = user.name
    if request.method == "POST":
        userName = request.form["name"]
        password = request.form["password"]
        try:
            f = request.files['profilePicture']
            name, extension = os.path.splitext(f.filename)
            thisdirPath = dirPath.replace("\\", "//")
            profilePicture = f"/static/img/{userName}{extension}"
            if extension == "":
                profilePicture = "/static/img/defaultUserProfilePic.png"
        except:
            profilePicture = "/static/img/defaultUserProfilePic.png"
        userToEdit = Users.query.filter_by(name=currentUsername).first()
        if userToEdit.name != userName:
            userToEdit.name = userName
            logout_user()
            db.session.commit()
        if userToEdit.password != generate_password_hash(password) and len(password)>0:
            userToEdit.password = generate_password_hash(password)
            db.session.commit()
        if userToEdit.profilePicture != profilePicture and profilePicture != "/static/img/defaultUserProfilePic.png":
            f = request.files['profilePicture']
            f.save(f"{thisdirPath}{profilePicture}")
            userToEdit.profilePicture = profilePicture
            db.session.commit()
    return render_template("profil.html", user=user)

@app.route("/getAccountType", methods=["GET", "POST"])
def getAccountType():
    user = current_user
    return json.dumps({"accountType": user.accountType})


@app.route("/chunkCaptionSerie/<language>/<index>/<episodeId>.vtt", methods=["GET"])
def chunkCaptionSerie(language, index, episodeId):
    seriesPath = config.get("ChocolateSettings", "SeriesPath")
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    episode = episode.__dict__
    slug = episode["slug"]
    video_path = f"{seriesPath}\{slug}"

    extractCaptionsCommand = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        video_path,
        "-map",
        f"0:{index}",
        "-f",
        "webvtt",
        "pipe:1",
    ]


    extractCaptions = subprocess.run(extractCaptionsCommand, stdout=subprocess.PIPE)

    extractCaptionsResponse = make_response(extractCaptions.stdout)
    extractCaptionsResponse.headers.set("Content-Type", "text/VTT")
    extractCaptionsResponse.headers.set(
        "Content-Disposition", "attachment", filename=f"{language}/{index}/{episodeId}.vtt"
    )

    return extractCaptionsResponse

@app.route("/saveSettings", methods=["POST"])
def saveSettings():
    MoviesPath = request.form["moviesPath"]
    SeriesPath = request.form["seriesPath"]
    GamesPath = request.form["gamesPath"]
    language = request.form["language"]
    discordRPC = request.form["discordRPCCheckbox"]
    port = request.form["port"]
    if MoviesPath != "":
        config.set("ChocolateSettings", "moviespath", MoviesPath)
    if SeriesPath != "":
        config.set("ChocolateSettings", "seriespath", SeriesPath)
    if GamesPath != "":
        config.set("ChocolateSettings", "gamespath", GamesPath)
    if language != "":
        config.set("ChocolateSettings", "language", language)
    if port != "" or port != " ":
        config.set("ChocolateSettings", "port", port)
    if discordRPC == "on":
        config.set("ChocolateSettings", "discordrpc", "true")
    else:
        config.set("ChocolateSettings", "discordrpc", "false")
    with open(os.path.join(dir, 'config.ini'), "w") as conf:
        config.write(conf)
    return redirect(url_for("settings"))



@app.route("/getAllMovies", methods=["GET"])
def getAllMovies():
    movies = Movies.query.all()
    moviesDict = [ movie.__dict__ for movie in movies ]
    for movie in moviesDict:
        del movie["_sa_instance_state"]

    return json.dumps(moviesDict, ensure_ascii=False)


@app.route("/getAllSeries", methods=["GET"])
def getAllSeries():
    global allSeriesDict
    thisAllSeriesDict = dict(sorted(allSeriesDict.items()))

    return json.dumps(thisAllSeriesDict, ensure_ascii=False, default=str, indent=4)


@app.route("/getRandomMovie")
def getRandomMovie():
    movies = Movies.query.all()
    randomMovie = random.choice(movies).__dict__
    del randomMovie["_sa_instance_state"]
    return json.dumps(randomMovie, ensure_ascii=False)


@app.route("/getRandomSerie")
def getRandomSeries():
    allSeries = Series.query.all()
    randomSerie = random.choice(allSeries).__dict__
    del randomSerie["_sa_instance_state"]
    return json.dumps(randomSerie, ensure_ascii=False, default=str)


def getSimilarMovies(movieId):
    global searchedFilms
    similarMoviesPossessed = []
    movie = Movie()
    similarMovies = movie.recommendations(movieId)
    for movieInfo in similarMovies:
        movieName = movieInfo.title
        for movie in searchedFilms:
            if movieName == movie:
                similarMoviesPossessed.append(movie)
                break
    return similarMoviesPossessed


def getSimilarSeries(seriesId) -> list:
    global allSeriesDict
    similarSeriesPossessed = []
    show = TV()
    similarSeries = show.recommendations(seriesId)
    for serieInfo in similarSeries:
        serieName = serieInfo.name
        for serie in allSeriesDict:
            try:
                if serieName == allSeriesDict[serie]["name"]:
                    similarSeriesPossessed.append(allSeriesDict[serie])
                    break
            except KeyError as e:
                print(e)
                pass
    return similarSeriesPossessed


@app.route("/getMovieData/<title>", methods=["GET", "POST"])
def getMovieData(title):
    exists = db.session.query(Movies).filter_by(title=title).first() is not None
    if exists:
        movie = Movies.query.filter_by(title=title).first().__dict__
        del movie["_sa_instance_state"]
        data = movie
        MovieId = data["id"]
        data["similarMovies"] = getSimilarMovies(MovieId)
        return json.dumps(data, ensure_ascii=False)
    else:
        return json.dumps("Not Found", ensure_ascii=False)


@app.route("/getSerieData/<title>", methods=["GET", "POST"])
def getSeriesData(title):

    title = title.replace("%20", " ")
    title = title.replace("_", " ")
    exists = db.session.query(Series).filter_by(name=title).first() is not None
    if exists:
        serie = Series.query.filter_by(name=title).first().__dict__
        serie["seasons"] = getSerieSeasons(serie["id"])
        del serie["_sa_instance_state"]
        return json.dumps(serie, ensure_ascii=False)
    exists = db.session.query(Series).filter_by(originalName=title).first() is not None
    if exists:
        serie = Series.query.filter_by(originalName=title).first().__dict__
        serie["seasons"] = getSerieSeasons(serie["id"])
        del serie["_sa_instance_state"]
        return json.dumps(serie, ensure_ascii=False)

    return json.dumps("Not Found", ensure_ascii=False)

def getSerieSeasons(id):
    seasons = Seasons.query.filter_by(serie=id).all()
    seasonsDict = {}
    for season in seasons:
        seasonsDict[season.seasonNumber] = dict(season.__dict__)
        del seasonsDict[season.seasonNumber]["_sa_instance_state"]
    return seasonsDict

@app.route("/getFirstSixMovies")
def getFirstEightMovies():
    movies = Movies.query.limit(6).all()
    moviesDict = [dict(movie.__dict__) for movie in movies]
    for movie in moviesDict:
        del movie["_sa_instance_state"]
    
    return json.dumps(moviesDict, ensure_ascii=False)


@app.route("/getFirstSixSeries")
def getFirstEightSeries():
    series = Series.query.limit(6).all()
    seriesList=[]
    for serie in series:
        del serie._sa_instance_state
        theSerie = [serie.name, serie.__dict__]
        seriesList.append(theSerie)

    return json.dumps(seriesList, ensure_ascii=False, default=str)


@app.route("/")
@app.route("/index")
@app.route("/home")
@login_required
def home():
    moviesPath = config.get("ChocolateSettings", "MoviesPath")
    filmIsntEmpty = moviesPath != "Empty"
    return render_template("index.html", moviesExist=filmIsntEmpty)


@app.route("/movies")
@login_required
def films():
    movies = Movies.query.all()
    moviesDict = [ movie.__dict__ for movie in movies ]
    for movie in moviesDict:
        del movie["_sa_instance_state"]
    searchedFilmsUp0 = len(moviesDict) == 0
    errorMessage = "Verify that the path is correct"
    routeToUse = "/getFirstSixMovies"

    return render_template("homeFilms.html", conditionIfOne=searchedFilmsUp0, errorMessage=errorMessage, routeToUse=routeToUse)


@app.route("/series")
@login_required
def series():
    global allSeriesDict
    searchedSeriesUp0 = len(allSeriesDict) == 0
    errorMessage = "Verify that the path is correct"
    routeToUse = "/getFirstSixSeries"

    return render_template("homeSeries.html", conditionIfOne=searchedSeriesUp0, errorMessage=errorMessage, routeToUse=routeToUse)


@app.route("/season/<theId>")
@login_required
def season(theId):
    #do the request to get the season
    with app.app_context():
        season = Seasons.query.filter_by(seasonId=theId).first()
        season = season.__dict__
        serie = Series.query.filter_by(id=int(season["serie"])).first()
        serie = serie.__dict__
        serie = serie["name"]
        name = f"{serie} | {season['seasonName']}"
        del season["_sa_instance_state"]
        return render_template("season.html", serie=season, title=name)


@app.route("/getSeasonData/<seasonId>/", methods=["GET", "POST"])
def getSeasonData(seasonId):
    global allSeriesDict
    season = Seasons.query.filter_by(seasonId=seasonId).first()
    episodes = Episodes.query.filter_by(seasonId=seasonId).all()
    episodesDict = {}
    for episode in episodes:
        episodesDict[episode.episodeNumber] = dict(episode.__dict__)
        del episodesDict[episode.episodeNumber]["_sa_instance_state"]
    season = season.__dict__
    del season["_sa_instance_state"]
    season["episodes"] = episodesDict
    return json.dumps(season, ensure_ascii=False, default=str)

@app.route("/getEpisodeData/<serieName>/<seasonId>/<episodeId>/", methods=["GET", "POST"])
def getEpisodeData(serieName, seasonId, episodeId):
    global allSeriesDict
    seasonId = seasonId.replace("S", "")
    episodeId = episodeId
    if serieName in allSeriesDict.keys():
        data = allSeriesDict[serieName]
        season = data["seasons"][seasonId]
        episode = season["episodes"][str(episodeId)]
        return json.dumps(episode, ensure_ascii=False, default=str)
    else:
        response = {"response": "Not Found"}
        return json.dumps(response, ensure_ascii=False, default=str)


@app.route("/<library>")
@login_required
def library():
    #get the library in the db
    library = Libraries.query.filter_by(name=library).first()
    libraryPath = library.path
    #get all movies where
    movies = Movies.query.all()
    moviesDict = [ movie.__dict__ for movie in movies ]
    for movie in moviesDict:
        del movie["_sa_instance_state"]
    searchedFilmsUp0 = len(moviesDict) == 0
    errorMessage = "Verify that the path is correct"
    routeToUse = "/getAllMovies"
    return render_template("allFilms.html",
        conditionIfOne=searchedFilmsUp0,
        errorMessage=errorMessage,
        routeToUse=routeToUse,
    )


@app.route("/serieLibrary")
@login_required
def seriesLibrary():
    global allSeriesDict
    searchedSeriesUp0 = len(allSeriesDict.keys()) == 0
    errorMessage = "Verify that the path is correct"
    routeToUse = "/getAllSeries"
    return render_template("allSeries.html",conditionIfOne=searchedSeriesUp0, errorMessage=errorMessage, routeToUse=routeToUse)

@app.route("/consoles")
@login_required
def consoles():
    return render_template("consoles.html")
    
@app.route("/getAllConsoles")
def getAllConsoles():
    consoles = Games.query.all()
    consolesDict = [ console.__dict__ for console in consoles ]
    for console in consolesDict:
        del console["_sa_instance_state"]
        #del everything that is not a console
        for key in list(console.keys()):
            if key != "console":
                del console[key]
    consolesDict = [i for n, i in enumerate(consolesDict) if i not in consolesDict[n + 1:]]
    consolesDict = [list(i.values())[0] for i in consolesDict]
    consolesDict = sorted(consolesDict)
    return json.dumps(consolesDict, ensure_ascii=False, default=str)

@app.route("/getConsoleData/<consoleName>")
def getConsoleData(consoleName):
    consolesData = {
        "GB": { "name": "Gameboy", "image": "/static/img/Gameboy.png" },
        "GBA": { "name": "Gameboy Advance", "image": "/static/img/Gameboy Advance.png" },
        "GBC": { "name": "Gameboy Color", "image": "/static/img/Gameboy Color.png" },
        "N64": { "name": "Nintendo 64", "image": "/static/img/N64.png" },
        "NES": { "name": "Nintendo Entertainment System", "image": "/static/img/NES.png" },
        "NDS": { "name": "Nintendo DS", "image": "/static/img/Nintendo DS.png" },
        "SNES": { "name": "Super Nintendo Entertainment System", "image": "/static/img/SNES.png" },
        "Sega Mega Drive": { "name": "Sega Mega Drive", "image": "/static/img/Sega Mega Drive.png" },
        "Sega Master System": { "name": "Sega Master System", "image": "/static/img/Sega Master System.png" },
        "Sega Saturn": { "name": "Sega Saturn", "image": "/static/img/Sega Saturn.png" },
        "PS1": { "name": "PS1", "image": "/static/img/PS1.png" },
    }
    return json.dumps(consolesData[consoleName], ensure_ascii=False, default=str)

consoles = {"Gameboy": "GB", "Gameboy Advance": "GBA", "Gameboy Color": "GBC", "Nintendo 64": "N64", "Nintendo Entertainment System": "NES", "Nintendo DS": "NDS", "Super Nintendo Entertainment System": "SNES", "Sega Mega Drive": "Sega Mega Drive", "Sega Master System": "Sega Master System", "Sega Saturn": "Sega Saturn", "PS1": "PS1"}
        
@app.route("/console/<consoleName>")
@login_required
def console(consoleName):
    if consoleName != "undefined":
        consoleName = consoleName.replace("%20", " ")
        global consoles
        games = Games.query.filter_by(console=consoles[consoleName])
        gamesDict = [ game.__dict__ for game in games ]
        for game in gamesDict:
            del game["_sa_instance_state"]
        searchedGamesUp0 = len(gamesDict) == 0
        errorMessage = "Verify that the games path is correct"
        
        routeToUse = "/getAllGames"
        return render_template("games.html",
            conditionIfOne=searchedGamesUp0,
            errorMessage=errorMessage,
            routeToUse=routeToUse,
            consoleName=consoleName
        )
    else:
        return json.dumps({"response": "Not Found"}, ensure_ascii=False, default=str)

@app.route("/getGames/<consoleName>")
def getGamesFor(consoleName):
    if consoleName != None:
        consoleName = consoleName.replace("%20", " ")
        global consoles
        games = Games.query.filter_by(console=consoles[consoleName]).all()
        gamesDict = [ game.__dict__ for game in games ]
        for game in gamesDict:
            del game["_sa_instance_state"]
        return json.dumps(gamesDict, ensure_ascii=False, default=str)
    else:
        return json.dumps({"response": "Not Found"}, ensure_ascii=False, default=str)

@app.route("/game/<console>/<gameSlug>")
@login_required
def game(console, gameSlug):
    if console != None:
        consoleName = console.replace("%20", " ")
        gameSlug = gameSlug.replace("%20", " ")
        global consoles
        game = Games.query.filter_by(console=consoles[consoleName], realTitle=gameSlug).first()
        game = game.__dict__
        gameFileName, gameExtension = os.path.splitext(gameSlug)
        slug = f"/gameFile/{game['console']}/{game['realTitle']}"
        bios = f"/bios/{consoleName}"
        del game["_sa_instance_state"]
        scripts = {
            "Gameboy": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "";\nEJS_gameUrl = "{slug}";\nEJS_core = "gb";\n</script>',
            "Gameboy Advance": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "";\nEJS_gameUrl = "{slug}";\nEJS_core = "gba";\n</script>',
            "Gameboy Color": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "";\nEJS_gameUrl = "{slug}";\nEJS_core = "gb";\n</script>',
            "Nintendo 64": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_gameUrl = "{slug}";\nEJS_core = "n64";\n</script>',
            "Nintendo Entertainment System": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "";\nEJS_gameUrl = "{slug}";\nEJS_core = "nes";\nEJS_lightgun = false;\n</script>',
            "Nintendo DS": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "";\nEJS_gameUrl = "{slug}";\nEJS_core = "nds";\n</script>',
            "Super Nintendo Entertainment System": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "";\nEJS_gameUrl = "{slug}";\nEJS_core = "snes";\nEJS_mouse = false;\nEJS_multitap = false;\n</script>',
            "Sega Mega Drive": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_gameUrl = "{slug}";\nEJS_core = "segaMD";\n</script>',
            "Sega Master System": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_gameUrl = "{slug}";\nEJS_core = "segaMS";\n</script>',
            "Sega Saturn": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "";\nEJS_gameUrl = "{slug}";\nEJS_core = "segaSaturn";\n</script>',
            "PS1": f'<script type="text/javascript">\nEJS_player = "#game";\nEJS_biosUrl = "{bios}";\nEJS_gameUrl = "{slug}";\nEJS_core = "psx";\n</script>',
        }
        theScript = scripts[consoleName]
        theScript = Markup(theScript)
        return render_template("game.html", script=theScript, gameName=game["title"], consoleName=consoleName)

@app.route("/gameFile/<console>/<gameSlug>")
def gameFile(console, gameSlug):
    if console != None:
        consoleName = console.replace("%20", " ")
        gameSlug = gameSlug.replace("%20", " ")
        game = Games.query.filter_by(console=consoleName, realTitle=gameSlug).first()
        game = game.__dict__
        slug = game["slug"]
        return send_file(slug, as_attachment=True)


@app.route("/PS1binFile/<gameSlug>")
def PS1binFile(gameSlug):
    if gameSlug != None:
        gameDir = config["ChocolateSettings"]["gamespath"]
        ps1Dir = f"{gameDir}/PS1"
        file = f"{ps1Dir}/{gameSlug}"
        return send_file(file, as_attachment=True)

@app.route("/bios/<console>")
def bios(console):
    if console != None:
        consoleName = console.replace("%20", " ")
        Bios = [i for i in os.listdir(f"{dirPath}/static/bios/{consoleName}") if i.endswith(".bin")]
        Bios = f"{dirPath}/static/bios/{consoleName}/{Bios[0]}"

        return send_file(Bios, as_attachment=True)

@app.route("/searchInMovies/<search>")
@login_required
def searchInAllMovies(search):
    movies = []
    points = {}
    #I have one or multiple arguments in a list, I want for each arguments, search in 5 columns of my Movies table, and order by most points
    args = search.split("%20")
    for arg in args:
        movies = Movies.query.filter((Movies.title.like(f"%{arg}%"), Movies.realTitle.like(f"%{arg}%"), Movies.description.like(f"%{arg}%"), Movies.slug.like(f"%{arg}%"), Movies.cast.like(f"%{arg}%"))).all()
        for movie in movies:
            if movie.title in points:
                points[movie.title] += 1
            else:
                points[movie.title] = 1

    for k in points:
        min = points[k]
        for l in points:
            if points[l] < min:
                min = points[l]
        points[k] = min

    points2 = points.copy()
    finalMovieList = []
    for k in sorted(points, key=points.get, reverse=True):
        finalMovieList.append(k)
        del points2[k]
        if len(points2) == 0:
            break

    return json.dumps(finalMovieList, ensure_ascii=False)


@app.route("/searchInSeries/<search>")
@login_required
def searchInAllSeries(search):
    global allSeriesDict
    bestMatchs = {}
    series = []
    points = {}
    for serie in allSeriesDict:
        search = search.replace("%20", " ")
        distance = fuzz.ratio(search, serie["title"])
        points[serie["title"]] = distance

    bestMatchs = sorted(points.items(), key=lambda x: x[1], reverse=True)
    for serie in bestMatchs:
        thisSerie = serie[0]
        for series in allSeriesDict:
            if series["title"] == thisSerie:
                series.append(series)
                break

    return json.dumps(series, ensure_ascii=False)


@app.route("/search/movies/<search>")
@login_required
def searchMovie(search):
    searchedFilmsUp0 = False
    errorMessage = "Verify your search terms"
    routeToUse = f"/searchInMovies/{search}"
    return render_template("allFilms.html",
        conditionIfOne=searchedFilmsUp0,
        errorMessage=errorMessage,
        routeToUse=routeToUse,
    )


@app.route("/search/series/<search>")
@login_required
def searchSerie(search):
    searchedFilmsUp0 = False
    errorMessage = "Verify your search terms"
    routeToUse = f"/searchInSeries/{search}"
    return render_template("allSeries.html",
        conditionIfOne=searchedFilmsUp0,
        errorMessage=errorMessage,
        routeToUse=routeToUse,
    )


@app.route("/movie/<slug>")
@login_required
def movie(slug):
    global movieExtension, searchedFilms
    if not slug.endswith("ttf"):
        rewriteSlug, movieExtension = os.path.splitext(slug)
        link = f"/video/{rewriteSlug}.m3u8".replace(" ", "%20")
        link1080 = f"/video/1080/{rewriteSlug}.m3u8".replace(" ", "%20")
        link720 = f"/video/720/{rewriteSlug}.m3u8".replace(" ", "%20")
        link480 = f"/video/480/{rewriteSlug}.m3u8".replace(" ", "%20")
        link360 = f"/video/360/{rewriteSlug}.m3u8".replace(" ", "%20")
        link240 = f"/video/240/{rewriteSlug}.m3u8".replace(" ", "%20")
        link144 = f"/video/144/{rewriteSlug}.m3u8".replace(" ", "%20")
        allCaptions = generateCaptionMovie(slug)
        title = rewriteSlug
        return render_template(
        "film.html", slug=slug, movieUrl=link, allCaptions=allCaptions, title=title, movieUrl1080=link1080, movieUrl720=link720, movieUrl480=link480, movieUrl360=link360, movieUrl240=link240, movieUrl144=link144)

@app.route("/serie/<episodeId>")
@login_required
def serie(episodeId):
    global allSeriesDict
    if episodeId.endswith("ttf"):
        pass
    else:
        thisEpisode = Episodes.query.filter_by(episodeId=episodeId).first().__dict__
        del thisEpisode["_sa_instance_state"]
        seasonId = thisEpisode["seasonId"]
        slug = thisEpisode["slug"]
        episodeName = thisEpisode["episodeName"]
        slugUrl = slug.split("/")[-1]
        link = f"/videoSerie/{episodeId}.m3u8".replace(" ", "%20")
        link1080 = f"/videoSerie/1080/{episodeId}.m3u8".replace(" ", "%20")
        link720 = f"/videoSerie/720/{episodeId}.m3u8".replace(" ", "%20")
        link480 = f"/videoSerie/480/{episodeId}.m3u8".replace(" ", "%20")
        link360 = f"/videoSerie/360/{episodeId}.m3u8".replace(" ", "%20")
        link240 = f"/videoSerie/240/{episodeId}.m3u8".replace(" ", "%20")
        link144 = f"/videoSerie/144/{episodeId}.m3u8".replace(" ", "%20")
        allCaptions = generateCaptionSerie(episodeId)
        episodeId = int(episodeId)
        season = Seasons.query.filter_by(seasonId=seasonId).first()
        lenOfThisSeason = season.episodesNumber
        buttonNext = episodeId-1 < int(lenOfThisSeason)
        buttonPrevious = episodeId-1 > 0
        thisEpisodeName = thisEpisode["episodeName"].replace("E", "")
        nextEpisodeId = Episodes.query.filter_by(episodeName=f"E{str(int(thisEpisodeName)+1)}").filter_by(seasonId=seasonId).first()
        previousEpisodeId = Episodes.query.filter_by(episodeName=f"E{str(int(thisEpisodeName)-1)}").filter_by(seasonId=seasonId).first()
        buttonPreviousHREF = f"/serie/{nextEpisodeId}"
        buttonNextHREF = f"/serie/{previousEpisodeId}"
        return render_template("serie.html", slug=slug, movieUrl=link, allCaptions=allCaptions, title=episodeName, buttonNext=buttonNext, buttonPrevious=buttonPrevious, buttonNextHREF=buttonNextHREF, buttonPreviousHREF=buttonPreviousHREF, movieUrl1080=link1080, movieUrl720=link720, movieUrl480=link480, movieUrl360=link360, movieUrl240=link240, movieUrl144=link144)
    return "Error"

def generateCaptionSerie(episodeId):
    seriesPath = config.get("ChocolateSettings", "SeriesPath")
    episode = Episodes.query.filter_by(episodeId=episodeId).first()
    episode = episode.__dict__
    slug = episode["slug"]
    slug = f"{seriesPath}\{slug}"
    captionCommand = [
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "s",
        "-show_entries",
        "stream=index:stream_tags=language",
        "-of",
        "csv=p=0",
        slug,
    ]
    captionPipe = subprocess.Popen(captionCommand, stdout=subprocess.PIPE)
    try:
        slug = slug.split("\\")[-1]
        slug = slug.split("/")[-1]
    except:
        slug = slug.split("/")[-1]
    captionResponse = captionPipe.stdout.read().decode("utf-8")
    captionResponse = captionResponse.split("\n")

    allCaptions = []
    languages = {
        "eng": "English",
        "fre": "Français",
        "spa": "Español",
        "por": "Português",
        "ita": "Italiano",
        "ger": "Deutsch",
        "rus": "Русский",
        "pol": "Polski",
        "por": "Português",
        "chi": "中文",
        "srp": "Srpski",
    }

    captionResponse.pop()

    for line in captionResponse:
        line = line.rstrip()
        language = line.split(",")[1]
        index = line.split(",")[0]
        allCaptions.append(
            {
                "index": index,
                "languageCode": language,
                "language": languages[language],
                "url": f"/chunkCaptionSerie/{language}/{index}/{episodeId}.vtt",
            }
        )
    return allCaptions



def generateCaptionMovie(slug):
    captionCommand = [
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "s",
        "-show_entries",
        "stream=index:stream_tags=language",
        "-of",
        "csv=p=0",
        slug,
    ]
    captionPipe = subprocess.Popen(captionCommand, stdout=subprocess.PIPE)
    try:
        slug = slug.split("\\")[-1]
        slug = slug.split("/")[-1]
    except:
        slug = slug.split("/")[-1]
    rewriteSlug, movieExtension = os.path.splitext(slug)
    captionResponse = captionPipe.stdout.read().decode("utf-8")
    captionResponse = captionResponse.split("\n")

    allCaptions = []
    languages = {
        "eng": "English",
        "fre": "Français",
        "spa": "Español",
        "por": "Português",
        "ita": "Italiano",
        "ger": "Deutsch",
        "rus": "Русский",
        "pol": "Polski",
        "por": "Português",
        "chi": "中文",
        "srp": "Srpski",
    }

    captionResponse.pop()
    for line in captionResponse:
        line = line.rstrip()
        try:
            language = line.split(",")[1]
            index = line.split(",")[0]
            allCaptions.append(
                {
                    "index": index,
                    "languageCode": language,
                    "language": languages[language],
                    "url": f"/chunkCaption/{language}/{index}/{rewriteSlug}.vtt",
                }
            )
        except:
            break

    return allCaptions


@app.route("/generateAudio/<slug>")
def generateAudio(slug):
    audioCommand = [
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=index:stream_tags=language",
        "-of",
        "csv=p=0",
        slug,
    ]
    audioPipe = subprocess.Popen(audioCommand, stdout=subprocess.PIPE)
    try:
        slug = slug.split("\\")[-1]
        slug = slug.split("/")[-1]
    except:
        slug = slug.split("/")[-1]
    rewriteSlug, movieExtension = os.path.splitext(slug)
    audioResponse = audioPipe.stdout.read().decode("utf-8")
    audioResponse = audioResponse.split("\n")
    audioResponse.pop()
    allAudio = []
    languages = {
        "eng": "English",
        "fre": "Français",
        "spa": "Español",
        "por": "Português",
        "ita": "Italiano",
        "ger": "Deutsch",
        "rus": "Русский",
        "pol": "Polski",
        "por": "Português",
        "chi": "中文",
        "srp": "Srpski",
    }
    for line in audioResponse:
        line = line.rstrip()
        language = line.split(",")[1]
        index = line.split(",")[0]
        allAudio.append(
            {
                "index": index,
                "languageCode": language,
                "language": languages[language],
                "url": f"/chunkAudio/{language}/{index}/{rewriteSlug}.mp3",
            }
        )

    return allAudio


@app.route("/actor/<actorId>")
@login_required
def actor(actorId):
    routeToUse = f"/getActorData/{actorId}"
    actor = Actors.query.filter_by(actorId=actorId).first()
    actorName = actor.name
    return render_template("actor.html", routeToUse=routeToUse, actorName=actorName)


@app.route("/getActorData/<actorId>", methods=["GET", "POST"])
def getActorData(actorId):
    moviesData = []
    actor = Actors.query.filter_by(actorId=actorId).first()
    movies = actor.actorPrograms.split(" ")
    for movie in movies:
        thisMovie = Movies.query.filter_by(id=movie).first().__dict__
        del thisMovie["_sa_instance_state"]
        moviesData.append(thisMovie)
    actorData = {
        "actorName": actor.name,
        "actorImage": actor.actorImage,
        "actorDescription": actor.actorDescription,
        "actorBirthday": actor.actorBirthDate,
        "actorBirthplace": actor.actorBirthPlace,
        "actorMovies": moviesData,
    }
    return json.dumps(actorData, default=lambda o: o.__dict__, ensure_ascii=False)


@app.route("/sendDiscordPresence/<name>/<actualDuration>/<totalDuration>")
def sendDiscordPresence(name, actualDuration, totalDuration):
    global rpc_obj, activity
    actualDuration = actualDuration
    totalDuration = totalDuration
    newActivity = {
        "state": "Chocolate",  # anything you like
        "details": f"Watching {name} | {actualDuration}/{totalDuration}",  # anything you like
        "assets": {
            "small_text": "Chocolate",  # anything you like
            "small_image": "None",  # must match the image key
            "large_text": "Chocolate",  # anything you like
            "large_image": "largeimage",  # must match the image key
        },
    }
    enabledRPC = config["ChocolateSettings"]["discordrpc"]
    if enabledRPC == "true":
        try:
            rpc_obj.set_activity(newActivity)
        except:
            try:
                client_id = "771837466020937728"
                rpc_obj = rpc.DiscordIpcClient.for_platform(client_id)
                
                activity = {
                    "state": "Chocolate",  # anything you like
                    "details": "The all-in-one MediaManager",  # anything you like
                    "timestamps": {"start": start_time},
                    "assets": {
                        "small_text": "Chocolate",  # anything you like
                        "small_image": "None",  # must match the image key
                        "large_text": "Chocolate",  # anything you like
                        "large_image": "largeimage",  # must match the image key
                    },
                }
                rpc_obj.set_activity(activity)
            except OSError:
                enabledRPC == "false"
                config.set("ChocolateSettings", "discordrpc", "false")
                with open(os.path.join(dir, 'config.ini'), "w") as conf:
                    config.write(conf)
    return json.dumps(
        f"You sent richPresence Data with this informations : name:{name}, actualDuration:{actualDuration}, totalDuration:{totalDuration}"
    )

@app.route("/getThisEpisodeData/<episodeID>", methods=["GET", "POST"])
def getThisEpisodeData(episodeID):
    episode = Episodes.query.filter_by(episodeId=episodeID).first()
    episodeData = {
        "episodeName": episode.episodeName,
        "introStart": episode.introStart,
        "introEnd": episode.introEnd,
    }
    return json.dumps(episodeData, default=lambda o: o.__dict__, ensure_ascii=False)


@app.route("/scanIntro")
def scanIntro():
    os.system("python intro.py")
    return redirect(url_for("settings"))


def sort_dict_by_key(unsorted_dict):

    sorted_keys = sorted(unsorted_dict.keys(), key=lambda x:x.lower())

    sorted_dict= {}
    for key in sorted_keys:
        sorted_dict.update({key: unsorted_dict[key]})

    return sorted_dict
        

if __name__ == "__main__":
    enabledRPC = config["ChocolateSettings"]["discordrpc"]
    if enabledRPC == "true":
        activity = {
            "state": "Loading Chocolate...",  # anything you like
            "details": "The all-in-one MediaManager",  # anything you like
            "timestamps": {"start": start_time},
            "assets": {
                "small_text": "Chocolate",  # anything you like
                "small_image": "None",  # must match the image key
                "large_text": "Chocolate",  # anything you like
                "large_image": "loader",  # must match the image key
            },
        }
        try:
            rpc_obj.set_activity(activity)
        except:
            pass
    #get all Libraries
    with app.app_context():
        libraries = Libraries.query.all()
        for library in libraries:
            if library.libType == "series":
                getSeries(library.libName)
            elif library.libType == "movies":
                getMovies(library.libName)
            elif library.libType == "games":
                getGames(library.libName)

    print()
    print("\033[?25h", end="")
    
    enabledRPC = config["ChocolateSettings"]["discordrpc"]
    if enabledRPC == "true":
        activity = {
            "state": "Chocolate",  # anything you like
            "details": "The all-in-one MediaManager",  # anything you like
            "timestamps": {"start": start_time},
            "assets": {
                "small_text": "Chocolate",  # anything you like
                "small_image": "None",  # must match the image key
                "large_text": "Chocolate",  # anything you like
                "large_image": "largeimage",  # must match the image key
            },
        }
        try:
            rpc_obj.set_activity(activity)
        except:
            pass

    with app.app_context():
        allSeriesDict = {}
        for u in db.session.query(Series).all():
            allSeriesDict[u.name] = u.__dict__

    app.run(host="0.0.0.0", port=serverPort, use_reloader=False, debug=True)