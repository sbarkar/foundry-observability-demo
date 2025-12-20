"""
Integration tests for chat endpoint.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import os
import azure.functions as func


class TestChatEndpoint(unittest.TestCase):
    """Test cases for /api/chat endpoint."""
    
    @patch.dict(os.environ, {"JWT_VALIDATION_ENABLED": "false"})
    def test_chat_missing_message(self):
        """Test chat endpoint with missing message field."""
        from chat import chat
        
        # Create mock request with no message
        req = func.HttpRequest(
            method='POST',
            url='/api/chat',
            body=json.dumps({}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        response = chat(req)
        
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.get_body())
        self.assertEqual(body['error'], 'Bad Request')
        self.assertIn('correlationId', body)
    
    @patch.dict(os.environ, {"JWT_VALIDATION_ENABLED": "false"})
    def test_chat_invalid_json(self):
        """Test chat endpoint with invalid JSON."""
        from chat import chat
        
        # Create mock request with invalid JSON
        req = func.HttpRequest(
            method='POST',
            url='/api/chat',
            body=b'invalid json',
            headers={'Content-Type': 'application/json'}
        )
        
        response = chat(req)
        
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.get_body())
        self.assertEqual(body['error'], 'Bad Request')
        self.assertIn('correlationId', body)
    
    @patch.dict(os.environ, {"JWT_VALIDATION_ENABLED": "false"})
    def test_chat_message_too_long(self):
        """Test chat endpoint with message exceeding max length."""
        from chat import chat
        
        # Create mock request with very long message
        long_message = "a" * 5000
        req = func.HttpRequest(
            method='POST',
            url='/api/chat',
            body=json.dumps({"message": long_message}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        response = chat(req)
        
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.get_body())
        self.assertEqual(body['error'], 'Bad Request')
        self.assertIn('maximum length', body['message'])
    
    @patch.dict(os.environ, {"JWT_VALIDATION_ENABLED": "true"})
    def test_chat_missing_auth_token(self):
        """Test chat endpoint without authorization token when required."""
        from chat import chat
        
        # Create mock request without auth header
        req = func.HttpRequest(
            method='POST',
            url='/api/chat',
            body=json.dumps({"message": "Hello"}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        response = chat(req)
        
        self.assertEqual(response.status_code, 401)
        body = json.loads(response.get_body())
        self.assertEqual(body['error'], 'Unauthorized')
        self.assertIn('correlationId', body)
    
    @patch.dict(os.environ, {
        "JWT_VALIDATION_ENABLED": "true",
        "ENTRA_ISSUER": "https://login.microsoftonline.com/test/v2.0",
        "ENTRA_AUDIENCE": "api://test"
    })
    @patch('chat.validate_jwt_token')
    def test_chat_invalid_token(self, mock_validate):
        """Test chat endpoint with invalid JWT token."""
        from chat import chat
        import jwt as pyjwt
        
        # Mock token validation to raise error
        mock_validate.side_effect = pyjwt.InvalidTokenError("Invalid token")
        
        # Create mock request with invalid token
        req = func.HttpRequest(
            method='POST',
            url='/api/chat',
            body=json.dumps({"message": "Hello"}).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer invalid.token.here'
            }
        )
        
        response = chat(req)
        
        self.assertEqual(response.status_code, 401)
        body = json.loads(response.get_body())
        self.assertEqual(body['error'], 'Unauthorized')
        self.assertIn('correlationId', body)
    
    @patch.dict(os.environ, {
        "JWT_VALIDATION_ENABLED": "false",
        "AZURE_OPENAI_ENDPOINT": ""
    })
    def test_chat_missing_openai_config(self):
        """Test chat endpoint with missing OpenAI configuration."""
        from chat import chat
        
        # Reset global client
        import chat as chat_module
        chat_module._openai_client = None
        
        # Create valid request
        req = func.HttpRequest(
            method='POST',
            url='/api/chat',
            body=json.dumps({"message": "Hello"}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        response = chat(req)
        
        self.assertEqual(response.status_code, 500)
        body = json.loads(response.get_body())
        self.assertEqual(body['error'], 'Service Configuration Error')
        self.assertIn('correlationId', body)


if __name__ == '__main__':
    unittest.main()
