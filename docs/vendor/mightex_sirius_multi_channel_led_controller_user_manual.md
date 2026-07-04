# MIGHTEX
**Simply Brighter**

| (In Canada) | (In US) |
| --- | --- |
| 111 Railside Road | 1241 Quarry Lane |
| Suite 201 | Suite 105 |
| Toronto, ON M3A 1B2 | Pleasanton, CA 94566 |
| CANADA | USA |
| Tel: 1-416-840 4991 | Tel: 1-925-218 1885 |
| Fax: 1-416-840 6541 | Email: sales@mightex.com |

---

# SLC-XXXX-S/U

# Multiple Channels LED Controller User Manual

Version: 1.3.6

Oct. 12, 2018

---

## Relevant Products

| Part Numbers |
| --- |
| SLC-AA02-U, SLC-AA04-U,SLC-AA02-S,SLC-AA04-S, |
| SLC-AV02-U, SLC-AV04-U,SLC-AV02-S,SLC-AV04-S, |
| SLC-SA02-U, SLC-SA04-U,SLC-SA02-S,SLC-SA04-S, |
| SLC-SV02-U, SLC-SV04-U,SLC-SA02-S,SLC-SV04-S, |
| SLC-MA01-U,SLC-MA02-U,SLC-MA12-U,SLC-MA16-U, |
| SLC-MA12-S,SLC-MA16-S,SLC-CA01-U,SLC-CA02-U,SLC-CA12-U,SLC-CA16-U,SLC-CA12-S,SLC-CA16-S |
| SLC-FA02-U, SLC-FA04-U, SLC-FV02-U, SLC-FV04-U |
| SLC-FA02-S, SLC-FA04-S, SLC-FV02-S, SLC-FV04-S |
| SLC-XA02-U, SLC-XA04-U, SLC-XV02-U, SLC-XV04-U |
| SLC-XA02-S, SLC-XA04-S, SLC-XV02-S, SLC-XV04-S |
| SLC-HA02-S, SLC-HA02-U, SLC-HV02-S, SLC-HV02-U |
| SLB-HA01-U, SLC-MA04-MU, SLC-CA04-MU |

*— Mightex Proprietary and Confidential · 2018-11-10 · 1 of 26 —*

---

## Revision History

| Revision | Date | Author | Description |
| --- | --- | --- | --- |
| 1.0.0 | Jan. 16, 2006 | JT Zheng | Initial Revision |
| 1.0.1 | Feb. 9, 2006 | JT Zheng | 128 Steps for Step Pattern |
| 1.0.2 | May 11, 2006 | JT Zheng | Multiple Devices Supported |
| 1.0.3 | Jun. 6, 2006 | JT Zheng | Current Linearity and Repeatability correction. |
| 1.0.4 | Jul. 6, 2006 | JT Zheng | External Trigger Mode Improvements |
| 1.1.0 | Oct. 30, 2006 | JT Zheng | Supporting 4 Modules |
| 1.1.1 | Nov. 7, 2006 | JT Zheng | New I-V Curve Application Example |
| 1.2.0 | Dec. 10, 2006 | JT Zheng | Add MA/CA Module |
| 1.2.1 | May. 12, 2007 | JT Zheng | Add FA/FV Module |
| 1.2.2 | Mar. 28, 2007 | JT Zheng | Add XA/XV Module |
| 1.2.3 | May 21, 2007 | JT Zheng | Add HA/HV Module |
| 1.2.4 | July 24 , 2007 | JT Zheng | Add USB, RS232 switch |
| 1.2.5 | Sep 8, 2007 | JT Zheng | Add QA Module |
| 1.2.6 | May. 13, 2008 | JT Zheng | Add Diagram for CA/MA |
| 1.2.7 | Jul. 30, 2008 | JT Zheng | Add "Caution" part. |
| 1.2.8 | Jan. 12, 2010 | JT Zheng | Add SLB-HA01-U model |
| 1.2.9 | Aug 11, 2010 | JT Zheng | Removing QA model |
| 1.3.0 | Jun. 2, 2011 | JT Zheng | Adding current limitation description for SA/SV/AA/AV…models. |
| 1.3.1 | July 12, 2011 | Zoaib Khan | Revision and editing |
| 1.3.2 | Nov. 12, 2011 | JT Zheng | Adding SLC-MA04/CA04-MU |
| 1.3.3 | Jun.21, 2012 | JT Zheng | FA/FV/XA/XV current on GUI |
| 1.3.4 | April 21,2014 | JT Zheng | Limits to application tabs |
| 1.3.5 | April 22, 2014 | JT Zheng | Adding "Unison" tab description |
| 1.3.6 | Oct. 12, 2018 | JT Zheng | New Logo |

*— Mightex Proprietary and Confidential · 2018-11-10 · 2 of 26 —*

---

## Caution:

Please read the "Security and Working Limit" section on page 9 to 12 of this manual carefully for the current and power limit of the controller and the heat dissipation cautions. When using an oscilloscope to measure the voltage on the LED, please make sure to note:

For **AA/AV/SA/SV/FA/FV/XA/XV/HA/HV**: When using a GND probe to measure LED-, a proper **"floating" measurement** method, such as using an isolator is required. The LED may be damaged because the scope's probe reference is usually connected to the earth GND by default.

Do not attempt to bypass the protective grounding system of the oscilloscope by using an isolation transformer OR disconnecting the ground connector on the power plug.

> **[Figure: For AA/AV/SA/SV/FA/FV/XA/XV/HA/HV/QA Modules]** — Schematic showing a control MOSFET driving the LED, with the LED+ / LED- terminals and an "oscilloscope probe, ground" connection to LED-.

*— Mightex Proprietary and Confidential · 2018-11-10 · 3 of 26 —*

---

## Introduction

Mightex Sirius™ Multi-Channel LED Controller was designed to drive various kinds of LEDs in the current market, including Mightex Sirius™ Light Sources, as well as LEDs from other vendors. Windows based PC software is provided to control individual channel operations easily. An external trigger is provided for each channel, allowing real time applications, such as machine vision application.

### Module Feature differences:

