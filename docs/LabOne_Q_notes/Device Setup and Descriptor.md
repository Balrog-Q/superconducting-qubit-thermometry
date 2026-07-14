---
tags:
  - laboneq
---
#laboneq
# Device Setup
## `DeviceSetup` Class
The `DeviceSetup` class takes information about instruments, their physical ports, and [[Logical and Experimental Signals|logical signal lines]] - all written in a `descriptor`. It also takes the data server address and port number and a user-defined name, as shown in this example:
```Python
device_setup = DeviceSetup.from_descriptor(
	descriptor,
	server_host="111.22.33.44",
	server_port="8004",
	setup_name="ZI_QCCS",
)
```
With the device setup object, experimental parameters are pushed, through calibration, to instruments. Additionally, `DeviceSetup` is used when connecting to a Session. The Session takes all of the information of the device setup and connects the setup to independently defined experiments at compilation. In this way, multiple device setups can be defined and used without the need to rewrite experiments.
## Descriptor
A typical Quantum Computing Control System (QCCS) consists of a central controller, which connects to a number of instruments for qubit control and qubit readout. The `descriptor` breaks down information about a setup into the necessary pieces to run experiments explained in detail in the below examples. It contains:
- A list of the type of instruments to be used in the experiment
	- The instrument serial numbers
	- User-defined ids for each instrument
 - The connection properties of the instrument
	 - Signal types
	 - Logical signal lines
	 - Physical ports
	 - Other connection options
- (Optional) Information on the LabOne data servers used to connect to the instruments
	- Data server id
	- IP address of the data server
	- Port number under which the data server can be reached
	- A list of instruments this data server is connected to
