from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal, NotRequired, TypeAlias, TypedDict, TypeGuard, final

from eth_typing import HexStr
from hexbytes import HexBytes

from hl.cloid import Cloid

# TODO: Fix the types which use FIXME
FIXME: TypeAlias = Any


# Library types
class Network(TypedDict):
    """A network such as Mainnet or Testnet."""

    api_url: str
    """The API URL for the network."""
    ws_url: str
    """The WebSocket URL for the network."""
    name: str
    """The name of the network."""
    signature_chain_id: str
    """The signature chain ID for the network."""
    phantom_agent_source: str
    """The phantom agent source for the network."""


class AssetInfo(TypedDict):
    """Information about an asset."""

    id: int
    """The asset ID."""
    name: str
    """The asset name."""
    type: Literal["SPOT", "PERPETUAL"]
    """The type of asset either SPOT or PERPETUAL."""
    pxDecimals: int
    """The maximum number of decimals for the price."""
    szDecimals: int
    """The maximum number of decimals for the size."""


#################
# GENERAL TYPES #
#################


# B = Bid = Buy, A = Ask = Short
Side = Literal["A", "B"]
"""The side of an order either A = Ask = Short or B = Bid = Buy."""
SIDES: list[Side] = ["A", "B"]
"""A list of all possible sides."""


##################
# INFO API TYPES #
##################

# GENERAL


## "type": "allMids"
class AllMidsRequest(TypedDict):
    """A request to retrieve all mids for all actively traded coins."""

    type: Literal["allMids"]
    """The allMids request type."""
    dex: NotRequired[str]
    """The dex to get the mids for."""


AllMids: TypeAlias = dict[str, str]
"""All mids for all actively traded coins mapping the coin name to the mid price."""


AllMidsResponse: TypeAlias = AllMids
"""All mids for all actively traded coins as a response to an all mids request."""

## "type": "openOrders"


class OpenOrdersRequest(TypedDict):
    """A request to retrieve a user's open orders."""

    type: Literal["openOrders"]
    """The openOrders request type."""
    user: str
    """The user to get the open orders for."""


class OpenOrder(TypedDict):
    """An open order."""

    coin: str
    """The asset of the order."""
    side: Side
    """The side of the order."""
    limitPx: str
    """The limit price of the order."""
    sz: str
    """The size of the order."""
    oid: int
    """The order ID."""
    timestamp: int
    """The timestamp of the order."""
    origSz: str
    """The original size of the order."""


OpenOrdersResponse: TypeAlias = list[OpenOrder]
"""A list of open orders as a response to an open orders request."""

## "type": "frontendOpenOrders"


class FrontendOpenOrdersRequest(TypedDict):
    """A request to retrieve a user's open orders with additional frontend info."""

    type: Literal["frontendOpenOrders"]
    """The frontendOpenOrders request type."""
    user: str
    """The user to get the open orders for."""


class FrontendOpenOrder(OpenOrder):
    """An open order with additional frontend info."""

    isPositionTpsl: bool
    """Whether the order is a position take profit or stop loss order."""
    isTrigger: bool
    """Whether the order is a trigger order."""
    orderType: Literal["Limit", "Trigger"]  # TODO: Validate values
    """The type of the order."""
    reduceOnly: bool
    """Whether the order is a reduce only order."""
    triggerCondition: Literal["N/A"]  # TODO: Validate values
    """The trigger condition of the order."""
    triggerPx: str
    """The trigger price of the order."""


FrontendOpenOrdersResponse: TypeAlias = list[FrontendOpenOrder]
"""A list of open orders with additional frontend info as a response to a frontend open orders request."""


# "type": "userFills
class UserFillsRequest(TypedDict):
    """A request to retrieve a user's fills."""

    type: Literal["userFills"]
    """The userFills request type."""
    user: str
    """The user to get the fills for."""


# TODO: Is this complete?
FillDirection = Literal[
    "Close Long",
    "Close Short",
    "Long > Short",
    "Open Long",
    "Open Short",
    "Short > Long",
]
"""The direction of a fill."""


class UserFill(TypedDict):
    """A user fill."""

    closedPnl: str
    """The closed PnL of the fill."""
    coin: str
    """The asset of the fill."""
    crossed: bool
    """Whether the fill was crossed."""
    dir: FillDirection
    """The direction of the fill."""
    hash: str
    """The hash of the fill."""
    oid: int
    """The order ID of the fill."""
    px: str
    """The price of the fill."""
    side: Side
    """The side of the fill."""
    startPosition: str
    """The start position of the fill."""
    sz: str
    """The size of the fill."""
    time: int
    """The timestamp of the fill."""
    fee: str
    """The fee of the fill."""
    feeToken: str
    """The fee token of the fill."""
    tid: int
    """The transaction ID of the fill."""
    liquidation: NotRequired[FIXME]
    """The liquidation of the fill."""
    builderFee: NotRequired[str]
    """The builder fee of the fill."""


UserFillsResponse: TypeAlias = list[UserFill]
"""A list of user fills as a response to a user fills request."""


## "type": "userFillsByTime"


class UserFillsByTimeRequest(TypedDict):
    """A request to retrieve a user's fills by time."""

    type: Literal["userFillsByTime"]
    """The userFillsByTime request type."""
    user: str
    """The user to get the fills for."""
    startTime: int
    """The start time of the fills."""
    endTime: NotRequired[int | None]
    """The end time of the fills."""
    aggregateByTime: NotRequired[bool | None]
    """Whether to aggregate the fills by time."""


## "type": "userTwapSliceFills"


class UserTwapSliceFillsRequest(TypedDict):
    """A request to retrieve a user's TWAP slice fills."""

    type: Literal["userTwapSliceFills"]
    """The userTwapSliceFills request type."""
    user: str
    """The user to get the TWAP slice fills for."""


class UserTwapSliceFill(TypedDict):
    """A user's TWAP slice fill."""

    fill: UserFill
    """The fill of the TWAP slice."""
    twapId: int
    """The TWAP ID of the TWAP slice."""


UserTwapSliceFillsResponse: TypeAlias = list[UserTwapSliceFill]
"""A user's TWAP slice fills as a response to a user TWAP slice fills request."""


## "type": "userRateLimit"


class UserRateLimitRequest(TypedDict):
    """A request to retrieve a user's rate limit."""

    type: Literal["userRateLimit"]
    """The userRateLimit request type."""
    user: str
    """The user to get the rate limit for."""


class UserRateLimitResponse(TypedDict):
    """A user's rate limit as a response to a user rate limit request."""

    cumVlm: str
    """The cumulative volume of the user."""
    nRequestsCap: int
    """The number of requests the user is allowed to make."""
    nRequestsUsed: int
    """The number of requests the user has made."""


## "type": "orderStatus"


class OrderStatusRequest(TypedDict):
    """A request to retrieve the status of an order."""

    type: Literal["orderStatus"]
    """The orderStatus request type."""
    user: str
    """The user to get the order status for."""
    oid: int | str
    """The order ID to get the status for."""


class OrderStatusData(TypedDict):
    """The data for an order status."""

    coin: str
    """The asset of the order."""
    side: Side
    """The side of the order."""
    limitPx: str
    """The limit price of the order."""
    sz: str
    """The size of the order."""
    oid: int
    """The order ID."""
    timestamp: int
    """The timestamp of the order."""
    triggerCondition: Literal["N/A"]  # TODO: Validate values
    """The trigger condition of the order."""
    isTrigger: bool
    """Whether the order is a trigger order."""
    triggerPx: str
    """The trigger price of the order."""
    children: list[FIXME]  # TODO: What type are the children?
    """The children of the order."""
    isPositionTpsl: bool
    """Whether the order is a position take profit or stop loss order."""
    reduceOnly: bool
    """Whether the order is a reduce only order."""
    orderType: Literal["Limit", "Trigger", "Market"]  # TODO: Validate values
    """The type of the order."""
    origSz: str
    """The original size of the order."""
    tif: Literal["FrontendMarket", "Gtc"]  # TODO: Possible values?
    """The time in force of the order."""
    cloid: str | None
    """The cloid of the order."""


OrderStatusValue = Literal[
    "open",
    "filled",
    "canceled",
    "triggered",
    "rejected",
    "marginCanceled",
    "vaultWithdrawalCanceled",
    "openInterestCapCanceled",
    "selfTradeCanceled",
    "reduceOnlyCanceled",
    "siblingFilledCanceled",
    "delistedCanceled",
    "liquidatedCanceled",
    "scheduledCancel",
]
"""The possible values for the status of an order (e.g. open, filled, canceled, etc.)."""


class OrderStatus(TypedDict):
    """The status of an order."""

    order: OrderStatusData
    """The order status data."""
    status: OrderStatusValue
    """The status of the order."""
    statusTimestamp: int
    """The timestamp of the status of the order."""


class OrderStatusResponse(TypedDict):
    """The response to a request for the status of an order."""

    status: Literal["order"]
    """The status of the response (always "order")."""
    order: OrderStatus
    """The order data."""


## "type": "historicalOrders"


class HistoricalOrdersRequest(TypedDict):
    """A request to retrieve a user's historical orders."""

    type: Literal["historicalOrders"]
    """The historicalOrders request type."""
    user: str
    """The user to get the historical orders for."""


HistoricalOrdersResponse: TypeAlias = list[OrderStatus]
"""A list of historical orders as a response to a historical orders request."""

## "type": "subAccounts"


class SubAccountsRequest(TypedDict):
    """A request to retrieve a user's subaccounts."""

    type: Literal["subAccounts"]
    """The subAccounts request type."""
    user: str
    """The user to get the subaccounts for."""


class SubAccount(TypedDict):
    """A subaccount."""

    name: str
    """The name of the subaccount."""
    subAccountUser: str
    """The subaccount user."""
    master: str
    """The master user."""
    clearingHouseState: UserState
    """The clearing house state of the subaccount."""
    spotState: SpotUserState
    """The spot state of the subaccount."""


SubAccountsResponse: TypeAlias = list[SubAccount]
"""A list of subaccounts as a response to a subaccounts request."""


## "type": "l2Book"


class L2BookRequest(TypedDict):
    """A request to retrieve the L2 book for a given coin."""

    type: Literal["l2Book"]
    """The l2Book request type."""
    coin: str
    """The asset to get the L2 book data for."""
    nSigFigs: NotRequired[int | None]
    """The number of significant figures to use for the L2 book."""
    mantissa: NotRequired[int | None]
    """The mantissa to use for the L2 book."""


class L2Level(TypedDict):
    """An entry on one side of the L2 book."""

    px: str
    """The price of the L2 level."""
    sz: str
    """The size of the L2 level."""
    n: int
    """The number of orders at the L2 level."""


class L2Book(TypedDict):
    """L2 book data."""

    coin: str
    """The asset of the L2 book."""
    # 0: Bid, 1: Ask
    levels: list[list[L2Level]]
    """The L2 levels for the bid and ask sides of the L2 book. The first list is the bid side, the second is the ask side."""
    time: int
    """The timestamp of the L2 book."""


L2BookResponse: TypeAlias = L2Book
"""L2 book data as a response to an L2 book request."""


## "type": "candleSnapshot"


CandleInterval = Literal[
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
    "1M",
]
"""The interval of a candle."""


class CandleSnapshotRequestPayload(TypedDict):
    """The specification for which candle snapshot to retrieve."""

    coin: str
    """The asset to get the candle snapshot for."""
    interval: CandleInterval
    """The interval of the candle snapshot."""
    startTime: int
    """The start time of the candle snapshot."""
    endTime: NotRequired[int | None]  # TODO: Is endTime really not required?
    """The end time of the candle snapshot."""


class CandleSnapshotRequest(TypedDict):
    """A request to retrieve a candle snapshot."""

    type: Literal["candleSnapshot"]
    """The candleSnapshot request type."""
    req: CandleSnapshotRequestPayload
    """The request payload."""


class Candle(TypedDict):
    """A candle."""

    h: str  # High
    """The high price of the candle."""
    l: str  # Low  # noqa: E741
    """The low price of the candle."""
    c: str  # Close
    """The close price of the candle."""
    o: str  # Open
    """The open price of the candle."""
    v: str  # Volume
    """The volume of the candle."""
    t: int  # Start time of candle in ms
    """The start time of the candle in ms."""
    T: int  # End time of candle in ms
    """The end time of the candle in ms."""
    i: CandleInterval  # Interval (e.g. 1m)
    """The interval of the candle."""
    s: str  # Symbol
    """The asset name of the candle."""
    n: int  # Number of trades
    """The number of trades in the candle."""


CandleSnapshotResponse: TypeAlias = list[Candle]
"""A list of candles as a response to a candle snapshot request."""


## "type: "maxBuilderFee"


class MaxBuilderFeeRequest(TypedDict):
    """A request to retrieve the max builder fee."""

    type: Literal["maxBuilderFee"]
    """The maxBuilderFee request type."""
    user: str
    """The user to get the max builder fee for."""
    builder: str
    """The builder to get the max builder fee for."""


MaxBuilderFeeResponse: TypeAlias = int
"""The max builder fee as a response to a max builder fee request."""


## "type": "vaultDetails"


class VaultDetailsRequest(TypedDict):
    """A request to retrieve vault details."""

    type: Literal["vaultDetails"]
    """The vaultDetails request type."""
    vaultAddress: str
    """The vault address to get the details for."""
    # TODO: This field is in the docs but not sure what it is for?
    user: NotRequired[str]
    """The user to get the vault details for."""


class VaultPortfolioItem(TypedDict):
    """A portfolio item."""

    # Inner list is always [timestamp: int, value: str]
    accountValueHistory: list[list[int | str]]
    """The account value history of the vault. Inner list is always [timestamp: int, value: str]"""
    # Inner list is always [timestamp: int, value: str]
    pnlHistory: list[list[int | str]]
    """The PNL history of the vault. Inner list is always [timestamp: int, value: str]"""
    vlm: str
    """The VLM (volume) of the vault."""


