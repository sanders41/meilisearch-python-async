from datetime import datetime

import pytest
from httpx import Response

from meilisearch_python_async._http_requests import HttpRequests
from meilisearch_python_async.errors import MeiliSearchApiError
from meilisearch_python_async.index import Index
from meilisearch_python_async.models.settings import (
    MeiliSearchSettings,
    MinWordLengthForTypo,
    TypoTolerance,
)
from meilisearch_python_async.task import wait_for_task


@pytest.fixture
def new_settings():
    return MeiliSearchSettings(
        ranking_rules=["typo", "words"],
        searchable_attributes=["title", "overview"],
        sortable_attributes=["genre", "title"],
        typo_tolerance=TypoTolerance(enabled=False),
    )


@pytest.fixture
def default_ranking_rules():
    return ["words", "typo", "proximity", "attribute", "sort", "exactness"]


@pytest.fixture
def new_ranking_rules():
    return ["typo", "exactness"]


@pytest.fixture
def new_distinct_attribute():
    return "title"


@pytest.fixture
def default_distinct_attribute():
    return None


@pytest.fixture
def new_searchable_attributes():
    return ["something", "random"]


@pytest.fixture
def displayed_attributes():
    return ["id", "release_date", "title", "poster", "overview", "genre"]


@pytest.fixture
def new_stop_words():
    return ["of", "the"]


@pytest.fixture
def new_synonyms():
    return {"hp": ["harry potter"]}


@pytest.fixture
def filterable_attributes():
    return ["release_date", "title"]


@pytest.fixture
def sortable_attributes():
    return ["genre", "title"]


@pytest.mark.asyncio
@pytest.mark.usefixtures("indexes_sample")
async def test_delete_index(test_client, index_uid, index_uid2):
    response = await test_client.index(uid=index_uid).delete()
    await wait_for_task(test_client.http_client, response.uid)

    with pytest.raises(MeiliSearchApiError):
        await test_client.get_index(uid=index_uid)

    response = await test_client.index(uid=index_uid2).delete()
    await wait_for_task(test_client.http_client, response.uid)

    with pytest.raises(MeiliSearchApiError):
        await test_client.get_index(uid=index_uid2)

    indexes = await test_client.get_indexes()
    assert indexes is None


@pytest.mark.asyncio
@pytest.mark.usefixtures("indexes_sample")
async def test_update_index(test_client, index_uid):
    index = test_client.index(uid=index_uid)
    await index.update(primary_key="objectID")

    assert index.primary_key == "objectID"
    assert await index.get_primary_key() == "objectID"


@pytest.mark.asyncio
async def test_get_stats(empty_index, small_movies):
    index = await empty_index()
    update = await index.add_documents(small_movies)
    await wait_for_task(index.http_client, update.uid)
    response = await index.get_stats()

    assert response.number_of_documents == 30


@pytest.mark.asyncio
async def test_get_settings_default(empty_index, default_ranking_rules):
    index = await empty_index()
    response = await index.get_settings()
    assert response.ranking_rules == default_ranking_rules
    assert response.distinct_attribute is None
    assert response.searchable_attributes == ["*"]
    assert response.displayed_attributes == ["*"]
    assert response.stop_words == []
    assert response.synonyms == {}
    assert response.sortable_attributes == []
    assert response.typo_tolerance.enabled is True


@pytest.mark.asyncio
async def test_update_settings(empty_index, new_settings):
    index = await empty_index()
    response = await index.update_settings(new_settings)
    update = await wait_for_task(index.http_client, response.uid)
    assert update.status == "succeeded"
    response = await index.get_settings()
    assert response.ranking_rules == new_settings.ranking_rules
    assert response.distinct_attribute is None
    assert response.searchable_attributes == new_settings.searchable_attributes
    assert response.displayed_attributes == ["*"]
    assert response.stop_words == []
    assert response.synonyms == {}
    assert response.sortable_attributes == new_settings.sortable_attributes
    assert response.typo_tolerance.enabled is False


