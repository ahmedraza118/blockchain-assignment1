from multiversx_sdk.wallet.user_pem import UserPEM
from multiversx_sdk.wallet.user_signer import UserSigner
from pathlib import Path

# Load the PEM file (replace with your PEM file path)
pem_file_path = Path("./new_wallet.pem")

# Load the PEM file and extract the secret key (use the first key in the PEM file)
user_pem = UserPEM.from_file(pem_file_path, index=0)  # You can change the index if you have multiple keys
secret_key = user_pem.secret_key

# Create a UserSigner using the secret key
signer = UserSigner(secret_key)

# Get the public key from the signer
public_key = signer.get_pubkey()

# Derive the wallet address from the public key, specifying the hrp ('erd' for Mainnet or 'dev' for Devnet)
wallet_address = public_key.to_address(hrp="dev")  # Replace 'dev' with 'erd' for Mainnet

# Print the wallet address in Bech32 format
print("Wallet Address:", wallet_address.to_bech32())

