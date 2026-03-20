import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web3 import Web3
import json

# -------------------------
# CONFIG
# -------------------------

from dotenv import load_dotenv
import os
load_dotenv()

RPC_URL = os.getenv("RPC_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")
print("RPC:", RPC_URL)
# -------------------------
# ABI
# -------------------------

ABI = json.loads("""[
	{
		"inputs": [],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "string",
				"name": "documentHash",
				"type": "string"
			},
			{
				"indexed": false,
				"internalType": "address",
				"name": "issuer",
				"type": "address"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			}
		],
		"name": "HashStored",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "_hash",
				"type": "string"
			}
		],
		"name": "storeHash",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "_hash",
				"type": "string"
			}
		],
		"name": "getCertificate",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			},
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "owner",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "_hash",
				"type": "string"
			}
		],
		"name": "verifyHash",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]""")

# -------------------------
# CONNECT
# -------------------------

w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    raise Exception("Blockchain not connected")

print("Connected to Sepolia")

contract = w3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=ABI
)

# -------------------------
# STORE HASH (SIGNED TX)
# -------------------------

def store_hash(document_hash: str):
    try:
        nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)

        tx = contract.functions.storeHash(document_hash).build_transaction({
            'from': ACCOUNT_ADDRESS,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': w3.to_wei('10', 'gwei')
        })

        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)

        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print("Stored hash:", document_hash)
        print("Transaction hash:", tx_hash.hex())

    except Exception as e:
        print("Error storing hash:", str(e))


# -------------------------
# VERIFY
# -------------------------

def verify_hash(document_hash: str):
    try:
        return contract.functions.verifyHash(document_hash).call()
    except Exception as e:
        print("Error verifying hash:", str(e))
        return False


# -------------------------
# GET CERTIFICATE
# -------------------------

def get_certificate(document_hash: str):
    try:
        exists, timestamp, issuer = contract.functions.getCertificate(document_hash).call()
        return {
            "exists": exists,
            "timestamp": timestamp,
            "issuer": issuer
        }
    except Exception as e:
        print("Error fetching certificate:", str(e))
        return None


# -------------------------
# MAIN
# -------------------------

if __name__ == "__main__":

    file_path = os.path.join("samples", "kiit_sem7.pdf")

    if not os.path.exists(file_path):
        raise Exception(f"File not found: {file_path}")

    print("Processing file:", file_path)

    from ocr.ocr_certificate_extractor import extract_from_file

    parsed = extract_from_file(file_path)

    # Save JSON to json_op (same logic as OCR)
    output_dir = os.path.join(os.path.dirname(__file__), "..", "json_op")
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(
        output_dir,
        os.path.splitext(os.path.basename(file_path))[0] + "_extracted.json"
    )

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2, ensure_ascii=False)

    print("JSON saved at:", json_path)

    document_hash = parsed["document_image_hash"].strip()

    print("Extracted Hash:", document_hash)

    exists = verify_hash(document_hash)

    if exists:
        print("Certificate already verified")
        print(get_certificate(document_hash))

    else:
        print("Storing hash...")
        store_hash(document_hash)

        print("Verification:", verify_hash(document_hash))