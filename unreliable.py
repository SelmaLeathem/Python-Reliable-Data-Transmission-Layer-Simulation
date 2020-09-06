
#############################################################################
# Date:        5/1/2020
# Description: Provided implementation of the unreliable channel. This code
#              has not been modified.
#############################################################################
import random
from functools import reduce

class Segment():

    def __init__(self):
        self.seqnum = -1
        self.acknum = -1
        self.payload = ''
        self.checksum = 0
        self.startIteration = 0
        self.startDelayIteration = 0

    def setData(self,seq,data):
        self.seqnum = seq
        self.acknum = -1
        self.payload = data
        self.checksum = 0
        str = self.to_string()
        self.checksum = self.calc_checksum(str)

    def setAck(self,ack):
        self.seqnum = -1
        self.acknum = ack
        self.payload = ''
        self.checksum = 0
        str = self.to_string()
        self.checksum = self.calc_checksum(str)

    def setStartIteration(self,iteration):
        self.startIteration = iteration

    def getStartIteration(self):
        return self.startIteration

    def setStartDelayIteration(self,iteration):
        self.startDelayIteration = iteration

    def getStartDelayIteration(self):
        return self.startDelayIteration

    def to_string(self):
        return "seq: {0}, ack: {1}, data: {2}"\
        .format(self.seqnum,self.acknum,self.payload)

    def checkChecksum(self):
        cs = self.calc_checksum(self.to_string())
        return cs == self.checksum

    def calc_checksum(self,str):
        return reduce(lambda x,y:x+y, map(ord, str))

    def dump(self):
        print(self.to_string())

    # Function to cause an error - Do not modify
    def createChecksumError(self):
        if not self.payload:
            return
        char = random.choice(self.payload)
        self.payload = self.payload.replace(char, 'X', 1)

class UnreliableChannel():
    RATIO_DROPPED_PACKETS = 0.1
    RATIO_DELAYED_PACKETS = 0.1
    RATIO_DATA_ERROR_PACKETS = 0.1
    RATIO_OUT_OF_ORDER_PACKETS = 0.1
    ITERATIONS_TO_DELAY_PACKETS = 5

    def __init__(self, canDeliverOutOfOrder_, canDropPackets_, canDelayPackets_, canHaveChecksumErrors_):
        self.sendQueue = []
        self.receiveQueue = []
        self.delayedPackets = []
        self.canDeliverOutOfOrder = canDeliverOutOfOrder_
        self.canDropPackets = canDropPackets_
        self.canDelayPackets = canDelayPackets_
        self.canHaveChecksumErrors = canHaveChecksumErrors_
        # stats
        self.countTotalDataPackets = 0
        self.countSentPackets = 0
        self.countChecksumErrorPackets = 0
        self.countDroppedPackets = 0
        self.countDelayedPackets = 0
        self.countOutOfOrderPackets = 0
        self.countAckPackets = 0
        self.currentIteration = 0

    def send(self,seg):
        self.sendQueue.append(seg)

    def receive(self):
        new_list = list(self.receiveQueue)
        self.receiveQueue.clear()
        #print("UnreliableChannel len receiveQueue: {0}".format(len(self.receiveQueue)))
        return new_list

    def manage(self):
        #print("UnreliableChannel manage - len sendQueue: {0}".format(len(self.sendQueue)))
        self.currentIteration += 1

        if len(self.sendQueue) == 0:
            return

        if self.canDeliverOutOfOrder:
            val = random.random()
            if val <= UnreliableChannel.RATIO_OUT_OF_ORDER_PACKETS:
                self.countOutOfOrderPackets += 1
                self.sendQueue.reverse()

        # add in delayed packets
        noLongerDelayed = []
        for seg in self.delayedPackets:
            numIterDelayed = self.currentIteration - seg.getStartDelayIteration()
            if (numIterDelayed) >= UnreliableChannel.ITERATIONS_TO_DELAY_PACKETS:
                noLongerDelayed.append(seg)

        for seg in noLongerDelayed:
            self.countSentPackets += 1
            self.delayedPackets.remove(seg)
            self.receiveQueue.append(seg)

        for seg in self.sendQueue:
            #self.receiveQueue.append(seg)

            addToReceiveQueue = False
            if self.canDelayPackets:
                val = random.random()
                if val <= UnreliableChannel.RATIO_DELAYED_PACKETS:
                    self.countDelayedPackets += 1
                    seg.setStartDelayIteration(self.currentIteration)
                    self.delayedPackets.append(seg)
                    continue

            if self.canDropPackets:
                val = random.random()
                if val <= UnreliableChannel.RATIO_DROPPED_PACKETS:
                    self.countDroppedPackets += 1
                else:
                    addToReceiveQueue = True
            else:
                addToReceiveQueue = True

            if addToReceiveQueue:
                self.receiveQueue.append(seg)
                self.countSentPackets += 1

            if seg.acknum == -1:
                self.countTotalDataPackets += 1

                # only data packets can have checksum errors...
                if self.canHaveChecksumErrors:
                    val = random.random()
                    if val <= UnreliableChannel.RATIO_DATA_ERROR_PACKETS:
                        seg.createChecksumError()
                        self.countChecksumErrorPackets += 1

            else:
                # count ack packets...
                self.countAckPackets += 1

            #print ("length of sendQueue = ", len(self.sendQueue))

            #print("UnreliableChannel len receiveQueue: {0}".format(len(self.receiveQueue)))

        self.sendQueue.clear()
        #print("UnreliableChannel manage - len receiveQueue: {0}".format(len(self.receiveQueue)))
