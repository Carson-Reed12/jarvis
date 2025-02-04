from openai import OpenAI
from rich import print
from rich.console import Console
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.progress import track
from rich.prompt import Prompt
from rich.prompt import Confirm
from playsound import playsound
from mutagen.mp3 import MP3
import art
import os
import subprocess
import sys
import argparse
import time
import json

parser = argparse.ArgumentParser(prog="python3 jarvis.py", description="An AI agent powered by OpenAI's o1-mini model.")
parser.add_argument("-s", "--step-by-step", help="require confirmation before command execution", action="store_true", default=False)
parser.add_argument("-t", "--token", help="API token used to authenticate with OpenAI", default="", type=str)
parser.add_argument("-d", "--device", help="device being used (Macbook, Windows desktop, etc. default: Raspberry Pi 4)", default="Raspberry Pi 4", type=str)
parser.add_argument("-tts", "--text-to-speech", help="enable text to speech during response", action="store_true", default=False)

args = parser.parse_args()
step_by_step = args.step_by_step
token = args.token
device = args.device
tts = args.text_to_speech

try:
    if token != "":
        openai_token = token
    else:
        openai_token = os.environ["OPENAI_TOKEN"]
except:
    print("Error: missing OPENAI_TOKEN environment variable or token flag.")
    sys.exit(1)

console = Console()

def initializeClient(device):
    global client
    global messages

    client = OpenAI(api_key=openai_token)
    messages = [{"role": "user", "content": f"""You are an AI assistant intended 
                to help the user by running commands on a {device}. You take on the personality and name of 'Jarvis' from Iron Man.
                If the user initiates a normal conversation, simply respond like Jarvis would wth Iron Man. However, the user may request that you
                assist with something on their Raspberry Pi. Your response to these questions should be in two parts: a [conversation] block where you respond
                conversationally, and a [command] block where you respond with the command necessary to complete the task. For example, if the user asked, 'Jarvis,
                please start an Apache2 server for me', you might respond with: [conversation]Of course sir, launching the server now.[/conversation] [command]
                systemctl start apache2[/command].
                Some tasks may require multiple commands. However, only respond with one command at a time. After you have submitted
                a command, you will be sent the result of the command you ran. The result will be in the [stdout] block and contain any output from the command,
                and the system code will be in the [code] block. If there are any errors encountered, the error will be returned in the [stderr] block. When receiving these
                result blocks, your conversation blocks should briefly explain the results and what you plan to do next. 
                Execute as many commands as necessary to complete your task by sending a command and receiving
                a result until you deem the task has been completed based on the results. You may execute any confirmation commands you feel necessary
                as well. For example, if you wanted to be thorough to verify that 'test.txt' was created in /tmp, you can continue processing and run an 'ls /tmp' command
                to ensure the file was created properly. Respond to this first message with a friendly greeting in the
                character of Jarvis using the conversation block and follow the prior results for subsequent communications."""}]

def clearScreen():
    os.system("cls" if os.name == "nt" else "clear")

def introAnimation():
    for i in range(len("jarvis") + 1):
        text = art.text2art(''.join(list("jarvis")[:i]), font="rnd-xlarge")
        print(f"[bold green]{text}")
        time.sleep(0.25)

        if i != len("jarvis"):
            clearScreen()

    for line in text.split("\n"):
        if len(line) > 0:
            art.lprint(length=len(line), height=1, char="-")
            break

def askQuestion(question = None, introduction = False):
    global messages

    if not introduction:
        messages.append({"role": "user", "content": question})

    with console.status("[bold green]Thinking..." if not introduction else "[bold green]Booting Jarvis...", spinner="dots" if not introduction else "bouncingBar") as status:
        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="o1-mini",
            )
        except Exception as e:
            error_code = e.message.split(' - ')[0]
            message_object = json.loads(e.message.split(' - ')[1].replace("'", '"').replace("None", "null"))
            console.log(f"{error_code}\nReason: {message_object['error']['code']}\nMessage: {message_object['error']['message']}", style='bold red')
            sys.exit(1)
        response = chat_completion.choices[0].message.content 

    messages.append({"role": "assistant", "content": response})
    return response

