from server.services.user_service import UserService


def lambda_handler_no_flask_experiment(event, context):
    user_service = UserService(None, None, None)
    user = user_service.get_user_by_email("zinovii+01@themoderngroom.com")

    print(user)
