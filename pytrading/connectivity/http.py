import hashlib
import hmac
import random
import time
from base64 import b64encode
from operator import itemgetter
from pathlib import Path
from typing import Optional, Dict, Any, Union, List, Tuple

import aiohttp
import requests
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA, ECC
from Crypto.Signature import pkcs1_15, eddsa


class BaseClient:
    # Default request timeout
    REQUEST_TIMEOUT: float = 10.0

    def __init__(
            self,
            api_key: Optional[str] = None,
            api_secret: Optional[str] = None,
            requests_params: Optional[Dict[str, Any]] = None,
            tld: str = "com",
            base_endpoint: str = "",
            testnet: bool = False,
            private_key: Optional[Union[str, Path]] = None,
            private_key_pass: Optional[str] = None,
    ):
        # Set the top level domain
        self.tld = tld

        # Set the API key and secret
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        # Set whether the client is using RSA or ECC
        self._is_rsa = False
        # Set the private key
        self.PRIVATE_KEY: Any = self._init_private_key(private_key, private_key_pass)
        # Set the session
        self.session = self._init_session()
        # Set the requests parameters
        self._requests_params = requests_params
        # Set the response
        self.response = None
        # Set whether the client is using testnet
        self.testnet = testnet
        # Set the timestamp offset
        self.timestamp_offset = 0

    def _get_headers(self) -> Dict:
        # Set the headers
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
            # noqa
        }
        # Add the API key to the headers if it exists
        if self.API_KEY:
            assert self.API_KEY
            headers["X-MBX-APIKEY"] = self.API_KEY
        return headers

    def _init_session(self):
        raise NotImplementedError

    def _init_private_key(
            self,
            private_key: Optional[Union[str, Path]],
            private_key_pass: Optional[str] = None,
    ):
        # If no private key is provided, return
        if not private_key:
            return
        # If the private key is a Path object, read it
        if isinstance(private_key, Path):
            with open(private_key, "r") as f:
                private_key = f.read()
        # If the private key is longer than 120 characters, it is RSA
        if len(private_key) > 120:
            self._is_rsa = True
            return RSA.import_key(private_key, passphrase=private_key_pass)
        # Otherwise, it is ECC
        return ECC.import_key(private_key)

    def _rsa_signature(self, query_string: str):
        # Generate the RSA signature
        assert self.PRIVATE_KEY
        h = SHA256.new(query_string.encode("utf-8"))
        signature = pkcs1_15.new(self.PRIVATE_KEY).sign(h)  # type: ignore
        return b64encode(signature).decode()

    def _ed25519_signature(self, query_string: str):
        # Generate the Ed25519 signature
        assert self.PRIVATE_KEY
        return b64encode(
            eddsa.new(self.PRIVATE_KEY, "rfc8032").sign(query_string.encode())
        ).decode()  # type: ignore

    def _hmac_signature(self, query_string: str) -> str:
        # Generate the HMAC signature
        assert self.API_SECRET, "API Secret required for private endpoints"
        m = hmac.new(
            self.API_SECRET.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        )
        return m.hexdigest()

    def _generate_signature(self, data: Dict) -> str:
        # Generate the signature
        sig_func = self._hmac_signature
        if self.PRIVATE_KEY:
            if self._is_rsa:
                sig_func = self._rsa_signature
            else:
                sig_func = self._ed25519_signature
        query_string = "&".join([f"{d[0]}={d[1]}" for d in self._order_params(data)])
        return sig_func(query_string)

    @staticmethod
    def _get_version(version: int, **kwargs) -> int:
        # Get the version
        if "data" in kwargs and "version" in kwargs["data"]:
            version_override = kwargs["data"].get("version")
            del kwargs["data"]["version"]
            return version_override
        return version

    @staticmethod
    def uuid22(length=22):
        # Generate a random UUID
        return format(random.getrandbits(length * 4), "x")

    @staticmethod
    def _order_params(data: Dict) -> List[Tuple[str, str]]:
        """Convert params to list with signature as last element

        :param data:
        :return:

        """
        # Remove any arguments with values of None
        data = dict(filter(lambda el: el[1] is not None, data.items()))
        # Set the signature as the last element
        has_signature = False
        params = []
        for key, value in data.items():
            if key == "signature":
                has_signature = True
            else:
                params.append((key, str(value)))
        # sort parameters by key
        params.sort(key=itemgetter(0))
        if has_signature:
            params.append(("signature", data["signature"]))
        return params

    def _get_request_kwargs(
            self, method, signed: bool, force_params: bool = False, **kwargs
    ) -> Dict:
        # set default requests timeout
        kwargs["timeout"] = self.REQUEST_TIMEOUT

        # add our global requests params
        if self._requests_params:
            kwargs.update(self._requests_params)

        data = kwargs.get("data", None)
        if data and isinstance(data, dict):
            kwargs["data"] = data
            # find any requests params passed and apply them
            if "requests_params" in kwargs["data"]:
                # merge requests params into kwargs
                kwargs.update(kwargs["data"]["requests_params"])
                del kwargs["data"]["requests_params"]

        if signed:
            # generate signature
            kwargs["data"]["timestamp"] = int(
                time.time() * 1000 + self.timestamp_offset
            )
            kwargs["data"]["signature"] = self._generate_signature(kwargs["data"])

        # sort get and post params to match signature order
        if data:
            # sort post params and remove any arguments with values of None
            kwargs["data"] = self._order_params(kwargs["data"])
            # Remove any arguments with values of None.
            null_args = [
                i for i, (key, value) in enumerate(kwargs["data"]) if value is None
            ]
            for i in reversed(null_args):
                del kwargs["data"][i]

        # if get request assign data array to params value for requests lib
        if data and (method == "get" or force_params):
            kwargs["params"] = "&".join(
                "%s=%s" % (data[0], data[1]) for data in kwargs["data"]
            )
            del kwargs["data"]

        # Temporary fix for Signature issue while using batchOrders in AsyncClient
        if "params" in kwargs.keys() and "batchOrders" in kwargs["params"]:
            kwargs["data"] = kwargs["params"]
            del kwargs["params"]

        return kwargs


