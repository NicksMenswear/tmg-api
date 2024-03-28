import awsgi

from server.app import init_app, init_logging, reset_db

init_logging()
app = init_app()

def lambda_handler(event, context):
    return awsgi.response(app, event, context)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)