set successCount to 0
set errorCount to 0

tell application "Messages"
    with timeout of 8 * 3600 seconds
        set phoneFilePath to my current_folder_path() & "phoneNumber.txt"
        set phoneData to read phoneFilePath
        set phoneEntries to paragraphs of phoneData
        set phone_nums to count phoneEntries

        repeat with i from 1 to count phoneEntries
            -- *******************************************
            -- 拼接发送的短信文本内容
            -- *******************************************
            set msgText to (my AppendFace("hello,")) & my AppendFace("下午好啊") &  my AppendFace("张三")
            set phone to (phoneEntries's item i)'s text
            set targetService to (1st service whose service type = iMessage)
            set theBuddy to buddy phone of targetService

            set num to the length of phone
            set isEmail to true
            if ((num > 0 and (my isSendPhone(phone)) = false) or isEmail) then
                try
                    send msgText to theBuddy
                    set logText to phone & " *** " & "1" & " *** " & date string of (current date) & " " & time string of (current date) & " *** " & "发送成功
"
                    ---延时，不然取不到已发送的状态
                    delay (random number from 1 to 3)
                    set chatNum to (get count of chat)
                    if (chatNum >100)  then
                        my deleteMsg(chatNum)
                    end if

                    my WriteLog(logText)
                    my WritePhone(phone)

                    set successCount to successCount + 1 -- 记录成功数
                on error errorMessage number errorNumber

                    set logText to phone & " *** " & "0" & " *** " & date string of (current date) & " " & time string of (current date) & " *** " & "发送失败
"
                    my WriteLog(logText)
                    log "捕获的异常：" & errorMessage & "异常的编号:" & errorNumber
                    set errorCount to errorCount + 1 -- 记录失败数
                end try
            end if
        end repeat


        set titleStr to "数据总数：" & phone_nums & "个  " & "发送成功：" & successCount & "个 " & "发送失败：" & errorCount & "个"
        set btns to {"知道了"}
        display dialog titleStr buttons btns default button 1 --默认选择第1个按钮(按return时就会让弹出框消失)
        get the button returned of the result -- 弹出框
    end timeout
end tell


on deleteMsg(maxNum)
    tell application "Messages" to activate

    tell application "System Events"
        tell process "Messages"
            tell window 1
                repeat's maxNum times

                    delay 0.5
                    click row 1 of table 1 of scroll area 1 of splitter group 1
                    delay 0.2
                    click menu item "删除对话…" of menu "文件" of menu bar item "文件" of menu bar 1 of application process "Messages" of application "System Events"
                    delay 0.2
                    try
                        click buttons "删除" of sheet 1
                    end try
                end repeat
            end tell
        end tell
    end tell
end deleteMsg


on AppendFace(msgText)
    set face to my RandomFace()
    set content to face & msgText & "
"
end AppendFace


on RandomFace()
    -- 表情数组
    set faceList to {"🐟", "🦐", "🦀️", "😊", "😂", "😄", "🎆", "🎉", "🍺", "💐", "🌹", "🦈", "🐲", "🐢", "🐳", "🐬", "🐚", "💰", "🎁"}
    set face to item (random number from 1 to count faceList) of faceList
    return face
end RandomFace


on isSendPhone(the_phone)
    set num to the length of the_phone
    if (num = 11) then
        set fileName to date string of (current date)
        set logFilePath to my current_folder_path() & "send/" & fileName & ".txt"
        set this_file to (POSIX file logFilePath as string)
        set this_story to the_phone & "
"
        try
            set fp to open for access this_file
            set myText to read fp

            if (myText does not contain the_phone) then
                return false
            else
                return true
            end if
        on error
            return false
        end try
    end if
end isSendPhone


on WritePhone(the_phone)
    set num to the length of the_phone
    if (num = 11) then
        set fileName to date string of (current date)
        set logFilePath to my current_folder_path() & "send/" & fileName & ".txt"
        set this_file to (POSIX file logFilePath as string)
        set this_story to the_phone & "
"
        try
            set fp to open for access this_file
            set myText to read fp

            if (myText does not contain the_phone) then
                my write_to_file(this_story, this_file, true, true)
            end if
        on error
            my write_to_file(this_story, this_file, true, true)
        end try
    end if
end WritePhone


on WriteLog(the_text)
    set fileName to date string of (current date)
    set logFilePath to my current_folder_path() & "log/" & fileName & ".txt"
    set this_file to (POSIX file logFilePath as string)
    my write_to_file(the_text, this_file, true, false)
end WriteLog


on write_to_file(this_data, target_file, append_data, append_end)
    try
        set the target_file to the target_file as text
        set the open_target_file to ¬
            open for access file target_file with write permission

        if append_data is false then
            set eof of the open_target_file to 0
            write this_data to the open_target_file starting at eof
        else if append_end is false then
            try
                set fp to open for access target_file
                set myText to read fp
                set eof of the open_target_file to 0
                write this_data to the open_target_file starting at eof
                write myText to the open_target_file starting at eof
            on error
                write this_data to the open_target_file starting at eof
            end try
        else
            write this_data to the open_target_file starting at eof
        end if

        close access the open_target_file
        return target_file
    on error
        try
            close access file target_file
        end try
        return false
    end try
end write_to_file


on current_folder_path()
    set UnixPath to POSIX path of ((path to me as text) & "::")
    return UnixPath
end current_folder_path