See also the options table for the device descriptor. Descriptors can either be defined within the experiment notebook as a YAML formatted string or they can be in a separate YAML file. The latter is often useful so that multiple device setups can be quickly swapped in and out. To use a separate file, the device setup definition will be:
```Python
descriptor_file = "./my_descriptor.yml"

device_setup = DeviceSetup.from_YAML(
	filepath = descriptor_file,
	server_host="111.22.33.44",
	server_port="8004",
	setup_name="MY_SETUP",
)
```
If the `server_host` and `server_port` arguments are given when calling the `from_descriptor` or `from_YAML` method, they will overwrite any definitions present already in the descriptor itself.
Additional electronics may be parts of the setup, such as DC sources or radio-frequency signal generators. These are not included in the descriptor since LabOne Q does not provide drivers for these instruments. Nevertheless, LabOne Q provides an interface to control such instruments in the normal workflow via user-friendly callback functions.
## Sampling Rates
The sampling rate of the instruments in the setup depends on the setup composition:
- HDAWG + UHFQA: The HDAWG runs at 2.4 GSa/s, while the UHFQA runs at 1.8 GSa/s.
- HDAWG + SHF instruments: All instruments run at 2 GSa/s.
- A combination of HDAWG, SHF instruments and UHFQA is not supported.
## Setup with PQSC, HDAWG and UHFQA
The first kind of typical setup comprises one PQSC (for system synchronizstion), one HDAWG (for qubit control) and one UHFQA (for qubit readout). The descriptor for defining such a setup looks as follows, here additionally including information on the data-server.
```Python
descriptor = """\
dataservers: 
	my_qccs_system: 
		host: 127.0.0.1 
		port: 8004 
		instruments: [device_hdawg, device_uhfqa, device_pqsc] 
	instruments: 
		HDAWG: 
		- address: DEV8000 
		  uid: device_hdawg 
		UHFQA: 
		- address: DEV2000 
		  uid: device_uhfqa 
		PQSC: 
		- address: DEV10000 
		  uid: device_pqsc 
	connections: 
		device_hdawg: 
			- iq_signal: q0/drive_line 
			  ports: [SIGOUTS/0, SIGOUTS/1] 
			- rf_signal: q0/flux_line 
			  ports: [SIGOUTS/2] 
			- to: device_uhfqa 
			  port: DIOS/0 
		device_uhfqa: 
			- iq_signal: q0/measure_line 
			  ports: [SIGOUTS/0, SIGOUTS/1] 
			- acquire_signal: q0/acquire_line 
"""
```
The first part of the descriptor lists all instruments that are part of the setup, together with their type (e.g., HDAWG), address (the serial number of the instrument), and unique identifier ('uid), e.g., device_hdawg).
The second part of the descriptor contains information about the connections of the instruments. Connections from the instrument to the experimental setup (the cryostat) require the definition of the signal line type followed by the name of the logicala signal line and the used ports. The available signal types vary between different instrument types and are summarised in the table below. For connections between instruments, the keyword 'to' is used, followed by the unique ID of the connected instrument and the used port.
> [!Note]
> The port numbering in the software is zero-based, while the numbering on the instrument panels is one-based.

> [!Note]
> A common pitfall is a mismatching ZSync port assignment on the PQSC. If the specified port and instrument pairs in the descriptor do not match the actual step configuration, the software will return an error.

Available signal line types in the descriptor for PQSC, HDAWG and UHFQA instruments. The amount of ports on the HDAWG depends on the instrument version (e.g., 4-versus 8-channel version). Note that `ig_signals` are described by a port pair.

| Instrument     | signal type             | ports                               | description                                                     |
| -------------- | ----------------------- | ----------------------------------- | --------------------------------------------------------------- |
| SHFSG          | iq_signal, rf_signal    | SGCHANNELS/{0…​7}/OUTPUT            | Signal outputs for (modulated) IQ and (unmodulated) RF signals. |
| SHFQA          | iq_signal               | QACHANNELS/{0…​3}/OUTPUT            | Signal output for readout pulses.                               |
| acquire_signal | QACHANNELS/{0…​3}/INPUT | Input signals for data acquisition. |                                                                 |
| SHFQC          | iq_signal, rf_signal    | SGCHANNELS/{0…​7}/OUTPUT            | Signal outputs for (modulated) IQ and (unmodulated) RF signals. |
| iq_signal      | QACHANNELS/0/OUTPUT     | Signal output for readout pulses.   |                                                                 |
| acquire_signal | QACHANNELS/0/INPUT      | Input signals for data acquisition. |                                                                 |

### Additional Descriptor Keywords
Besides the information described above, the descriptor accepts additional keywords which allow to further customize the setup.

|Instrument|section|keyword|description|
|---|---|---|---|
|PQSC|connections|internal_clock_signal|Switches the reference clock to internal mode. Only available in setups without UHFQA.|
|HDAWG|connections|external_clock_signal|Switches the reference clock to external mode. Only available for a standalone HDAWG (plus non-QCCS instruments), where otherwise the default is the internal reference clock (see example descriptor below).|
|UHFQA|connections|external_clock_signal|Switches the reference clock to external mode. Only available for small setups, where otherwise the default is the internal reference clock.|

Additional keywords that are accepted by the descriptor in order to customize the setup beyond the default configuration.
### Connecting to Instruments via USB
Although LabOne and LabOne Q are optimised to communicate with our instruments via Ethernet, it is possible to use the USB connection. In this case, the `interface` property must be set in the descriptor, for example:
```Python
descriptor = """\
instruments:
	SHFQC:
	- address: DEV12000
	  uid: device_shfsg
	  interface: usb
connections:
	...
"""
```

## Setting up a Small System
LabOne Q supports setups without PQSC, which can contain at most one HDAWG and (optionally) one UHFQA. Such systems are termed 'small system'. This section explains how a small system can be set up using the descriptor.
>[!Note]
>For systems containing more than one HDAWG, a PQSC is inevitable in order to guarantee synchronisation of all signal outputs.

As before, the descriptor is used in order to define a small setup. LabOne Q compiler automatically detects a small system and configures the instruments accordingly, in particular the HDAWG is configured as leader.
### Setup with Single HDAWG and Single UHFQA
Similarly to device setups containing a PQSC, the descriptor contains information about the instruments, the connections and the logical signal lines. All available keywords for e.g. signal types stay the same. An example descriptor for a small system is as follows:

```Python
descriptor_small_system = """\ 
instruments:   
	HDAWG:   
	- address: DEV8000     
	  uid: device_hdawg   
	UHFQA:   
	- address: DEV2000     
	  uid: device_uhfqa 
connections:   
	device_hdawg:     
	- iq_signal: q0/drive_line       
	  ports: [SIGOUTS/0, SIGOUTS/1]     
	- to: device_uhfqa       
	  port: DIOS/0   
	device_uhfqa:     
	- iq_signal: q0/measure_line       
	  ports: [SIGOUTS/0, SIGOUTS/1]     
	- acquire_signal: q0/acquire_line     
	## optional: use external 10 MHz reference clock     
	- external_clock_signal 
"""
```

For instrument synchronisation, the 10 MHz reference clock of the UHFQA is connected to the HDAWG as shown in [Figure 1](https://docs.zhinst.com/labone_q_user_manual/core/functionality_and_concepts/00_device_setup/concepts/index.html#fig_qccs_small_setup_connections). The reference clock output at the back of the UHFQA is connected to both the reference clock input (backpanel) and trigger input 1 (frontpanel) of the HDAWG. An external 10 MHz reference clock can be used for the UHFQA by adding the `external_clock_signal` keyword to the descriptor.

[![](https://docs.zhinst.com/labone_q_user_manual/core/assets/images/getting_started/labone_q_software_small_setup.svg)](https://docs.zhinst.com/labone_q_user_manual/core/assets/images/getting_started/labone_q_software_small_setup.svg)

Figure 1: Connecting the 10 MHz reference clock to the instruments in a small setup without PQSC.

### Setup with Single HDAWG

The smallest setup which is supported by LabOne Q is a standalone HDAWG. The descriptor for such a system is built up in the same way as before:

```Python
descriptor_single_hdawg = """\ 
instruments:   
	HDAWG:   
	- address: DEV8000     
	  uid: device_hdawg 
connections:   
	device_hdawg:     
	- iq_signal: q0/drive_line       
	  ports: [SIGOUTS/0, SIGOUTS/1]     
	- rf_signal: q0/flux_line       
	  ports: [SIGOUTS/2]     
	  ## optional: use external 10 MHz reference clock     
	- external_clock_signal 
"""
```

In such a setup, we can choose if the HDAWG uses its internal reference clock or if it synchronizes with an external 10 MHz reference clock (e.g., in order to synchronize with a lock-in amplifier for readout). The first case is the default configuration. In the second case the external reference signal is connected in the same way as shown in the previous [figure](https://docs.zhinst.com/labone_q_user_manual/core/functionality_and_concepts/00_device_setup/concepts/index.html#fig_qccs_small_setup_connections). Both the reference clock input at the back of the HDAWG as well as the 'Trig In 1' at the front of the instrument are connected to the external reference clock. In the descriptor, another line with the keyword 'external_clock_signal' is added to the descriptor.