| Module | Strobe/Trigger Profile | Voltage Monitoring | TRIGGER Mode | Maximum Current* | Current Resolution |
| --- | --- | --- | --- | --- | --- |
| SLC-AAcc-X | 128 Steps | No | Yes | 1A/3.5A | 1mA |
| SLC-AVcc-X | 128 Steps | Yes | Yes | 1A/3.5A | 1mA |
| SLC-SAcc-X | 2 Steps | No | Yes | 1A/3.5A | 1mA |
| SLC-SVcc-X | 2 Steps | Yes | Yes | 1A/3.5A | 1mA |
| SLC-FAcc-X | 2 Steps | No | Yes | 100mA/350mA | 0.1mA |
| SLC-FVcc-X | 2 Steps | Yes | Yes | 100mA/350mA | 0.1mA |
| SLC-XAcc-X | 128 Steps | No | Yes | 100mA/350mA | 0.1mA |
| SLC-XVcc-X | 128 Steps | Yes | Yes | 100mA/350mA | 0.1mA |
| SLB/C-HAcc-X | 2 Steps | No | Yes | 2A/3.5A | 1mA |
| SLC-HVcc-X | 2 Steps | Yes | Yes | 2A/3.5A | 1mA |
| SLC-MAcc-X | 2 Steps | No | No | 1A/1A (1.2A/1.2A) | 1mA |
| SLC-CAcc-X | 2 Steps | No | No | 1A/1A (1.2A/1.2A) | 5mA |

\*. For SLC-MA04/CA04-MU Module, the Maximum Current is 1.2A

cc – Channel Number of the module, e.g. for 4 channel module, it's 04

X – "U" for USB module and "S" for RS232 Module. If it is "X", the module is with USB and RS232 interface, and can be selected with the switch between them, as following:

> **[Figure: Interface select switch]** — Shows a "Mightex" module with a "USB / RS232" selector switch.

The interface select switch, while it's at the USB/RS232 side, the USB/RS232 port is the selected interface. Please note that when a new selection is made, the module should be power cycled before the selection is effective. (Note that this is available on new Mightex LED driver module only)

\*In Maximum Current column, there are two currents, the first one is the maximum current in NORMAL mode, and the second one is the maximum current in STROBE/TRIGGER mode, (if the TRIGGER mode is applicable to the module).

*— Mightex Proprietary and Confidential · 2018-11-10 · 4 of 26 —*

---

## OPERATION MODES:

Each channel can be individually configured to function as one of the following modes:

**Disable:** Channel is shut down completely.

**Normal:** Continuous intensity control via setting driving current from 0 mA to 1000 mA. It's controllable via PC interface.

**Trigger:** (For AA/AV/SA/SV/FA/FV/XA/XV/HA/HV/QA only) External signal as "Trigger In" via connector switches channel on. A pre-programmed pattern may be generated after the trigger. The overdrive rules must be met.

**Strobe:** A strobe pattern is generated (repeatedly) on the channel. It may be triggered by a soft strobe command. In this mode, strobe frequencies can be as high as 25KHz(See the following timing spec.) The strobe pattern (current/period pairs) is predefined via the command interface. The overdrive rules must be met.

### ELECTRICAL SPECIFICATION: (AA/AV/SA/SV Modules)

| Parameters | Value | Unit |
| --- | --- | --- |
| Power Input Voltage | 12 – 24 | V(dc) |
| Power Input Current | 4000 (4 channel module) | mA |
| Channel Driving Voltage | V(dc) – 0.5 (Max) | V |
| Channel Driving Current | 0 – 1000 (Normal) | mA |
| | 0 – 3500 (Strobe, Trigger) | mA |
| Current Resolution | 12 (0 – 3500mA) | Bit (1mA) |
| Current Accuracy Error | +/-4 or +/-0.5% | mA |
| Current Repeatability | +/-1 or +/-0.2% | mA |
| Trigger Input High Level | 4.5 – 10.0 | V |
| Trigger Input Low Level | 0 – 0.8 | V |
| Voltage Monitor ( AV and SV Only) | +/-10 | mV |

\*. AA and AV Modules provide 128 steps, and for SA and SV, it only provides 2 steps.

### ELECTRICAL SPECIFICATION: (FA/FV/XA/XV Modules)

| Parameters | Value | Unit |
| --- | --- | --- |
| Power Input Voltage | 12 – 24 | V(dc) |
| Power Input Current | 1500 (4 channel module) | mA |
| Channel Driving Voltage | V(dc) – 0.5 (Max) | V |
| Channel Driving Current | 0 – 100 (Normal) | mA |
| | 0 – 350 (Strobe Trigger) | mA |
| Current Resolution | 0.1 (0 – 350mA) | mA |
| Current Accuracy Error | +/-0.4 or +/-0.5% | mA |
| Current Repeatability | +/-0.1 or +/-0.2% | mA |
| Trigger Input High Level | 4.5 – 10.0 | V |
| Trigger Input Low Level | 0 – 0.8 | V |
| Voltage Monitor ( AV and SV Only) | +/-10 | mV |

*— Mightex Proprietary and Confidential · 2018-11-10 · 5 of 26 —*

---

### ELECTRICAL SPECIFICATION: (HA/HV Modules)

| Parameters | Value | Unit |
| --- | --- | --- |
| Power Input Voltage | 9 – 12 | V(dc) |
| Power Input Current | 4500 (2 channel module) | mA |
| Channel Driving Voltage | V(dc) – 0.5 (Max) | V |
| Channel Driving Current | 0 – 2000 (Normal) | mA |
| | 0 – 3500(Strobe Trigger) | mA |
| Current Resolution | 1 (0 – 3500mA) | mA |
| Current Accuracy Error | +/-4 or +/-0.5% | mA |
| Current Repeatability | +/-1 or +/-0.2% | mA |
| Trigger Input High Level | 4.5 – 10.0 | V |
| Trigger Input Low Level | 0 – 0.8 | V |
| Voltage Monitor ( AV and SV Only) | +/-10 | mV |

### TIMING SPECIFICATION: (AA/AV/SA/SV/FA/FV/XA/XV/HA/HV Modules)

| Parameters | Value | Unit |
| --- | --- | --- |
| Timing Resolution | 20 | μs |
| Max Profile Steps | 2/128 | |
| Max Trigger Delay | 25 | μs |

Basically, (FA/FV) (XA/XV) has the same functionalities as (SA/SV), (AA/AV), (HA/HV), except that they provide 0.1mA current resolution, only while its current range is 0 – 100mA (NORMAL Mode) and 0 – 350mA (STROBE and TRIGGER Mode).

### MECHANICAL SPECIFICATION: (SLC-AA/AV/SA/SV/FA/FV/XA/XV/HA/HV Modules)

