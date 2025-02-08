import pyotp

totp = pyotp.TOTP("MAXC4MHFKQGZ672VZJPUKSUTEX32B4R5")

print(f"Current OTP: {totp.now()}")
