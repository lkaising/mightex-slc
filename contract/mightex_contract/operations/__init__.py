"""Operation request, success, and reply models.

One module per public operation. The client and server import operation models
from this package. Each operation exposes a Request model, a per-operation Ok
success model, and a Reply union discriminated on the status field.
"""

from __future__ import annotations

from mightex_contract.operations.close_device import (
    CloseDeviceOk,
    CloseDeviceReply,
    CloseDeviceRequest,
)
from mightex_contract.operations.configure_normal import (
    ConfigureNormalOk,
    ConfigureNormalReply,
    ConfigureNormalRequest,
)
from mightex_contract.operations.configure_strobe import (
    ConfigureStrobeOk,
    ConfigureStrobeReply,
    ConfigureStrobeRequest,
)
from mightex_contract.operations.configure_trigger import (
    ConfigureTriggerOk,
    ConfigureTriggerReply,
    ConfigureTriggerRequest,
)
from mightex_contract.operations.device_info import (
    DeviceInfoOk,
    DeviceInfoReply,
    DeviceInfoRequest,
)
from mightex_contract.operations.enumerate_devices import (
    EnumerateDevicesOk,
    EnumerateDevicesReply,
    EnumerateDevicesRequest,
)
from mightex_contract.operations.get_active_mode import (
    GetActiveModeOk,
    GetActiveModeReply,
    GetActiveModeRequest,
)
from mightex_contract.operations.get_capabilities import (
    GetCapabilitiesOk,
    GetCapabilitiesReply,
    GetCapabilitiesRequest,
)
from mightex_contract.operations.initialize import (
    InitializeOk,
    InitializeReply,
    InitializeRequest,
)
from mightex_contract.operations.open_device import (
    OpenDeviceOk,
    OpenDeviceReply,
    OpenDeviceRequest,
)
from mightex_contract.operations.read_load_voltage import (
    ReadLoadVoltageOk,
    ReadLoadVoltageReply,
    ReadLoadVoltageRequest,
)
from mightex_contract.operations.read_parameters import (
    ReadParametersOk,
    ReadParametersReply,
    ReadParametersRequest,
)
from mightex_contract.operations.restore_factory_defaults import (
    RestoreFactoryDefaultsOk,
    RestoreFactoryDefaultsReply,
    RestoreFactoryDefaultsRequest,
)
from mightex_contract.operations.set_active_mode import (
    SetActiveModeOk,
    SetActiveModeReply,
    SetActiveModeRequest,
)
from mightex_contract.operations.set_fan_pwm_level import (
    SetFanPwmLevelOk,
    SetFanPwmLevelReply,
    SetFanPwmLevelRequest,
)
from mightex_contract.operations.set_normal_current import (
    SetNormalCurrentOk,
    SetNormalCurrentReply,
    SetNormalCurrentRequest,
)
from mightex_contract.operations.soft_reset import (
    SoftResetOk,
    SoftResetReply,
    SoftResetRequest,
)
from mightex_contract.operations.store_settings import (
    StoreSettingsOk,
    StoreSettingsReply,
    StoreSettingsRequest,
)

__all__ = [
    # enumerate_devices
    "EnumerateDevicesRequest",
    "EnumerateDevicesOk",
    "EnumerateDevicesReply",
    # open_device
    "OpenDeviceRequest",
    "OpenDeviceOk",
    "OpenDeviceReply",
    # get_capabilities
    "GetCapabilitiesRequest",
    "GetCapabilitiesOk",
    "GetCapabilitiesReply",
    # device_info
    "DeviceInfoRequest",
    "DeviceInfoOk",
    "DeviceInfoReply",
    # initialize
    "InitializeRequest",
    "InitializeOk",
    "InitializeReply",
    # store_settings
    "StoreSettingsRequest",
    "StoreSettingsOk",
    "StoreSettingsReply",
    # restore_factory_defaults
    "RestoreFactoryDefaultsRequest",
    "RestoreFactoryDefaultsOk",
    "RestoreFactoryDefaultsReply",
    # soft_reset
    "SoftResetRequest",
    "SoftResetOk",
    "SoftResetReply",
    # set_fan_pwm_level
    "SetFanPwmLevelRequest",
    "SetFanPwmLevelOk",
    "SetFanPwmLevelReply",
    # close_device
    "CloseDeviceRequest",
    "CloseDeviceOk",
    "CloseDeviceReply",
    # configure_normal
    "ConfigureNormalRequest",
    "ConfigureNormalOk",
    "ConfigureNormalReply",
    # set_normal_current
    "SetNormalCurrentRequest",
    "SetNormalCurrentOk",
    "SetNormalCurrentReply",
    # configure_strobe
    "ConfigureStrobeRequest",
    "ConfigureStrobeOk",
    "ConfigureStrobeReply",
    # configure_trigger
    "ConfigureTriggerRequest",
    "ConfigureTriggerOk",
    "ConfigureTriggerReply",
    # set_active_mode
    "SetActiveModeRequest",
    "SetActiveModeOk",
    "SetActiveModeReply",
    # get_active_mode
    "GetActiveModeRequest",
    "GetActiveModeOk",
    "GetActiveModeReply",
    # read_parameters
    "ReadParametersRequest",
    "ReadParametersOk",
    "ReadParametersReply",
    # read_load_voltage
    "ReadLoadVoltageRequest",
    "ReadLoadVoltageOk",
    "ReadLoadVoltageReply",
]
