import os
from dotenv import load_dotenv
from multiversx_sdk import (
    Address,
    Transaction,
    ProxyNetworkProvider,
    UserSigner,
    TransactionPayload,
    TokenPayment,
    abi,
)
from multiversx_sdk import QueryRunnerAdapter, SmartContractQueriesController , TransactionComputer, TransactionsConverter
from pathlib import Path

# Load environment variables
load_dotenv()
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
SC_ADDRESS = os.getenv("SC_ADDRESS")

# Initialize provider
provider = ProxyNetworkProvider("https://devnet-gateway.multiversx.com")

# Initialize UserSigner from JSON wallet
wallet_path = Path("./output/wallet.json")
signer = UserSigner.from_wallet(wallet_path, "password")

# Load ABI
abi_path = Path("tema1.abi.json")
contract_abi = abi.Abi.load(abi_path)

# Initialize query runner and controller with ABI
query_runner = QueryRunnerAdapter(provider)
query_controller = SmartContractQueriesController(query_runner, contract_abi)


def decode_hex_properties(namespace_properties):
    """
    Extract properties from the SimpleNamespace object.
    """
    class_value = int(getattr(namespace_properties, 'class').__discriminant__)
    rarity_value = int(namespace_properties.rarity.__discriminant__)
    power_value = int(namespace_properties.power.__discriminant__)
    return [class_value, rarity_value, power_value]


def get_your_nft_properties():
    """
    Query the smart contract to get your assigned NFT properties.
    """
    contract_address = Address.from_bech32(SC_ADDRESS)
    query = query_controller.create_query(
        contract=contract_address.to_bech32(),
        function="getYourNftCardProperties",
        arguments=[],
    )
    response = query_controller.run_query(query)
    data_parts = query_controller.parse_query_response(response)

    hex_properties = data_parts[0]
    # print(f"Hex properties raw: {hex_properties}")
    attributes = decode_hex_properties(hex_properties)
    print(f"Assigned NFT Properties: Class {attributes[0]}, Rarity {attributes[1]}, Power {attributes[2]}")
    return attributes


def parse_nft_metadata(nft_list):
    """
    Parse metadata of available NFTs.
    """
    nfts = []
    for index, nft_group in enumerate(nft_list, start=1):
        for nft in nft_group:
            print(f"Raw NFT data: {nft}")

            attributes = nft.attributes
            rarity = int(attributes[0])
            class_ = int(attributes[1])
            power = int(attributes[2])

            token_id = nft.hash

            print(f"Token ID: {token_id.hex()}, Rarity: {rarity}, Class: {class_}, Power: {power}")

            nfts.append({
                "nonce": index,
                "token_id": token_id.hex(),
                "rarity": rarity,
                "class": class_,
                "power": power,
            })
    return nfts


def query_available_nfts():
    """
    Query available NFTs from the smart contract.
    """
    contract_address = Address.from_bech32(SC_ADDRESS)
    query = query_controller.create_query(
        contract=contract_address.to_bech32(),
        function="nftSupply",
        arguments=[],
    )
    response = query_controller.run_query(query)
    data_parts = query_controller.parse_query_response(response)

    nft_list = data_parts
    available_nfts = parse_nft_metadata(nft_list)
    # print("Available NFTs:", available_nfts)
    return available_nfts


def find_matching_nft(nft_list, target_properties, fallback_properties=None):
    """
    Find an NFT matching the target properties. If no exact match is found, apply fallback logic.
    """
    print("Starting NFT matching process...")
    for nft in nft_list:
        print(f"Checking NFT: {nft}")
        if (
            nft.get("class") == target_properties["class"]
            and nft.get("rarity") == target_properties["rarity"]
            and nft.get("power") == target_properties["power"]
        ):
            print(f"Found exact match: {nft}")
            return nft

    # Fallback logic
    if fallback_properties:
        print("No exact match found. Attempting fallback criteria...")
        for nft in nft_list:
            if (
                nft.get("class") == fallback_properties["class"]
                and nft.get("rarity") == target_properties["rarity"]
                and nft.get("power") == target_properties["power"]
            ):
                print(f"Found fallback match: {nft}")
                return nft

    print("No matching NFT found after fallback.")
    return None


def create_and_trade_nft(moodle_id, nonce):
    """
    Create and trade an NFT with another user.
    """
    tx_data = f"exchangeNFT@{nonce:02x}@{moodle_id.encode().hex()}"
    payload = TransactionPayload.from_str(tx_data)
    transaction = Transaction(
        sender=WALLET_ADDRESS,
        receiver=SC_ADDRESS,
        value=TokenPayment.egld_from_amount(0),
        data=tx_data.encode(),
        gas_limit=6000000,
        chain_id="D",
        nonce=1
    )

    transaction_computer = TransactionComputer()
    signable_bytes = transaction_computer.compute_bytes_for_signing(transaction)

    # Sign the bytes
    transaction.signature = signer.sign(signable_bytes)

    # Now send the transaction (assuming `provider` is set up)
    tx_hash = provider.send_transaction(transaction)
    print(f"Transaction submitted. TX Hash: {tx_hash}")
    return tx_hash


if __name__ == "__main__":
    try:
        # Get assigned NFT properties
        assigned_props = get_your_nft_properties()

        # Query available NFTs
        available_nfts = query_available_nfts()

        # Define target and fallback properties
        target_properties = {
            "class": assigned_props[0],
            "rarity": assigned_props[1],
            "power": assigned_props[2],
        }
        fallback_properties = {
            "class": 3,  # Example fallback class
        }

        # Find the matching NFT
        matched_nft = find_matching_nft(available_nfts, target_properties, fallback_properties)

        if matched_nft:
            nonce = matched_nft["nonce"]
            print(f"Target NFT Nonce: {nonce}")

            #  Moodle ID
            moodle_id = "ahmed.raza"

            # Create and trade the NFT
            create_and_trade_nft(moodle_id, nonce)
        else:
            print("No matching NFT found.")

    except Exception as e:
        print(f"An error occurred: {e}")