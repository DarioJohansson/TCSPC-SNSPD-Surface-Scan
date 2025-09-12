import telnetlib3

class SRSCT100:
    def __init__(self, ip: str, port: int = 23, test_command: str = "*IDN?"):
        self.ip = ip
        self.port = port
        self.reader = None
        self.writer = None
        self.test_command = test_command
        # Async users must call await self.connect()

    async def connect(self):
        try:
            self.reader, self.writer = await telnetlib3.open_connection(
                host=self.ip, port=self.port, encoding='utf8'
            )
            await self._send_command(self.test_command)  # test comm
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.ip}:{self.port}: {e}")

    async def _send_command(self, command: str) -> str:
        self.writer.write(command + '\r\n')
        await self.writer.drain()
        response = await self.reader.read(1024)
        return response.strip()

    async def send(self, command: str) -> str:
        return await self._send_command(command)

    async def disconnect(self):
        if self.writer:
            self.writer.close()  # no await
            self.writer = None
            self.reader = None
