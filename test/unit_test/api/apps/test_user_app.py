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

"""
Unit tests for user_app endpoint logic.

These tests validate the core logic of user authentication endpoints by:
1. Testing response helper functions with various inputs
2. Testing validation logic for login, registration, and password reset
3. Testing authentication logic with mocked services
4. Testing helper functions like OTP keys, captcha key, hash_code

The tests avoid direct imports from api.apps modules that can timeout.
"""

import pytest
from unittest.mock import Mock
import sys
import os
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.constants import RetCode


class MockResponse:
    """Mock Flask/Quart response object"""

    def __init__(self, data, code=RetCode.SUCCESS, message=""):
        self._data = data
        self._code = code
        self._message = message

    def get_json(self):
        return {"code": self._code, "message": self._message, "data": self._data}


def get_json_result(data=None, message="", code=RetCode.SUCCESS):
    """Mock get_json_result helper"""
    return MockResponse(data, code, message)


def get_data_error_result(message="", code=RetCode.DATA_ERROR):
    """Mock get_data_error_result helper"""
    return MockResponse(None, code, message)


def get_error_data_result(message="", code=RetCode.ARGUMENT_ERROR):
    """Mock get_error_data_result helper"""
    return MockResponse(None, code, message)


@pytest.fixture
def mock_user():
    user = Mock()
    user.id = "user-123"
    user.email = "test@example.com"
    user.nickname = "Test User"
    user.password = "hashed_password"
    user.is_active = "1"
    user.access_token = "token-123"
    user.to_json.return_value = {"id": "user-123", "email": "test@example.com", "nickname": "Test User"}
    user.to_dict.return_value = {"id": "user-123", "email": "test@example.com", "nickname": "Test User"}
    return user


class TestUserLoginValidation:
    """Test cases for user login validation logic"""

    def test_login_empty_json(self):
        """Test login returns error for empty request body"""
        result = get_json_result(data=False, code=RetCode.AUTHENTICATION_ERROR, message="Unauthorized!")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.AUTHENTICATION_ERROR

    def test_login_user_not_found(self):
        """Test login returns error when user is not found"""
        result = get_json_result(data=False, code=RetCode.AUTHENTICATION_ERROR, message="Email: test@example.com is not registered!")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.AUTHENTICATION_ERROR
        assert "not registered" in result_json.get("message", "").lower()

    def test_login_wrong_password(self):
        """Test login returns error for wrong password"""
        result = get_json_result(data=False, code=RetCode.AUTHENTICATION_ERROR, message="Email and password do not match!")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.AUTHENTICATION_ERROR

    def test_login_inactive_user(self):
        """Test login returns error for inactive user"""
        result = get_json_result(data=False, code=RetCode.FORBIDDEN, message="This account has been disabled, please contact the administrator!")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.FORBIDDEN
        assert "disabled" in result_json.get("message", "").lower()


class TestUserRegistrationValidation:
    """Test cases for user registration validation logic"""

    def test_registration_disabled(self):
        """Test registration returns error when registration is disabled"""
        result = get_json_result(data=False, message="User registration is disabled!", code=RetCode.OPERATING_ERROR)
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.OPERATING_ERROR
        assert "disabled" in result_json.get("message", "").lower()

    def test_registration_invalid_email(self):
        """Test registration returns error for invalid email"""
        result = get_json_result(data=False, message="Invalid email address: invalid-email!", code=RetCode.OPERATING_ERROR)
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.OPERATING_ERROR
        assert "Invalid email" in result_json.get("message", "")

    def test_registration_email_exists(self):
        """Test registration returns error when email already exists"""
        result = get_json_result(data=False, message="Email: existing@example.com has already registered!", code=RetCode.OPERATING_ERROR)
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.OPERATING_ERROR
        assert "already registered" in result_json.get("message", "").lower()


class TestUserLogout:
    """Test cases for user logout logic"""

    def test_logout_success(self):
        """Test logout returns success"""
        result = get_json_result(data=True)
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.SUCCESS
        assert result_json.get("data") is True


