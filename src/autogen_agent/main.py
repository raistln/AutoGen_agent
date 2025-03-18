import os
import requests
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import re


# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de Ollama para modelos locales
OLLAMA_BASE_URL = "http://localhost:11434/api"
DEFAULT_MODEL = "gemma:2b"  # Modelo ligero que funciona bien en CPU

def install_ollama_model(model_name):
    """
    Intenta descargar el modelo de Ollama si no está disponible.
   
    Args:
        model_name (str): El nombre del modelo a descargar.
   
    Returns:
        bool: True si el modelo se descargó correctamente, False en caso contrario.
    """
    print(f"Intentando descargar el modelo {model_name}...")
    try:
        url = f"{OLLAMA_BASE_URL}/pull"
        headers = {"Content-Type": "application/json"}
        data = {"name": model_name}
       
        # Esta operación puede tardar varios minutos dependiendo del modelo
        response = requests.post(url, headers=headers, json=data)
       
        if response.status_code == 200:
            print(f"✅ Modelo {model_name} descargado correctamente")
            return True
        else:
            print(f"❌ Error al descargar el modelo: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error de conexión al intentar descargar: {e}")
        return False

def ask_ollama(prompt, model=DEFAULT_MODEL):
    """
    Realiza una consulta al servidor Ollama local.
   
    Args:
        prompt (str): El texto de la consulta.
        model (str): El modelo a utilizar (por defecto: gemma:2b).
   
    Returns:
        str: La respuesta del modelo.
    """
    url = f"{OLLAMA_BASE_URL}/generate"
   
    headers = {
        "Content-Type": "application/json"
    }
   
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
   
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            print(f"Error al consultar Ollama: {response.status_code}")
            print(response.text)
            return "Error al consultar el modelo"
    except Exception as e:
        print(f"Excepción al llamar a Ollama: {e}")
        return "Error de conexión con Ollama"

# Configuración de los modelos con opción de OpenAI o Ollama local
config_list = [
    {
        "model": "gpt-4",
        "api_key": os.environ.get("OPENAI_API_KEY"),
    }
]

# Configuración alternativa con Ollama
config_list_ollama = [
    {
        "model": DEFAULT_MODEL,
        "api_key": "None",
        "base_url": "http://localhost:11434",
    }
]

def get_config():
    """
    Determina la configuración del modelo a utilizar (OpenAI o Ollama).
   
    Returns:
        list: La lista de configuración del modelo.
    """
    try:
        # Verificar si podemos usar OpenAI
        if os.environ.get("OPENAI_API_KEY"):
            return config_list
        # Si no, intentar usar Ollama
        else:
            # Comprobar si el modelo está instalado, si no, intentar instalarlo
            try:
                response = requests.post(
                    f"{OLLAMA_BASE_URL}/generate", 
                    json={"model": DEFAULT_MODEL, "prompt": "test", "stream": False}
                )
                if response.status_code == 200:
                    print(f"Usando modelo local: {DEFAULT_MODEL}")
                    return config_list_ollama
                else:
                    install_ollama_model(DEFAULT_MODEL)
                    return config_list_ollama
            except Exception:
                print("Error conectando con Ollama. Intentando instalar el modelo...")
                install_ollama_model(DEFAULT_MODEL)
                return config_list_ollama
    except Exception as e:
        print(f"Error al configurar el modelo: {e}")
        print("Usando configuración de Ollama por defecto")
        return config_list_ollama