Dimension: 201mm(L) × 147mm (W) × 40mm ( H )

Weight: 600g

### MECHANICAL SPECIFICATION: (SLB-HA Modules)

Dimension: 133mm(L) × 112mm (W) × 60mm ( H )

Weight: 300g

*— Mightex Proprietary and Confidential · 2018-11-10 · 6 of 26 —*

---

### ELECTRICAL SPECIFICATION: (MA/CA Module)

| Parameters | Value | Unit |
| --- | --- | --- |
| Power Input Voltage | 9 – 24 | V(dc) |
| Power Input Current | 4000 | mA |
| Channel Driving Voltage | V(dc) – 3.0 (Max) | V |
| Channel Driving Current | 0 – 1000 (Normal) / 0 – 1200 (Normal)* | mA |
| | 0 – 1000 (Strobe) / 0 – 1200 (Normal)* | mA |
| Channel Output Power Limit | 10 (15)* | W |
| Current Resolution | 1/5** (0 – 1000mA) | mA |
| Current Accuracy Error | +/-5 or +/-1.0% | mA |
| Current Repeatability | +/-2 or +/-0.5% | mA |

\*Although each channel may output 21V as maximum load voltage and 1A as its maximum current, the average power limit is 10W.This means while output current is 1A, the maximum allowed LOAD voltage must be less than 10V in NORMAL (DC) mode, and similarly for the 21V output. In STROBE (PWM) mode, an output of 21V at 1A is allowed as long as the average power output is less than 10W.

For SLC-MA04/CA04-MU modules, the input voltage range is 12 – 24V, the maximum current is 1.2A and the channel power limit is 18W.

\*\* MA Modules achieves 1mA resolution and CA Modules can only achieve 5mA resolution.

### TIMING SPECIFICATION: (MA/CA Module)

| Parameters | Value | Unit |
| --- | --- | --- |
| Timing Resolution | 100** | μs |
| Max Profile Steps | 2 | |

\*\*. The minimum step time width is 1000µs, which means the time value may be set as 1000, 1100….and so on for the time of each step.

### MECHANICAL SPECIFICATION: (MA/CA Module)

\* 4/12/16 Channel version:

Dimension: 190mm(L) × 180mm (W) × 34mm ( H )

Weight: 600g

\* 1/2 Channel version:

Dimension: 80mm(L) × 65mm (W) × 24mm ( H )

Weight: 600g

### OPERATION CONDITION:

Operating Temperature Range: 0℃ – 45℃

Storage Temperature Range: -25℃ – 85℃

Relative Humidity, Non-condensing: 5% – 95%

*— Mightex Proprietary and Confidential · 2018-11-10 · 7 of 26 —*

---

## Operation Mode

Each channel of the controller may be in one of the FOUR operation modes:

**DISABLE:** In this mode, the channel is disabled and the output current driving capability is ZERO.

**NORMAL:** Channel may output from 0 to maximum setting current to drive the load on this channel. PC software can be used to set the current and, after setting the current, the channel will work constantly with this driving current.

**STROBE:** Each channel can have a programmed pattern for strobe mode. The pattern is a multiple step profile. Each step consists of a current/time pair, and while the channel is set to this mode, the channel is driven according to the pattern. An additional programmable repeat count is also provided for each channel, allowing the pattern to be repeated. With these programmable parameters, the channel can be set to output a high frequency strobe, programmable duty cycle PWM signal…etc. Virtually, it can output any arbitrary driving wave form.

**TRIGGER:** (For AA/AV/SA/SV/FA/FV/XA/XV/HA/HV only) Each channel can have a programmed pattern. For trigger mode, the pattern is a multiple step profile, and each step consists of a current/time pair. While the channel is set in this mode and the defined external trigger is asserted, the channel is driven according to the pattern, and when it's finished, the channel output is set to OFF and waits for the next trigger. If a trigger occurs during the execution of the pattern, (triggered by the previous assertion), the pattern will start from the beginning. There's a special case of this mode: the channel output is completely conformed to the trigger input signal with the programmable driving current.

(For QA Modules only) Each channel can have 3 steps, and the module will use the three "T" settings in these three steps. For the "I" setting in the second step, please refer to the "Timing control of QA module"

Each channel has its own parameter sets for each of its modes. For instance, for NORMAL mode, it has maximum current and set current, and for STROBE mode, it has maximum current, repeat count and a 2/128 step profile. Setting those parameters will NOT change the current working mode of the channel. For changing the working mode, a particular MODE SWITCH command is used, and the controller has the following defined behaviors upon this command:

**Switch to DISABLE mode:** The channel is OFF immediately.

**Switch to NORMAL mode:** The channel output is set at a constant current.

**Switch to STROBE mode:** The channel starts the strobe pattern.

**Switch to TRIGGER mode:** The channel is OFF, waiting for external trigger.

As all the parameters and current working modes of all channels can be stored in the flash memory of the controller, after switching the power on, controller will read these settings and set each channel to their proper working mode and parameters. The behavior of each channel upon power on is the same as the above "Switch to". For example, if channel ONE is set to STROBE mode with a pattern, and these settings are stored to flash, after switching the power on, this channel will start to output the pattern immediately.

*— Mightex Proprietary and Confidential · 2018-11-10 · 8 of 26 —*

---

## 1.0 Programmable Pattern

The pattern used in STROBE and TRIGGER mode has the following format:

```
Step1: (Current, Time)
Step2: (Current, Time)
…
```

A total of 128 Steps are provided for STROBE and TRIGGER mode profile. However, a (0, 0) pair must be used to end the profile, therefore only a maximum of 127 steps may be defined. If less steps are enough for a certain profile, a (0, 0) pair should be used at the end. For modules with 2 effective steps only, it actually accepts 3 steps, the third one must be (0, 0).

Note that the unit of time is "μs" and the unit of current is "mA".

Example:

```
Step1: (100, 100000)
Step2: (1000, 10000)
Step3: (0, 1000000)
Step4: (500, 20000)
Step5: (0, 0)
```

The pattern is as following:

```
 1000mA
 500mA
100mA
        100ms   10ms   1000ms   20ms
```

> **[Figure: Waveform diagram]** — Shows the programmed pattern above: 100mA for 100ms, 1000mA for 10ms, 0mA (off) for 1000ms, and 500mA for 20ms.

