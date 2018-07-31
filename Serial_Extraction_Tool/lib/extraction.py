import touchpointcom # custom serial module for our Touchpoints

def main_demo():
    print "--------------------------------"
    print "*********** STARTING ***********"
    print "--------------------------------"
    touchpointcom.listen_port()

main_demo()
