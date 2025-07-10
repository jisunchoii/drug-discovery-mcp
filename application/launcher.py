import subprocess
import sys
import time
import signal
import os

# 실행할 MCP 서버 목록 (Python과 Docker)
mcp_servers = [
    {"type": "python", "path": "application/mcp_server_tavily.py"},
]

processes = []

def signal_handler(sig, frame):
    print("\nCtrl+C 감지됨. 모든 서버를 종료합니다...")
    for process in processes:
        if process.poll() is None:  # 프로세스가 아직 실행 중인 경우
            process.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    print("모든 MCP 서버를 시작합니다...")
    
    for server in mcp_servers:
        server_type = server["type"]
        
        if server_type == "python":
            server_path = server["path"]
            print(f"{server_path} (Python) 시작 중...")
            process = subprocess.Popen(
                [sys.executable, server_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
        elif server_type == "javascript":
            server_path = server["path"]
            print(f"{server_path} (JavaScript) 시작 중...")
            process = subprocess.Popen(
                ["node", server_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
        elif server_type == "docker":
            image_name = server["image"]
            container_name = server["name"]
            print(f"{image_name} (Docker) 시작 중...")
            process = subprocess.Popen(
                ["docker", "run", "-i", "--name", container_name, "--rm", image_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
        else:
            print(f"지원하지 않는 서버 타입: {server_type}")
            continue
            
        processes.append(process)
        
        # 서버가 시작될 때까지 약간의 지연
        time.sleep(2)
        
        # 초기 로그 출력 확인
        if process.poll() is not None:
            # 프로세스가 이미 종료된 경우
            stdout, stderr = process.communicate()
            server_id = server.get("path", server.get("image", "unknown"))
            print(f"오류: {server_id} 시작 실패")
            print(f"STDERR: {stderr}")
            print(f"STDOUT: {stdout}")
            # 다른 모든 프로세스 종료
            for p in processes:
                if p != process and p.poll() is None:
                    p.terminate()
            sys.exit(1)
    
    print("\n모든 MCP 서버가 성공적으로 시작되었습니다.")
    print("서버 로그:")
    
    # 모든 서버의 로그를 실시간으로 모니터링
    try:
        while True:
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    # 프로세스가 예기치 않게 종료된 경우
                    stdout, stderr = process.communicate()
                    server_id = mcp_servers[i].get("path", mcp_servers[i].get("image", "unknown"))
                    print(f"\n오류: {server_id} 서버가 예기치 않게 종료되었습니다.")
                    print(f"STDERR: {stderr}")
                    # 다른 모든 프로세스 종료
                    for p in processes:
                        if p != process and p.poll() is None:
                            p.terminate()
                    sys.exit(1)
                
                # 표준 출력 및 오류 읽기
                for line in iter(process.stdout.readline, ""):
                    if not line:
                        break
                    server_id = mcp_servers[i].get("path", mcp_servers[i].get("image", "unknown"))
                    print(f"[{server_id}] {line.strip()}")
                
                for line in iter(process.stderr.readline, ""):
                    if not line:
                        break
                    server_id = mcp_servers[i].get("path", mcp_servers[i].get("image", "unknown"))
                    print(f"[{server_id} ERROR] {line.strip()}")
                    
            time.sleep(0.1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()