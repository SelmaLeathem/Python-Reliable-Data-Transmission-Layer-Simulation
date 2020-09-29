# Date:        5/1/2020
# Description: Code entry point for simulating reliable data transmission
#              over an unreliable channel.
#              The code was provided and has not been modified except to
#              set flags to introduce several types of unreliablity to
#              the underlying channel.

import time

from reliable_layer import *

# --- Main ---

# The strings that are sent over the unreliable channel

dataToSend = "\r\n\r\nAmerican Kennel Club -- Labradors \r\n\r\n" \
             "The sturdy, well-balanced Labrador Retriever can, " \
             "depending on " \
             "the " \
             "sex, stand from 21.5 to 24.5 inches at the shoulder and weigh " \
             "between " \
             "55 to 80 pounds. The dense, hard coat comes in yellow, black, " \
             "and a " \
             "luscious chocolate. The head is wide, the eyes glimmer with " \
             "kindliness, " \
             "and the thick, tapering “otter tail” seems to be forever " \
             "signaling the " \
             "breed’s innate eagerness." \
             "\r\n\r\n" \
             "Labs are famously friendly. They are companionable housemates " \
             "who  " \
             "bond with the whole family, and they socialize well with " \
             "neighbor dogs " \
             "and humans alike. But don’t mistake his easygoing personality " \
             "for low " \
             "energy: The Lab is an enthusiastic athlete that requires lots " \
             "of exercise, " \
             "like swimming and marathon games of fetch, to keep physically " \
             "and mentally fit." \
             "\r\n\r\n" \
             "American Kennel Club -- Pugs \r\n\r\n" \
             "The Pug’s motto is the Latin phrase ‘multum in parvo’ (a lot " \
             "in a little)—an apt description of " \
             "this small but muscular breed. They come in three colors: " \
             "silver or apricot-fawn with a black  " \
             "face mask, or all black. The large round head, the big, " \
             "sparkling eyes, and the wrinkled brow " \
             "give Pugs a range of human-like expressions—surprise, " \
             "happiness, curiosity—that have " \
             "delighted owners for centuries." \
             "\r\n\r\n" \
             "Pug owners say their breed is the ideal house dog. Pugs are " \
             "happy in the city or country, with " \
             "kids or old folks, as an only pet or in a pack. They enjoy " \
             "their food, and care must be taken to " \
             "keep them trim. They do best in moderate climates—not too hot, "\
             "not too cold—but, with proper " \
             "care, Pugs can be their adorable selves anywhere.\r\n"

client = ReliableLayer()
server = ReliableLayer()

# Start with a reliable channel (all flags false)
outOfOrder = True
dropPackets = True
delayPackets = True
dataErrors = True

clientToServerChannel = Channel(outOfOrder, dropPackets, delayPackets,
                                dataErrors)
serverToClientChannel = Channel(outOfOrder, dropPackets, delayPackets,
                                dataErrors)

client.set_send_channel(clientToServerChannel)
client.set_receive_channel(serverToClientChannel)

server.set_send_channel(serverToClientChannel)
server.set_receive_channel(clientToServerChannel)

client.set_data_to_send(dataToSend)

loopIter = 1
while True:
    client.manage()

    clientToServerChannel.manage()

    server.manage()

    serverToClientChannel.manage()

    # show the data received so far
    dataReceived = server.get_data_received()

    if dataReceived == dataToSend:
        print("\ndataReceived: {0}\n".format(dataReceived))
        print('$$$$$$$$ ALL DATA RECEIVED $$$$$$$$')
        break

    loopIter += 1

print("count_total_data_packets: {0}".format(clientToServerChannel.
                                             count_total_data_packets))
print("count_sent_packets: {0}".format(clientToServerChannel.
                                       count_sent_packets +
                                       serverToClientChannel.
                                       count_sent_packets))
print("count_checksum_error_packets: {0}".format(clientToServerChannel.
                                                 count_checksum_error_packets))
print("count_out_of_order_packets: {0}".format(clientToServerChannel.
                                               count_out_of_order_packets))
print("count_delayed_packets: {0}".format(clientToServerChannel.
                                          count_delayed_packets +
                                          serverToClientChannel.
                                          count_delayed_packets))
print("countDroppedDataPackets: {0}".format(clientToServerChannel.
                                            count_dropped_packets))
print("count_ack_packets: {0}".format(serverToClientChannel.count_ack_packets))
print("countDroppedAckPackets: {0}".format(serverToClientChannel.
                                           count_dropped_packets))

print("# segment timeouts: {0}".format(client.count_segment_timeouts))

print("TOTAL ITERATIONS: {0}".format(loopIter))

print("\n...exactus...\n")