def getBlocks(response):
    conversation = response.split("[conversation]")[1].split("[/conversation]")[0] if "[conversation]" in response else ""
    command = response.split("[command]")[1].split("[/command]")[0] if "[command]" in response else ""

    if conversation:
        if conversation[0] == "\n":
            conversation = conversation[1:]
        conversation = conversation.strip()
    if command:
        if command[0] == "\n":
            command = command[1:]
        command = command.strip()

    if command.startswith('echo -e'):
        command = command.replace('echo -e', 'echo')

    return {"conversation": conversation, "command": command}

def runCommand(command):
    with console.status("[bold blue]Executing command...[/bold blue]", spinner="boxBounce") as status:
        command_result = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        stdout = ""

        print(Markdown("# Output", style="blue underline"), end="")
        for char in iter(lambda : command_result.stdout.read(1), ""):
            status.stop()
            if char == "\\":
                char = "\\\\"
            print(f"[yellow3]{char}[/yellow3]", end="", flush=True)
            stdout += char

    if stdout != "":
        if stdout[-1] != "\n":
            print("")

    command_result.wait()
    stderr = command_result.stderr.read()
    code = command_result.returncode

    if stderr:
        console.log(stderr.strip())
    print(Markdown(f"# Status Code: {code}", style="bold green" if code == 0 else "bold red"), end="")

    return f"[stdout]{stdout}[/stdout] [code]{code}[/code] [stderr]{stderr}[/stderr]"

def getResponse(conversation, introduction = False):
    jarvis_tag = ("\n" if not introduction else "") + "[bold green][i][u]jarvis[/i]>[/bold green][/u]"
    if not tts:
        print(jarvis_tag)
        print(Markdown(f"{conversation}"))
    else:
        playResponse(jarvis_tag, conversation)

def playResponse(jarvis_tag, conversation):
    with console.status("[bold green]Getting response...[/bold green]") as status:
        try:
            response = client.audio.speech.create(input=conversation, model='tts-1', voice='fable')
        except Exception as e:
            error_code = e.message.split(' - ')[0]
            message_object = json.loads(e.message.split(' - ')[1].replace("'", '"').replace("None", "null"))
            console.log(f"{error_code}\nReason: {message_object['error']['code']}\nMessage: {message_object['error']['message']}", style='bold red')
            sys.exit(1)
        with open('speech.mp3', 'wb') as file:
            file.write(response.content)
    try:
        print(jarvis_tag)
        print(Markdown(f"{conversation}"))
        playsound('speech.mp3', False)
        for i in track(range(int(MP3('speech.mp3').info.length)*10 + 3), description=""):
            time.sleep(0.1)
    except Exception as e:
        console.log(f"Error: {e}")
        os.remove('speech.mp3')
        sys.exit(1)
    os.remove('speech.mp3')

def main():
    introAnimation()
    initializeClient(device)

    user = subprocess.Popen("whoami", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True).stdout.read()
    user_tag = f"[bold yellow][i][u]{user.strip()}[/i]>[/bold yellow][/u]"

    introduction = askQuestion(introduction=True)
    blocks = getBlocks(introduction)
    getResponse(blocks['conversation'], introduction=True)

    while True:
        print(f"\n{user_tag}")
        request = Prompt.ask(Text("$", style="rgb(59,120,255)"))
        if request == "done" or request == "quit" or request == "exit" or request == "":
            break

        response = askQuestion(question=request)
        blocks = getBlocks(response)
        getResponse(blocks['conversation'])

        while blocks["command"]:
            syntax = Syntax(blocks["command"], "bash")
            console.print(syntax)

            if step_by_step:
                command_confirmation = Confirm.ask("Execute command?")
            else:
                command_confirmation = True

            if command_confirmation:
                if "sudo" in blocks["command"]:
                    sudo_confirmation = Confirm.ask("Are you sure you want to let Jarvis run a sudo command?")
                    if not sudo_confirmation:
                        break

                result = runCommand(blocks["command"])

                response = askQuestion(question=result)
                blocks = getBlocks(response)
                getResponse(blocks['conversation'])
            else:
                break

if __name__ == "__main__":
    main()