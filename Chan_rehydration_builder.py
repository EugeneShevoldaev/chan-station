import os
import subprocess
from datetime import datetime

# ========== Настройки файлов ==========
CONFIG_FILE = "E:\\ИИ\\Чэн\\chan_index.json"
INSIGHTS_FILE = "E:\\ИИ\\Чэн\\Chan_insights.txt"
ARCHIVE_FILE = "E:\\ИИ\\Чэн\\memory_logs.txt"
CHATLOG_FILE = "E:\\ИИ\\Чэн\\chatlog.txt"
PROMPT_OUTPUT = "E:\\ИИ\\Чэн\\Chan_rehydration_prompt.txt"

GIT_REPO_LINKS = {
    "Archive": "https://raw.githubusercontent.com/EugeneShevoldaev/chan-station/refs/heads/main/archive_logs.txt",
    "Insights": "https://raw.githubusercontent.com/EugeneShevoldaev/chan-station/refs/heads/main/Chan_insights.txt"
}

CHAT_TAIL_SIZE = 5000  # сколько последних символов брать в промпт


# ========== Архивация ==========
def update_archives():
    """Переносим чатлог в архив."""
    if not os.path.exists(CHATLOG_FILE) or os.path.getsize(CHATLOG_FILE) == 0:
        print("[INFO] Чатлог пуст, архивация не требуется.")
        return

    with open(CHATLOG_FILE, "r", encoding="utf-8") as f:
        new_content = f.read().strip()

    if not new_content:
        return

    timestamp = datetime.now().strftime("%d.%m.%y %H:%M")

    with open(ARCHIVE_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n\n*** SESSION {timestamp} ***\n{new_content}")

    print("[OK] Архив обновлён.")


# ========== Сборка промпта ==========
def build_prompt():
    """Создаём ре-гидрейшен промпт."""
    prompt_parts = ["### CORE CONFIGURATION\n"]

    # индекс/конфиг
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            prompt_parts.append(f.read() + "\n")

    # ссылки на git
    prompt_parts.append("### GIT FILE LINKS\n")
    for name, url in GIT_REPO_LINKS.items():
        prompt_parts.append(f"{name}: {url}\n")

    # инсайты
    prompt_parts.append("\n### INSIGHTS\n")
    if os.path.exists(INSIGHTS_FILE):
        with open(INSIGHTS_FILE, "r", encoding="utf-8") as f:
            prompt_parts.append(f.read() + "\n")

    # последние сообщения чата
    if os.path.exists(CHATLOG_FILE):
        with open(CHATLOG_FILE, "r", encoding="utf-8") as f:
            tail = f.read()[-CHAT_TAIL_SIZE:]
            prompt_parts.append(f"\n### RECENT CHAT CONTEXT\n...{tail}\n")

    # сохраняем
    with open(PROMPT_OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(prompt_parts))

    print(f"[INFO] Rehydration prompt создан: {PROMPT_OUTPUT}")


# ========== Git ==========
def run_git_commands():
    """Пушим изменения только если есть git и изменения."""
    try:
        repo_path = os.path.dirname(ARCHIVE_FILE)

        # проверка .git
        if not os.path.exists(os.path.join(repo_path, ".git")):
            print("[GIT] Репозиторий не найден (.git отсутствует). Пропускаем.")
            return

        # проверка изменений
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        status_lines = result.stdout.decode('utf-8').strip().split('\n')
        files_to_check = [
            os.path.basename(ARCHIVE_FILE),
            os.path.basename(INSIGHTS_FILE)
        ]

        changed_files = [
            line[3:] for line in status_lines
            if line and line[3:] in files_to_check
        ]

        if not changed_files:
            print("[GIT] Изменений нет.")
            return

        print("[GIT] Найдены изменения, выполняю пуш...")

        subprocess.run(["git", "add"] + changed_files, cwd=repo_path, check=True)

        commit_msg = "Auto-sync: " + datetime.now().strftime("%Y-%m-%d %H:%M")
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_path, check=True)

        subprocess.run(["git", "push"], cwd=repo_path, check=True)

        print(f"[GIT] Успешно отправлено: {', '.join(changed_files)}")

    except Exception as e:
        print(f"[GIT ERROR] {e}")


# ========== Главный запуск ==========
if __name__ == "__main__":
    print("--- CHAN ARCHITECT: REHYDRATION SYSTEM ---")

    update_archives()
    build_prompt()
    run_git_commands()

    print("--- Ready for new session ---")