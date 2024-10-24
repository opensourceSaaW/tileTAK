import asyncio
from aiohttp import ClientSession
import xml.etree.ElementTree as ET
from configparser import ConfigParser
from pytile import async_login
import pytak


class TileSerializer(pytak.QueueWorker):
    async def handle_data(self, data):
        event = data
        await self.put_queue(event)

    async def run(self, number_of_iterations=-1):
        while 1:
            async with ClientSession() as session:
                api = await async_login("EMAIL", "PASSWORD", session)
                tiles = await api.async_get_tiles()

                for tile in tiles.values():
                    data = tile_cot(tile)
                    await self.handle_data(data)
            await asyncio.sleep(60)


def tile_cot(tile):
    tile_timestamp = tile.last_timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    root = ET.Element("event")
    root.set("version", "2.0")
    root.set("type", "a-f-G-O")  # insert your type of marker
    root.set("uid", tile.name)
    root.set("how", "m-g")
    root.set("time", pytak.cot_time())
    root.set("start", tile_timestamp)
    root.set("stale", pytak.cot_time(1200))

    pt_attr = {
        "lat": str(tile.latitude),
        "lon": str(tile.longitude),
        "hae": str(tile.altitude),
        "ce": str(tile.accuracy),
        "le": "10",
    }

    ET.SubElement(root, "point", attrib=pt_attr)

    return ET.tostring(root)


async def main() -> None:
    config = ConfigParser()
    config["tilecot"] = {"COT_URL": "tcp://IP_ADDRESS:8087"}
    config = config["tilecot"]

    clitool = pytak.CLITool(config)
    await clitool.setup()

    clitool.add_tasks(set([TileSerializer(clitool.tx_queue, config)]))

    await clitool.run()


if __name__ == "__main__":
    asyncio.run(main())
