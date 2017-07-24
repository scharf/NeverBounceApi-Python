"""Test the API endpoints located at /jobs"""
import json

import pytest
import responses

import neverbounce_sdk
from neverbounce_sdk import urlfor, NeverBounceAPIException


@pytest.fixture
def client():
    auth = 'secret key'
    return neverbounce_sdk.client(auth=auth)


@pytest.fixture
def tempfile(tmpdir):
    return tmpdir.join('test.csv')


@responses.activate
def test_download_defaults(client, tempfile):
    responses.add(responses.POST,
                  urlfor('jobs', 'download'),
                  body=r'data\ndata',
                  status=200,
                  content_type='application/octet-stream')

    client.download(123, tempfile, line_feed_type='LINEFEED_0A')
    assert tempfile.read() == r'data\ndata'

    called_with = json.loads(responses.calls[0].request.body)
    default_args = {
        'line_feed_type': 'LINEFEED_0A',
        'binary_operators_type': 'BIN_1_0',
        'valids': 1,
        'invalids': 1,
        'catchalls': 1,
        'unknowns': 1,
        'job_id': 123
    }

    for k,v in default_args.items():
        assert called_with[k] == v


@responses.activate
def test_download_upstream_error(client, tempfile):
    responses.add(responses.POST,
                  urlfor('jobs', 'download'),
                  status=200,
                  json={'status': 'failure'})

    with pytest.raises(NeverBounceAPIException):
        client.download(123, tempfile)


def test_malformed_download_options(client, tempfile):
    with pytest.raises(ValueError):
        client.download(123, tempfile, segmentation=('not an opt',))
    with pytest.raises(ValueError):
        client.download(123, tempfile, appends=('not an opt',))
    with pytest.raises(ValueError):
        client.download(123, tempfile, yes_no_representation='frowns')
    with pytest.raises(ValueError):
        client.download(123, tempfile, line_feed_type='emojis')
