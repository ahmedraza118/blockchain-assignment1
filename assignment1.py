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
    TokenTransfer, SmartContractTransactionsFactory, TransactionsFactoryConfig
)
from multiversx_sdk import (
    Token,
    QueryRunnerAdapter,
    SmartContractQueriesController,
    TransactionComputer, TransactionsConverter
)
from pathlib import Path
from multiversx_sdk.abi import Abi, AbiDefinition


# Load environment variables
load_dotenv()



WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
SC_ADDRESS = os.getenv("SC_ADDRESS")

if not WALLET_ADDRESS or not SC_ADDRESS:
    raise ValueError("Environment variables WALLET_ADDRESS and SC_ADDRESS must be set.")

# Initialize provider and signer
abi_1 = Abi.load(Path("tema1.abi.json"))
provider = ProxyNetworkProvider("https://devnet-gateway.multiversx.com")
config = TransactionsFactoryConfig(chain_id="D")
factory = SmartContractTransactionsFactory(config, abi_1)
transaction_converter = TransactionsConverter()
transaction_computer = TransactionComputer()


wallet_path = Path("output/wallet.json")
signer = UserSigner.from_wallet(wallet_path, "password")

# Load ABI
abi_path = Path("tema1.abi.json")
if not abi_path.exists():
    raise FileNotFoundError(f"ABI file not found at {abi_path}")
contract_abi = abi.Abi.load(abi_path)

# Initialize query controller
query_runner = QueryRunnerAdapter(provider)
query_controller = SmartContractQueriesController(query_runner, contract_abi)

# Get the current wallet nonce
def get_wallet_nonce():
    try:
        account_address = Address.new_from_bech32(WALLET_ADDRESS)
        account_info = provider.get_account(account_address)
        return account_info.nonce
    except Exception as e:
        raise RuntimeError(f"Error getting wallet nonce: {e}")

# Mint an NFT Collection

def create_nft(nft_name, ticker, nft_class, rarity, power, img_uri):
    """
    Function to create an NFT with dynamic attributes and include an image URI.

    Parameters:
    nft_name (str): Name of the NFT.
    ticker (str): Ticker of the NFT.
    nft_class (int): Class of the NFT (1 byte).
    rarity (int): Rarity of the NFT (1 byte).
    power (int): Power of the NFT (1 byte).
    img_uri (str): Image URI for the NFT.

    Returns:
    str: Transaction hash of the submitted transaction.
    """
    try:
        nonce = get_wallet_nonce()

        # Dynamically construct the attributes string in hexadecimal format
        attributes = f"tags:class{nft_class};rarity{rarity};power{power}"

        # Encode all data fields into hexadecimal
        name_hex = nft_name.encode().hex()
        ticker_hex = ticker.encode().hex()
        quantity_hex = f"{1:02x}"  # Quantity is 1 for NFTs
        royalties_hex = f"{250:04x}"  # Example: 2.5% royalties (250 = 2.5%)
        hash_hex = "516d53614b325471315238696d6d463464743267776d4a416d6f7465336262654d5933564e506d71355462556632"  # IPFS hash example
        attributes_hex = attributes.encode().hex()
        img_uri_hex = img_uri.encode().hex()

        # Construct the transaction data
        tx_data = (
            f"ESDTNFTCreate@{ticker_hex}"
            f"@{quantity_hex}"
            f"@{name_hex}"
            f"@{royalties_hex}"
            f"@{hash_hex}"
            f"@{attributes_hex}"
            f"@{img_uri_hex}"
        )

        # Log the data for debugging
        print("Transaction Data:", tx_data)

        payload = TransactionPayload.from_str(tx_data)

        # Create the transaction where sender and receiver are the same wallet address
        transaction = Transaction(
            sender=Address.from_bech32(WALLET_ADDRESS).bech32(),
            receiver=Address.from_bech32(WALLET_ADDRESS).bech32(),
            value=TokenPayment.egld_from_amount(0),  # No EGLD should be sent
            data=payload.data,
            gas_limit=60000000,  # Adjust the gas limit as needed
            chain_id="D",  # Set the correct chain ID (Devnet or Mainnet)
            nonce=nonce,
        )

        # Sign the transaction and submit it
        transaction_computer = TransactionComputer()
        signable_bytes = transaction_computer.compute_bytes_for_signing(transaction)
        transaction.signature = signer.sign(signable_bytes)
        tx_hash = provider.send_transaction(transaction)
        print(f"Transaction submitted. TX Hash: {tx_hash}")
        return tx_hash
    except Exception as e:
        raise RuntimeError(f"Error creating NFT: {e}")




# Query NFT properties from the SC
def get_your_nft_properties():
    try:
        contract_address = Address.new_from_bech32(SC_ADDRESS)
        query = query_controller.create_query(
            contract=contract_address.bech32(),
            function="getYourNftCardProperties",
            arguments=[],
        )
        response = query_controller.run_query(query)
        raw_data_parts = query_controller.parse_query_response(response)
        print(f"Raw NFT properties: {raw_data_parts}")

        # Access the attributes directly from the SimpleNamespace object
        nft_properties = raw_data_parts[0]
        rarity = nft_properties.rarity.__discriminant__
        class_id = getattr(nft_properties, 'class').__discriminant__
        power = nft_properties.power.__discriminant__

        return [class_id, rarity, power]
    except Exception as e:
        raise RuntimeError(f"Error getting NFT properties: {e}")