In STROBE mode, there is an additional repeat count, which allows the pattern to be repeated at programmable counts from 1 – 99999999. Note that the number 9999 is a special case which will cause the pattern to infinitely repeat in STROBE mode. For modules with 2 steps only, there are only 2 steps that can be programmed as above. Please note that for QA modules, the second step "I" setting is always taken as "ZERO", even if programmed to a non-zero value. So for QA modules, while it is in STROBE mode, it can output PWM only, and for the timing control, please refer to "Timing control of QA module.

*— Mightex Proprietary and Confidential · 2018-11-10 · 9 of 26 —*

---

## 1.1 Security and Working Limit

### For AA/AV/SA/SV/FA/FV/XA/XV/HA/HV/QA Modules:

> **[Figure: Output circuit]** — Common-anode channel output circuit showing "Control", "LED+" and "LED-".

For AA/AV/SA/SV/FA/FV/XA/XV/HA/HV/QA Modules, the output circuit of each channel is shown as above. It is a common-anode design for the channels. For those with LED combinations (e.g. tri-LED module), it is fine to tie the LED+ of the channels together.

Because these modules are designed as universal LED drivers, it gives the most flexibility for driving various LED loads. Care must be taken while driving an LED head on a certain channel. For protecting the LED head and the controller, the following items should always be considered:

**1). HEAT SINK FOR LED:** A proper heat sink for the LED load (usually the light head) is required. Especially for some high power LEDs, the heat dissipation is considerably large, so it is expected that an appropriate heat sink will be used in accordance to the specifications.

**2). CHANNEL MAXIMUM CURRENT:** When driving any LED (or LED combination), maximum current of the load must be carefully set in the appropriate channel's parameters. (Note that each mode has a programmable maximum current, while in STROBE and TRIGGER mode, this current might be larger than the one in NORMAL mode). It must be made certain that the load can work under this maximum current for the programmed pattern (including the constant driving in NORMAL mode), and it might require referencing the specification sheet of the LED.

**3). CONTROLLER INPUT CURRENT/VOLTAGE:** Although the factory AC-DC adapter rating is 12V/4000mA, an adapter which outputs higher voltage and current may be used. However, the following precautionary steps must be taken:

- Read the LED specification and calculate the minimum driving voltage. The lowest output voltage adapter capable of driving the device must be chosen. For example, if the driving voltage is under 11V, a 12V adapter must be used in this case. A higher voltage adapter may cause the housing of the controller to become very HOT. Use the following formula to calculate the Voltage capability of an adapter:

```
Adapter Output Voltage = Vload + 1V (For QA module, Vadapter = Vload + 3.5V)
```

So, the correct adapter should always be chosen (among the 12V, 15V, and 24V series). If the controller output is at maximum current on all its channels, the metal case may get hot after prolonged use. It is recommended to put the controller on a metal surface for better heat dissipation.

The output current of the adapter can be calculated in the following formula:

```
Adapter Output Current = 300mA + Total Channel Constant Current
```

For example, if all four channels are working under NORMAL mode with 1000mA setting current, the Adapter should provide (300mA + 4000mA), in this case, a 4.5A – 5A adapter is recommended.

*— Mightex Proprietary and Confidential · 2018-11-10 · 10 of 26 —*

---

**4).** When using an oscilloscope to monitor current/voltage, please be sure the scope's AC plug is disconnected from the GROUND (using 2 pin AC Plug instead of the 3 pin), if it is desired to put the GND probe to LED-. However, for the sake of safety, it is not recommended, unless it is a professional who performs this modification.

**5).** When a channel is put in STROBE/TRIGGER mode, it is possible to have maximum current greater than 1000mA (or 2000mA on HX models), but make sure that:

The total current of the module does not exceed 4A DC Average.

The current of a Channel does not exceed 1A DC Average, e.g.: when a channel is working under STROBE mode, if the current is set to 2A, the PWM ratio should be less than 50%, and similarly, 30% for 3.5A.

The above limitations can be lowered slightly when the heat dissipation of the LED Driver is very efficient. The case temperature should be kept below 55 ℃ (in this case, the PCBA temperature might go to 60 - 65 ℃).

### For MA/CA Modules:

> **[Figure: MA/CA output circuit]** — Common-cathode channel output circuit showing "Control", "DC-DC", "LED+" and "LED-".

For MA/CA Modules, the output circuit of each channel is shown as above. Basically, it is a common-cathode design; there it is OK to tie the LED- of the channels together.

MA modules are designed with high-efficiency DC-DC switch inside. Each channel can work separately with very different loads, and the efficiency will be 80 - 90% in most cases. However, caution must be taken while driving an LED head on a certain channel in order to protect the LED head and the controller. It is imperative that the following items be considered:

**1). HEAT SINK FOR LED:** The LED load must have the proper heat sink (usually the light head). Especially for some high power LEDs, the heat dissipation is considerably large, so it is expected that the necessary heat sink for the LED is installed to make sure the LED can work under the desired current/voltage.

**2). HEAT SINK FOR DRVIER:** For the 16 channel MA/CA modules, while the total output power of all channels is more than 120W (as it may output 160W at maximum), it is recommended to use an external heat sink for better heat dissipation, such as a metal plate. It should be mounted on the bottom surface of the driver.

**3). CHANNEL MAXIMUM CURRENT:** For driving a certain LED (or LED combination), the maximum current of the load must be carefully set in the appropriate channel's parameters. Note that each mode has a programmable maximum current. While in STROBE and TRIGGER mode, this current might be greater than the one in NORMAL mode. It must be ensured that the load can work under this maximum current for the programmed pattern (including the constant driving in NORMAL mode). This information can be found in the specifications sheet of the LED.

*— Mightex Proprietary and Confidential · 2018-11-10 · 11 of 26 —*

---

**4). CONTROLLER INPUT CURRENT/VOLTAGE:** Although the factory AC-DC adapter rating is 12V/4000mA, an adapter which outputs higher voltage and current may be used. However, the following precautionary steps must be taken:

1. Choose an AC-DC adapter which can output voltage at least 3V higher than the highest load voltage of all channels, for example, for a 4 channel modules, the load on channels are:

```
Channel 1: 3.5V at 1A
Channel 2: 7.0V at 1A
Channel 3: 9.0V at 0.5A
Channel 4: 11.5V at 0.35A
```

In this case, an AC-DC adapter with at least 15V output voltage (15V- 24V) should be used. As for current, considering 80% power efficiency, the total output power for the above example is:

