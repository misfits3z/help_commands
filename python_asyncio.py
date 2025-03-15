# Якщо треба асинхронно обходити папки та файли,
# використовуй Path.iterdir() або os.scandir(),
# а читати файли — через async_open().
import asyncio
from argparse import ArgumentParser
from pathlib import Path
from aiofile import async_open

# Обробка аргументів командного рядка
parser = ArgumentParser(
    description="Copy files asynchronously into subfolders based on extension"
)
parser.add_argument("source", type=Path, help="Вихідна папка або файл")
parser.add_argument("dest", type=Path, help="Цільова папка")
parser.add_argument(
    "--chunk-size", type=int, default=65535, help="Розмір буфера копіювання"
)


async def read_folder(source: Path):
    """Рекурсивно читає всі файли у вихідній папці та її підпапках"""
    tasks = []
    for entry in source.iterdir():
        if entry.is_dir():
            tasks.append(read_folder(entry))  # Рекурсивно обробляємо папку
        elif entry.is_file():
            tasks.append(entry)  # Додаємо файл у список для копіювання

    return (
        await asyncio.gather(*tasks) if tasks else []
    )  # Виконуємо всі таски паралельно


async def copy_file(source: Path, dest_folder: Path, chunk_size: int):
    """Копіює файл у відповідну підпапку на основі розширення"""
    # через суфікс забираємо все що після крапки
    ext = source.suffix.lstrip(".") or "unknown"   
    target_folder = dest_folder / ext
    target_folder.mkdir(parents=True, exist_ok=True) 
    destination = target_folder / source.name  # Шлях до нового файлу

    async with async_open(source, "rb") as src, async_open(destination, "wb") as dest:
        async for chunk in src.iter_chunked(
            chunk_size
        ):  # Читаємо та записуємо шматками
            await dest.write(chunk)


async def main(args):
    tasks = []
    if args.source.is_dir():
        files = await read_folder(args.source)  # Отримуємо список файлів
        for file in files:
            tasks.append(copy_file(file, args.dest, args.chunk_size))
    else:
        tasks.append(copy_file(args.source, args.dest, args.chunk_size))

    await asyncio.gather(*tasks)  # Виконуємо всі таски паралельно


if __name__ == "__main__":
    asyncio.run(main(parser.parse_args()))
