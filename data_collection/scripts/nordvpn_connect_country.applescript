on run argv
	if (count of argv) > 0 then
		set targetCountry to item 1 of argv
	else
		set fallbackCountries to {"Japan", "Singapore", "United States", "Germany"}
		set randomIndex to (random number from 1 to (count of fallbackCountries))
		set targetCountry to item randomIndex of fallbackCountries
	end if

	tell application id "com.nordvpn.macos" to activate
	delay 1

	tell application "System Events"
		if UI elements enabled is false then
			error "System Events 접근성 권한이 필요합니다. 시스템 설정에서 허용해 주세요."
		end if

		tell process "NordVPN"
			set frontmost to true
			delay 1

			try
				click menu bar item 1 of menu bar 2
			on error
				try
					click menu bar item 1 of menu bar 1
				end try
			end try
			delay 1

			if (count of windows) is 0 then
				error "NordVPN 메인 창이 열려 있지 않습니다."
			end if

			set mainWindow to window 1
			set sidePanel to group 1 of group 3 of group 1 of mainWindow
			set searchField to text field 1 of sidePanel

			click searchField
			delay 0.2
			keystroke "a" using command down
			key code 51
			delay 0.2
			keystroke targetCountry
			delay 1.5

			set serverTable to table 1 of scroll area 1 of sidePanel
			set matchingRows to {}

			repeat with rowIndex from 1 to count of rows of serverTable
				try
					set serverName to value of static text 1 of button 1 of UI element 1 of row rowIndex of serverTable
					if serverName contains targetCountry then
						set end of matchingRows to {serverName, rowIndex}
					end if
				on error
					-- 헤더나 일반 행이 아닌 경우는 건너뜀
				end try
			end repeat

			if (count of matchingRows) is 0 then
				error "선택한 국가에 대응하는 서버를 찾지 못했습니다: " & targetCountry
			end if

			set selectedServer to some item of matchingRows
			set selectedServerName to item 1 of selectedServer
			set selectedRowIndex to item 2 of selectedServer

			click button 1 of UI element 1 of row selectedRowIndex of serverTable
			delay 2

			click searchField
			keystroke "a" using command down
			key code 51

			return selectedServerName
		end tell
	end tell
end run
