from __future__ import annotations

from types import TracebackType
from typing import Type

from httpx import AsyncClient

from meilisearch_python_async._http_requests import _HttpRequests
from meilisearch_python_async.errors import MeiliSearchApiError
from meilisearch_python_async.index import Index
from meilisearch_python_async.models import ClientStats, DumpInfo, Health, IndexInfo, Keys, Version


class Client:
    """The client to connect to the MeiliSearchApi."""

    def __init__(self, url: str, api_key: str | None = None, *, timeout: int | None = None) -> None:
        """Class initializer.

        **Args:**

        * **url:** The url to the MeiliSearch API (ex: http://localhost:7700)
        * **api_key:** The optional API key for MeiliSearch. Defaults to None.
        * **timeout:** The amount of time in seconds that the client will wait for a response before
            timing out. Defaults to None.
        """
        self._http_client = AsyncClient(
            base_url=url, timeout=timeout, headers=self._set_headers(api_key)
        )
        self._http_requests = _HttpRequests(self._http_client)

    async def __aenter__(self) -> Client:
        return self

    async def __aexit__(
        self,
        et: Type[BaseException] | None,
        ev: Type[BaseException] | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Closes the client.

        This only needs to be used if the client was not created with a context manager.
        """
        await self._http_client.aclose()

    async def create_dump(self) -> DumpInfo:
        """Trigger the creation of a MeiliSearch dump.

        **Returns:** Information about the dump.
            https://docs.meilisearch.com/reference/api/dump.html#create-a-dump

        **Raises:**

        * **MeilisearchCommunicationError:** If there was an error communicating with the server.
        * **MeilisearchApiError:** If the MeiliSearch API returned an error.

        Usage:

        ```py
        >>> from meilisearch_async_client import Client
        >>> async with Client("http://localhost.com", "masterKey") as client:
        >>>     await client.create_dump()
        ```
        """
        response = await self._http_requests.post("dumps")
        return DumpInfo(**response.json())

    async def create_index(self, uid: str, primary_key: str | None = None) -> Index:
        """Creates a new index.

        **Args:**

        * **uid:** The index's unique identifier.
        * **primary_key:** The primary key of the documents. Defaults to None.

        **Returns:** An instance of Index containing the information of the newly created index.

        **Raises:**

        * **MeilisearchCommunicationError:** If there was an error communicating with the server.
        * **MeilisearchApiError:** If the MeiliSearch API returned an error.

        Usage:

        ```py
        >>> from meilisearch_async_client import Client
        >>> async with Client("http://localhost.com", "masterKey") as client:
        >>>     index = await client.create_index("movies")
        ```
        """
        return await Index.create(self._http_client, uid, primary_key)

    async def delete_index_if_exists(self, uid: str) -> bool:
        """Deletes an index if it already exists.

        **Args:**

        * **uid:** The index's unique identifier.

        **Returns:** True if an index was deleted for False if not.

        **Raises:**

        * **MeilisearchCommunicationError:** If there was an error communicating with the server.
        * **MeilisearchApiError:** If the MeiliSearch API returned an error.

        Usage:

        ```py
        >>> from meilisearch_async_client import Client
        >>> async with Client("http://localhost.com", "masterKey") as client:
        >>>     await client.delete_index_if_exists()
        ```
        """
        try:
            url = f"indexes/{uid}"
            await self._http_requests.delete(url)
            return True
        except MeiliSearchApiError as error:
            if error.code != "index_not_found":
                raise error
            return False

    async def get_indexes(self) -> list[Index] | None:
        """Get all indexes.

        **Returns:** A list of all indexes.

        **Raises:**
        * **MeilisearchCommunicationError:** If there was an error communicating with the server.
        * **MeilisearchApiError:** If the MeiliSearch API returned an error.

        Usage:

        ```py
        >>> from meilisearch_async_client import Client
        >>> async with Client("http://localhost.com", "masterKey") as client:
        >>>     indexes = await client.get_indexes()
        ```
        """
        response = await self._http_requests.get("indexes")

        if not response.json():
            return None

        return [
            Index(
                http_client=self._http_client,
                uid=x["uid"],
                primary_key=x["primaryKey"],
                created_at=x["createdAt"],
                updated_at=x["updatedAt"],
            )
            for x in response.json()
        ]

    async def get_index(self, uid: str) -> Index:
        """Gets a single index based on the uid of the index.

        **Args:**

        * **uid:** The index's unique identifier.

        **Returns:** An Index instance containing the information of the fetched index.

        **Raises:**

        * **MeilisearchCommunicationError:** If there was an error communicating with the server.
        * **MeilisearchApiError:** If the MeiliSearch API returned an error.

        Usage:

        ```py
        >>> from meilisearch_async_client import Client
        >>> async with Client("http://localhost.com", "masterKey") as client:
        >>>     index = await client.get_index()
        ```
        """
        return await Index(self._http_client, uid).fetch_info()

    def index(self, uid: str) -> Index:
        """Create a local reference to an index identified by UID, without making an HTTP call.

        Because no network call is made this method is not awaitable.

        **Args:**

        * **uid:** The index's unique identifier.

        **Returns:** An Index instance.

        **Raises:**

        * **MeilisearchCommunicationError:** If there was an error communicating with the server.
        * **MeilisearchApiError:** If the MeiliSearch API returned an error.

        Usage:

        ```py
        >>> from meilisearch_async_client import Client
        >>> async with Client("http://localhost.com", "masterKey") as client:
        >>>     index = client.index("movies")
        ```
        """
        return Index(self._http_client, uid=uid)

    async def get_all_stats(self) -> ClientStats:
        """Get stats for all indexes.

        **Returns:** Information about database size and all indexes.
            https://docs.meilisearch.com/reference/api/stats.html

        **Raises:**

        * **MeilisearchCommunicationError:** If there was an error communicating with the server.
        * **MeilisearchApiError:** If the MeiliSearch API returned an error.

        Usage:

        ```py
        >>> from meilisearch_async_client import Client
        >>> async with Client("http://localhost.com", "masterKey") as client:
        >>>     stats = await client.get_all_stats()
        ```
        """
        response = await self._http_requests.get("stats")
        return ClientStats(**response.json())

    async def get_dump_status(self, uid: str) -> DumpInfo:
        """Retrieve the status of a MeiliSearch dump creation.

        **Args:**
        * **uid:** The update identifier for the dump creation.

        **Returns:** Information about the dump status.
            https://docs.meilisearch.com/reference/api/dump.html#get-dump-status

        **Raises:**

        * **MeilisearchCommunicationError:** If there was an error communicating with the server.
        * **MeilisearchApiError:** If the MeiliSearch API returned an error.

        Usage:

        ```py
        >>> from meilisearch_async_client import Client
        >>> async with Client("http://localhost.com", "masterKey") as client:
        >>>     status = await client.get_dump_status("20201101-110357260")
        ```
        """
        url = f"dumps/{uid}/status"
        response = await self._http_requests.get(url)
        return DumpInfo(**response.json())

    async def get_or_create_index(self, uid: str, primary_key: str | None = None) -> Index:
        """Get an index, or create it if it doesn't exist.

        **Args:**

        * **uid:** The index's unique identifier.
        * **primary_key:** The primary key of the documents. Defaults to None.

        **Returns:** An instance of Index containing the information of the retrieved or newly created index.

        **Raises:**

        * **MeilisearchCommunicationError:** If there was an error communicating with the server.
        * **MeilisearchApiError:** If the MeiliSearch API returned an error.MeiliSearchTimeoutError: If the connection times out.
            MeiliSearchTimeoutError: If the connection times out.

        Usage:

        ```py
        >>> from meilisearch_async_client import Client
        >>> async with Client("http://localhost.com", "masterKey") as client:
        >>>     index = await client.get_or_create_index("movies")
        ```
        """
        try:
            index_instance = await self.get_index(uid)
        except MeiliSearchApiError as err:
            if "index_not_found" not in err.code:
                raise err
            index_instance = await self.create_index(uid, primary_key)
        return index_instance

    async def get_keys(self) -> Keys:
        """Gets the MeiliSearch public and private keys.

        **Returns:** The public and private keys.
            https://docs.meilisearch.com/reference/api/keys.html#get-keys

        **Raises:**

        * **MeilisearchCommunicationError:** If there was an error communicating with the server.
        * **MeilisearchApiError:** If the MeiliSearch API returned an error.

        Usage:

        ```py
        >>> from meilisearch_async_client import Client
        >>> async with Client("http://localhost.com", "masterKey") as client:
        >>>     keys = await client.get_keys()
        ```
        """
        response = await self._http_requests.get("keys")
        return Keys(**response.json())

    async def get_raw_index(self, uid: str) -> IndexInfo | None:
        """Gets the index and returns all the index information rather than an Index instance.

        **Args:**

        * **uid:** The index's unique identifier.

        **Returns:** Index information rather than an Index instance.

        **Raises:**

        * **MeilisearchCommunicationError:** If there was an error communicating with the server.
        * **MeilisearchApiError:** If the MeiliSearch API returned an error.

        Usage:

        ```py
        >>> from meilisearch_async_client import Client
        >>> async with Client("http://localhost.com", "masterKey") as client:
        >>>     index = await client.get_raw_index("movies")
        ```
        """
        response = await self._http_client.get(f"indexes/{uid}")

        if response.status_code == 404:
            return None

        return IndexInfo(**response.json())

    async def get_raw_indexes(self) -> list[IndexInfo] | None:
        """Gets all the indexes.

        Returns all the index information rather than an Index instance.

        **Returns:** A list of the Index information rather than an Index instances.

        **Raises:**

        * **MeilisearchCommunicationError:** If there was an error communicating with the server.
        * **MeilisearchApiError:** If the MeiliSearch API returned an error.

        Usage:

        ```py
        >>> from meilisearch_async_client import Client
        >>> async with Client("http://localhost.com", "masterKey") as client:
        >>>     index = await client.get_raw_indexes()
        ```
        """
        response = await self._http_requests.get("indexes")

        if not response.json():
            return None

        return [IndexInfo(**x) for x in response.json()]

    async def get_version(self) -> Version:
        """Get the MeiliSearch version.

        **Returns:** Information about the version of MeiliSearch.

        **Raises:**

        * **MeilisearchCommunicationError:** If there was an error communicating with the server.
        * **MeilisearchApiError:** If the MeiliSearch API returned an error.

        Usage:

        ```py
        >>> from meilisearch_async_client import Client
        >>> async with Client("http://localhost.com", "masterKey") as client:
        >>>     version = await client.get_version()
        ```
        """
        response = await self._http_requests.get("version")
        return Version(**response.json())

    async def health(self) -> Health:
        """Get health of the MeiliSearch server.

        **Returns:** The status of the MeiliSearch server.

        **Raises:**

        * **MeilisearchCommunicationError:** If there was an error communicating with the server.
        * **MeilisearchApiError:** If the MeiliSearch API returned an error.

        Usage:

        ```py
        >>> from meilisearch_async_client import Client
        >>> async with Client("http://localhost.com", "masterKey") as client:
        >>>     health = await client.get_healths()
        ```
        """
        response = await self._http_requests.get("health")
        return Health(**response.json())

    def _set_headers(self, api_key: str | None = None) -> dict[str, str]:
        if api_key:
            return {
                "X-Meili-Api-Key": api_key,
                "Content-Type": "application/json",
            }
        else:
            return {
                "Content-Type": "application/json",
            }
