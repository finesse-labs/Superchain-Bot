from rich.console import Console
from rich.panel import Panel
from rich import box
from rich.box import DOUBLE as BOX_DOUBLE

import os

console = Console()

# Разделяем логотип на строки с цветами внутри каждой
LOGO_LINES = [
    " ",
    " ",
    " ",
    "[bold red] ███████╗██╗   ██╗██████╗ ███████╗██████╗   ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗",
    "[bold red] ██╔════╝██║   ██║██╔══██╗██╔════╝██╔══██╗ ██╔════╝██║  ██║██╔══██╗██║████╗  ██║",
    "[bold red] ███████╗██║   ██║██████╔╝█████╗  ██████╔╝ ██║     ███████║███████║██║██╔██╗ ██║",
    "[bold red] ╚════██║██║   ██║██╔═══╝ ██╔══╝  ██╔══██╗ ██║     ██╔══██║██╔══██║██║██║╚██╗██║",
    "[bold red] ███████║╚██████╔╝██║     ███████╗██║  ██║ ╚██████╗██║  ██║██║  ██║██║██║ ╚████║",
    "[bold red] ╚══════╝ ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝",
    " ",
    " ",
    "[bold green]  ███████╗██╗███╗   ██╗███████╗███████╗███████╗     ██╗      █████╗ ██████╗ ███████╗",
    "[bold green]  ██╔════╝██║████╗  ██║██╔════╝██╔════╝██╔════╝     ██║     ██╔══██╗██╔══██╗██╔════╝",
    "[bold green]  █████╗  ██║██╔██╗ ██║█████╗  ███████╗███████╗     ██║     ███████║██████╔╝███████╗",
    "[bold green]  ██╔══╝  ██║██║╚██╗██║██╔══╝  ╚════██║╚════██║     ██║     ██╔══██║██╔══██╗╚════██║",
    "[bold green]  ██║     ██║██║ ╚████║███████╗███████║███████║     ███████╗██║  ██║██████╔╝███████║",
    "[bold green]  ╚═╝     ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚══════╝     ╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝",
    " ",
    " "
]

PROJECT_INFO = Panel(
"""
[bold cyan]Superchain Activity Bot 1.0[/bold cyan]
[white]─────────────────────────────────────────────────────[/white]
[bold yellow]⚡ Devs:[/] [link=https://t.me/ftp_crypto]@ftp_crypto[/link] | [link=https://t.me/cryptoforto]@cryptoforto[/link]
[bold yellow]💬 Support: [white]https://t.me/+HlDlu6F3iGwzMjFi[/white][/bold yellow]
[bold yellow]📦 GitHub: [white]https://github.com/noxuspace/cryptofortochka/[/white][/bold yellow]
""",
    title="[bold green] ⚡ Info ⚡[/bold green]",
    border_style="bright_green",
    box=BOX_DOUBLE,
    width=70,
    padding=(1, 2)
)

def get_module():
    for line in LOGO_LINES:
        console.print(line, justify="center")
    console.print(PROJECT_INFO, justify="center")

    console.print("\n[bold green]Available options:[/bold green]\n")
    console.print("[1] ⚡ Generate new database")
    console.print("[2] 🛠  Work with existing database")
    console.print("[3] 🚪 Exit\n")

    while True:
        try:
            choice = console.input("[bold green]Enter option (1–3): [/bold green]").strip()
            if choice in ["1", "2", "3"]:
                return int(choice)
            elif not choice or choice == "3":
                return 3
            else:
                console.print("[red]Invalid option! Please enter 1, 2, or 3.[/red]")
        except ValueError:
            console.print("[red]Invalid input! Please enter a number (1–3).[/red]")

def get_module_menu():
    console.print("\n[bold green]Available options:[/bold green]")
    console.print("[1] ⚡ Generate new database")
    console.print("[2] 🛠  Work with existing database")
    console.print("[3] 🚪 Exit\n")

    while True:
        try:
            choice = console.input("[bold green]Enter option (1–3): [/bold green]").strip()
            if choice in ["1", "2", "3"]:
                return int(choice)
            console.print("[red]Invalid option! Please enter 1, 2, or 3.[/red]")
        except ValueError:
            console.print("[red]Invalid input! Please enter a number (1–3).[/red]")


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# Запуск
if __name__ == "__main__":
    get_module()


__all__ = ["get_module", "LOGO_LINES", "PROJECT_INFO", "clear_screen", "get_module_menu"]