```
Pout = 3.5×1 + 7.0×1 + 9.0×0.5 + 11.5×0.35 = 19.025W
```

So the Pin = 19.025/0.8 + 1.5 = 25.28W (Note that 1.5W is the power consumption for controlling circuit). In this case, the AC-DC output current should be greater than 25.28/15 = 1.7A. Therefore, a 15V/2.0A adapter is proper in this case.

2. Although each channel may output 21V maximum load voltage and 1A maximum current, the maximum power output limit is 10W (15W for MA04/CA04 modules), which means while the output is 21V, the current should not be more than 0.48A (in DC mode), and if the output current is 1A, the output voltage should be kept less than 10V (in DC mode). While in PWM mode, 21V at 1A is acceptable as long as the average power is less than 10W (at proper duty cycle).

\*. For SLC-MA04/CA04-MU, the maximum output current of each channel is 1.2A and the channel power output limit is 15W.

## 1.2 External Trigger (For AA/AV/SA/SV/FA/FV/XA/XV/HA/HV/QA only)

External trigger is only effective while the channel is set in TRIGGER mode. A programmable pattern and a trigger edge can be set for each channel. When the edge occurs on the trigger signal, the pattern is driven on the channel immediately (refer to the maximum trigger delay).

Internally, the controller has the following opto-coupler based design for each trigger input:

> **[Figure: Trigger input circuit]** — Opto-coupler based trigger input with a built-in 360 Ω resistor.

The diode is expected to be working under :

```
Iforward = 5mA – 25mA
Vforward = ~1.2V
```

As a 360Ω resistor built in, a 3.3 – 10.0V source with 6mA minimum current source capability is expected to be the trigger input.

*— Mightex Proprietary and Confidential · 2018-11-10 · 12 of 26 —*

---

There is a special case used, which is defined by programing the unit of "time" for the first point of the profile to "9999". It means that the TRIGGER mode is working differently from its normally defined value. In this case, the channel outputs the programmed current of the first point with the conformed time (or reversed, depending on the polarity value of the TRIGGER mode parameters) chart of the input trigger signal. When polarity is "0" (Rising edge for Trigger Polarity), the output follows the trigger input, e.g. while the external trigger signal is "H", the output current is set current, while external signal is "L", the output is shut off. For polarity "1" (Falling edge for Trigger Polarity), it's a reversed follower.

With this feature, a possible connection might be an external flash pulse from devices like cameras to the LED driver, which can be used for external lighting.

Example:

```
Step1: (100, 9999) --- The output current is 100mA.
Step2: (0, 0)
```

Note that for QA Module, the Current setting is always at the second step, so it should be

```
Step1: (0, 9999)
Step2: (100, x)
Step3: (0,x)
```

## 2.0 PC Software Description

A PC with a RS232 COM port or USB (USB2.0 is preferred) is required to run the software. It is designed to run on Windows 98/ME/NT/2000/XP, with the following setup:

> **[Figure: System setup]** — Shows a PC connected via RS232/USB to the LED Controller (with AC-DC power), driving Channel 1 … Channel 4.

The installation of the software is very simple. Copy the "\Software" sub-directory, which includes the .EXE and .DLL files, as well as some other sample channel profile files, to the local disk, and run the .EXE from there.

Note that the "\Software" sub-directory (and all its files) copied from the CD-ROM might be marked with the "ReadOnly" attribute. If this is the case, remove the "Read-Only" attribute for this directory. This can be performed in the "Properties" dialog, which shows up by right clicking the sub-directory and choosing "Properties".

After the program starts, the "COM selection" form will open:

*— Mightex Proprietary and Confidential · 2018-11-10 · 13 of 26 —*

---

## 2.1 COM / USB Port Selection

> **[Figure 1. Port Selection Form]** — A "Port Selection" dialog with radio buttons COM1–COM8 and USB, plus an OK button (COM1 selected).

When using RS232 Modules (SLC-XXXX-S), select a COM port, and make sure the selected COM port is available on the PC. Then select the LED Controller that is connected to this port. Note that in this case, only ONE module is supported for this Software.

When using USB Modules (SLC-XXXX-U), select the "USB" option, which supports multiple modules to be controlled via the software. **Please make sure all the USB modules are powered on and connected properly before running the software.**

Note that although USB modules are Plug&Play. This PC Software only initializes the USB devices once at its startup, so it is important to make sure all the USB modules are powered on and connected when the software starts to run. Any changes of the USB module's state (e.g. disconnect one module) will require a re-start of the PC software to make sure the software works properly.

Here, the USB modules mean Mightex LED Driver (e.g. SLC-AAXX-U). Other USB Devices are not considered by the PC software.

*— Mightex Proprietary and Confidential · 2018-11-10 · 14 of 26 —*

---

## 2.2 Main GUI

> **[Figure 2. Main Page]** — The "Led Driver Control Panel V3.2.2" main window, showing Normal Mode Settings, Strobe Mode Settings and Trigger Mode Settings panels, Parameters Setting Selection, Current Mode Selection (DISABLE / NORMAL / STROBE / TRIGGER), and the Channel Controls / Advanced Controls / Applications tabs.

The main page consists of "*Channel Controls*", "*Advanced Controls*" and "**Applications**" pages. In the "Channel Controls" page, the parameters for each mode can be set for each channel, and the current working mode for each channel can be switched.

***Note: For different module types, the GUI is different. The part corresponding to features which are NOT applicable to a certain module type will NOT appear on the main window.***

### 2.2.1 Device and Channel Select

For USB modules, select the current control module by selecting the module in the drop-down box:

> **[Figure: Drop-down]** — `Sirius SLC-AV04-U :04-DEFAULT`

Note that it is in a "ModuleNo: SerialNo." format, the serial No. is the module's serial number.

For RS232 modules, only ONE RS232 module is supported, "COM", and there is no need to change it.

*— Mightex Proprietary and Confidential · 2018-11-10 · 15 of 26 —*

---

When there is more than one device connected to the PC via USB, always select the correct device before performing any operations (including its channels setting, and other operations in "**Advanced Controls**" and "**Applications**").

After selecting the device, the channel of this device will be listed on the `CHANNEL 1` box.

Select the channel desired to be set from this box. After selecting the device and channel, the tab of the channel control will show the combination of the selected device and channel as:

> **[Figure]** — `Sirius SLC-AV04-U :04-DEFAULT : Channel-1`

