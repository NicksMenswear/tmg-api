import awsgi
import signal

from server.app import init_app, init_logging, init_sentry, reset_db, lambda_teardown


if __name__ == "__main__":
    print("Running a local dev server...")
    init_logging(debug=True)
    app = init_app(swagger=True)
    app.run(host="0.0.0.0", port=8080)
else:
    print("Running in AWS Lambda...")
    init_logging(debug=True)
    init_sentry()
    app = init_app(swagger=False)


# This is the entry point for the AWS Lambda function
def lambda_handler(event, context):
    return awsgi.response(app, event, context)


# Handle lambda termination gracefully
signal.signal(signal.SIGTERM, lambda_teardown)