class VaultFollower(TypedDict):
    """A vault follower."""

    user: str
    """The user of the vault follower."""
    vaultEquity: str
    """The vault equity of the vault follower."""
    pnl: str
    """The PNL of the vault follower."""
    allTimePnl: str
    """The all time PNL of the vault follower."""
    daysFollowing: int
    """The number of days the vault follower has been following the vault."""
    vaultEntryTime: int
    """The timestamp of the vault entry time of the vault follower."""
    lockupUntil: int
    """The timestamp of the lockup until of the vault follower."""


class VaultRelationship(TypedDict):
    """A vault relationship."""

    type: Literal["normal", "leader", "follower"]
    """The type of the vault relationship."""


class VaultDetailsResponse(TypedDict):
    """A response from the exchange after retrieving vault details."""

    name: str
    """The name of the vault."""
    vaultAddress: str
    """The vault address of the vault."""
    leader: str
    """The leader of the vault."""
    description: str
    """The description of the vault."""
    # Inner list is always [period: Literal, portfolio_item: VaultPortfolioItem]
    portfolio: list[
        list[Literal["day", "week", "month", "allTime"] | VaultPortfolioItem]
    ]
    """The portfolio of the vault. Inner list is always [period: Literal["day", "week", "month", "allTime"], portfolio_item: VaultPortfolioItem]"""
    apr: float
    """The APR of the vault."""
    followerState: FIXME | None  # TODO: What other types can this be?
    """The follower state of the vault."""
    leaderFraction: float
    """The leader fraction of the vault."""
    leaderCommission: float
    """The leader commission of the vault."""
    followers: list[VaultFollower]
    """The followers of the vault."""
    maxDistributable: float
    """The max distributable of the vault."""
    maxWithdrawable: float
    """The max withdrawable of the vault."""
    isClosed: bool
    """Whether the vault is closed."""
    relationship: FIXME | None  # TODO: What other types can this be?
    """The relationship of the vault."""
    allowDeposits: bool
    """Whether the vault allows deposits."""
    alwaysCloseOnWithdraw: bool
    """Whether the vault always closes on withdraw."""


## "type": "userVaultEquities"


class UserVaultEquitiesRequest(TypedDict):
    """A request to retrieve a user's vault equities."""

    type: Literal["userVaultEquities"]
    """The userVaultEquities request type."""
    user: str
    """The user to get the vault equities for."""


class UserVaultEquity(TypedDict):
    """A user's vault equity."""

    vaultAddress: str
    """The vault address of the vault equity."""
    equity: str
    """The equity of the vault equity."""
    # TODO: Is this field always present?
    lockedUntilTimestamp: NotRequired[int]
    """The timestamp of until when the vault equity is locked."""


UserVaultEquitiesResponse: TypeAlias = list[UserVaultEquity]
"""A list of user vault equities as a response to a user vault equities request."""


## "type": "userRole"


class UserRoleRequest(TypedDict):
    """A request to retrieve a user's role."""

    type: Literal["userRole"]
    """The userRole request type."""
    user: str
    """The user to get the role for."""


class UserUserRoleResponse(TypedDict):
    """A response to a user role request for a user."""

    role: Literal["user"]
    """The role user."""


class VaultUserRoleResponse(TypedDict):
    """A response to a user role request for a vault."""

    role: Literal["vault"]
    """The role vault."""


class SubAccountData(TypedDict):
    """Data for a sub account."""

    master: str
    """The master user of the sub account."""


class SubAccountUserRoleResponse(TypedDict):
    """A response to a user role request for a sub account."""

    role: Literal["subAccount"]
    """The role sub account."""
    data: SubAccountData
    """The data of the sub account."""


class AgentData(TypedDict):
    """Data for an agent."""

    user: str
    """The user of the agent."""


class AgentUserRoleResponse(TypedDict):
    """A response to a user role request for an agent."""

    role: Literal["agent"]
    """The role agent."""
    data: AgentData
    """The data of the agent."""


class MissingUserRoleResponse(TypedDict):
    """A response to a user role request for a missing user."""

    role: Literal["missing"]
    """The role missing."""


UserRoleResponse: TypeAlias = (
    UserUserRoleResponse
    | VaultUserRoleResponse
    | SubAccountUserRoleResponse
    | AgentUserRoleResponse
    | MissingUserRoleResponse
)
"""A response to a user role request."""

## "type": "portfolio"


class PortfolioRequest(TypedDict):
    """A request to retrieve a user's portfolio."""

    type: Literal["portfolio"]
    """The portfolio request type."""
    user: str
    """The user to get the portfolio for."""


class PortfolioItem(TypedDict):
    """A portfolio item."""

    accountValueHistory: list[list[int | str]]
    """The account value history of the portfolio. Inner list is always [timestamp: int, value: str]"""
    pnlHistory: list[list[int | str]]
    """The PNL history of the portfolio. Inner list is always [timestamp: int, value: str]"""
    vlm: str
    """The VLM of the portfolio."""


PortfolioResponse: TypeAlias = list[
    list[
        Literal[
            "day",
            "week",
            "month",
            "allTime",
            "perpDay",
            "perpWeek",
            "perpMonth",
            "perpAllTime",
        ]
        | PortfolioItem
    ]
]
"""A response to a user's portfolio request. Inner list is always [period: Literal["day", "week", "month", "allTime", "perpDay", "perpWeek", "perpMonth", "perpAllTime"], portfolio_item: PortfolioItem]"""


## "type": "referral"


class ReferralRequest(TypedDict):
    """A request to retrieve a user's referral."""

    type: Literal["referral"]
    """The referral request type."""
    user: str
    """The user to get the referral for."""


class ReferredBy(TypedDict):
    """A referred by."""

    referrer: str
    """Referrer's address"""
    name: str
    """Referrer's name"""


class NeedToCreateCodeReferrerState(TypedDict):
    """A referrer state when the referrer needs to create a code."""

    stage: Literal["needToCreateCode"]
    """The stage of the referrer state."""


class ReferralState(TypedDict):
    """A referral state."""

    cumVlm: str
    """Cumulative VLM"""
    cumRewardedFeesSinceReferred: str
    """Cumulative rewarded fees since referred"""
    cumFeesRewardedToReferrer: str
    """Cumulative fees rewarded to referrer"""
    timeJoined: int
    """Time joined"""
    user: str
    """User's address"""


class ReadyReferrerStateData(TypedDict):
    """Data for a ready referrer state."""

    code: str
    """Referrer's code"""
    referralStates: list[ReferralState]
    """The referral states of the referrer."""


class ReadyReferrerState(TypedDict):
    """A referrer state when the referrer is ready."""

    stage: Literal["ready"]
    """The stage of the referrer state."""
    data: ReadyReferrerStateData
    """The data of the referrer state."""


ReferrerState: TypeAlias = NeedToCreateCodeReferrerState | ReadyReferrerState
"""A referrer state."""


class ReferralResponse(TypedDict):
    """A referral response."""

    referredBy: ReferredBy | None
    """The referred by of the referral."""
    cumVlm: str
    """The cumulative VLM of the referral."""
    unclaimedRewards: str
    """The unclaimed rewards of the referral."""
    claimedRewards: str
    """The claimed rewards of the referral."""
    builderRewards: str
    """The builder rewards of the referral."""
    referrerState: ReferrerState
    """The referrer state of the referral."""
    rewardHistory: list[list[int | str]]
    """Legacy field"""


## "type": "userFees"


class UserFeesRequest(TypedDict):
    """A request to retrieve a user's fees."""

    type: Literal["userFees"]
    """The userFees request type."""
    user: str
    """The user to get the fees for."""


class DailyUserVlm(TypedDict):
    """A daily user VLM."""

    date: str
    """The date of the daily user VLM."""
    userCross: str
    """The user cross of the daily user VLM."""
    userAdd: str
    """The user add of the daily user VLM."""
    exchange: str
    """The exchange of the daily user VLM."""


class VipTier(TypedDict):
    """A VIP tier."""

    ntlCutoff: str
    """The notional cutoff of the VIP tier."""
    cross: str
    """The cross of the VIP tier."""
    add: str
    """The add of the VIP tier."""
    spotCross: str
    """The spot cross of the VIP tier."""
    spotAdd: str
    """The spot add of the VIP tier."""


class MakerFractionCutoffTier(TypedDict):
    """A maker fraction cutoff tier."""

    makerFractionCutoff: str
    """The maker fraction cutoff of the maker fraction cutoff tier."""
    add: str
    """The add of the maker fraction cutoff tier."""


class FeeTiers(TypedDict):
    """A fee tiers."""

    vip: list[VipTier]
    """The VIP tiers."""
    mm: list[MakerFractionCutoffTier]
    """The maker fraction cutoff tiers."""


class StakingDiscountTier(TypedDict):
    """A staking discount tier."""

    bpsOfMaxSupply: str
    """The basis points of the max supply of the staking discount tier."""
    discount: str
    """The discount of the staking discount tier."""


class FeeSchedule(TypedDict):
    """A fee schedule."""

    cross: str
    """The cross trading fee rate."""
    add: str
    """The add liquidity fee rate."""
    spotCross: str
    """The spot cross trading fee rate."""
    spotAdd: str
    """The spot add liquidity fee rate."""
    tiers: FeeTiers
    """The fee tiers structure."""
    referralDiscount: str
    """The referral discount amount."""
    stakingDiscountTiers: list[StakingDiscountTier]
    """The staking discount tiers."""


class StakingLink(TypedDict):
    """A staking link."""

    type: Literal["tradingUser"]
    """The type of staking link."""
    stakingUser: str
    """The staking user address."""


class UserFeesResponse(TypedDict):
    """A response to a user's fees request."""

    dailyUserVlm: list[DailyUserVlm]
    """The daily user VLM data."""
    feeSchedule: FeeSchedule
    """The fee schedule information."""
    userCrossRate: str
    """The user's cross trading fee rate."""
    userAddRate: str
    """The user's add liquidity fee rate."""
    userSpotCrossRate: str
    """The user's spot cross trading fee rate."""
    userSpotAddRate: str
    """The user's spot add liquidity fee rate."""
    activeReferralDiscount: str
    """The active referral discount amount."""
    trial: None  # TODO: Can it have another type?
    """The trial information."""
    feeTrialReward: str
    """The fee trial reward amount."""
    nextTrialAvailableTimestamp: None  # TODO: Can it have another type?
    """The timestamp when the next trial becomes available."""
    stakingLink: StakingLink | None
    """The staking link information."""
    activeStakingDiscount: StakingDiscountTier
    """The active staking discount tier."""


## "type": "delegations"


class DelegationsRequest(TypedDict):
    """A request to retrieve a user's delegations."""

    type: Literal["delegations"]
    """The delegations request type."""
    user: str
    """The user to get the delegations for."""


class Delegation(TypedDict):
    """A delegation."""

    validator: str
    """The validator address."""
    amount: str
    """The amount delegated."""
    lockedUntilTimestamp: int
    """The timestamp until which the delegation is locked."""


DelegationsResponse: TypeAlias = list[Delegation]
"""A response to a user's delegations request."""


## "type": "delegatorSummary"


class DelegatorSummaryRequest(TypedDict):
    """A request to retrieve a user's delegator summary."""

    type: Literal["delegatorSummary"]
    """The delegatorSummary request type."""
    user: str
    """The user to get the delegator summary for."""


class DelegatorSummaryResponse(TypedDict):
    """A response to a user's delegator summary request."""

    delegated: str
    """The amount delegated."""
    undelegated: str
    """The amount undelegated."""
    totalPendingWithdrawal: str
    """The total pending withdrawal amount."""
    nPendingWithdrawals: int
    """The number of pending withdrawals."""


## "type": "delegatorHistory"


class DelegatorHistoryRequest(TypedDict):
    """A request to retrieve a user's delegator history."""

    type: Literal["delegatorHistory"]
    """The delegatorHistory request type."""
    user: str
    """The user to get the delegator history for."""


class DelegatorDeltaDelegateData(TypedDict):
    """A delegator delta delegate."""

    validator: str
    """The validator address."""
    amount: str
    """The amount delegated/undelegated."""
    isUndelegate: bool
    """Whether this is an undelegate operation."""


class DelegatorDeltaDelegate(TypedDict):
    """A delegator delta."""

    delegate: DelegatorDeltaDelegateData
    """The delegate data."""


class DelegatorDeltaWithdrawalData(TypedDict):
    """A delegator delta withdrawal."""

    amount: str
    """The withdrawal amount."""
    phase: Literal["finalized", "initiated"]
    """The phase of the withdrawal."""


class DelegatorDeltaWithdrawal(TypedDict):
    """A delegator delta withdrawal."""

    withdrawal: DelegatorDeltaWithdrawalData
    """The withdrawal data."""


class DelegatorDeltaCDepositData(TypedDict):
    """A delegator delta c deposit."""

    amount: str
    """The deposit amount."""


class DelegatorDeltaCDeposit(TypedDict):
    """A delegator delta c deposit."""

    cDeposit: DelegatorDeltaCDepositData
    """The c deposit data."""


class DelegatorHistoryItem(TypedDict):
    """A delegator history item."""

    time: int
    """The timestamp of the history item."""
    hash: str
    """The hash of the history item."""
    delta: DelegatorDeltaDelegate | DelegatorDeltaWithdrawal | DelegatorDeltaCDeposit
    """The delta data for the history item."""


DelegatorHistoryResponse: TypeAlias = list[DelegatorHistoryItem]
"""A response to a user's delegator history request."""


## "type": "delegatorRewards"


