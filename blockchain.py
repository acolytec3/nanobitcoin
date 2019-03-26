import requests
import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4
from flask import Flask
from flask import jsonify
from flask import request
from urllib.parse import urlparse

class Blockchain(object):
	def __init__(self):
		self.chain = []
		self.current_transactions = []
		self.nodes = set()
		self.new_block(previous_hash=1, proof=100)

	def register_node(self, address):
		parsed_url = urlparse(address)
		self.nodes.add(parsed_url.path)

	def new_block(self, proof, previous_hash=None):
		block = {
			'index': len(self.chain)+1,
			'timestamp': time(),
			'transactions': self.current_transactions,
			'proof': proof,
			'previous_hash': previous_hash or self.hash(self.chain[-1])
		}

		self.current_transactions = []

		self.chain.append(block)
		return block

	def valid_transaction(self, sender, recipient, amount):
		print('Checking transactions')
		if sender == 0:
			return False
		index = 0
		balance = 0
		valid_sender = False
		while index < len(self.chain):
			block = self.chain[index]
			for transaction in block['transactions']:
				if transaction['sender'] == sender:
					if balance < amount:
						return 2
					balance -= amount
					valid_sender = True
				elif transaction['recipient'] == sender:
					balance += amount
					valid_sender = True
			index +=1
		return valid_sender
			
			
	def new_transaction(self, sender, recipient, amount):
		self.current_transactions.append({
			'sender': sender,
			'recipient': recipient,
			'amount': amount,
		})

		return self.last_block['index'] + 1

	def proof_of_work(self, last_proof):
		proof = 0
		while Blockchain.valid_proof(last_proof, proof) is False:
			proof +=1
		return proof

	def valid_chain(self, chain):
		last_block = chain[0]
		current_index = 1

		while current_index < len(chain):
			block = chain[current_index]
			print('{last_block}'.format(last_block=last_block))
			print('{block}'.format(block=block))
			print("\n-------------\n")

			if block['previous_hash'] != self.hash(last_block):
				return False

			if not Blockchain.valid_proof(last_block['proof'], block['proof']):
				return False

			last_block = block
			current_index += 1

		return True

	def resolve_conflicts(self):
		neighbors = self.nodes
		new_chain = None

		max_length = len(self.chain)

		for node in neighbors:
			response = requests.get('http://{node}/chain'.format(node=node))

			if response.status_code == 200:
				length = response.json()['length']
				chain = response.json()['chain']

				if length > max_length and self.valid_chain(chain):
					max_length = length
					new_chain = chain

		if new_chain:
			self.chain = new_chain
			return True

		return False

	@staticmethod
	def hash(block):
		blockstring = json.dumps(block, sort_keys=True).encode()
		return hashlib.sha256(blockstring).hexdigest()

	@staticmethod
	def valid_proof(last_proof, proof):
		guess = '{last_proof}{proof}'.format(last_proof=last_proof, proof=proof).encode()
		guess_hash = hashlib.sha256(guess).hexdigest()
		return guess_hash[:4] == "0000"

	@property
	def last_block(self):
		return self.chain[-1]


app = Flask(__name__)

node_identifier = str(uuid4()).replace('-','')

blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
	last_block = blockchain.last_block
	last_proof = last_block['proof']
	proof = blockchain.proof_of_work(last_proof)

	blockchain.new_transaction(
		sender='0',
		recipient=node_identifier,
		amount=1,
	)

	previous_hash = blockchain.hash(last_block)
	block = blockchain.new_block(proof, previous_hash)

	response = {
		'message': 'New block forged',
		'index': block['index'],
		'transactions': block['transactions'],
		'proof': block['proof'],
		'previous_hash': block['previous_hash'],
	}

	return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
	values = request.get_json()
	required = ['sender', 'recipient', 'amount']
#	if ('sender' not in values):
#		return 'Missing values', 400
	try:
		if not all(k in values for k in required):
			return 'Missing values', 400
	except:
		return 'Malformed request', 400
	valid_transaction = blockchain.valid_transaction(values['sender'], values['recipient'], values['amount'])
	if valid_transaction == 2:
		return 'Insufficient funds', 400
	elif valid_transaction == False:
		return 'Unknown sender', 400
		
	index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

	response = {'message': 'Transaction will be added to block {index}'.format(index=index)}
	return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
	response = {
		'chain': blockchain.chain,
		'length': len(blockchain.chain),
	}
	return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
	values = request.get_json()

	nodes = values.get('nodes')

	if nodes is None:
		return "Error: PLease supply a valid list of nodes", 400

	for node in nodes:
		blockchain.register_node(node)

	response = {
		'message': 'New nodes have been added',
		'total_nodes': list(blockchain.nodes),
	}
	return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
	replaced = blockchain.resolve_conflicts()

	if replaced:
		response = {
			'message': 'Our chain was replaced',
			'new_chain': blockchain.chain
		}
	else:
		response = {
			'message': 'Our chain is authoritative',
			'chain': blockchain.chain
		}

	return jsonify(response), 200

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