class Client(BaseClient):
    def __init__(
            self,
            api_key: Optional[str] = None,
            api_secret: Optional[str] = None,
            requests_params: Optional[Dict[str, Any]] = None,
            tld: str = "com",
            base_endpoint: str = "",
            testnet: bool = False,
            private_key: Optional[Union[str, Path]] = None,
            private_key_pass: Optional[str] = None,
            ping: Optional[bool] = True,
    ):
        super().__init__(
            api_key,
            api_secret,
            requests_params,
            tld,
            base_endpoint,
            testnet,
            private_key,
            private_key_pass,
        )

    def _init_session(self) -> requests.Session:
        # Set the headers
        headers = self._get_headers()

        # Set the session
        session = requests.session()
        session.headers.update(headers)
        return session

    def _request(
            self, method, uri: str, signed: bool, force_params: bool = False, **kwargs
    ):
        # Get the request kwargs
        kwargs = self._get_request_kwargs(method, signed, force_params, **kwargs)

        # Make the request
        self.response = getattr(self.session, method)(uri, **kwargs)
        return self._handle_response(self.response)

    @staticmethod
    def _handle_response(response: requests.Response):
        """Internal helper for handling API responses from the server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """
        # If the response is not successful, raise an exception
        if not (200 <= response.status_code < 300):
            raise Exception(response, response.status_code, response.text)
        try:
            # Return the response
            return response.json()
        except ValueError:
            # If the response is not JSON, raise an exception
            raise Exception(f"Invalid Response: {response.text}")


class AsyncClient(BaseClient):
    def __init__(
            self,
            api_key: Optional[str] = None,
            api_secret: Optional[str] = None,
            requests_params: Optional[Dict[str, Any]] = None,
            tld: str = "com",
            base_endpoint: str = "",
            testnet: bool = False,
            loop=None,
            session_params: Optional[Dict[str, Any]] = None,
            private_key: Optional[Union[str, Path]] = None,
            private_key_pass: Optional[str] = None,
            https_proxy: Optional[str] = None,
    ):
        # Set the https proxy
        self.https_proxy = https_proxy
        # Set the loop
        self.loop = loop
        # Set the session parameters
        self._session_params: Dict[str, Any] = session_params or {}
        super().__init__(
            api_key,
            api_secret,
            requests_params,
            tld,
            base_endpoint,
            testnet,
            private_key,
            private_key_pass,
        )

    def _init_session(self) -> aiohttp.ClientSession:
        # Set the session
        session = aiohttp.ClientSession(
            loop=self.loop, headers=self._get_headers(), **self._session_params
        )
        return session

    async def close_connection(self):
        # Close the connection
        if self.session:
            assert self.session
            await self.session.close()

    async def _request(
            self, method, uri: str, signed: bool, force_params: bool = False, **kwargs
    ):
        # Get the request kwargs
        kwargs = self._get_request_kwargs(method, signed, force_params, **kwargs)

        # Make the request
        async with getattr(self.session, method)(
                uri, proxy=self.https_proxy, **kwargs
        ) as response:
            self.response = response
            return await self._handle_response(response)

    async def _handle_response(self, response: aiohttp.ClientResponse):
        """Internal helper for handling API responses from the server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """
        # If the response is not successful, raise an exception
        if not str(response.status).startswith("2"):
            raise Exception(response, response.status, await response.text())
        try:
            # Return the response
            return await response.json()
        except ValueError:
            # If the response is not JSON, raise an exception
            txt = await response.text()
            raise Exception(f"Invalid Response: {txt}")