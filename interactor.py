from multiversx_sdk import Address, ProxyNetworkProvider, SmartContractTransactionsFactory, UserSigner, Transaction, TransactionsConverter, TransactionsFactoryConfig
from multiversx_sdk.abi import Abi
from pathlib import Path

# Initialize the provider
config = TransactionsFactoryConfig(chain_id="D")

provider = ProxyNetworkProvider("https://devnet-gateway.multiversx.com")
network_config = provider.get_network_config()
# provider.set_chain_id("D")  # For Devnet, use "1" for Mainnet


# Load the ABI
abi_path = Path("./tema1.abi.json")
abi = Abi.load(abi_path)

# Define the smart contract address
contract_address = Address.from_bech32("erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th")

# Initialize the transactions factory
factory = SmartContractTransactionsFactory(provider, abi)

# Load the user's private key (replace with your PEM file path)
pem_path = Path("./new_wallet.pem")  # Path to your wallet PEM file
signer = UserSigner.from_pem_file(pem_path)
ahmed = Address.new_from_bech32("dev1v5wgm8g32yg9zlzdhdu4l03rlm6a27d0978yk9049kjcncqgv50q82wu4v")

# Create a transaction for the smart contract interaction
transaction = factory.create_transaction_for_execute(
    # chain_id=network_config.chain_id,
    contract=contract_address,
    function="getYourNftCardProperties",
    arguments=[],  # No arguments required for this function
    gas_limit=500_000,  # Adjust gas limit as needed
    sender=ahmed,  # Address of the caller
)


# Sign the transaction
signed_transaction = signer.sign(transaction)

# Send the signed transaction to the network
tx_hash = provider.send_transaction(signed_transaction)

# Wait for the transaction result
result = provider.get_transaction_status(tx_hash)

# Print the result
print("Transaction Hash:", tx_hash)
print("Transaction Result:", result)
