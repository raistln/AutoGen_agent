import requests
import json
import time
import random
import os

# Configuración para usar Ollama directamente
OLLAMA_BASE_URL = "http://localhost:11434/api"
DEFAULT_MODEL = "gemma:2b"  #llama2:7b Modelo muy ligero, corre bien en CPU
# Alternativas más ligeras: orca-mini:3b, gemma:2b, phi2:3b

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

# Clase para simular búsqueda en internet
class MockInternetSearchTool:
    def search_playlists(self, query):
        """Simula la búsqueda de listas de reproducción sin necesidad de API"""
        print(f"Buscando listas de reproducción para: {query}")
        
        # Usar datos ficticios basados en conocimiento común de música
        mock_data = self._get_mock_data(query)
        
        # Simulamos un pequeño retraso para hacerlo más realista
        time.sleep(0.5)
        
        return mock_data
    
    def _get_mock_data(self, query):
        """Proporciona datos de ejemplo basados en la consulta"""
        query = query.lower()
        
        # Diccionario de datos de ejemplo por artista/género
        mock_database = {
            "ac/dc": {
                "playlists": [
                    {
                        "title": "AC/DC Greatest Hits",
                        "songs": ["Back in Black", "Highway to Hell", "Thunderstruck", 
                                 "You Shook Me All Night Long", "Hells Bells", "TNT", 
                                 "Dirty Deeds Done Dirt Cheap", "Shoot to Thrill"]
                    },
                    {
                        "title": "Lo Mejor de AC/DC",
                        "songs": ["Back in Black", "Highway to Hell", "TNT", 
                                 "Thunderstruck", "Shoot to Thrill", "Hells Bells",
                                 "Rock N Roll Train", "Whole Lotta Rosie"]
                    },
                    {
                        "title": "AC/DC Rock Classics",
                        "songs": ["Back in Black", "Highway to Hell", "Thunderstruck", 
                                 "Shoot to Thrill", "T.N.T", "Hell Ain't a Bad Place to Be",
                                 "If You Want Blood (You've Got It)", "Rock and Roll Ain't Noise Pollution"]
                    }
                ]
            },
            "rock 80s": {
                "playlists": [
                    {
                        "title": "80s Rock Classics",
                        "songs": ["Sweet Child O' Mine - Guns N' Roses", "Livin' on a Prayer - Bon Jovi", 
                                 "Pour Some Sugar on Me - Def Leppard", "The Final Countdown - Europe",
                                 "Eye of the Tiger - Survivor", "Jump - Van Halen", 
                                 "Every Breath You Take - The Police", "Should I Stay or Should I Go - The Clash"]
                    },
                    {
                        "title": "80s Rock Anthems",
                        "songs": ["Sweet Child O' Mine - Guns N' Roses", "Welcome to the Jungle - Guns N' Roses",
                                 "Livin' on a Prayer - Bon Jovi", "You Give Love a Bad Name - Bon Jovi",
                                 "Pour Some Sugar on Me - Def Leppard", "Jump - Van Halen",
                                 "We're Not Gonna Take It - Twisted Sister", "Here I Go Again - Whitesnake"]
                    },
                    {
                        "title": "Rock de los 80",
                        "songs": ["Sweet Child O' Mine - Guns N' Roses", "November Rain - Guns N' Roses",
                                 "Livin' on a Prayer - Bon Jovi", "The Final Countdown - Europe",
                                 "Here I Go Again - Whitesnake", "Still Loving You - Scorpions",
                                 "Jump - Van Halen", "Rock You Like a Hurricane - Scorpions"]
                    }
                ]
            },
            "metal": {
                "playlists": [
                    {
                        "title": "Metal Classics",
                        "songs": ["Master of Puppets - Metallica", "Paranoid - Black Sabbath",
                                 "Run to the Hills - Iron Maiden", "Breaking the Law - Judas Priest",
                                 "Crazy Train - Ozzy Osbourne", "Enter Sandman - Metallica",
                                 "The Trooper - Iron Maiden", "Symphony of Destruction - Megadeth"]
                    }
                ]
            },
            "pop": {
                "playlists": [
                    {
                        "title": "Pop Hits",
                        "songs": ["Billie Jean - Michael Jackson", "Like a Prayer - Madonna",
                                 "Shape of You - Ed Sheeran", "Bad Guy - Billie Eilish",
                                 "Uptown Funk - Mark Ronson ft. Bruno Mars", "Blinding Lights - The Weeknd",
                                 "Dance Monkey - Tones and I", "Rolling in the Deep - Adele"]
                    }
                ]
            }
        }
        
        # Buscar coincidencias parciales
        for key, data in mock_database.items():
            if key in query:
                return data
        
        # Si no hay coincidencia específica, devolver pop como predeterminado
        return mock_database["pop"]

