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


class RAGFlowError(Exception):
    """Base exception for all RAGFlow SDK errors."""

    def __init__(self, message: str, details=None):
        self.message = message
        self.details = details
        super().__init__(message)


class APIError(RAGFlowError):
    """Exception raised for server-side API errors."""

    def __init__(self, message: str, status_code: int = None, details=None):
        self.status_code = status_code
        super().__init__(message, details)


class NetworkError(RAGFlowError):
    """Exception raised for network connectivity issues."""

    def __init__(self, message: str, details=None):
        super().__init__(message, details)


class AuthenticationError(RAGFlowError):
    """Exception raised for authentication/authorization failures."""

    def __init__(self, message: str, details=None):
        super().__init__(message, details)
