import os
import signal
import psutil


def terminate_process(process_name):
    """
    Завершение процесса по имени
    :param process_name:
    :return:
    """
    # os.system(f"kill {pid}")
    # os.system(f"kill -SIGKILL {pid}")
    # os.system(f"killall -9 {pid}")
    # os.system(f"pkill -P {pid}"
    #     os.kill(pid, signal.SIGKILL)

    try:
        print(os.system(f"pkill -9 -f '{process_name}'"))
    except ProcessLookupError:
        print(f"Процесс с именем {process_name} не найден.")


def terminate_process_psutil(pid) -> None:
    """
    Завершает процесс
    :param pid:
    :return:
    """

    try:
        p = psutil.Process(pid)
        if p.is_running():
            p.terminate()
    except psutil.NoSuchProcess:
        return