# Clase para simular la creación de listas de reproducción en YouTube
class MockYouTubeTool:
    def create_playlist(self, title, description, songs):
        """Simula la creación de una lista de reproducción en YouTube sin API real"""
        print(f"Creando lista de reproducción en YouTube: {title}")
        print(f"Descripción: {description}")
        print(f"Canciones: {songs}")
        
        # Generar un ID de playlist simulado
        playlist_id = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(34))
        
        # Construir una URL ficticia pero realista
        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        
        # Simulamos un pequeño retraso para hacerlo más realista
        time.sleep(1)
        
        return {
            "playlist_id": playlist_id,
            "url": playlist_url,
            "videos_added": len(songs)
        }

# Clase para simular la creación de listas de reproducción en Spotify
class MockSpotifyTool:
    def create_playlist(self, title, description, songs):
        """Simula la creación de una lista de reproducción en Spotify sin API real"""
        print(f"Creando lista de reproducción en Spotify: {title}")
        print(f"Descripción: {description}")
        print(f"Canciones: {songs}")
        
        # Generar un ID de playlist simulado
        playlist_id = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(22))
        
        # Construir una URL ficticia pero realista
        playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
        
        # Simulamos un pequeño retraso para hacerlo más realista
        time.sleep(1)
        
        return {
            "playlist_id": playlist_id,
            "url": playlist_url,
            "tracks_added": len(songs)
        }

# Clase para simular el envío de notificaciones
class MockNotificationTool:
    def send_email(self, to_email, subject, body):
        """Simula el envío de un correo electrónico"""
        print(f"\n--- SIMULACIÓN DE CORREO ELECTRÓNICO ---")
        print(f"Para: {to_email}")
        print(f"Asunto: {subject}")
        print(f"Cuerpo del mensaje:\n{body}")
        print(f"--- FIN DEL CORREO ELECTRÓNICO ---\n")
        return True
    
    def send_whatsapp(self, phone_number, message):
        """Simula el envío de un mensaje de WhatsApp"""
        print(f"\n--- SIMULACIÓN DE MENSAJE WHATSAPP ---")
        print(f"Para: {phone_number}")
        print(f"Mensaje:\n{message}")
        print(f"--- FIN DEL MENSAJE WHATSAPP ---\n")
        return True