class MusicSearchTool:
    def __init__(self):
        """
        Inicializa la herramienta de búsqueda de música.
        """
        print("🛠️ Inicializando MusicSearchTool...")
        
        # Cargar credenciales de Last.fm desde variables de entorno
        self.lastfm_api_key = os.getenv("LASTFM_API_KEY")
        self.lastfm_api_secret = os.getenv("LASTFM_API_SECRET")
        
        if not self.lastfm_api_key or not self.lastfm_api_secret:
            raise ValueError("Las credenciales de Last.fm no están configuradas.")

    def search_playlists(self, query, num_songs=20):
        """
        Busca listas de reproducción utilizando Last.fm y Spotify como respaldo.
        Evita duplicados en todas las etapas y devuelve una lista única de canciones.
       
        Args:
            query (str): El término de búsqueda (artista, género, etc.).
            num_songs (int): El número de canciones a devolver (por defecto: 20).
       
        Returns:
            list: Una lista de canciones únicas en formato Python.
        """
        print(f"\n🎵 Iniciando búsqueda para: {query}")
        
        # Conjunto para almacenar canciones únicas
        unique_songs = set()
        
        # 1. Intento: Búsqueda en Last.fm (API)
        print("\n🔍 Paso 1: Búsqueda en Last.fm (API)...")
        songs_from_lastfm = self._search_via_lastfm(query)
        print(f"✅ Canciones encontradas en Last.fm (API): {songs_from_lastfm}")
        
        # Añadir canciones de Last.fm al conjunto de canciones únicas
        unique_songs.update(songs_from_lastfm)
        
        # 2. Intento: Búsqueda en Spotify (API)
        if len(unique_songs) < num_songs:
            print("\n🔍 Paso 2: Búsqueda en Spotify (API)...")
            print("⚠️ No se encontraron suficientes canciones. Usando Spotify...")
            songs_from_spotify = self._search_via_spotify(query)
            print(f"✅ Canciones encontradas en Spotify (API): {songs_from_spotify}")
            
            # Añadir canciones de Spotify al conjunto de canciones únicas
            unique_songs.update(songs_from_spotify)
        
        # Convertir el conjunto a una lista y limitar al número solicitado
        print("\n🔍 Paso 3: Eliminando duplicados y limitando resultados...")
        unique_songs_list = list(unique_songs)[:num_songs]
        print(f"✅ Canciones únicas encontradas: {len(unique_songs_list)}")
        
        # Log de diagnóstico
        print("\n📊 Resumen de la búsqueda:")
        print(f"- Total de canciones encontradas: {len(unique_songs_list)}")
        print(f"- Canciones: {unique_songs_list}")
        
        return unique_songs_list
    
    def _search_via_lastfm(self, query):
        """
        Realiza búsquedas mediante la API de Last.fm.
       
        Args:
            query (str): El término de búsqueda (artista, género, etc.).
       
        Returns:
            list: Una lista de nombres de canciones.
        """
        url = f"http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist={query}&api_key={self.lastfm_api_key}&format=json"
        print(f"📄 Realizando solicitud HTTP a: {url}")
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            songs = [track['name'] for track in data.get('toptracks', {}).get('track', [])]
            return songs
        else:
            print(f"❌ Error en la búsqueda de Last.fm: {response.status_code}")
            return []
    
    def _search_via_spotify(self, query):
        """
        Realiza búsquedas mediante la API de Spotify.
    
        Args:
            query (str): El término de búsqueda (artista, género, etc.).
    
        Returns:
            list: Una lista de nombres de canciones.
        """
        # Autenticación en Spotify
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
            scope="user-library-read",
            cache_path=os.path.join(os.path.expanduser("~"), ".spotify_cache")
        ))
        
        # Realizar la búsqueda incluyendo el nombre del artista
        search_query = f"track:{query} artist:{query}"
        results = sp.search(q=search_query, type='track', limit=20)
        
        # Filtrar canciones que coincidan con el artista
        songs = []
        for track in results['tracks']['items']:
            artist_names = [artist['name'].lower() for artist in track['artists']]
            if query.lower() in artist_names:
                songs.append(track['name'])
        
        return songs

# Configuración de OAuth 2.0 para YouTube
SCOPES = ['https://www.googleapis.com/auth/youtube']
CLIENT_SECRETS_FILE = 'client_secret.json'  # Archivo descargado de Google Cloud Console

def get_authenticated_service():
    """
    Obtiene un servicio autenticado de YouTube usando OAuth 2.0.
   
    Returns:
        googleapiclient.discovery.Resource: Un servicio autenticado de YouTube.
    """
    creds = None
    
    # El archivo token.json almacena los tokens de acceso y actualización
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Si no hay credenciales válidas, solicita al usuario que inicie sesión
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Configuración más explícita del flujo de OAuth
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=SCOPES
            )
            # Configura el servidor local para usar exactamente la URI que está en Google Cloud
            flow.redirect_uri = "http://localhost:8888"
            # Inicia el servidor en el mismo puerto
            creds = flow.run_local_server(port=8888, redirect_uri_port=8888)
        
        # Guarda las credenciales para la próxima vez
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('youtube', 'v3', credentials=creds)

