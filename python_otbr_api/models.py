"""Data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import voluptuous as vol


@dataclass
class Timestamp:
    """Timestamp."""

    SCHEMA = vol.Schema(
        {
            vol.Optional("authoritative"): bool,
            vol.Optional("seconds"): int,
            vol.Optional("ticks"): int,
        }
    )

    authoritative: bool | None = None
    seconds: int | None = None
    ticks: int | None = None

    def as_json(self) -> dict[str, Any]:
        """Serialize to JSON."""
        result: dict[str, Any] = {}
        if self.authoritative is not None:
            result["authoritative"] = self.authoritative
        if self.seconds is not None:
            result["seconds"] = self.seconds
        if self.ticks is not None:
            result["ticks"] = self.ticks
        return result

    @classmethod
    def from_json(cls, json_data: Any) -> Timestamp:
        """Deserialize from JSON."""
        cls.SCHEMA(json_data)
        return cls(
            json_data.get("authoritative"),
            json_data.get("seconds"),
            json_data.get("ticks"),
        )


@dataclass
class SecurityPolicy:  # pylint: disable=too-many-instance-attributes
    """Security policy."""

    SCHEMA = vol.Schema(
        {
            vol.Optional("autonomousEnrollment"): bool,
            vol.Optional("commercialCommissioning"): bool,
            vol.Optional("externalCommissioning"): bool,
            vol.Optional("nativeCommissioning"): bool,
            vol.Optional("networkKeyProvisioning"): bool,
            vol.Optional("nonCcmRouters"): bool,
            vol.Optional("obtainNetworkKey"): bool,
            vol.Optional("rotationTime"): int,
            vol.Optional("routers"): bool,
            vol.Optional("tobleLink"): bool,
        }
    )

    autonomous_enrollment: bool | None = None
    commercial_commissioning: bool | None = None
    external_commissioning: bool | None = None
    native_commissioning: bool | None = None
    network_key_provisioning: bool | None = None
    non_ccm_routers: bool | None = None
    obtain_network_key: bool | None = None
    rotation_time: int | None = None
    routers: bool | None = None
    to_ble_link: bool | None = None

    def as_json(self) -> dict[str, Any]:
        """Serialize to JSON."""
        result: dict[str, Any] = {}
        if self.autonomous_enrollment is not None:
            result["autonomousEnrollment"] = self.autonomous_enrollment
        if self.commercial_commissioning is not None:
            result["commercialCommissioning"] = self.commercial_commissioning
        if self.external_commissioning is not None:
            result["externalCommissioning"] = self.external_commissioning
        if self.native_commissioning is not None:
            result["nativeCommissioning"] = self.native_commissioning
        if self.network_key_provisioning is not None:
            result["networkKeyProvisioning"] = self.network_key_provisioning
        if self.non_ccm_routers is not None:
            result["nonCcmRouters"] = self.non_ccm_routers
        if self.obtain_network_key is not None:
            result["obtainNetworkKey"] = self.obtain_network_key
        if self.rotation_time is not None:
            result["rotationTime"] = self.rotation_time
        if self.routers is not None:
            result["routers"] = self.routers
        if self.to_ble_link is not None:
            result["tobleLink"] = self.to_ble_link
        return result

    @classmethod
    def from_json(cls, json_data: Any) -> SecurityPolicy:
        """Deserialize from JSON."""
        cls.SCHEMA(json_data)
        return cls(
            json_data.get("autonomousEnrollment"),
            json_data.get("commercialCommissioning"),
            json_data.get("externalCommissioning"),
            json_data.get("nativeCommissioning"),
            json_data.get("networkKeyProvisioning"),
            json_data.get("nonCcmRouters"),
            json_data.get("obtainNetworkKey"),
            json_data.get("rotationTime"),
            json_data.get("routers"),
            json_data.get("tobleLink"),
        )


@dataclass
class ActiveDataSet:  # pylint: disable=too-many-instance-attributes
    """Operational dataset."""

    SCHEMA = vol.Schema(
        {
            vol.Optional("activeTimestamp"): dict,
            vol.Optional("channelMask"): int,
            vol.Optional("channel"): int,
            vol.Optional("extPanId"): str,
            vol.Optional("meshLocalPrefix"): str,
            vol.Optional("networkKey"): str,
            vol.Optional("networkName"): str,
            vol.Optional("panId"): int,
            vol.Optional("pskc"): str,
            vol.Optional("securityPolicy"): dict,
        }
    )

    active_timestamp: Timestamp | None = None
    channel_mask: int | None = None
    channel: int | None = None
    extended_pan_id: str | None = None
    mesh_local_prefix: str | None = None
    network_key: str | None = None
    network_name: str | None = None
    pan_id: int | None = None
    psk_c: str | None = None
    security_policy: SecurityPolicy | None = None

    def as_json(self) -> dict[str, Any]:
        """Serialize to JSON."""
        result: dict[str, Any] = {}
        if self.active_timestamp is not None:
            result["activeTimestamp"] = self.active_timestamp.as_json()
        if self.channel_mask is not None:
            result["channelMask"] = self.channel_mask
        if self.channel is not None:
            result["channel"] = self.channel
        if self.extended_pan_id is not None:
            result["extPanId"] = self.extended_pan_id
        if self.mesh_local_prefix is not None:
            result["meshLocalPrefix"] = self.mesh_local_prefix
        if self.network_key is not None:
            result["networkKey"] = self.network_key
        if self.network_name is not None:
            result["networkName"] = self.network_name
        if self.pan_id is not None:
            result["panId"] = self.pan_id
        if self.psk_c is not None:
            result["pskc"] = self.psk_c
        if self.security_policy is not None:
            result["securityPolicy"] = self.security_policy.as_json()
        return result

    @classmethod
    def from_json(cls, json_data: Any) -> ActiveDataSet:
        """Deserialize from JSON."""
        cls.SCHEMA(json_data)
        active_timestamp = None
        security_policy = None
        if "activeTimestamp" in json_data:
            active_timestamp = Timestamp.from_json(json_data["activeTimestamp"])
        if "securityPolicy" in json_data:
            security_policy = SecurityPolicy.from_json(json_data["securityPolicy"])

        return ActiveDataSet(
            active_timestamp,
            json_data.get("channelMask"),
            json_data.get("channel"),
            json_data.get("extPanId"),
            json_data.get("meshLocalPrefix"),
            json_data.get("networkKey"),
            json_data.get("networkName"),
            json_data.get("panId"),
            json_data.get("pskc"),
            security_policy,
        )


@dataclass
class PendingDataSet:  # pylint: disable=too-many-instance-attributes
    """Operational dataset."""

    SCHEMA = vol.Schema(
        {
            vol.Optional("activeDataset"): dict,
            vol.Optional("delay"): int,
            vol.Optional("pendingTimestamp"): dict,
        }
    )

    active_dataset: ActiveDataSet | None = None
    delay: int | None = None
    pending_timestamp: Timestamp | None = None

    def as_json(self) -> dict[str, Any]:
        """Serialize to JSON."""
        result: dict[str, Any] = {}
        if self.active_dataset is not None:
            result["activeDataset"] = self.active_dataset.as_json()
        if self.delay is not None:
            result["delay"] = self.delay
        if self.pending_timestamp is not None:
            result["pendingTimestamp"] = self.pending_timestamp.as_json()
        return result

    @classmethod
    def from_json(cls, json_data: Any) -> PendingDataSet:
        """Deserialize from JSON."""
        cls.SCHEMA(json_data)
        active_dataset = None
        pending_timestamp = None
        if "activeDataset" in json_data:
            active_dataset = ActiveDataSet.from_json(json_data["activeDataset"])
        if "pendingTimestamp" in json_data:
            pending_timestamp = Timestamp.from_json(json_data["pendingTimestamp"])

        return PendingDataSet(
            active_dataset,
            json_data.get("delay"),
            pending_timestamp,
        )
