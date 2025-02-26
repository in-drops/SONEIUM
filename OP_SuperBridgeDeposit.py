from loguru import logger
import time
from config import config, Chains
from core.bot import Bot
from core.onchain import Onchain
from core.excel import Excel
from models.account import Account
from utils.inputs import input_pause, input_deposit_amount
from utils.logging import init_logger
from utils.utils import (random_sleep, get_accounts, select_profiles)
import random


def main():

    if not config.is_browser_run:
        config.is_browser_run = True
    init_logger()
    accounts = get_accounts()
    accounts_for_work = select_profiles(accounts)
    amount_input = input_deposit_amount()
    multiplier = random.uniform(1.01, 1.05)
    amount_input *= multiplier
    print(f"Сумма хранения каждого кошелька в сети SONEIUM: {amount_input:.5f} ETH!")
    pause = input_pause()

    for i in range(config.cycle):
        random.shuffle(accounts_for_work)
        for account in accounts_for_work:
            worker(account, amount_input)
            random_sleep(pause)

        logger.success(f'Цикл {i + 1} завершен, обработано {len(accounts_for_work)} аккаунтов!')
        logger.info(f'Ожидание перед следующим циклом ~{config.pause_between_cycle[1]} секунд')

        random_sleep(*config.pause_between_cycle)

def worker(account: Account, amount_input) -> None:
    try:
        with Bot(account) as bot:
            activity(bot, amount_input)
    except Exception as e:
        logger.critical(f"{account.profile_number} Ошибка при инициализации Bot: {e}")

def activity(bot: Bot, amount_input):

    excel_report = Excel(bot.account, file='SoneiumActivity.xlsx')
    soneium_onchain = Onchain(bot.account, Chains.SONEIUM)
    balance_before = soneium_onchain.get_balance().ether
    if balance_before > amount_input:
        logger.warning(
            f'Баланс в сети {Chains.SONEIUM.name.upper()}: {balance_before:.5f} ETH. Пополнение не требуется!')
        return


    op_onchain = Onchain(bot.account, Chains.OP)
    op_balance = op_onchain.get_balance(address=bot.account.address)
    deposit_amount = amount_input - balance_before
    if deposit_amount > op_balance * 1.05:
        logger.error(
            f'Баланс в сети {Chains.OP.name.upper()} недостаточный для перевода: {balance_before:.5f} ETH!')
        return

    bot.metamask.auth_metamask()
    bot.metamask.select_chain(Chains.OP)
    bot.ads.open_url('https://superbridge.app/soneium')
    random_sleep(2, 3)
    button_agree = bot.ads.page.get_by_role('button', name='Agree & continue')
    if button_agree.count():
        button_agree.click()

    connect_button = bot.ads.page.get_by_role('button', name='Connect')
    if connect_button.count():
        bot.ads.page.get_by_role('button', name='Connect').first.click()
        random_sleep(2, 3)
        bot.ads.page.get_by_text('MetaMask').click()
        bot.metamask.universal_confirm()
        random_sleep(2, 3)

    bot.ads.page.locator('//span[text()="From"]/following-sibling::span').click()
    random_sleep(2, 3)
    bot.ads.page.get_by_role('heading', name='OP Mainnet').click()
    random_sleep(2, 3)
    bot.ads.page.get_by_role('textbox').click()
    random_sleep(2, 3)
    bot.ads.page.keyboard.type(f'{deposit_amount:.5f}', delay=300)
    if bot.ads.page.locator('button', has_text='Insufficient ETH for gas').count():
        logger.error('Недостаточно средств для отправки транзакции!')
        return
    time.sleep(10)
    bot.ads.page.get_by_role('button', name='Review bridge').click()
    random_sleep(2, 3)
    bot.ads.page.get_by_role('button', name='Continue').click()
    if bot.ads.page.get_by_role('heading',
                                name="Make sure the wallet you're bridging to supports Soneium").count():
        bot.ads.page.locator('#addressCheck').click()
        bot.ads.page.get_by_role('button', name='Continue').click()
    bot.ads.page.get_by_role('button', name='Start').click()
    bot.metamask.universal_confirm(windows=2, buttons=2)

    for _ in range(60):
        balance_after = soneium_onchain.get_balance().ether
        if balance_after > balance_before:
            excel_report.set_cell('Address', f'{bot.account.address}')
            excel_report.set_date('Date')
            excel_report.set_cell(f'OP Bridge', f'{deposit_amount:.5f}')
            logger.success('Транзакция прошла успешно! Данные записаны в таблицу SoneiumActivity.xlsx')
            break
        random_sleep(10, 15)
    else:
        logger.error('Транзакция не прошла!')
        raise Exception('Транзакция не прошла!')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную')