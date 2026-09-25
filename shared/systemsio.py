"""
A server-side module for managing JSON and file-based IO operations
"""

import json
import os
import logging
import threading
import queue
from contextlib import ExitStack
from typing import Any

import requests
from flask import Flask, request, jsonify, Response
from jsonschema import validate, ValidationError

from shared.address import Address

# Disable Flask's default logging
log = logging.getLogger("werkzeug")
log.setLevel(logging.WARNING)

class Endpoint:
    """
    Represents an API endpoint with a specific URL and an optional schema.

    :ivar url: The URL of the endpoint. Must start with '/'
    :type url: str
    :ivar schema: The optional schema associated with the endpoint
    :type schema: str | None
    """
    def __init__(self, url: str, schema: str | None = None):
        self.url = url
        self.schema = schema


class SystemsIO:
    """
    Manages a Flask-based server for handling JSON and file-based endpoints. Provides functionality
    to send and receive data while maintaining internal queues and schemas for validation

    :ivar queues: Each endpoint has a dedicated queue for incoming data
    :type queues: dict[str, queue.Queue]
    :ivar schemas: Endpoints mapped to JSON validation schemas. Only applicable to JSON endpoints
    :type schemas: dict[str, dict[str, Any]]
    :ivar app: The Flask application instance used for the server
    :type app: Flask
    :ivar port: The port number the server listens to
    :type port: int
    :ivar host: The host address the server listens to
    :type host: str
    """

    def __init__(self, endpoints: list[Endpoint], port: int):
        self.app = Flask(__name__)
        self.port = port
        self.host = "0.0.0.0"
        self.queues: dict[str, queue.Queue] = {}
        self.schemas: dict[str, dict[str, Any]] = {}

        for endpoint in endpoints:
            self.app.add_url_rule(
                endpoint.url,
                endpoint=endpoint.url,
                view_func=self._handle_incoming_request,
                methods=["POST"]
            )
            self.queues[endpoint.url] = queue.Queue()

            if endpoint.schema:
                with open(endpoint.schema, encoding="utf-8") as schema_file:
                    schema = json.load(schema_file)
                self.schemas[endpoint.url] = schema
                print(f"[SystemsIO] Registered JSON endpoint {endpoint.url} with schema {endpoint.schema}")
            else:
                print(f"[SystemsIO] Registered FILE endpoint {endpoint.url}")

        # Start Flask in a background thread
        threading.Thread(
            target=self.app.run,
            kwargs={
                "host": self.host,
                "port": self.port,
                "debug": False,
                "use_reloader": False
            },
            daemon=True
        ).start()
        print(f"[SystemsIO] Flask server started on {self.host}:{self.port}")
        
    def _handle_incoming_request(self) -> tuple[Response, int]:
        """
        Internal Flask route handler for ALL registered endpoints
        """
        if request.is_json:
            path = request.path
            data = request.get_json()
            #print(f"[SystemsIO] Received JSON payload: {data}")
            schema = self.schemas.get(path)
            try:
                validate(instance=data, schema=schema)
            except ValidationError as e:
                print(f"[SystemsIO] Schema validation failed on {path}: {e.message}")
                return jsonify({"error": "Schema validation failed", "details": e.message}), 400
            self.queues[path].put(data)
            return jsonify({"status": "Queued"}), 200

        if request.files:
            path = request.path
            os.makedirs("files", exist_ok=True)
            received_files = []
            for _, file_storage in request.files.items():
                filename = f"files/{file_storage.filename}"
                file_storage.save(filename)
                received_files.append(filename)
            self.queues[path].put(received_files)
            print(f"[SystemsIO] Received FILES: {received_files}")
            return jsonify({"status": "Ok"}), 200

        return jsonify({"error": "Unsupported Media Type. Send 'application/json'"
            " or 'multipart/form-data' with files"}), 415

    @staticmethod
    def send_json(target: Address, endpoint: str, data: dict[str, Any]) -> None:
        """
        Sends a JSON payload to a specified target system
        """
        url = f"http://{target.ip}:{target.port}{endpoint}"
        requests.post(url, json=data, timeout=None).raise_for_status()
        #print(f"[SystemsIO] Sent to {url} JSON payload: {data}")

    @staticmethod
    def send_files(target: Address, endpoint: str, file_paths: list[str]) -> None:
        """
        Sends one or more files to a specified endpoint on a target address using HTTP POST
        """
        url = f"http://{target.ip}:{target.port}{endpoint}"
        # ExitStack allows us to manage a dynamic number of context managers (open files)
        with ExitStack() as stack:
            files = []
            for path in file_paths:
                # Open the file and ensure it closes automatically when we exit the block
                file_obj = stack.enter_context(open(path, 'rb'))
                filename = os.path.basename(path)
                files.append((filename, file_obj))
            requests.post(url, files=files, timeout=None).raise_for_status()
        print(f"[SystemsIO] Sent to {url} FILES: {file_paths}")

    def receive(self, endpoint: str) -> dict[str, Any] | list[str]:
        """
        Retrieve data from the specified endpoint queue.
        Data can be either a JSON object or the path of a file.
        This method blocks indefinitely until data is available
        """
        if endpoint not in self.queues:
            raise ValueError(f"Endpoint '{endpoint}' is not registered. "
                f"Available endpoints are: {list(self.queues.keys())}")
        return self.queues[endpoint].get(block=True)
