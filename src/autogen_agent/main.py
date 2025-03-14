from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
import os
import json
import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de Ollama para modelos locales
OLLAMA_BASE_URL = "http://localhost:11434/api"
DEFAULT_MODEL = "gemma:2b"  # Modelo ligero que funciona bien en CPU
# Alternativas: orca-mini:3b, llama2:7b, phi2:3b

def install_ollama_model(model_name):
    """Intenta descargar el modelo de Ollama si no está disponible"""
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
    Realiza una consulta al servidor Ollama local
   
    Args:
        prompt: El texto de la consulta
        model: El modelo a utilizar
       
    Returns:
        str: La respuesta del modelo
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

# Función para determinar qué configuración usar
def get_config():
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

# Clase para manejar la búsqueda en internet usando DuckDuckGo
class DuckDuckGoSearchTool:
    def search_playlists(self, query):
        """Busca listas de reproducción usando DuckDuckGo y un modelo de lenguaje (LLM)"""
        print(f"Buscando listas de reproducción para: {query}")
        
        try:
            # Realiza una búsqueda en DuckDuckGo
            search_query = f"{query} playlist top songs"
            url = f"https://api.duckduckgo.com/?q={search_query}&format=json"
            response = requests.get(url)
            results = response.json()
            
            # Extrae los textos de los resultados
            texts = []
            topics = results.get('RelatedTopics', [])
            for topic in topics:
                if 'Text' in topic:
                    texts.append(topic['Text'])
            
            # Si no hay suficientes resultados, usa el respaldo
            if len(texts) < 3:
                return self._fallback_search(query)
            
            # Envía los textos al LLM para extraer canciones
            prompt = f"""
            A continuación se muestran los resultados de una búsqueda sobre '{query}'. 
            Extrae una lista de las 10 canciones más relevantes. Devuélvelo como una lista de Python, por ejemplo: ['Canción 1', 'Canción 2', ...]
            
            Resultados de la búsqueda:
            {texts}
            """
            response = ask_ollama(prompt)  # Usa el LLM local (Ollama) o GPT-4
            
            # Extrae la lista de canciones de la respuesta del LLM
            songs = self._parse_llm_response(response)
            
            # Si no encontramos suficientes canciones, usamos el respaldo
            if len(songs) < 5:
                return self._fallback_search(query)
            
            return {
                "playlists": [
                    {
                        "title": f"Top canciones de {query} (DuckDuckGo + LLM)",
                        "songs": songs
                    }
                ]
            }
            
        except Exception as e:
            print(f"Error en la búsqueda de DuckDuckGo o al consultar el LLM: {e}")
            return self._fallback_search(query)
        
    def _parse_llm_response(self, response):
        """
        Extrae la lista de canciones de la respuesta del LLM.
        La respuesta debe ser una lista de Python, por ejemplo: ['Canción 1', 'Canción 2', ...]
        """
        try:
            # Busca la lista en la respuesta (puede estar entre ```python ``` o ser una lista directa)
            if "```python" in response:
                # Extrae el contenido entre ```python ```
                start = response.find("```python") + len("```python")
                end = response.find("```", start)
                list_str = response[start:end].strip()
            else:
                # Asume que la respuesta es una lista directa
                list_str = response.strip()
            
            # Convierte la cadena en una lista de Python
            songs = eval(list_str)
            if isinstance(songs, list):
                return songs[:10]  # Limita a 10 canciones
            else:
                raise ValueError("La respuesta no es una lista válida")
        
        except Exception as e:
            print(f"Error al parsear la respuesta del LLM: {e}")
            return []
        
    def _fallback_search(self, query):
        """Proporciona resultados de respaldo en caso de fallo"""
        print("Usando búsqueda de respaldo")
        # Datos de ejemplo - se utilizan cuando la búsqueda real falla
        if "ac/dc" in query.lower():
            return {
                "playlists": [
                    {
                        "title": "Los mejores éxitos de AC/DC",
                        "songs": ["Back in Black", "Highway to Hell", "Thunderstruck", 
                                 "You Shook Me All Night Long", "Hells Bells"]
                    }
                ]
            }
        elif "rock" in query.lower():
            return {
                "playlists": [
                    {
                        "title": "Rock Clásico",
                        "songs": ["Sweet Child O' Mine", "Welcome to the Jungle", 
                                 "Livin' on a Prayer", "Final Countdown", "Jump"]
                    }
                ]
            }
        else:
            # Búsqueda genérica de respaldo
            return {
                "playlists": [
                    {
                        "title": f"Playlist de {query}",
                        "songs": [f"Canción 1 de {query}", f"Canción 2 de {query}", 
                                 f"Canción 3 de {query}", f"Canción 4 de {query}", 
                                 f"Canción 5 de {query}"]
                    }
                ]
            }

