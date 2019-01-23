# -*- coding: utf-8 -*-

import re
import json

import pytest

from cfenv import AppEnv

@pytest.fixture
def application(monkeypatch):
    app = {
        'application_uris': [],
        'name': 'test-app',
        'space_name': 'dev',
        'uris': [],
    }
    monkeypatch.setenv('VCAP_APPLICATION', json.dumps(app))
    return app

@pytest.fixture
def services(monkeypatch):
    services = {
        'test-credentials': [
            {
                'name': 'test-credentials',
                'label': 'user-provided',
                'plan': 'free',
                'credentials': {
                    'url': 'https://test-service.com/',
                    'username': 'user',
                    'password': 'pass',
                },
            }
        ],
        'test-database': [
            {
                'name': 'test-database',
                'label': 'webscaledb',
                'plan': 'free',
                'credentials': {
                    'url': 'https://test-service.com/',
                    'username': 'user',
                    'password': 'pass',
                },
            },
            {
                'name': 'test-database2',
                'label': 'webscaledb2',
                'plan': 'free',
                'credentials': {
                    'url': 'https://test-service2.com/',
                    'username': 'user2',
                    'password': 'pass2',
                },
            }
        ],
    }
    monkeypatch.setenv('VCAP_SERVICES', json.dumps(services))
    return services

@pytest.fixture
def env(application, services):
    return AppEnv()

class TestEnv:

    def test_name(self, env):
        assert env.name == 'test-app'

    @pytest.mark.parametrize(['raw', 'parsed'], [
        ('0', 0),
        ('1', 1),
        ('', None),
    ])
    def test_index(self, raw, parsed, env, monkeypatch):
        monkeypatch.setenv('CF_INSTANCE_INDEX', raw)
        assert env.index == parsed

    @pytest.mark.parametrize(['key', 'raw', 'parsed'], [
        ('PORT', '3000', 3000),
        ('CF_INSTANCE_PORT', '4000', 4000),
        ('VCAP_APP_PORT', '5000', 5000),
        ('VCAP_APP_PORT', '', None),
    ])
    def test_port(self, key, raw, parsed, env, monkeypatch):
        monkeypatch.setenv(key, raw)
        assert env.port == parsed

    def test_get_credential(self, env):
        assert env.get_credential('password') == 'pass'

    def test_get_credential_default(self, env):
        assert env.get_credential('missing') is None
        assert env.get_credential('missing', 'default') == 'default'

    def test_named_services(self, env):
        assert len(env.named_services['test-credentials']) == 1
        assert len(env.named_services['test-database']) == 2
        assert env.named_services['test-database'][0].name == 'test-database'
        assert env.named_services['test-database'][1].name == 'test-database2'

class TestService:

    def test_name(self, env):
        service = env.get_service(name='test-credentials')
        assert service.name == 'test-credentials'

    def test_regex(self, env):
        service = env.get_service(label=re.compile(r'^webscale'))
        assert service.name == 'test-database'

    def test_get_url(self, env):
        service = env.get_service(label='user-provided')
        url = service.get_url(url='url', username='username', password='password')
        assert url == 'https://user:pass@test-service.com/'
