import brownie
from brownie import Contract
from useful_methods import genericStateOfVault, genericStateOfStrat
import random
import pytest


def test_apr(accounts, token, vault, strategy, chain, strategist, whale):
    strategist = accounts[0]

    amount = 1 * 1e18
    # Deposit to the vault
    token.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    assert token.balanceOf(vault.address) == amount

    # harvest
    strategy.harvest()
    startingBalance = vault.totalAssets()
    for i in range(2):

        waitBlock = 50
        # print(f'\n----wait {waitBlock} blocks----')
        chain.mine(waitBlock)
        chain.sleep(waitBlock * 13)
        # print(f'\n----harvest----')
        strategy.harvest({"from": strategist})

        # genericStateOfStrat(strategy, currency, vault)
        # genericStateOfVault(vault, currency)

        profit = (vault.totalAssets() - startingBalance) / 1e18
        strState = vault.strategies(strategy)
        totalReturns = strState[7]
        totaleth = totalReturns / 1e18
        # print(f'Real Profit: {profit:.5f}')
        difff = profit - totaleth
        # print(f'Diff: {difff}')

        blocks_per_year = 2_252_857
        assert startingBalance != 0
        time = (i + 1) * waitBlock
        assert time != 0
        apr = (totalReturns / startingBalance) * (blocks_per_year / time)
        assert apr > 0
        # print(apr)
        print(f"implied apr: {apr:.8%}")


def test_normal_activity(accounts, token, vault, strategy, strategist, whale, chain):

    amount = 1 * 1e18
    bbefore = token.balanceOf(whale)

    # Deposit to the vault
    token.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    assert token.balanceOf(vault.address) == amount

    # harvest
    strategy.harvest()
    for i in range(15):
        waitBlock = random.randint(10, 50)

    strategy.harvest()
    chain.sleep(60000)
    # withdrawal
    vault.withdraw({"from": whale})
    assert token.balanceOf(whale) > bbefore
    genericStateOfStrat(strategy, token, vault)
    genericStateOfVault(vault, token)


def test_emergency_withdraw(
    accounts, token, vault, strategy, strategist, whale, chain, pid, RELATIVE_APPROX
):
    amount = 1 * 1e18
    bbefore = token.balanceOf(whale)

    # Deposit to the vault
    token.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})

    # harvest deposit into staking contract
    strategy.harvest()
    assert token.balanceOf(strategy) == 0
    strategy.emergencyWithdrawal(pid, {"from": accounts[0]})
    assert token.balanceOf(strategy) >= amount


def test_emergency_exit(
    accounts, token, vault, strategy, strategist, amount, RELATIVE_APPROX
):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": accounts[0]})
    vault.deposit(amount, {"from": accounts[0]})
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount
    # set emergency and exit
    strategy.setEmergencyExit()
    strategy.harvest()
    assert token.balanceOf(strategy.address) < amount


def test_profitable_harvest(
    accounts, token, vault, strategy, strategist, amount, RELATIVE_APPROX
):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": accounts[0]})
    vault.deposit(amount, {"from": accounts[0]})
    assert token.balanceOf(vault.address) == amount

    # harvest
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # You should test that the harvest method is capable of making a profit.
    # TODO: uncomment the following lines.
    # strategy.harvest()
    # chain.sleep(3600 * 24)
    # assert token.balanceOf(strategy.address) > amount


def test_change_debt(gov, token, vault, strategy, strategist, amount, RELATIVE_APPROX):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": gov})
    vault.deposit(amount, {"from": gov})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    strategy.harvest()

    half = int(amount / 2)

    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == half

    vault.updateStrategyDebtRatio(strategy.address, 10_000, {"from": gov})
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount


def test_sweep(gov, vault, strategy, token, amount, wbnb, wbnb_amout):
    # Strategy want token doesn't work
    token.transfer(strategy, amount, {"from": gov})
    assert token.address == strategy.want()
    assert token.balanceOf(strategy) > 0
    with brownie.reverts("!want"):
        strategy.sweep(token, {"from": gov})

    # Vault share token doesn't work
    with brownie.reverts("!shares"):
        strategy.sweep(vault.address, {"from": gov})

    # TODO: If you add protected tokens to the strategy.
    # Protected token doesn't work
    # with brownie.reverts("!protected"):
    #     strategy.sweep(strategy.protectedToken(), {"from": gov})

    wbnb.transfer(strategy, wbnb_amout, {"from": gov})
    assert wbnb.address != strategy.want()
    assert wbnb.balanceOf(gov) == 0
    strategy.sweep(wbnb, {"from": gov})
    assert wbnb.balanceOf(gov) == wbnb_amout


def test_triggers(gov, vault, strategy, token, amount, wbnb, wbnb_amout):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": gov})
    vault.deposit(amount, {"from": gov})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    strategy.harvest()

    strategy.harvestTrigger(0)
    strategy.tendTrigger(0)
