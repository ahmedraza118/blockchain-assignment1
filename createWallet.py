from multiversx_sdk import Mnemonic

mnemonic = Mnemonic.generate()
words = mnemonic.get_words()

print(words)

from multiversx_sdk import UserWallet
from pathlib import Path

path = Path("./output")
if not path.exists():
    path.mkdir(parents=True, exist_ok=True)

wallet = UserWallet.from_mnemonic(mnemonic.get_text(), "password")
wallet.save(path / "walletWithMnemonic.json")

secret_key = mnemonic.derive_key(0)
public_key = secret_key.generate_public_key()

print("Secret key:", secret_key.hex())
print("Public key:", public_key.hex())

path = Path("./output")
if not path.exists():
    path.mkdir(parents=True, exist_ok=True)

wallet = UserWallet.from_secret_key(secret_key, "password")
wallet.save(path / "wallet.json", address_hrp="erd")

from multiversx_sdk import Address, UserPEM

path = Path("./output")
if not path.exists():
    path.mkdir(parents=True, exist_ok=True)

label = Address(public_key.buffer, "erd").to_bech32()
pem = UserPEM(label=label, secret_key=secret_key)
pem.save(path / "wallet.pem")