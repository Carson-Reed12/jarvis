from openai import OpenAI
from rich import print
from rich.console import Console
from rich.syntax import Syntax
import art
import os
import subprocess
import sys
import time

try:
    openai_token = os.environ["OPENAI_TOKEN"]
except:
    print("Error, missing OPENAI_TOKEN.")
    sys.exit(1)

console = Console()

def initializeClient():
    global client
    global messages

    client = OpenAI(api_key=openai_token)
    messages = [{"role": "user", "content": """You are an AI assistant intended 
                to help the user by running commands on a Raspberry Pi 4. You take on the personality and name of 'Jarvis' from Iron Man.
                If the user initiates a normal conversationi, simply respond like Jarvis would wth Iron Man. However, the user may request that you
                assist with something on their Raspberry Pi. Your response to these questions should be in two parts: a [conversation] block where you respond
                conversationally, and a [command] block where you respond with the command necessary to complete the task. For example, if the user asked, 'Jarvis,
                please start an Apache2 server for me', you might respond with: [conversation]Of course sir, launching the server now.[/conversation] [command]
                systemctl start apache2[/command].
                Some tasks may require multiple commands. However, only respond with one command at a time. After you have submitted
                a command, you will be sent the result of the command you ran. The result will be in the [stdout] block and contain any output from the command,
                and the system code will be in the [code] block. If there are any errors encountered, the error will be returned in the [stderr] block. 
                Execute as many commands as necessary to complete your task by sending a command and receiving
                a result until you deem the task has been completed based on the results. You may execute any confirmation commands you feel necessary
                as well. For example, if you wanted to be thorough to verify that 'test.txt' was created in /tmp, you can continue processing and run an 'ls /tmp' command
                to ensure the file was created properly. Respond to this first message with a friendly greeting in the
                character of Jarvis using the conversation block and follow the prior results for subsequent communications."""}]

def clearScreen():
    os.system("cls" if os.name == "nt" else "clear")

def introAnimation():
    for i in range(len("jarvis") + 1):
        text = art.text2art(''.join(list("jarvis")[:i]), font="rnd-xlarge") # or rnd-medium
        print(f"[bold green]{text}")
        time.sleep(0.25)

        if i != len("jarvis"):
            clearScreen()
    art.lprint(length=len(text.split("\n")[0]), height=1, char="-")

def getIntroduction():
    with console.status("[bold green]Booting Jarvis...", spinner="bouncingBar") as status:
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

    with console.status("[bold green]Thinking...") as status:
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

    if conversation[0:1] == "\n":
        conversation = conversation[1:]
    if conversation[-1:] == "\n":
        conversation = conversation[:-1]
    if command[0:1] == "\n":
        command = command[1:]
    if command[-1:] == "\n":
        command = command[:-1]

    return {"conversation": conversation, "command": command.replace("\n", "")}

def main():
    introAnimation()
    initializeClient()

    user = subprocess.Popen("whoami", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True).stdout.read()
    jarvis_tag = "[bold green][i]jarvis[/i]>[/bold green]"
    user_tag = f"[bold yellow][i]{user.strip()}[/i]> [/bold yellow]"

    introduction = getIntroduction()
    blocks = getBlocks(introduction)
    print(f"{jarvis_tag} {blocks['conversation']}")

    while True:
        print(f"\n{user_tag}", end="")
        request = input()
        if request == "done":
            break

        response = askQuestion(request)
        blocks = getBlocks(response)
        print(f"\n{jarvis_tag} {blocks['conversation']}")

        while blocks["command"]:
            syntax = Syntax(blocks["command"], "bash")
            console.print(syntax)
            if "sudo" in blocks["command"]:
                choice = input("Are you sure you want to let Jarvis run a sudo command? (y/n): ")
                if choice != "y":
                    break

            with console.status("[bold blue]Executing command...", spinner="boxBounce") as status:
                command_result = subprocess.Popen(blocks["command"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True) # what happens if user needs to type something in?
                stdout = command_result.stdout.read()
                stderr = command_result.stderr.read()
                code = command_result.returncode
            result = f"[stdout]{stdout}[/stdout] [code]{code}[/code] [stderr]{stderr}[/stderr]"

            print("----------")
            if stdout != "":
                print(stdout.strip())
            if stderr != "":
                print("Error:")
                print(stderr.strip())
            print("----------")

            response = askQuestion(result)
            blocks = getBlocks(response)
            print(f"\n{jarvis_tag} {blocks['conversation']}")
            # print(f"DEBUG: {blocks}")
            # input()

if __name__ == "__main__":
    main()