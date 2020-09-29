# Python Simulate a Reliable Transmission Layer on An Unreliable Channel

Developed a simulation of a reliable transmission layer on top of an unreliable channel similar to the transport layer in the internet protocol stack in Python. Features include: 

*  The number of packets sent are limited by the size of the flow control window. 
*  A cumulative ack is implemented by sending one acknowledgement per every FLOW_CONTROL_WIN_SIZE/DATA_LENGTH number of segments sent out. The value of the ACK number is the largest segment number of the group of packets plus the size of the payload. 
*  Pipelining is implemented by using a cumulative ack. Groups of packets are sent out before receiving an acknowledgement back. 
*  Selective retransmit is implemented by the server firstly sending an acknowledgement number reflecting the largest packet received without a gap in the data. The client in response resends all remaining packets at or above the acknowledgement number. This could mean anywhere from only one packet to the entire batch is resent. 
*  Timeouts are implemented as described in the book. When a timeout occurs, the packets are resent, and the timeout time is doubled. After the acknowledgement is received by the client the timeout period goes back to its default value of one roundtrip time. 

## Instructions

Run *main.py* with Python3.

## Run in Google Colaboratory

1. Vist https://colab.research.google.com/drive/177iCJ5qfdEHaIQOL4I_gNL4AJ3IH1l1d?usp=sharing
1. Select Runtime-> Factory reset runtime
1. Select Select Runtime-> Run all
