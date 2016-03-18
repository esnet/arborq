import cStringIO
import socket
import xml.etree.ElementTree as xml

import requests

# TODO:
# support for AS inclusion like old setup, filter2
# improve DNS resolution

TIMEPERIODS = {
    '1d': 'day',
    '7d': 'week',
    '30d': 'month',
    '1y': 'year',
}


class ArborQuery(object):
    """Build XML queries for Arbor PeakFlow SP.

    :param qtype: the type of query, currently one of "traffic" or "gossip"
    :param begin_time: a `datetime.datetime` object specifying the begin time
    :param end_time: a `datetime.datetime` object specifying the end time
    :param timeperiod: one of the time periods specified in `TIMEPERIODS`
    :param units: which units to use, defaults to bps
    :param limit: how many responses to request, defaults to 200
    :param peakflow_version: version to send with the request, defaults to "1.0"
    :param peakflow_release: release to send with the request, defaults to "5.5"
    """

    def __init__(self, qtype, begin_time=None, end_time=None,
                 timeperiod=None, unit='bps', limit=200,
                 peakflow_version="1.0", peakflow_release="5.5"):
        self.qtype = qtype

        if begin_time is not None:
            self.begin_time = begin_time.strftime('%m/%d/%Y %H:%M:%S')
        else:
            self.begin_time = None
        if end_time is not None:
            self.end_time = end_time.strftime('%m/%d/%Y %H:%M:%S')
        else:
            self.end_time = None
        self.timeperiod = timeperiod

        self.unit = unit
        self.limit = str(limit)
        self.peakflow_version = peakflow_version
        self.peakflow_release = peakflow_release

        self.xmlquery = self._build_xmlquery_skeleton()

    def _build_xmlquery_skeleton(self):
        """Build the basic query skeleton."""

        query = xml.Element("query", {'id': 'query1', 'type': self.qtype})
        if self.qtype == "gossip":
            if self.timeperiod in TIMEPERIODS:
                query.append(xml.Element("time", {
                    'period_ascii': TIMEPERIODS[self.timeperiod]}))
            else:
                # otherwise just default to one day
                query.append(xml.Element("time", {'period_ascii': "day"}))
        else:
            query.append(xml.Element("time", {
                'start_ascii': self.begin_time,
                'end_ascii': self.end_time
            }))

        query.append(xml.Element("unit", {'type': self.unit}))
        query.append(xml.Element("search", {'limit': self.limit}))

        return query

    def add_filter(self, filter_name, value=None):
        """Add a filter to the query."""
        filter = xml.Element("filter", {'type': filter_name, 'binby': '1'})

        if value:
            if not type(value) == list:
                value = [value]

            for val in value:
                filter.append(xml.Element("instance", {'value': str(val)}))

        self.xmlquery.append(filter)

    def get_query(self):
        """Return the XML query suitable to send to the Arbor system."""

        peakflow = xml.Element("peakflow", {
            'version': self.peakflow_version,
            'release': self.peakflow_release
        })
        peakflow.append(self.xmlquery)

        tree = xml.ElementTree(peakflow)
        xmlfile = cStringIO.StringIO()
        tree.write(xmlfile)
        output = xmlfile.getvalue()
        xmlfile.close()

        return output

    def get_timeperiod(self, data):
        # Getting the arbor returned time ranges (Which can differ from
        # the supplied time ranges esp in the end date.)
        stime = data.find('query/time').get('start_ascii')
        etime = data.find('query/time').get('end_ascii')
        return {'start': stime, 'end': etime}


class ArborFetcherError(Exception):
    pass


