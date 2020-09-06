#################################################################################
# Date:        5/1/2020
# Description: Code implementation for the reliable data transport layer. The
#              book "Computer Networking a Top-Down Approach" by Kurose was
#              used to as reference to determine how to implement each feature.
#
#               Features include:
#
#               * The number of packets sent are limited by the size of the
#                 flow control window.
#
#               * A cumulative ack is implemented by sending one acknowledgement
#                 per every FLOW_CONTROL_WIN_SIZE/DATA_LENGTH number of segments
#                 sent out. The value of the ACK number is the largest segment
#                 number of the group of packets plus the size of the payload.
#
#               * Pipelining is implemented by using a cumulative ack. Groups of
#                 packets are sent out before receiving an acknowledgement back.
#
#               * Selective retransmit is implemented by the server firstly
#                 sending an acknowledgement number reflecting the largest
#                 packet received without a gap in the data. The client in
#                 response resends all remaining packets at or above the
#                 acknowledgement number. This could mean anywhere from only one
#                 packet to the entire batch is resent.
#
#               * Timeouts are implemented as described in the book "Computer
#                 Networking A Top-Down Approach" by Kurose. When a timeout occurs
#                 the packets are resent and the timeout time is doubled. After
#                 the acknowledgement is received by the client the timeout period
#                 goes back to its default value of one roundtrip time.
#
#                * One roundtrip time is equivalent to 2 iterations.
#
##################################################################################
from unreliable import *


