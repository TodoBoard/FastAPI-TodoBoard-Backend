import pyotp

totp = pyotp.TOTP("MAXC4MHFKQGZ672VZJPUKSUTEX32B4R5")

current_otp = totp.now()

print(f"Current OTP: {current_otp}")
