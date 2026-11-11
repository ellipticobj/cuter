import asyncio


async def tcp_client():
    reader, writer = await asyncio.open_connection("127.0.0.1", 8888)
    print("[*] Connected to the chat server! Type your messages below:\n")

    # Task to continuously listen for incoming messages from the server
    async def receive_messages():
        try:
            while True:
                data = await reader.readline()
                if not data:
                    print("\n[*] Disconnected from server.")
                    break
                print(data.decode("utf-8").strip())
        except asyncio.CancelledError:
            pass

    # Task to read user input from the console and send it to the server
    async def send_messages():
        loop = asyncio.get_running_loop()
        while True:
            message = await loop.run_in_executor(None, input)
            if message.lower() == "exit":
                break
            writer.write((message + "\n").encode("utf-8"))
            await writer.drain()

    receive_task = asyncio.create_task(receive_messages())
    send_task = asyncio.create_task(send_messages())

    done, pending = await asyncio.wait(
        [send_task, receive_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

    writer.close()
    await writer.wait_closed()


def main():
    # handle usernames

    asyncio.run(tcp_client())


if __name__ == "__main__":
    asyncio.run(tcp_client())
