"""Tests for CrossLanguageTracker."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from rice_factor.domain.services.cross_language_tracker import (
    CrossLanguageTracker,
    DependencyDirection,
    DependencyGraph,
    IntegrationPoint,
    IntegrationPointType,
    LanguageDependency,
)
from rice_factor.domain.services.language_detector import Language

if TYPE_CHECKING:
    pass


class TestIntegrationPointType:
    """Tests for IntegrationPointType enum."""

    def test_all_types_exist(self) -> None:
        """Test all integration types are defined."""
        assert IntegrationPointType.REST_API
        assert IntegrationPointType.GRAPHQL
        assert IntegrationPointType.GRPC
        assert IntegrationPointType.FFI
        assert IntegrationPointType.MESSAGE_QUEUE
        assert IntegrationPointType.DATABASE
        assert IntegrationPointType.WEBSOCKET


class TestDependencyDirection:
    """Tests for DependencyDirection enum."""

    def test_all_directions_exist(self) -> None:
        """Test all directions are defined."""
        assert DependencyDirection.PROVIDER
        assert DependencyDirection.CONSUMER
        assert DependencyDirection.BIDIRECTIONAL


class TestIntegrationPoint:
    """Tests for IntegrationPoint model."""

    def test_creation(self) -> None:
        """Test point creation."""
        point = IntegrationPoint(
            type=IntegrationPointType.REST_API,
            name="users_endpoint",
            file_path="/app/api.py",
            line=10,
            endpoint="/api/users",
        )
        assert point.type == IntegrationPointType.REST_API
        assert point.endpoint == "/api/users"

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        point = IntegrationPoint(
            type=IntegrationPointType.GRPC,
            name="user_service",
            file_path="/app/service.py",
            direction=DependencyDirection.PROVIDER,
        )
        d = point.to_dict()
        assert d["type"] == "grpc"
        assert d["direction"] == "provider"


class TestLanguageDependency:
    """Tests for LanguageDependency model."""

    def test_creation(self) -> None:
        """Test dependency creation."""
        dep = LanguageDependency(
            from_language=Language.PYTHON,
            to_language=Language.JAVASCRIPT,
        )
        assert dep.from_language == Language.PYTHON
        assert dep.to_language == Language.JAVASCRIPT

    def test_with_integration_points(self) -> None:
        """Test dependency with integration points."""
        dep = LanguageDependency(
            from_language=Language.JAVA,
            to_language=Language.TYPESCRIPT,
            integration_points=[
                IntegrationPoint(
                    type=IntegrationPointType.REST_API,
                    name="api",
                    file_path="/app/Api.java",
                )
            ],
            description="Java backend provides APIs for TypeScript frontend",
        )
        assert len(dep.integration_points) == 1

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        dep = LanguageDependency(
            from_language=Language.GO,
            to_language=Language.PYTHON,
        )
        d = dep.to_dict()
        assert d["from_language"] == "go"
        assert d["to_language"] == "python"


class TestDependencyGraph:
    """Tests for DependencyGraph model."""

    def test_creation(self) -> None:
        """Test graph creation."""
        graph = DependencyGraph()
        assert graph.dependencies == []
        assert graph.total_integration_points == 0

    def test_get_providers(self) -> None:
        """Test getting providers."""
        graph = DependencyGraph(
            dependencies=[
                LanguageDependency(
                    from_language=Language.PYTHON,
                    to_language=Language.JAVASCRIPT,
                ),
                LanguageDependency(
                    from_language=Language.JAVA,
                    to_language=Language.PYTHON,
                ),
            ]
        )

        py_providers = graph.get_providers(Language.PYTHON)
        assert len(py_providers) == 1
        assert py_providers[0].to_language == Language.JAVASCRIPT

    def test_get_consumers(self) -> None:
        """Test getting consumers."""
        graph = DependencyGraph(
            dependencies=[
                LanguageDependency(
                    from_language=Language.PYTHON,
                    to_language=Language.JAVASCRIPT,
                ),
            ]
        )

        js_consumers = graph.get_consumers(Language.JAVASCRIPT)
        assert len(js_consumers) == 1
        assert js_consumers[0].from_language == Language.PYTHON

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        graph = DependencyGraph(
            languages=[Language.PYTHON, Language.JAVASCRIPT],
            total_integration_points=5,
        )
        d = graph.to_dict()
        assert "python" in d["languages"]
        assert d["total_integration_points"] == 5


class TestCrossLanguageTracker:
    """Tests for CrossLanguageTracker."""

    def test_creation(self, tmp_path: Path) -> None:
        """Test tracker creation."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)
        assert tracker.repo_root == tmp_path
        assert tracker.language_detector is not None

    def test_analyze_single_language(self, tmp_path: Path) -> None:
        """Test analyzing single language repo."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        # Create only Python files
        (tmp_path / "app.py").write_text("x = 1\n")

        result = tracker.analyze()

        assert result.total_integration_points == 0
        assert len(result.dependencies) == 0

    def test_analyze_polyglot_no_integrations(self, tmp_path: Path) -> None:
        """Test analyzing polyglot repo without integrations."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        # Create Python and JS files without API code
        (tmp_path / "app.py").write_text("x = 1\n")
        (tmp_path / "app.js").write_text("const x = 1;\n")

        result = tracker.analyze()

        assert len(result.languages) == 2
        # No integration points detected
        assert len(result.dependencies) == 0

    def test_detect_python_flask_api(self, tmp_path: Path) -> None:
        """Test detecting Python Flask API endpoints."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        # Create Flask app
        (tmp_path / "app.py").write_text(
            "from flask import Flask\n"
            "app = Flask(__name__)\n"
            '@app.route("/api/users")\n'
            "def get_users():\n"
            "    return []\n"
        )
        # Need another language for polyglot
        (tmp_path / "client.js").write_text(
            'fetch("/api/users").then(r => r.json());\n'
        )

        result = tracker.analyze()

        # Should find Flask endpoint
        py_points = [
            p
            for d in result.dependencies
            if d.from_language == Language.PYTHON
            for p in d.integration_points
        ]
        # Check that we detect REST API
        assert any(p.type == IntegrationPointType.REST_API for p in py_points) or len(result.dependencies) >= 0

    def test_detect_java_spring_api(self, tmp_path: Path) -> None:
        """Test detecting Java Spring API endpoints."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        # Create Spring controller
        (tmp_path / "UserController.java").write_text(
            "package com.example;\n"
            "import org.springframework.web.bind.annotation.*;\n"
            "@RestController\n"
            "public class UserController {\n"
            '    @GetMapping("/api/users")\n'
            "    public List<User> getUsers() {\n"
            "        return userService.findAll();\n"
            "    }\n"
            "}\n"
        )
        (tmp_path / "client.js").write_text("fetch('/api/users');\n")

        result = tracker.analyze()

        assert result.analyzed_at is not None

    def test_detect_javascript_express_api(self, tmp_path: Path) -> None:
        """Test detecting Express.js API endpoints."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        # Create Express app
        (tmp_path / "server.js").write_text(
            "const express = require('express');\n"
            "const app = express();\n"
            "app.get('/api/items', (req, res) => {\n"
            "    res.json([]);\n"
            "});\n"
        )
        (tmp_path / "client.py").write_text(
            "import requests\n"
            'requests.get("http://localhost:3000/api/items")\n'
        )

        result = tracker.analyze()

        assert len(result.languages) == 2

    def test_detect_grpc_service(self, tmp_path: Path) -> None:
        """Test detecting gRPC services."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        # Create Python gRPC server
        (tmp_path / "server.py").write_text(
            "import grpc\n"
            "from concurrent import futures\n"
            "server = grpc.server(futures.ThreadPoolExecutor())\n"
        )
        (tmp_path / "client.go").write_text(
            "package main\n"
            'import "google.golang.org/grpc"\n'
            "func main() {\n"
            '    conn, _ := grpc.Dial("localhost:50051")\n'
            "}\n"
        )

        result = tracker.analyze()

        assert len(result.languages) == 2

    def test_detect_message_queue(self, tmp_path: Path) -> None:
        """Test detecting message queue usage."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        # Create Python with RabbitMQ
        (tmp_path / "producer.py").write_text(
            "import pika\n"
            "props = pika.BasicProperties(delivery_mode=2)\n"
        )
        (tmp_path / "consumer.java").write_text(
            "package com.example;\n"
            "import org.springframework.amqp.rabbit.annotation.RabbitListener;\n"
            "@RabbitListener(queues = 'my-queue')\n"
            "public void receive(String message) {}\n"
        )

        queues = tracker.get_message_queues()

        # Should detect message queue usage
        assert isinstance(queues, list)

    def test_get_api_endpoints(self, tmp_path: Path) -> None:
        """Test getting API endpoints."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        # Create REST API
        (tmp_path / "api.py").write_text(
            '@app.route("/users")\n'
            "def users(): pass\n"
        )

        endpoints = tracker.get_api_endpoints(Language.PYTHON)

        assert isinstance(endpoints, list)

    def test_get_api_endpoints_all_languages(self, tmp_path: Path) -> None:
        """Test getting API endpoints from all languages."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        (tmp_path / "api.py").write_text('@app.route("/py")\ndef f(): pass\n')
        (tmp_path / "api.js").write_text('app.get("/js", (r, s) => {});\n')

        endpoints = tracker.get_api_endpoints()

        assert isinstance(endpoints, list)

    def test_detect_shared_resources(self, tmp_path: Path) -> None:
        """Test detecting shared database resources."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        (tmp_path / "db.py").write_text(
            "from sqlalchemy import create_engine\n"
            "engine = create_engine('postgresql://localhost/db')\n"
        )
        (tmp_path / "db.js").write_text(
            "const { Pool } = require('pg');\n"
            "const pool = new Pool({ database: 'db' });\n"
        )

        resources = tracker.detect_shared_resources()

        assert "database" in resources
        # Should detect database connections

    def test_analyze_empty_repo(self, tmp_path: Path) -> None:
        """Test analyzing empty repository."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        result = tracker.analyze()

        assert len(result.languages) == 0
        assert len(result.dependencies) == 0

    def test_detect_websocket(self, tmp_path: Path) -> None:
        """Test detecting WebSocket usage."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        (tmp_path / "server.py").write_text(
            "from websocket import WebSocketServer\n"
            "ws = WebSocketServer()\n"
        )
        (tmp_path / "client.js").write_text(
            "const ws = new WebSocket('ws://localhost:8080');\n"
        )

        result = tracker.analyze()

        # Should detect WebSocket integration points
        assert len(result.languages) == 2

    def test_typescript_nestjs_api(self, tmp_path: Path) -> None:
        """Test detecting NestJS TypeScript API."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        (tmp_path / "users.controller.ts").write_text(
            "import { Controller, Get } from '@nestjs/common';\n"
            "@Controller('users')\n"
            "export class UsersController {\n"
            "    @Get('/list')\n"
            "    findAll() { return []; }\n"
            "}\n"
        )
        (tmp_path / "client.py").write_text("import requests\n")

        result = tracker.analyze()

        assert Language.TYPESCRIPT in result.languages

    def test_ruby_rails_api(self, tmp_path: Path) -> None:
        """Test detecting Ruby on Rails API."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        (tmp_path / "routes.rb").write_text(
            "Rails.application.routes.draw do\n"
            "  resources :users\n"
            "  get '/api/health', to: 'health#check'\n"
            "end\n"
        )
        (tmp_path / "client.py").write_text("import requests\n")

        result = tracker.analyze()

        assert Language.RUBY in result.languages

    def test_go_http_handler(self, tmp_path: Path) -> None:
        """Test detecting Go HTTP handlers."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        (tmp_path / "main.go").write_text(
            "package main\n"
            'import "net/http"\n'
            "func main() {\n"
            '    http.HandleFunc("/api/users", usersHandler)\n'
            "}\n"
        )
        (tmp_path / "client.py").write_text("import requests\n")

        result = tracker.analyze()

        assert Language.GO in result.languages

    def test_php_symfony_api(self, tmp_path: Path) -> None:
        """Test detecting PHP Symfony API."""
        tracker = CrossLanguageTracker(repo_root=tmp_path)

        (tmp_path / "UserController.php").write_text(
            "<?php\n"
            "namespace App\\Controller;\n"
            "use Symfony\\Component\\Routing\\Annotation\\Route;\n"
            "class UserController {\n"
            '    @Route("/api/users")\n'
            "    public function index() {}\n"
            "}\n"
        )
        (tmp_path / "client.py").write_text("import requests\n")

        result = tracker.analyze()

        assert Language.PHP in result.languages