@pytest.mark.asyncio
async def test_reset_settings(empty_index, new_settings, default_ranking_rules):
    index = await empty_index()
    response = await index.update_settings(new_settings)
    update = await wait_for_task(index.http_client, response.uid)
    assert update.status == "succeeded"
    response = await index.get_settings()
    assert response.ranking_rules == new_settings.ranking_rules
    assert response.distinct_attribute is None
    assert response.searchable_attributes == new_settings.searchable_attributes
    assert response.displayed_attributes == ["*"]
    assert response.stop_words == []
    assert response.synonyms == {}
    assert response.sortable_attributes == new_settings.sortable_attributes
    assert response.typo_tolerance.enabled is False
    response = await index.reset_settings()
    update = await wait_for_task(index.http_client, response.uid)
    assert update.status == "succeeded"
    response = await index.get_settings()
    assert response.ranking_rules == default_ranking_rules
    assert response.distinct_attribute is None
    assert response.displayed_attributes == ["*"]
    assert response.searchable_attributes == ["*"]
    assert response.stop_words == []
    assert response.synonyms == {}
    assert response.sortable_attributes == []
    assert response.typo_tolerance.enabled is True


@pytest.mark.asyncio
async def test_get_ranking_rules_default(empty_index, default_ranking_rules):
    index = await empty_index()
    response = await index.get_ranking_rules()
    assert response == default_ranking_rules


@pytest.mark.asyncio
async def test_update_ranking_rules(empty_index, new_ranking_rules):
    index = await empty_index()
    response = await index.update_ranking_rules(new_ranking_rules)
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_ranking_rules()
    assert response == new_ranking_rules


@pytest.mark.asyncio
async def test_reset_ranking_rules(empty_index, new_ranking_rules, default_ranking_rules):
    index = await empty_index()
    response = await index.update_ranking_rules(new_ranking_rules)
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_ranking_rules()
    assert response == new_ranking_rules
    response = await index.reset_ranking_rules()
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_ranking_rules()
    assert response == default_ranking_rules


@pytest.mark.asyncio
async def test_get_distinct_attribute(empty_index, default_distinct_attribute):
    index = await empty_index()
    response = await index.get_distinct_attribute()
    assert response == default_distinct_attribute


@pytest.mark.asyncio
async def test_update_distinct_attribute(empty_index, new_distinct_attribute):
    index = await empty_index()
    response = await index.update_distinct_attribute(new_distinct_attribute)
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_distinct_attribute()
    assert response == new_distinct_attribute


@pytest.mark.asyncio
async def test_reset_distinct_attribute(
    empty_index, new_distinct_attribute, default_distinct_attribute
):
    index = await empty_index()
    response = await index.update_distinct_attribute(new_distinct_attribute)
    update = await wait_for_task(index.http_client, response.uid)
    assert update.status == "succeeded"
    response = await index.get_distinct_attribute()
    assert response == new_distinct_attribute
    response = await index.reset_distinct_attribute()
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_distinct_attribute()
    assert response == default_distinct_attribute


@pytest.mark.asyncio
async def test_get_searchable_attributes(empty_index, small_movies):
    index = await empty_index()
    response = await index.get_searchable_attributes()
    assert response == ["*"]
    response = await index.add_documents(small_movies, primary_key="id")
    await wait_for_task(index.http_client, response.uid)
    get_attributes = await index.get_searchable_attributes()
    assert get_attributes == ["*"]


@pytest.mark.asyncio
async def test_update_searchable_attributes(empty_index, new_searchable_attributes):
    index = await empty_index()
    response = await index.update_searchable_attributes(new_searchable_attributes)
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_searchable_attributes()
    assert response == new_searchable_attributes


@pytest.mark.asyncio
async def test_reset_searchable_attributes(empty_index, new_searchable_attributes):
    index = await empty_index()
    response = await index.update_searchable_attributes(new_searchable_attributes)
    update = await wait_for_task(index.http_client, response.uid)
    assert update.status == "succeeded"
    response = await index.get_searchable_attributes()
    assert response == new_searchable_attributes
    response = await index.reset_searchable_attributes()
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_searchable_attributes()
    assert response == ["*"]


@pytest.mark.asyncio
async def test_get_displayed_attributes(empty_index, small_movies):
    index = await empty_index()
    response = await index.get_displayed_attributes()
    assert response == ["*"]
    response = await index.add_documents(small_movies)
    await wait_for_task(index.http_client, response.uid)
    get_attributes = await index.get_displayed_attributes()
    assert get_attributes == ["*"]


