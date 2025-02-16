from pydantic import BaseModel


class LoginSchema(BaseModel):
    username: str
    password: str


class RegisterSchema(LoginSchema):
    pass


class PasswordResetCheckSchema(BaseModel):
    username: str


class PasswordResetSchema(BaseModel):
    username: str
    totp_code: str
    new_password: str


class TwoFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class TwoFARequest(BaseModel):
    totp_code: str
