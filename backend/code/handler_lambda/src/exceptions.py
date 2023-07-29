class FourTwoTwoError(Exception):
    def __init__(self, message=""):
        self.message = message
        super().__init__(self.message)


class FiveHundredError(Exception):
    def __init__(self, message="", response={}):
        self.message = message
        if message == "" and response != {}:
            self.message = (
                response["message"]
                if "message" in response and response["message"]
                else "Error: a problem occured"
            )
            super().__init__(self.message)
        elif message != "" and response == {}:
            super().__init__(self.message)
        else:
            super().__init__("There was a problem")


class JenkinsHistoryLimit(Exception):
    def __init__(self):
        super().__init__()
