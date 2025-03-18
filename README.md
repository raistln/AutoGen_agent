Generador de Listas de Reproducción Automatizado 🎵

Este proyecto es una herramienta que permite crear listas de reproducción automáticamente en plataformas como YouTube y Spotify basadas en un término de búsqueda (artista, género, etc.). Además, ofrece la opción de enviar notificaciones por correo electrónico con los detalles de las listas creadas.
Características Principales ✨

    Búsqueda de Canciones: Utiliza APIs de Last.fm y Spotify para encontrar canciones relacionadas con un término de búsqueda.

    Creación de Playlists: Crea listas de reproducción en YouTube y Spotify con las canciones encontradas.

    Notificaciones por Correo: Envía un correo electrónico con los enlaces a las listas de reproducción creadas.

    Modelos de Lenguaje Local: Usa Ollama con el modelo Gemma 2B para generar contenido personalizado en los correos electrónicos.

    Interfaz de Línea de Comandos (CLI): Fácil de usar desde la terminal.

Requisitos Previos 📋

Antes de ejecutar el proyecto, asegúrate de tener lo siguiente:

    Python 3.8 o superior.

    Credenciales de APIs:

        Last.fm: Necesitas una clave de API (LASTFM_API_KEY) y un secreto (LASTFM_API_SECRET).

        Spotify: Registra una aplicación en el Dashboard de Spotify para obtener SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET y SPOTIFY_REDIRECT_URI.

        YouTube: Descarga el archivo client_secret.json desde Google Cloud Console.

        OpenAI (opcional): Si prefieres usar GPT-4 en lugar de Ollama, necesitas una clave de API (OPENAI_API_KEY).

    Ollama: Si usas el modelo local, asegúrate de tener Ollama instalado y en ejecución.

Instalación 🛠️

    Clona el repositorio:
    bash
    Copy

    git clone https://github.com/tu-usuario/tu-repositorio.git
    cd tu-repositorio

    Crea un entorno virtual (opcional pero recomendado):
    bash
    Copy

    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate

    Instala las dependencias:
    bash
    Copy

    pip install -r requirements.txt

    Configura las variables de entorno:

        Crea un archivo .env en la raíz del proyecto y añade las siguientes variables:
        plaintext
        Copy

        LASTFM_API_KEY=tu_clave_de_lastfm
        LASTFM_API_SECRET=tu_secreto_de_lastfm
        SPOTIFY_CLIENT_ID=tu_client_id_de_spotify
        SPOTIFY_CLIENT_SECRET=tu_client_secret_de_spotify
        SPOTIFY_REDIRECT_URI=tu_redirect_uri_de_spotify
        EMAIL_USER=tu_correo@gmail.com
        EMAIL_PASSWORD=tu_contraseña_de_app
        OPENAI_API_KEY=tu_clave_de_openai  # Opcional

    Descarga el modelo de Ollama (si no usas OpenAI):
    bash
    Copy

    ollama pull gemma:2b

Uso 🚀

    Ejecuta el programa:
    bash
    Copy

    python main.py

    Sigue las instrucciones en la terminal:

        Ingresa un término de búsqueda (por ejemplo, "Rock Clásico" o "AC/DC").

        Especifica el número de canciones que deseas incluir en la playlist.

        Decide si deseas recibir una notificación por correo electrónico.

    Resultados:

        El programa generará listas de reproducción en YouTube y Spotify.

        Si proporcionaste un correo, recibirás un mensaje con los enlaces y detalles de las canciones.

Estructura del Proyecto 📂
Copy

.
├── .env                     # Variables de entorno
├── main.py                  # Punto de entrada del programa
├── README.md                # Este archivo
├── requirements.txt         # Dependencias del proyecto
├── client_secret.json       # Credenciales de YouTube (descargado de Google Cloud)
└── .spotify_cache           # Caché de autenticación de Spotify

Herramientas y Tecnologías Utilizadas 🛠️

    APIs:

        Last.fm

        Spotify

        YouTube

    Lenguajes y Librerías:

        Python

        requests (para solicitudes HTTP)

        spotipy (API de Spotify)

        googleapiclient (API de YouTube)

        smtplib (para enviar correos)

        dotenv (para manejar variables de entorno)

    Modelos de Lenguaje:

        Ollama (Gemma 2B)

        OpenAI GPT-4 (opcional)

Ejemplo de Uso 💡
bash
Copy

$ python main.py
🎵 Bienvenido al Generador de Listas de Reproducción 🎵
-----------------------------------------------------
¿Qué grupo o tipo de música te gustaría buscar? (por ejemplo, 'Rock Clásico', 'AC/DC'): Rock Clásico
¿Cuántas canciones te gustaría incluir en la playlist? (por defecto: 20): 15
¿Deseas recibir una notificación con los resultados? (s/n): s
Ingresa tu correo electrónico: usuario@example.com

🔍 Buscando canciones y creando listas de reproducción...
🎵 Lista de reproducción creada exitosamente 🎵
🔍 Búsqueda: Rock Clásico

🎶 Canciones incluidas:
1. Bohemian Rhapsody
2. Stairway to Heaven
3. Hotel California
...

🎧 Escucha la lista en YouTube: https://www.youtube.com/playlist?list=EXAMPLE_ID
🎧 Escucha la lista en Spotify: https://open.spotify.com/playlist/EXAMPLE_ID

📬 Se ha enviado una notificación con los detalles.

Contribuciones 🤝

¡Las contribuciones son bienvenidas! Si deseas mejorar el proyecto, sigue estos pasos:

    Haz un fork del repositorio.

    Crea una rama con tu feature (git checkout -b feature/nueva-funcionalidad).

    Haz commit de tus cambios (git commit -m 'Añade nueva funcionalidad').

    Haz push a la rama (git push origin feature/nueva-funcionalidad).

    Abre un Pull Request.

Licencia 📄

Este proyecto está bajo la licencia MIT. Consulta el archivo LICENSE para más detalles.