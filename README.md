# beats-pill-keepalive

USB-C로 Mac에 상시 연결된 Beats Pill(또는 비슷하게 무신호 시 자동 꺼지는 스피커)이
약 60분 무음 후 자동으로 꺼지는 것을 막기 위한 초경량 백그라운드 데몬.

20초 간격으로 사람 귀에는 거의 들리지 않는 19kHz 근처의 저진폭 사인파 핑(ping)을
현재 macOS 기본 출력 장치로 재생해서, 스피커의 auto-sleep 타이머를 계속 리셋시킵니다.

## 빠른 시작

1. 터미널에서 설치 명령을 실행합니다.
   ```bash
   curl -fsSL https://raw.githubusercontent.com/travisherpaz/beats-pill-keepalive/main/install.sh | bash
   ```
2. **시스템 설정 > 사운드**에서 출력 장치를 Beats Pill로 지정합니다.
3. 끝. 로그인할 때마다 자동으로 실행되며, 별도로 켜거나 끌 필요가 없습니다.

- 필요 환경: macOS, `git`, `python3` (없으면 `xcode-select --install`)
- 동작 확인: `tail ~/Library/"Application Support"/BeatsKeepAlive/keepalive.log`
- 제거: `~/.local/share/beats-pill-keepalive/uninstall.sh`

## 동작 방식

- `beats_keepalive.py`가 `~/Library/Application Support/BeatsKeepAlive/`에
  무음에 가까운 1초짜리 wav 파일을 생성하고, `afplay`로 주기 재생합니다.
- 매 재생마다 스트림을 새로 열고 닫기 때문에 Mac이 잠자기에서 깨어나도
  별도 처리 없이 다음 주기에 자동으로 복구됩니다.
- 약 5분마다 `system_profiler`로 현재 기본 출력 장치를 확인해 로그에 남깁니다
  (`keepalive.log`) — 스피커가 실제로 꺼지거나 장치가 바뀌었는지 사후 확인용.
- 상수(`AMPLITUDE`, `FREQUENCY_HZ`, `INTERVAL_SEC` 등)를 바꾸면 다음 실행 시
  자동으로 무음 파일을 재생성합니다 (수동 삭제 불필요).

## 수동 설치 (선택)

1. 이 저장소를 원하는 위치에 클론합니다.
2. `com.local.beatskeepalive.plist.template`을 복사해서
   `~/Library/LaunchAgents/com.local.beatskeepalive.plist`로 저장하고,
   `REPLACE_WITH_ABSOLUTE_PATH_TO`와 `REPLACE_WITH_HOME`을 실제 경로로 바꿉니다.
3. 등록 및 실행:
   ```bash
   plutil -lint ~/Library/LaunchAgents/com.local.beatskeepalive.plist
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.local.beatskeepalive.plist
   launchctl enable gui/$(id -u)/com.local.beatskeepalive
   ```
4. macOS 사운드 설정에서 출력 장치를 Beats Pill로 지정해두어야 합니다.

## 운영

- 상태 확인: `launchctl print gui/$(id -u)/com.local.beatskeepalive`
- 로그 확인: `cat ~/Library/"Application Support"/BeatsKeepAlive/keepalive.log`
- 설정 변경 후 재시작: `launchctl kickstart -k gui/$(id -u)/com.local.beatskeepalive`
- 중지: `launchctl bootout gui/$(id -u)/com.local.beatskeepalive`

## 리소스 사용량

유휴 상태 CPU 0%, 메모리 약 15MB. 20초마다 1초간 `afplay` 자식 프로세스가
잠깐 뜨는 정도로, 체감되는 성능/배터리 영향은 없습니다.