@pytest.mark.asyncio
async def test_update_displayed_attributes(empty_index, displayed_attributes):
    index = await empty_index()
    response = await index.update_displayed_attributes(displayed_attributes)
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_displayed_attributes()
    assert response == displayed_attributes


@pytest.mark.asyncio
async def test_reset_displayed_attributes(empty_index, displayed_attributes):
    index = await empty_index()
    response = await index.update_displayed_attributes(displayed_attributes)
    update = await wait_for_task(index.http_client, response.uid)
    assert update.status == "succeeded"
    response = await index.get_displayed_attributes()
    assert response == displayed_attributes
    response = await index.reset_displayed_attributes()
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_displayed_attributes()
    assert response == ["*"]


@pytest.mark.asyncio
async def test_get_stop_words_default(empty_index):
    index = await empty_index()
    response = await index.get_stop_words()
    assert response is None


@pytest.mark.asyncio
async def test_update_stop_words(empty_index, new_stop_words):
    index = await empty_index()
    response = await index.update_stop_words(new_stop_words)
    update = await wait_for_task(index.http_client, response.uid)
    assert update.status == "succeeded"
    response = await index.get_stop_words()
    assert response == new_stop_words


@pytest.mark.asyncio
async def test_reset_stop_words(empty_index, new_stop_words):
    index = await empty_index()
    response = await index.update_stop_words(new_stop_words)
    update = await wait_for_task(index.http_client, response.uid)
    assert update.status == "succeeded"
    response = await index.get_stop_words()
    assert response == new_stop_words
    response = await index.reset_stop_words()
    update = await wait_for_task(index.http_client, response.uid)
    assert update.status == "succeeded"
    response = await index.get_stop_words()
    assert response is None


@pytest.mark.asyncio
async def test_get_synonyms_default(empty_index):
    index = await empty_index()
    response = await index.get_synonyms()
    assert response is None


@pytest.mark.asyncio
async def test_update_synonyms(empty_index, new_synonyms):
    index = await empty_index()
    response = await index.update_synonyms(new_synonyms)
    update = await wait_for_task(index.http_client, response.uid)
    assert update.status == "succeeded"
    response = await index.get_synonyms()
    assert response == new_synonyms


@pytest.mark.asyncio
async def test_reset_synonyms(empty_index, new_synonyms):
    index = await empty_index()
    response = await index.update_synonyms(new_synonyms)
    update = await wait_for_task(index.http_client, response.uid)
    assert update.status == "succeeded"
    response = await index.get_synonyms()
    assert response == new_synonyms
    response = await index.reset_synonyms()
    update = await wait_for_task(index.http_client, response.uid)
    assert update.status == "succeeded"
    response = await index.get_synonyms()
    assert response is None


@pytest.mark.asyncio
async def test_get_filterable_attributes(empty_index):
    index = await empty_index()
    response = await index.get_filterable_attributes()
    assert response is None


@pytest.mark.asyncio
async def test_update_filterable_attributes(empty_index, filterable_attributes):
    index = await empty_index()
    response = await index.update_filterable_attributes(filterable_attributes)
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_filterable_attributes()
    assert sorted(response) == filterable_attributes


@pytest.mark.asyncio
async def test_reset_filterable_attributes(empty_index, filterable_attributes):
    index = await empty_index()
    response = await index.update_filterable_attributes(filterable_attributes)
    update = await wait_for_task(index.http_client, response.uid)
    assert update.status == "succeeded"
    response = await index.get_filterable_attributes()
    assert sorted(response) == filterable_attributes
    response = await index.reset_filterable_attributes()
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_filterable_attributes()
    assert response is None


@pytest.mark.asyncio
async def test_get_sortable_attributes(empty_index):
    index = await empty_index()
    response = await index.get_sortable_attributes()
    assert response == []


@pytest.mark.asyncio
async def test_update_sortable_attributes(empty_index, sortable_attributes):
    index = await empty_index()
    response = await index.update_sortable_attributes(sortable_attributes)
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_sortable_attributes()
    assert sorted(response) == sortable_attributes


@pytest.mark.asyncio
async def test_reset_sortable_attributes(empty_index, sortable_attributes):
    index = await empty_index()
    response = await index.update_sortable_attributes(sortable_attributes)
    update = await wait_for_task(index.http_client, response.uid)
    assert update.status == "succeeded"
    response = await index.get_sortable_attributes()
    assert response == sortable_attributes
    response = await index.reset_sortable_attributes()
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_sortable_attributes()
    assert response == []


