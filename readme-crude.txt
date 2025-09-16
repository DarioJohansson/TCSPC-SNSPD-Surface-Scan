I have a little discussion i want you to format nicely in markdown:

 Imaging software:
 this repo contains all the executable code which the project needs except for a few dependencies.
 install latest python and make sure to have this series of dependencies installed into your virtual environment. 
 {make a small tutorial of how to create a venv in windows.}

 the dependency list: 
 blinker 1.9.0 
 build 1.2.2.post1 
 click 8.2.1 
 colorama 0.4.6 
 itsdangerous 2.2.0 
 Jinja2 3.1.6 
 MarkupSafe 3.0.2 
 packaging 25.0 
 pip 25.2 
 pyproject_hooks 1.2.0 
 pyzmq 27.0.1 
 setuptools 80.9.0 
 Werkzeug 3.1.3 
 zmq 0.0.0 
 
 
 now i will explain how the folder structure is, it's in the picture.
 in devices lie these scripts second picture in scans third picture in utils some redistributed code from IDQuantique hardware vendors
 which manage connections contexts and data exchange functionalities via zmq to the IDQ devices.
 All the devices were possible to connect via IP and ethernet capabilities, 
 avoiding serial, USB or other out of plane data transfer buses and improving keeping track f the device connection statuses.
 
 for the montana cryoadvance 50, the code is mostly based on https RESTful API 
 so it's modern, simple, uses unified ethernet for behaving like a modern IP device and has webservers
 with data panels and script interaction endpoints. 
 
 leave a mark to make some space for explanations of the code in the devices/ folder.
 
 for the IDQ the hardware is more precise and the devices have less processing power so they use zero message queue zmq
 to transfer data under the shape of formatted text strings in {tcp or udp?} protocol, always under IP. 
 
 leave a mark to make space for an image of the network layout of the components