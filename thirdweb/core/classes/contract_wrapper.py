from typing import Any, List, Optional, Union, cast
from eth_typing import Address

from web3 import Web3
from web3.contract import Contract
from thirdweb.abi import TWFactory, TWRegistry
from thirdweb.common.error import NoSignerException

from thirdweb.core.classes.provider_handler import ProviderHandler
from thirdweb.abi import TokenERC721, TokenERC1155, TokenERC20
from web3.eth import TxReceipt
from eth_account.account import LocalAccount
from zero_ex.contract_wrappers.tx_params import TxParams

from thirdweb.types.sdk import SDKOptions


class ContractWrapper(ProviderHandler):
    """
    The contract wrapper wraps an instance of a specific thirdweb contract ABI
    and exposed functions for interacting with the contract.
    """

    _contract_abi: Union[TokenERC721, TokenERC1155, TokenERC20, TWRegistry, TWFactory]

    def __init__(
        self,
        contract_abi: Union[
            TokenERC721, TokenERC1155, TokenERC20, TWRegistry, TWFactory
        ],
        provider: Web3,
        signer: Optional[LocalAccount] = None,
        options: SDKOptions = SDKOptions(),
    ):
        """
        Initializes the contract wrapper.

        :param contract_abi: ABI of the thirdweb contract to use
        :param provider: web3 provider instance to use
        :param signer: optional account to use for signing transactions
        """

        super().__init__(provider, signer, options)
        self._contract_abi = contract_abi

    def get_chain_id(self) -> int:
        """
        Get the chain ID of the active provider

        :returns: chain ID of the active provider
        """

        provider = self.get_provider()
        return provider.eth.chain_id

    def get_signer_address(self) -> str:
        """
        Get the address of the active signer

        :returns: address of the active signer
        """

        signer = self.get_signer()

        if signer is None:
            raise NoSignerException

        return signer.address

    def get_contract_interface(self) -> Contract:
        """
        Get the contract interface of the contract wrapper.

        :returns: contract interface of the contract wrapper
        """

        return self.get_provider().eth.contract(
            address=cast(Address, self._contract_abi.contract_address),
            abi=self._contract_abi.abi(),
        )

    def send_transaction(self, fn: str, args: List[Any]) -> TxReceipt:
        """
        Send and execute a transaction and return the receipt.

        :param fn: name of the function you want to call on the contract
        :param args: list of arguments to pass to the function
        """

        provider = self.get_provider()
        signer = self.get_signer()

        if signer is None:
            raise NoSignerException

        nonce = provider.eth.get_transaction_count(signer.address)
        tx = getattr(self._contract_abi, fn).build_transaction(
            *args, tx_params=TxParams(gas_price=provider.eth.gas_price)
        )
        tx["nonce"] = nonce

        # TODO why do we need to do this? (joaquim)
        del tx["from"]

        signed_tx = signer.sign_transaction(tx)
        tx_hash = provider.eth.send_raw_transaction(signed_tx.rawTransaction)

        return provider.eth.wait_for_transaction_receipt(tx_hash)

    def multi_call(self, encoded: List[str]) -> TxReceipt:
        """
        Execute a multicall and return the result.

        :param encoded: list of encoded function calls to execute
        """

        return self.send_transaction("multicall", [encoded])
