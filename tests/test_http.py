import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import hashlib
import hmac
from pathlib import Path
from Crypto.PublicKey import RSA, ECC
from Crypto.Signature import pkcs1_15, eddsa
from Crypto.Hash import SHA256
import aiohttp
import requests

from pytrading.connectivity.http import AsyncClient, Client, BaseClient

class TestBaseClient(unittest.TestCase):
    def setUp(self):
        self.client = BaseClient(
            api_key="test_api_key",
            api_secret="test_api_secret",
            tld="test",
            testnet=True,
            private_key="test_private_key",
            private_key_pass="test_pass"
        )

    def test_init(self):
        self.assertEqual(self.client.API_KEY, "test_api_key")
        self.assertEqual(self.client.API_SECRET, "test_api_secret")
        self.assertEqual(self.client.tld, "test")
        self.assertTrue(self.client.testnet)
        self.assertIsNotNone(self.client.PRIVATE_KEY)

    def test_get_headers(self):
        headers = self.client._get_headers()
        self.assertIn("Accept", headers)
        self.assertIn("User-Agent", headers)
        self.assertIn("X-MBX-APIKEY", headers)

    def test_init_private_key_rsa(self):
        private_key = RSA.generate(2048).export_key()
        client = BaseClient(private_key=private_key)
        self.assertTrue(client._is_rsa)
        self.assertIsInstance(client.PRIVATE_KEY, RSA.RsaKey)

    def test_init_private_key_ecc(self):
        private_key = ECC.generate(curve='P-256').export_key()
        client = BaseClient(private_key=private_key)
        self.assertFalse(client._is_rsa)
        self.assertIsInstance(client.PRIVATE_KEY, ECC.EccKey)

    def test_rsa_signature(self):
        query_string = "test_query_string"
        signature = self.client._rsa_signature(query_string)
        self.assertIsInstance(signature, str)

    def test_ed25519_signature(self):
        query_string = "test_query_string"
        signature = self.client._ed25519_signature(query_string)
        self.assertIsInstance(signature, str)

    def test_hmac_signature(self):
        query_string = "test_query_string"
        signature = self.client._hmac_signature(query_string)
        self.assertIsInstance(signature, str)

    def test_generate_signature(self):
        data = {"test": "data"}
        signature = self.client._generate_signature(data)
        self.assertIsInstance(signature, str)

    def test_uuid22(self):
        uuid = self.client.uuid22()
        self.assertEqual(len(uuid), 22)

    def test_order_params(self):
        data = {"b": "2", "a": "1", "c": None}
        ordered_params = self.client._order_params(data)
        self.assertEqual(ordered_params, [("a", "1"), ("b", "2")])

    def test_get_request_kwargs(self):
        kwargs = {"data": {"test": "data"}}
        request_kwargs = self.client._get_request_kwargs("get", True, **kwargs)
        self.assertIn("timeout", request_kwargs)
        self.assertIn("data", request_kwargs)
        self.assertEqual(request_kwargs["data"], [("test", "data")])

class TestClient(unittest.TestCase):
    def setUp(self):
        self.client = Client(
            api_key="test_api_key",
            api_secret="test_api_secret",
            tld="test",
            testnet=True,
            private_key="test_private_key",
            private_key_pass="test_pass"
        )

    def test_init_session(self):
        session = self.client._init_session()
        self.assertIsInstance(session, requests.Session)
        self.assertIn("X-MBX-APIKEY", session.headers)

    @patch('requests.Session.get')
    def test_request_get(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response

        response = self.client._request("get", "test_uri", False)
        self.assertEqual(response, {"test": "data"})

    @patch('requests.Session.post')
    def test_request_post(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_post.return_value = mock_response

        response = self.client._request("post", "test_uri", False)
        self.assertEqual(response, {"test": "data"})

    @patch('requests.Session.get')
    def test_handle_response_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            self.client._request("get", "test_uri", False)

    @patch('requests.Session.get')
    def test_handle_response_invalid_json(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Invalid JSON"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            self.client._request("get", "test_uri", False)

class TestAsyncClient(unittest.TestCase):
    def setUp(self):
        self.client = AsyncClient(
            api_key="test_api_key",
            api_secret="test_api_secret",
            tld="test",
            testnet=True,
            private_key="test_private_key",
            private_key_pass="test_pass"
        )

    def test_init_session(self):
        session = self.client._init_session()
        self.assertIsInstance(session, aiohttp.ClientSession)
        self.assertIn("X-MBX-APIKEY", session.headers)

    @patch('aiohttp.ClientSession.get')
    async def test_request_get(self, mock_get):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response

        response = await self.client._request("get", "test_uri", False)
        self.assertEqual(response, {"test": "data"})

    @patch('aiohttp.ClientSession.post')
    async def test_request_post(self, mock_post):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = {"test": "data"}
        mock_post.return_value = mock_response

        response = await self.client._request("post", "test_uri", False)
        self.assertEqual(response, {"test": "data"})

    @patch('aiohttp.ClientSession.get')
    async def test_handle_response_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status = 400
        mock_response.text = "Bad Request"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            await self.client._request("get", "test_uri", False)

    @patch('aiohttp.ClientSession.get')
    async def test_handle_response_invalid_json(self, mock_get):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = "Invalid JSON"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            await self.client._request("get", "test_uri", False)

if __name__ == '__main__':
    unittest.main()
