# USAFA ECE cUAS Capstone GUI

#### 2024-'25 authors: Geoffrey Stentiford and Jimmy Nguyen

This repository contains the GUI application for monitoring drone locations. It is meant to be run in conjunction with C3Mission. Specifically, it must run on the **same computer**, as IPC occurs over a UNIX socket.

## Installation

First, install requirements. A virtual environment is recommended but not required.

`pip install -r requirements.txt`

GTK4 libraries must be installed on the host system, although this shouldn't be an issue on any modern Linux distro. New Ubuntu installs should have it mostly set up out of the box.

## Usage

To run:  
`python gui.py`

To start the IPC client in standalone mode for testing:  
`python client.py`

C3Mission needs to be running in order for the GUI to have data to display. For information on how it talks to C3Mission, see [the `data_bridge` documentation](https://github.com/DFEC-cUAS/cuas_main/blob/main/agent_core/data_bridge.md).

## Development

You'll probably want to install `pygobject-stubs` to make dealing with GTK and GDK more pleasant in VSCode:  

`pip install pygobject-stubs --no-cache-dir --config-settings=config=Gtk4,Gdk4`

## `gui.py` Internals

Upon starting the script, the following happens:
- Absolute paths to the `assets` and `logs` folders are found and stored
- The icons of the discovery drone and rogue drones are preloaded and scaled
- The map is preloaded and copied into a `Pixbuf` which is also cached
- IPC client is started
- Main window is created and populated
- Periodic trigger to refresh the map with data is set up

Repainting is triggered by a timer running on a separate thread of the main process, although the actual repainting still occurs in the main thread. To avoid unnecessary repaints, repainting is skipped if no new data have arrived since the last repaint. This is determined by comparing the timestamp of the data used in the previous repaint to the timestamp of the current data.

To improve repaint performance, a lot of caching is used. On the first map update, a clean copy of the map is pulled and all data points up until the second-to-last pairs on both the discovery and rogue drone are plotted (using dots). Then, the map in this state is copied and stored for later, and the last pair of locations are plotted (using drone icons).

On each subsequent repaint, the copy of the map with dots but no drone icons is pulled, the new second-to-last points are plotted with dots, and the last points are again plotted with drone icons. This caching means that instead of replotting every point on each update, only the two most recent locations are painted.

Plotting points and icons is all done in Pillow. To render the output, however, it is converted to a `Pixbuf`. When the map is cleared, the cached clean `Pixbuf` copy of the map is directly used, avoiding the conversion from Pillow to Pixbuf in that case.

## `client.py` Internals

The IPC client, provided by `client.py`, spins up a child process to handle communication with AgentCore. If it cannot connect on the socket, it retries every 250 milliseconds.

The client may be run directly for debugging purposes, in which case it simply prints out whatever data is receives. It expects data in structured JSON:

```javascript
{
    [disco_lat, disco_long, disco_abs_alt, disco_rel_alt, disco_hdg],
    [rogue_lat, rogue_long, rogue_abs_alt, rogue_rel_alt, rogue_hdg],
    unix_time,
    disco_state
}
```

This is represented in Python as:
```python
Tuple[List[float], List[float], float, int]
```

The data are extracted and stored into `Synchronized` values and `SynchronizedArray`s. Outside of the child process, the coordinate values are appended to two lists containing all previous locations of the drones. The GUI accesses these values using API calls listed below.

## Client API

```python
# Starts the client:
client.start()
return = None

# Stops the client:
client.stop()
return = None

# Returns discovery and rogue drone coordinate history as a pair of parallel lists:
client.getVals()
return = (List[Tuple[float, float]], List[Tuple[float, float]])

# Clears coordinate history of drones:
client.clearVals()
return = None

# Check if client is connected to AgentCore:
client.isConnected()
return = bool

# Get timestamp of last data update:
client.getTimestamp()
return = float

# Get mode of discovery drone:
client.getMode()
return = int
```

There exist other calls you could, in theory, make, but they are designed to be used internally within `client.py` only.