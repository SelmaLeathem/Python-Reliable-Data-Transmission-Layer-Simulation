# Date:        5/1/2020
# Description: Code implementation for the reliable data transport layer. The
#              book "Computer Networking a Top-Down Approach" by Kurose was
#              used to as reference to determine how to implement each feature.
#
# Features include:
#
# * The number of packets sent are limited by the size of the
# flow control window.
#
# * A cumulative ack is implemented by sending one acknowledgement per every
# FLOW_CTRL_WINDOW_SIZE/STRING_DATA_LENGTH number of segments sent out. The
# value of the ACK number is the largest segment number of the group of
# packets plus the size of the payload.
#
# * Pipelining is implemented by using a cumulative ack. Groups of packets
# are sent out before receiving an acknowledgement back.
#
# * Selective retransmit is implemented by the server firstly sending an
# acknowledgement number reflecting the largest packet received without a
# gap in the data. The client in response resends all remaining packets at
# or above the acknowledgement number. This could mean anywhere from only
# one packet to the entire batch is resent.
#
# * Timeouts are implemented as described in the book "Computer Networking A
# Top-Down Approach" by Kurose. When a timeout occurs the packets are resent
# and the timeout time is doubled. After the acknowledgement is received by
# the client the timeout period goes back to its default value of one
# roundtrip time.
#
# * One roundtrip time is equivalent to 2 iterations.

from unreliable_channel import *