class ArborFetcher:
    """Fetch data from an Arbor Peakflow system.

    :param arbor_url: The URL for the Pearkflow system API.
    :param api_key: The API key to authenticate to the Peakflow system.
    :param query: a :class:`ArborQuery <ArborQuery>` instance
    :param verify_ssl_cert: Check the validity of the SSL cert?
    """

    def __init__(self, arbor_url, api_key, query, verify_ssl_cert=False):
        self.arbor_url = arbor_url
        self.api_key = api_key
        self.query = query
        self.verify_ssl_cert = verify_ssl_cert

        self.xml_data = None

    def fetch(self):
        try:
            r = requests.post(self.arbor_url + "traffic",
                              params={'api_key': self.api_key},
                              data={'query': self.query.get_query()},
                              verify=self.verify_ssl_cert)
        except requests.ConnectionError, e:
            raise ArborFetcherError(e)

        if r.status_code != requests.codes.ok:
            raise ArborFetcherError(r.text)
        else:
            self.err = None
            try:
                self.xml_data = xml.fromstring(r.text)
            except xml.etree.ElementTree.ParseError, e:
                raise ArborFetcherError("Bad response: ".format(e))
            self.response = r

    def to_timeseries(self):
        if self.xml_data is None:
            raise ArborFetcherError("No data. (Have you called .fetch()?)")

        qtype = self.xml_data.find('query').get('type')

        if qtype == "traffic":
            parser = TrafficParser(self.xml_data)
        elif qtype == "gossip":
            parser = TopTalkerParser(self.xml_data)
        else:
            raise ArborFetcherError("Unknown response type: {}".format(qtype))

        return parser.parse()


class TrafficParser:
    """Parse an Arbor traffic response into a list of Pond TimeSeries

    :param xml_data: The ElementTree of the data from the Arbor server.
    :param timestamp_scalar: Used to convert the timestamp. The default is 1000
                             to convert from unix timestamps to the JavaScript
                             convention of milliseconds since the epoch.
    """

    def __init__(self, xml_data, timestamp_scalar=1000):
        self.xml = xml_data
        self.timestamp_scalar = timestamp_scalar

    def parse(self):
        sample_info = self.xml.find("query-reply/sample_info")
        self.begin = int(sample_info.get("earliest_bin"))
        self.end = int(sample_info.get("latest_bin"))
        self.frequency = int(sample_info.get("duration"))

        items = self.xml.findall("query-reply/item")

        timeseries_list = []

        for item in items:
            timeseries_list.append(self._items_to_timeseries(item))

        return timeseries_list

    def _items_to_timeseries(self, item):
        keys = item.findall("key")
        if len(keys) == 2:
            name = keys[1].get("name")
        else:
            name = item.get("name")

        raw_points = self._get_points(item)
        points = []

        for i, data_in in enumerate(raw_points["in"]):
            time = (self.begin + (i * self.frequency)) * self.timestamp_scalar
            points.append([
                time,
                data_in,
                raw_points["out"][i]
            ])

        return {
            "name": name,
            "columns": ["time", "in", "out"],
            "points": points
        }

    def _get_points(self, item):
        points = {}
        for klass in item.findall("class"):
            direction = klass.get("type")

            points[direction] = [
                int(x) for x in klass.find("sample").get("value").split("|")
            ]

        return points


class TopTalkerParser:
    """Parse an Arbor gossip/top talkers response into a Pond TimeSeries

    :param xml_data: The ElementTree of the data from the Arbor server.
    :param redact: If True, obscure the IP addresses in the response.
    :param resolve_dns: If true, attempt to resolve DNS for each IP address.
    :param timestamp_scalar: Used to convert the timestamp. The default is 1000
                             to convert from unix timestamps to the JavaScript
                             convention of milliseconds since the epoch.
    """

    def __init__(self, xml_data, redact=True, resolve_dns=True,
                 timestamp_scalar=1000):
        self.xml = xml_data
        self.redact = redact
        self.resolve_dns = resolve_dns
        self.timestamp_scalar = timestamp_scalar

    def parse(self):
        items = self.xml.findall('query-reply/item')

        points = []
        for item in items:
            addr = item.find('key').get('id')

            if self.resolve_dns:
                dns_name = self._dns_lookup(addr)
                if self.redact:
                    parts = ['xxx']
                    parts.extend(dns_name.split('.')[1:])
                    dns_name = '.'.join(parts)
            else:
                dns_name = "[DNS resolution not enabled]"

            if self.redact:
                addr = '.'.join(addr.split('.')[:3]) + ".xxx"

            max_val = int(item.find('max').get('value'))
            time = int(item.find('time').get('value')) * self.timestamp_scalar

            points.append([time, addr, dns_name, max_val])

        return {
            "name": "top talkers",
            "columns": ["time", "ip_addr", "dns_name", "max"],
            "points": points
        }

    def _dns_lookup(self, addr):
        try:
            dns_name = socket.gethostbyaddr(addr)[0]
            if self.redact:
                parts = dns_name.split('.')
                parts[0] = "xxx"
                dns_name = ".".join(parts)
        except socket.herror:
            dns_name = "[No DNS Entry]"

        return dns_name
