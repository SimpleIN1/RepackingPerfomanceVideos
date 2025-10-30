import os
import signal
import psutil


def terminate_process(pid):

    # os.system(f"kill {pid}")
    # os.system(f"kill -SIGKILL {pid}")
    # os.system(f"killall -9 {pid}")
    # os.system(f"pkill -P {pid}")

    pid = int(pid)

    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        print(f"Процесс с PID {pid} не найден.")

    pid += 1

    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        print(f"Процесс с PID {pid} не найден.")


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
