from requests_threads import AsyncSession

session = AsyncSession()


async def _main():
    rs = []
    for _ in range(100):

        rs.append(session.get("", ))
        rs.append(await session.get('http://httpbin.org/get'))
    print(rs)

if __name__ == '__main__':
    session.run(_main)