class ReliableLayer(object):
    # The length of the string data that will be sent per packet...
    STRING_DATA_LENGTH = 4   # characters
    # Receive window size for flow-control
    FLOW_CTRL_WINDOW_SIZE = 15   # characters
    # The round trip time for a packet to arrive at the server and the
    # server to to send back an acknowledgment
    BASIC_RTT = 2
    # The maximum size of the time delay
    RTT_MAX = 4

    # Add class members as needed...
    #
    def __init__(self):
        self.send_channel = None
        self.receive_channel = None
        self.data_to_send = ''
        self.current_iteration = 0   # <--- Use this for segment 'timeouts'
        self.seqnum = 0  # the sequence number of a segment
        self.acknum = 0  # the acknowledgement number sent by the receiver
        # the cumulative size of the total data sent in # of chars
        self.size_of_data_sent = 0
        # holds the message received by the server
        self.message_received = ''
        # Holds the segment number and payload of each segment received by
        # the server when it receives a group of segments. This dictionary
        # is cleared out between "receive" events.
        self.segments_received = {}
        # When a group of segments arrive and there is a gap (eg a
        # dropped/delayed segment) then the packets that arrived are stored
        # in this dictionary
        self.segments_waiting = {}
        # The acknowledgment number the client expects to receive if the
        # segments arrive at the server without issues
        self.expected_ACK = 0
        # A flag used by the client to indicate whether or not it can send
        # data during that iteration. Note: the client does not send the
        # next batch of of segments until it has receieved acknowledgment
        # for the previously sent out batch
        self.turn_to_send = True
        # The value of the last received acknowledgment number sent by the
        # server
        self.last_good_server_acknum = 0
        # Used to indicate the iteration number that a batch of packets was
        # sent sent out on
        self.send_time = 0
        # A flag used to indicate if the client is resending segments
        self.are_resending = False
        # Indicates the timeout value
        self.rtt = self.BASIC_RTT
        # A counter that holds the number of segment timeouts
        self.count_segment_timeouts = 0

    # Called by main to set the unreliable sending lower-layer channel
    def set_send_channel(self, channel):
        self.send_channel = channel

    # Called by main to set the unreliable receiving lower-layer channel
    def set_receive_channel(self, channel):
        self.receive_channel = channel

    # Called by main to set the string data to send
    def set_data_to_send(self, data):
        self.data_to_send = data

    # Called by main to get the currently received and buffered string data,
    # in order
    def get_data_received(self):
        # Note: message Received is obtained with function:
        # add_data_received(self, data, segment_numbers)
        return self.message_received

    # "timeslice". Called by main once per iteration
    def manage(self):
        self.current_iteration += 1
        self.manage_send()
        self.manage_receive()

    # Manage Segment sending  tasks... If there is data to send the client
    # sends out FLOW_CTRL_WINDOW_SIZE/STRING_DATA_LENGTH number of segments.
    # If the client is resending segments then a special flag is set to
    # ensure the client only resends part or all of what they sent earlier.
    # If the client cannot send data segments because they are waiting for
    # an acknowledgment from the server for the previously sent segments
    # then the turn_to_send flag is turned off.
    #
    # Timeouts are implemented in this function. When a batch of segments
    # are sent the timer is started. If the turn_to_send flag is not turned
    # back on before the expected timeout then a timeout event occurs,
    # the turn_to_send flag is turned back on and part or all of the
    # segments are resent.
    def manage_send(self):
        # If there is no data to send then exit the function
        if self.data_to_send == '':
            return

        # Make sure the timeout interval does not go over RTT_MAX
        if (self.rtt > self.RTT_MAX):
            self.rtt = self.RTT_MAX

        # Check for a timeout. If there is a timeout the timeout period is
        # doubled and the resend flag is set to true. Also the
        # "turn_to_send" flag is turned on. Normally this flag is turned on
        # when the client receives an acknowledgment from the server
        if self.current_iteration - self.send_time >= \
                self.rtt and not self.turn_to_send:
            self.count_segment_timeouts += 1  # increment the number of
            # timeouts
            self.rtt *= 2  # double the timeout period
            self.turn_to_send = True  # turn on flag that says can send now
            self.are_resending = True  # turn on flag that says are resending
            # segments

        # If the client has not received an acknowlegement for the last
        # segments sent then this flag prevents more segments going out
        if not self.turn_to_send:
            return

        # Set the current segment sequence number to the last received
        # acknowledgement number sent by the server
        self.seqnum = self.last_good_server_acknum

        # Check for missing segments. If the cumulative size of the number
        # of chars sent so far is larger than the last acknowledgment number
        # received from the server then then decrease its value so it
        # accurately represents the amount of data sent
        if self.size_of_data_sent > self.last_good_server_acknum:
            self.size_of_data_sent = self.last_good_server_acknum
            self.are_resending = True  # if the server acknum <
            # size_of_data_sent then need to resend
        else:  # make sure the are_resending flag is turned off
            self.are_resending = False

        # If the expected acknum was received ensure that the timeout period
        # is reset to its default value
        if self.expected_ACK == self.last_good_server_acknum:
            self.rtt = self.BASIC_RTT

        # holds the size of the each segment sent as the number of chars
        payloadSize = 0

        # Keep sending segments until have sent an amount of data that is <=
        # FLOW_CTRL_WINDOW_SIZE
        while True:

            # current seqnum size = (last seqnum value) + (size of last
            # payload sent)
            self.seqnum += payloadSize

            # pull out a chunk of data from the send string of size
            # STRING_DATA_LENGTH to send in a segment resource:
            # https://www.geeksforgeeks.org/python-get-the-substring-from
            # -given-string-using-list-slicing/
            data = self.data_to_send[self.seqnum: self.seqnum +
                                     self.STRING_DATA_LENGTH]

            # get the payload size of the data
            payloadSize = len(data)

            # if the payload size is zero then have nothing to send so exit
            # the function
            if (payloadSize == 0):
                break

            # if the next data chunk does not fit into the flow-control
            # window size then exit
            if ((self.size_of_data_sent + payloadSize -
                 self.last_good_server_acknum) > self.FLOW_CTRL_WINDOW_SIZE):
                break

            # if are resending then only send what previously sent before
            if self.are_resending:
                # if the size of the sent data is such that it is equal to
                # expected acknum -1 then exit
                if (self.size_of_data_sent + payloadSize) > self.expected_ACK:
                    self.are_resending = False
                    break

            # if all of the above conditions are satisfied then the last
            # chunk of data to be pulled will be sent and is therefore
            # counted in the size_of_data_sent variable
            self.size_of_data_sent += payloadSize

            # send the data chunk by using a Segment class object
            seg = Segment()
            seg.set_data(self.seqnum, data)  # set the data and sequence
            # number of the segment
            # seg.dump() prints state values to screen
            # Use the unreliable send_channel to send the segment
            self.send_channel.send(seg)

        # start monitoring the time for catching timeouts
        self.send_time = self.current_iteration

        # set the expected acknum to be returned by the server
        self.expected_ACK = self.size_of_data_sent

        # turn off the turn_to_send flag, so another batch of segments can't
        # be sent until either an acknum is received for the last batch of
        # segments or a timeout occurs
        self.turn_to_send = False

    # Manage Segment receive  tasks...
    # Most of error checking is done in the receive function, such as checking
    # for packets out of order, missing packets and checksum checks.
    #
    # All incoming packets are pulled from the unreliable channel into a
    # list. If the elements in the list pass the checksum checks then they
    # are added to the dictionary segments_received as segments_received[
    # seqnum] = payload. This dictionary is then sorted according to seqnum
    # and checked to see if any sequence numbers are missing. If packets are
    # missing then these are moved to a segments_waiting dictionary. Note
    # that segments_received is cleared after every iteration. When in
    # future iterations more packets arrive these waiting segments are then
    # moved to the segments_received dictionary and if there are no gaps the
    # payload contents of segments_received are added to the dataReceived
    # string and an acknum is generated and sent to the client
    def manage_receive(self):
        # get a list of the incoming segments from the unreliable channel
        list_incoming = self.receive_channel.receive()

        # if the list is not empty then process it
        if len(list_incoming) > 0:

            # holds the segments numbers that have arrived in the latest
            # receive
            segment_numbers = []

            # go through each segment that has arrived to determine errors
            # and whether or not the segment is an acknum
            for item in list_incoming:

                # do a checksum check on the received packets
                check_checksum_result = self.perform_checksum_check(item)

                # if the packet passes the checksum test then process it
                if check_checksum_result:

                    # variables used to add packet to dictionary[item_seq_num]
                    # = payload
                    word = item.payload
                    item_seq_num = item.seq_num

                    # if the packet is an ack number then ensure the sender
                    # retrieves it and then exit the function.
                    if item_seq_num >= self.acknum or item_seq_num == -1:
                        if item_seq_num == -1:
                            # store the new ack number in the
                            # last_good_server_acknum
                            self.last_good_server_acknum = item.ack_num

                            # set the "can send" flag for the send function
                            # since the ACK has been received
                            self.turn_to_send = True
                            return

                        # store the segment numbers in a list
                        segment_numbers.append(item_seq_num)

                        # add the packet to the segments_received dictionary
                        self.segments_received[item_seq_num] = word

            # if there are packets waiting in the segments_waiting
            # dictionary then move these to the segments_received dictionary
            if len(self.segments_waiting) > 0:
                for key in self.segments_waiting.keys():
                    segment_numbers.append(key)
                    # duplicates are not allowed in dictionaries so there
                    # should be only one of each packet listed
                    self.segments_received[key] = self.segments_waiting[key]
                self.segments_waiting.clear()  # clear the dictionary

            # if after some initial processing there are elements in the
            # segments_received dictionary then check for missing segments
            # and if there are none add the payloads to the receiveString
            # otherwise move the segments to the segments_waiting dictionary
            if len(self.segments_received) > 0:

                # remove duplicate segnums from list reference:
                # https://www.w3schools.com/python
                # /python_howto_remove_duplicates.asp
                segment_numbers = list(dict.fromkeys(segment_numbers))

                # check for missing segments. If there are missing segments
                # the flag missingSegments is true. Regardless of missing
                # segments or not the acknum is set to be the value of the
                # largest in order segment+payload before any potential gaps.
                missing_segments, self.acknum = \
                    self.verify_segment_numbers(segment_numbers,
                                                self.segments_received)

                # if there are no missing segments then add the payloads to
                # the receive string
                if not missing_segments:
                    self.acknum = \
                        self.add_data_received(self.segments_received,
                                               segment_numbers)
                else:  # if there are missing segments then add them to the
                    # segments_waiting dictionary
                    self.add_data_waiting(self.segments_received,
                                          segment_numbers)

                self.segments_received.clear()  # clear the dictionary

            # send the acknum by making a segment object and sending that
            # down the unreliable channel
            ack = Segment()
            ack.set_ack(self.acknum)  # set the value of acknum
            # ack.dump() prints state values to screen
            # Use the unreliable send_channel to send the ack packet
            self.send_channel.send(ack)

    # Verify that there are no missing segments by looking for gaps in the
    # segment numbers. input: a list of segment numbers a dictionary of the
    # form dict[segnum] = payload output: a boolean that is true if there
    # are segments missing the acknum for the last segment before any
    # missing segments
    def verify_segment_numbers(self, segment_numbers, data):
        segment_missing = False  # true if segment missing

        length = len(segment_numbers)  # size of list

        # reference: https://www.w3schools.com/python/ref_list_sort.asp
        segment_numbers.sort()  # sort the segment numbers

        # if the first or only segment number is greater than the ACK number
        # then there is at least one segment missing at the beginning
        if segment_numbers[0] > self.acknum:
            return True, self.acknum

        # if there is only one segment in the list and it satisfies the above
        # condition then by default nothing is missing
        i = 0
        if length == 1:
            num_index = segment_numbers[i]
            # acknum= segnum + payload size
            last_valid_ack = segment_numbers[i] + len(data[num_index])
            return False, last_valid_ack  # exit the function

        # for list sizes > 1 check to see if there is a gap between segment
        # numbers
        for i in range(length - 1):
            num_index = segment_numbers[i]
            if (segment_numbers[i + 1] - segment_numbers[i]) > \
                    len(data[num_index]):
                # there is a gap between segment number so the acknum is
                # that of the last valid segment number before the gap occurs
                last_valid_ack = segment_numbers[i] + len(data[num_index])
                return True, last_valid_ack  # exit the function

        # if reach this point without exiting then unless the list was size
        # 1 there are no gaps or missing segments
        i = length - 1
        num_index = segment_numbers[i]

        # acknum= segnum + payload size
        last_valid_ack = segment_numbers[i] + len(data[num_index])

        # resource: https://www.geeksforgeeks.org/g-fact-41-multiple-return
        # -values-in-python/
        return segment_missing, last_valid_ack

    # Adds validated data received to the dataReceived string.
    # input: a list of segment numbers
    #        a dictionary of the form dict[segnum] = payload
    # output: the latest acknum value
    def add_data_received(self, data, segment_numbers):
        segment_numbers.sort()  # sort the segnums to ensure adding the
        # payloads in the correct order

        next_num = segment_numbers[0]  # initialize next_num

        for i in range(len(data)):
            next_num = segment_numbers[i]
            self.message_received += data[next_num]  # concatenated the next
            # payload string

        return next_num + len(data[next_num])  # return last segment number +
        # segment size = new ack #

    # Performs a checksum check of an element in the list returned from the
    # unreliable's channel receive() function. input: a list element
    # returned from the unreliable.py receive function output: true if the
    # checksum is valid
    def perform_checksum_check(self, item):
        seg = Segment()
        seg.checksum = item.checksum
        seg.seq_num = item.seq_num
        seg.ack_num = item.ack_num
        seg.payload = item.payload
        return seg.check_checksum()

    # Add dictionary data to the segments_waiting dictionary.
    # input: a dictionary of the form dict[segnum] = payload
    #        a list of segment numbers
    def add_data_waiting(self, data, segment_numbers):
        for i in range(len(segment_numbers)):
            nextNum = segment_numbers[i]
            self.segments_waiting[nextNum] = data[nextNum]
