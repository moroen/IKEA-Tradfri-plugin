# Synology NAS
These instructions assume that you already have SSH access to your Synology NAS. To enable SSH access to your Synology NAS do a Google search, there are many instructions regarding this subject.

To install the Tradfri plugin on a Synology NAS, follow these steps:

## 1. Requirements

### Python
Make sure that you have installed Python3 on your Synology NAS. You can find the Python3 package in the DSM Package Manager

### Git
Make sure that you have installed Git on your Synology NAS. You can find the Git package in the ‘Community’ section of the DSM Package Manager

### Golang
Open a SSH connection to your Synology NAS and execute the following command on the command line: 
```
uname -m
```
Make a note of the result. This value indicates what type of architecture the CPU in your Synology NAS uses, you need this value to find the correct ‘Go’ version for your NAS

Go to https://golang.org/dl/ and download the correct Go version for your CPU architecture, save it in an easy to find location on your NAS. I recommend using the DSM ‘File Station’ application to upload it to your Synology home folder. If you can’t find the exact version for your CPU architecture, a lower version will probably work to. ARMv6, for instance, works fine for ARMv7l CPU

On the NAS command line go to your home directory by executing this command: 
```
cd $HOME
``` 
Use the command ‘ll’ (double l) to see a list of files in your home folder, the Go installation file should be in the file list

Follow the Go installation instructions here https://golang.org/doc/install

When Go is successfully installed, go to step 1 of the IKEA-Tradfri plugin [installation instructions](README.md), skip step 2 (you don’t need PIP) and then proceed to step 3b and follow the rest of the instructions

## 3. Restart domoticz
Restart Domoticz through the DSM Package Manager (Stop it, that start it)

You should now see the Tradfri plugin in the Hardware section of Domoticz, where you can add it and configure it.