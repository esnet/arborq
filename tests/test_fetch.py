import datetime
import os

import pytest
import pytz

from pypond.series import TimeSeries

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

    end = datetime.datetime.now(pytz.UTC)
    begin = end - datetime.timedelta(1)

    q = arborq.ArborQuery("traffic", begin, end)  # pylint: disable=invalid-name

    q.add_filter("customer", arbor_id)
    q.add_filter("customer", None)

    fetcher = arborq.ArborFetcher(arbor_url, arbor_key, q)
    fetcher.fetch()

    timeseries = fetcher.to_timeseries()

    for series in timeseries:
        assert isinstance(series, TimeSeries)
        assert len([x for x in series.events()]) > 0



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

    assert len([timeseries.events()]) > 0

    for point in timeseries.events():
        print point.get("ip_addr"), point.get("dns_name")
        assert point.get("ip_addr").endswith(".xxx")
        assert point.get("dns_name").startswith("xxx") or point.get("dns_name") == "[No DNS Entry]"

    unredacted = arborq.TopTalkerParser(fetcher.xml_data, redact=False).parse()
    for point in unredacted.events():
        assert not point.get("ip_addr").endswith(".xxx")
        assert int(point.get("ip_addr").split(".")[-1]) < 256
        assert not point.get("dns_name").startswith("xxx.")

    no_dns = arborq.TopTalkerParser(fetcher.xml_data, resolve_dns=False).parse()
    for point in no_dns.events():
        assert point.get("dns_name") == "[DNS resolution not enabled]"

    unredacted_no_dns = arborq.TopTalkerParser(fetcher.xml_data,
                                               redact=False, resolve_dns=False).parse()
    for point in unredacted_no_dns.events():
        assert not point.get("ip_addr").endswith(".xxx")
        assert int(point.get("ip_addr").split(".")[-1]) < 256
        assert point.get("dns_name") == "[DNS resolution not enabled]"


def test_fetch_connection_failure():
    q = arborq.ArborQuery("gossip", timeperiod="1d")  # pylint: disable=invalid-name
    q.add_filter("customer", 1)

    with pytest.raises(arborq.ArborFetcherError):
        arborq.ArborFetcher("https://localhost:9999/", "foobar", q).fetch()
