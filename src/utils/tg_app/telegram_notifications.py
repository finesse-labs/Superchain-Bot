from src.database.base_models.pydantic_manager import DataBaseManagerConfig
from src.database.utils.db_manager import DataBaseUtils
from src.utils.request_client.client import RequestClient
from src.utils.user.account import Account


class TGApp(RequestClient):
    def __init__(
            self,
            token: str,
            tg_id: int,
            private_key: str,
    ):
        self.private_key = private_key
        self.__account = Account(
            private_key=private_key,
            proxy=None
        )

        self.token = token
        self.tg_id = tg_id
        super().__init__(proxy=None)

        self.__db_utils = DataBaseUtils(
            manager_config=DataBaseManagerConfig(
                action='wallets_tasks'
            )
        )

    def progress_bar(self, completed, total):
        filled = int(completed * 10 / total) if total > 0 else 0
        return "█" * filled + "░" * (10 - filled)

    async def _get_text(self) -> str:
        completed_tasks, uncompleted_tasks = await self.__db_utils.get_tasks_info(self.private_key)

        completed_tasks_list = "\n".join(f"- {task.task_name}" for task in completed_tasks) or "No tasks completed."
        uncompleted_tasks_list = "\n".join(f"- {task.task_name}" for task in uncompleted_tasks) or "All tasks completed."

        completed_wallets_count = await self.__db_utils.get_completed_wallets_count()
        total_wallets_count = await self.__db_utils.get_total_wallets_count()

        completed_tasks_list = escape_markdown_v2(completed_tasks_list)
        uncompleted_tasks_list = escape_markdown_v2(uncompleted_tasks_list)

        text = (
            f"💼 **Wallet Processed**:\n"
            f"`{self.__account.wallet_address}`\n\n"
            f"📋 **Tasks**:\n"
            f"🟢**Done**: {len(completed_tasks)} \n"
            f"🟠**To Do**: {len(uncompleted_tasks)} \n\n"
            f"ℹ️**Details**:\n"
            f"**Completed**:\n{completed_tasks_list}\n"
            f"**Pending**:\n{uncompleted_tasks_list}\n\n"
            f"📈 **Progress**:\n"
            f"**{completed_wallets_count}/{total_wallets_count}** [{self.progress_bar(completed_wallets_count, total_wallets_count)}]"
        )

        return text

    async def send_message(self) -> None:
        text = await self._get_text()

        await self.make_request(
            method='GET',
            url=f'https://api.telegram.org/bot{self.token}/sendMessage',
            params={
                "parse_mode": "MarkdownV2",
                "disable_web_page_preview": 1,
                "chat_id": self.tg_id,
                "text": text,
            }
        )


def escape_markdown_v2(text: str) -> str:
    specials = r"_-*[]()~`>#+=|{}.!"
    for char in specials:
        text = text.replace(char, f"\\{char}")
    return text