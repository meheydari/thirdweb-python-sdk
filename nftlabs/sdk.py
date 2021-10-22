from eth_account.account import LocalAccount, Account
from web3 import Web3, HTTPProvider

from typing import Optional

from .errors import NoSignerException
from .modules import CurrencyModule, NftModule, PackModule, CollectionModule
from .options import SdkOptions
from .storage import IpfsStorage

from zero_ex.contract_wrappers import TxParams


class NftlabsSdk(object):
	client: Web3
	options: SdkOptions

	__private_key: str
	signer_address: str
	__current_account: Optional[LocalAccount]

	storage: IpfsStorage

	__currency_module: Optional[CurrencyModule]
	__nft_module: Optional[NftModule]
	__pack_module: Optional[PackModule]
	__collection_module: Optional[CollectionModule]

	"""
	Create instance of the NftlabsSdk
	"""
	def __init__(self, options: SdkOptions, url: str, private_key=""):
		print("Created Nftlabs SDK!")

		self.__currency_module = None
		self.__nft_module = None
		self.__pack_module = None
		self.__collection_module = None
		self.__current_account = None

		self.options = options
		if private_key != "":
			self.set_private_key(private_key)

		self.storage = IpfsStorage(
			options.ipfs_gateway_url if options.ipfs_gateway_url
			else "https://cloudflare-ipfs.com/ipfs/")

		self.client = Web3(HTTPProvider(url))
		if not self.client.isConnected():
			raise Exception("Failed to connect to the web3 provider")

	"""
	Sets the Private Key used across the entire SDK. Calling this method
	will automatically reload the private key across all instantiated
	modules, which allows you to operate on behalf of multiple
	wallets by calling a single method.
	"""
	def set_private_key(self, private_key=""):
		self.__current_account = Account.from_key(private_key)
		self.__private_key = "0x" + private_key.lstrip("0x")
		self.signer_address = self.__current_account.address

	"""
	Returns an instance of the currency module
	"""
	def get_currency_module(self, address: str) -> CurrencyModule:
		if self.__currency_module is not None:
			return self.__currency_module

		module = CurrencyModule(address, self.__get_client())
		self.__init_module(module)
		self.__currency_module = module
		return self.__currency_module

	"""
	Returns an instance of the nft module
	"""
	def get_nft_module(self, address: str) -> NftModule:
		if self.__nft_module is not None:
			return self.__nft_module

		module = NftModule(address, self.__get_client())
		self.__init_module(module)
		self.__nft_module = module
		return self.__nft_module

	"""
	Returns an instance of the pack module
	"""
	def get_pack_module(self, address: str) -> PackModule:
		if self.__pack_module is not None:
			return self.__pack_module

		module = PackModule(address, self.__get_client())
		self.__init_module(module)
		self.__pack_module = module
		return self.__pack_module

	"""
	Returns an instance of the collection module
	"""
	def get_collection_module(self, address: str) -> CollectionModule:
		if self.__collection_module is not None:
			return self.__collection_module

		module = CollectionModule(address, self.__get_client())
		self.__init_module(module)
		self.__collection_module = module
		return self.__collection_module

	"""
	Internal function used to return the current web3 provider used by downstream modules
	"""
	def __get_client(self) -> Web3:
		return self.client

	def __get_storage(self) -> IpfsStorage:
		return self.storage

	def __get_signer_address(self) -> str:
		if self.signer_address == "":
			raise NoSignerException()
		return self.signer_address

	def __get_private_key(self) -> str:
		return self.__private_key

	def __get_transact_ops(self) -> TxParams:
		return TxParams(
			from_=self.__get_signer_address(),
			gas_price=self.client.toWei(self.options.max_gas_price_in_gwei, 'gwei')
		)

	def __get_account(self) -> Optional[LocalAccount]:
		return self.__current_account

	def __get_options(self) -> Optional[SdkOptions]:
		return self.options

	def __init_module(self, module):
		module.get_account = self.__get_account
		module.get_options = self.__get_options
		module.get_client = self.__get_client
		module.get_storage = self.__get_storage
		module.get_signer_address = self.__get_signer_address
		module.get_private_key = self.__get_private_key
		module.get_transact_opts = self.__get_transact_ops
