"""Test the API endpoints located at /jobs (except /jobs/download)"""
from __future__ import unicode_literals
import json

import pytest
import responses

import neverbounce_sdk
from neverbounce_sdk import urlfor
from neverbounce_sdk.bulk import _job_status


@pytest.fixture
def client():
    auth = 'secret key'
    return neverbounce_sdk.client(auth=auth)


def test_search(client, monkeypatch):
    # Tests that the iteration wrapper works and that client.search correctly
    # calls client.raw_search
    expected_results = [{'data': val} for val in 'abc123']

    def _search(**kwargs):
        if not kwargs:
            kwargs=dict(job_id=None, filename=None, show_only=None,
                        page=0, items_per_page=10)
        return dict(results=expected_results,
                    total_pages=1,
                    query=kwargs)

    monkeypatch.setattr(client, 'raw_search', _search)
    results = client.search()
    for res, exp in zip(iter(results), expected_results):
        assert res == exp


def test_results(client, monkeypatch):
    # Tests that the iteration wrapper works and that client.results correctly
    # calls client.raw_results
    expected_results = [{'data': val} for val in 'abc123']

    def _results(job_id=0, **kwargs):
        if not kwargs:
            kwargs=dict(filename=None, show_only=None,
                        page=0, items_per_page=10)
        return dict(results=expected_results,
                    total_pages=1,
                    query=kwargs)

    monkeypatch.setattr(client, 'raw_results', _results)
    results = client.results(0)
    for res, exp in zip(iter(results), expected_results):
        assert res == exp


@responses.activate
def test_raw_result_interface(client):
    responses.add(responses.GET,
                  urlfor('jobs', 'results'),
                  status=200,
                  json={'status': 'success'})

    client.raw_results(123)
    for arg in ('job_id=123', 'page=1', 'items_per_page=10'):
        assert arg in responses.calls[0].request.url


@responses.activate
def test_raw_search_interface(client):
    responses.add(responses.GET,
                  urlfor('jobs', 'search'),
                  status=200,
                  json={'status': 'success'})

    # defaults
    client.raw_search()
    request_url = responses.calls[0].request.url
    for arg in ('job_id', 'filename') + tuple(_job_status):
        assert arg not in request_url
    for arg in ('page=1', 'items_per_page=10'):
        assert arg in request_url

    client.raw_search(job_id=123, filename='test.csv', show_only='completed')
    request_url = responses.calls[1].request.url
    for arg in ('page=1', 'items_per_page=10', 'job_id=123',
                'filename=test.csv', 'completed=1'):
        assert arg in request_url

    with pytest.raises(ValueError):
        client.raw_search(show_only='some unknown value OH NO')


@responses.activate
def test_create(client):
    responses.add(responses.POST,
                  urlfor('jobs', 'create'),
                  json={'status': 'success'},
                  status=200)

    raw_args = dict(input=['test@example.com'],
                    input_location='supplied',
                    auto_parse=0, auto_run=0, as_sample=0)

    client.create(['test@example.com'])
    called_with = json.loads(responses.calls[0].request.body.decode('UTF-8'))
    assert 'filename' not in called_with
    for k,v in raw_args.items():
        assert called_with[k] == v

    new_raw_args = raw_args.copy()
    new_raw_args['filename'] = 'testfile.csv'
    client.create(['test@example.com'], filename='testfile.csv')
    called_with = json.loads(responses.calls[1].request.body.decode('UTF-8'))
    for k,v in raw_args.items():
        assert called_with[k] == v


@responses.activate
def test_parse(client):
    responses.add(responses.POST,
                  urlfor('jobs', 'parse'),
                  json={'status': 'success'},
                  status=200)

    client.parse(123)
    called_with = json.loads(responses.calls[0].request.body.decode('UTF-8'))
    expected_args = dict(job_id=123, auto_start=1)
    for k,v in expected_args.items():
        assert called_with[k] == v


@responses.activate
def test_start(client):
    responses.add(responses.POST,
                  urlfor('jobs', 'start'),
                  json={'status': 'success'},
                  status=200)

    client.start(123)
    called_with = json.loads(responses.calls[0].request.body.decode('UTF-8'))
    expected_args = dict(job_id=123, run_sample=0)
    for k,v in expected_args.items():
        assert called_with[k] == v


@responses.activate
def test_status(client):
    responses.add(responses.GET,
                  urlfor('jobs', 'status'),
                  json={'status': 'success'},
                  status=200)

    client.status(123)
    assert 'job_id=123' in responses.calls[0].request.url


@responses.activate
def test_delete(client):
    responses.add(responses.GET,
                  urlfor('jobs', 'delete'),
                  json={'status': 'success'},
                  status=200)

    client.delete(123)
    assert 'job_id=123' in responses.calls[0].request.url
