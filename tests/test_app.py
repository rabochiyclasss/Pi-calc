import pytest
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200


def test_index_returns_json(client):
    response = client.get('/')
    data = response.get_json()
    assert 'endpoints' in data


def test_calculate_pi_missing_n(client):
    response = client.get('/calculate_pi')
    assert response.status_code == 400


def test_calculate_pi_negative_n(client):
    response = client.get('/calculate_pi?n=-5')
    assert response.status_code == 400


@patch('app.calculate_pi_task')
def test_calculate_pi_valid(mock_task, client):
    mock_task.apply_async.return_value = MagicMock(id='test-task-id')
    response = client.get('/calculate_pi?n=10')
    assert response.status_code == 202
    data = response.get_json()
    assert 'task_id' in data


def test_check_progress_missing_task_id(client):
    response = client.get('/check_progress')
    assert response.status_code == 400