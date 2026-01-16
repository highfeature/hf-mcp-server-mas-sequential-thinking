import logging
import re


class SensitiveDataFilter(logging.Filter):
    # Define a list of keys that values are sensitive data
    SENSITIVE_KEYS = (
        "credentials",
        "authorization",
        "token",
        "password",
        "access_token",
    )
    TOKEN_PATTERN = r"token=([^;]+)"

    def filter(self, record):
        try:
            record.args = self.mask_sensitive_args(record.args)
            record.msg = self.mask_sensitive_msg(record.msg)
            return True
        except Exception:
            return True

    def mask_sensitive_args(self, args):
        if isinstance(args, dict):
            new_args = args.copy()
            for key in args.keys():
                if key.lower() in self.SENSITIVE_KEYS:
                    new_args[key] = "******"
                else:
                    # mask sensitive data in dict values
                    new_args[key] = self.mask_sensitive_msg(args[key])
            return new_args
        # when there are multi arg in record.args
        return tuple([self.mask_sensitive_msg(arg) for arg in args])

    def mask_sensitive_msg(self, message):
        # mask sensitive data in multi record.args
        if isinstance(message, dict):
            return self.mask_sensitive_args(message)
        if isinstance(message, str):
            replace = "token=******"
            message = re.sub(self.TOKEN_PATTERN, replace, message)
        return message
