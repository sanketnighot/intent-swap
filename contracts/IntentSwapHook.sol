// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {BaseHook} from "@uniswap/v4-periphery/src/base/hooks/BaseHook.sol";
import {Hooks} from "@uniswap/v4-core/src/libraries/Hooks.sol";
import {StateLibrary} from "@uniswap/v4-core/src/libraries/StateLibrary.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "@uniswap/v4-core/src/types/PoolId.sol";
import {BeforeSwapDelta} from "@uniswap/v4-core/src/types/BeforeSwapDelta.sol";

contract IntentSwapHook is BaseHook {
    using PoolIdLibrary for PoolKey;
    using StateLibrary for IPoolManager;

    enum ConditionType {
        TARGET_SQRT_PRICE_X96,
        MAX_SLIPPAGE_BPS
    }

    struct Intent {
        address user;
        address tokenIn;
        address tokenOut;
        uint256 amountIn;
        ConditionType conditionType;
        uint160 conditionValue;
        uint64 expiry;
        bool executed;
        PoolId poolId;
        bool zeroForOne;
        uint160 referenceSqrtPriceX96;
    }

    error IntentNotFound();
    error InvalidExpiry();
    error InvalidAmount();
    error InvalidCondition();
    error InvalidHookData();
    error IntentExpired();
    error IntentAlreadyExecuted();
    error PoolMismatch();
    error DirectionMismatch();
    error AmountMismatch();
    error TokenMismatch();
    error PriceConditionNotMet();

    uint256 public intentCount;
    mapping(uint256 => Intent) private intents;

    event IntentCreated(
        uint256 indexed intentId,
        address indexed user,
        address indexed tokenIn,
        address tokenOut,
        uint256 amountIn,
        ConditionType conditionType,
        uint160 conditionValue,
        uint64 expiry
    );

    event IntentExecuted(uint256 indexed intentId, address indexed executor);

    constructor(IPoolManager _poolManager) BaseHook(_poolManager) {}

    function getHookPermissions() public pure override returns (Hooks.Permissions memory permissions) {
        permissions.beforeSwap = true;
    }

    function submitIntent(
        PoolKey calldata key,
        bool zeroForOne,
        uint256 amountIn,
        ConditionType conditionType,
        uint160 conditionValue,
        uint64 expiry
    ) external returns (uint256 intentId) {
        if (amountIn == 0) revert InvalidAmount();
        if (expiry <= block.timestamp) revert InvalidExpiry();
        if (conditionType == ConditionType.MAX_SLIPPAGE_BPS && conditionValue > 10_000) revert InvalidCondition();

        PoolId poolId = key.toId();
        uint160 referenceSqrtPriceX96 = _readSqrtPriceX96(poolId);
        address tokenIn = Currency.unwrap(zeroForOne ? key.currency0 : key.currency1);
        address tokenOut = Currency.unwrap(zeroForOne ? key.currency1 : key.currency0);

        intentId = intentCount;
        intentCount = intentId + 1;

        intents[intentId] = Intent({
            user: msg.sender,
            tokenIn: tokenIn,
            tokenOut: tokenOut,
            amountIn: amountIn,
            conditionType: conditionType,
            conditionValue: conditionValue,
            expiry: expiry,
            executed: false,
            poolId: poolId,
            zeroForOne: zeroForOne,
            referenceSqrtPriceX96: referenceSqrtPriceX96
        });

        emit IntentCreated(intentId, msg.sender, tokenIn, tokenOut, amountIn, conditionType, conditionValue, expiry);
    }

    function getIntent(uint256 intentId) external view returns (Intent memory) {
        Intent memory intent = intents[intentId];
        if (intent.user == address(0)) revert IntentNotFound();
        return intent;
    }

    function canExecuteIntent(
        uint256 intentId,
        PoolKey calldata key,
        IPoolManager.SwapParams calldata params
    ) external view returns (bool) {
        Intent memory intent = intents[intentId];

        if (intent.user == address(0)) return false;
        if (intent.executed) return false;
        if (block.timestamp > intent.expiry) return false;
        if (PoolId.unwrap(key.toId()) != PoolId.unwrap(intent.poolId)) return false;
        if (params.zeroForOne != intent.zeroForOne) return false;
        if (params.amountSpecified <= 0) return false;
        if (uint256(params.amountSpecified) != intent.amountIn) return false;

        address swapTokenIn = Currency.unwrap(params.zeroForOne ? key.currency0 : key.currency1);
        address swapTokenOut = Currency.unwrap(params.zeroForOne ? key.currency1 : key.currency0);
        if (swapTokenIn != intent.tokenIn || swapTokenOut != intent.tokenOut) return false;

        uint160 currentSqrtPriceX96 = _readSqrtPriceX96(intent.poolId);
        return _meetsPriceCondition(intent, currentSqrtPriceX96);
    }

    function _beforeSwap(
        address sender,
        PoolKey calldata key,
        IPoolManager.SwapParams calldata params,
        bytes calldata hookData
    ) internal override returns (bytes4, BeforeSwapDelta, uint24) {
        if (hookData.length != 32) revert InvalidHookData();

        uint256 intentId = abi.decode(hookData, (uint256));
        _validateIntent(intentId, key, params);

        intents[intentId].executed = true;
        emit IntentExecuted(intentId, sender);

        return (BaseHook.beforeSwap.selector, BeforeSwapDelta.wrap(0), 0);
    }

    function _validateIntent(uint256 intentId, PoolKey calldata key, IPoolManager.SwapParams calldata params) internal view {
        Intent memory intent = intents[intentId];

        if (intent.user == address(0)) revert IntentNotFound();
        if (intent.executed) revert IntentAlreadyExecuted();
        if (block.timestamp > intent.expiry) revert IntentExpired();
        if (PoolId.unwrap(key.toId()) != PoolId.unwrap(intent.poolId)) revert PoolMismatch();
        if (params.zeroForOne != intent.zeroForOne) revert DirectionMismatch();
        if (params.amountSpecified <= 0 || uint256(params.amountSpecified) != intent.amountIn) revert AmountMismatch();

        address swapTokenIn = Currency.unwrap(params.zeroForOne ? key.currency0 : key.currency1);
        address swapTokenOut = Currency.unwrap(params.zeroForOne ? key.currency1 : key.currency0);
        if (swapTokenIn != intent.tokenIn || swapTokenOut != intent.tokenOut) revert TokenMismatch();

        uint160 currentSqrtPriceX96 = _readSqrtPriceX96(intent.poolId);
        if (!_meetsPriceCondition(intent, currentSqrtPriceX96)) revert PriceConditionNotMet();
    }

    function _meetsPriceCondition(Intent memory intent, uint160 currentSqrtPriceX96) internal pure returns (bool) {
        if (intent.conditionType == ConditionType.TARGET_SQRT_PRICE_X96) {
            if (intent.zeroForOne) {
                return currentSqrtPriceX96 >= intent.conditionValue;
            }
            return currentSqrtPriceX96 <= intent.conditionValue;
        }

        if (intent.referenceSqrtPriceX96 == 0) return false;
        uint256 reference = uint256(intent.referenceSqrtPriceX96);
        uint256 current = uint256(currentSqrtPriceX96);
        uint256 delta = reference > current ? reference - current : current - reference;
        uint256 slippageBps = (delta * 10_000) / reference;

        return slippageBps <= uint256(intent.conditionValue);
    }

    function _readSqrtPriceX96(PoolId poolId) internal view returns (uint160 sqrtPriceX96) {
        (sqrtPriceX96,,,) = poolManager.getSlot0(poolId);
    }
}
