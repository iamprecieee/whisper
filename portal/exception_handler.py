from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    ValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
)
from rest_framework.response import Response


def whisper_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, (ValidationError, AuthenticationFailed, NotAuthenticated)):
        error_list = []
        try:
            for key, value in exc.get_full_details().items():
                try:
                    for error in value:
                        if error["code"] == "unique":
                            error_list.append(error["message"].capitalize())
                        elif error["code"] == "invalid":
                            error_list.append(error["message"].capitalize())
                        elif error["code"] == "required":
                            error_list.append(f"{key.title()} field is required.")
                        elif error["code"] == "blank":
                            error_list.append(f"{key.title()} field cannot be blank.")
                        elif error["code"] == "invalid_choice":
                            error_list.append(error["message"])
                        else:
                            error_list.append(error)
                except:
                    error_list.append(value["message"])

            if len(error_list) == 1:
                error_list = error_list[0]

            response.data = error_list
        except:
            try:
                response.data = f"{exc.detail["messages"][0]["message"]}."
            except:
                response.data = f"{exc.detail}."

    elif isinstance(exc, NotFound):
        response.data = exc.detail

    else:
        response = Response(str(exc).strip("[]'"))

    return response
