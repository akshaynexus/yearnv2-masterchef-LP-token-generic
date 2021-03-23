import pytest
from brownie import config, Contract


@pytest.fixture
def gov(accounts):
    yield accounts[0]


@pytest.fixture
def rewards(accounts):
    yield accounts[1]


@pytest.fixture
def whale(accounts):
    # big binance7 wallet
    # acc = accounts.at('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', force=True)
    # big binance8 wallet
    acc = accounts.at("0x73feaa1eE314F8c655E354234017bE2193C9E24E", force=True)

    # lots of wbnb account
    # wbnbAcc = accounts.at("0x767Ecb395def19Ab8d1b2FCc89B3DDfBeD28fD6b", force=True)
    # wbnb.approve(acc, 2 ** 256 - 1, {"from": wbnbAcc})
    # wbnb.transfer(acc, wbnb.balanceOf(wbnbAcc), {"from": wbnbAcc})

    # assert wbnb.balanceOf(acc) > 0
    yield acc


@pytest.fixture
def token(interface):
    yield interface.ERC20("0xf64a269F0A06dA07D23F43c1Deb217101ee6Bee7")


@pytest.fixture
def cake(interface):
    yield interface.ERC20("0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82")


@pytest.fixture
def masterchef(interface):
    yield Contract("0x73feaa1ee314f8c655e354234017be2193c9e24e")


@pytest.fixture
def router():
    yield Contract("0x05fF2B0DB69458A0750badebc4f9e13aDd608C7F")


@pytest.fixture
def pid(masterchef, token):
    # pid = 0
    # found = False
    # while found == False:
    #     (lpToken, _, _, _) = masterchef.poolInfo(pid)
    #     if lpToken == token:
    #         print(f"found PID: {pid}")
    #         found = True
    #     else:
    #         print(pid)
    #         pid += 1

    # yield pid
    yield 102


@pytest.fixture
def guardian(accounts):
    yield accounts[2]


@pytest.fixture
def management(accounts):
    yield accounts[3]


@pytest.fixture
def strategist(accounts):
    yield accounts[4]


@pytest.fixture
def keeper(accounts):
    yield accounts[5]


@pytest.fixture
def amount(accounts, token):
    amount = 10_000 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at("0x73feaa1eE314F8c655E354234017bE2193C9E24E", force=True)
    token.transfer(accounts[0], amount, {"from": reserve})
    yield amount


@pytest.fixture
def wbnb(interface):
    token_address = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
    yield interface.ERC20(token_address)


@pytest.fixture
def wbnb_amout(gov, wbnb):
    wbnb_amout = 10 ** wbnb.decimals()
    gov.transfer(wbnb, wbnb_amout)
    yield wbnb_amout


# @pytest.fixture
# def live_vault(pm, gov, rewards, guardian, management, token):
#     Vault = pm(config["dependencies"][0]).Vault
#     yield Vault.at('0xE14d13d8B3b85aF791b2AADD661cDBd5E6097Db1')

# @pytest.fixture
# def live_strat(Strategy):
#     yield Strategy.at('0xd4419DDc50170CB2DBb0c5B4bBB6141F3bCc923B')

# @pytest.fixture
# def live_vault_wbnb(pm, gov, rewards, guardian, management, token):
#     Vault = pm(config["dependencies"][0]).Vault
#     yield Vault.at('0xa9fE4601811213c340e850ea305481afF02f5b28')

# @pytest.fixture
# def live_strat_wbnb(Strategy):
#     yield Strategy.at('0xDdf11AEB5Ce1E91CF19C7E2374B0F7A88803eF36')


@pytest.fixture
def vault(pm, gov, rewards, guardian, management, token):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    yield vault


@pytest.fixture
def strategy(
    strategist, keeper, vault, token, wbnb, Strategy, gov, masterchef, cake, router, pid
):
    strategy = strategist.deploy(Strategy, vault, masterchef, cake, router, pid)
    strategy.setKeeper(keeper)

    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    yield strategy


@pytest.fixture(scope="session")
def RELATIVE_APPROX():
    yield 1e-5