Also, the selected device will be shown on status pane at the bottom left corner of the main window.

### 2.2.2 Channel Controls

After the device and channels are selected, operations can be performed on the selected channel. There are two parts for each channel. The first part is for the parameter settings for each mode of the channel. These parameters are:

For **NORMAL** mode: Maximum Current and Set Current.

For **STROBE** mode: Maximum Current, 128 Steps* Pattern (Current/Time pairs) and Repeat Count.

For **TRIGGER** mode: Maximum Current, 128 Steps* Pattern (Current/Time pairs) and Trigger Polarity.

\*. The 128th pair must be (0, 0), which allows 127 programmable maximum steps. In any case, a (0, 0) pair should be used for the end of the profile. For SA/FA/XA/CA/MA modules, it actually shows 3 steps, and the last one should always be a (0, 0) pair.

> **[Figure 3: Parameters Setting]** — The Normal / Strobe / Trigger Mode Settings panels with Max Current sliders, I(mA)/T(uS) step tables, Repeat Count, Trigger Polarity (Rising / Falling Edge), Parameters Setting Selection checkboxes (Normal / Strobe / Trigger Setting), Set Parameters, Load File and Save File.

After setting the parameters, select which mode(s), and their respective parameters, to be sent to the controller by checking the checkboxes in the **Parameters Setting Selection** (Normal Setting / Strobe Setting / Trigger Setting) and then clicking the **Set Parameters** button to send the parameters to the controller.

*— Mightex Proprietary and Confidential · 2018-11-10 · 16 of 26 —*

---

While the channel is working in Normal mode, the **RealTime Update Current** box can be checked and "Setting Current" marker can be slid, changing the channel current in real time.

The Voltage monitoring panel is displayed below. This panel only appears when the device is an "AV" or "SV" module. "AA" and "SA" modules do not have this display.

> **[Figure]** — `Voltage(mv): 10` with a `RealTime Refresh` checkbox.

Note that in Strobe Mode and Trigger Mode settings, there are **[Load CSV]** and **[Save CSV]** buttons for the programmed step pattern to be loaded from or saved to, respectively, a "*.CSV" file. The "*.CSV" (Comma Separated Variables) file is a text file which has several columns separated by commas. It is one of the native file formats MS Excel supports. So for a complicated pattern, MS Excel may be used to edit and save the pattern as a "*.CSV" file, and then load it for a latter application. ***It is recommended to use MS Excel to open, edit and save the "*.CSV" file to ensure it is in the correct format.***

The **Save File** button is used to save all the current settings of the channel to a file, and the **Load File** button may be used to reload these settings. Note that the *.CPL file contains all the settings for a certain channel, and can be used for other channels.

Also note that operations in this part will ONLY set the channel's parameter (except the **RealTime Update Current** feature), it will **NOT** change the channel's current working mode.

In order to change the current working mode, remember to select the mode in the **Current Mode Selection** (DISABLE / NORMAL / STROBE / TRIGGER) box and click **Set Current Mode** button. This will switch the channel to the selected mode immediately.

**Note:** For **CA** modules, although it is possible to set the currents Imax and Iset to any value between 0 – 1000mA, the module will revise the current to the closest acceptable value (e.g. set to 123 – 127mA, module will actually revise it to 125mA, 118 – 122mA will be 120mA). This is because CA modules can only achieve approximately 8bit output current resolution (from 0 – 1000mA).

**Note:** For **FA/XA/FV/XV** modules, as the current resolution is 100μA (0.1mA), the GUI is with "0.1mA" unit for all current, E.g. it will show as 100(0.1mA) for Imax and Iset on the GUI when it actually means 10.0mA. When user wants to set 30.0mA, user should set value to 300, as it's 300 (0.1mA).

*— Mightex Proprietary and Confidential · 2018-11-10 · 17 of 26 —*

---

### 2.2.3 Advance Controls

In addition to the channel parameter and mode setting, there are other important features for controlling the controller, and those features are provided in the Advance Controls page:

> **[Figure 4. Advanced Controls Page]** — Panels for "Support And Info", "Device Information" (with DeviceInfo / Send Command), "Firmware Upgrade Control" (Current Firmware version, Get Version, Stay at Boot Loader, Soft Reset, New Firmware, PROG, Active New Version) and "System Controls" (Store All Parameters To Module Eeprom).

In this page, the "**System Controls**" has only one feature When clicking the **Store All Parameters To Module Eeprom** button, all the current settings of all channels, including the current working modes and parameters of all channels, will be stored to the selected device ( in its Non-volatile memory). Next time after power cycling, all the parameters and current working modes for each channel will be restored automatically.

The "**Firmware Upgrade Control**" is used to download new firmware to the selected device. Use the following steps to properly upgrade the firmware.

**1).** In **Current Firmware**, click the **Get Version** button. The current version will be displayed in **Version:**.

**2).** Then check the **Stay at Boot Loader** and click the **Soft Reset** button, that will force the controller stay in the Boot Loader and wait for PC to download the new image.

Note that if **Soft Reset** is clicked with **Stay at Boot Loader** **unchecked**, it will reset the controller only, and the controller won't stay in Boot Loader. (Also note: before downloading a new firmware to the module, the module must be in Boot Loader).

*— Mightex Proprietary and Confidential · 2018-11-10 · 18 of 26 —*

---

**3).** In **New Firmware**, select the new firmware file ( *.bin file) with **[Browse]**. After selecting a correct file, the version will be displayed in its **Version:** field.

**4).** Click the **PROG** button. Downloading starts and its process will be showed in the progress bar, until the downloading completes successfully. The following dialog will show:

> **[Figure: Leddriver dialog]** — "Firmware Download Complete!" with an OK button.

**5).** Power cycle the controller, or simply click the **Active New Version** button to activate the new firmware.

A snapshot of a successful firmware download is shown below (Figure 5):

> **[Figure 5. After Successful Firmware Download]** — Firmware Upgrade Control panel showing Current Firmware Version 1.0.2, Stay at Boot Loader checked, New Firmware Version 1.0.2, progress bar at 100%.

If there are any problems during the downloading, power cycle the controller, and then restart from the step (1).

*— Mightex Proprietary and Confidential · 2018-11-10 · 19 of 26 —*

---

The "**Device Information**" panel can be used to get the information of the current module. Clicking the "Send Command" button will echo back the device information, including Firmware version, module serial number...etc., as the following:

