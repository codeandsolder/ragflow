#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import os
import queue
import threading
from typing import Any, Callable, Coroutine, Optional, Type, Union
import asyncio
from functools import wraps

from quart import make_response as quart_make_response, jsonify as quart_jsonify
from common.constants import RetCode

TimeoutException = Union[Type[BaseException], BaseException]
OnTimeoutCallback = Union[Callable[..., Any], Coroutine[Any, Any, Any]]


def _build_response_dict(code: int, message: str, data: Any) -> dict[str, Any]:
    """Build response dictionary, excluding None values except for 'code'."""
    result_dict = {"code": code, "message": message, "data": data}
    return {key: value for key, value in result_dict.items() if value is not None or key == "code"}


def _add_cors_headers(response) -> None:
    """Add CORS headers to the response object."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Method"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "Authorization"


def timeout(seconds: float | int | str = None, attempts: int = 2, *, exception: Optional[TimeoutException] = None, on_timeout: Optional[OnTimeoutCallback] = None):
    """Decorator that applies a timeout to a function.

    Args:
        seconds: Timeout in seconds. Can be float, int, or string that can be converted to float.
        attempts: Number of attempts to retry.
        exception: Optional exception to raise on timeout.
        on_timeout: Optional callback to call on timeout.

    Returns:
        Decorated function with timeout applied.
    """
    if isinstance(seconds, str):
        seconds = float(seconds)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result_queue = queue.Queue(maxsize=1)

            def target():
                try:
                    result = func(*args, **kwargs)
                    result_queue.put(result)
                except Exception as e:
                    result_queue.put(e)

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()

            for a in range(attempts):
                try:
                    if os.environ.get("ENABLE_TIMEOUT_ASSERTION"):
                        result = result_queue.get(timeout=seconds)
                    else:
                        result = result_queue.get()
                    if isinstance(result, Exception):
                        raise result
                    return result
                except queue.Empty:
                    pass
            raise TimeoutError(f"Function '{func.__name__}' timed out after {seconds} seconds and {attempts} attempts.")

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            if seconds is None:
                return await func(*args, **kwargs)

            for a in range(attempts):
                try:
                    if os.environ.get("ENABLE_TIMEOUT_ASSERTION"):
                        return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
                    else:
                        return await func(*args, **kwargs)
                except asyncio.TimeoutError:
                    if a < attempts - 1:
                        continue
                    if on_timeout is not None:
                        if callable(on_timeout):
                            result = on_timeout()
                            if isinstance(result, Coroutine):
                                return await result
                            return result
                        return on_timeout

                    if exception is None:
                        raise TimeoutError(f"Operation timed out after {seconds} seconds and {attempts} attempts.")

                    if isinstance(exception, BaseException):
                        raise exception

                    if isinstance(exception, type) and issubclass(exception, BaseException):
                        raise exception(f"Operation timed out after {seconds} seconds and {attempts} attempts.")

                    raise RuntimeError("Invalid exception type provided")

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


async def construct_response(code: int = RetCode.SUCCESS, message: str = "success", data: Any = None, auth: Optional[str] = None):
    """Construct an async HTTP response.

    Args:
        code: Response code (default: RetCode.SUCCESS)
        message: Response message (default: "success")
        data: Response data (default: None)
        auth: Optional authorization header value

    Returns:
        Quart response object with JSON body and CORS headers
    """
    response_dict = _build_response_dict(code, message, data)
    response = await quart_make_response(quart_jsonify(response_dict))
    if auth:
        response.headers["Authorization"] = auth
    _add_cors_headers(response)
    return response


def sync_construct_response(code: int = RetCode.SUCCESS, message: str = "success", data: Any = None, auth: Optional[str] = None):
    """Construct a sync HTTP response.

    Args:
        code: Response code (default: RetCode.SUCCESS)
        message: Response message (default: "success")
        data: Response data (default: None)
        auth: Optional authorization header value

    Returns:
        Flask response object with JSON body and CORS headers
    """
    import flask

    response_dict = _build_response_dict(code, message, data)
    response = flask.make_response(flask.jsonify(response_dict))
    if auth:
        response.headers["Authorization"] = auth
    _add_cors_headers(response)
    return response