class DelegatorRewardsRequest(TypedDict):
    """A request to retrieve a user's delegator rewards."""

    type: Literal["delegatorRewards"]
    """The delegatorRewards request type."""
    user: str
    """The user to get the delegator rewards for."""


class DelegatorReward(TypedDict):
    """A delegator reward."""

    time: str
    """The time of the reward."""
    source: Literal["delegation", "commission"]  # TODO: Is this exhaustive?
    """The source of the reward."""
    totalAmount: str
    """The total amount of the reward."""


DelegatorRewardsResponse: TypeAlias = list[DelegatorReward]
"""A response to a user's delegator rewards request."""


# PERPETUALS

## "type": "perpDexs"


class PerpDexsRequest(TypedDict):
    """A request to retrieve perp dexs."""

    type: Literal["perpDexs"]


class PerpDex(TypedDict):
    """A perp dex."""

    name: str
    """The name of the perp dex."""
    full_name: str
    """The full name of the perp dex."""
    deployer: str
    """The deployer address."""
    oracle_updater: str | None
    """The oracle updater address."""


PerpDexsResponse: TypeAlias = list[None | PerpDex]
"""A response to a perp dexs request. The first item is always None, subsequent items are perp dex dicts."""


## "type": "meta"


class MetaRequest(TypedDict):
    """A request to retrieve perpetual metadata."""

    type: Literal["meta"]


class AssetMeta(TypedDict):
    """Perpetual asset metadata."""

    name: str
    """The name of the asset."""
    szDecimals: int
    """The number of decimals for the size."""
    maxLeverage: int
    """The maximum leverage allowed."""
    onlyIsolated: NotRequired[bool]
    """Whether the asset is only available for isolated margin."""


class MarginTier(TypedDict):
    """A margin tier."""

    lowerBound: str
    """The lower bound of the margin tier."""
    maxLeverage: int
    """The maximum leverage for this tier."""


class MarginTable(TypedDict):
    """A margin table."""

    description: str
    """The description of the margin table."""
    marginTiers: list[MarginTier]
    """The margin tiers in the table."""


class Meta(TypedDict):
    """Perpetual metadata."""

    universe: list[AssetMeta]
    """The list of asset metadata."""
    # NOTE: Technically not a list of tuple but a list of lists
    marginTables: list[tuple[int, MarginTable]]
    """The margin tables for different assets."""


MetaResponse: TypeAlias = Meta
"""Perpetual metadata as a response to a meta request."""


## "type": "metaAndAssetCtxs"


class MetaAndAssetCtxsRequest(TypedDict):
    """A request to retrieve perpetual metadata and asset context."""

    type: Literal["metaAndAssetCtxs"]


class AssetCtx(TypedDict):
    """Additional context for a perpetual asset."""

    funding: str
    """The funding rate."""
    openInterest: str
    """The open interest."""
    prevDayPx: str
    """The previous day price."""
    dayNtlVlm: str
    """The day notional volume."""
    premium: str | None
    """The premium."""
    oraclePx: str
    """The oracle price."""
    markPx: str
    """The mark price."""
    midPx: str | None
    """The mid price."""
    # NOTE: Technically a list with two items
    impactPxs: tuple[str, str] | None
    """The impact prices."""
    dayBaseVlm: str
    """The day base volume."""


# NOTE: Technically top-level is not a tuple but rather a list with two items
MetaAndAssetCtxsResponse: TypeAlias = tuple[Meta, list[AssetCtx]]
"""The perpetual metadata and asset context as a response to a meta and asset ctxs request."""


## "type": "clearinghouseState"


class UserStateRequest(TypedDict):
    """A request to retrieve a user's open positions and margin summary for perpetuals trading."""

    type: Literal["clearinghouseState"]
    """The clearinghouseState request type."""
    user: str
    """The user to get the state for."""


class Leverage(TypedDict):
    """The leverage of a position."""

    type: Literal["cross", "isolated"]
    """The type of leverage (cross or isolated)."""
    value: int
    """The leverage value."""


class CumFunding(TypedDict):
    """The cumulative funding of a position."""

    allTime: str
    """The cumulative funding all time."""
    sinceChange: str
    """The cumulative funding since the last change."""
    sinceOpen: str
    """The cumulative funding since the position was opened."""


class Position(TypedDict):
    """Details of a user's position in a perpetual asset."""

    coin: str
    """The asset of the position."""
    cumFunding: CumFunding
    """The cumulative funding data."""
    entryPx: str
    """The entry price of the position."""
    leverage: Leverage
    """The leverage information."""
    liquidationPx: str | None
    """The liquidation price."""
    marginUsed: str
    """The margin used for the position."""
    maxLeverage: int
    """The maximum leverage allowed."""
    positionValue: str
    """The value of the position."""
    returnOnEquity: str
    """The return on equity."""
    szi: str
    """The size of the position."""
    unrealizedPnl: str
    """The unrealized PnL."""


class AssetPosition(TypedDict):
    """A user's position in a perpetual asset."""

    position: Position
    """The position details."""
    type: Literal["oneWay"]  # TODO: What are the other type values?
    """The type of position."""


class MarginSummary(TypedDict):
    """A summary of either the cross or total account margin."""

    accountValue: str
    """The account value."""
    totalMarginUsed: str
    """The total margin used."""
    totalNtlPos: str
    """The total notional position."""
    totalRawUsd: str
    """The total raw USD."""


class UserState(TypedDict):
    """A user's open positions and margin summary for perpetuals trading."""

    assetPositions: list[AssetPosition]
    """The list of asset positions."""
    crossMaintenanceMarginUsed: str
    """The cross maintenance margin used."""
    crossMarginSummary: MarginSummary
    """The cross margin summary."""
    marginSummary: MarginSummary
    """The overall margin summary."""
    time: int
    """The timestamp of the state."""
    withdrawable: str
    """The withdrawable amount."""


UserStateResponse: TypeAlias = UserState
"""A user's open positions and margin summary for perpetuals trading as a response to a user state request."""


## "type": "userFunding"


class UserFundingRequest(TypedDict):
    """A request to retrieve a user's funding history."""

    type: Literal["userFunding"]
    """The userFunding request type."""
    user: str
    """The user to get the funding history for."""
    startTime: int
    """The start time for the funding history."""
    endTime: NotRequired[int]
    """The end time for the funding history."""


class _UserFundingDeltaBase(TypedDict):
    coin: str
    """The asset of the funding."""
    usdc: str
    """The USDC amount."""
    szi: str
    """The size."""
    fundingRate: str
    """The funding rate."""
    nSamples: None  # TODO: What is this? Type probably not complete
    """The number of samples."""


class UserFundingDelta(_UserFundingDeltaBase):
    """The delta of an entry in a user's funding history."""

    type: Literal["funding"]
    """The type of funding delta."""


class UserFunding(TypedDict):
    """An entry in a user's funding history."""

    time: int
    """The timestamp of the funding entry."""
    hash: str
    """The hash of the funding entry."""
    delta: UserFundingDelta
    """The funding delta data."""


UserFundingResponse: TypeAlias = list[UserFunding]
"""A list of user funding history entries as a response to a user funding request."""


## "type": "userNonFundingLedgerUpdates"


class UserNonFundingLedgerUpdatesRequest(TypedDict):
    """A request to retrieve a user's non-funding ledger."""

    type: Literal["userNonFundingLedgerUpdates"]
    """The userNonFundingLedgerUpdates request type."""
    user: str
    """The user to get the non-funding ledger for."""
    startTime: int
    """The start time for the ledger updates."""
    endTime: NotRequired[int]
    """The end time for the ledger updates."""


class UserAccountClassTransferDelta(TypedDict):
    """The delta of an account class transfer in a user's non-funding ledger."""

    type: Literal["accountClassTransfer"]
    """The type of delta."""
    usdc: str
    """The USDC amount transferred."""
    toPerp: bool
    """Whether the transfer is to perpetuals."""


class UserDepositDelta(TypedDict):
    """The delta of a deposit in a user's non-funding ledger."""

    type: Literal["deposit"]
    """The type of delta."""
    usdc: str
    """The USDC amount deposited."""


class UserWithdrawDelta(TypedDict):
    """The delta of a withdrawal in a user's non-funding ledger."""

    type: Literal["withdraw"]
    """The type of delta."""
    usdc: str
    """The USDC amount withdrawn."""
    nonce: int
    """The nonce of the withdrawal."""
    fee: str
    """The fee amount."""


class UserSpotTransferDelta(TypedDict):
    """The delta of a spot transfer in a user's non-funding ledger."""

    type: Literal["spotTransfer"]
    """The type of delta."""
    token: str
    """The token being transferred."""
    amount: str
    """The amount transferred."""
    usdcValue: str
    """The USDC value of the transfer."""
    user: str
    """The user making the transfer."""
    destination: str
    """The destination address."""
    fee: str
    """The fee amount."""
    nonce: int
    """The nonce of the transfer."""
    nativeTokenFee: str
    """The native token fee."""


class UserSpotGenesisDelta(TypedDict):
    """The delta of a spot genesis in a user's non-funding ledger."""

    type: Literal["spotGenesis"]
    """The type of delta."""
    token: str
    """The token in the genesis."""
    amount: str
    """The amount of the token."""


class UserVaultCreateDelta(TypedDict):
    """The delta of a vault create in a user's non-funding ledger."""

    type: Literal["vaultCreate"]
    """The type of delta."""
    vault: str
    """The vault address."""
    usdc: str
    """The USDC amount."""
    fee: str
    """The fee amount."""


class UserNonFundingLedgerUpdate(TypedDict):
    """An entry in a user's non-funding ledger."""

    time: int
    """The timestamp of the ledger update."""
    hash: str
    """The hash of the ledger update."""
    # TODO: Is this exhaustive?
    delta: (
        UserAccountClassTransferDelta
        | UserDepositDelta
        | UserWithdrawDelta
        | UserSpotTransferDelta
        | UserSpotGenesisDelta
        | UserVaultCreateDelta
    )
    """The delta data for the ledger update."""


UserNonFundingLedgerUpdatesResponse: TypeAlias = list[UserNonFundingLedgerUpdate]
"""A list of user non-funding ledger entries as a response to a user non-funding ledger updates request."""

## "type": "fundingHistory"


class FundingHistoryRequest(TypedDict):
    """A request to retrieve funding history."""

    type: Literal["fundingHistory"]
    """The fundingHistory request type."""
    coin: str
    """The asset to get the funding history for."""
    startTime: int
    """The start time for the funding history."""
    endTime: NotRequired[int | None]
    """The end time for the funding history."""


class FundingHistoryItem(TypedDict):
    """An entry in a funding history."""

    coin: str
    """The asset of the funding history item."""
    fundingRate: str
    """The funding rate."""
    premium: str
    """The premium."""
    time: int
    """The timestamp of the funding history item."""


FundingHistoryResponse: TypeAlias = list[FundingHistoryItem]
"""A list of funding history items as a response to a funding history request."""


## "type": "predictedFundings"


class PredictedFundingsRequest(TypedDict):
    """A request to retrieve predicted fundings."""

    type: Literal["predictedFundings"]


class PredictedFundingRate(TypedDict):
    """A predicted funding rate."""

    fundingRate: str
    """The predicted funding rate."""
    nextFundingTime: int
    """The next funding time."""


PredictedFundingsItem: TypeAlias = list[list[str | PredictedFundingRate]]
"""A list of list of predicted funding rates. First item in the inner list is the venue, second item is a list of predicted funding rates."""


PredictedFundingsResponse: TypeAlias = list[list[str | PredictedFundingsItem]]
"""A list of list of predicted fundings as a response to a predicted fundings request.
First item of the inner list is the coin, second item is a list of predicted fundings."""


## "type": "perpsAtOpenInterestCap"


class PerpsAtOpenInterestCapRequest(TypedDict):
    """A request to retrieve perps at open interest cap."""

    type: Literal["perpsAtOpenInterestCap"]


PerpsAtOpenInterestCapResponse: TypeAlias = list[str]
"""A list of perps at open interest cap as a response to a perps at open interest cap request."""


## "type": "perpDeployAuctionStatus"


class PerpDeployAuctionStatusRequest(TypedDict):
    """A request to retrieve perp deploy auction status."""

    type: Literal["perpDeployAuctionStatus"]


class PerpDeployAuctionStatusResponse(TypedDict):
    """The perp deploy auction status as a response to a perp deploy auction status request."""

    startTimeSeconds: int
    """The start time in seconds."""
    durationSeconds: int
    """The duration in seconds."""
    startGas: str
    """The starting gas price."""
    currentGas: str | None
    """The current gas price."""
    endGas: str | None
    """The ending gas price."""


# SPOT
## "type": "spotMeta"


class SpotMetaRequest(TypedDict):
    """A request to retrieve spot metadata."""

    type: Literal["spotMeta"]


class SpotAssetMeta(TypedDict):
    """Spot asset metadata."""

    name: str
    """The name of the spot asset."""
    tokens: tuple[int, int]
    """The token IDs that make up the asset."""
    index: int
    """The index of the asset."""
    isCanonical: bool
    """Whether the asset is canonical."""


class SpotTokenMeta(TypedDict):
    """Spot token metadata."""

    name: str
    """The name of the spot token."""
    szDecimals: int
    """The number of decimals for the size."""
    weiDecimals: int
    """The number of decimals for wei."""
    index: int
    """The index of the token."""
    tokenId: str
    """The token ID."""
    isCanonical: bool
    """Whether the token is canonical."""
    evmContract: None
    """The EVM contract address."""
    fullName: None | str
    """The full name of the token."""


class SpotMeta(TypedDict):
    """Spot metadata."""

    universe: list[SpotAssetMeta]
    """The list of spot asset metadata."""
    tokens: list[SpotTokenMeta]
    """The list of spot token metadata."""


