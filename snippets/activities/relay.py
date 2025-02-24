from pprint import pprint
from loguru import logger
import random
from core.bot import Bot
from models.amount import Amount
from config import Chains
from config import Contracts
from core.onchain import Onchain
from models.chain import Chain
import requests


def get_request_id(bot: Bot, amount: Amount, from_chain: Chain, to_chain: Chain) -> str:
    url = 'https://api.relay.link/quote'
    body = {
        'user': bot.account.address,
        'originChainId': from_chain.chain_id,
        'destinationChainId': to_chain.chain_id,
        'originCurrency': '0x0000000000000000000000000000000000000000',
        'destinationCurrency': '0x0000000000000000000000000000000000000000',
        'recipient': bot.account.address,
        'tradeType': 'EXACT_INPUT',
        'amount': amount.wei,
        'referrer': 'relay.link/swap',
        'slippageTolerance': '',
        'useExternalLiquidity': False
    }

    response = requests.post(url, json=body)
    response.raise_for_status()
    response = response.json()
    return response['steps'][0]['requestId']


def relay(bot: Bot, to_chain: Chain, amount: Amount, onchain: Onchain | None = None):

    if onchain is None:
        onchain = bot.onchain

    from_chain = onchain.chain
    relay_contract = Contracts.get_contract_by_name('relay', from_chain)
    request_id = get_request_id(bot, amount, from_chain, to_chain)
    tx_params = onchain._prepare_tx(value=amount, to_address=relay_contract.address)
    tx_params['data'] = request_id
    tx_params = onchain._estimate_gas(tx_params)
    tx_hash = onchain._sign_and_send(tx_params)
    message = f'Cумма: {amount} ETH | В сеть: {to_chain.name.upper()} | Tx hash: {tx_hash}'
    logger.info(f'Транзакция отправлена! {message}')








