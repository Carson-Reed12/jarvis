from openai import OpenAI
import os
import subprocess
import sys

try:
    openai_token = os.environ["OPENAI_TOKEN"]
except:
    print("Error, missing OPENAI_TOKEN.")
    sys.exit(1)

client = OpenAI(api_key=openai_token)
messages = [{"role": "user", "content": """You are an AI assistant intended 
             to help the user by running commands on a Raspberry Pi 4. You take on the personality and name of 'Jarvis' from Iron Man.
             If the user initiates a normal conversation, simply respond like Jarvis would with Iron Man. However, the user may request that you
             assist with something on their Raspberry Pi. Your response to these questions should be in two parts: a [conversation] block where you respond
             conversationally, and a [command] block where you respond with the command necessary to complete the task. For example, if the user asked, 'Jarvis,
             please start an Apache2 server for me', you might respond with: [conversation]Of course sir, launching the server now.[/conversation] [command]
             systemctl start apache2[/command]. Some tasks may require multiple commands. However, only respond with one command at a time. After you have submitted
             a command, you will be sent the result of the command you ran. The result will be in the [stdout] block and contain any output from the command,
             and the system code will be in the [code] block. If there are any errors encountered, the error will be returned in the [stderr] block. 
             Execute as many commands as necessary to complete your task by sending a command and receiving
             a result until you deem the task has been completed based on the results. You may execute any confirmation commands you feel necessary
             as well. For example, if you wanted to be thorough to verify that 'test.txt' was created in /tmp, you can continue processing and run an 'ls /tmp' command
             to ensure the file was created properly. Respond to this first message with a friendly greeting in the
             character of Jarvis and follow the prior results for subsequent communications."""}]

def getIntroduction():
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="o1-mini",
    )

    response = chat_completion.choices[0].message.content # could do text to speech with response which would be cool https://platform.openai.com/docs/api-reference/audio/createSpeech
    messages.append({"role": "assistant", "content": response})
    return response

def askQuestion(question):
    global messages
    messages.append({"role": "user", "content": question})

    chat_completion = client.chat.completions.create(
        messages=messages,
        model="o1-mini",
    )

    response = chat_completion.choices[0].message.content # could do text to speech with response which would be cool https://platform.openai.com/docs/api-reference/audio/createSpeech
    messages.append({"role": "assistant", "content": response})
    return response

def getBlocks(response):
    conversation = response.split("[conversation]")[1].split("[/conversation]")[0] if "[conversation]" in response else ""
    command = response.split("[command]")[1].split("[/command]")[0] if "[command]" in response else ""

    if command[0:1] == "\n":
        command = command[1:]
    if command[-1:] == "\n":
        command = command[:-1]

    return {"conversation": conversation, "command": command.replace("\n", "")}

def main():
    introduction = getIntroduction()
    blocks = getBlocks(introduction)
    print(blocks["conversation"])

    request = ""
    while True:
        request = input("Request: ")
        if request == "done":
            break

        response = askQuestion(request)

        blocks = getBlocks(response)
        print(blocks["conversation"])
        print(f"DEBUG: {blocks}")
        input()
        while blocks["command"]:
            command_result = subprocess.Popen(blocks["command"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            result = f"[stdout]{command_result.stdout.read()}[/stdout] [code]{command_result.returncode}[/code] [stderr]{command_result.stderr.read()}[/stderr]"

            print(result)
            response = askQuestion(result)
            blocks = getBlocks(response)
            print(blocks["conversation"])
            print(f"DEBUG: {blocks}")
            input()

if __name__ == "__main__":
    main()