SpotMetaResponse: TypeAlias = SpotMeta
"""Spot metadata as a response to a spot meta request."""

## "type": "spotMetaAndAssetCtxs"


class SpotMetaAndAssetCtxsRequest(TypedDict):
    """A request to retrieve spot metadata and asset context."""

    type: Literal["spotMetaAndAssetCtxs"]


class SpotAssetCtx(TypedDict):
    """Spot asset context."""

    circulatingSupply: str
    """The circulating supply."""
    coin: str
    """The asset name."""
    dayNtlVlm: str
    """The day notional volume."""
    markPx: str
    """The mark price."""
    midPx: str | None
    """The mid price."""
    prevDayPx: str
    """The previous day price."""


SpotMetaAndAssetCtxsResponse: TypeAlias = list[SpotMeta | list[SpotAssetCtx]]
"""The spot metadata and asset context as a response to a spot meta and asset ctxs request.
First item is the spot metadata, the second item is a list of asset contexts."""


## "type": "spotClearinghouseState"


class SpotUserStateRequest(TypedDict):
    """A request to retrieve a user's spot balances."""

    type: Literal["spotClearinghouseState"]
    """The spotClearinghouseState request type."""
    user: str
    """The user to get the spot balances for."""


class SpotBalance(TypedDict):
    """A user's spot balance for a given coin."""

    coin: str
    """The asset name."""
    token: int
    """The token ID."""
    total: str
    """The total balance."""
    hold: str
    """The amount on hold."""
    entryNtl: str
    """The entry notional value."""


class SpotUserState(TypedDict):
    """A user's spot balances."""

    balances: list[SpotBalance]
    """The list of spot balances."""


SpotUserStateResponse: TypeAlias = SpotUserState
"""A user's spot balances as a response to a spot user state request."""

## "type": "spotDeployState"


class SpotDeployAuctionStatusRequest(TypedDict):
    """A request to retrieve spot deploy auction status."""

    # NOTE: Type name differs from the API reference to stay consistent with the perp deploy auction status request
    type: Literal["spotDeployState"]
    """The spotDeployState request type."""
    user: str
    """The user to get the spot deploy auction status for."""


class SpotDeploySpec(TypedDict):
    """A spot deploy spec."""

    name: str
    """The name of the spot deploy."""
    szDecimals: int
    """The number of decimals for the size."""
    weiDecimals: int
    """The number of decimals for wei."""


class SpotDeployState(TypedDict):
    """A spot deploy state."""

    token: int
    """The token ID."""
    spec: SpotDeploySpec
    """The spot deploy specification."""
    fullName: str
    """The full name of the token."""
    spots: list[int]
    """The list of spot asset IDs."""
    maxSupply: int
    """The maximum supply."""
    hyperliquidityGenesisBalance: str
    """The hyperliquidity genesis balance."""
    totalGenesisBalanceWei: str
    """The total genesis balance in wei."""
    userGenesisBalances: list[list[str]]
    """The user genesis balances."""
    existingTokenGenesisBalances: list[list[int | str]]
    """The existing token genesis balances."""


class GasAuction(TypedDict):
    """A gas auction."""

    startTimeSeconds: int
    """The start time in seconds."""
    durationSeconds: int
    """The duration in seconds."""
    startGas: str
    """The starting gas price."""
    currentGas: str | None
    """The current gas price."""
    endGas: str | None
    """The ending gas price."""


class SpotDeployAuctionStatusResponse(TypedDict):
    """A response to a spot deploy auction status request."""

    states: list[SpotDeployState]
    """The list of spot deploy states."""
    gasAuction: GasAuction
    """The gas auction information."""


## "type": "tokenDetails"


class TokenDetailsRequest(TypedDict):
    """A request to retrieve token details."""

    type: Literal["tokenDetails"]
    """The tokenDetails request type."""
    tokenId: str
    """The token ID to get details for."""


class GenesisTokenDetails(TypedDict):
    """A token's genesis details."""

    userBalances: list[list[str]]
    """The user balances in the genesis."""
    existingTokenBalances: list[list[int | str]]
    """The existing token balances in the genesis."""


class TokenDetailsResponse(TypedDict):
    """A response to a token details request."""

    name: str
    """The name of the token."""
    maxSupply: str
    """The maximum supply."""
    totalSupply: str
    """The total supply."""
    circulatingSupply: str
    """The circulating supply."""
    szDecimals: int
    """The number of decimals for the size."""
    weiDecimals: int
    """The number of decimals for wei."""
    midPx: str
    """The mid price."""
    markPx: str
    """The mark price."""
    prevDayPx: str
    """The previous day price."""
    genesis: GenesisTokenDetails
    """The genesis token details."""
    deployer: str
    """The deployer address."""
    deployGas: str
    """The deployment gas price."""
    deployTime: str
    """The deployment time."""
    seededUsdc: str
    """The seeded USDC amount."""
    nonCirculatingUserBalances: list[list[str]]
    """The non-circulating user balances."""
    futureEmissions: str
    """The future emissions."""


# General

InfoRequest = (
    AllMidsRequest
    | OpenOrdersRequest
    | FrontendOpenOrdersRequest
    | UserFillsRequest
    | UserFillsByTimeRequest
    | UserTwapSliceFillsRequest
    | UserRateLimitRequest
    | OrderStatusRequest
    | HistoricalOrdersRequest
    | SubAccountsRequest
    | L2BookRequest
    | CandleSnapshotRequest
    | MaxBuilderFeeRequest
    | VaultDetailsRequest
    | UserVaultEquitiesRequest
    | UserRoleRequest
    | PortfolioRequest
    | ReferralRequest
    | UserFeesRequest
    | DelegationsRequest
    | DelegatorSummaryRequest
    | DelegatorHistoryRequest
    | DelegatorRewardsRequest
    | PerpDexsRequest
    | MetaRequest
    | MetaAndAssetCtxsRequest
    | UserStateRequest
    | UserFundingRequest
    | UserNonFundingLedgerUpdatesRequest
    | FundingHistoryRequest
    | PredictedFundingsRequest
    | PerpsAtOpenInterestCapRequest
    | PerpDeployAuctionStatusRequest
    | SpotMetaRequest
    | SpotMetaAndAssetCtxsRequest
    | SpotUserStateRequest
    | SpotDeployAuctionStatusRequest
    | TokenDetailsRequest
)
"""A union of all possible requests that can be sent to the info API."""

InfoResponse = (
    AllMidsResponse
    | OpenOrdersResponse
    | FrontendOpenOrdersResponse
    | UserFillsResponse
    | UserTwapSliceFillsResponse
    | UserRateLimitResponse
    | OrderStatusResponse
    | HistoricalOrdersResponse
    | SubAccountsResponse
    | L2BookResponse
    | CandleSnapshotResponse
    | MaxBuilderFeeResponse
    | VaultDetailsResponse
    | UserVaultEquitiesResponse
    | UserRoleResponse
    | PortfolioResponse
    | ReferralResponse
    | UserFeesResponse
    | DelegationsResponse
    | DelegatorSummaryResponse
    | DelegatorHistoryResponse
    | DelegatorRewardsResponse
    | PerpDexsResponse
    | MetaResponse
    | MetaAndAssetCtxsResponse
    | UserStateResponse
    | UserFundingResponse
    | UserNonFundingLedgerUpdatesResponse
    | FundingHistoryResponse
    | PredictedFundingsResponse
    | PerpsAtOpenInterestCapResponse
    | PerpDeployAuctionStatusResponse
    | SpotMetaResponse
    | SpotMetaAndAssetCtxsResponse
    | SpotUserStateResponse
    | SpotDeployAuctionStatusResponse
    | TokenDetailsResponse
)
"""A union of all possible responses that can be returned from the info API."""

######################
# EXCHANGE API TYPES #
######################


# Shared


class Signature(TypedDict):
    """A signature for an action request."""

    r: HexStr
    """The r component of the signature."""
    s: HexStr
    """The s component of the signature."""
    v: HexBytes | int
    """The v component of the signature."""


# "type": "order"

Tif = Literal["Alo", "Ioc", "Gtc"]
"""Time in force literals."""

Tpsl = Literal["tp", "sl"]
"""Take profit/stop loss literals."""


class LimitOrderTypeWireData(TypedDict):
    """Specific time in force for a limit order."""

    tif: Tif
    """The time in force setting."""


class LimitOrderTypeWire(TypedDict):
    """Serialized limit parameters for an order."""

    limit: LimitOrderTypeWireData
    """The limit order data."""


class LimitOrderType(TypedDict):
    """Limit parameters for an order."""

    type: Literal["limit"]
    """The order type."""
    tif: Tif
    """The time in force setting."""


class TriggerOrderType(TypedDict):
    """Trigger price, limit vs market, and take profit/stop loss parameters for an order."""

    type: Literal["trigger"]
    """The order type."""
    price: Decimal
    """The trigger price."""
    is_market: bool
    """Whether this is a market order."""
    trigger: Tpsl
    """The trigger type (take profit or stop loss)."""


class TriggerOrderTypeWireData(TypedDict):
    """Serialized trigger price, limit vs market, and take profit/stop loss parameters for an order."""

    triggerPx: str
    """The trigger price."""
    isMarket: bool
    """Whether this is a market order."""
    tpsl: Tpsl
    """The trigger type (take profit or stop loss)."""


class TriggerOrderTypeWire(TypedDict):
    """Serialized trigger parameters for an order."""

    trigger: TriggerOrderTypeWireData
    """The trigger order data."""


OrderTypeWire: TypeAlias = LimitOrderTypeWire | TriggerOrderTypeWire
"""Serialized limit or trigger parameters for an order."""

OrderType = LimitOrderType | TriggerOrderType
"""A union of order types (limit or trigger)."""


class OrderWire(TypedDict):
    """Serialized order to be sent to the exchange."""

    a: int
    """The asset ID."""
    b: bool
    """Whether this is a buy order."""
    p: str
    """The price."""
    s: str
    """The size."""
    r: bool
    """Whether this is a reduce-only order."""
    t: OrderTypeWire
    """The order type data."""
    c: NotRequired[str | None]
    """The client order ID."""


Grouping = Literal["na", "normalTpsl", "positionTpsl"]
"""Grouping literals."""


class BuilderOptions(TypedDict):
    """Options for a builder."""

    b: str
    """Address that should receive the additional fee."""

    f: int
    """Size of the fee in tenths of a basis point e.g. if f is 10, 1bp of the order notional."""


class OrderAction(TypedDict):
    """An action to place one or more orders."""

    type: Literal["order"]
    """The action type."""
    orders: list[OrderWire]
    """The list of orders to place."""
    grouping: Grouping
    """The grouping for the orders."""
    builder: NotRequired[BuilderOptions]
    """The builder options."""


class OrderRequest(TypedDict):
    """A request to place one or more orders."""

    action: OrderAction
    """The order action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""
    vaultAddress: str | None
    """The vault address if trading on behalf of a vault."""


class OrderParams(TypedDict):
    """Parameters for an order. Used for high-level order creation."""

    asset: int | str
    """The asset ID or name."""
    is_buy: bool
    """Whether this is a buy order."""
    size: Decimal
    """The size of the order."""
    limit_price: Decimal
    """The limit price for the order."""
    order_type: OrderType
    """The order type (limit or trigger)."""
    reduce_only: bool
    """Whether this is a reduce-only order."""
    cloid: NotRequired[Cloid | None]
    """The client order ID."""


class OrderIdData(TypedDict):
    """The id of a placed order."""

    oid: int
    """The order ID."""
    cloid: NotRequired[str]
    """The client order ID."""


class OrderResponseDataStatusResting(TypedDict):
    """The status of an order that is still resting."""

    resting: OrderIdData
    """The order ID data for the resting order."""


class OrderResponseDataStatusError(TypedDict):
    """The status of an order that failed to be placed."""

    error: str
    """The error message."""


class OrderResponseFill(TypedDict):
    """The details of a fill of a filled order."""

    totalSz: str
    """The total size filled."""
    avgPx: str
    """The average price of the fill."""
    oid: int
    """The order ID."""


class OrderResponseDataStatusFilled(TypedDict):
    """The status of a filled order."""

    filled: OrderResponseFill
    """The fill details."""


OrderResponseDataStatus: TypeAlias = (
    OrderResponseDataStatusResting
    | OrderResponseDataStatusError
    | OrderResponseDataStatusFilled
)
"""The status of an order."""


def is_resting_status(
    status: OrderResponseDataStatus,
) -> TypeGuard[OrderResponseDataStatusResting]:
    """Type guard to check if an order status is resting."""
    return "resting" in status


def is_error_status(
    status: OrderResponseDataStatus,
) -> TypeGuard[OrderResponseDataStatusError]:
    """Type guard to check if an order status is an error."""
    return "error" in status


def is_filled_status(
    status: OrderResponseDataStatus,
) -> TypeGuard[OrderResponseDataStatusFilled]:
    """Type guard to check if an order status is filled."""
    return "filled" in status


class OrderResponseData(TypedDict):
    """The statuses of the orders in a response from the exchange after placing an order."""

    statuses: list[OrderResponseDataStatus]
    """The list of order statuses."""


class OrderResponseResponse(TypedDict):
    """The content of a response from the exchange after placing an order."""

    type: Literal["order"]
    """The response type."""
    data: OrderResponseData
    """The order response data."""


class OrderResponse(TypedDict):
    """A response from the exchange after placing an order."""

    status: Literal["ok"]
    """The response status."""
    response: OrderResponseResponse
    """The response content."""


def decimal_to_wire(x: Decimal) -> str:
    rounded = "{:.8f}".format(x)
    if abs(Decimal(rounded) - x) >= 1e-12:
        raise ValueError("decimal_to_wire causes rounding", x)
    if rounded == "-0":
        rounded = "0"
    normalized = Decimal(rounded).normalize()
    return f"{normalized:f}"


def order_type_to_wire(order_type: OrderType) -> OrderTypeWire:
    if order_type["type"] == "limit":
        return {"limit": {"tif": order_type["tif"]}}
    elif order_type["type"] == "trigger":
        value = TriggerOrderTypeWire(
            trigger={
                "isMarket": order_type["is_market"],
                "triggerPx": decimal_to_wire(order_type["price"]),
                "tpsl": order_type["trigger"],
            }
        )
        return value
    raise ValueError("Invalid order type", order_type)


def order_request_to_order_wire(order: OrderParams, asset_id: int) -> OrderWire:
    order_wire: OrderWire = {
        "a": asset_id,
        "b": order["is_buy"],
        "p": decimal_to_wire(order["limit_price"]),
        "s": decimal_to_wire(order["size"]),
        "r": order["reduce_only"],
        "t": order_type_to_wire(order["order_type"]),
    }
    if "cloid" in order and order["cloid"] is not None:
        order_wire["c"] = order["cloid"].to_raw()
    return order_wire


# "type": "cancel"


class Cancel(TypedDict):
    """A request to cancel an order by its oid."""

    a: int  # Asset ID
    """The asset ID."""
    o: int  # Order Id
    """The order ID."""


class CancelAction(TypedDict):
    """An action to cancel one or more orders by their oid."""

    type: Literal["cancel"]
    """The action type."""
    cancels: list[Cancel]
    """The list of cancels."""


class CancelRequest(TypedDict):
    """A request to cancel one or more orders by their oid."""

    action: CancelAction
    """The cancel action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""
    vaultAddress: str | None
    """The vault address if trading on behalf of a vault."""


