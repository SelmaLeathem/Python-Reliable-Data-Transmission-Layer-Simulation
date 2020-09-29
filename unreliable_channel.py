#############################################################################
# Date:        5/1/2020
# Description: Provided implementation of the unreliable channel. This code
#              has not been modified.
#############################################################################
import random
from functools import reduce


class Segment:

    def __init__(self):
        self.seq_num = -1
        self.ack_num = -1
        self.payload = ''
        self.checksum = 0
        self.start_iteration = 0
        self.start_delay_iteration = 0

    def set_data(self, seq, data):
        self.seq_num = seq
        self.ack_num = -1
        self.payload = data
        self.checksum = 0
        str = self.to_string()
        self.checksum = self.calc_checksum(str)

    def set_ack(self, ack):
        self.seq_num = -1
        self.ack_num = ack
        self.payload = ''
        self.checksum = 0
        str = self.to_string()
        self.checksum = self.calc_checksum(str)

    def set_start_iteration(self, iteration):
        self.start_iteration = iteration

    def get_start_iteration(self):
        return self.start_iteration

    def set_start_delay_iteration(self, iteration):
        self.start_delay_iteration = iteration

    def get_start_delay_iteration(self):
        return self.start_delay_iteration

    def to_string(self):
        return "seq: {0}, ack: {1}, data: {2}" \
            .format(self.seq_num, self.ack_num, self.payload)

    def check_checksum(self):
        cs = self.calc_checksum(self.to_string())
        return cs == self.checksum

    def calc_checksum(self, str):
        return reduce(lambda x, y: x + y, map(ord, str))

    def dump(self):
        print(self.to_string())

    # Function to cause an error
    def create_checksum_error(self):
        if not self.payload:
            return
        char = random.choice(self.payload)
        self.payload = self.payload.replace(char, 'X', 1)


class Channel:
    DROPPED_PACKET_RATIO = 0.1
    DELAYED_PACKET_RATIO = 0.1
    DATA_ERROR_PACKET_RATIO = 0.1
    OUT_OF_ORDER_PACKET_RATIO = 0.1
    NUM_ITERATIONS_TO_DELAY_PACKETS = 5

    def __init__(self, can_deliver_out_of_order_, can_drop_packets_,
                 can_delay_packets_, can_have_checksum_errors_):
        self.send_queue = []
        self.receive_queue = []
        self.delayed_packets = []
        self.can_deliver_out_of_order = can_deliver_out_of_order_
        self.can_drop_packets = can_drop_packets_
        self.can_delay_packets = can_delay_packets_
        self.can_have_checksum_errors = can_have_checksum_errors_
        # stats
        self.count_total_data_packets = 0
        self.count_sent_packets = 0
        self.count_checksum_error_packets = 0
        self.count_dropped_packets = 0
        self.count_delayed_packets = 0
        self.count_out_of_order_packets = 0
        self.count_ack_packets = 0
        self.current_iteration = 0

    def send(self, seg):
        self.send_queue.append(seg)

    def receive(self):
        new_list = list(self.receive_queue)
        self.receive_queue.clear()
        return new_list

    def manage(self):
        self.current_iteration += 1

        if len(self.send_queue) == 0:
            return

        if self.can_deliver_out_of_order:
            val = random.random()
            if val <= Channel.OUT_OF_ORDER_PACKET_RATIO:
                self.count_out_of_order_packets += 1
                self.send_queue.reverse()

        # add in delayed packets
        no_longer_delayed = []
        for seg in self.delayed_packets:
            num_iter_delayed = self.current_iteration - \
                             seg.get_start_delay_iteration()
            if (
                    num_iter_delayed) >= \
                    Channel.NUM_ITERATIONS_TO_DELAY_PACKETS:
                no_longer_delayed.append(seg)

        for seg in no_longer_delayed:
            self.count_sent_packets += 1
            self.delayed_packets.remove(seg)
            self.receive_queue.append(seg)

        for seg in self.send_queue:
            # self.receive_queue.append(seg)

            add_to_receive_queue = False
            if self.can_delay_packets:
                val = random.random()
                if val <= Channel.DELAYED_PACKET_RATIO:
                    self.count_delayed_packets += 1
                    seg.set_start_delay_iteration(self.current_iteration)
                    self.delayed_packets.append(seg)
                    continue

            if self.can_drop_packets:
                val = random.random()
                if val <= Channel.DROPPED_PACKET_RATIO:
                    self.count_dropped_packets += 1
                else:
                    add_to_receive_queue = True
            else:
                add_to_receive_queue = True

            if add_to_receive_queue:
                self.receive_queue.append(seg)
                self.count_sent_packets += 1

            if seg.ack_num == -1:
                self.count_total_data_packets += 1

                # only data packets can have checksum errors...
                if self.can_have_checksum_errors:
                    val = random.random()
                    if val <= Channel.DATA_ERROR_PACKET_RATIO:
                        seg.create_checksum_error()
                        self.count_checksum_error_packets += 1

            else:
                # count ack packets...
                self.count_ack_packets += 1

        self.send_queue.clear()
