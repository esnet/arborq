import os
import xml.etree.ElementTree as xml

import pytest

from pypond.series import TimeSeries
from pypond.util import ms_from_dt

from .context import arborq

DATADIR = os.path.join(os.path.dirname(__file__), "data")

# pytest relies on magic names for fixtures, so:
# pylint: disable=redefined-outer-name

# XXX(jdugan): can be removed when pypond lands
def is_chronological(ts):
    """Check to see if a timeseries is chronological."""
    timestamp = None
    for event in ts.collection().events():
        if timestamp:
            if event.timestamp() < timestamp:
                return False

        timestamp = event.timestamp()

    return True

@pytest.fixture
def traffic_xml():
    """Load test traffic data."""
    return xml.fromstring(open(os.path.join(DATADIR, "traffic.xml")).read())


def test_traffic_parser(traffic_xml):
    """Test traffic parser."""
    parser = arborq.TrafficParser(traffic_xml)
    timeseries_list = parser.parse()

    print len(timeseries_list)

    assert len(timeseries_list) == 7

    names = [x.name() for x in timeseries_list]
    assert names == ["tcp", "udp", "esp", "icmp", "ip", "ipv6", "ipv6-icmp"]

    ts = timeseries_list[0]

    assert isinstance(ts, TimeSeries)

    assert sorted(ts.columns()) == ["in", "out"]

    first_point = ts.at(0)
    assert first_point.get(["in"]) == 1039759104
    assert first_point.get(["out"]) == 3126717184
    assert ms_from_dt(first_point.begin()) == 1457630700000

    last_point = ts.at(-1)

    assert ms_from_dt(last_point.begin()) == 1457717100000
    assert last_point.get("in") == 1127157376
    assert last_point.get("out") == 7807356416

    assert is_chronological(ts) == True

@pytest.fixture
def top_talkers_xml():
    """Load top talkers test data."""
    return xml.fromstring(open(os.path.join(DATADIR, "toptalkers.xml")).read())


def test_top_talker_parser(top_talkers_xml):
    """Test the top talker parser."""
    parser = arborq.TopTalkerParser(top_talkers_xml, redact=False, resolve_dns=False)

    ts = parser.parse()

    assert isinstance(ts, TimeSeries)

    assert sorted(ts.columns()) == ["dns_name", "ip_addr", "max"]

    assert len([x for x in ts.events()]) == 200

    first_point = ts.at(0)
    assert ms_from_dt(first_point.begin()) == 1457928000000
    assert first_point.get("ip_addr") == "10.11.12.245"
    assert first_point.get("dns_name") == "[DNS resolution not enabled]"
    assert first_point.get("max") == 66911320

    last_point = ts.at(-1)
    assert ms_from_dt(last_point.begin()) == 1458011700000
    assert last_point.get("ip_addr") == "10.11.12.8"
    assert last_point.get("dns_name") == "[DNS resolution not enabled]"
    assert last_point.get("max") == 19755360

    assert is_chronological(ts) == True


def test_top_talker_parser_redacted(top_talkers_xml):
    """Test redacting IP address information."""
    parser = arborq.TopTalkerParser(top_talkers_xml, redact=True, resolve_dns=False)

    ts = parser.parse()

    assert isinstance(ts, TimeSeries)

    assert sorted(ts.columns()) == ["dns_name", "ip_addr", "max"]

    assert len([x for x in ts.events()]) == 200

    first_point = ts.at(0)
    assert ms_from_dt(first_point.begin()) == 1457928000000
    assert first_point.get("ip_addr") == "10.11.12.xxx"

    last_point = ts.at(-1)
    assert ms_from_dt(last_point.begin()) == 1458011700000
    assert last_point.get("ip_addr") == "10.11.12.xxx"