class CancelParams(TypedDict):
    """Parameters for a request to cancel an order by its oid."""

    asset: int | str
    """The asset ID or name."""
    order_id: int
    """The order ID to cancel."""


class CancelResponseDataErrorStatus(TypedDict):
    """The status of an order that failed to be cancelled."""

    error: str
    """The error message."""


class CancelResponseData(TypedDict):
    """The data of a response from the exchange after cancelling an order by its oid."""

    statuses: list[Literal["success"] | CancelResponseDataErrorStatus]
    """The list of cancellation statuses."""


class CancelResponseResponse(TypedDict):
    """A response from the exchange after cancelling an order by its oid."""

    type: Literal["cancel"]
    """The response type."""
    data: CancelResponseData
    """The cancel response data."""


class CancelResponse(TypedDict):
    """A response from the exchange after cancelling an order by its oid."""

    status: Literal["ok"]
    """The response status."""
    response: CancelResponseResponse
    """The response content."""


# "type": "cancelByCloid"


class CancelByCloid(TypedDict):
    """A request to cancel an order by its cloid."""

    asset: int
    """The asset ID."""
    cloid: str
    """The client order ID."""


class CancelByCloidAction(TypedDict):
    """An action to cancel one or more orders by their cloid."""

    type: Literal["cancelByCloid"]
    """The action type."""
    cancels: list[CancelByCloid]
    """The list of cancels by cloid."""


class CancelByCloidRequest(TypedDict):
    """A request to cancel one or more orders by their cloid."""

    action: CancelByCloidAction
    """The cancel by cloid action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""
    vaultAddress: str | None
    """The vault address if trading on behalf of a vault."""


class CancelByCloidParams(TypedDict):
    """Parameters for a request to cancel an order by its cloid."""

    asset: int | str
    """The asset ID or name."""
    client_order_id: Cloid | str
    """The client order ID."""


class CancelByCloidResponse(TypedDict):
    """A response from the exchange after cancelling an order by its cloid."""

    status: Literal["ok"]
    """The response status."""
    response: CancelResponseResponse
    """The response content."""


# "type": "scheduleCancel"


class ScheduleCancelAction(TypedDict):
    """An action to schedule a cancel-all operation at a future time."""

    type: Literal["scheduleCancel"]
    """The action type."""
    time: NotRequired[int | None]
    """The time at which to schedule the cancel-all operation."""


class ScheduleCancelRequest(TypedDict):
    """A request to schedule a cancel-all operation at a future time."""

    action: ScheduleCancelAction
    """The schedule cancel action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""
    vaultAddress: str | None
    """The vault address if trading on behalf of a vault."""


class ScheduleCancelResponse(TypedDict):
    """A response from the exchange after scheduling a cancel-all operation at a future time."""

    # TODO: Not documented in docs
    todo: str
    """Placeholder field - not documented in API docs."""


# "type": "modify"


class ModifyAction(TypedDict):
    """An action to modify an order."""

    type: Literal["modify"]
    """The action type."""
    oid: int | str
    """The order ID to modify."""
    order: OrderWire
    """The new order details."""


class ModifyRequest(TypedDict):
    """A request to modify an order."""

    action: ModifyAction
    """The modify action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""
    vaultAddress: str | None
    """The vault address if trading on behalf of a vault."""


class ModifyResponseResponse(TypedDict):
    """The response from the exchange after modifying an order."""

    type: Literal["default"]
    """The response type."""


class ModifyResponse(TypedDict):
    """A response from the exchange after modifying an order."""

    status: Literal["ok"]
    """The response status."""
    response: ModifyResponseResponse
    """The response content."""


# "type": "batchModify"
class ModifyWire(TypedDict):
    """A request to modify an order."""

    oid: int | str
    """The order ID to modify."""
    order: OrderWire
    """The new order details."""


class BatchModifyAction(TypedDict):
    """An action to modify multiple orders."""

    type: Literal["batchModify"]
    """The action type."""
    modifies: list[ModifyWire]
    """The list of order modifications."""


class BatchModifyRequest(TypedDict):
    """A request to modify multiple orders."""

    action: BatchModifyAction
    """The batch modify action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""
    vaultAddress: str | None
    """The vault address if trading on behalf of a vault."""


class ModifyParams(TypedDict):
    """Parameters for a request to modify an order."""

    order_id: int | Cloid
    """The order ID or client order ID."""
    order: OrderParams
    """The new order parameters."""


class BatchModifyResponseResponse(TypedDict):
    """The response from the exchange after modifying multiple orders."""

    type: Literal["order"]
    """The response type."""
    data: OrderResponseData
    """The order response data."""


class BatchModifyResponse(TypedDict):
    """A response from the exchange after modifying multiple orders."""

    status: Literal["ok"]
    """The response status."""
    response: BatchModifyResponseResponse
    """The response content."""


# "type": "updateLeverage"


class UpdateLeverageAction(TypedDict):
    """An action to update the leverage for a given asset."""

    type: Literal["updateLeverage"]
    """The action type."""
    asset: int
    """The asset ID."""
    isCross: bool
    """Whether to use cross margin."""
    leverage: int
    """The leverage value."""


class UpdateLeverageRequest(TypedDict):
    """A request to update the leverage for a given asset."""

    action: UpdateLeverageAction
    """The update leverage action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""
    vaultAddress: str | None
    """The vault address if trading on behalf of a vault."""


class UpdateLeverageResponseBody(TypedDict):
    """The body of a response from the exchange after successfully updating the leverage for a given asset."""

    type: Literal["default"]
    """The response type."""


class UpdateLeverageResponse(TypedDict):
    """A response from the exchange after successfully updating the leverage for a given asset."""

    status: Literal["ok"]
    """The response status."""
    response: UpdateLeverageResponseBody
    """The response body."""


# "type": "updateIsolatedMargin"


class UpdateIsolatedMarginAction(TypedDict):
    """An action to update the isolated margin for a given asset."""

    type: Literal["updateIsolatedMargin"]
    """The action type."""
    asset: int
    """The asset ID."""
    isBuy: bool
    """Whether this is for a buy position."""
    ntli: int
    """The notional value in USD."""


class UpdateIsolatedMarginRequest(TypedDict):
    """A request to update the isolated margin for a given asset."""

    action: UpdateIsolatedMarginAction
    """The update isolated margin action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""
    vaultAddress: str | None
    """The vault address if trading on behalf of a vault."""


class UpdateIsolatedMarginResponseBody(TypedDict):
    """The body of a response from the exchange after successfully updating the isolated margin for a given asset."""

    type: Literal["default"]
    """The response type."""


class UpdateIsolatedMarginResponse(TypedDict):
    """A response from the exchange after successfully updating the isolated margin for a given asset."""

    status: Literal["ok"]
    """The response status."""
    response: UpdateIsolatedMarginResponseBody
    """The response body."""


# "type": "topUpIsolatedOnlyMargin"


class TopUpIsolatedOnlyMarginAction(TypedDict):
    """An action to top up the isolated margin for a given asset."""

    type: Literal["topUpIsolatedOnlyMargin"]
    """The action type."""
    asset: int
    """The asset ID."""
    leverage: str
    """The leverage value."""


class TopUpIsolatedOnlyMarginRequest(TypedDict):
    """A request to top up the isolated margin for a given asset."""

    action: TopUpIsolatedOnlyMarginAction
    """The top up isolated margin action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""
    vaultAddress: str | None
    """The vault address if trading on behalf of a vault."""


class TopUpIsolatedOnlyMarginResponseBody(TypedDict):
    """The data of a response from the exchange after top up of the isolated margin for a given asset."""

    type: Literal["default"]
    """The response type."""


class TopUpIsolatedOnlyMarginResponse(TypedDict):
    """A response from the exchange after top up of the isolated margin for a given asset."""

    status: Literal["ok"]
    """The response status."""
    response: TopUpIsolatedOnlyMarginResponseBody
    """The response body."""


# "type": "usdSend"


class UsdSendAction(TypedDict):
    """An action to send USDC to another address."""

    type: Literal["usdSend"]
    """The action type."""
    hyperliquidChain: str
    """The hyperliquid chain identifier."""
    signatureChainId: str
    """The signature chain ID."""
    destination: str
    """The destination address."""
    amount: str
    """The amount to send."""
    time: int
    """The timestamp."""


class UsdSendRequest(TypedDict):
    """A request to send USDC to another address."""

    action: UsdSendAction
    """The USD send action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class UsdSendResponseBody(TypedDict):
    """The body of a response from the exchange after sending USDC to another address."""

    type: Literal["default"]
    """The response type."""


class UsdSendResponse(TypedDict):
    """A response from the exchange after sending USDC to another address."""

    status: Literal["ok"]
    """The response status."""
    response: UsdSendResponseBody
    """The response body."""


# "type": "spotSend"


class SpotSendAction(TypedDict):
    """An action to send a spot asset to another address."""

    type: Literal["spotSend"]
    """The action type."""
    hyperliquidChain: str
    """The hyperliquid chain identifier."""
    signatureChainId: str
    """The signature chain ID."""
    destination: str
    """The destination address."""
    token: str
    """The token to send."""
    amount: str
    """The amount to send."""
    time: int
    """The timestamp."""


class SpotSendRequest(TypedDict):
    """A request to send a spot asset to another address."""

    action: SpotSendAction
    """The spot send action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class SpotSendResponseBody(TypedDict):
    """The body of a response from the exchange after sending a spot asset to another address."""

    type: Literal["default"]
    """The response type."""


class SpotSendResponse(TypedDict):
    """A response from the exchange after sending a spot asset to another address."""

    status: Literal["ok"]
    """The response status."""
    response: SpotSendResponseBody
    """The response body."""


# "type": "withdraw3"


class WithdrawAction(TypedDict):
    """An action to withdraw USDC via Arbitrum."""

    type: Literal["withdraw3"]
    """The action type."""
    hyperliquidChain: str
    """The hyperliquid chain identifier."""
    signatureChainId: str
    """The signature chain ID."""
    amount: str
    """The amount to withdraw."""
    # TODO: Does order or keys matter here?
    destination: str
    """The destination address."""
    time: int
    """The timestamp."""


class WithdrawRequest(TypedDict):
    """A request to withdraw USDC via Arbitrum."""

    action: WithdrawAction
    """The withdraw action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class WithdrawResponseBody(TypedDict):
    """The body of a response from the exchange after withdrawing USDC via Arbitrum."""

    type: Literal["default"]
    """The response type."""


class WithdrawResponse(TypedDict):
    """A response from the exchange after withdrawing USDC via Arbitrum."""

    status: Literal["ok"]
    """The response status."""
    response: WithdrawResponseBody
    """The response body."""


# "type": "usdClassTransfer"


class UsdClassTransferAction(TypedDict):
    """An action to transfer USDC from a user's spot wallet to their perp wallet and vice versa."""

    type: Literal["usdClassTransfer"]
    """The action type."""
    # TODO: Can this be any other value, i.e. locally?
    hyperliquidChain: str
    """The hyperliquid chain identifier."""
    signatureChainId: str
    """The signature chain ID."""
    amount: str
    """The amount to transfer."""
    toPerp: bool
    """Whether to transfer to perpetuals or from perpetuals."""
    nonce: int
    """The nonce for the action."""


class UsdClassTransferRequest(TypedDict):
    """A request to transfer USDC from a user's spot wallet to their perp wallet and vice versa."""

    action: UsdClassTransferAction
    """The USD class transfer action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class UsdClassTransferResponseBody(TypedDict):
    """The body of a response from the exchange after transferring USDC from a user's spot wallet to their perp wallet and vice versa."""

    type: Literal["default"]
    """The response type."""


class UsdClassTransferResponse(TypedDict):
    """A response from the exchange after transferring USDC from a user's spot wallet to their perp wallet and vice versa."""

    status: Literal["ok"]
    """The response status."""
    response: UsdClassTransferResponseBody
    """The response body."""


# "type": "perpDexClassTransfer"


