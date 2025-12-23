"""
Unit tests for health endpoint.
"""
import unittest
import json
import azure.functions as func


class TestHealthEndpoint(unittest.TestCase):
    """Test cases for /api/health endpoint."""
    
    def test_health_endpoint_success(self):
        """Test health endpoint returns 200 OK."""
        from health import health
        
        # Create mock request
        req = func.HttpRequest(
            method='GET',
            url='/api/health',
            body=None
        )
        
        response = health(req)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/json')
        
        # Parse response body
        body = json.loads(response.get_body())
        self.assertEqual(body['status'], 'healthy')
        self.assertEqual(body['service'], 'foundry-observability-demo-api')
        self.assertIn('correlationId', body)
        
        # Check correlation ID header
        headers = dict(response.headers)
        self.assertIn('X-Correlation-ID', headers)
        self.assertEqual(headers['X-Correlation-ID'], body['correlationId'])


if __name__ == '__main__':
    unittest.main()