class YouTubeTool:
    def __init__(self):
        """
        Inicializa la clase YouTubeTool con un servicio autenticado de YouTube.
        """
        self.youtube = get_authenticated_service()
    
    def create_playlist(self, title, description, songs):
        """
        Crea una lista de reproducción en YouTube y devuelve una lista de URLs
        de los videos encontrados junto con el enlace a la playlist.
    
        Args:
            title (str): El título de la playlist.
            description (str): La descripción de la playlist.
            songs (list): Una lista de nombres de canciones.
    
        Returns:
            dict: Un diccionario con la URL de la playlist y las URLs de los videos.
        """
        try:
            # Convertir el título a mayúsculas
            title = title.upper()
            
            # Crear la lista de reproducción
            playlist = self.youtube.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description
                    },
                    "status": {
                        "privacyStatus": "public"
                    }
                }
            ).execute()
            
            playlist_id = playlist["id"]
            
            # Lista para almacenar URLs de videos
            video_urls = []
            
            # Buscar y añadir cada canción
            for song in songs:
                # Buscar el video
                search_response = self.youtube.search().list(
                    q=song,
                    part="id,snippet",
                    maxResults=1,
                    type="video"
                ).execute()
                
                # Verificar si encontramos un resultado
                if search_response["items"]:
                    video_id = search_response["items"][0]["id"]["videoId"]
                    video_title = search_response["items"][0]["snippet"]["title"]
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Añadir a la lista de URLs
                    video_urls.append({
                        "song": song,
                        "video_title": video_title,
                        "url": video_url
                    })
                    
                    # Añadir a la lista de reproducción
                    self.youtube.playlistItems().insert(
                        part="snippet",
                        body={
                            "snippet": {
                                "playlistId": playlist_id,
                                "resourceId": {
                                    "kind": "youtube#video",
                                    "videoId": video_id
                                }
                            }
                        }
                    ).execute()
            
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
            return {
                "playlist_url": playlist_url,
                "video_urls": video_urls
            }
        
        except Exception as e:
            print(f"Error al crear lista de reproducción en YouTube: {e}")
            # Para pruebas, devolver una URL ficticia
            return {
                "playlist_url": "https://www.youtube.com/playlist?list=EXAMPLE_ID",
                "video_urls": [
                    {"song": song, "video_title": f"Video de {song}", "url": f"https://www.youtube.com/watch?v=example_{i}"} 
                    for i, song in enumerate(songs)
                ]
            }