# Función para obtener las canciones más populares
def get_most_popular_songs(search_results, limit=10):
    """Analiza los resultados de búsqueda y devuelve las canciones más populares"""
    # Contar frecuencia de canciones
    song_counts = {}
    
    # Iterar a través de las listas de reproducción
    for playlist in search_results["playlists"]:
        for song in playlist["songs"]:
            if song in song_counts:
                song_counts[song] += 1
            else:
                song_counts[song] = 1
    
    # Ordenar por popularidad (frecuencia de aparición)
    top_songs = sorted(song_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    # Devolver solo los nombres de las canciones
    return [song for song, count in top_songs]

# Configuración de herramientas simuladas
search_tool = MockInternetSearchTool()
youtube_tool = MockYouTubeTool()
spotify_tool = MockSpotifyTool()
notification_tool = MockNotificationTool()

# Agentes simulados mediante Ollama
class OllamaAgent:
    def __init__(self, name, system_message, model=DEFAULT_MODEL):
        self.name = name
        self.system_message = system_message
        self.model = model
    
    def ask(self, message):
        """Consulta al agente (LLM) con un mensaje"""
        full_prompt = f"""
{self.system_message}

Usuario: {message}

Asistente:"""
        
        response = ask_ollama(full_prompt, self.model)
        print(f"\n--- RESPUESTA DEL AGENTE {self.name} ---")
        print(response)
        print(f"--- FIN DE LA RESPUESTA ---\n")
        return response

# Función principal para crear recomendaciones musicales usando agentes
def create_music_recommendation_with_agents(query, agents, email=None, phone=None):
    """
    Flujo completo para crear y compartir listas de reproducción usando agentes
    
    Args:
        query: Consulta del usuario (artista, género, etc.)
        agents: Diccionario con los agentes a utilizar
        email: Correo electrónico para enviar los resultados (opcional)
        phone: Número de teléfono para WhatsApp (opcional)
    
    Returns:
        dict: Resultado con las URLs de las listas y mensajes de estado
    """
    print(f"\n=== Iniciando búsqueda para: {query} ===")
    
    # Paso 1: Consultar al agente de búsqueda
    search_response = agents["search"].ask(f"Busca listas de reproducción para '{query}' y recomienda las 8 mejores canciones.")
    
    # Paso 2: Buscar las listas de reproducción (simulado)
    search_results = search_tool.search_playlists(query)
    selected_songs = get_most_popular_songs(search_results, limit=8)
    print(f"\nCanciones seleccionadas: {selected_songs}")
    
    # Paso 3: Consultar al agente de YouTube
    youtube_prompt = f"Crea una lista de reproducción en YouTube para estas canciones: {', '.join(selected_songs)}"
    youtube_response = agents["youtube"].ask(youtube_prompt)
    
    # Crear en YouTube (simulado)
    youtube_result = youtube_tool.create_playlist(
        title=f"Playlist Recomendada: {query}", 
        description=f"Lista de reproducción generada automáticamente para '{query}'",
        songs=selected_songs
    )
    
    # Paso 4: Consultar al agente de Spotify
    spotify_prompt = f"Crea una lista de reproducción en Spotify para estas canciones: {', '.join(selected_songs)}"
    spotify_response = agents["spotify"].ask(spotify_prompt)
    
    # Crear en Spotify (simulado)
    spotify_result = spotify_tool.create_playlist(
        title=f"Playlist Recomendada: {query}",
        description=f"Lista de reproducción generada automáticamente para '{query}'",
        songs=selected_songs
    )
    
    # Paso 5: Preparar mensaje de notificación
    message_body = f"""
    ¡Hola! Tu lista de reproducción para "{query}" está lista.
    
    Canciones incluidas:
    {chr(10).join('- ' + song for song in selected_songs)}
    
    Escúchala en:
    - YouTube: {youtube_result['url']}
    - Spotify: {spotify_result['url']}
    
    ¡Disfruta la música!
    """
    
    # Paso 6: Consultar al agente de notificaciones si es necesario
    notifications_sent = []
    notification_response = None
    
    if email or phone:
        notification_prompt = f"""
        Envía una notificación con los siguientes datos:
        
        Email: {email or 'No proporcionado'}
        Teléfono: {phone or 'No proporcionado'}
        
        Mensaje:
        {message_body}
        """
        notification_response = agents["notification"].ask(notification_prompt)
    
    # Enviar notificaciones (simulado)
    if email:
        email_result = notification_tool.send_email(
            to_email=email,
            subject=f"Tu lista de reproducción para {query}",
            body=message_body
        )
        if email_result:
            notifications_sent.append("email")
    
    if phone:
        whatsapp_result = notification_tool.send_whatsapp(
            phone_number=phone,
            message=message_body
        )
        if whatsapp_result:
            notifications_sent.append("whatsapp")
    
    # Devolver resultados
    return {
        "query": query,
        "songs": selected_songs,
        "youtube_url": youtube_result['url'],
        "spotify_url": spotify_result['url'],
        "notifications_sent": notifications_sent or None,
        "agent_responses": {
            "search": search_response,
            "youtube": youtube_response,
            "spotify": spotify_response,
            "notification": notification_response
        }
    }

# Función simple sin interacción LLM
def create_music_recommendation(query, email=None, phone=None):
    """
    Flujo completo para crear y compartir listas de reproducción
    
    Args:
        query: Consulta del usuario (artista, género, etc.)
        email: Correo electrónico para enviar los resultados (opcional)
        phone: Número de teléfono para WhatsApp (opcional)
    
    Returns:
        dict: Resultado con las URLs de las listas y mensajes de estado
    """
    print(f"\n=== Iniciando búsqueda para: {query} ===")
    
    # Paso 1: Buscar listas de reproducción
    search_results = search_tool.search_playlists(query)
    
    # Paso 2: Analizar y seleccionar las canciones más populares
    selected_songs = get_most_popular_songs(search_results, limit=8)
    print(f"\nCanciones seleccionadas: {selected_songs}")
    
    # Paso 3: Crear listas de reproducción
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
    
    # Paso 4: Preparar mensaje de notificación
    message_body = f"""
    ¡Hola! Tu lista de reproducción para "{query}" está lista.
    
    Canciones incluidas:
    {chr(10).join('- ' + song for song in selected_songs)}
    
    Escúchala en:
    - YouTube: {youtube_result['url']}
    - Spotify: {spotify_result['url']}
    
    ¡Disfruta la música!
    """
    
    # Paso 5: Enviar notificaciones si se proporcionaron datos de contacto
    notifications_sent = []
    
    if email:
        email_result = notification_tool.send_email(
            to_email=email,
            subject=f"Tu lista de reproducción para {query}",
            body=message_body
        )
        if email_result:
            notifications_sent.append("email")
    
    if phone:
        whatsapp_result = notification_tool.send_whatsapp(
            phone_number=phone,
            message=message_body
        )
        if whatsapp_result:
            notifications_sent.append("whatsapp")
    
    # Devolver resultados
    return {
        "query": query,
        "songs": selected_songs,
        "youtube_url": youtube_result['url'],
        "spotify_url": spotify_result['url'],
        "notifications_sent": notifications_sent or None
    }

# Ejemplo de uso para probar el funcionamiento
if __name__ == "__main__":
    use_llm = False
    current_model = DEFAULT_MODEL
    
    # Verificar que Ollama esté funcionando
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/tags")
        if response.status_code != 200:
            print("⚠️ Error: No se pudo conectar con Ollama. Asegúrate de que el servidor esté en ejecución.")
            print("Cambiando a modo sin LLM...")
            use_llm = False
        else:
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            
            if DEFAULT_MODEL not in model_names:
                print(f"⚠️ Advertencia: El modelo {DEFAULT_MODEL} no está disponible.")
                
                # Intentar descargar el modelo
                if install_ollama_model(DEFAULT_MODEL):
                    current_model = DEFAULT_MODEL
                    use_llm = True
                else:
                    # Si no se puede descargar, usar uno disponible
                    print(f"Modelos disponibles: {', '.join(model_names)}")
                    if len(model_names) > 0:
                        current_model = model_names[0]
                        print(f"Usando el modelo {current_model} en su lugar.")
                        use_llm = True
                    else:
                        print("No hay modelos disponibles. Cambiando a modo sin LLM...")
                        use_llm = False
            else:
                current_model = DEFAULT_MODEL
                use_llm = True
                print(f"Ollama está funcionando correctamente. Usando el modelo {current_model}.")
    except Exception as e:
        print(f"⚠️ Error al conectar con Ollama: {e}")
        print("Cambiando a modo sin LLM...")
        use_llm = False
    
    # Inicializar agentes si se usará LLM
    agents = {}
    if use_llm:
        # Crear los agentes con el modelo seleccionado
        agents = {
            "search": OllamaAgent(
                name="SearchAgent",
                system_message="""
                Eres un agente especializado en buscar listas de reproducción en internet.
                Tu tarea es encontrar las canciones más populares según el género o artista solicitado,
                y crear una lista consolidada de las canciones más mencionadas en diferentes fuentes.
                """,
                model=current_model
            ),
            
            "youtube": OllamaAgent(
                name="YouTubeAgent",
                system_message="""
                Eres un agente especializado en crear listas de reproducción en YouTube.
                Tu tarea es tomar una lista de canciones y crear una lista de reproducción,
                devolviendo el enlace para acceder a ella.
                """,
                model=current_model
            ),
            
            "spotify": OllamaAgent(
                name="SpotifyAgent",
                system_message="""
                Eres un agente especializado en crear listas de reproducción en Spotify.
                Tu tarea es tomar una lista de canciones y crear una lista de reproducción,
                devolviendo el enlace para acceder a ella.
                """,
                model=current_model
            ),
            
            "notification": OllamaAgent(
                name="NotificationAgent",
                system_message="""
                Eres un agente especializado en enviar notificaciones.
                Tu tarea es enviar mensajes por correo electrónico o WhatsApp
                con enlaces a listas de reproducción y una descripción amigable.
                """,
                model=current_model
            )
        }
    
    print("\n=== SISTEMA DE RECOMENDACIÓN MUSICAL ===")
    print("1. Buscar por artista/grupo (ej: AC/DC)")
    print("2. Buscar por género (ej: rock 80s)")
    
    query = input("\nIntroduce tu búsqueda: ")
    if not query:
        query = "AC/DC"  # Valor predeterminado
    
    email = input("\nCorreo electrónico (opcional, pulsa Enter para omitir): ")
    phone = input("Número de teléfono para WhatsApp (opcional, pulsa Enter para omitir): ")
    
    print("\nProcesando solicitud...\n")
    
    # Ejecutar con o sin LLM según disponibilidad
    if use_llm:
        print("Usando agentes LLM para procesamiento...")
        result = create_music_recommendation_with_agents(
            query=query,
            agents=agents,
            email=email if email else None,
            phone=phone if phone else None
        )
    else:
        print("Usando modo sin LLM (simulación)...")
        result = create_music_recommendation(
            query=query,
            email=email if email else None,
            phone=phone if phone else None
        )
    
    # Mostrar resultados de forma bonita
    print("\n=== RESULTADOS DE LA RECOMENDACIÓN ===")
    print(json.dumps({k: v for k, v in result.items() if k != 'agent_responses'}, indent=2))
    print("=======================================")