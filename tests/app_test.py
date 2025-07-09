# -*- coding: utf-8 -*-
import sys
import os
import asyncio
import time
import pytest
from httpx import AsyncClient
#sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import users_db, tasks_db

# Необходимо для работы pytest-asyncio
pytest_plugins = ['pytest_asyncio']

# Тесты для пользователей
@pytest.mark.asyncio
async def test_create_duplicate_user(client):
    user_data = {"id": 1, "name": "John Doe", "email": "john@example.com"}
    await client.post("/users", json=user_data)
    response = await client.post("/users", json=user_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"

@pytest.mark.asyncio
async def test_get_user(client):
    user_data = {"id": 1, "name": "John Doe", "email": "john@example.com"}
    await client.post("/users", json=user_data)
    response = await client.get("/users/1")
    assert response.status_code == 200
    assert response.json() == user_data

@pytest.mark.asyncio
async def test_get_nonexistent_user(client):
    response = await client.get("/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_create_task(client):
    # Сначала создаем пользователя
    user_data = {"id": 1, "name": "John Doe", "email": "john@example.com"}
    await client.post("/users", json=user_data)

    task_data = {"id": 1, "user_id": 1, "status": "pending"}
    response = await client.post("/tasks", json=task_data)
    assert response.status_code == 200
    assert response.json() == task_data
    assert tasks_db[1].status == "pending"

# Тесты для задач
@pytest.mark.asyncio
async def test_create_task_nonexistent_user(client):
    task_data = {"id": 1, "user_id": 999, "status": "pending"}
    response = await client.post("/tasks", json=task_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "User does not exist"

@pytest.mark.asyncio
async def test_get_task(client):
    # Создаем пользователя и задачу
    user_data = {"id": 1, "name": "John Doe", "email": "john@example.com"}
    await client.post("/users", json=user_data)
    task_data = {"id": 1, "user_id": 1, "status": "pending"}
    await client.post("/tasks", json=task_data)

    response = await client.get("/tasks/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["user_id"] == 1

@pytest.mark.asyncio
async def test_create_user(client):
    user_data = {"id": 1, "name": "John Doe", "email": "john@example.com"}
    response = await client.post("/users", json=user_data)
    assert response.status_code == 200
    assert response.json() == user_data
    assert users_db[1].name == "John Doe"

@pytest.mark.asyncio
async def test_get_nonexistent_task(client):
    response = await client.get("/tasks/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"

@pytest.mark.asyncio
async def test_task_processing(client):
    user_data = {"id": 1, "name": "John Doe", "email": "john@example.com"}
    await client.post("/users", json=user_data)
    
    task_data = {"id": 1, "user_id": 1, "status": "pending"}
    await client.post("/tasks", json=task_data)

    for _ in range(10):  # Максимум 10 попыток ожидания завершения задачи
        response = await client.get("/tasks/1")
        if response.json()["status"] == "done":
            break
        await asyncio.sleep(1)  # Ждем 1 секунду между проверками

    response = await client.get("/tasks/1")
    assert response.json()["status"] == "done"

    # Ожидание завершения задачи (максимум 6 секунд)
    start_time = time.time()
    while time.time() - start_time < 6:
        response = await client.get("/tasks/1")
        if response.status_code == 200 and response.json()["status"] == "done":
            break
        await asyncio.sleep(0.5)  # Проверяем каждые 0.5 секунды

    # Проверяем финальный статус
    response = await client.get("/tasks/1")
    assert response.status_code == 200
    assert response.json()["status"] == "done"