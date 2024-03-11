import hmac
import hashlib
import os
from flask import request


secret_key = os.getenv("SECRET_KEY")
secret_key=secret_key.encode('utf-8')

def hmac_verification():
    """HMAC verification authorizes all API calls by calculating and matching tokens received from Shopify with those created on the server side."""
    
    def decorator(func):
        def wrapper(**kwargs):
            """Creating a decorator wrapper function for HMAC verification that accepts *kwargs from the API endpoint."""
            
            signature = request.args.get('signature', '')
            query_params = request.args.copy()
            query_params.pop('signature', None)
            sorted_params = ''.join([f"{key}={','.join(value) if isinstance(value, list) else value}" for key, value in sorted(query_params.items())])
            calculated_signature = hmac.new(secret_key, sorted_params.encode('utf-8'), hashlib.sha256).hexdigest()
            if hmac.compare_digest(signature, calculated_signature):
                return func(**kwargs)
            else:
                return "Unauthorized user!", 401

        return wrapper
    return decorator