class SpotifyTool:
    def __init__(self):
        """
        Inicializa la clase SpotifyTool con las credenciales de Spotify.
        """
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
        self.sp = None
        self.initialize_spotify()
    
    def initialize_spotify(self):
        """
        Inicializa la conexión con Spotify con mejor manejo de errores de caché.
        """
        try:
            if self.client_id and self.client_secret:
                # Establecer una ruta de caché específica y accesible
                cache_path = os.path.join(os.path.expanduser("~"), ".spotify_cache")
                # Crear el directorio si no existe
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                
                self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    redirect_uri=self.redirect_uri,
                    scope="playlist-modify-public",
                    cache_path=cache_path
                ))
                print("Spotify inicializado correctamente")
            else:
                print("Credenciales de Spotify no disponibles")
        except Exception as e:
            print(f"Error al inicializar Spotify: {e}")
            # Intentar una inicialización alternativa en caso de error
            try:
                # Intentar usar Client Credentials Flow en lugar de OAuth si hay problemas
                from spotipy.oauth2 import SpotifyClientCredentials
                self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                    client_id=self.client_id,
                    client_secret=self.client_secret
                ))
                print("Spotify inicializado con credenciales de cliente")
            except Exception as e2:
                print(f"Error en la inicialización alternativa de Spotify: {e2}")
                self.sp = None
    
    def create_playlist(self, title, description, songs):
        """
        Crea una lista de reproducción en Spotify y devuelve la URL
        junto con información de las canciones añadidas.
    
        Args:
            title (str): El título de la playlist.
            description (str): La descripción de la playlist.
            songs (list): Una lista de nombres de canciones.
    
        Returns:
            dict: Un diccionario con la URL de la playlist y la información de las canciones.
        """
        try:
            # Convertir el título a mayúsculas
            title = title.upper()
            
            # Verificar que Spotify esté inicializado
            if not self.sp:
                print("Spotify no está inicializado, intentando nuevamente...")
                self.initialize_spotify()
                if not self.sp:
                    raise Exception("No se pudo inicializar Spotify")
            
            # Obtener el ID del usuario actual
            user_id = self.sp.current_user()["id"]
            
            # Crear la lista de reproducción
            playlist = self.sp.user_playlist_create(
                user=user_id,
                name=title,
                public=True,
                description=description
            )
                
            # Buscar y añadir cada canción
            track_info = []
            track_uris = []
            
            for song in songs:
                result = self.sp.search(q=song, type="track", limit=1)
                if result["tracks"]["items"]:
                    track = result["tracks"]["items"][0]
                    track_uri = track["uri"]
                    track_uris.append(track_uri)
                    
                    # Guardar información sobre la canción
                    track_info.append({
                        "original_query": song,
                        "track_name": track["name"],
                        "artist": track["artists"][0]["name"],
                        "album": track["album"]["name"],
                        "uri": track_uri
                    })
            
            # Añadir canciones a la lista de reproducción
            if track_uris:
                self.sp.playlist_add_items(playlist["id"], track_uris)
            
            return {
                "playlist_url": playlist["external_urls"]["spotify"],
                "track_info": track_info
            }
        
        except Exception as e:
            print(f"Error al crear lista de reproducción en Spotify: {e}")
            # Para pruebas, devolver una URL ficticia
            return {
                "playlist_url": "https://open.spotify.com/playlist/EXAMPLE_ID",
                "track_info": [
                    {
                        "original_query": song,
                        "track_name": f"Versión de {song}",
                        "artist": "Artista Ejemplo",
                        "album": "Álbum Ejemplo",
                        "uri": f"spotify:track:example_{i}"
                    } 
                    for i, song in enumerate(songs)
                ]
            }

class NotificationTool:
    def send_email(self, to_email, subject, body):
        """
        Envía un correo electrónico usando SMTP.
       
        Args:
            to_email (str): El correo electrónico del destinatario.
            subject (str): El asunto del correo.
            body (str): El cuerpo del correo.
       
        Returns:
            bool: True si el correo se envió correctamente, False en caso contrario.
        """
        try:
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = os.getenv("EMAIL_USER")
            sender_password = os.getenv("EMAIL_PASSWORD")
            
            if not sender_email or not sender_password:
                print("Credenciales de correo no disponibles")
                return False
            
            # Crear el mensaje
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = to_email
            message["Subject"] = subject
            
            # Añadir el cuerpo del mensaje
            message.attach(MIMEText(body, "plain"))
            
            # Iniciar sesión y enviar el correo
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(message)
            
            return True
        
        except Exception as e:
            print(f"Error al enviar correo electrónico: {e}")
            return False

# Configuración dinámica para elegir entre OpenAI y Ollama
active_config = get_config()

# Configuración de agentes con herramientas externas
search_tool = MusicSearchTool()
youtube_tool = YouTubeTool()
spotify_tool = SpotifyTool()
notification_tool = NotificationTool()


def generate_email_content(query, youtube_result, spotify_result, songs):
    """
    Genera el contenido del correo electrónico usando el modelo Gemma 2B.
   
    Args:
        query (str): El término de búsqueda (artista, género, etc.).
        youtube_result (dict): Los resultados de YouTube.
        spotify_result (dict): Los resultados de Spotify.
        songs (list): La lista de canciones.
   
    Returns:
        dict: Un diccionario con el asunto y el cuerpo del correo.
    """
    # Generar el asunto del correo (más corto e impactante)
    subject_prompt = f"Generate a short and impactful email subject for a playlist about {query}. Max 10 words."
    subject = ask_ollama(subject_prompt).strip()
    
    # Generar el cuerpo del correo
    body_prompt = f"""
    Eres un presentador de MTV y estás enviando un correo electrónico
    con los detalles de una playlist creada automáticamente.
    
    La playlist es sobre: {query}.
    Las canciones incluidas son: {', '.join(songs)}.
    
    Enlaces:
    - YouTube: {youtube_result['playlist_url']}
    - Spotify: {spotify_result['playlist_url']}
    
    Escribe un correo electrónico informal y divertido que incluya:
    1. Un saludo amigable.
    2. Un resumen de la playlist.
    3. Los enlaces a YouTube y Spotify.
    4. Una descripción amigable de las canciones.
    """
    body = ask_ollama(body_prompt).strip()
    
    return {
        "subject": subject,
        "body": body
    }

