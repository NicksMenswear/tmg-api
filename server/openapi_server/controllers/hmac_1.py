import hmac
import hashlib
from dotenv import load_dotenv
import os


secret_key = os.getenv("SECRET_KEY")
message = os.getenv("MSG")


def calculate_hmac(message, secret_key):
    """Calculating hmac"""
    message = message.encode('utf-8')
    secret_key = secret_key.encode('utf-8')
    return hmac.new(secret_key, message, hashlib.sha256).hexdigest()

def verify_hmac(recieved_hmac):
    """Compairing recieved hmac with our hmac"""
    expaxted_hmac = calculate_hmac(message, secret_key)
    return hmac.compare_digest(expaxted_hmac, recieved_hmac)


