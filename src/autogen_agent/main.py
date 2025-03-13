from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
import os
import json
import requests
from googleapiclient.discovery import build
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
import re

# Configuración de los modelos
config_list = [
    {
        "model": "gpt-4",  # Puedes usar un modelo más potente para mejores resultados
        "api_key": os.environ.get("OPENAI_API_KEY"),
    }
    # Alternativamente, puedes seguir usando Ollama localmente
    # {
    #     "model": "mistral:7b",
    #     "api_key": "None",
    #     "base_url": "http://localhost:11434",
    # }
]

# Clase para manejar la búsqueda en internet usando DuckDuckGo
class DuckDuckGoSearchTool:
    def search_playlists(self, query):
        """Busca listas de reproducción en internet usando DuckDuckGo"""
        search_query = f"{query} playlist top songs"
        print(f"Buscando listas de reproducción para: {search_query}")
        
        try:
            # Construir la URL de búsqueda de DuckDuckGo
            url = f"https://api.duckduckgo.com/?q={search_query}&format=json"
            response = requests.get(url)
            results = response.json()
            
            # En caso de que la API de DuckDuckGo no devuelva resultados útiles,
            # hacemos una búsqueda web normal y parseamos los resultados
            if not results.get('RelatedTopics'):
                html_url = f"https://html.duckduckgo.com/html/?q={search_query}"
                html_response = requests.get(html_url)
                soup = BeautifulSoup(html_response.text, 'html.parser')
                
                # Extracción de resultados
                links = soup.find_all('a', class_='result__a')
                songs = self._extract_songs_from_results(links, query)
                
                # Si no encontramos suficientes canciones, usamos el respaldo
                if len(songs) < 5:
                    return self._fallback_search(query)
                
                return {
                    "playlists": [
                        {
                            "title": f"Top canciones de {query} (DuckDuckGo)",
                            "songs": songs
                        }
                    ]
                }
            
            # Procesamos los resultados de la API si están disponibles
            topics = results.get('RelatedTopics', [])
            songs = []
            
            for topic in topics:
                if 'Text' in topic:
                    # Intentamos extraer nombres de canciones del texto
                    text = topic['Text']
                    potential_songs = self._extract_song_names(text, query)
                    songs.extend(potential_songs)
            
            # Eliminamos duplicados y limitamos a 10 canciones
            songs = list(dict.fromkeys(songs))[:10]
            
            # Si no encontramos suficientes canciones, usamos el respaldo
            if len(songs) < 5:
                return self._fallback_search(query)
            
            return {
                "playlists": [
                    {
                        "title": f"Top canciones de {query} (DuckDuckGo)",
                        "songs": songs
                    }
                ]
            }
            
        except Exception as e:
            print(f"Error en la búsqueda de DuckDuckGo: {e}")
            return self._fallback_search(query)
    
    def _extract_songs_from_results(self, links, query):
        """Extrae nombres de canciones de los resultados de búsqueda"""
        songs = []
        for link in links[:20]:  # Limitar a los primeros 20 resultados
            text = link.get_text()
            potential_songs = self._extract_song_names(text, query)
            songs.extend(potential_songs)
        
        # Eliminar duplicados y limitar a 10
        return list(dict.fromkeys(songs))[:10]
    
    def _extract_song_names(self, text, artist_or_genre):
        """
        Extrae posibles nombres de canciones de un texto
        basado en patrones comunes de listas de canciones
        """
        # Patrones para identificar canciones
        patterns = [
            r'"([^"]+)"',  # Texto entre comillas
            r"'([^']+)'",  # Texto entre comillas simples
            r'(?:^|\s)([A-Z][a-zA-Z\s\']+)(?:\s-|\sby)',  # Título capitalizado seguido de "by" o "-"
            r'(?:^|\d\.\s)([A-Z][a-zA-Z\s\']+)(?:$|\n)',  # Título numerado (1. Título)
            r'(?<=\n|\s)([A-Z][a-zA-Z0-9\s\']+)(?=\n|\s|$)'  # Líneas que comienzan con mayúscula
        ]
        
        potential_songs = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Filtrar para evitar falsos positivos
                if len(match) > 3 and len(match) < 50:
                    if artist_or_genre.lower() not in match.lower():
                        potential_songs.append(match.strip())
        
        return potential_songs
    
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

# Clase para interactuar con YouTube
class YouTubeTool:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def create_playlist(self, title, description, songs):
        """
        Crea una lista de reproducción en YouTube y devuelve una lista de URLs
        de los videos encontrados junto con el enlace a la playlist
        """
        try:
            # Usando la API de YouTube
            youtube = build("youtube", "v3", developerKey=self.api_key)
            
            # Crear la lista de reproducción
            playlist = youtube.playlists().insert(
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
                search_response = youtube.search().list(
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
                    youtube.playlistItems().insert(
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
    def __init__(self, client_id, client_secret, redirect_uri):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="playlist-modify-public"
        ))
    
    def create_playlist(self, title, description, songs):
        """
        Crea una lista de reproducción en Spotify y devuelve la URL
        junto con información de las canciones añadidas
        """
        try:
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
            sender_email = os.environ.get("EMAIL_USER")
            sender_password = os.environ.get("EMAIL_PASSWORD")
            
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

# Configuración de agentes con herramientas externas
search_tool = DuckDuckGoSearchTool()
youtube_tool = YouTubeTool(api_key=os.environ.get("YOUTUBE_API_KEY", "TU_API_KEY"))
spotify_tool = SpotifyTool(
    client_id=os.environ.get("SPOTIFY_CLIENT_ID", "TU_CLIENT_ID"),
    client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET", "TU_CLIENT_SECRET"),
    redirect_uri="http://localhost:8888/callback"
)
notification_tool = NotificationTool()

# Agente de Búsqueda en Internet
search_agent = AssistantAgent(
    name="search_agent",
    llm_config={"config_list": config_list},
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
    llm_config={"config_list": config_list},
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
    llm_config={"config_list": config_list},
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
    llm_config={"config_list": config_list},
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
    
    Args:
        query: Consulta del usuario (artista, género, etc.)
        email: Correo electrónico para enviar los resultados
        phone: Número de teléfono para WhatsApp
    
    Returns:
        dict: Resultado con las URLs de las listas y mensajes de estado
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
    
    # Crear en YouTube
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
    - YouTube: {youtube_result['playlist_url']}
    - Spotify: {spotify_result['playlist_url']}
    
    Detalles de YouTube:
    """
    
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
        "youtube_result": youtube_result,
        "spotify_result": spotify_result,
        "notification_sent": notification_sent
    }

# Ejemplo de uso
if __name__ == "__main__":
    # Configurar tus claves de API como variables de entorno antes de ejecutar
    result = create_music_recommendation(
        query="AC/DC",
        email="usuario@ejemplo.com",
        # phone="+1234567890"  # Descomentar para enviar por WhatsApp
    )
    
    print(json.dumps(result, indent=2))