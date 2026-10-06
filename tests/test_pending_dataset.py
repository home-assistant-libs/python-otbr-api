"""Test the pending dataset writers against a border router that reports verdicts.

Since openthread/ot-br-posix#3582 the router registers the dataset with the
Thread leader and answers with the leader's verdict, or with none.
"""

from http import HTTPStatus

import pytest
import python_otbr_api
from python_otbr_api import KeyFormat

from tests.test_util.aiohttp import AiohttpClientMocker

BASE_URL = "http://core-silabs-multiprotocol:8081"


async def test_create_pending_dataset_leader_unanswered(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a write the leader never answered is reported as such, not refused."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(
        f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.GATEWAY_TIMEOUT
    )

    with pytest.raises(python_otbr_api.PendingDatasetOutcomeUnknownError):
        await otbr.create_pending_dataset(python_otbr_api.PendingDataSet())


async def test_create_pending_dataset_client_timeout(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a write the client stopped waiting for is an unknown outcome too."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(f"{BASE_URL}/node/dataset/pending", exc=TimeoutError)

    with pytest.raises(python_otbr_api.PendingDatasetOutcomeUnknownError):
        await otbr.create_pending_dataset(python_otbr_api.PendingDataSet())


@pytest.mark.parametrize(("client_timeout", "expected"), [(10, 40), (60, 60)])
async def test_pending_dataset_write_waits_for_the_leader(
    aioclient_mock: AiohttpClientMocker, client_timeout: int, expected: int
) -> None:
    """Test the write waits long enough for the leader's verdict to arrive."""
    otbr = python_otbr_api.OTBR(
        BASE_URL,
        aioclient_mock.create_session(),
        client_timeout,
        key_format=KeyFormat.PASCAL_CASE,
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.CREATED)

    await otbr.create_pending_dataset(python_otbr_api.PendingDataSet())
    await otbr.set_pending_dataset_tlvs(b"")

    # The pre-write checks keep the client's timeout; only the writes wait.
    assert [t.total for t in aioclient_mock.mock_timeouts[-4:]] == [
        client_timeout,
        expected,
        client_timeout,
        expected,
    ]


async def test_set_pending_dataset_tlvs_leader_unanswered(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a write the leader never answered is reported as such, not refused."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(
        f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.GATEWAY_TIMEOUT
    )

    with pytest.raises(python_otbr_api.PendingDatasetOutcomeUnknownError):
        await otbr.set_pending_dataset_tlvs(b"")


async def test_set_pending_dataset_tlvs_client_timeout(
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test a write the client stopped waiting for is an unknown outcome too."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(f"{BASE_URL}/node/dataset/pending", exc=TimeoutError)

    with pytest.raises(python_otbr_api.PendingDatasetOutcomeUnknownError):
        await otbr.set_pending_dataset_tlvs(b"")


@pytest.mark.parametrize(
    ("body", "kwargs"),
    [
        # What the router sends when it is not attached or still busy with an
        # earlier registration: the status phrase and nothing else.
        ("bare JSON error", {"json": {"title": "Conflict", "status": 409}}),
        ("empty body", {}),
    ],
)
async def test_set_pending_dataset_tlvs_rejected_without_reason(
    aioclient_mock: AiohttpClientMocker, body: str, kwargs: dict
) -> None:
    """Test a rejection the border router did not explain."""
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)
    aioclient_mock.put(
        f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.CONFLICT, **kwargs
    )

    with pytest.raises(python_otbr_api.PendingDatasetRejectedError) as exc_info:
        await otbr.set_pending_dataset_tlvs(b"")
    assert exc_info.value.reason == "", body
    assert str(exc_info.value) == "the border router rejected the pending dataset"


@pytest.mark.parametrize(
    "writer", ["create_pending_dataset", "set_pending_dataset_tlvs"]
)
async def test_pending_dataset_write_aborted(
    aioclient_mock: AiohttpClientMocker, writer: str
) -> None:
    """Test a write aborted after it was sent is an unknown outcome, not refused.

    The router answers 409 "no longer attached" when the exchange with the
    leader was aborted after the dataset was sent, which the leader may
    have accepted.
    """
    otbr = python_otbr_api.OTBR(
        BASE_URL, aioclient_mock.create_session(), key_format=KeyFormat.PASCAL_CASE
    )

    aioclient_mock.put(
        f"{BASE_URL}/node/dataset/pending",
        json={"title": "Conflict", "status": 409, "detail": "no longer attached"},
        status=HTTPStatus.CONFLICT,
    )
    aioclient_mock.get(f"{BASE_URL}/node/dataset/pending", status=HTTPStatus.NO_CONTENT)

    with pytest.raises(python_otbr_api.PendingDatasetOutcomeUnknownError):
        if writer == "create_pending_dataset":
            await otbr.create_pending_dataset(python_otbr_api.PendingDataSet())
        else:
            await otbr.set_pending_dataset_tlvs(b"")