class PerpDexClassTransferAction(TypedDict):
    """An action to transfer a token from a user's spot wallet to their perp wallet and vice versa."""

    type: Literal["perpDexClassTransfer"]
    """The action type."""
    hyperliquidChain: str
    """The hyperliquid chain identifier."""
    signatureChainId: str
    """The signature chain ID."""
    dex: str
    """The dex identifier."""
    token: str
    """The token to transfer."""
    amount: str
    """The amount to transfer."""
    toPerp: bool
    """Whether to transfer to perpetuals or from perpetuals."""
    nonce: int
    """The nonce for the action."""


class PerpDexClassTransferRequest(TypedDict):
    """A request to transfer a token from a user's spot wallet to their perp wallet and vice versa."""

    action: PerpDexClassTransferAction
    """The perp dex class transfer action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class PerpDexClassTransferResponseBody(TypedDict):
    """The body of a response from the exchange after transferring a token from a user's spot wallet to their perp wallet and vice versa."""

    type: Literal["default"]
    """The response type."""


class PerpDexClassTransferResponse(TypedDict):
    """A response from the exchange after transferring a token from a user's spot wallet to their perp wallet and vice versa."""

    status: Literal["ok"]
    """The response status."""
    response: PerpDexClassTransferResponseBody
    """The response body."""


# "type": "cDeposit"


class DepositStakingAction(TypedDict):
    """An action to deposit a token into staking."""

    type: Literal["cDeposit"]
    """The action type."""
    hyperliquidChain: str
    """The hyperliquid chain identifier."""
    signatureChainId: str
    """The signature chain ID."""
    wei: int
    """The amount in wei."""
    nonce: int
    """The nonce for the action."""


class DepositStakingRequest(TypedDict):
    """A request to deposit a token into staking."""

    action: DepositStakingAction
    """The deposit staking action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class DepositStakingResponseBody(TypedDict):
    """The body of a response from the exchange after depositing a token into staking."""

    type: Literal["default"]
    """The response type."""


class DepositStakingResponse(TypedDict):
    """A response from the exchange after depositing a token into staking."""

    status: Literal["ok"]
    """The response status."""
    response: DepositStakingResponseBody
    """The response body."""


# "type": "cWithdraw"


class WithdrawStakingAction(TypedDict):
    """An action to withdraw a token from staking."""

    type: Literal["cWithdraw"]
    """The action type."""
    hyperliquidChain: str
    """The hyperliquid chain identifier."""
    signatureChainId: str
    """The signature chain ID."""
    wei: int
    """The amount in wei."""
    nonce: int
    """The nonce for the action."""


class WithdrawStakingRequest(TypedDict):
    """A request to withdraw a token from staking."""

    action: WithdrawStakingAction
    """The withdraw staking action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class WithdrawStakingResponseBody(TypedDict):
    """The body of a response from the exchange after withdrawing a token from staking."""

    type: Literal["default"]
    """The response type."""


class WithdrawStakingResponse(TypedDict):
    """A response from the exchange after withdrawing a token from staking."""

    status: Literal["ok"]
    """The response status."""
    response: WithdrawStakingResponseBody
    """The response body."""


# "type": "tokenDelegate"


class TokenDelegateAction(TypedDict):
    """An action to delegate or undelegate stake from a validator."""

    type: Literal["tokenDelegate"]
    """The action type."""
    hyperliquidChain: str
    """The hyperliquid chain identifier."""
    signatureChainId: str
    """The signature chain ID."""
    validator: str
    """The validator address."""
    isUndelegate: bool
    """Whether this is an undelegate operation."""
    wei: int
    """The amount in wei."""
    nonce: int
    """The nonce for the action."""


class TokenDelegateRequest(TypedDict):
    """A request to delegate or undelegate stake from a validator."""

    action: TokenDelegateAction
    """The token delegate action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class TokenDelegateResponseBody(TypedDict):
    """The body of a response from the exchange after delegating or undelegating a stake."""

    type: Literal["default"]
    """The response type."""


class TokenDelegateResponse(TypedDict):
    """The response from the exchange after delegating or undelegating a stake."""

    status: Literal["ok"]
    """The response status."""
    response: TokenDelegateResponseBody
    """The response body."""


# "type": "vaultTransfer"


class VaultTransferAction(TypedDict):
    """An action to add or remove USDC from a vault."""

    type: Literal["vaultTransfer"]
    """The action type."""
    vaultAddress: str
    """The vault address."""
    isDeposit: bool
    """Whether this is a deposit or withdrawal."""
    usd: int
    """The USD amount."""


class VaultTransferRequest(TypedDict):
    """A request to add or remove USDC from a vault."""

    action: VaultTransferAction
    """The vault transfer action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class VaultTransferResponseBody(TypedDict):
    """The body of a response from the exchange after adding or removing USDC from a vault."""

    type: Literal["default"]
    """The response type."""


class VaultTransferResponse(TypedDict):
    """A response from the exchange after adding or removing USDC from a vault."""

    status: Literal["ok"]
    """The response status."""
    response: VaultTransferResponseBody
    """The response body."""


# "type": "approveAgent"


class ApproveAgentAction(TypedDict):
    """An action to approve an agent."""

    type: Literal["approveAgent"]
    """The action type."""
    hyperliquidChain: str
    """The hyperliquid chain identifier."""
    signatureChainId: str
    """The signature chain ID."""
    agentAddress: str
    """The agent address."""
    agentName: str | None
    """The agent name."""
    nonce: int
    """The nonce for the action."""


class ApproveAgentRequest(TypedDict):
    """A request to approve an agent."""

    action: ApproveAgentAction
    """The approve agent action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class ApproveAgentResponseBody(TypedDict):
    """The body of a response from the exchange after approving an agent."""

    type: Literal["default"]
    """The response type."""


class ApproveAgentResponse(TypedDict):
    """A response from the exchange after approving an agent."""

    status: Literal["ok"]
    """The response status."""
    response: ApproveAgentResponseBody
    """The response body."""


# "type": "approveBuilderFee"


class ApproveBuilderFeeAction(TypedDict):
    """An action to approve a builder fee."""

    type: Literal["approveBuilderFee"]
    """The action type."""
    hyperliquidChain: str
    """The hyperliquid chain identifier."""
    signatureChainId: str
    """The signature chain ID."""
    maxFeeRate: str
    """The maximum fee rate."""
    builder: str
    """The builder address."""
    nonce: int
    """The nonce for the action."""


class ApproveBuilderFeeRequest(TypedDict):
    """A request to approve a builder fee."""

    action: ApproveBuilderFeeAction
    """The approve builder fee action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class ApproveBuilderFeeResponseBody(TypedDict):
    """The body of a response from the exchange after approving a builder fee."""

    type: Literal["default"]
    """The response type."""


class ApproveBuilderFeeResponse(TypedDict):
    """A response from the exchange after approving a builder fee."""

    status: Literal["ok"]
    """The response status."""
    response: ApproveBuilderFeeResponseBody
    """The response body."""


# "type": "twapOrder"


class TwapWire(TypedDict):
    """A wire representation of a twap order."""

    a: int
    """The asset ID."""
    b: bool
    """Whether this is a buy order."""
    s: str
    """The size of the TWAP order."""
    r: bool
    """Whether this is a reduce-only order."""
    m: int
    """The duration in minutes."""
    t: bool
    """Whether the TWAP order is randomized."""


class TwapOrderAction(TypedDict):
    """An action to place a TWAP order."""

    type: Literal["twapOrder"]
    """The action type."""
    twap: TwapWire
    """The TWAP order details."""


class TwapOrderRequest(TypedDict):
    """A request to place a TWAP order."""

    action: TwapOrderAction
    """The TWAP order action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class TwapOrderDataStatusRunningData(TypedDict):
    """A twap id of in response to placing a TWAP order."""

    twapId: int
    """The TWAP order ID."""


class TwapOrderDataStatusRunning(TypedDict):
    """A running status in response to placing a TWAP order."""

    running: TwapOrderDataStatusRunningData
    """The running status data."""


class TwapOrderDataStatusError(TypedDict):
    """A error status in response to placing a TWAP order."""

    error: str
    """The error message."""


class TwapOrderData(TypedDict):
    """A status in response to placing a TWAP order."""

    status: TwapOrderDataStatusRunning | TwapOrderDataStatusError
    """The status of the TWAP order."""


class TwapOrderResponseBody(TypedDict):
    """A body of response to a request to place a TWAP order."""

    type: Literal["twapOrder"]
    """The response type."""
    data: TwapOrderData
    """The TWAP order data."""


class TwapOrderResponse(TypedDict):
    """A response to a request to place a TWAP order."""

    status: Literal["ok"]
    """The response status."""
    response: TwapOrderResponseBody
    """The response body."""


# "type": "twapCancel"


class TwapCancelAction(TypedDict):
    """An action to cancel a TWAP order."""

    type: Literal["twapCancel"]
    """The action type."""
    a: int
    """The asset ID."""
    t: int
    """The TWAP order ID."""


class TwapCancelRequest(TypedDict):
    """A request to cancel a TWAP order."""

    action: TwapCancelAction
    """The cancel action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class TwapCancelResponseDataErrorDetail(TypedDict):
    """A error status' details in response to canceling a TWAP order."""

    error: str
    """The error message."""


class TwapCancelResponseDataError(TypedDict):
    """A error status in response to canceling a TWAP order."""

    status: TwapCancelResponseDataErrorDetail
    """The error details."""


class TwapCancelResponseDataSuccess(TypedDict):
    """A success status in response to canceling a TWAP order."""

    status: Literal["success"]
    """The success status."""


class TwapCancelResponseBody(TypedDict):
    """A body of response to a request to cancel a TWAP order."""

    type: Literal["twapCancel"]
    """The response type."""
    data: TwapCancelResponseDataSuccess
    """The cancel response data."""


class TwapCancelResponse(TypedDict):
    """A response to a request to cancel a TWAP order."""

    status: Literal["ok"]
    """The response status."""
    response: TwapCancelResponseBody
    """The response body."""


# "type": "reserveRequestWeight"


class ReserveRequestWeightAction(TypedDict):
    """An action to reserve additional request weight."""

    type: Literal["reserveRequestWeight"]
    """The action type."""
    weight: int
    """The amount of request weight to reserve."""


class ReserveRequestWeightRequest(TypedDict):
    """A request to reserve additional request weight."""

    action: ReserveRequestWeightAction
    """The reserve request weight action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class ReserveRequestWeightResponseBody(TypedDict):
    """A body of response to a request to reserve additional request weight."""

    type: Literal["default"]
    """The response type."""


class ReserveRequestWeightResponse(TypedDict):
    """A response to a request to reserve additional request weight."""

    status: Literal["ok"]
    """The response status."""
    response: ReserveRequestWeightResponseBody
    """The response body."""


# "type": "setReferrer"


class SetReferrerAction(TypedDict):
    """An action to set a referrer."""

    type: Literal["setReferrer"]
    """The action type."""
    code: str
    """The referrer code."""


class SetReferrerRequest(TypedDict):
    """A request to set a referrer."""

    action: SetReferrerAction
    """The set referrer action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class SetReferrerResponse(TypedDict):
    """A response from the exchange after setting a referrer."""

    # TODO: Not documented in docs
    todo: str
    """Placeholder field - not documented in API docs."""


# "type": "createVault"


class CreateVaultAction(TypedDict):
    """An action to create a vault."""

    type: Literal["createVault"]
    """The action type."""
    name: str
    """The name of the vault."""
    description: str
    """The description of the vault."""
    initialUsd: int
    """The initial USD amount for the vault."""
    nonce: int
    """The nonce for the action."""


class CreateVaultRequest(TypedDict):
    """A request to create a vault."""

    action: CreateVaultAction
    """The create vault action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class CreateVaultResponseBody(TypedDict):
    """The body of a response from the exchange after creating a vault."""

    type: Literal["createVault"]
    """The response type."""
    data: str  # Vault address
    """The vault address."""


class CreateVaultResponse(TypedDict):
    """A response from the exchange after creating a vault."""

    status: Literal["ok"]
    """The response status."""
    response: CreateVaultResponseBody
    """The response body."""


# "type": "createSubAccount"


class CreateSubAccountAction(TypedDict):
    """An action to create a subaccount."""

    type: Literal["createSubAccount"]
    """The action type."""
    name: str
    """The name of the subaccount."""


class CreateSubAccountRequest(TypedDict):
    """A request to create a subaccount."""

    action: CreateSubAccountAction
    """The create subaccount action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class CreateSubAccountResponseBody(TypedDict):
    """The body of a response from the exchange after creating a subaccount."""

    type: Literal["createSubAccount"]
    """The response type."""
    data: str
    """The subaccount user address."""


class CreateSubAccountResponse(TypedDict):
    """A response from the exchange after creating a subaccount."""

    status: Literal["ok"]
    """The response status."""
    response: CreateSubAccountResponseBody
    """The response body."""


# "type": "registerReferrer"


class RegisterReferrerAction(TypedDict):
    """An action to register a referrer."""

    type: Literal["registerReferrer"]
    """The action type."""
    code: str
    """The referrer code."""


class RegisterReferrerRequest(TypedDict):
    """A request to register a referrer."""

    action: RegisterReferrerAction
    """The register referrer action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class RegisterReferrerResponseBody(TypedDict):
    """The body of a response from the exchange after registering a referrer."""

    type: Literal["default"]
    """The response type."""


class RegisterReferrerResponse(TypedDict):
    """A response from the exchange after registering a referrer."""

    status: Literal["ok"]
    """The response status."""
    response: RegisterReferrerResponseBody
    """The response body."""


# "type": "subAccountTransfer"


class SubAccountTransferAction(TypedDict):
    """An action to transfer USDC between a user's main account and a subaccount."""

    type: Literal["subAccountTransfer"]
    """The action type."""
    subAccountUser: str
    """The subaccount user address."""
    isDeposit: bool
    """Whether this is a deposit to the subaccount."""
    # TODO: Do we have to multiply by 10^6?
    usd: str
    """The USD amount to transfer."""


