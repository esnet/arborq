import os
import xml.etree.ElementTree as xml

import pytest

from .context import arborq

DATADIR = os.path.join(os.path.dirname(__file__), "data")

@pytest.fixture
def traffic_xml():
    return xml.fromstring(
            open(os.path.join(DATADIR, "traffic.xml")).read())


def test_traffic_parser(traffic_xml):
    parser = arborq.TrafficParser(traffic_xml)
    timeseries_list = parser.parse()

    print len(timeseries_list)

    assert len(timeseries_list) == 7

    names = [x["name"] for x in timeseries_list]
    assert names == ["tcp", "udp", "esp", "icmp", "ip", "ipv6", "ipv6-icmp"]

    ts = timeseries_list[0]

    assert ts["columns"] == ["time", "in", "out"]

    assert ts["points"][0] == [1457630700000, 1039759104, 3126717184]
    assert ts["points"][-1] == [1457717100000, 1127157376, 7807356416]


@pytest.fixture
def top_talkers_xml():
    return xml.fromstring(
            open(os.path.join(DATADIR, "toptalkers.xml")).read())


def test_top_talker_parser(top_talkers_xml):
    parser = arborq.TopTalkerParser(top_talkers_xml, redact=False, resolve_dns=False)

    ts = parser.parse()

    assert ts["columns"] == ["time", "ip_addr", "dns_name", "max"]

    assert len(ts["points"]) == 200

    assert ts["points"][0] == [1457986500000,
                               '10.11.12.141',
                               '[DNS resolution not enabled]',
                               1852789632]

    assert ts["points"][-1] == [1458004800000,
                                '10.11.12.18',
                                '[DNS resolution not enabled]',
                                18135902]


def test_top_talker_parser_redacted(top_talkers_xml):
    parser = arborq.TopTalkerParser(top_talkers_xml, redact=True, resolve_dns=False)

    ts = parser.parse()

    assert ts["columns"] == ["time", "ip_addr", "dns_name", "max"]

    assert len(ts["points"]) == 200

    assert ts["points"][0] == [1457986500000,
                               '10.11.12.xxx',
                               '[DNS resolution not enabled]',
                               1852789632]

    assert ts["points"][-1] == [1458004800000,
                                '10.11.12.xxx',
                                '[DNS resolution not enabled]',
                                18135902]