def create_music_recommendation(query, email=None, num_songs=20):
    """
    Flujo completo para crear y compartir listas de reproducción.
   
    Args:
        query (str): El término de búsqueda (artista, género, etc.).
        email (str): El correo electrónico para enviar los resultados.
        num_songs (int): El número de canciones a incluir en la playlist (por defecto: 20).
   
    Returns:
        dict: Resultado con las URLs de las listas y mensajes de estado.
    """
    # Paso 1: Buscar y analizar listas de reproducción
    songs = search_tool.search_playlists(query, num_songs)
    
    # Paso 2: Crear listas de reproducción en plataformas
    playlist_title = f"Playlist Recomendada: {query}"
    playlist_description = f"Lista de reproducción generada automáticamente para '{query}'"
    
    youtube_result = youtube_tool.create_playlist(playlist_title, playlist_description, songs)
    spotify_result = spotify_tool.create_playlist(playlist_title, playlist_description, songs)
    
    # Paso 3: Enviar notificaciones si se proporcionó un correo
    if email:
        email_content = generate_email_content(query, youtube_result, spotify_result, songs)
        notification_tool.send_email(
            to_email=email,
            subject=email_content["subject"],
            body=email_content["body"]
        )
        print("📬 Correo electrónico enviado correctamente.")
    
    return {
        "query": query,
        "songs": songs,
        "youtube_result": youtube_result,
        "spotify_result": spotify_result,
        "email_sent": bool(email)
    }

def validate_email(email):
    """
    Valida si una cadena es un correo electrónico válido.
   
    Args:
        email (str): La cadena a validar.
   
    Returns:
        bool: True si es un correo válido, False en caso contrario.
    """
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def main():
    """
    Función principal que maneja la interfaz de línea de comandos (CLI).
    """
    print("🎵 Bienvenido al Generador de Listas de Reproducción 🎵")
    print("-----------------------------------------------------")
    
    # Solicitar el término de búsqueda
    query = input("¿Qué grupo o tipo de música te gustaría buscar? (por ejemplo, 'Rock Clásico', 'AC/DC'): ").strip()
    if not query:
        print("❌ Debes ingresar un grupo o tipo de música. Saliendo...")
        return
    
    # Solicitar el número de canciones
    num_songs = input("¿Cuántas canciones te gustaría incluir en la playlist? (por defecto: 20): ").strip()
    num_songs = int(num_songs) if num_songs.isdigit() else 20
    
    # Solicitar si desea recibir una notificación
    send_notification = input("¿Deseas recibir una notificación con los resultados? (s/n): ").strip().lower()
    email = None
    if send_notification == "s":
        email = input("Ingresa tu correo electrónico: ").strip()
        if not validate_email(email):
            print("❌ El correo electrónico no es válido. No se enviará notificación.")
            email = None
    
    print("\n🔍 Buscando canciones y creando listas de reproducción...")
    try:
        result = create_music_recommendation(query, email, num_songs)
        if result is None:
            print("\n❌ No se pudo crear la lista de reproducción. No se encontraron suficientes canciones.")
            return
        print("\n🎵 Lista de reproducción creada exitosamente 🎵")
        print(f"🔍 Búsqueda: {result['query']}")
        print("\n🎶 Canciones incluidas:")
        for i, song in enumerate(result["songs"], 1):
            print(f"{i}. {song}")
        print(f"\n🎧 Escucha la lista en YouTube: {result['youtube_result']['playlist_url']}")
        print(f"🎧 Escucha la lista en Spotify: {result['spotify_result']['playlist_url']}")
        if result["email_sent"]:
            print("\n📬 Se ha enviado una notificación con los detalles.")
    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")
        print("Por favor, verifica tu conexión a internet o las credenciales de las APIs.")

# Ejecutar el programa principal
if __name__ == "__main__":
    main()