class SubAccountTransferRequest(TypedDict):
    """A request to transfer USDC between a user's main account and a subaccount."""

    action: SubAccountTransferAction
    """The subaccount transfer action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class SubAccountTransferResponse(TypedDict):
    """A response from the exchange after transferring USDC between a user's main account and a subaccount."""

    # TODO: Not documented in docs
    todo: str
    """Placeholder field - not documented in API docs."""


# "type": "convertToMultiSigUser"


class Signers(TypedDict):
    """Signers of a multi-sig."""

    authorizedUsers: list[str]
    """The addresses of the authorized users. NOTE: Must be sorted."""
    threshold: int
    """The number of signatures required to authorize a transaction."""


class ConvertToMultiSigUserAction(TypedDict):
    """An action to convert an address to a multi-sig address."""

    type: Literal["convertToMultiSigUser"]
    """The action type."""
    signers: str
    """JSON dump of :obj:`Signers` (i.e. `signers=json.dumps(signers)`)."""
    nonce: int
    """The nonce for the action."""


class ConvertToMultiSigUserRequest(TypedDict):
    """A request to convert an address to a multi-sig address."""

    action: ConvertToMultiSigUserAction
    """The convert to multi-sig action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class ConvertToMultiSigUserResponse(TypedDict):
    """A response from the exchange after converting an address to a multi-sig address."""

    # TODO: Not documented in docs
    todo: FIXME
    """Placeholder field - not documented in API docs."""


# "type": "multiSig"


class MultiSigActionPayload(TypedDict):
    """The payload of a multi-sig action."""

    multiSigUser: str
    """The multi-sig user address."""
    outerSigner: str
    """The outer signer address."""
    action: "Action"
    """The action to be performed."""


class MultiSigAction(TypedDict):
    """An action to perform a multi-sig transaction."""

    type: Literal["multiSig"]
    """The action type."""
    # TODO: signatureChainId: int
    signatures: list[Signature]
    """The list of signatures."""
    payload: MultiSigActionPayload
    """The multi-sig action payload."""


class MultiSigRequest(TypedDict):
    """A request to perform a multi-sig transaction."""

    action: MultiSigAction
    """The multi-sig action."""
    nonce: int
    """The nonce for the request."""
    signature: Signature
    """The signature for the request."""


class MultiSigResponse(TypedDict):
    """A response from the exchange after performing a multi-sig transaction."""

    # TODO: Not documented in docs
    todo: FIXME
    """Placeholder field - not documented in API docs."""


# General

Action: TypeAlias = (
    OrderAction
    | ModifyAction
    | BatchModifyAction
    | CancelAction
    | CancelByCloidAction
    | ScheduleCancelAction
    | UpdateLeverageAction
    | UpdateIsolatedMarginAction
    | TopUpIsolatedOnlyMarginAction
    | TwapOrderAction
    | TwapCancelAction
    # User actions
    | UsdSendAction
    | SpotSendAction
    | WithdrawAction
    | UsdClassTransferAction
    | PerpDexClassTransferAction
    | VaultTransferAction
    | ApproveAgentAction
    | ApproveBuilderFeeAction
    | DepositStakingAction
    | WithdrawStakingAction
    | TokenDelegateAction
    # Other
    | ReserveRequestWeightAction
    | SetReferrerAction
    | CreateVaultAction
    | CreateSubAccountAction
    | RegisterReferrerAction
    | SubAccountTransferAction
    | ConvertToMultiSigUserAction
    | MultiSigAction
)
"""A union of all possible actions that can be performed on the exchange."""

ExchangeRequest = (
    OrderRequest
    | CancelRequest
    | CancelByCloidRequest
    | ScheduleCancelRequest
    | ModifyRequest
    | BatchModifyRequest
    | UpdateLeverageRequest
    | UpdateIsolatedMarginRequest
    | TopUpIsolatedOnlyMarginRequest
    | TwapOrderRequest
    | TwapCancelRequest
    # User action requests
    | UsdSendRequest
    | SpotSendRequest
    | WithdrawRequest
    | UsdClassTransferRequest
    | PerpDexClassTransferRequest
    | VaultTransferRequest
    | ApproveAgentRequest
    | ApproveBuilderFeeRequest
    | DepositStakingRequest
    | WithdrawStakingRequest
    | TokenDelegateRequest
    # Other
    | ReserveRequestWeightRequest
    | SetReferrerRequest
    | CreateVaultRequest
    | CreateSubAccountRequest
    | SubAccountTransferRequest
    | ConvertToMultiSigUserRequest
    | MultiSigRequest
)
"""A union of all possible requests that can be sent to the exchange API."""

ExchangeResponse = (
    OrderResponse
    | CancelResponse
    | CancelByCloidResponse
    | ScheduleCancelResponse
    | ModifyResponse
    | BatchModifyResponse
    | UpdateLeverageResponse
    | UpdateIsolatedMarginResponse
    | TopUpIsolatedOnlyMarginResponse
    | TwapOrderResponse
    | TwapCancelResponse
    # User action responses
    | UsdSendResponse
    | SpotSendResponse
    | WithdrawResponse
    | UsdClassTransferResponse
    | PerpDexClassTransferResponse
    | VaultTransferResponse
    | ApproveAgentResponse
    | ApproveBuilderFeeResponse
    | DepositStakingResponse
    | WithdrawStakingResponse
    | TokenDelegateResponse
    # Other
    | ReserveRequestWeightResponse
    | SetReferrerResponse
    | CreateVaultResponse
    | CreateSubAccountResponse
    | SubAccountTransferResponse
    | ConvertToMultiSigUserResponse
    | MultiSigResponse
)
"""A union of all possible responses that can be returned from the exchange API."""

#######################
# WEBSOCKET API TYPES #
#######################
# method: "ping"


class Ping(TypedDict):
    """A request to ping the exchange."""

    method: Literal["ping"]
    """The method set to `ping`."""


class PongMsg(TypedDict):
    """A message from the exchange indicating a ping was received. Response to a :obj:`Ping`."""

    channel: Literal["pong"]
    """The channel of the message set to `pong`."""


# method: "subscribe" / "unsubscribe"

## type: "allMids"


class AllMidsSubscription(TypedDict):
    """Subscribe to all mids."""

    type: Literal["allMids"]
    """The subscription type."""


class AllMidsData(TypedDict):
    """The payload of a message from the exchange containing all mids."""

    # NOTE: This is different from the /info response since it doesn't have an intermediary "mids" key
    mids: AllMids
    """The mids data mapping asset names to prices."""


class AllMidsMsg(TypedDict):
    """A message from the exchange containing all mids. Response to an :obj:`AllMidsSubscription`."""

    channel: Literal["allMids"]
    """The channel of the message set to `allMids`."""
    data: AllMidsData
    """The all mids data."""


## type: "notification"


class NotificationSubscription(TypedDict):
    """Subscribe to notifications."""

    type: Literal["notification"]
    """The subscription type."""
    user: str
    """The user address to subscribe to."""


# TODO: This has not been validated against prod
class Notification(TypedDict):
    """A notification."""

    notification: str
    """The notification message."""


class NotificationMsg(TypedDict):
    """A message from the exchange containing a notification. Response to a :obj:`NotificationSubscription`."""

    channel: Literal["notification"]
    """The channel of the message set to `notification`."""
    data: Notification
    """The notification data."""


## type: "webData2"


class WebData2Subscription(TypedDict):
    """Subscribe to web data 2."""

    type: Literal["webData2"]
    """The subscription type."""
    user: str
    """The user address to subscribe to."""


class WsSpotAssetCtx(SpotAssetCtx):
    """Spot asset context with additional fields only present in the WebSocket version."""

    totalSupply: str
    """The total supply of the asset."""
    dayBaseVlm: str
    """The day base volume of the asset."""


class WebData2Data(TypedDict):
    """The payload of a message from the exchange containing web data 2."""

    clearingHouseState: UserState
    """The user's clearing house state containing positions and margin info."""
    leadingVaults: list[FIXME]
    """List of leading vaults."""
    totalVaultEquity: str
    """The total vault equity."""
    openOrders: list[FIXME]
    """List of open orders."""
    agentAddress: str
    """The agent address."""
    agentValidUntil: int
    """The timestamp until which the agent is valid."""
    cumLedger: str
    """The cumulative ledger value."""
    meta: Meta
    """The perpetual metadata."""
    assetCtxs: list[AssetCtx]
    """List of asset contexts for perpetual assets."""
    serverTime: int
    """The server timestamp."""
    isVault: bool
    """Whether the user is a vault."""
    user: str
    """The user address."""
    twapStates: list[FIXME]
    """List of TWAP states."""
    spotState: SpotUserState
    """The user's spot state."""
    spotAssetCtxs: list[SpotAssetCtx]
    """List of spot asset contexts."""


class WebData2Msg(TypedDict):
    """A message from the exchange containing web data 2. Response to a :obj:`WebData2Subscription`."""

    channel: Literal["webData2"]
    """The channel of the message set to `webData2`."""
    data: WebData2Data
    """The web data 2 payload."""


## type: "candle"


class CandleSubscription(TypedDict):
    """Subscribe to candles."""

    type: Literal["candle"]
    """The subscription type."""
    coin: str
    """The asset to subscribe to."""
    interval: CandleInterval
    """The candle interval."""


class CandleMsg(TypedDict):
    """A message from the exchange containing a candle. Response to a :obj:`CandleSubscription`."""

    channel: Literal["candle"]
    """The channel of the message set to `candle`."""
    data: Candle
    """The candle data."""


## type: "l2Book"


class L2BookSubscription(TypedDict):
    """Subscribe to the L2 book."""

    type: Literal["l2Book"]
    """The subscription type."""
    coin: str
    """The asset to subscribe to."""
    nSigFigs: NotRequired[int]
    """The number of significant figures to use for the L2 book."""
    mantissa: NotRequired[int]
    """The mantissa to use for the L2 book."""


class L2BookMsg(TypedDict):
    """A message from the exchange containing the L2 book for a given coin. Response to an :obj:`L2BookSubscription`."""

    channel: Literal["l2Book"]
    """The channel of the message set to `l2Book`."""
    data: L2Book
    """The L2 book data."""


## type: "trades"


class TradesSubscription(TypedDict):
    """Subscribe to trades."""

    type: Literal["trades"]
    """The subscription type."""
    coin: str
    """The asset to subscribe to."""


class Trade(TypedDict):
    """A trade."""

    coin: str
    """The asset of the trade."""
    hash: str
    """The hash of the trade."""
    px: str
    """The price of the trade."""
    side: Side
    """The side of the trade."""
    sz: str
    """The size of the trade."""
    tid: int
    """The trade ID."""
    time: int
    """The timestamp of the trade."""
    # NOTE: Technically a list since parsed from JSON. Typed as tuple for convenience.
    users: tuple[str, str]
    """The users involved in the trade (buyer and seller addresses)."""


class TradesMsg(TypedDict):
    """A message from the exchange containing trades. Response to a :obj:`TradesSubscription`."""

    channel: Literal["trades"]
    """The channel of the message set to `trades`."""
    data: list[Trade]
    """List of trades."""


## type: "orderUpdates"


class OrderUpdatesSubscription(TypedDict):
    """Subscribe to order updates."""

    type: Literal["orderUpdates"]
    """The subscription type."""
    user: str
    """The user address to subscribe to."""


class OrderUpdate(TypedDict):
    """A single order update."""

    # NOTE: This type is similar to OrderStatus but the order field only contains the OpenOrder subset of fields.
    order: OpenOrder
    """The order data."""
    status: OrderStatusValue
    """The status of the order."""
    statusTimestamp: int
    """The timestamp of the status change."""


class OrderUpdatesMsg(TypedDict):
    """A message from the exchange containing order updates. Response to an :obj:`OrderUpdatesSubscription`."""

    channel: Literal["orderUpdates"]
    """The channel of the message set to `orderUpdates`."""
    data: list[OrderUpdate]
    """List of order updates."""


## type: "userEvents"


class UserEventsSubscription(TypedDict):
    """Subscribe to user events."""

    type: Literal["userEvents"]
    """The subscription type."""
    user: str
    """The user address to subscribe to."""


class UserFillsEvent(TypedDict):
    """The payload of a message from the exchange containing user fills. Response to a :obj:`UserFillsSubscription`."""

    fills: list[UserFill]
    """List of user fills."""


class UserFundingData(TypedDict):
    """A user funding."""

    # TODO: Is this the same as UserFundingDelta?
    todo: FIXME


class UserFundingEvent(TypedDict):
    """The payload of a message from the exchange containing a user funding. Response to a :obj:`UserFundingsSubscription`."""

    funding: UserFundingData
    """The user funding data."""


class UserLiquidation(TypedDict):
    """A user liquidation."""

    # TODO: Validate in prod
    lid: int
    """The liquidation ID."""
    liquidator: str
    """The liquidator address."""
    liquidated_user: str
    """The liquidated user address."""
    liquidated_ntl_pos: str
    """The liquidated notional position."""
    liquidated_account_value: str
    """The liquidated account value."""


class UserLiquidationEvent(TypedDict):
    """The payload of a message from the exchange containing a user liquidation. Response to a :obj:`UserLiquidationsSubscription`."""

    liquidation: UserLiquidation
    """The user liquidation data."""


class NonUserCancel(TypedDict):
    """A non-user cancel."""

    # TODO: Validate in prod
    coin: str
    """The asset of the cancelled order."""
    oid: int
    """The order ID that was cancelled."""


