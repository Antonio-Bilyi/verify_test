class AppException(Exception):

    def __init__(self, msg: str):

        self.message = msg
        super().__init__(msg)

class ContactNotFoundError(AppException):

    def __init__(self, contact_id: int):

        super().__init__(f'Contact with id={contact_id} not found')

class ContactAlreadyExistsError(AppException):

    def __init__(self, email: str):

        super().__init__(f'Contact with email={email} already exists')