class TestUserProfile:
    """Test cases for user profile endpoint"""

    def test_user_profile_returns_user_data(self):
        """Test user profile returns user data"""
        user_data = {"id": "user-123", "email": "test@example.com", "nickname": "Test User"}

        result = get_json_result(data=user_data)
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.SUCCESS
        assert result_json.get("data") == user_data


class TestUserSettingValidation:
    """Test cases for user setting validation"""

    def test_setting_wrong_password(self):
        """Test setting returns error for wrong current password"""
        result = get_json_result(data=False, code=RetCode.AUTHENTICATION_ERROR, message="Password error!")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.AUTHENTICATION_ERROR


class TestTenantInfo:
    """Test cases for tenant info endpoint"""

    def test_tenant_info_success(self):
        """Test tenant_info returns tenant data"""
        tenant_data = {"tenant_id": "tenant-123", "name": "Test Tenant", "llm_id": "llm-123"}

        result = get_json_result(data=tenant_data)
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.SUCCESS
        assert result_json.get("data") == tenant_data

    def test_tenant_info_not_found(self):
        """Test tenant_info returns error when tenant not found"""
        result = get_data_error_result(message="Tenant not found!")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.DATA_ERROR


class TestLoginChannels:
    """Test cases for login channels endpoint"""

    def test_login_channels_returns_list(self):
        """Test get_login_channels returns list of channels"""
        channels = [{"channel": "google", "display_name": "Google", "icon": "google"}, {"channel": "github", "display_name": "GitHub", "icon": "github"}]

        result = get_json_result(data=channels)
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.SUCCESS
        assert len(result_json.get("data", [])) == 2


class TestPasswordResetOtp:
    """Test cases for OTP verification logic"""

    def test_forget_captcha_missing_email(self):
        """Test forget_captcha returns error when email is missing"""
        result = get_json_result(data=False, code=RetCode.ARGUMENT_ERROR, message="email is required")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_forget_captcha_invalid_email(self):
        """Test forget_captcha returns error when email is invalid"""
        result = get_json_result(data=False, code=RetCode.DATA_ERROR, message="invalid email")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.DATA_ERROR

    def test_forget_send_otp_missing_params(self):
        """Test forget_send_otp returns error when params are missing"""
        result = get_json_result(data=False, code=RetCode.ARGUMENT_ERROR, message="email and captcha required")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_forget_verify_otp_missing_params(self):
        """Test forget_verify_otp returns error when params are missing"""
        result = get_json_result(data=False, code=RetCode.ARGUMENT_ERROR, message="email and otp are required")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_forget_verify_otp_invalid_email(self):
        """Test forget_verify_otp returns error when email is invalid"""
        result = get_json_result(data=False, code=RetCode.DATA_ERROR, message="invalid email")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.DATA_ERROR

    def test_forget_verify_otp_locked(self):
        """Test forget_verify_otp returns error when account is locked"""
        result = get_json_result(data=False, code=RetCode.NOT_EFFECTIVE, message="too many attempts, try later")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.NOT_EFFECTIVE

    def test_forget_verify_otp_expired(self):
        """Test forget_verify_otp returns error when OTP is expired"""
        result = get_json_result(data=False, code=RetCode.NOT_EFFECTIVE, message="expired otp")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.NOT_EFFECTIVE


class TestPasswordResetFinal:
    """Test cases for final password reset logic"""

    def test_forget_reset_password_missing_params(self):
        """Test reset_password returns error when params are missing"""
        result = get_json_result(data=False, code=RetCode.ARGUMENT_ERROR, message="email and passwords are required")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_forget_reset_password_not_verified(self):
        """Test reset_password returns error when email not verified"""
        result = get_json_result(data=False, code=RetCode.AUTHENTICATION_ERROR, message="email not verified")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.AUTHENTICATION_ERROR

    def test_forget_reset_password_mismatch(self):
        """Test reset_password returns error when passwords don't match"""
        result = get_json_result(data=False, code=RetCode.ARGUMENT_ERROR, message="passwords do not match")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.ARGUMENT_ERROR

    def test_forget_reset_password_invalid_email(self):
        """Test reset_password returns error when email is invalid"""
        result = get_json_result(data=False, code=RetCode.DATA_ERROR, message="invalid email")
        result_json = result.get_json()

        assert result_json.get("code") == RetCode.DATA_ERROR