# Query available NFTs


def query_available_nfts():
    try:
        contract_address = Address.new_from_bech32(SC_ADDRESS)
        query = query_controller.create_query(
            contract=contract_address.bech32(),
            function="nftSupply",
            arguments=[],
        )
        response = query_controller.run_query(query)
        raw_data_parts = query_controller.parse_query_response(response)
        print(f"Raw data parts for available NFTs: {raw_data_parts}")

        nfts = []
        nonce = 1  # Start nonce at 1

        for idx, part in enumerate(raw_data_parts, start=1):
            print(f"Processing part: {part}")

            # Access the attributes directly from the SimpleNamespace object
            for nft in part:
                print(f"NFT object: {vars(nft)}")
                attributes = nft.attributes
                if isinstance(attributes, bytes):
                    print(f"Attributes bytes: {attributes}")
                    try:
                        # Assuming the first byte is rarity, second byte is class, third byte is power
                        rarity = attributes[0]
                        class_ = attributes[1]
                        power = attributes[2]
                    except IndexError:
                        print(f"Error extracting attributes from: {attributes}")
                        continue
                else:
                    print(f"Attributes are not in bytes format: {attributes}")
                    continue
                
                token_id = nft.hash.hex() if nft.hash else None  # Check if hash exists
                if not token_id:
                    print(f"Missing token_id for NFT: {nft.name}")
                    continue  # Skip this NFT if it doesn't have a token ID
                
                print(f"Token ID: {token_id}, Rarity: {rarity}, Class: {class_}, Power: {power}")

                # Debug print the nonce value before adding the NFT
                print(f"Adding NFT with nonce: {nonce}")

                # Only append the NFT if all required attributes are valid
                if token_id and rarity is not None and class_ is not None and power is not None:
                    nfts.append({
                        "nonce": nonce,  # Adding nonce starting from 1
                        "token_id": token_id,
                        "rarity": rarity,
                        "class": class_,
                        "power": power
                    })
                else:
                    print(f"Skipping NFT with invalid attributes: {nft.name}")
                
                nonce += 1  # Increment nonce after processing each NFT

        return nfts
    except Exception as e:
        raise RuntimeError(f"Error querying available NFTs: {e}")



# Find a matching NFT
def find_matching_nft(nfts, target_properties):
    for nft in nfts:
        if (
            nft["class"] == target_properties["class"] and
            nft["rarity"] == target_properties["rarity"]
        ):
            return nft
    return None

# Trade an NFT

def create_and_trade_nft(nonce):
    try:
        # Corrected function call with the correct nonce
        tx_data = f"exchangeNft@{nonce:02x}"
        payload = TransactionPayload.from_str(tx_data)

        # NFT payment (TokenPayment) is required as part of the transaction
        nft_payment = Token("AHMEDRAZA-4fc0cb-03"     
        )
        transfer = TokenTransfer(
            token=nft_payment, 
            amount=1,       
        ) 
        transaction = factory.create_transaction_for_execute(
            sender=Address.from_bech32(WALLET_ADDRESS),  
            contract=Address.from_bech32(SC_ADDRESS),  
            function="exchangeNft",  
            gas_limit=6000000, 
            arguments=[nonce],  
            token_transfers=[transfer],  
        )

        # Print transaction details
        print("Transaction:", transaction_converter.transaction_to_dictionary(transaction))
        print("Transaction data:", transaction.data.decode())

        # Sign and send the transaction
        signable_bytes = transaction_computer.compute_bytes_for_signing(transaction)
        transaction.signature = signer.sign(signable_bytes)

        # Send the transaction
        tx_hash = provider.send_transaction(transaction)
        print(f"Transaction submitted. TX Hash: {tx_hash}")
        return tx_hash

    except Exception as e:
        raise RuntimeError(f"Error creating and trading NFT: {e}")








# Main flow
# if __name__ == "__main__":
#     try:
        # Mint an NFT
        # nft_name = "ahmed.raza11"
        # nft_ticker = "AHMEDRAZA-4fc0cb"
        # create_nft(nft_name, nft_ticker,8,3,2 , 'https://ipfs.io/ipfs/QmSaK2Tq1R8immF4dt2gwmJAmote3bbeMY3VNPmq5TbUf2')

        # # Get assigned NFT properties
        # assigned_props = get_your_nft_properties()

        # # Query available NFTs
        # available_nfts = query_available_nfts()

        # # Find a matching NFT
        # target_properties = {
        #     "class": assigned_props[0],
        #     "rarity": assigned_props[1],
        # }
        # matched_nft = find_matching_nft(available_nfts, target_properties)

        # if matched_nft:
        #     tx_hash = create_and_trade_nft("choudry.waseem", matched_nft["nonce"])
        #     print(f"Trade successful. TX Hash: {tx_hash}")
        # else:
        #     print("No matching NFT found.")
    # except Exception as e:
    #     print(f"An error occurred: {e}")


tx_hash = create_and_trade_nft(76)
print(f"Trade successful. TX Hash: {tx_hash}")