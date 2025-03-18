import unittest
from unittest.mock import patch, MagicMock
import sys
import os  

src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.append(src_path)

from autogen_agent.main import (
    MusicSearchTool,
    YouTubeTool,
    SpotifyTool,
    NotificationTool,
    generate_email_content,
    create_music_recommendation,
    validate_email,
)
import requests
from dotenv import load_dotenv

# Cargar variables de entorno para pruebas
load_dotenv()

class TestMusicSearchTool(unittest.TestCase):
    def setUp(self):
        self.search_tool = MusicSearchTool()

    @patch("requests.get")
    def test_search_via_lastfm(self, mock_get):
        # Simular una respuesta exitosa de Last.fm
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "toptracks": {
                "track": [
                    {"name": "Bohemian Rhapsody"},
                    {"name": "Stairway to Heaven"},
                ]
            }
        }
        mock_get.return_value = mock_response

        songs = self.search_tool._search_via_lastfm("Queen")
        self.assertEqual(len(songs), 2)
        self.assertIn("Bohemian Rhapsody", songs)

    @patch("requests.get")
    def test_search_via_lastfm_error(self, mock_get):
        # Simular un error en la API de Last.fm
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        songs = self.search_tool._search_via_lastfm("Queen")
        self.assertEqual(len(songs), 0)

    @patch("spotipy.Spotify.search")
    def test_search_via_spotify(self, mock_search):
        # Simular una respuesta exitosa de Spotify
        mock_search.return_value = {
            "tracks": {
                "items": [
                    {
                        "name": "Bohemian Rhapsody",
                        "artists": [{"name": "Queen"}],
                        "album": {"name": "A Night at the Opera"},
                        "uri": "spotify:track:123",
                    }
                ]
            }
        }

        songs = self.search_tool._search_via_spotify("Queen")
        self.assertEqual(len(songs), 1)
        self.assertIn("Bohemian Rhapsody", songs)

class TestYouTubeTool(unittest.TestCase):
    def setUp(self):
        self.youtube_tool = YouTubeTool()

    @patch("googleapiclient.discovery.build")
    def test_create_playlist(self, mock_build):
        # Simular la creación de una playlist en YouTube
        mock_service = MagicMock()
        mock_service.playlists.return_value.insert.return_value.execute.return_value = {
            "id": "PLAYLIST_ID"
        }
        mock_service.search.return_value.list.return_value.execute.return_value = {
            "items": [{"id": {"videoId": "VIDEO_ID"}, "snippet": {"title": "Video Title"}}]
        }
        mock_build.return_value = mock_service

        result = self.youtube_tool.create_playlist("Test Playlist", "Test Description", ["Bohemian Rhapsody"])
        self.assertIn("playlist_url", result)
        self.assertIn("video_urls", result)

class TestSpotifyTool(unittest.TestCase):
    def setUp(self):
        self.spotify_tool = SpotifyTool()

    @patch("spotipy.Spotify.user_playlist_create")
    @patch("spotipy.Spotify.search")
    def test_create_playlist(self, mock_search, mock_create):
        # Simular la creación de una playlist en Spotify
        mock_create.return_value = {
            "id": "PLAYLIST_ID",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/PLAYLIST_ID"},
        }
        mock_search.return_value = {
            "tracks": {
                "items": [
                    {
                        "name": "Bohemian Rhapsody",
                        "artists": [{"name": "Queen"}],
                        "album": {"name": "A Night at the Opera"},
                        "uri": "spotify:track:123",
                    }
                ]
            }
        }

        result = self.spotify_tool.create_playlist("Test Playlist", "Test Description", ["Bohemian Rhapsody"])
        self.assertIn("playlist_url", result)
        self.assertIn("track_info", result)

class TestNotificationTool(unittest.TestCase):
    def setUp(self):
        self.notification_tool = NotificationTool()

    @patch("smtplib.SMTP")
    def test_send_email(self, mock_smtp):
        # Simular el envío de un correo electrónico
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        result = self.notification_tool.send_email(
            "test@example.com", "Test Subject", "Test Body"
        )
        self.assertTrue(result)

class TestEmailContentGeneration(unittest.TestCase):
    @patch("main.ask_ollama")
    def test_generate_email_content(self, mock_ask_ollama):
        # Simular la generación de contenido de correo
        mock_ask_ollama.return_value = "Test Email Content"

        result = generate_email_content(
            "Queen",
            {"playlist_url": "https://youtube.com/playlist/123"},
            {"playlist_url": "https://spotify.com/playlist/123"},
            ["Bohemian Rhapsody", "Stairway to Heaven"],
        )
        self.assertIn("subject", result)
        self.assertIn("body", result)

class TestCreateMusicRecommendation(unittest.TestCase):
    @patch("main.MusicSearchTool.search_playlists")
    @patch("main.YouTubeTool.create_playlist")
    @patch("main.SpotifyTool.create_playlist")
    @patch("main.NotificationTool.send_email")
    def test_create_music_recommendation(self, mock_send_email, mock_spotify, mock_youtube, mock_search):
        # Simular el flujo completo de creación de listas de reproducción
        mock_search.return_value = ["Bohemian Rhapsody", "Stairway to Heaven"]
        mock_youtube.return_value = {"playlist_url": "https://youtube.com/playlist/123"}
        mock_spotify.return_value = {"playlist_url": "https://spotify.com/playlist/123"}
        mock_send_email.return_value = True

        result = create_music_recommendation("Queen", "test@example.com")
        self.assertIn("youtube_result", result)
        self.assertIn("spotify_result", result)
        self.assertTrue(result["email_sent"])

class TestValidateEmail(unittest.TestCase):
    def test_validate_email(self):
        # Verificar que la validación de correo funcione correctamente
        self.assertTrue(validate_email("test@example.com"))
        self.assertFalse(validate_email("invalid-email"))

if __name__ == "__main__":
    unittest.main()