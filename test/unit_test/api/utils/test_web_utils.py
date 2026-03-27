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

import pytest

from api.utils.web_utils import is_valid_url, is_private_ip, is_reserved_ip


class TestIsReservedIP:
    """Test cases for IP address validation."""

    @pytest.mark.parametrize(
        "ip",
        [
            "127.0.0.1",
            "127.0.0.2",
            "127.255.255.255",
            "10.0.0.1",
            "10.255.255.255",
            "172.16.0.1",
            "172.31.255.255",
            "192.168.0.1",
            "192.168.255.255",
            "169.254.0.1",
            "169.254.255.255",
            "0.0.0.0",
            "255.255.255.255",
            "::1",
            "fe80::1",
        ],
    )
    def test_reserved_ips_blocked(self, ip):
        """Test that reserved IP addresses are correctly identified."""
        assert is_reserved_ip(ip) is True

    @pytest.mark.parametrize(
        "ip",
        [
            "8.8.8.8",
            "1.1.1.1",
            "93.184.216.34",
            "142.250.185.46",
        ],
    )
    def test_public_ips_allowed(self, ip):
        """Test that public IP addresses are not blocked."""
        assert is_reserved_ip(ip) is False

    def test_invalid_ip_returns_false(self):
        """Test that invalid IP strings return False."""
        assert is_reserved_ip("invalid") is False
        assert is_reserved_ip("") is False


class TestIsPrivateIP:
    """Test cases for private IP detection."""

    @pytest.mark.parametrize(
        "ip",
        [
            "127.0.0.1",
            "10.0.0.1",
            "172.16.0.1",
            "192.168.0.1",
        ],
    )
    def test_private_ips_detected(self, ip):
        assert is_private_ip(ip) is True

    @pytest.mark.parametrize(
        "ip",
        [
            "8.8.8.8",
            "1.1.1.1",
        ],
    )
    def test_public_ips_not_detected(self, ip):
        assert is_private_ip(ip) is False


class TestIsValidURL:
    """Test cases for URL validation including SSRF protection."""

    @pytest.mark.parametrize(
        "url",
        [
            "http://example.com",
            "https://example.com",
            "https://www.google.com",
            "https://github.com",
        ],
    )
    def test_valid_public_urls_allowed(self, url):
        """Test that valid public URLs are allowed."""
        assert is_valid_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "http://localhost",
            "http://localhost:8080",
            "https://localhost",
            "http://127.0.0.1",
            "http://127.0.0.1:9000",
            "http://127.1",
            "http://[::1]",
            "http://[::1]:8080",
            "http://0.0.0.0",
            "http://0.0.0.0:3000",
        ],
    )
    def test_localhost_blocked(self, url):
        """Test that localhost variants are blocked."""
        assert is_valid_url(url) is False

    @pytest.mark.parametrize(
        "url",
        [
            "http://10.0.0.1",
            "http://10.255.255.255",
            "http://10.0.0.1:8080",
        ],
    )
    def test_private_network_10_blocked(self, url):
        """Test that 10.0.0.0/8 private network is blocked."""
        assert is_valid_url(url) is False

    @pytest.mark.parametrize(
        "url",
        [
            "http://172.16.0.1",
            "http://172.31.255.255",
            "http://172.16.0.1:8080",
        ],
    )
    def test_private_network_172_blocked(self, url):
        """Test that 172.16.0.0/12 private network is blocked."""
        assert is_valid_url(url) is False

    @pytest.mark.parametrize(
        "url",
        [
            "http://192.168.0.1",
            "http://192.168.255.255",
            "http://192.168.0.1:8080",
        ],
    )
    def test_private_network_192_blocked(self, url):
        """Test that 192.168.0.0/16 private network is blocked."""
        assert is_valid_url(url) is False

    @pytest.mark.parametrize(
        "url",
        [
            "http://169.254.169.254",
            "http://169.254.169.254/latest/meta-data/",
        ],
    )
    def test_cloud_metadata_ip_blocked(self, url):
        """Test that cloud metadata IPs (169.254.169.254) are blocked."""
        assert is_valid_url(url) is False

    @pytest.mark.parametrize(
        "url",
        [
            "http://internal",
            "http://test.internal",
            "http://server.local",
        ],
    )
    def test_internal_hostnames_blocked(self, url):
        """Test that internal/locally resolved hostnames are blocked."""
        assert is_valid_url(url) is False

    def test_invalid_url_format(self):
        """Test that invalid URL formats are rejected."""
        assert is_valid_url("not-a-url") is False
        assert is_valid_url("htp://bad") is False
        assert is_valid_url("") is False
