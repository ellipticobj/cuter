import asyncio

# set of all connected client writers
clients = set()


async def handle_client(reader, writer):
    # Add the new client's writer to our set
    clients.add(writer)
    peername = writer.get_extra_info("peername")
    print(f"[+] New connection from {peername}")

    try:
        while True:
            # read data from the client
            data = await reader.read(100)
            if not data:
                break  # client disconnected

            message = data.decode("utf-8").strip()
            print(f"[{peername}] says: {message}")

            for client_writer in clients:
                if client_writer != writer:
                    try:
                        client_writer.write(
                            f"[{peername}] says: {message}\n".encode("utf-8")
                        )
                        await client_writer.drain()
                    except Exception as e:
                        print(f"error broadcasting client message: {e}")
                        writer.write(f"error sending message: {e}\n".encode("utf-8"))

    except asyncio.CancelledError:
        pass
    finally:
        # Clean up when client disconnects
        print(f"[-] Connection closed for {peername}")
        clients.remove(writer)
        writer.close()
        await writer.wait_closed()


async def handleserverinput():
    loop = asyncio.get_running_loop()
    while True:
        message = await loop.run_in_executor(None, input)
        if not message.strip():
            continue

        for client_writer in clients:
            client_writer.write(f"[SERVER] says: {message}\n".encode("utf-8"))
            await client_writer.drain()


async def main():
    ip = "127.0.0.1"
    port = 8888
    # Start the TCP server on localhost port 8888
    server = await asyncio.start_server(handle_client, ip, port)

    addr = server.sockets[0].getsockname()
    print(f"[*] Chat server running on {addr}")

    async with server:
        await asyncio.gather(server.serve_forever(), handleserverinput())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")
