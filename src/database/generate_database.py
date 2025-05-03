import random
import sys
from rich import print

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from loguru import logger

from src.database.base_models.pydantic_manager import DataBaseManagerConfig
from src.database.models import WorkingWallets, WalletsTasks
from src.database.utils.db_manager import DataBaseUtils
from config import *

ALLOWED_TASKS = {
    "OKX_WITHDRAW", "DISPERSE_BRIDGE", "BASE_RANDOM_TX", "INK_RANDOM_TX",
    "OP_RANDOM_TX", "LISK_RANDOM_TX", "UNICHAIN_RANDOM_TX", "SONEIUM_RANDOM_TX",
    "ZORA_RANDOM_TX", "SWELL_RANDOM_TX", "MODE_RANDOM_TX", "CLAIM_BADGES", "STARGATE_BRIDGE"
}


def generate_task_list():
    def validate_task(task):
        if task not in ALLOWED_TASKS:
            print(f"[bold red]⛔ Error:[/bold red] [white]Invalid task '{task}'![/white]")
            print(f"[yellow]Allowed tasks: {', '.join(sorted(ALLOWED_TASKS))}[/yellow]")
            sys.exit(1)

    def process_task(task):
        """Рекурсивно обрабатывает задачи, включая вложенные списки и кортежи."""
        if isinstance(task, str):
            validate_task(task)
            return [task]
        
        elif isinstance(task, list):
            if not task:
                return []
            chosen = random.choice(task)
            return process_task(chosen)
        
        elif isinstance(task, tuple):
            subtasks = []
            for subtask in task:
                subtasks.extend(process_task(subtask))
            random.shuffle(subtasks)
            return subtasks
        
        else:
            raise ValueError(f"Unsupported task type: {type(task)}")

    try:
        tasks_to_process = []
        for task in TASKS:
            if task in globals():
                tasks_to_process.extend(globals()[task])
            else:
                tasks_to_process.append(task)

        final_tasks = []
        for task in tasks_to_process:
            final_tasks.extend(process_task(task))
        
        return final_tasks

    except Exception as e:
        print(f"[bold red]⛔ Error:[/bold red] [white]{str(e)}[/white]")
        sys.exit(1)



async def clear_database(engine) -> None:
    async with AsyncSession(engine) as session:
        async with session.begin():
            for model in [WorkingWallets, WalletsTasks]:
                await session.execute(delete(model))
            await session.commit()
    logger.info("The database has been cleared")


async def generate_database(
        engine,
        private_keys: list[str],
        proxies: list[str],
) -> None:
    await clear_database(engine)

    tasks = []

    proxy_index = 0
    for private_key in private_keys:
        tasks = generate_task_list()

        proxy = proxies[proxy_index]
        proxy_index =(proxy_index + 1) % len(proxies)

        proxy_url = None
        change_link = ''

        if proxy:
            if MOBILE_PROXY:
                proxy_url, change_link = proxy.split('|')
            else:
                proxy_url = proxy

        db_utils = DataBaseUtils(
            manager_config=DataBaseManagerConfig(
                action='working_wallets'
            )
        )

        await db_utils.add_to_db(
            private_key=private_key,
            proxy=f'{proxy_url}|{change_link}' if MOBILE_PROXY else proxy_url,
            status='pending',
        )

        for task in tasks:
            db_utils = DataBaseUtils(
                manager_config=DataBaseManagerConfig(
                    action='wallets_tasks'
                )
            )
            await db_utils.add_to_db(
                private_key=private_key,
                status='pending',
                task_name=task
            )