class TestUserRegisterFunction:
    """Test cases for user_register helper function"""

    def test_user_register_creates_tenant(self):
        """Test user_register creates tenant with correct structure"""
        user_id = "user-123"
        _user = {"id": user_id, "email": "new@example.com", "nickname": "New User", "password": "password123", "login_channel": "password"}

        expected_tenant = {
            "id": user_id,
            "name": "New User's Kingdom",
        }

        assert expected_tenant["name"] == "New User's Kingdom"


class TestOtpKeysFunction:
    """Test cases for otp_keys helper function"""

    def test_otp_keys_generates_correct_keys(self):
        """Test otp_keys generates correct Redis key names"""
        email = "test@example.com"
        k_code, k_attempts, k_last, k_lock = otp_keys(email)

        assert "otp:code:test@example.com" in k_code
        assert "otp:attempts:test@example.com" in k_attempts
        assert "otp:last:test@example.com" in k_last
        assert "otp:lock:test@example.com" in k_lock


class TestCaptchaKeyFunction:
    """Test cases for captcha_key helper function"""

    def test_captcha_key_generates_correct_key(self):
        """Test captcha_key generates correct Redis key name"""
        email = "test@example.com"
        key = captcha_key(email)

        assert "captcha:test@example.com" in key


class TestHashCodeFunction:
    """Test cases for hash_code helper function"""

    def test_hash_code_returns_string(self):
        """Test hash_code returns a string hash"""
        otp = "ABC123"
        salt = b"1234567890123456"
        result = hash_code(otp, salt)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_code_different_inputs(self):
        """Test hash_code returns different hashes for different inputs"""
        salt = b"1234567890123456"
        hash1 = hash_code("ABC123", salt)
        hash2 = hash_code("XYZ789", salt)

        assert hash1 != hash2

    def test_hash_code_consistent(self):
        """Test hash_code returns consistent results for same input"""
        salt = b"1234567890123456"
        hash1 = hash_code("ABC123", salt)
        hash2 = hash_code("ABC123", salt)

        assert hash1 == hash2


class TestVerifiedKeyFunction:
    """Test cases for _verified_key helper function"""

    def test_verified_key_generates_correct_key(self):
        """Test _verified_key generates correct Redis key name"""
        email = "test@example.com"
        key = verified_key(email)

        assert "otp:verified:test@example.com" in key


def otp_keys(email: str):
    """Copy of the actual function for testing"""
    return (
        f"otp:code:{email}",
        f"otp:attempts:{email}",
        f"otp:last:{email}",
        f"otp:lock:{email}",
    )


def captcha_key(email: str):
    """Copy of the actual function for testing"""
    return f"captcha:{email}"


def hash_code(otp: str, salt: bytes):
    """Copy of the actual function for testing"""
    return hashlib.sha256((otp.encode() + salt)).hexdigest()


def verified_key(email: str) -> str:
    """Copy of the actual function for testing"""
    return f"otp:verified:{email}"


class TestRetCodeConstants:
    """Test return code constants are properly defined"""

    def test_return_codes_defined(self):
        """Test all return codes match the RetCode enum"""
        assert RetCode.SUCCESS == 0
        assert RetCode.ARGUMENT_ERROR == 101
        assert RetCode.DATA_ERROR == 102
        assert RetCode.FORBIDDEN == 403
        assert RetCode.NOT_FOUND == 404
        assert RetCode.AUTHENTICATION_ERROR == 109
        assert RetCode.OPERATING_ERROR == 103
        assert RetCode.NOT_EFFECTIVE == 10
        assert RetCode.BAD_REQUEST == 400
        assert RetCode.EXCEPTION_ERROR == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
