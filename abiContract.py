import os
import json
from dotenv import load_dotenv
from multiversx_sdk import Address, Transaction, TokenPayment, TransactionPayload
from multiversx_sdk import ProxyNetworkProvider
from multiversx_sdk import (QueryRunnerAdapter, SmartContractQueriesController)
from multiversx_sdk import UserSigner
from pathlib import Path

# Load environment variables
load_dotenv()
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
SC_ADDRESS = os.getenv("SC_ADDRESS")
WALLET_PASSWORD = os.getenv("WALLET_PASSWORD")

# Initialize provider
provider = ProxyNetworkProvider("https://devnet-api.multiversx.com")

# Initialize UserSigner from JSON wallet
wallet_path = Path("wallet.json")
signer = UserSigner.from_wallet(wallet_path, WALLET_PASSWORD)

# Initialize query runner and controller
query_runner = QueryRunnerAdapter(provider)
query_controller = SmartContractQueriesController(query_runner)

# Load Contract ABI
with open("tema1.abi.json", "r") as abi_file:
    contract_abi = json.load(abi_file)["endpoints"]

def decode_hex_properties(byte_properties):
    """Decode byte properties to readable values."""
    return list(byte_properties)

def call_contract_function(function_name, arguments=None):
    """Call a smart contract function using the ABI."""
    if arguments is None:
        arguments = []

    # Extract the function ABI from the list of endpoints
    function_abi = next((f for f in contract_abi if f["name"] == function_name), None)
    if not function_abi:
        raise ValueError(f"Function {function_name} not found in ABI.")

    contract_address = Address.from_bech32(SC_ADDRESS)
    query = query_controller.create_query(
        contract=contract_address.to_bech32(),
        function=function_name,
        arguments=arguments
    )

    try:
        response = query_controller.run_query(query)
        data_parts = query_controller.parse_query_response(response)
        return data_parts
    except Exception as e:
        print(f"Error calling {function_name}: {e}")
        return None

def get_your_nft_properties():
    """Query the smart contract to get your assigned NFT properties."""
    data_parts = call_contract_function("getYourNftCardProperties")

    if not data_parts:
        print("Failed to fetch NFT properties.")
        return None

    hex_properties = data_parts[0]  # Assuming the first element contains the properties
    attributes = decode_hex_properties(hex_properties)
    
    # Debug print for assigned NFT properties
    print(f"Assigned NFT Properties: Class {attributes[0]}, Rarity {attributes[1]}, Power {attributes[2]}")
    return attributes

def parse_nft_metadata(nft_list):
    """Parse metadata of available NFTs."""
    nfts = []
    for index, nft in enumerate(nft_list, start=1):
        # Debug print to show the raw NFT data
        print(f"Raw NFT Data: {nft}")
        
        if len(nft) < 11:
            print(f"Invalid NFT data length: {len(nft)}")
            continue

        token_id = nft[:8]  # Assuming token_id is the first 8 bytes
        rarity = nft[8]     # Assuming rarity is at index 8
        class_ = nft[3]     # Assuming class is at index 9
        power = nft[1]      # Assuming power is at index 10

        nfts.append({
            "nonce": index,
            "token_id": token_id.hex(),
            "rarity": rarity,
            "class": class_,
            "power": power
        })
    
    # Debug print after parsing the NFTs
    print("Parsed NFTs:", nfts)
    return nfts

def query_available_nfts():
    """Query available NFTs from the smart contract."""
    contract_address = Address.from_bech32(SC_ADDRESS)
    query = query_controller.create_query(
        contract=contract_address.to_bech32(),
        function="nftSupply",
        arguments=[],
    )
    response = query_controller.run_query(query)
    data_parts = query_controller.parse_query_response(response)

    nft_list = data_parts  # Assuming the response format is a list of NFT metadata
    available_nfts = parse_nft_metadata(nft_list)
    
    # Debug print to show all available NFTs
    print("Available NFTs:", available_nfts)
    return available_nfts

def create_and_trade_nft(moodle_id, nonce):
    """Create and trade an NFT with another user."""
    # Prepare the transaction data
    # Nonce needs to be packed correctly as a u64 (8 bytes)
    nonce_hex = f"{nonce:016x}"  # Convert nonce to a 16-character hex string (8 bytes for u64)
    moodle_id_hex = moodle_id.encode().hex()  # Encode Moodle ID to hex string

    # Form the payload as expected by the smart contract
    tx_data = f"exchangeNFT@{nonce_hex}@{moodle_id_hex}"
    
    # Create the transaction payload
    payload = TransactionPayload.from_str(tx_data)
    
    # Create the transaction
    transaction = Transaction(
        sender=Address.from_bech32(WALLET_ADDRESS),  # Sender address (your wallet)
        receiver=Address.from_bech32(SC_ADDRESS),   # Smart contract address
        value=TokenPayment.egld_from_amount(0),      # No EGLD payment, just the transaction
        data=payload,
        gas_limit=6000000,                           # Gas limit for the transaction
        chain_id="D"                                 # Chain ID (assuming "D" for mainnet)
    )

    # Sign the transaction
    signer.sign(transaction)
    
    # Send the transaction
    tx_hash = provider.send_transaction(transaction)
    print(f"Transaction submitted. TX Hash: {tx_hash}")
    return tx_hash

def menu():
    # Show menu options to the user
    print("Select an option:")
    print("1. Get NFT properties")
    print("2. Get available NFTs")
    print("3. Exchange NFT")
    print("4. Exit")

    # Get the user choice
    choice = input("Enter your choice: ")
    return choice

if __name__ == "__main__":
    # Your Moodle ID
    moodle_id = "ahmed.raza"  # Replace with your actual Moodle ID

    assigned_props = None
    available_nfts = None

    while True:
        choice = menu()

        if choice == '1':
            # Get assigned NFT properties
            assigned_props = get_your_nft_properties()
            if assigned_props:
                print(f"Assigned Properties: {assigned_props}")
            else:
                print("Failed to fetch assigned NFT properties.")
        
        elif choice == '2':
            # Get available NFTs
            available_nfts = query_available_nfts()
            if available_nfts:
                print("Available NFTs:")
                for nft in available_nfts:
                    print(nft)
            else:
                print("No NFTs available.")

        elif choice == '3':
            # Exchange NFT
            if not assigned_props:
                print("Please fetch assigned NFT properties first (option 1).")
            elif not available_nfts:
                print("Please fetch available NFTs first (option 2).")
            else:
                # Identify the correct nonce from available NFTs
                target_nft = next(
                    (nft for nft in available_nfts if nft["class"] == assigned_props[0] and 
                                                  nft["rarity"] == assigned_props[1] and 
                                                  nft["power"] == assigned_props[2]),
                    None
                )

                if target_nft:
                    nonce = target_nft["nonce"]
                    print(f"Target NFT Nonce: {nonce}")

                    # Create and trade the Student-NFT with Moodle ID
                    create_and_trade_nft(moodle_id, nonce)
                else:
                    print("No matching NFT found.")
        
        elif choice == '4':
            # Exit the program
            print("Exiting the program.")
            break
        
        else:
            print("Invalid choice. Please try again.")
