import datetime
import os

import pytest

from .context import arborq


def get_credentials():
    return (
        os.environ.get("ARBOR_URL"),
        os.environ.get("ARBOR_KEY"),
        os.environ.get("ARBOR_ID")
    )


def have_credentials():
    url, key, arbor_id = get_credentials()
    return url is None or key is None or arbor_id is None


@pytest.fixture
def credentials():
    return get_credentials()


@pytest.mark.skipif(have_credentials(), reason="Arbor credentials not provided")
def test_traffic_fetch(credentials):  # pylint: disable=redefined-outer-name
    arbor_url, arbor_key, arbor_id = credentials

    end = datetime.datetime.now()
    begin = end - datetime.timedelta(1)

    q = arborq.ArborQuery("traffic", begin, end)  # pylint: disable=invalid-name

    q.add_filter("customer", arbor_id)
    q.add_filter("customer", None)

    fetcher = arborq.ArborFetcher(arbor_url, arbor_key, q)
    fetcher.fetch()

    timeseries = fetcher.to_timeseries()

    for series in timeseries:
        assert "columns" in series
        assert "name" in series
        assert "points" in series
        assert len(series["points"]) > 0

        # print series["name"]
        # print series["columns"]
        # for row in series["points"]:
        #     print row


@pytest.mark.skipif(have_credentials(), reason="Arbor credentials not provided")
def test_toptalker_fetch(credentials):  # pylint: disable=redefined-outer-name
    arbor_url, arbor_key, arbor_id = credentials

    q = arborq.ArborQuery("gossip", timeperiod="1d")  # pylint: disable=invalid-name
    q.add_filter("customer", arbor_id)
    q.add_filter("internal", None)

    fetcher = arborq.ArborFetcher(arbor_url, arbor_key, q)
    fetcher.fetch()

    # redacted and dns_resolution
    timeseries = fetcher.to_timeseries()

    assert "columns" in timeseries
    assert "name" in timeseries
    assert "points" in timeseries
    assert len(timeseries["points"]) > 0

    ip_addr_idx = timeseries["columns"].index("ip_addr")
    dns_name_idx = timeseries["columns"].index("dns_name")

    for point in timeseries["points"]:
        assert point[ip_addr_idx].endswith(".xxx")
        assert point[dns_name_idx].startswith("xxx")

    unredacted = arborq.TopTalkerParser(fetcher.xml_data, redact=False).parse()
    for point in unredacted["points"]:
        assert not point[ip_addr_idx].endswith(".xxx")
        assert int(point[ip_addr_idx].split(".")[-1]) < 256
        assert not point[dns_name_idx].startswith("xxx.")

    no_dns = arborq.TopTalkerParser(fetcher.xml_data, resolve_dns=False).parse()
    for point in no_dns["points"]:
        assert point[dns_name_idx] == "[DNS resolution not enabled]"

    unredacted_no_dns = arborq.TopTalkerParser(fetcher.xml_data,
                                               redact=False, resolve_dns=False).parse()
    for point in unredacted_no_dns["points"]:
        assert not point[ip_addr_idx].endswith(".xxx")
        assert int(point[ip_addr_idx].split(".")[-1]) < 256
        assert point[dns_name_idx] == "[DNS resolution not enabled]"


def test_fetch_connection_failure():
    q = arborq.ArborQuery("gossip", timeperiod="1d")  # pylint: disable=invalid-name
    q.add_filter("customer", 1)

    with pytest.raises(arborq.ArborFetcherError):
        arborq.ArborFetcher("https://localhost:9999/", "foobar", q).fetch()
