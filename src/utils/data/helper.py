from colorama import Fore, Style
import re
import sys
import asyncio
from asyncio import Semaphore
from aiohttp import ClientSession
from rich import print
import time

with open('config.py', 'r', encoding='utf-8-sig') as file:
    module_config = file.read()
exec(module_config)

PROXY_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+@[a-zA-Z0-9.-]+:\d+$')
PRIVATE_KEY_PATTERN = re.compile(r'^0x[a-fA-F0-9]{64}$')


def validate_and_load(file_path: str, pattern: re.Pattern, name: str) -> list[str]:
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            items = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"[bold red]⛔ Error:[/bold red] [white]{file_path} not found![/white] [yellow]Create the file with valid {name}s.[/yellow]")
        sys.exit(1)

    if not items:
        if not name == "proxy":
            print(f"[bold yellow]⚠️ Warning:[/bold yellow] [white]{file_path} is empty. No {name}s loaded.[/white]")
            sys.exit(1)  # Stop for wallets or other critical files
        else:
            print(f"[bold yellow]⚠️ Warning:[/bold yellow] [white]{file_path} is empty. No {name}s loaded. Continuing without proxies.[/white]")
            return []  # Proceed if it's just proxies

    invalid_items = [(i + 1, item) for i, item in enumerate(items) if not pattern.match(item)]
    if invalid_items:
        print(f"[bold red]⛔ Invalid {name}s detected in {file_path}:[/bold red]")
        for line_num, item in invalid_items:
            print(f"[red]  → Line {line_num}:[/red] '[white]{item}[/white]' [dim]does not match the expected pattern[/dim]")
        print(f"[yellow]⚙️ Expected pattern:[/yellow] [white]{pattern.pattern}[/white]")
        sys.exit(1)

    print(f"[bold green]✅ Success:[/bold green] [white]{len(items)} {name}s loaded.[/white]")
    time.sleep(0.5)
    return items


private_keys = validate_and_load('wallets.txt', PRIVATE_KEY_PATTERN, "wallet")
proxies = validate_and_load('proxies.txt', PROXY_PATTERN, "proxy")
if not proxies:
    proxies = [None for _ in range(len(private_keys))]


async def check_proxy(proxy: str, semaphore: Semaphore) -> bool:
    test_url = "https://lisk.drpc.org"
    async with semaphore:
        try:
            async with ClientSession() as session:
                async with session.get(test_url, proxy=f"http://{proxy}", timeout=8) as response:
                    if response.status == 200:
                        return True
        except Exception:
            return False


async def filter_and_update_proxies(proxies: list[str], max_concurrent_tasks: int = 50) -> list[str]:
    semaphore = Semaphore(max_concurrent_tasks)
    tasks = [check_proxy(proxy, semaphore) for proxy in proxies]
    results = await asyncio.gather(*tasks)

    working_proxies = [proxy for proxy, is_working in zip(proxies, results) if is_working]

    with open('proxies.txt', 'w', encoding='utf-8-sig') as file:
        file.write("\n".join(working_proxies))

    print(f"{Fore.BLUE}Number of working proxies: {len(working_proxies)}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}Number of non-working proxies: {len(proxies) - len(working_proxies)}{Style.RESET_ALL}")

    return working_proxies