class NonUserCancelEvent(TypedDict):
    """The payload of a message from the exchange containing a non-user cancel. Response to a :obj:`NonUserCancelsSubscription`."""

    nonUserCancel: list[NonUserCancel]
    """List of non-user cancels."""


UserEvent = (
    UserFillsEvent | UserFundingEvent | UserLiquidationEvent | NonUserCancelEvent
)
"""A union of all possible user events that can be received via WebSocket."""


class UserEventsMsg(TypedDict):
    """A message from the exchange containing user events. Response to a :obj:`UserEventsSubscription`."""

    channel: Literal["user"]
    """The channel of the message set to `user`."""
    data: UserEvent
    """The user event data."""


## type: "userFills"


class UserFillsSubscription(TypedDict):
    """Subscribe to user fills."""

    type: Literal["userFills"]
    """The subscription type."""
    user: str
    """The user address to subscribe to."""
    aggregateByTime: NotRequired[bool]
    """Whether to aggregate fills by time."""


class UserFillsData(TypedDict):
    """The payload of a message from the exchange containing user fills. Response to a :obj:`UserFillsSubscription`."""

    # isSnapshot is only present in the first message received after subscribing where it is always True
    isSnapshot: NotRequired[bool]
    """Whether this is a snapshot message (only present in the first message)."""
    user: str
    """The user address."""
    fills: list[UserFill]
    """List of user fills."""


class UserFillsMsg(TypedDict):
    """A message from the exchange containing user fills. Response to a :obj:`UserFillsSubscription`."""

    channel: Literal["userFills"]
    """The channel of the message set to `userFills`."""
    data: UserFillsData
    """The user fills data."""


## type: "userFundings"


class UserFundingsSubscription(TypedDict):
    """Subscribe to user fundings."""

    type: Literal["userFundings"]
    """The subscription type."""
    user: str
    """The user address to subscribe to."""


class WsUserFundingDelta(_UserFundingDeltaBase):
    """A user funding delta as present in the WebSocket version."""

    time: int
    """The timestamp of the funding delta."""


class UserFundingsData(TypedDict):
    """The payload of a message from the exchange containing user fundings. Response to a :obj:`UserFundingsSubscription`."""

    # isSnapshot is only present in the first message received after subscribing where it is always True
    isSnapshot: NotRequired[bool]
    """Whether this is a snapshot message (only present in the first message)."""
    user: str
    """The user address."""
    fundings: list[WsUserFundingDelta]
    """List of user funding deltas."""


class UserFundingsMsg(TypedDict):
    """A message from the exchange containing user fundings. Response to a :obj:`UserFundingsSubscription`."""

    channel: Literal["userFundings"]
    """The channel of the message set to `userFundings`."""
    data: UserFundingsData
    """The user fundings data."""


## type: "userNonFundingLedgerUpdates"


class UserNonFundingLedgerUpdatesSubscription(TypedDict):
    """Subscribe to user non-funding ledger updates."""

    type: Literal["userNonFundingLedgerUpdates"]
    """The subscription type."""
    user: str
    """The user address to subscribe to."""


class UserNonFundingLedgerUpdatesData(TypedDict):
    """The payload of a message from the exchange containing user non-funding ledger updates. Response to a :obj:`UserNonFundingLedgerUpdatesSubscription`."""

    # isSnapshot is only present in the first message received after subscribing where it is always True
    isSnapshot: NotRequired[bool]
    """Whether this is a snapshot message (only present in the first message)."""
    user: str
    """The user address."""
    nonFundingLedgerUpdates: list[UserNonFundingLedgerUpdate]
    """List of non-funding ledger updates."""


class UserNonFundingLedgerUpdatesMsg(TypedDict):
    """A message from the exchange containing user non-funding ledger updates. Response to a :obj:`UserNonFundingLedgerUpdatesSubscription`."""

    channel: Literal["userNonFundingLedgerUpdates"]
    """The channel of the message set to `userNonFundingLedgerUpdates`."""
    data: UserNonFundingLedgerUpdatesData
    """The user non-funding ledger updates data."""


## type: "activeAssetCtx"


class ActiveAssetCtxSubscription(TypedDict):
    """Subscribe to active asset context."""

    type: Literal["activeAssetCtx"]
    """The subscription type."""
    coin: str
    """The asset to subscribe to."""


class AssetCtxData(TypedDict):
    """The payload of a message from the exchange containing active asset context. Response to an :obj:`ActiveAssetCtxSubscription`."""

    coin: str
    """The asset name."""
    ctx: AssetCtx
    """The asset context information."""


class ActiveAssetCtxMsg(TypedDict):
    """A message from the exchange containing active perpetual asset context. Response to an [`ActiveAssetCtxSubscription`][hl.types.ActiveAssetCtxSubscription] ."""

    channel: Literal["activeAssetCtx"]
    """The channel of the message set to `activeAssetCtx`."""
    data: AssetCtxData
    """The payload of the message containing the active asset context."""


class ActiveSpotAssetCtxMsg(TypedDict):
    """A message from the exchange containing active spot asset context. Response to an :obj:`ActiveAssetCtxSubscription`."""

    channel: Literal["activeSpotAssetCtx"]
    """The channel of the message set to `activeSpotAssetCtx`."""
    data: SpotAssetCtx
    """The spot asset context data."""


## type: "activeAssetData"


class ActiveAssetDataSubscription(TypedDict):
    """Subscribe to active asset data.

    Note: Only supports perpetual assets.
    """

    type: Literal["activeAssetData"]
    """The subscription type."""
    user: str
    """The user address to subscribe to."""
    coin: str
    """The asset to subscribe to."""


class ActiveAssetData(TypedDict):
    """The payload of a message from the exchange containing active asset data. Response to an :obj:`ActiveAssetDataSubscription`."""

    user: str
    """The user address."""
    coin: str
    """The asset name."""
    leverage: Leverage
    """The leverage information for the asset."""
    maxTradeSzs: tuple[str, str]
    """The maximum trade sizes for buy and sell orders."""
    availableToTrade: tuple[str, str]
    """The available amounts to trade for buy and sell orders."""


class ActiveAssetDataMsg(TypedDict):
    """A message from the exchange containing active asset data. Response to an :obj:`ActiveAssetDataSubscription`."""

    channel: Literal["activeAssetData"]
    """The channel of the message set to `activeAssetData`."""
    data: ActiveAssetData
    """The active asset data."""


## type: "userTwapSliceFills"


class UserTwapSliceFillsSubscription(TypedDict):
    """Subscribe to user TWAP slice fills."""

    type: Literal["userTwapSliceFills"]
    """The subscription type."""
    user: str
    """The user address to subscribe to."""


class UserTwapSliceFillsData(TypedDict):
    """The payload of a message from the exchange containing user TWAP slice fills. Response to an :obj:`UserTwapSliceFillsSubscription`."""

    isSnapshot: NotRequired[bool]
    """Whether this is a snapshot message (only present in the first message)."""
    user: str
    """The user address."""
    twapSliceFills: list[UserTwapSliceFill]
    """List of TWAP slice fills."""


class UserTwapSliceFillsMsg(TypedDict):
    """A message from the exchange containing user TWAP slice fills. Response to an :obj:`UserTwapSliceFillsSubscription`."""

    channel: Literal["userTwapSliceFills"]
    """The channel of the message set to `userTwapSliceFills`."""
    data: UserTwapSliceFillsData
    """The user TWAP slice fills data."""


## type: "userTwapHistory"


class UserTwapHistorySubscription(TypedDict):
    """Subscribe to user TWAP history."""

    type: Literal["userTwapHistory"]
    """The subscription type."""
    user: str
    """The user address to subscribe to."""


class TwapState(TypedDict):
    """A user TWAP state."""

    coin: str
    """The asset for the TWAP order."""
    user: str
    """The user address."""
    side: str
    """The side of the TWAP order."""
    sz: float
    """The size of the TWAP order."""
    executedSz: float
    """The executed size of the TWAP order."""
    executedNtl: float
    """The executed notional value of the TWAP order."""
    minutes: int
    """The duration of the TWAP order in minutes."""
    reduceOnly: bool
    """Whether the TWAP order is reduce-only."""
    randomize: bool
    """Whether the TWAP order is randomized."""
    timestamp: int
    """The timestamp when the TWAP order was created."""


class TwapStatus(TypedDict):
    """A user TWAP status."""

    status: Literal["activated", "terminated", "finished", "error"]
    """The status of the TWAP order."""
    description: str
    """The description of the TWAP status."""


class UserTwapHistoryItem(TypedDict):
    """A user TWAP history item."""

    state: TwapState
    """The state of the TWAP order."""
    status: TwapStatus
    """The status of the TWAP order."""
    time: int
    """The timestamp of the TWAP history item."""


class UserTwapHistoryData(TypedDict):
    """The payload of a message from the exchange containing user TWAP history. Response to an :obj:`UserTwapHistorySubscription`."""

    isSnapshot: NotRequired[bool]
    """Whether this is a snapshot message (only present in the first message)."""
    user: str
    """The user address."""
    history: list[UserTwapHistoryItem]
    """List of TWAP history items."""


class UserTwapHistoryMsg(TypedDict):
    """A message from the exchange containing user TWAP history. Response to an :obj:`UserTwapHistorySubscription`."""

    channel: Literal["userTwapHistory"]
    """The channel of the message set to `userTwapHistory`."""
    data: UserTwapHistoryData
    """The user TWAP history data."""


## type: "bbo"


class BestBidOfferSubscription(TypedDict):
    """Subscribe to best bid offer data."""

    type: Literal["bbo"]
    """The subscription type."""
    coin: str
    """The asset to subscribe to."""


class BestBidOfferData(TypedDict):
    """The payload of a message from the exchange containing best bid offer data. Response to an :obj:`BestBidOfferSubscription`."""

    coin: str
    """The asset for the best bid offer data."""
    time: int
    """The timestamp of the best bid offer data."""
    bbo: list[L2Level | None]
    """The best bid offer levels."""


class BestBidOfferMsg(TypedDict):
    """A message from the exchange containing best bid offer data. Response to an :obj:`BestBidOfferSubscription`."""

    channel: Literal["bbo"]
    """The channel of the message set to `bbo`."""
    data: BestBidOfferData
    """The best bid offer data."""


## General

Subscription: TypeAlias = (
    AllMidsSubscription
    | NotificationSubscription
    | WebData2Subscription
    | CandleSubscription
    | L2BookSubscription
    | TradesSubscription
    | OrderUpdatesSubscription
    | UserEventsSubscription
    | UserFillsSubscription
    | UserFundingsSubscription
    | UserNonFundingLedgerUpdatesSubscription
    | ActiveAssetCtxSubscription
    | ActiveAssetDataSubscription
    | UserTwapSliceFillsSubscription
    | UserTwapHistorySubscription
    | BestBidOfferSubscription
)
"""A union of all possible WebSocket subscription types."""


class Subscribe(TypedDict):
    """A request to subscribe to a specific data feed."""

    method: Literal["subscribe"]
    """The method set to `subscribe`."""
    subscription: Subscription
    """The subscription details."""


class Unsubscribe(TypedDict):
    """A request to unsubscribe from a specific data feed."""

    method: Literal["unsubscribe"]
    """The method set to `unsubscribe`."""
    subscription: Subscription
    """The subscription details."""


class SubscriptionResponseMsg(TypedDict):
    """The response from the exchange after subscribing to a data feed."""

    channel: Literal["subscriptionResponse"]
    """The channel of the message set to `subscriptionResponse`."""
    data: Subscribe | Unsubscribe
    """The subscription or unsubscription request data."""


# method: "post"


class PostRequestInfo(TypedDict):
    """A request to send to the websocket API via the `post` method to the /info endpoint."""

    type: Literal["info"]
    """The request type."""
    payload: InfoRequest
    """The info request payload."""


class PostRequestExchange(TypedDict):
    """A request to send to the websocket API via the `post` method to the /exchange endpoint."""

    type: Literal["exchange"]
    """The request type."""
    payload: ExchangeRequest
    """The exchange request payload."""


class PostRequest(TypedDict):
    """A request to send to the websocket API via the `post` method."""

    method: Literal["post"]
    """The method set to `post`."""
    id: int
    """The request ID."""
    request: PostRequestInfo | PostRequestExchange
    """The request details."""


class PostResponseInfo(TypedDict):
    """The value of a response from the exchange after sending a /info :obj:`PostRequest`."""

    type: Literal["info"]
    """The response type."""
    payload: InfoResponse
    """The info response payload."""


class PostResponseExchange(TypedDict):
    """The value of a response from the exchange after sending a /exchange :obj:`PostRequest`."""

    type: Literal["exchange"]
    """The response type."""
    payload: ExchangeResponse
    """The exchange response payload."""


class PostData(TypedDict):
    """The data of a response from the exchange after sending a :obj:`PostRequest`."""

    id: int
    """The request ID."""
    response: PostResponseInfo | PostResponseExchange
    """The response data."""


class PostMsg(TypedDict):
    """A message from the exchange containing the response to a :obj:`PostRequest`."""

    channel: Literal["post"]
    """The channel of the message set to `post`."""
    data: PostData
    """The post response data."""


# General

Msg = (
    PongMsg
    | SubscriptionResponseMsg
    | AllMidsMsg
    | NotificationMsg
    | WebData2Msg
    | CandleMsg
    | L2BookMsg
    | TradesMsg
    | OrderUpdatesMsg
    | UserEventsMsg
    | UserFillsMsg
    | UserFundingsMsg
    | UserNonFundingLedgerUpdatesMsg
    | ActiveAssetCtxMsg
    | ActiveSpotAssetCtxMsg
    | ActiveAssetDataMsg
    | UserTwapSliceFillsMsg
    | UserTwapHistoryMsg
    | BestBidOfferMsg
    | PostMsg
)
"""A union of all possible messages that can be received via WebSocket."""