# Configuración de OAuth 2.0 para YouTube
SCOPES = ['https://www.googleapis.com/auth/youtube']
CLIENT_SECRETS_FILE = 'client_secret.json'  # Archivo descargado de Google Cloud Console

def get_authenticated_service():
    """Obtiene un servicio autenticado de YouTube usando OAuth 2.0"""
    creds = None
    
    # El archivo token.json almacena los tokens de acceso y actualización
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Si no hay credenciales válidas, solicita al usuario que inicie sesión
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=SCOPES,
                redirect_uri="http://127.0.0.1:8888/callback"  # Usar 127.0.0.1 en lugar de localhost
            )
            creds = flow.run_local_server(port=0)
        
        # Guarda las credenciales para la próxima vez
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('youtube', 'v3', credentials=creds)

# Clase para interactuar con YouTube
class YouTubeTool:
    def __init__(self):
        self.youtube = get_authenticated_service()
    
    def create_playlist(self, title, description, songs):
        """
        Crea una lista de reproducción en YouTube y devuelve una lista de URLs
        de los videos encontrados junto con el enlace a la playlist
        """
        try:
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

# Clase para interactuar con Spotify
class SpotifyTool:
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
        self.sp = None
        self.initialize_spotify()
    
    def initialize_spotify(self):
        """Inicializa la conexión con Spotify si las credenciales están disponibles"""
        try:
            if self.client_id and self.client_secret:
                self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    redirect_uri=self.redirect_uri,
                    scope="playlist-modify-public"
                ))
                print("Spotify inicializado correctamente")
            else:
                print("Credenciales de Spotify no disponibles")
        except Exception as e:
            print(f"Error al inicializar Spotify: {e}")
    
    def create_playlist(self, title, description, songs):
        """
        Crea una lista de reproducción en Spotify y devuelve la URL
        junto con información de las canciones añadidas
        """
        try:
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

# Clase para enviar notificaciones
class NotificationTool:
    def send_email(self, to_email, subject, body):
        """Envía un correo electrónico"""
        try:
            # Configuración del servidor de correo
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = os.getenv("EMAIL_USER")
            sender_password = os.getenv("EMAIL_PASSWORD")
            
            # Verificar que las credenciales estén disponibles
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
    
    def send_whatsapp(self, phone_number, message):
        """
        Envía un mensaje de WhatsApp usando la API de WhatsApp Business
        Nota: Esto requeriría una cuenta de WhatsApp Business API
        """
        # En una implementación real, aquí usarías la API de WhatsApp Business
        # Este es un ejemplo simplificado
        print(f"Enviando mensaje de WhatsApp a {phone_number}: {message}")
        return True

# Configuración dinámica para elegir entre OpenAI y Ollama
active_config = get_config()

# Configuración de agentes con herramientas externas
search_tool = DuckDuckGoSearchTool()
youtube_tool = YouTubeTool()
spotify_tool = SpotifyTool()
notification_tool = NotificationTool()

# Agente de Búsqueda en Internet
search_agent = AssistantAgent(
    name="search_agent",
    llm_config={"config_list": active_config},
    system_message="""
    Eres un agente especializado en buscar listas de reproducción en internet.
    Tu tarea es encontrar las canciones más populares según el género o artista solicitado,
    y crear una lista consolidada de las canciones. Debes utilizar la API de DuckDuckGo
    para buscar listas de reproducción, tops de canciones o videos.
    
    Tu salida DEBE ser una lista de Python con los títulos de las canciones,
    para que otros agentes puedan utilizarla directamente.
    
    Ejemplo de salida:
    ```python
    ["Canción 1", "Canción 2", "Canción 3", "Canción 4", "Canción 5"]
    ```
    """
)

# Agente de YouTube
youtube_agent = AssistantAgent(
    name="youtube_agent",
    llm_config={"config_list": active_config},
    system_message="""
    Eres un agente especializado en crear listas de reproducción en YouTube.
    Tu tarea es tomar una lista de canciones proporcionada por el agente de búsqueda,
    y utilizar la API de YouTube para buscar cada canción y añadirla a una lista de reproducción.
    
    Debes devolver:
    1. La URL de la lista de reproducción creada
    2. Una lista de las URLs de los videos individuales
    
    Formato de salida:
    ```python
    {
        "playlist_url": "URL_de_la_playlist",
        "video_urls": [
            {"song": "Título original", "video_title": "Título del video", "url": "URL_del_video"},
            ...
        ]
    }
    ```
    """
)

# Agente de Spotify
spotify_agent = AssistantAgent(
    name="spotify_agent",
    llm_config={"config_list": active_config},
    system_message="""
    Eres un agente especializado en crear listas de reproducción en Spotify.
    Tu tarea es tomar una lista de canciones proporcionada por el agente de búsqueda,
    y utilizar la API de Spotify para buscar cada canción y añadirla a una lista de reproducción.
    
    Debes devolver:
    1. La URL de la lista de reproducción creada
    2. Información detallada sobre las canciones añadidas
    
    Formato de salida:
    ```python
    {
        "playlist_url": "URL_de_la_playlist",
        "track_info": [
            {
                "original_query": "Consulta original",
                "track_name": "Nombre de la canción en Spotify",
                "artist": "Nombre del artista",
                "album": "Nombre del álbum",
                "uri": "URI de Spotify"
            },
            ...
        ]
    }
    ```
    """
)