> **[Figure: Device Information]** — `PhotonEdge LED Driver:1.1.5 Device Serial No.:04-060510-001`, with `DeviceInfo` and `Send Command`.

Note that the default "DeviceInfo" command should NOT be changed before clicking the button.

### 2.2.4 Applications (Only applicable to AA/AV/SA/SV/FA/FV/XA/XV/HA/HV Modules)

This tab provides examples of applications in which the LED controller might be used. The first example is a strobe generator. (**Note it's only applicable to AA/AV/XA/XV Modules**) It allows for the adjusting of the frequency, On/Off Ratio and Phase of the strobe.

> **[Figure: Strobe generator]** — Timing diagram (t1, t2, t3, T = 1/f, Ratio = t2/T, Phase = t1/T), Current Control sliders (I1, I2, I3), Timing Control (Frequency Range, FREQUENCY, RATIO, PHASE, Strobe Count, Repeat Forever), Real Time Test Control, and Data Setting Control (Select Channel, Set Data As Strobe/Trigger Mode Parameter).

Setting the parameters (I1, t1), (I2, t2) and (I3, t3) can be performed in an expanded GUI. The t1, t2 and t3 are set via the Frequency, Ratio, and Phase slide bars. When the **Real Time Update Enable** checkbox is checked, the strobe will be generated on the selected channel (when the channel is in Strobe mode) in real time. Once satisfied with the strobe parameters, the parameters may be set as the Strobe (and/or Trigger) profile for the selected channel. Note that "Strobe Count" is only applicable to the Strobe mode, as Trigger mode doesn't have this parameter.

*— Mightex Proprietary and Confidential · 2018-11-10 · 20 of 26 —*

---

The second example is a real time color changing application (**Note this is only applicable to LED driver with at least 3 channels**). Before running this example, be sure to connect the Red LED to channel 1, Green LED to channel 2, and Blue LED to channel 3, otherwise the application will not run as intended. In NORMAL mode, click the **Set Channels Mode/Parameters** button to set these channels to NORMAL mode. Before that, be sure the Imax in the "Channel Controls" Tab is set to a proper.

> **[Figure: Color changing application]** — "About Color Changing Led" panel, "Color Control Panel" with a color picker and Hue/Sat/Lum, Red/Green/Blue values, "Color Changing Control Settings" (Set Channels Mode/Parameters), RealTime Color Changing checkbox and Set Color button.

Checking the **RealTime Color Changing** will enable real time adjusting of the Red, Green and Blue values of the LEDs. While moving the mouse on the color panel with the left mouse button held down, the "Set Color" button can be used to send the color values to the LEDs.

Note that the color value is from 0 to 255, and the corresponding current is 0 – Imax*(value/256), increased by the step of Imax/256.

*— Mightex Proprietary and Confidential · 2018-11-10 · 21 of 26 —*

---

The third example is an I-V curve generator (**Note It's only applicable to AV/SV/FV/XV/HV modules**). The load should be connected to Channel 1 of the driver, and then set the Imax in NORMAL mode to a proper value to ensure it can cover the whole measurement range.

> **[Figure: I-V curve generator]** — "Load at channel: 1", "Set Channel to NORMAL mode", Current Start(mA), Current Step(mA), Total Steps, Step Interval(0.1s), Start button, and a Load Voltage(mv) vs Current(mA) plot.

Remember to click the **Set Channel to NORMAL mode** button to set Channel 1 to NORMAL mode (no matter which mode it was in previously).

Before clicking the **Start** button to start the measurement, input proper values for each parameter:

| Parameter | Meaning |
| --- | --- |
| **Current Start (mA):** | Starting Current. |
| **Current Step (mA):** | Step Current. |
| **Total Steps:** | Number of test points. |
| **Step Interval (0.1s):** | Interval between each step. |

In the above example, the parameters are (0, 10, 100, 2), which means the measurement will start from 0mA, the step is 10mA, with 100 total steps (0, 10, 20….980, 990), and the time interval between steps is 0.2 seconds. For some loads, the time interval will affect the measurement, as the load might change its characteristics when the temperature changes, even under the same current.

Note that the "Current Start" can be set to a fixed current, such as 200mA, and set "Current Step" to 0 to testing the voltage drift of the load under constant current.

From Application software V3.2.0, there's one additional application tab called "Unison" is added for MA/CA modules, it allows user to combine multiple channels as ONE channel to get bigger driving current, e.g. for MA02 module, user might connect the LED+ of 2 channels together and LED- of 2 channels together to get 2A driving current. And similarly, with MA12/16, user can get up to 12/16A driving current. (Note: This is only possible with MA/CA modules which are with common-cathode design).

When user does the corresponding hardware wiring (tie the LED+/LED- of the channels together), user might Use the "Unison" tab to set Imax (which can be set to multiple of the channel Imax), Iset …etc.

*— Mightex Proprietary and Confidential · 2018-11-10 · 22 of 26 —*

---

The GUI of the Unison tab is as following:

> **[Figure: Unison tab]** — "Channel Group1" selector, Chl# Select checkboxes (Chl#1–Chl#16), Normal Mode Settings and Strobe Mode Settings panels, Current Mode Selection (DISABLE / NORMAL / STROBE), Set Current Mode. Status bar: `Sirius SLC-MA02-U_04-1112(`.

Note that user should first define the channels included in a certain channel group, there're 4 groups can be defined as maximum. A certain channel can only be included in one group, when a channel was selected for a certain group, it's "gray out" when user selects channels for another group.

After user defines channels for a group (e.g. user select Channel #1, #2, #3 and #4) for group1, user can use the group as ONE channel, e.g. the Imax can be set to 4A when there're 4 channels in the group.

The operation of Mode selection, Imax/Iset and Strobe settings of the group are the same as these controls of the single channel control in the main window…Note that when user does hardware wiring and select channels into a Unison group, user should control the parameters of these channels in this "Unison" tab as a group, it's not recommended for user to set driving parameters in the single channel settings in the main GUI.

*— Mightex Proprietary and Confidential · 2018-11-10 · 23 of 26 —*

---

## 3.0 Manual Mode of SLC-MA04/CA04-MU module

The SLC-MA04/CA04-MU module is a 4 channel LED driver with the ability to control the output of multiple channels manually with knobs, in addition to controlling outputs purely with a PC. This is known as Manual Mode and is specific to SLC-MA04/CA04-MU modules.

### 3.1 PC Mode and Manual Mode

**PC Mode:** When the LED Driver is in this mode, the Driver gets commands from the host via the USB port, and controls the channels' currents accordingly. All LED Drivers can work in this mode. The devices can also work without a host connected. In this case, the last stored parameters (via USB command) are automatically set for the output currents when the device is powered up.

**Manual Mode:** When the LED Driver is in this mode, the output current of each channel can be controlled via the manual knobs on the device. Only SLC-MA04/CA04-MU devices have such manual knobs and support this mode.

The SLC-MA04/CA04-MU module is always in **Manual Mode** when it is powered on, thus the output current can be controlled manually on power up and will stay in **Manual Mode** when there is no PC Host connected.

It will enter **PC Mode** when it gets an "ECHOON" or "ECHOOFF" command from the PC Host via USB port (please refer to the SDK manual for the command sets). For example, the "LEDDriver.exe" application sends an "ECHOOFF" command when the software starts, so when the "LEDDriver.exe" application runs, the connected device will enter **PC Mode** automatically. User generated software (based on the SDK) should do similarly by sending an "ECHOOFF" command to the MA04 module on start up.

### 3.2 Manual Nodes and LCD Display

The SLC-MA04/CA04-MU has additional hardware to support operations of Manual Mode, it has 5 turning knobs and one 4x16 LCD display.

> **[Figure: Top View and Bottom View of MA04/CA04 Module]** — Two 3D renderings labeled "Top View of MA04/CA04 Module" and "Bottom View of MA04/CA04 Module".

*— Mightex Proprietary and Confidential · 2018-11-10 · 24 of 26 —*

---

### 3.3 Fan Control

In addition to four LED channels, SLC-MA04/CA04-MU provides one motor driving interface (Fan+ and Fan-) for a 12V DC motor, the main purpose of this interface is for driving the 12V DC fan on some of Mightex's high power light source devices.

The fan speed can be controlled via the LEDDriver.exe software and can be set from speeds of 0 (Full Off) to 100% (Full On).

The speed level, called Fan PWM, can be set via the interface below, and the PWM level can be saved to the Non-Volatile memory of the device by clicking the button. The set PWM level will be remembered by the device and set to the saved level on the next power up.

> **[Figure: System Controls / Module Control]** — "Fan PWM (50%)" slider, "PowerUp On Manual Mode" checkbox, and "Store All Parameters To Module Eeprom" button.

**The Fan PWM Level control:** set from 0% to 100%

**Power Up Mode Control:** it is recommended to keep it checked. This will power up the device in **Manual Mode**.

Clicking this button will store all the settings (including the currents for all channels, PWM Level, power up mode…etc. into the device's NV memory, so the device will remember those settings during its next power up.

---

**Callouts for the front/side panel figures (page 25):**

*It has 5 knobs, the left most knob is a global node for controlling all 4 channels, and the following knobs (from left to right) are for channel 1 to 4. There is also a USB port on the right side.*

*There's a 4x16 LCD display which will show the currents of each channel when the module is in Manual Mode as:*

```
Chl1: xxxx (mA)
Chl2: xxxx (mA)
Chl3: xxxx (mA)
Chl4: xxxx (mA)
```

*It has 4 LED+/LED- for each channel, and there is an additional Motor+/- for DC Motor fan driving, the power plug is 12 – 24 DC input.*

*— Mightex Proprietary and Confidential · 2018-11-10 · 25 of 26 —*

---

### 3.4 Power Up Mode

Although it is recommended to set the MA/CA04 module in Manual Mode on power up, it is possible to set it to PC Mode when it is powered up. In order to do that, uncheck the "PowerUp On Manual Mode" check box and store the setting to the device.

**Note:** The device will be in PC mode after power up, and there will be no way to control the current manually via the knobs.

### 3.5 Steps to use MA04/CA04 device in Manual Mode

When initially receiving the SLC-MA04/CA04-MU device, the factory settings for each channel's I<sub>max</sub> (including I<sub>max</sub> for NORMAL mode and STROBE mode) are set to 20mA for the safety. The following steps must be performed:

**1).** Run "LEDDriver.exe" and set the proper I<sub>max</sub> in NORMAL mode of each channel, sending the parameters to the device. Set the I<sub>max</sub> according to the specific light source connected to each channel, e.g. set I<sub>max</sub> = 350mA for channel 1, I<sub>max</sub> = 500mA for channel 2, I<sub>max</sub> = 750mA for channel 3 and I<sub>max</sub> = 1200mA. These values can be found in the specification data of each individual LED.

> **[Figure: Manual Mode setup GUI]** — `Sirius SLC-MA04-MU :04-DEFAULT : Channel-1`, Normal Mode Settings (Maximum/Setting Current, 750mA / 10mA), Strobe Mode Settings, Parameters Setting Selection (Normal Setting checked), Set Parameters. With annotated callouts (see below).

**2).** Set a proper PWM level if driving a fan is needed for a certain light source.

**3).** Store the parameters (in the above (1) and (2) steps) by clicking the **Store All Parameters To Module Eeprom** button (refer to the above "3.3 Fan Control" section about the feature of this button)

**4).** Turn off the device and disconnect it from the PC. The next time the device is power on, it will be working in Manual Mode with I<sub>max</sub> set to the value stored on the device. The channels' output currents are in the range of 0 – I<sub>max</sub> (e.g. for channel 1, the current is from 0mA – 350mA); the actual output currents are as following:

```
Iout = Imax × Position of Global Node × Position of Channel Node.
```

Note that Position of a knob can be recognized as 0% – 100% from Left to Right positions, when it is in the middle position, it is 50%.

---

**Annotated callouts for the Manual Mode setup GUI figure (page 26):**

*Select channel here, for MA04 module, there are 4 channels.*

*Use this box to set the proper I<sub>max</sub> (for Normal Mode) of the selected channel according to the light source connected. It is recommended to set I<sub>set</sub> to a small number (e.g. 10mA).*

*Checking the "Normal Setting", and clicking the [Set Parameters] button will send the I<sub>max</sub> and I<sub>set</sub> (for Normal Mode only) parameters to the device.*

*Note: Proper I<sub>max</sub> values need to be set for all channels intended for use. Clicking the [Set Parameters] button sends the parameters to the device, but those parameters are NOT stored in the NV memory of device. In order to store them to the device, click the [Store…] button which is described below.*

*— Mightex Proprietary and Confidential · 2018-11-10 · 26 of 26 —*
