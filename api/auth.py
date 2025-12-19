"""
JWT token validation for Entra ID tokens.
"""
import os
import logging
from typing import Dict, Optional
import jwt
from jwt import PyJWKClient
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_jwks_client() -> Optional[PyJWKClient]:
    """
    Get cached JWKS client for token validation.
    Returns None if JWT validation is disabled.
    """
    if os.getenv("JWT_VALIDATION_ENABLED", "true").lower() != "true":
        return None
    
    issuer = os.getenv("ENTRA_ISSUER", "")
    if not issuer:
        logger.warning("JWT validation enabled but ENTRA_ISSUER not set")
        return None
    
    # Construct JWKS URI from issuer
    jwks_uri = f"{issuer.rstrip('/')}/discovery/keys"
    return PyJWKClient(jwks_uri)


def validate_jwt_token(token: str) -> Dict:
    """
    Validate JWT token from Entra ID.
    
    Args:
        token: Bearer token from Authorization header
        
    Returns:
        Decoded token payload
        
    Raises:
        jwt.InvalidTokenError: If token is invalid
        ValueError: If validation is misconfigured
    """
    # Check if validation is enabled
    if os.getenv("JWT_VALIDATION_ENABLED", "true").lower() != "true":
        logger.info("JWT validation disabled, skipping token validation")
        return {"sub": "anonymous"}
    
    # Get configuration
    issuer = os.getenv("ENTRA_ISSUER")
    audience = os.getenv("ENTRA_AUDIENCE")
    
    if not issuer or not audience:
        raise ValueError("JWT validation enabled but ENTRA_ISSUER or ENTRA_AUDIENCE not configured")
    
    # Get JWKS client
    jwks_client = get_jwks_client()
    if not jwks_client:
        raise ValueError("Failed to initialize JWKS client")
    
    # Get signing key
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    
    # Validate token
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=issuer,
        audience=audience,
        options={
            "verify_signature": True,
            "verify_exp": True,
            "verify_nbf": True,
            "verify_iat": True,
            "verify_aud": True,
            "verify_iss": True,
        }
    )
    
    logger.info(f"JWT token validated for subject: {payload.get('sub', 'unknown')}")
    return payload


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    """
    Extract bearer token from Authorization header.
    
    Args:
        authorization_header: Value of Authorization header
        
    Returns:
        Token string without 'Bearer ' prefix, or None if not found
    """
    if not authorization_header:
        return None
    
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]