# Agente de Notificaciones
notification_agent = AssistantAgent(
    name="notification_agent",
    llm_config={"config_list": active_config},
    system_message="""
    Eres un agente especializado en enviar notificaciones.
    Tu tarea es enviar mensajes por correo electrónico o WhatsApp
    con enlaces a listas de reproducción y una descripción amigable.
    """
)

# Agente Coordinador con capacidad de ejecución de código
coordinator = UserProxyAgent(
    name="coordinator",
    human_input_mode="NEVER",
    code_execution_config={"work_dir": "coding"},
    system_message="""
    Eres el coordinador principal del sistema de recomendación musical.
    Tu trabajo es:
    1. Recibir solicitudes de usuarios sobre listas de reproducción
    2. Delegar tareas a los agentes especializados
    3. Recopilar y procesar resultados
    4. Entregar el producto final al usuario
    
    Debes coordinar el flujo completo, asegurándote de que:
    - El agente de búsqueda use DuckDuckGo para encontrar canciones y genere una lista de Python
    - El agente de YouTube use la API para buscar cada título y crear una lista de reproducción
    - El agente de Spotify use la API para crear una lista de reproducción a partir de los resultados
    """
)

# Función de flujo principal
def create_music_recommendation(query, email=None, phone=None):
    """
    Flujo completo para crear y compartir listas de reproducción
    """
    # Paso 1: Buscar y analizar listas de reproducción
    print(f"Iniciando búsqueda para: {query}")
    search_results = search_tool.search_playlists(query)
    
    # Extraer canciones de los resultados
    songs = []
    for playlist in search_results["playlists"]:
        songs.extend(playlist["songs"])
    
    # Eliminar duplicados y limitar a 10 canciones
    selected_songs = list(dict.fromkeys(songs))[:10]
    
    print(f"Canciones seleccionadas: {selected_songs}")
    
    # Paso 2: Crear listas de reproducción en plataformas
    playlist_title = f"Playlist Recomendada: {query}"
    playlist_description = f"Lista de reproducción generada automáticamente para '{query}'"
    
    # Crear en YouTube (comentado para pruebas de Spotify)
    youtube_result = youtube_tool.create_playlist(
        title=playlist_title,
        description=playlist_description,
        songs=selected_songs
    )
    
    # Crear en Spotify
    spotify_result = spotify_tool.create_playlist(
        title=playlist_title,
        description=playlist_description,
        songs=selected_songs
    )
    
    # Paso 3: Enviar notificaciones si se proporcionaron datos de contacto
    notification_sent = False
    
    # Crear mensaje con información detallada
    message_body = f"""
    ¡Hola! Tu lista de reproducción para "{query}" está lista.
    
    Canciones incluidas:
    {', '.join(selected_songs)}
    
    Escúchala en:
    - Spotify: {spotify_result['playlist_url']}
    """
    
    #Añadir detalles de YouTube si está habilitado
    if youtube_result:
        message_body += "\n\nDetalles de YouTube:"
        for video in youtube_result['video_urls']:
            message_body += f"\n- {video['song']}: {video['url']}"
    
    message_body += "\n\n¡Disfruta la música!"
    
    if email:
        notification_tool.send_email(
            to_email=email,
            subject=f"Tu lista de reproducción para {query}",
            body=message_body
        )
        notification_sent = True
    
    if phone:
        notification_tool.send_whatsapp(
            phone_number=phone,
            message=message_body
        )
        notification_sent = True
    
    # Devolver resultados
    return {
        "query": query,
        "songs": selected_songs,
        "youtube_result": {},  # Devolver un diccionario vacío para YouTube
        "spotify_result": spotify_result,
        "notification_sent": notification_sent
    }
    

# Ejemplo de uso
if __name__ == "__main__":
    # Verificar disponibilidad de API keys
    if not os.environ.get("SPOTIFY_CLIENT_ID") or not os.environ.get("SPOTIFY_CLIENT_SECRET"):
        print("⚠️ ADVERTENCIA: No se encontraron las credenciales de Spotify")
    
    # Ejecutar el flujo de recomendación de música
    result = create_music_recommendation(
        query="AC/DC",
        email="usuario@ejemplo.com",
        # phone="+1234567890"  # Descomentar para enviar por WhatsApp
    )
    
    # Mostrar resultados de manera más amigable
    print("\n🎵 Lista de reproducción creada exitosamente 🎵")
    print(f"🔍 Búsqueda: {result['query']}")
    print("\n🎶 Canciones incluidas:")
