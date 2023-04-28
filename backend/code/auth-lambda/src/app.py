import os
import json

AUTH_TOKEN = os.getenv('AUTH_TOKEN', 'invalid-token')

def handler(event: dict, context) -> dict:
    auth_policy = {
      "principalId": "user",
      "policyDocument": {
        "Version": "2012-10-17",
        "Statement": [
          {
            "Action": "execute-api:Invoke",
            "Effect": None,
            "Resource": event["methodArn"]
          }
        ]
      }
    }
    print('request: {}'.format(json.dumps(event)))
    if (
        "authorizationToken" in event and
        event["authorizationToken"] == AUTH_TOKEN
    ):
        auth_policy["policyDocument"]["Statement"][0]["Effect"] = 'Allow'
    else:
        auth_policy["policyDocument"]["Statement"][0]["Effect"] = 'Deny'
    return auth_policy