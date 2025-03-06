from loguru import logger
import time
from config import config, Chains
from core.bot import Bot
from core.excel import Excel
from models.account import Account
from utils.inputs import input_pause
from utils.logging import init_logger
from utils.utils import (random_sleep, get_accounts, select_profiles)
import random


def main():

    if not config.is_browser_run:
        config.is_browser_run = True
    init_logger()
    accounts = get_accounts()
    accounts_for_work = select_profiles(accounts)
    pause = input_pause()

    for i in range(config.cycle):
        random.shuffle(accounts_for_work)
        for account in accounts_for_work:
            worker(account)
            random_sleep(pause)

        logger.success(f'Цикл {i + 1} завершен, обработано {len(accounts_for_work)} аккаунтов!')
        logger.info(f'Ожидание перед следующим циклом ~{config.pause_between_cycle[1]} секунд')
        random_sleep(*config.pause_between_cycle)

def worker(account: Account) -> None:
    try:
        with Bot(account) as bot:
            activity(bot)
    except Exception as e:
        logger.critical(f"{account.profile_number} Ошибка при инициализации Bot: {e}")

def activity(bot: Bot):

    excel_report = Excel(bot.account, file='SoneiumActivity.xlsx')
    excel_report.set_cell('Address', f'{bot.account.address}')
    excel_report.set_date('Date')
    bot.metamask.auth_metamask()
    bot.metamask.select_chain(Chains.SONEIUM)
    bot.ads.open_url('https://app.kyo.finance/swap')
    random_sleep(2, 3)

    connect_button = bot.ads.page.get_by_role('button', name='Connect Wallet')
    if connect_button.count():
        bot.ads.page.get_by_role('button', name='Connect Wallet').first.click()
        bot.ads.page.get_by_role('alertdialog').locator('wui-icon[name="checkmarkBold"]').check()
        bot.metamask.connect(bot.ads.page.get_by_text('MetaMask'))
        random_sleep(2, 3)
    random_sleep(2, 3)
    bot.ads.page.locator('div.mantine-13sk9yc').nth(4).click()
    random_sleep(3, 5)
    tokens = [
        bot.ads.page.locator("div.token-selector-elt-container").locator("div.token-selector-elt").filter(
            has_text="USDT"),
        bot.ads.page.locator("div.token-selector-elt-container").locator("div.token-selector-elt").filter(
            has_text="SONE").nth(0),
        bot.ads.page.locator("div.token-selector-elt-container").locator("div.token-selector-elt").filter(
            has_text="ASTR").nth(1),
        bot.ads.page.locator("div.token-selector-elt-container").locator("div.token-selector-elt").filter(
            has_text="ARCAS").nth(0),
        bot.ads.page.locator("div.token-selector-elt-container").locator("div.token-selector-elt").filter(
            has_text="USDC.e")
    ]

    random_tokens = random.sample(tokens, 5)

    for token in random_tokens:
        token.click()
        random_sleep(3, 5)
        bot.ads.page.get_by_role('button', name='25%').first.click()
        time.sleep(5)
        bot.metamask.send_tx(bot.ads.page.get_by_role('button', name='Swap'))
        excel_report.increase_counter(f'KYO Swap')
        time.sleep(10)
        bot.ads.page.locator('section').page.locator('svg[viewBox="0 0 15 15"]').nth(2).click()
        random_sleep(10, 20)
        bot.ads.page.locator('div.swap-arrow-icon').click()
        random_sleep(10, 20)
        bot.ads.page.get_by_role('button', name='100%').first.click()
        random_sleep(10, 20)
        bot.ads.page.get_by_role('button', name='Swap').click()
        bot.metamask.universal_confirm(windows=2, buttons=2)
        excel_report.increase_counter(f'KYO Swap')
        time.sleep(10)
        bot.ads.page.locator('section').page.locator('svg[viewBox="0 0 15 15"]').nth(2).click()
        random_sleep(10, 20)
        bot.ads.page.locator('div.swap-arrow-icon').click()
        random_sleep(10, 20)
        bot.ads.page.locator('div.mantine-13sk9yc').nth(4).click()
        random_sleep(10, 20)

    logger.success('Активность на KYO.FINANCE прошла успешно! Данные записаны в таблицу SoneiumActivity.xlsx')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную')