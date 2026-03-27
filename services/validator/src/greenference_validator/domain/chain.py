"""Bittensor chain client — metagraph sync, hotkey validation, set_weights."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from greenference_protocol import ChainWeightCommit, MetagraphEntry

logger = logging.getLogger(__name__)


class BittensorChainClient:
    """Wraps substrate-interface calls to the Bittensor chain."""

    def __init__(
        self,
        network: str = "test",
        netuid: int = 16,
        wallet_path: str | None = None,
    ) -> None:
        self.network = network
        self.netuid = netuid
        self.wallet_path = wallet_path
        self._substrate = None

    def _get_substrate(self):
        if self._substrate is not None:
            return self._substrate
        try:
            from substrateinterface import SubstrateInterface
        except ImportError:
            logger.error("substrate-interface not installed — chain calls will fail")
            raise

        endpoint = self._resolve_endpoint()
        self._substrate = SubstrateInterface(url=endpoint)
        logger.info("connected to bittensor chain at %s (netuid=%d)", endpoint, self.netuid)
        return self._substrate

    def _resolve_endpoint(self) -> str:
        endpoints = {
            "test": "wss://test.finney.opentensor.ai:443/",
            "finney": "wss://entrypoint-finney.opentensor.ai:443/",
            "local": "ws://127.0.0.1:9944",
        }
        return endpoints.get(self.network, self.network)

    def sync_metagraph(self) -> list[MetagraphEntry]:
        """Read all neurons registered on our netuid."""
        substrate = self._get_substrate()
        try:
            result = substrate.query_map(
                module="SubtensorModule",
                storage_function="Neurons",
                params=[self.netuid],
            )
        except Exception:
            logger.exception("failed to query metagraph for netuid=%d", self.netuid)
            return []

        entries: list[MetagraphEntry] = []
        for uid, neuron_data in result:
            uid_val = uid.value if hasattr(uid, "value") else int(uid)
            data = neuron_data.value if hasattr(neuron_data, "value") else neuron_data
            hotkey = data.get("hotkey", "")
            coldkey = data.get("coldkey", "")
            stake = float(data.get("stake", 0)) / 1e9  # rao to tao
            trust = float(data.get("trust", 0)) / 65535.0
            incentive = float(data.get("incentive", 0)) / 65535.0
            emission = float(data.get("emission", 0)) / 1e9

            entries.append(MetagraphEntry(
                netuid=self.netuid,
                uid=uid_val,
                hotkey=str(hotkey),
                coldkey=str(coldkey),
                stake=stake,
                trust=trust,
                incentive=incentive,
                emission=emission,
                synced_at=datetime.now(UTC),
            ))

        logger.info("synced metagraph: %d neurons on netuid=%d", len(entries), self.netuid)
        return entries

    def is_registered(self, hotkey: str) -> bool:
        """Check if a hotkey is registered on our netuid."""
        substrate = self._get_substrate()
        try:
            result = substrate.query(
                module="SubtensorModule",
                storage_function="Uids",
                params=[self.netuid, hotkey],
            )
            return result is not None and result.value is not None
        except Exception:
            logger.exception("failed to check registration for %s", hotkey)
            return False

    def set_weights(
        self,
        uids: list[int],
        weights: list[float],
        wallet_name: str = "default",
        hotkey_name: str = "default",
    ) -> ChainWeightCommit:
        """Push weight vector to chain via set_weights extrinsic."""
        substrate = self._get_substrate()

        # Normalize weights to u16 range
        total = sum(weights) or 1.0
        normalized = [int((w / total) * 65535) for w in weights]

        try:
            from substrateinterface import Keypair

            if self.wallet_path:
                keypair = Keypair.create_from_uri(self.wallet_path)
            else:
                keypair = Keypair.create_from_uri(f"//{wallet_name}//{hotkey_name}")

            call = substrate.compose_call(
                call_module="SubtensorModule",
                call_function="set_weights",
                call_params={
                    "netuid": self.netuid,
                    "dests": uids,
                    "weights": normalized,
                    "version_key": 0,
                },
            )
            extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)
            receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)

            tx_hash = receipt.extrinsic_hash if hasattr(receipt, "extrinsic_hash") else str(receipt)
            logger.info("set_weights tx submitted: %s (uids=%d)", tx_hash, len(uids))

            return ChainWeightCommit(
                netuid=self.netuid,
                tx_hash=tx_hash,
                uids=uids,
                weights=weights,
                committed_at=datetime.now(UTC),
            )

        except Exception:
            logger.exception("failed to set_weights on netuid=%d", self.netuid)
            raise