async def test_get_typo_tolerance(empty_index):
    index = await empty_index()
    response = await index.get_typo_tolerance()
    assert response.enabled is True


async def test_update_typo_tolerance(empty_index):
    typo_tolerance = TypoTolerance(
        enabled=True,
        disable_on_attributes=["title"],
        disable_on_words=["spiderman"],
        min_word_length_for_typo=MinWordLengthForTypo(one_typo=10, two_typos=20),
    )
    index = await empty_index()
    response = await index.update_typo_tolerance(typo_tolerance)
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_typo_tolerance()
    assert response.dict() == typo_tolerance.dict()


async def test_reset_typo_tolerance(empty_index):
    index = await empty_index()
    response = await index.update_typo_tolerance(TypoTolerance(enabled=False))
    await wait_for_task(index.http_client, response.uid)
    response = await index.reset_typo_tolerance()
    await wait_for_task(index.http_client, response.uid)
    response = await index.get_typo_tolerance()
    assert response.enabled is True


@pytest.mark.parametrize(
    "iso_date, expected",
    [
        ("2021-05-11T03:12:22.563960100Z", datetime(2021, 5, 11, 3, 12, 22, 563960)),
        (datetime(2021, 5, 11, 3, 12, 22, 563960), datetime(2021, 5, 11, 3, 12, 22, 563960)),
        (None, None),
    ],
)
def test_iso_to_date_time(iso_date, expected, test_client):
    index = Index(test_client, "test")
    converted = index._iso_to_date_time(iso_date)

    assert converted == expected


@pytest.mark.asyncio
async def test_str(empty_index):
    index = await empty_index()
    got = index.__str__()

    assert "uid" in got
    assert "primary_key" in got
    assert "created_at" in got
    assert "updated_at" in got


@pytest.mark.asyncio
async def test_repr(empty_index):
    index = await empty_index()
    got = index.__repr__()

    assert "uid" in got
    assert "primary_key" in got
    assert "created_at" in got
    assert "updated_at" in got


@pytest.mark.asyncio
@pytest.mark.usefixtures("indexes_sample")
async def test_delete_if_exists(test_client, index_uid):
    assert await test_client.get_index(uid=index_uid)
    deleted = await test_client.index(index_uid).delete_if_exists()
    assert deleted is True
    with pytest.raises(MeiliSearchApiError):
        await test_client.get_index(uid=index_uid)


@pytest.mark.asyncio
async def test_delete_if_exists_no_delete(test_client):
    with pytest.raises(MeiliSearchApiError):
        await test_client.get_index(uid="none")

    deleted = await test_client.index("none").delete_if_exists()
    assert deleted is False


@pytest.mark.asyncio
@pytest.mark.usefixtures("indexes_sample")
async def test_delete_if_exists_error(test_client, index_uid, monkeypatch):
    async def mock_response(*args, **kwargs):
        raise MeiliSearchApiError("test", Response(status_code=404))

    monkeypatch.setattr(HttpRequests, "_send_request", mock_response)
    with pytest.raises(MeiliSearchApiError):
        await test_client.index(index_uid).delete_if_exists()


@pytest.mark.asyncio
@pytest.mark.usefixtures("indexes_sample")
async def test_delete_index_if_exists(test_client, index_uid):
    assert await test_client.get_index(uid=index_uid)
    deleted = await test_client.delete_index_if_exists(index_uid)
    assert deleted is True
    with pytest.raises(MeiliSearchApiError):
        await test_client.get_index(uid=index_uid)


@pytest.mark.asyncio
async def test_delete_index_if_exists_no_delete(test_client):
    with pytest.raises(MeiliSearchApiError):
        await test_client.get_index(uid="none")

    deleted = await test_client.delete_index_if_exists("none")
    assert deleted is False


@pytest.mark.asyncio
@pytest.mark.usefixtures("indexes_sample")
async def test_delete_index_if_exists_error(test_client, index_uid, monkeypatch):
    async def mock_response(*args, **kwargs):
        raise MeiliSearchApiError("test", Response(status_code=404))

    monkeypatch.setattr(HttpRequests, "_send_request", mock_response)
    with pytest.raises(MeiliSearchApiError):
        await test_client.delete_index_if_exists(index_uid)
