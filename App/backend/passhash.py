from werkzeug.security import generate_password_hash

raw_password = "Passw0rd"  # replace with the actual password
hashed_password = generate_password_hash(raw_password)
print(hashed_password)