class RDTLayer(object):
    # The length of the string data that will be sent per packet...
    DATA_LENGTH = 4 # characters
    # Receive window size for flow-control
    FLOW_CONTROL_WIN_SIZE = 15 # characters
    # The round trip time for a packet to arrive at the server and the server to
    # to send back an acknowledgment
    BASIC_RTT = 2
    # The maximum size of the time delay
    RTT_MAX = 4


    # Add class members as needed...
    #
    def __init__(self):
        self.sendChannel = None
        self.receiveChannel = None
        self.dataToSend = ''
        self.currentIteration = 0 # <--- Use this for segment 'timeouts'
        #print('Complete this...in RDT layer constructor')
        self.seqnum = 0  # the sequence number of a segment
        self.acknum = 0  # the acknowledgement number sent by the receiver
        # the cumulative size of the total data sent in # of chars
        self.sizeOfDataSent = 0
        # holds the message received by the server
        self.messageReceived = ''
        # Holds the segment number and payload of each segment received by the server
        # when it receives a group of segments. This dictionary is cleared out between
        # "receive" events.
        self.segmentsReceived = {}
        # When a group of segments arrive and there is a gap (eg a dropped/delayed
        # segment) then the packets that arrived are stored in this dictionary
        self.segmentsWaiting = {}
        # The acknowledgment number the client expects to receive if the segments
        # arrive at the server without issues
        self.expectedACK = 0
        # A flag used by the client to indicate whether or not it can send data
        # during that iteration. Note: the client does not send the next batch of
        # of segments until it has receieved acknowledgment for the previously
        # sent out batch
        self.turnToSend= True
        # The value of the last received acknowledgment number sent by the server
        self.lastGoodServerAcknum = 0
        # Used to indicate the iteration number that a batch of packets was sent
        # sent out on
        self.sendTime = 0
        # A flag used to indicate if the client is resending segments
        self.areResending = False
        # Indicates the timeout value
        self.rtt = self.BASIC_RTT
        # A counter that holds the number of segment timeouts
        self.countSegmentTimeouts = 0


    # Called by main to set the unreliable sending lower-layer channel
    def setSendChannel(self, channel):
        self.sendChannel = channel

    # Called by main to set the unreliable receiving lower-layer channel
    def setReceiveChannel(self, channel):
        self.receiveChannel = channel

    # Called by main to set the string data to send
    def setDataToSend(self,data):
        self.dataToSend = data

    # Called by main to get the currently received and buffered string data, in order
    def getDataReceived(self):
        #print('Complete this... in getDataReceived')

        # Note: message Received is obtained with function: add_data_received(self, data, segment_numbers)
        return self.messageReceived

    # "timeslice". Called by main once per iteration
    def manage(self):
        self.currentIteration += 1
        self.manageSend()
        self.manageReceive()

    # Manage Segment sending  tasks...
    # If there is data to send the client sends out FLOW_CONTROL_WIN_SIZE/DATA_LENGTH
    # number of segments. If the client is resending segments then a special flag is
    # set to ensure the client only resends part or all of what they sent earlier.
    # If the client cannot send data segments because they are waiting for an
    # acknowledgment from the server for the previously sent segments then the
    # turnToSend flag is turned off.
    #
    # Timeouts are implemented in this function. When a batch of segments are sent
    # the timer is started. If the turnToSend flag is not turned back on before the
    # expected timeout then a timeout event occurs, the turnToSend flag is turned back
    # on and part or all of the segments are resent.
    def manageSend(self):
        #print('Complete this... in manageSend')

        # If there is no data to send then exit the function
        if self.dataToSend == '':
            return

        # Make sure the timeout interval does not go over RTT_MAX
        if (self.rtt > self.RTT_MAX):
            self.rtt = self.RTT_MAX

        # Check for a timeout. If there is a timeout the timeout period is doubled
        # and the resend flag is set to true. Also the "turnToSend" flag is turned
        # on. Normally this flag is turned on when the client receives an acknowledgment
        # from the server
        if (self.currentIteration - self.sendTime >= self.rtt and self.turnToSend == False):
            self.countSegmentTimeouts += 1 # increment the number of timeouts
            self.rtt *= 2 # double the timeout period
            self.turnToSend = True # turn on flag that says can send now
            self.areResending = True # turn on flag that says are resending segments

        # If the client has not received an acknowlegement for the last segments sent then
        # this flag prevents more segments going out
        if (self.turnToSend == False):
            return

        # Set the current segment sequence number to the last received acknowledgement number
        # sent by the server
        self.seqnum = self.lastGoodServerAcknum

        # Check for missing segments. If the cumulative size of the number of chars sent so
        # far is larger than the last acknowledgment number received from the server then
        # then decrease its value so it accurately represents the amount of data sent
        if (self.sizeOfDataSent > self.lastGoodServerAcknum):
            self.sizeOfDataSent = self.lastGoodServerAcknum
            self.areResending = True  # if the server acknum < sizeOfDataSent then need to resend
        else: # make sure the areResending flag is turned off
            self.areResending = False

        # If the expected acknum was received ensure that the timeout period is reset to its
        # default value
        if (self.expectedACK == self.lastGoodServerAcknum):
            self.rtt = self.BASIC_RTT

        # holds the size of the each segment sent as the number of chars
        payloadSize = 0

        # Keep sending segments until have sent an amount of data that is <= FLOW_CONTROL_WIN_SIZE
        while True:

            # current seqnum size = (last seqnum value) + (size of last payload sent)
            self.seqnum += payloadSize

            # pull out a chunk of data from the send string of size DATA_LENGTH to send in
            # a segment
            # resource: https://www.geeksforgeeks.org/python-get-the-substring-from-given-string-using-list-slicing/
            data = self.dataToSend[self.seqnum: self.seqnum + self.DATA_LENGTH]

            # get the payload size of the data
            payloadSize = len(data)

            # if the payload size is zero then have nothing to send so exit the function
            if (payloadSize == 0):
                break

            # if the next data chunk does not fit into the flow-control window size then exit
            if ((self.sizeOfDataSent  + payloadSize - self.lastGoodServerAcknum) > self.FLOW_CONTROL_WIN_SIZE):
                break

            # if are resending then only send what previously sent before
            if (self.areResending == True):
                # if the size of the sent data is such that it is equal to expected acknum -1
                # then exit
                if((self.sizeOfDataSent  + payloadSize) > self.expectedACK):
                    self.areResending = False
                    break

            # if all of the above conditions are satisfied then the last chunk of data to be
            # pulled will be sent and is therefore counted in the sizeOfDataSent variable
            self.sizeOfDataSent += payloadSize

            # send the data chunk by using a Segment class object
            seg = Segment()
            seg.setData(self.seqnum,data) # set the data and sequence number of the segment
            # seg.dump() prints state values to screen
            # Use the unreliable sendChannel to send the segment
            self.sendChannel.send(seg)

        # start monitoring the time for catching timeouts
        self.sendTime = self.currentIteration

        # set the expected acknum to be returned by the server
        self.expectedACK = self.sizeOfDataSent

        # turn off the turnToSend flag, so another batch of segments can't be sent until
        # either an acknum is received for the last batch of segments or a timeout occurs
        self.turnToSend = False


    # Manage Segment receive  tasks...
    # Most of error checking is done in the receive function, such as checking
    # for packets out of order, missing packets and checksum checks.
    #
    # All incoming packets are pulled from the unreliable channel into a list.
    # If the elements in the list pass the checksum checks then they are
    # added to the dictionary segmentsReceived as segmentsReceived[seqnum] = payload.
    # This dictionary is then sorted according to seqnum and checked to see if any
    # sequence numbers are missing. If packets are missing then these are moved to
    # a segmentsWaiting dictionary. Note that segmentsReceived is cleared after
    # every iteration. When in future iterations more packets arrive these waiting
    # segments are then moved to the segmentsReceived dictionary and if there are
    # no gaps the payload contents of segmentsReceived are added to the dataReceived
    # string and an acknum is generated and sent to the client
    def manageReceive(self):
        #print('Complete this... in manage receive')

        # get a list of the incoming segments from the unreliable channel
        listIncoming = self.receiveChannel.receive()

        # if the list is not empty then process it
        if len(listIncoming) > 0:

            #holds the segments numbers that have arrived in the latest receive
            segment_numbers = []

            # go through each segment that has arrived to determine errors and whether
            # or not the segment is an acknum
            for item in listIncoming:

                # do a checksum check on the received packets
                checkChecksumResult = self.perform_checksumCheck(item)

                # if the packet passes the checksum test then process it
                if (checkChecksumResult == True):

                    # variables used to add packet to dictionary[itemSeqNum] = payload
                    word = item.payload
                    itemSeqNum = item.seqnum

                    # if the packet is an ack number then ensure the sender retreives it
                    # and then exit the function.
                    if (itemSeqNum >= self.acknum  or  itemSeqNum == -1):
                        if (itemSeqNum == -1):

                            # store the new ack number in the lastGoodServerAcknum
                            self.lastGoodServerAcknum = item.acknum

                            # set the "can send" flag for the send function since the ACK
                            # has been received
                            self.turnToSend = True
                            return

                        # store the segment numbers in a list
                        segment_numbers.append(itemSeqNum)

                        # add the packet to the segmentsReceived dictionary
                        self.segmentsReceived[itemSeqNum] = word

            # if there are packets waiting in the segmentsWaiting dictionary then move these
            # to the segmentsReceived dictionary
            if (len(self.segmentsWaiting) > 0):
                for key in self.segmentsWaiting.keys():
                    segment_numbers.append(key)
                    # duplicates are not allowed in dictionaries so there should be only one
                    # of each packet listed
                    self.segmentsReceived[key] = self.segmentsWaiting[key]
                self.segmentsWaiting.clear() # clear the dictionary

            # if after some initial processing there are elements in the segmentsReceived
            # dictionary then check for missing segments and if there are none add the payloads
            # to the receiveString otherwise move the segments to the segmentsWaiting dictionary
            if ( len(self.segmentsReceived) > 0):

                # remove duplicate segnums from list
                # reference: https://www.w3schools.com/python/python_howto_remove_duplicates.asp
                segment_numbers = list(dict.fromkeys(segment_numbers))

                # check for missing segments. If there are missing segments the flag missingSegments
                # is true. Regardless of missing segments or not the acknum is set to be the value
                # of the largest in order segment+payload before any potential gaps.
                missingSegments, self.acknum = self.verify_segment_numbers(segment_numbers, self.segmentsReceived)

                # if there are no missing segments then add the payloads to the receive string
                if (missingSegments == False):
                    self.acknum = self.add_data_received(self.segmentsReceived, segment_numbers)
                else: # if there are missing segments then add them to the segmentsWaiting dictionary
                    self.add_data_waiting(self.segmentsReceived, segment_numbers)

                self.segmentsReceived.clear()  #clear the dictionary

            # send the acknum by making a segment object and sending that down the
            # unreliable channel
            ack = Segment()
            ack.setAck(self.acknum) # set the value of acknum
            # ack.dump() prints state values to screen
            # Use the unreliable sendChannel to send the ack packet
            self.sendChannel.send(ack)

    # Verify that there are no missing segments by looking for gaps in the segment numbers.
    # input: a list of segment numbers
    #        a dictionary of the form dict[segnum] = payload
    # output: a boolean that is true if there are segments missing
    #         the acknum for the last segment before any missing segments
    def verify_segment_numbers(self, segment_numbers, data):
        segmentMissing = False  # true if segment missing

        length = len(segment_numbers) # size of list

        # reference: https://www.w3schools.com/python/ref_list_sort.asp
        segment_numbers.sort() # sort the segment numbers

        # if the first or only segment number is greater than the ACK number then
        # there is at least one segment missing at the beginning
        if (segment_numbers[0] > self.acknum):
            return True, self.acknum

        # if there is only one segment in the list and it satisfies the above
        # condition then by default nothing is missing
        i=0
        if (length == 1):
            numIndex = segment_numbers[i]
            # acknum= segnum + payload size
            lastValidAck = segment_numbers[i] + len(data[numIndex])
            return False, lastValidAck  #exit the function

        # for list sizes > 1 check to see if there is a gap between segment numbers
        for i in range(length -1):
            numIndex = segment_numbers[i]
            if( (segment_numbers[i+1] - segment_numbers[i]) > len(data[numIndex]) ):
                # there is a gap between segment number so the acknum is that of
                # the last valid segment number before the gap occurs
                lastValidAck = segment_numbers[i] + len(data[numIndex])
                return True, lastValidAck #exit the function

        # if reach this point without exiting then unless the list was size 1 there
        # are no gaps or missing segments
        i = length-1
        numIndex = segment_numbers[i]

        # acknum= segnum + payload size
        lastValidAck = segment_numbers[i] + len(data[numIndex])

        # resource: https://www.geeksforgeeks.org/g-fact-41-multiple-return-values-in-python/
        return segmentMissing, lastValidAck

    # Adds validated data received to the dataReceived string.
    # input: a list of segment numbers
    #        a dictionary of the form dict[segnum] = payload
    # output: the latest acknum value
    def add_data_received(self, data, segment_numbers):
        segment_numbers.sort() # sort the segnums to ensure adding the payloads in the correct order

        nextNum= segment_numbers[0] # initialize nextNum

        for i in range (len(data)):
            nextNum = segment_numbers[i]
            self.messageReceived += data[nextNum] #concatenated the next payload string

        return nextNum + len(data[nextNum]) #return last segment number + segment size = new ack #

    # Performs a checksum check of an element in the list returned from the unreliable's channel
    # receive() function.
    # input: a list element returned from the unreliable.py receive function
    # output: true if the checksum is valid
    def perform_checksumCheck(self,item):
        seg = Segment()
        seg.checksum = item.checksum
        seg.seqnum = item.seqnum
        seg.acknum = item.acknum
        seg.payload = item.payload
        return seg.checkChecksum()

    # Add dictionary data to the segmentsWaiting dictionary.
    # input: a dictionary of the form dict[segnum] = payload
    #        a list of segment numbers
    def add_data_waiting(self, data, segment_numbers):
        for i in range(len(segment_numbers)):
            nextNum = segment_numbers[i]
            self.segmentsWaiting[nextNum] = data[nextNum]






