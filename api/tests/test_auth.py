"""
Unit tests for authentication module.
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import jwt as pyjwt
from auth import validate_jwt_token, extract_bearer_token


class TestAuth(unittest.TestCase):
    """Test cases for JWT authentication."""
    
    def test_extract_bearer_token_valid(self):
        """Test extracting valid bearer token."""
        header = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test.token"
        token = extract_bearer_token(header)
        self.assertEqual(token, "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test.token")
    
    def test_extract_bearer_token_invalid_format(self):
        """Test extraction with invalid format."""
        self.assertIsNone(extract_bearer_token("InvalidFormat"))
        self.assertIsNone(extract_bearer_token(""))
        self.assertIsNone(extract_bearer_token(None))
    
    def test_extract_bearer_token_case_insensitive(self):
        """Test that 'bearer' is case-insensitive."""
        header = "bearer test.token.here"
        token = extract_bearer_token(header)
        self.assertEqual(token, "test.token.here")
    
    @patch.dict(os.environ, {"JWT_VALIDATION_ENABLED": "false"})
    def test_validate_jwt_disabled(self):
        """Test JWT validation when disabled."""
        payload = validate_jwt_token("any.token.here")
        self.assertEqual(payload, {"sub": "anonymous"})
    
    @patch.dict(os.environ, {"JWT_VALIDATION_ENABLED": "true", "ENTRA_ISSUER": "", "ENTRA_AUDIENCE": ""})
    def test_validate_jwt_missing_config(self):
        """Test JWT validation with missing configuration."""
        with self.assertRaises(ValueError) as context:
            validate_jwt_token("test.token")
        self.assertIn("not configured", str(context.exception))
    
    @patch.dict(os.environ, {
        "JWT_VALIDATION_ENABLED": "true",
        "ENTRA_ISSUER": "https://login.microsoftonline.com/test-tenant/v2.0",
        "ENTRA_AUDIENCE": "api://test-app-id"
    })
    @patch('auth.PyJWKClient')
    @patch('auth.jwt.decode')
    def test_validate_jwt_valid_token(self, mock_decode, mock_jwks_client):
        """Test JWT validation with valid token."""
        # Mock JWKS client
        mock_client_instance = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = "test-key"
        mock_client_instance.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwks_client.return_value = mock_client_instance
        
        # Mock jwt.decode
        expected_payload = {"sub": "test-user", "aud": "api://test-app-id"}
        mock_decode.return_value = expected_payload
        
        # Clear cache to force new client creation
        from auth import get_jwks_client
        get_jwks_client.cache_clear()
        
        payload = validate_jwt_token("valid.test.token")
        
        self.assertEqual(payload, expected_payload)
        mock_decode.assert_called_once()
    
    @patch.dict(os.environ, {
        "JWT_VALIDATION_ENABLED": "true",
        "ENTRA_ISSUER": "https://login.microsoftonline.com/test-tenant/v2.0",
        "ENTRA_AUDIENCE": "api://test-app-id"
    })
    @patch('auth.PyJWKClient')
    @patch('auth.jwt.decode')
    def test_validate_jwt_expired_token(self, mock_decode, mock_jwks_client):
        """Test JWT validation with expired token."""
        # Mock JWKS client
        mock_client_instance = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = "test-key"
        mock_client_instance.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwks_client.return_value = mock_client_instance
        
        # Mock jwt.decode to raise ExpiredSignatureError
        mock_decode.side_effect = pyjwt.ExpiredSignatureError("Token has expired")
        
        # Clear cache
        from auth import get_jwks_client
        get_jwks_client.cache_clear()
        
        with self.assertRaises(pyjwt.ExpiredSignatureError):
            validate_jwt_token("expired.test.token")


if __name__ == '__main__':
    unittest.main()
