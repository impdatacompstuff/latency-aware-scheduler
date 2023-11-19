import iperf3
import os


def main():
    print("Application started :)")

    server = iperf3.Server()
    # ich könnte auch auf 0.0.0.0 binden -> lausche auf allen IP Adressen
    server.bind_address = os.getenv('POD_IP')
    server.port = 5201
    server.verbose = True
    while True:
        print("here")
        server.run()
        print("there")


if __name__ == "__main__":
    main()
